from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.models.project import Chapter, Project
from app.models.glossary import GlossaryTerm, TermStatus
from app.services.cache_service import cache_service
from app.services.glossary_service import GlossaryService
from app.core.translation_engine import translation_engine
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.services.gemini_client import gemini_client

class TranslationService:
    @staticmethod
    def translate_chapter(
        db: Session, 
        chapter_id: int, 
        use_glossary: bool = True
    ) -> Dict[str, Any]:
        """Оркестрация перевода главы: кэш, глоссарий, саммари, перевод, сохранение."""
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}
            
        # 1. Глоссарий
        glossary_terms = []
        relevant_relationships = []
        
        if use_glossary:
            all_terms = db.query(GlossaryTerm).filter(
                GlossaryTerm.project_id == chapter.project_id,
                GlossaryTerm.status == TermStatus.APPROVED
            ).all()
            
            # Smart Filtering: Only send terms present in the text
            glossary_terms = GlossaryService.filter_terms_by_text(chapter.original_text, all_terms)
            
            # 1.1 Получаем связи между найденными терминами
            if glossary_terms:
                relevant_relationships = TranslationService._get_relevant_relationships(db, glossary_terms)
            
        # 2. Кэш
        glossary_hash = cache_service.generate_glossary_hash([
            {
                "source_term": t.source_term,
                "translated_term": t.translated_term,
                "category": t.category
            } for t in glossary_terms
        ])
        
        cached_translation = cache_service.get_cached_translation(chapter.id, glossary_hash)
        if cached_translation:
            return {
                "chapter_id": chapter_id,
                "translated_text": cached_translation,
                "glossary_terms_used": len(glossary_terms),
                "context_used": bool(chapter.summary),
                "project_context_used": False,
                "message": "Translation retrieved from cache",
                "cached": True
            }
            
        # 3. Контекст проекта
        project_summary = TranslationService._get_project_summary(db, chapter.project_id)
        
        # 3.1 Контекст предыдущей главы
        previous_context = None
        previous_chapter = db.query(Chapter).filter(
            Chapter.project_id == chapter.project_id, 
            Chapter.order < chapter.order
        ).order_by(Chapter.order.desc()).first()
        
        if previous_chapter and previous_chapter.original_text:
            # Берем последние 1000 символов оригинала предыдущей главы
            text_len = len(previous_chapter.original_text)
            start_pos = max(0, text_len - 1000)
            previous_context = previous_chapter.original_text[start_pos:]
        
        # 4. Перевод
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary,
            relationships=relevant_relationships,
            genre=chapter.project.genre,
            previous_context=previous_context
        )
        
        # 5. Сохранение
        chapter.translated_text = translated_text
        db.commit()
        
        # 6. Обновление кэша
        cache_service.cache_translation(chapter.id, glossary_hash, translated_text)
        
        return {
            "chapter_id": chapter_id,
            "translated_text": translated_text,
            "glossary_terms_used": len(glossary_terms),
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "message": "Translation completed successfully",
            "cached": False
        }

    @staticmethod
    def preview_translation(db: Session, chapter_id: int) -> Dict[str, Any]:
        """Превью перевода без сохранения."""
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}
            
        all_terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == chapter.project_id,
            GlossaryTerm.status == TermStatus.APPROVED
        ).all()
        
        # Smart Filtering
        glossary_terms = GlossaryService.filter_terms_by_text(chapter.original_text, all_terms)
        
        if not glossary_terms:
            return {
                "chapter_id": chapter_id,
                "preview_available": False,
                "message": "No relevant glossary terms found in text.",
                "glossary_terms_count": 0
            }
            
        # Получаем связи
        relevant_relationships = TranslationService._get_relevant_relationships(db, glossary_terms)
            
        project_summary = TranslationService._get_project_summary(db, chapter.project_id)
        
        # Контекст предыдущей главы
        previous_context = None
        previous_chapter = db.query(Chapter).filter(
            Chapter.project_id == chapter.project_id, 
            Chapter.order < chapter.order
        ).order_by(Chapter.order.desc()).first()
        
        if previous_chapter and previous_chapter.original_text:
            text_len = len(previous_chapter.original_text)
            start_pos = max(0, text_len - 1000)
            previous_context = previous_chapter.original_text[start_pos:]
        
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary,
            relationships=relevant_relationships,
            genre=chapter.project.genre,
            previous_context=previous_context
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
                    "source_term": t.source_term,
                    "translated_term": t.translated_term,
                    "category": getattr(getattr(t, "category", None), "value", getattr(t, "category", None))
                } for t in glossary_terms
            ]
        }
    
    @staticmethod
    def review_translation(db: Session, chapter_id: int) -> Dict[str, Any]:
        """Рецензирование перевода через Gemini."""
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}
            
        if not chapter.translated_text:
            return {"error": "Chapter has no translation to review", "status_code": 400}
            
        all_terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.project_id == chapter.project_id,
            GlossaryTerm.status == TermStatus.APPROVED
        ).all()
        
        glossary_terms = GlossaryService.filter_terms_by_text(chapter.original_text, all_terms)
        
        source_lang = chapter.project.source_language
        target_lang = chapter.project.target_language
        
        review_prompt = f"""
        Please conduct a stylistic and grammatical review of the translation from {source_lang} to {target_lang}.
        
        Original text ({source_lang}):
        {chapter.original_text[:1000]}...
        
        Current translation ({target_lang}):
        {chapter.translated_text}
        
        Approved glossary terms:
        {chr(10).join([f"- {t.source_term} -> {t.translated_term}" for t in glossary_terms[:10]])}
        
        Please analyze the translation and provide:
        1. Overall translation quality score (1-10)
        2. List of grammatical errors with corrections
        3. Stylistic suggestions for improvement
        4. Recommendations for using glossary terms
        5. General improvement comments
        
        The response should be structured and specific.
        """
        
        review_text = gemini_client.complete(review_prompt)
        
        review_key = f"translation_review:{chapter_id}"
        cache_service.set(review_key, review_text, ttl=3600)
        
        return {
            "chapter_id": chapter_id,
            "review_available": True,
            "review_text": review_text,
            "glossary_terms_used": len(glossary_terms),
            "message": "Translation review completed successfully"
        }

    @staticmethod
    def _get_relevant_relationships(db: Session, glossary_terms: List[GlossaryTerm]) -> List[Dict[str, Any]]:
        """Извлекает связи между переданными терминами."""
        from app.models.glossary import TermRelationship # Local import to avoid circular dependency
        
        if len(glossary_terms) < 2:
            return []
            
        term_ids = [t.id for t in glossary_terms]
        
        # Ищем связи, где оба участника есть в списке терминов
        relationships_db = db.query(TermRelationship).filter(
            TermRelationship.source_term_id.in_(term_ids),
            TermRelationship.target_term_id.in_(term_ids)
        ).all()
        
        formatted_relationships = []
        term_map = {t.id: t.source_term for t in glossary_terms}
        
        for r in relationships_db:
            formatted_relationships.append({
                "source": term_map.get(r.source_term_id, "Unknown"),
                "target": term_map.get(r.target_term_id, "Unknown"),
                "type": r.relation_type,
                "description": r.context or ""
            })
            
        return formatted_relationships

    @staticmethod
    def _get_project_summary(db: Session, project_id: int) -> Optional[str]:
        """Вспомогательный метод для получения саммари проекта."""
        project_chapters = db.query(Chapter).filter(
            Chapter.project_id == project_id,
            Chapter.summary.isnot(None)
        ).order_by(Chapter.id).all()
        
        if len(project_chapters) > 1:
            chapters_data = [
                {
                    "title": ch.title,
                    "summary": ch.summary,
                    "original_text": ch.original_text
                }
                for ch in project_chapters[:5]
            ]
            return context_summarizer.create_project_summary(chapters_data)
        return None
