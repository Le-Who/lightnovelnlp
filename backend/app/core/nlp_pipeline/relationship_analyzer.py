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
        terms: List[GlossaryTerm]
    ) -> List[Dict[str, Any]]:
        """
        Анализирует связи между терминами в тексте.
        
        Args:
            text: Текст для анализа
            terms: Список терминов глоссария
            
        Returns:
            List[Dict]: Список связей с полями:
                - source_term: исходный термин
                - target_term: целевой термин  
                - relation_type: тип связи
                - confidence: уверенность (0-100)
                - context: контекст связи
        """
        logger.info(f"[REL] Starting relationship analysis for {len(terms)} terms")
        
        if len(terms) < 2:
            logger.info("[REL] Less than 2 terms, skipping")
            return []  # Нужно минимум 2 термина для анализа связей
            
        prompt = self._build_relationship_prompt(text, terms)
        logger.info(f"[REL] Built prompt, length: {len(prompt)} chars")
        
        try:
            logger.info("[REL] Calling Gemini API...")
            # Используем новую поддержку response_schema в GeminiClient
            response = self.client.complete(
                prompt,
                # max_tokens removed to use default (8192 for Flash)
                response_schema=RelationshipResponse
            )
            logger.info(f"[REL] Gemini returned response of type: {type(response).__name__}")
            result = self._parse_relationship_response(response)
            logger.info(f"[REL] Parsed {len(result)} relationships")
            return result
        except Exception as e:
            logger.error(f"[REL] Error analyzing relationships: {e}", exc_info=True)
            return []

    def _build_relationship_prompt(self, text: str, terms: List[GlossaryTerm]) -> str:
        """Строит промпт для анализа связей."""
        
        # Формируем список терминов для анализа
        def cat_label(term):
            cat = getattr(term, "category", None)
            return getattr(cat, "value", cat)
        terms_text = "\n".join([
            f"- {term.source_term} ({cat_label(term)})"
            for term in terms
        ])
        
        return f"""
Ты - эксперт по анализу текстов ранобэ. Проанализируй связи между терминами в следующем тексте.

Текст для анализа:
{text}

Термины для анализа связей:
{terms_text}

Проанализируй все возможные связи между этими терминами. Типы связей могут быть:
- friend/enemy (друзья/враги)
- family (семейные отношения)
- location (место действия/проживания)
- skill_related (связанные умения)
- artifact_owner (владелец артефакта)
- teacher_student (учитель-ученик)
- rival (соперники)
- ally (союзники)
- other (другие связи)

Ответ должен быть в формате JSON:
{{
    "relationships": [
        {{
            "source_term": "первый термин",
            "target_term": "второй термин", 
            "relation_type": "тип связи",
            "confidence": 85,
            "context": "краткое описание связи на основе текста"
        }}
    ]
}}

Важно:
- Анализируй только связи, которые явно упоминаются в тексте
- Указывай уверенность от 0 до 100
- В контексте опиши, на чем основана связь
- Не создавай связи, если их нет в тексте
"""

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
