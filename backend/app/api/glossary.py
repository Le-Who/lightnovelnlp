from __future__ import annotations

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship, GlossaryVersion
from app.schemas.glossary import (
    GlossaryTermCreate, 
    GlossaryTermRead, 
    GlossaryTermUpdate,
    TermRelationshipCreate,
    TermRelationshipRead,
    GlossaryVersionCreate,
    GlossaryVersionRead
)
from app.services.cache_service import cache_service
from app.services.gemini_client import gemini_client

router = APIRouter()


@router.get("/terms/{project_id}", response_model=List[GlossaryTermRead])
def get_glossary_terms(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="id"),
    order: str = Query(default="asc")
) -> List[GlossaryTerm]:
    """Получить все термины глоссария для проекта с пагинацией/поиском/сортировкой."""
    q = db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id)
    if search:
        s = f"%{search}%"
        q = q.filter((GlossaryTerm.source_term.ilike(s)) | (GlossaryTerm.translated_term.ilike(s)))
    # Сортировка
    sort_map = {
        "id": GlossaryTerm.id,
        "source_term": GlossaryTerm.source_term,
        "translated_term": GlossaryTerm.translated_term,
        "created_at": GlossaryTerm.created_at,
        "status": GlossaryTerm.status,
    }
    sort_col = sort_map.get(sort_by, GlossaryTerm.id)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.get("/terms/{project_id}/pending", response_model=List[GlossaryTermRead])
def get_pending_glossary_terms(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="asc")
) -> List[GlossaryTerm]:
    """Получить термины глоссария в ожидании утверждения для проекта (с пагинацией/поиском/сортировкой)."""
    q = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id,
        GlossaryTerm.status == TermStatus.PENDING
    )
    if search:
        s = f"%{search}%"
        q = q.filter((GlossaryTerm.source_term.ilike(s)) | (GlossaryTerm.translated_term.ilike(s)))
    sort_map = {
        "id": GlossaryTerm.id,
        "source_term": GlossaryTerm.source_term,
        "translated_term": GlossaryTerm.translated_term,
        "created_at": GlossaryTerm.created_at,
    }
    sort_col = sort_map.get(sort_by, GlossaryTerm.created_at)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.get("/terms/{term_id}/details", response_model=GlossaryTermRead)
def get_glossary_term_details(term_id: int, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Получить детали конкретного термина глоссария."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    return db_term


@router.post("/terms", response_model=GlossaryTermRead, status_code=status.HTTP_201_CREATED)
def create_glossary_term(term: GlossaryTermCreate, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Создать новый термин в глоссарии."""
    # Проверяем, не существует ли уже такой термин в проекте
    existing_term = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == term.project_id,
        GlossaryTerm.source_term == term.source_term
    ).first()
    
    if existing_term:
        raise HTTPException(
            status_code=400, 
            detail=f"Term '{term.source_term}' already exists in this project"
        )
    
    db_term = GlossaryTerm(**term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    return db_term


@router.put("/terms/{term_id}", response_model=GlossaryTermRead)
def update_glossary_term(term_id: int, term: GlossaryTermUpdate, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Обновить термин в глоссарии."""
    db_term = db.get(GlossaryTerm, term_id)
    if not db_term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    # Проверка уникальности source_term в рамках проекта, если меняется
    updates = term.dict(exclude_unset=True)
    new_source = updates.get("source_term")
    if new_source and new_source != db_term.source_term:
        conflict = db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == db_term.project_id,
            GlossaryTerm.source_term == new_source,
            GlossaryTerm.id != term_id,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Term '{new_source}' already exists in this project")
    
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
    db_term.approved_at = datetime.utcnow()
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
    db_term.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(db_term)
    return db_term


@router.get("/relationships/{project_id}", response_model=List[TermRelationshipRead])
def get_term_relationships(project_id: int, db: Session = Depends(get_db)) -> List[TermRelationship]:
    """Получить связи между терминами для проекта."""
    relationships = db.query(TermRelationship).filter(TermRelationship.project_id == project_id).all()
    return relationships


@router.post("/relationships", response_model=TermRelationshipRead, status_code=status.HTTP_201_CREATED)
def create_term_relationship(relationship: TermRelationshipCreate, db: Session = Depends(get_db)) -> TermRelationship:
    """Создать связь между терминами."""
    db_relationship = TermRelationship(**relationship.dict())
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship


@router.get("/versions/{project_id}", response_model=List[GlossaryVersionRead])
def get_glossary_versions(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="id"),
    order: str = Query(default="desc")
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


@router.post("/versions/{project_id}", response_model=GlossaryVersionRead, status_code=status.HTTP_201_CREATED)
def create_glossary_version(project_id: int, version: GlossaryVersionCreate, db: Session = Depends(get_db)) -> GlossaryVersion:
    """Создать новую версию глоссария."""
    # Получаем все утвержденные термины для проекта
    terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    # Создаем версию
    db_version = GlossaryVersion(
        project_id=project_id,
        version_name=version.name or f"Version {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        description=version.description,
        terms_data=[{
            "source_term": term.source_term,
            "translated_term": term.translated_term,
            "category": term.category,
            "context": term.context
        } for term in terms]
    )
    
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


@router.post("/versions/{version_id}/restore", response_model=List[GlossaryTermRead])
def restore_glossary_version(version_id: int, db: Session = Depends(get_db)) -> List[GlossaryTerm]:
    """Восстановить версию глоссария."""
    db_version = db.get(GlossaryVersion, version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Удаляем все существующие термины проекта
    db.query(GlossaryTerm).filter(GlossaryTerm.project_id == db_version.project_id).delete()
    
    # Восстанавливаем термины из версии
    restored_terms = []
    for term_data in db_version.terms_data:
        term = GlossaryTerm(
            project_id=db_version.project_id,
            source_term=term_data["source_term"],
            translated_term=term_data["translated_term"],
            category=term_data["category"],
            context=term_data.get("context", ""),
            status=TermStatus.APPROVED,
            approved_at=datetime.utcnow()
        )
        db.add(term)
        restored_terms.append(term)
    
    db.commit()
    return restored_terms


@router.get("/api-usage")
def get_gemini_api_usage():
    """Получить статистику использования Gemini API ключей."""
    try:
        stats = gemini_client.get_usage_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


@router.get("/cache-stats")
def get_cache_stats():
    """Получить статистику кэширования."""
    try:
        # Получаем базовую информацию о кэше
        cache_info = {
            "cache_service_available": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Попробуем получить несколько ключей для проверки (с мягкими ретраями уже в сервисе)
        test_key = "cache_test"
        cache_service.set(test_key, "test_value", ttl=15)
        test_value = cache_service.get(test_key)
        cache_service.delete(test_key)
        
        cache_info["cache_working"] = test_value == "test_value"
        
        return {
            "success": True,
            "data": cache_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }
