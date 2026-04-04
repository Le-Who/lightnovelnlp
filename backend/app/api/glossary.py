from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_db
from app.models.glossary import (
    GlossaryTerm,
    GlossaryVersion,
    TermOccurrence,
    TermRelationship,
    TermStatus,
)
from app.models.project import Chapter
from app.schemas.glossary import (
    GlossaryTermCreate,
    GlossaryTermRead,
    GlossaryTermUpdate,
    GlossaryVersionCreate,
    GlossaryVersionRead,
    TermRelationshipCreate,
    TermRelationshipRead,
)
from app.services.cache_service import cache_service
from app.services.gemini_client import gemini_client

router = APIRouter()


@router.get("/{project_id}/terms", response_model=List[GlossaryTermRead])
def get_glossary_terms(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="id"),
    order: str = Query(default="asc"),
) -> List[GlossaryTerm]:
    """Получить все термины глоссария для проекта с пагинацией/поиском/сортировкой."""

    # Subqueries for relationship counts
    # We use correlate(GlossaryTerm) so the subquery references the outer GlossaryTerm
    stmt_source = (
        select(func.count(TermRelationship.id))
        .where(TermRelationship.source_term_id == GlossaryTerm.id)
        .scalar_subquery()
    )
    stmt_target = (
        select(func.count(TermRelationship.id))
        .where(TermRelationship.target_term_id == GlossaryTerm.id)
        .scalar_subquery()
    )

    # Select GlossaryTerm and the counts
    q = db.query(
        GlossaryTerm,
        stmt_source.label("source_count"),
        stmt_target.label("target_count"),
    ).filter(GlossaryTerm.project_id == project_id)

    # Eager load for metrics
    q = q.options(
        selectinload(GlossaryTerm.occurrences).load_only(
            TermOccurrence.chapter_id, TermOccurrence.frequency
        ),
        # Optimize: Only load ID and order to avoid fetching heavy text fields
        selectinload(GlossaryTerm.first_chapter).load_only(Chapter.id, Chapter.order),
        selectinload(GlossaryTerm.last_chapter).load_only(Chapter.id, Chapter.order),
    )
    # Removed eager loading of source/target relationships as we only need counts

    if search:
        s = f"%{search}%"
        q = q.filter(
            (GlossaryTerm.source_term.ilike(s))
            | (GlossaryTerm.translated_term.ilike(s))
        )
    # Сортировка
    sort_map = {
        "id": GlossaryTerm.id,
        "source_term": GlossaryTerm.source_term,
        "translated_term": GlossaryTerm.translated_term,
        "created_at": GlossaryTerm.created_at,
        "status": GlossaryTerm.status,
        "frequency": GlossaryTerm.frequency,
    }
    sort_col = sort_map.get(sort_by, GlossaryTerm.id)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)

    results = q.all()

    terms = []
    # Populate computed fields
    for row in results:
        # row is a tuple-like result: (GlossaryTerm, source_count, target_count)
        term = row[0]
        source_count = row[1] or 0
        target_count = row[2] or 0

        term.centrality_score = source_count + target_count
        term.occurrences_data = [
            {"chapter_id": occ.chapter_id, "freq": occ.frequency}
            for occ in term.occurrences
        ]
        if term.first_chapter:
            term.first_chapter_order = term.first_chapter.order
        if term.last_chapter:
            term.last_chapter_order = term.last_chapter.order

        terms.append(term)

    return terms


@router.get("/{project_id}/terms/pending", response_model=List[GlossaryTermRead])
def get_pending_glossary_terms(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="asc"),
) -> List[GlossaryTerm]:
    """Получить термины глоссария в ожидании утверждения для проекта (с пагинацией/поиском/сортировкой)."""
    q = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id, GlossaryTerm.status == TermStatus.PENDING
    )
    if search:
        s = f"%{search}%"
        q = q.filter(
            (GlossaryTerm.source_term.ilike(s))
            | (GlossaryTerm.translated_term.ilike(s))
        )
    sort_map = {
        "id": GlossaryTerm.id,
        "source_term": GlossaryTerm.source_term,
        "translated_term": GlossaryTerm.translated_term,
        "created_at": GlossaryTerm.created_at,
        "frequency": GlossaryTerm.frequency,  # Добавляем сортировку по частоте
    }
    sort_col = sort_map.get(sort_by, GlossaryTerm.created_at)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.get("/terms/{term_id}/details", response_model=GlossaryTermRead)
def get_glossary_term_details(
    term_id: int, db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Получить детали конкретного термина глоссария."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    return db_term


@router.get("/terms/{term_id}", response_model=GlossaryTermRead)
def get_glossary_term_direct(
    term_id: int, db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Convenience alias for getting term details."""
    return get_glossary_term_details(term_id, db)


@router.post(
    "/terms", response_model=GlossaryTermRead, status_code=status.HTTP_201_CREATED
)
def create_glossary_term(
    term: GlossaryTermCreate, db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Создать новый термин в глоссарии."""
    # Проверяем, не существует ли уже такой термин в проекте
    existing_term = (
        db.query(GlossaryTerm)
        .filter(
            GlossaryTerm.project_id == term.project_id,
            GlossaryTerm.source_term == term.source_term,
        )
        .first()
    )

    if existing_term:
        raise HTTPException(
            status_code=400,
            detail=f"Term '{term.source_term}' already exists in this project",
        )

    db_term = GlossaryTerm(**term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term


@router.put("/terms/{term_id}", response_model=GlossaryTermRead)
def update_glossary_term(
    term_id: int, term: GlossaryTermUpdate, db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Обновить термин в глоссарии."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    # Проверка уникальности source_term в рамках проекта, если меняется
    updates = term.dict(exclude_unset=True)
    new_source = updates.get("source_term")
    if new_source and new_source != db_term.source_term:
        conflict = (
            db.query(GlossaryTerm)
            .filter(
                GlossaryTerm.project_id == db_term.project_id,
                GlossaryTerm.source_term == new_source,
                GlossaryTerm.id != term_id,
            )
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Term '{new_source}' already exists in this project",
            )

    for field, value in updates.items():
        setattr(db_term, field, value)

    db.commit()
    db.refresh(db_term)
    return db_term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)):
    """Удалить термин из глоссария."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    db.delete(db_term)
    db.commit()


@router.post("/terms/{term_id}/approve", response_model=GlossaryTermRead)
def approve_glossary_term(term_id: int, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Утвердить термин в глоссарии."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    db_term.status = TermStatus.APPROVED
    db_term.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_term)
    return db_term


@router.post("/terms/{term_id}/reject", response_model=GlossaryTermRead)
def reject_glossary_term(term_id: int, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Отклонить термин в глоссарии."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")

    db_term.status = TermStatus.REJECTED
    db_term.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_term)
    return db_term


@router.get("/{project_id}/relationships", response_model=List[TermRelationshipRead])
def get_term_relationships(
    project_id: int, db: Session = Depends(get_db)
) -> List[TermRelationship]:
    """Получить связи между терминами для проекта."""
    relationships = (
        db.query(TermRelationship)
        .filter(TermRelationship.project_id == project_id)
        .all()
    )
    return relationships


@router.post(
    "/relationships",
    response_model=TermRelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_term_relationship(
    relationship: TermRelationshipCreate, db: Session = Depends(get_db)
) -> TermRelationship:
    """Создать связь между терминами."""
    db_relationship = TermRelationship(**relationship.dict())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship


@router.get("/{project_id}/versions", response_model=List[GlossaryVersionRead])
def get_glossary_versions(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="id"),
    order: str = Query(default="desc"),
) -> List[GlossaryVersion]:
    """Получить версии глоссария для проекта (с пагинацией/сортировкой)."""
    from app.models.glossary import GlossaryVersion  # локальный импорт для типов

    q = db.query(GlossaryVersion).filter(GlossaryVersion.project_id == project_id)
    sort_map = {
        "id": GlossaryVersion.id,
        "created_at": GlossaryVersion.created_at,
        "version_name": GlossaryVersion.version_name,
    }
    sort_col = sort_map.get(sort_by, GlossaryVersion.id)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.post(
    "/{project_id}/versions",
    response_model=GlossaryVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_glossary_version(
    project_id: int, version: GlossaryVersionCreate, db: Session = Depends(get_db)
) -> GlossaryVersion:
    """Создать новую версию глоссария."""
    # Получаем все утвержденные термины для проекта
    terms = (
        db.query(GlossaryTerm)
        .filter(
            GlossaryTerm.project_id == project_id,
            GlossaryTerm.status == TermStatus.APPROVED,
        )
        .all()
    )

    # Создаем версию
    db_version = GlossaryVersion(
        project_id=project_id,
        version_name=version.name
        or f"Version {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        description=version.description,
        terms_data=[
            {
                "source_term": term.source_term,
                "translated_term": term.translated_term,
                "category": term.category,
                "context": term.context,
                "frequency": term.frequency,
            }
            for term in terms
        ],
    )

    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


@router.post("/versions/{version_id}/restore", response_model=List[GlossaryTermRead])
def restore_glossary_version(
    version_id: int, db: Session = Depends(get_db)
) -> List[GlossaryTerm]:
    """Восстановить версию глоссария."""
    db_version = db.get(GlossaryVersion, version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Удаляем все существующие термины проекта
    db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == db_version.project_id
    ).delete()

    # Восстанавливаем термины из версии
    restored_terms = []
    for term_data in db_version.terms_data:
        term = GlossaryTerm(
            project_id=db_version.project_id,
            source_term=term_data["source_term"],
            translated_term=term_data["translated_term"],
            category=term_data["category"],
            context=term_data.get("context", ""),
            frequency=term_data.get("frequency", 1),
            status=TermStatus.APPROVED,
            approved_at=datetime.now(timezone.utc),
        )
        db.add(term)
        restored_terms.append(term)

    db.commit()
    return restored_terms


@router.get("/api-usage")
def get_gemini_api_usage():
    """Получить статистику использования Gemini API ключей."""
    # Не дергаем Redis напрямую из ручки; статистика берется у клиента
    stats = gemini_client.get_usage_stats()
    return {"success": True, "data": stats}


@router.get("/cache-stats")
def get_cache_stats():
    """Получить статистику кэширования."""
    cache_info = {
        "cache_service_available": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    test_key = "cache_ping"
    ok_set = cache_service.set(test_key, "1", ttl=10)
    # 'тихий' get, без логов даже при отвале
    val = cache_service.get_quiet(test_key)
    ok_get = (val == 1) or (val == "1")
    ok_del = cache_service.delete(test_key)
    cache_info["cache_working"] = bool(ok_set and ok_get and ok_del)
    return {"success": True, "data": cache_info}
