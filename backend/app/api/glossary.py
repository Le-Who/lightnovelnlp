from __future__ import annotations

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
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
def get_glossary_terms(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryTerm]:
    """Получить все термины глоссария для проекта."""
    terms = db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id).all()
    return terms


@router.post("/terms", response_model=GlossaryTermRead, status_code=status.HTTP_201_CREATED)
def create_glossary_term(term: GlossaryTermCreate, db: Session = Depends(get_db)) -> GlossaryTerm:
    """Создать новый термин в глоссарии."""
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
    
    for field, value in term.dict(exclude_unset=True).items():
        setattr(db_term, field, value)
    
    db.commit()
    db.refresh(db_term)
    return db_term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)) -> None:
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
def get_glossary_versions(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryVersion]:
    """Получить версии глоссария для проекта."""
    versions = db.query(GlossaryVersion).filter(GlossaryVersion.project_id == project_id).all()
    return versions


@router.post("/versions", response_model=GlossaryVersionRead, status_code=status.HTTP_201_CREATED)
def create_glossary_version(version: GlossaryVersionCreate, db: Session = Depends(get_db)) -> GlossaryVersion:
    """Создать новую версию глоссария."""
    # Получаем все утвержденные термины для проекта
    terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == version.project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    # Создаем версию
    db_version = GlossaryVersion(
        project_id=version.project_id,
        version_name=version.version_name,
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
        
        # Попробуем получить несколько ключей для проверки
        test_key = "cache_test"
        cache_service.set(test_key, "test_value", ttl=60)
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
