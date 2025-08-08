from __future__ import annotations

from celery import shared_task
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.project import Chapter
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer


@shared_task(name="process_chapter")
def process_chapter_task(chapter_id: int) -> dict:
    """Обработать главу: извлечь термины, проанализировать связи и создать саммари."""
    db = SessionLocal()
    
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
        
        # 2. Анализируем связи между терминами (если есть минимум 2 термина)
        existing_terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == chapter.project_id
        ).all()
        
        relationships_saved = 0
        if len(existing_terms) >= 2:
            relationships = relationship_analyzer.analyze_relationships(
                chapter.original_text, 
                existing_terms
            )
            
            # Сохраняем связи
            for rel_data in relationships:
                # Находим термины по названию
                source_term = db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.source_term == rel_data["source_term"]
                ).first()
                
                target_term = db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.source_term == rel_data["target_term"]
                ).first()
                
                if source_term and target_term:
                    # Проверяем, не существует ли уже такая связь
                    existing_rel = db.query(TermRelationship).filter(
                        TermRelationship.project_id == chapter.project_id,
                        TermRelationship.source_term_id == source_term.id,
                        TermRelationship.target_term_id == target_term.id,
                        TermRelationship.relation_type == rel_data["relation_type"]
                    ).first()
                    
                    if not existing_rel:
                        relationship = TermRelationship(
                            project_id=chapter.project_id,
                            source_term_id=source_term.id,
                            target_term_id=target_term.id,
                            relation_type=rel_data["relation_type"],
                            confidence=rel_data.get("confidence"),
                            context=rel_data.get("context")
                        )
                        db.add(relationship)
                        relationships_saved += 1
            
            db.commit()
        
        # 3. Создаем саммари контекста
        # Получаем саммари предыдущих глав для контекста
        previous_chapters = db.query(Chapter).filter(
            Chapter.project_id == chapter.project_id,
            Chapter.id < chapter.id
        ).order_by(Chapter.id.desc()).limit(3).all()
        
        previous_summary = None
        if previous_chapters:
            # Объединяем саммари предыдущих глав
            summaries = [ch.summary for ch in previous_chapters if ch.summary]
            if summaries:
                previous_summary = " ".join(summaries[-2:])  # Последние 2 саммари
        
        # Создаем саммари текущей главы
        chapter_summary = context_summarizer.summarize_context(
            chapter.original_text,
            chapter.title,
            previous_summary
        )
        
        # Сохраняем саммари
        if chapter_summary:
            chapter.summary = chapter_summary
            db.commit()
        
        return {
            "chapter_id": chapter_id,
            "status": "completed",
            "extracted_terms": len(extracted_terms),
            "saved_terms": len(saved_terms),
            "relationships_saved": relationships_saved,
            "summary_created": bool(chapter_summary),
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
