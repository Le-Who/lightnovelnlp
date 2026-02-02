from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client

logger = logging.getLogger(__name__)


class ContextSummarizer:
    def __init__(self):
        self.client = gemini_client

    def summarize_context(
        self, 
        text: str,
        chapter_title: str | None = None,
        previous_summary: str | None = None
    ) -> str:
        """
        Создает краткое саммари контекста главы.
        
        Args:
            text: Текст главы
            chapter_title: Название главы (опционально)
            previous_summary: Саммари предыдущих глав (опционально)
            
        Returns:
            str: Краткое саммари контекста
        """
        prompt = self._build_summary_prompt(text, chapter_title, previous_summary)
        
        try:
            response = self.client.complete(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error summarizing context: {e}")
            return ""

    def _build_summary_prompt(
        self, 
        text: str, 
        chapter_title: str | None = None,
        previous_summary: str | None = None
    ) -> str:
        """Строит промпт для создания саммари."""
        
        prompt = f"""
Ты - эксперт по анализу текстов ранобэ. Создай краткое саммари ключевых событий и контекста.

"""
        
        if chapter_title:
            prompt += f"Название главы: {chapter_title}\n\n"
            
        if previous_summary:
            prompt += f"""
КОНТЕКСТ ПРЕДЫДУЩИХ ГЛАВ:
{previous_summary}

"""
        
        prompt += f"""
ТЕКСТ ГЛАВЫ:
{text}

Создай краткое саммари (2-3 предложения) ключевых событий этой главы, включая:
- Основные действия персонажей
- Важные диалоги или решения
- Новые локации или артефакты
- Развитие сюжета

Саммари должно быть информативным, но кратким. Пиши на русском языке.

САММАРИ:
"""
        
        return prompt

    def create_project_summary(
        self, 
        chapters: List[Dict[str, Any]],
        window_size: int = 3
    ) -> str:
        """
        Создает иерархическое саммари проекта:
        1. "История ранее" (сжатое саммари старых глав)
        2. "Последние события" (подробное саммари последних N глав)
        
        Args:
            chapters: Список всех глав с summary
            window_size: Количество последних глав для подробного контекста
            
        Returns:
            str: Структурированное саммари для контекста перевода
        """
        if not chapters:
            return ""
            
        total_chapters = len(chapters)
        
        # Разделяем на "старые" и "новые"
        recent_chapters = chapters[-window_size:]
        old_chapters = chapters[:-window_size] if total_chapters > window_size else []
        
        summary_parts = []
        
        # 1. Глобальный контекст (если есть старые главы)
        if old_chapters:
            old_summary_text = "\n".join([ch.get('summary', '') for ch in old_chapters if ch.get('summary')])
            if old_summary_text:
                summary_parts.append(f"ПРЕДЫСТОРИЯ (Главы 1-{len(old_chapters)}):\n{old_summary_text[:2000]}...") 
        
        # 2. Актуальный контекст (последние главы)
        if recent_chapters:
            recent_text = "\n\n".join([
                f"Глава {ch.get('title')}: {ch.get('summary')}" 
                for ch in recent_chapters 
                if ch.get('summary')
            ])
            summary_parts.append(f"ПОСЛЕДНИЕ СОБЫТИЯ:\n{recent_text}")
            
        return "\n\n".join(summary_parts)


context_summarizer = ContextSummarizer()
