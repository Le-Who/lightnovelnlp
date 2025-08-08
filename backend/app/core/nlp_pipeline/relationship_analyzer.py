from __future__ import annotations

import json
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client
from app.models.glossary import GlossaryTerm


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
        if len(terms) < 2:
            return []  # Нужно минимум 2 термина для анализа связей
            
        prompt = self._build_relationship_prompt(text, terms)
        
        try:
            response = self.client.complete(prompt)
            return self._parse_relationship_response(response)
        except Exception as e:
            print(f"Error analyzing relationships: {e}")
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

    def _parse_relationship_response(self, response: str) -> List[Dict[str, Any]]:
        """Парсит JSON-ответ от Gemini API."""
        try:
            # Ищем JSON в ответе
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start == -1 or end == 0:
                return []
                
            json_str = response[start:end]
            data = json.loads(json_str)
            
            return data.get('relationships', [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing relationship response: {e}")
            print(f"Raw response: {response}")
            return []


relationship_analyzer = RelationshipAnalyzer()
