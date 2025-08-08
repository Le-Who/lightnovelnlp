from __future__ import annotations

from typing import List, Dict, Any

from app.services.gemini_client import gemini_client


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
            print(f"Error summarizing context: {e}")
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
        chapters: List[Dict[str, Any]]
    ) -> str:
        """
        Создает общее саммари проекта на основе всех глав.
        
        Args:
            chapters: Список глав с полями title, summary, original_text
            
        Returns:
            str: Общее саммари проекта
        """
        if not chapters:
            return ""
            
        # Собираем все саммари глав
        summaries = []
        for chapter in chapters:
            if chapter.get('summary'):
                summaries.append(f"Глава '{chapter.get('title', 'Без названия')}': {chapter['summary']}")
        
        if not summaries:
            return ""
            
        combined_summaries = "\n".join(summaries)
        
        prompt = f"""
Ты - эксперт по анализу текстов ранобэ. Создай краткое общее саммари проекта на основе саммари всех глав.

САММАРИ ГЛАВ:
{combined_summaries}

Создай краткое общее саммари проекта (3-4 предложения), включающее:
- Основную сюжетную линию
- Ключевых персонажей и их роли
- Основные локации и мир
- Общий тон и атмосферу произведения

Пиши на русском языке.

ОБЩЕЕ САММАРИ ПРОЕКТА:
"""
        
        try:
            response = self.client.complete(prompt)
            return response.strip()
        except Exception as e:
            print(f"Error creating project summary: {e}")
            return ""


context_summarizer = ContextSummarizer()
