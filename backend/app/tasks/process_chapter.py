from __future__ import annotations

from celery import shared_task
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.project import Chapter
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory
from app.core.nlp_pipeline.term_extractor import term_extractor


@shared_task(name="process_chapter")
def process_chapter_task(chapter_id: int) -> dict:
    """Обработать главу: извлечь термины и сохранить в глоссарий."""
    db = SessionLocal()
    
    try:
        # Получаем главу
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "chapter_id": chapter_id}
        
        # Извлекаем термины
        extracted_terms = term_extractor.extract_terms(chapter.original_text)
        
        # Сохраняем термины в БД
        saved_terms = []
        for term_data in extracted_terms:
            # Проверяем, не существует ли уже такой термин
            existing = db.query(GlossaryTerm).filter(
                GlossaryTerm.project_id == chapter.project_id,
                GlossaryTerm.source_term == term_data["source_term"]
            ).first()
            
            if existing:
                continue  # Пропускаем дубликаты
            
            # Создаем новый термин
            term = GlossaryTerm(
                project_id=chapter.project_id,
                source_term=term_data["source_term"],
                translated_term=term_data["translated_term"],
                category=TermCategory(term_data["category"]),
                context=term_data.get("context"),
                status=TermStatus.PENDING
            )
            
            db.add(term)
            saved_terms.append(term_data["source_term"])
        
        db.commit()
        
        return {
            "chapter_id": chapter_id,
            "status": "completed",
            "extracted_terms": len(extracted_terms),
            "saved_terms": len(saved_terms),
            "terms": saved_terms
        }
        
    except Exception as e:
        db.rollback()
        return {
            "chapter_id": chapter_id,
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()
