from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.deps import get_db
from app.models.project import Chapter
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship
from app.services.cache_service import cache_service

router = APIRouter()


def process_chapter_sync(chapter_id: int, db: Session):
    """Синхронная обработка главы для извлечения терминов."""
    try:
        # Получаем главу
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "chapter_id": chapter_id}
        
        # 1. Извлекаем термины
        extracted_terms = term_extractor.extract_terms(chapter.original_text)
        
        # Сохраняем термины в БД
        saved_terms = []
        for term_data in extracted_terms:
            # Проверяем, не существует ли уже такой термин
            existing_term = db.query(GlossaryTerm).filter(
                GlossaryTerm.project_id == chapter.project_id,
                GlossaryTerm.source_term == term_data["source_term"]
            ).first()
            
            if not existing_term:
                term = GlossaryTerm(
                    project_id=chapter.project_id,
                    source_term=term_data["source_term"],
                    translated_term=term_data.get("translated_term", ""),
                    category=term_data.get("category", TermCategory.OTHER),
                    status=TermStatus.PENDING,
                    context=term_data.get("context", "")
                )
                db.add(term)
                saved_terms.append(term)
        
        # 2. Анализируем связи между терминами
        if len(saved_terms) > 1:
            relationships = relationship_analyzer.analyze_relationships(
                chapter.original_text, 
                [term.source_term for term in saved_terms]
            )
            
            for rel_data in relationships:
                relationship = TermRelationship(
                    project_id=chapter.project_id,
                    source_term=rel_data["source_term"],
                    target_term=rel_data["target_term"],
                    relationship_type=rel_data["relationship_type"],
                    confidence=rel_data.get("confidence", 0.5),
                    context=rel_data.get("context", "")
                )
                db.add(relationship)
        
        # 3. Создаем саммари главы
        chapter_summary = context_summarizer.summarize_chapter(
            chapter.original_text,
            [term.source_term for term in saved_terms]
        )
        
        # Обновляем главу
        chapter.summary = chapter_summary
        chapter.processed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "chapter_id": chapter_id,
            "extracted_terms": len(saved_terms),
            "relationships": len(relationships) if 'relationships' in locals() else 0,
            "summary_created": bool(chapter_summary)
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "chapter_id": chapter_id}


@router.post("/chapters/{chapter_id}/analyze", status_code=status.HTTP_200_OK)
def analyze_chapter(
    chapter_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы для извлечения терминов (синхронно)."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Выполняем обработку синхронно
    result = process_chapter_sync(chapter_id, db)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "message": "Analysis completed",
        "chapter_id": chapter_id,
        "result": result
    }


@router.post("/chapters/{chapter_id}/analyze-async", status_code=status.HTTP_202_ACCEPTED)
def analyze_chapter_async(
    chapter_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы в фоновом режиме (если доступен)."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Добавляем задачу в фоновые задачи FastAPI
    background_tasks.add_task(process_chapter_sync, chapter_id, db)
    
    return {
        "message": "Analysis started in background",
        "chapter_id": chapter_id,
        "note": "Processing will continue in background. Check chapter status for updates."
    }


@router.get("/chapters/{chapter_id}/status")
def get_chapter_status(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить статус обработки главы."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Подсчитываем количество терминов для этой главы
    terms_count = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id
    ).count()
    
    return {
        "chapter_id": chapter_id,
        "processed": chapter.processed_at is not None,
        "processed_at": chapter.processed_at,
        "summary": chapter.summary is not None,
        "terms_count": terms_count,
        "status": "completed" if chapter.processed_at else "pending"
    }
