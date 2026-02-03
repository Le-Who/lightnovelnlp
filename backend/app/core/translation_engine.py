from __future__ import annotations

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.gemini_client import gemini_client
from app.models.glossary import GlossaryTerm, TermStatus

logger = logging.getLogger(__name__)


class TranslationEngine:
    def __init__(self):
        self.client = gemini_client

    def translate_with_glossary(
        self, 
        text: str, 
        glossary_terms: List[GlossaryTerm],
        context_summary: str | None = None,
        project_summary: str | None = None,
        relationships: List[Dict[str, Any]] | None = None,
        genre: str | None = None,
        source_language: str = "en",
        custom_genre_instructions: str | None = None
    ) -> str:
        """
        Переводит текст с использованием утвержденного глоссария и контекста.
        
        Args:
            text: Оригинальный текст для перевода
            glossary_terms: Список утвержденных терминов глоссария
            context_summary: Саммари текущей главы (опционально)
            project_summary: Общее саммари проекта (опционально)
            relationships: Список связей между терминами (опционально)
            genre: Жанр проекта для настройки стиля
            source_language: Язык оригинала (zh, ja, ko, en)
            custom_genre_instructions: Кастомные инструкции для жанра/стиля
            
        Returns:
            str: Переведенный текст
        """
        prompt = self._build_translation_prompt(
            text, glossary_terms, context_summary, project_summary, 
            relationships, genre, source_language, custom_genre_instructions
        )
        
        try:
            response = self.client.complete(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            raise

    def _build_translation_prompt(
        self, 
        text: str, 
        glossary_terms: List[GlossaryTerm],
        context_summary: str | None = None,
        project_summary: str | None = None,
        relationships: List[Dict[str, Any]] | None = None,
        genre: str | None = None,
        source_language: str = "en",
        custom_genre_instructions: str | None = None
    ) -> str:
        """Строит промпт для перевода с учетом глоссария и контекста."""
        # Нормализуем входной текст: приводим переводы строк к \n и убираем лишние пустые
        normalized = text.replace("\r\n", "\n")
        lines = [ln.rstrip() for ln in normalized.split("\n")]
        # Оставляем максимум одну пустую строку подряд
        compact_lines = []
        prev_empty = False
        for ln in lines:
            if ln == "":
                if not prev_empty:
                    compact_lines.append("")
                prev_empty = True
            else:
                compact_lines.append(ln)
                prev_empty = False
        normalized_text = "\n".join(compact_lines)

        # Формируем глоссарий для промпта
        glossary_text = self._format_glossary_for_prompt(glossary_terms) if glossary_terms else "(нет утвержденных терминов)"
        
        # Определение языка
        lang_names = {"zh": "китайского", "ja": "японского", "ko": "корейского", "en": "английского"}
        source_lang_name = lang_names.get(source_language, "английского")
        
        genre_instruction = ""
        if custom_genre_instructions:
            genre_instruction = f"Стиль: {custom_genre_instructions}"
        elif genre:
            genre = str(genre).lower()
            if "wuxia" in genre:
                genre_instruction = "Стиль: Используй терминологию ушу, возвышенный тон, архаизмы. Сохраняй названия техник."
            elif "xianxia" in genre:
                genre_instruction = "Стиль: Даосская терминология культивации, возвышенный тон, небесные законы."
            elif "scifi" in genre or "sci-fi" in genre:
                genre_instruction = "Стиль: Технически точный язык, футуристическая терминология."
            elif "romance" in genre:
                genre_instruction = "Стиль: Акцент на эмоциональные оттенки и чувства персонажей."
            elif "litrpg" in genre:
                genre_instruction = "Стиль: Игровая терминология, четкие описания навыков и статов."
            elif "isekai" in genre:
                genre_instruction = "Стиль: Контраст миров, уникальные способности протагониста."
        
        # Базовый промпт
        prompt = f"""Ты - профессиональный переводчик ранобэ с {source_lang_name} на русский. 
Цель: Литературный перевод, сохраняющий стиль оригинала.
{genre_instruction}

ГЛОССАРИЙ (ОБЯЗАТЕЛЬНО использовать эти переводы):
{glossary_text}
"""
        # Добавляем связи между терминами
        if relationships:
            rels_text = "\n".join([
                f"- {r.get('source_term', r.get('source', '?'))} и {r.get('target_term', r.get('target', '?'))}: {r.get('relation_type', r.get('type', '?'))} ({r.get('context', r.get('description', ''))})"
                for r in relationships
            ])
            prompt += f"""
СВЯЗИ МЕЖДУ ПЕРСОНАЖАМИ (учитывать при выборе тона диалогов):
{rels_text}

"""
        
        # Добавляем общее саммари проекта, если есть
        if project_summary:
            prompt += f"""
ОБЩИЙ КОНТЕКСТ ПРОИЗВЕДЕНИЯ:
{project_summary}

"""
        
        # Добавляем контекст текущей главы, если есть
        if context_summary:
            prompt += f"""
КОНТЕКСТ ТЕКУЩЕЙ ГЛАВЫ:
{context_summary}

"""
        
        prompt += f"""
ТЕКСТ ДЛЯ ПЕРЕВОДА:
{normalized_text}

ИНСТРУКЦИИ:
1. Переведи текст на русский язык, сохраняя стиль и атмосферу
2. ОБЯЗАТЕЛЬНО используй точные переводы из глоссария для всех терминов
3. Если в тексте встречается термин из глоссария, используй ТОЛЬКО указанный перевод
4. Сохраняй структуру предложений и абзацев
5. Переводи естественно, как будто это оригинальный русский текст
6. Учитывай контекст произведения и главы для более точного перевода
7. Не добавляй комментарии или пояснения в перевод
8. Сохраняй эмоциональную окраску и тон повествования

ПЕРЕВОД:
"""
        
        return prompt

    def _format_glossary_for_prompt(self, glossary_terms: List[GlossaryTerm]) -> str:
        """Форматирует глоссарий для включения в промпт."""
        if not glossary_terms:
            return "Глоссарий пуст - переводи как обычно."
        
        # Группируем по категориям для лучшей читаемости
        categories = {}
        for term in glossary_terms:
            if term.status != TermStatus.APPROVED:
                continue  # Используем только утвержденные термины
                
            cat = getattr(term, "category", None)
            cat = getattr(cat, "value", cat)
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(term)
        
        # Формируем текст глоссария
        glossary_lines = []
        for category, terms in categories.items():
            category_label = self._get_category_label(category)
            glossary_lines.append(f"{category_label}:")
            
            for term in terms:
                glossary_lines.append(f"  {term.source_term} → {term.translated_term}")
            
            glossary_lines.append("")  # Пустая строка между категориями
        
        return "\n".join(glossary_lines)

    def _get_category_label(self, category: str) -> str:
        """Возвращает русское название категории."""
        labels = {
            "character": "Персонажи",
            "location": "Локации", 
            "skill": "Умения",
            "artifact": "Артефакты",
            "other": "Другие термины"
        }
        return labels.get(category, category)


translation_engine = TranslationEngine()
