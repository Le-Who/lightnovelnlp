from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship, GlossaryVersion
from app.schemas.glossary import (
    GlossaryTermCreate, 
    GlossaryTermRead, 
    GlossaryTermUpdate,
    TermRelationshipRead,
    GlossaryVersionCreate,
    GlossaryVersionRead,
    GlossaryVersionInfo
)
from app.services.cache_service import cache_service

router = APIRouter()


@router.get("/{project_id}/terms", response_model=List[GlossaryTermRead])
def list_glossary_terms(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryTerm]:
    """Получить все термины глоссария для проекта."""
    # Проверяем кэш
    cached_glossary = cache_service.get_cached_glossary(project_id)
    if cached_glossary:
        return cached_glossary
    
    terms = db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id).all()
    
    # Кэшируем результат
    cache_service.cache_glossary(project_id, terms)
    
    return terms


@router.get("/{project_id}/terms/pending", response_model=List[GlossaryTermRead])
def list_pending_terms(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryTerm]:
    """Получить только ожидающие утверждения термины."""
    terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id,
        GlossaryTerm.status == TermStatus.PENDING
    ).all()
    return terms


@router.post("/{project_id}/terms", response_model=GlossaryTermRead, status_code=status.HTTP_201_CREATED)
def create_glossary_term(
    project_id: int, 
    payload: GlossaryTermCreate, 
    db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Создать новый термин в глоссарии."""
    # Проверяем, что проект существует
    from app.models.project import Project
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверяем уникальность термина в рамках проекта
    existing = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id,
        GlossaryTerm.source_term == payload.source_term
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Term already exists in this project")
    
    term = GlossaryTerm(
        project_id=project_id,
        source_term=payload.source_term,
        translated_term=payload.translated_term,
        category=payload.category,
        context=payload.context
    )
    
    db.add(term)
    db.commit()
    db.refresh(term)
    
    # Инвалидируем кэш глоссария
    cache_service.invalidate_glossary_cache(project_id)
    
    return term


@router.put("/terms/{term_id}", response_model=GlossaryTermRead)
def update_glossary_term(
    term_id: int, 
    payload: GlossaryTermUpdate, 
    db: Session = Depends(get_db)
) -> GlossaryTerm:
    """Обновить термин глоссария."""
    term = db.get(GlossaryTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    # Обновляем только переданные поля
    if payload.translated_term is not None:
        term.translated_term = payload.translated_term
    if payload.category is not None:
        term.category = payload.category
    if payload.status is not None:
        term.status = payload.status
    
    db.commit()
    db.refresh(term)
    
    # Инвалидируем кэш глоссария
    cache_service.invalidate_glossary_cache(term.project_id)
    
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)) -> None:
    """Удалить термин из глоссария."""
    term = db.get(GlossaryTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    project_id = term.project_id
    
    db.delete(term)
    db.commit()
    
    # Инвалидируем кэш глоссария
    cache_service.invalidate_glossary_cache(project_id)
    
    return None


@router.post("/terms/{term_id}/approve", response_model=GlossaryTermRead)
def approve_term(term_id: int, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Утвердить термин (изменить статус на approved)."""
    term = db.get(GlossaryTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    term.status = TermStatus.APPROVED
    db.commit()
    db.refresh(term)
    
    # Инвалидируем кэш глоссария
    cache_service.invalidate_glossary_cache(term.project_id)
    
    return term


# API для связей между терминами
@router.get("/{project_id}/relationships", response_model=List[TermRelationshipRead])
def list_term_relationships(project_id: int, db: Session = Depends(get_db)) -> List[TermRelationship]:
    """Получить все связи между терминами для проекта."""
    # Проверяем кэш
    cached_relationships = cache_service.get_cached_relationships(project_id)
    if cached_relationships:
        return cached_relationships
    
    relationships = db.query(TermRelationship).filter(
        TermRelationship.project_id == project_id
    ).all()
    
    # Кэшируем результат
    cache_service.cache_relationships(project_id, relationships)
    
    return relationships


@router.get("/terms/{term_id}/relationships", response_model=List[TermRelationshipRead])
def get_term_relationships(term_id: int, db: Session = Depends(get_db)) -> List[TermRelationship]:
    """Получить все связи для конкретного термина."""
    # Проверяем, что термин существует
    term = db.get(GlossaryTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    # Получаем связи где термин является источником или целью
    relationships = db.query(TermRelationship).filter(
        (TermRelationship.source_term_id == term_id) | 
        (TermRelationship.target_term_id == term_id)
    ).all()
    
    return relationships


@router.get("/{project_id}/relationships/graph")
def get_relationships_graph(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить граф связей для визуализации."""
    # Получаем все термины проекта
    terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id
    ).all()
    
    # Получаем все связи
    relationships = db.query(TermRelationship).filter(
        TermRelationship.project_id == project_id
    ).all()
    
    # Формируем данные для графа
    nodes = []
    edges = []
    
    # Узлы (термины)
    for term in terms:
        nodes.append({
            "id": term.id,
            "label": term.source_term,
            "translated": term.translated_term,
            "category": term.category,
            "status": term.status
        })
    
    # Ребра (связи)
    for rel in relationships:
        edges.append({
            "source": rel.source_term_id,
            "target": rel.target_term_id,
            "type": rel.relation_type,
            "confidence": rel.confidence,
            "context": rel.context
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }


# API для версионирования глоссария
@router.post("/{project_id}/versions", response_model=GlossaryVersionRead, status_code=status.HTTP_201_CREATED)
def create_glossary_version(
    project_id: int,
    payload: GlossaryVersionCreate,
    db: Session = Depends(get_db)
) -> GlossaryVersion:
    """Создать новую версию глоссария."""
    # Проверяем, что проект существует
    from app.models.project import Project
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Получаем текущие термины
    terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == project_id
    ).all()
    
    if not terms:
        raise HTTPException(
            status_code=400, 
            detail="No terms found in glossary. Cannot create version."
        )
    
    # Определяем номер версии
    latest_version = db.query(GlossaryVersion).filter(
        GlossaryVersion.project_id == project_id
    ).order_by(GlossaryVersion.version_number.desc()).first()
    
    version_number = (latest_version.version_number + 1) if latest_version else 1
    
    # Создаем снимок терминов
    terms_snapshot = []
    for term in terms:
        terms_snapshot.append({
            "id": term.id,
            "source_term": term.source_term,
            "translated_term": term.translated_term,
            "category": term.category,
            "status": term.status,
            "context": term.context,
            "created_at": term.created_at.isoformat()
        })
    
    # Создаем версию
    version = GlossaryVersion(
        project_id=project_id,
        version_number=version_number,
        name=payload.name,
        description=payload.description,
        terms_snapshot=terms_snapshot,
        created_by="system"  # В будущем можно добавить аутентификацию
    )
    
    db.add(version)
    db.commit()
    db.refresh(version)
    
    return version


@router.get("/{project_id}/versions", response_model=List[GlossaryVersionInfo])
def list_glossary_versions(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryVersionInfo]:
    """Получить список версий глоссария."""
    versions = db.query(GlossaryVersion).filter(
        GlossaryVersion.project_id == project_id
    ).order_by(GlossaryVersion.version_number.desc()).all()
    
    version_infos = []
    for version in versions:
        # Подсчитываем статистику
        terms_count = len(version.terms_snapshot)
        approved_terms_count = sum(
            1 for term in version.terms_snapshot 
            if term.get("status") == TermStatus.APPROVED
        )
        
        version_infos.append(GlossaryVersionInfo(
            version_id=version.id,
            version_number=version.version_number,
            name=version.name,
            description=version.description,
            created_at=version.created_at,
            terms_count=terms_count,
            approved_terms_count=approved_terms_count
        ))
    
    return version_infos


@router.get("/versions/{version_id}", response_model=GlossaryVersionRead)
def get_glossary_version(version_id: int, db: Session = Depends(get_db)) -> GlossaryVersion:
    """Получить конкретную версию глоссария."""
    version = db.get(GlossaryVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version


@router.post("/versions/{version_id}/restore", status_code=status.HTTP_200_OK)
def restore_glossary_version(version_id: int, db: Session = Depends(get_db)) -> dict:
    """Восстановить глоссарий из версии."""
    version = db.get(GlossaryVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    try:
        # Удаляем текущие термины
        db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == version.project_id
        ).delete()
        
        # Восстанавливаем термины из снимка
        for term_data in version.terms_snapshot:
            term = GlossaryTerm(
                project_id=version.project_id,
                source_term=term_data["source_term"],
                translated_term=term_data["translated_term"],
                category=term_data["category"],
                status=term_data["status"],
                context=term_data.get("context")
            )
            db.add(term)
        
        db.commit()
        
        # Инвалидируем кэш
        cache_service.invalidate_glossary_cache(version.project_id)
        
        return {
            "message": f"Glossary restored from version {version.version_number}",
            "restored_terms": len(version.terms_snapshot)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore glossary: {str(e)}"
        )
