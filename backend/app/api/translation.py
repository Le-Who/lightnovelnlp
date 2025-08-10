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
        # Проверяем кэш перевода
        glossary_hash = cache_service.generate_glossary_hash([
            {
                "source_term": term.source_term,
                "translated_term": term.translated_term,
                "category": term.category
            }
            for term in glossary_terms
        ])
        
        cached_translation = cache_service.get_cached_translation(chapter.id, glossary_hash)
        if cached_translation:
            # Возвращаем кэшированный перевод
            return {
                "chapter_id": chapter_id,
                "translated_text": cached_translation,
                "glossary_terms_used": len(glossary_terms) if use_glossary else 0,
                "context_used": bool(chapter.summary),
                "project_context_used": False,  # Кэш не содержит project context
                "message": "Translation retrieved from cache",
                "cached": True
            }
        
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
        
        # Кэшируем результат перевода
        cache_service.cache_translation(chapter.id, glossary_hash, translated_text)
        
        return {
            "chapter_id": chapter_id,
            "translated_text": translated_text,
            "glossary_terms_used": len(glossary_terms) if use_glossary else 0,
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "message": "Translation completed successfully",
            "cached": False
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


@router.post("/chapters/{chapter_id}/review")
def review_translation(
    chapter_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Запросить рецензирование перевода главы у LLM."""
    # Получаем главу
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if not chapter.translated_text:
        raise HTTPException(
            status_code=400, 
            detail="Chapter has no translation to review"
        )
    
    try:
        # Получаем утвержденные термины глоссария
        glossary_terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == chapter.project_id,
            GlossaryTerm.status == TermStatus.APPROVED
        ).all()
        
        # Создаем промпт для рецензирования
        review_prompt = f"""
        Пожалуйста, проведите стилистическую и грамматическую проверку перевода с русского на английский.
        
        Оригинальный текст (русский):
        {chapter.original_text[:1000]}...
        
        Текущий перевод (английский):
        {chapter.translated_text}
        
        Утвержденные термины глоссария:
        {chr(10).join([f"- {term.source_term} → {term.translated_term}" for term in glossary_terms[:10]])}
        
        Пожалуйста, проанализируйте перевод и предоставьте:
        1. Общую оценку качества перевода (1-10)
        2. Список грамматических ошибок с исправлениями
        3. Стилистические предложения по улучшению
        4. Рекомендации по использованию терминов глоссария
        5. Общие комментарии по улучшению
        
        Ответ должен быть структурированным и конкретным.
        """
        
        # Получаем рецензию от LLM
        from app.services.gemini_client import gemini_client
        review_text = gemini_client.complete(review_prompt)
        
        # Сохраняем рецензию в кэше (не в БД, так как это временные данные)
        review_key = f"translation_review:{chapter_id}"
        cache_service.set_cache(review_key, review_text, ttl=3600)  # 1 час
        
        return {
            "chapter_id": chapter_id,
            "review_available": True,
            "review_text": review_text,
            "glossary_terms_used": len(glossary_terms),
            "message": "Translation review completed successfully"
        }
        
    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": f"Review generation failed: {str(e)}"
        }


@router.get("/chapters/{chapter_id}/review")
def get_translation_review(chapter_id: int) -> dict:
    """Получить рецензию перевода главы."""
    # Проверяем кэш на наличие рецензии
    review_key = f"translation_review:{chapter_id}"
    review_text = cache_service.get_cache(review_key)
    
    if not review_text:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": "No review found. Please generate a review first."
        }
    
    return {
        "chapter_id": chapter_id,
        "review_available": True,
        "review_text": review_text,
        "message": "Review retrieved from cache"
    }
