from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship
from app.schemas.glossary import (
    GlossaryTermCreate, 
    GlossaryTermRead, 
    GlossaryTermUpdate,
    TermRelationshipRead
)

router = APIRouter()


@router.get("/{project_id}/terms", response_model=List[GlossaryTermRead])
def list_glossary_terms(project_id: int, db: Session = Depends(get_db)) -> List[GlossaryTerm]:
    """Получить все термины глоссария для проекта."""
    terms = db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id).all()
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
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)) -> None:
    """Удалить термин из глоссария."""
    term = db.get(GlossaryTerm, term_id)
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    
    db.delete(term)
    db.commit()
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
    return term


# API для связей между терминами
@router.get("/{project_id}/relationships", response_model=List[TermRelationshipRead])
def list_term_relationships(project_id: int, db: Session = Depends(get_db)) -> List[TermRelationship]:
    """Получить все связи между терминами для проекта."""
    relationships = db.query(TermRelationship).filter(
        TermRelationship.project_id == project_id
    ).all()
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
            "category": term.category.value,
            "status": term.status.value
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
