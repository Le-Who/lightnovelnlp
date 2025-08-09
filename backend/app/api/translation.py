from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Chapter
from app.models.glossary import GlossaryTerm, TermStatus
from app.core.translation_engine import translation_engine
from app.services.cache_service import cache_service

router = APIRouter()


@router.post("/chapters/{chapter_id}/translate", status_code=status.HTTP_200_OK)
def translate_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    use_glossary: bool = Query(default=True)
) -> dict:
    """Перевести главу с использованием утвержденного глоссария и контекста."""
    # Получаем главу
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Получаем утвержденные термины глоссария для проекта (pending не блокируют перевод)
    glossary_terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    try:
        # Получаем общее саммари проекта (если есть)
        project_summary = None
        project_chapters = db.query(Chapter).filter(
            Chapter.project_id == chapter.project_id,
            Chapter.summary.isnot(None)
        ).order_by(Chapter.id).all()
        
        if len(project_chapters) > 1:  # Если есть несколько глав с саммари
            # Создаем краткое общее саммари
            from app.core.nlp_pipeline.context_summarizer import context_summarizer
            chapters_data = [
                {
                    "title": ch.title,
                    "summary": ch.summary,
                    "original_text": ch.original_text
                }
                for ch in project_chapters[:5]  # Берем первые 5 глав
            ]
            project_summary = context_summarizer.create_project_summary(chapters_data)
        
        # Переводим текст
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms if use_glossary else [],
            context_summary=chapter.summary,
            project_summary=project_summary
        )
        
        # Сохраняем перевод в БД
        chapter.translated_text = translated_text
        db.commit()
        
        # Инвалидируем кэш перевода для главы
        cache_service.invalidate_translation_cache(chapter_id)
        
        return {
            "chapter_id": chapter_id,
            "translated_text": translated_text,
            "glossary_terms_used": len(glossary_terms) if use_glossary else 0,
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "message": "Translation completed successfully"
        }
        
    except Exception as e:
        # В случае проблем с внешним API или кэшем избегаем краха транзакции
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=f"Translation failed: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/translation-preview")
def preview_translation(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Предварительный просмотр перевода (без сохранения)."""
    # Получаем главу
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Получаем утвержденные термины глоссария
    glossary_terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    if not glossary_terms:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": "No approved glossary terms found. Please approve some terms first.",
            "glossary_terms_count": 0
        }
    
    try:
        # Получаем общее саммари проекта (если есть)
        project_summary = None
        project_chapters = db.query(Chapter).filter(
            Chapter.project_id == chapter.project_id,
            Chapter.summary.isnot(None)
        ).order_by(Chapter.id).all()
        
        if len(project_chapters) > 1:
            from app.core.nlp_pipeline.context_summarizer import context_summarizer
            chapters_data = [
                {
                    "title": ch.title,
                    "summary": ch.summary,
                    "original_text": ch.original_text
                }
                for ch in project_chapters[:5]
            ]
            project_summary = context_summarizer.create_project_summary(chapters_data)
        
        # Создаем предварительный перевод
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary
        )
        
        return {
            "chapter_id": chapter_id,
            "preview_available": True,
            "original_text": chapter.original_text,
            "translated_text": translated_text,
            "glossary_terms_count": len(glossary_terms),
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "glossary_terms": [
                {
                    "source_term": term.source_term,
                    "translated_term": term.translated_term,
                    "category": getattr(getattr(term, "category", None), "value", getattr(term, "category", None))
                }
                for term in glossary_terms
            ]
        }
        
    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": f"Preview generation failed: {str(e)}",
            "glossary_terms_count": len(glossary_terms)
        }
