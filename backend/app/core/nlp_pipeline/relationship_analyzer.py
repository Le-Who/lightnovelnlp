from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client
from app.schemas.nlp import RelationshipResponse
from app.models.glossary import GlossaryTerm

logger = logging.getLogger(__name__)


class RelationshipAnalyzer:
    def __init__(self):
        self.client = gemini_client

    def analyze_relationships(
        self, 
        text: str, 
        terms: List[GlossaryTerm],
        project_genre: str = "other"  # Added project_genre
    ) -> List[Dict[str, Any]]:
        """
        Анализирует связи между терминами в тексте.
        
        Args:
            text: Текст для анализа
            terms: Список терминов глоссария
            project_genre: Жанр проекта
            
        Returns:
            List[Dict]: Список связей
        """
        logger.info(f"[REL] Starting relationship analysis for {len(terms)} terms (Genre: {project_genre})")
        
        if len(terms) < 2:
            logger.info("[REL] Less than 2 terms, skipping")
            return []
            
        prompt = self._build_relationship_prompt(text, terms, project_genre)
        logger.info(f"[REL] Built prompt, length: {len(prompt)} chars")
        
        try:
            logger.info("[REL] Calling Gemini API...")
            response = self.client.complete(
                prompt,
                task_type="relationships",
                response_schema=RelationshipResponse
            )
            # logger.info(f"[REL] Gemini returned response of type: {type(response).__name__}")
            result = self._parse_relationship_response(response)
            
            # Filter low confidence results
            filtered_result = [r for r in result if r.get('confidence', 0) >= 70]
            
            logger.info(f"[REL] Parsed {len(result)} relationships, kept {len(filtered_result)} after filtering")
            return filtered_result
        except Exception as e:
            logger.error(f"[REL] Error analyzing relationships: {e}", exc_info=True)
            return []

    def _build_relationship_prompt(self, text: str, terms: List[GlossaryTerm], project_genre: str = "other") -> str:
        """Строит промпт для анализа связей с учетом жанра."""
        
        # Формируем список терминов для анализа
        def cat_label(term):
            cat = getattr(term, "category", None)
            return getattr(cat, "value", cat)
        terms_text = "\n".join([
            f"- {term.source_term} ({cat_label(term)})"
            for term in terms
        ])
        
        genre_instructions = ""
        if project_genre == "xianxia" or project_genre == "wuxia":
             genre_instructions = "В этом жанре важны связи: учитель-ученик (shifu-disciple), соученики, члены одной секты, вражда между кланами."
        elif project_genre == "romance":
             genre_instructions = "Фокусируйся на эмоциональных связях, романтических интересах, семейных узах."
        
        return f"""
Ты - эксперт по анализу текстов ранобэ (Жанр: {project_genre.upper()}). 
Твоя задача: найти ВАЖНЫЕ сюжетные связи между указанными терминами в тексте.

{genre_instructions}

Текст для анализа:
{text}

Термины:
{terms_text}

Инструкции:
1. Ищи только ЯВНЫЕ взаимодействия в тексте. Простое упоминание в одном предложении НЕ является связью.
2. Игнорируй тривиальные связи (например, "видели друг друга").
3. Указывай уровень уверенности (confidence) от 0 до 100.
   - 90-100: Прямое взаимодействие, диалог, явное описание отношений.
   - 70-89: Косвенное взаимодействие, сильный контекстный намек.
   - <70: Слабая связь (такие будут отфильтрованы).
4. Типы связей:
   - friend/ally (друзья, союзники)
   - enemy/rival (враги, соперники)
   - family (семья, родственники)
   - master_student (учитель-ученик, наставник)
   - superior_subordinate (начальник-подчиненный)
   - lovers (возлюбленные)
   - member_of (член организации/секты)
   - other (другое)

Пример вывода (JSON):
{{
    "relationships": [
        {{
            "source_term": "Линь Фэн",
            "target_term": "Ван Линь", 
            "relation_type": "rival",
            "confidence": 95,
            "context": "Линь Фэн открыто бросил вызов Ван Линю на арене."
        }}
    ]
}}

Выведи JSON с найденными связями:"""

    def _parse_relationship_response(self, response: Any) -> List[Dict[str, Any]]:
        """Парсит ответ от Gemini API (Native JSON Mode или Response Schema)."""
        try:
            # Если ответ уже спарсен SDK
            if hasattr(response, 'relationships'):
                return [rel.model_dump() if hasattr(rel, 'model_dump') else rel.dict() 
                        for rel in response.relationships]
            
            # Если это строка (fallback)
            if isinstance(response, str):
                data = json.loads(response)
                if isinstance(data, list):
                    payload = {"relationships": data}
                else:
                    payload = data
                validated = RelationshipResponse.model_validate(payload)
                return [rel.model_dump() for rel in validated.relationships]
            
            # Если это словарь
            if isinstance(response, dict):
                if 'relationships' in response:
                    validated = RelationshipResponse.model_validate(response)
                    return [rel.model_dump() for rel in validated.relationships]
                return response.get('relationships', [])

            error_msg = f"Unexpected response type: {type(response)}"
            logger.error(error_msg)
            return []
            
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.error(f"Error parsing/validating response: {e}")
            logger.debug(f"Raw response type: {type(response)}")
            return []


relationship_analyzer = RelationshipAnalyzer()
