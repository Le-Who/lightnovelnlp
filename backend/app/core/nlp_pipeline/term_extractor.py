from __future__ import annotations

import json
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client


class TermExtractor:
    def __init__(self):
        self.client = gemini_client

    def extract_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Извлекает ключевые термины из текста с помощью Gemini API.
        
        Returns:
            List[Dict]: Список терминов с полями:
                - source_term: оригинальный термин
                - translated_term: предложенный перевод
                - category: категория (character, location, skill, artifact, other)
                - context: контекст извлечения
        """
        prompt = self._build_extraction_prompt(text)
        
        try:
            response = self.client.complete(prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"Error extracting terms: {e}")
            return []

    def _build_extraction_prompt(self, text: str) -> str:
        return f"""
Ты - эксперт по анализу текстов ранобэ. Проанализируй следующий текст и извлеки все важные термины, которые нужно переводить консистентно.

Текст для анализа:
{text}

Извлеки следующие типы терминов:
1. Имена персонажей (character)
2. Названия локаций (location) 
3. Названия умений/способностей (skill)
4. Названия артефактов/предметов (artifact)
5. Другие важные термины (other)

Для каждого термина предложи подходящий перевод на русский язык.

Ответ должен быть в формате JSON:
{{
    "terms": [
        {{
            "source_term": "оригинальный термин",
            "translated_term": "перевод на русский",
            "category": "character|location|skill|artifact|other",
            "context": "краткий контекст извлечения (1-2 предложения)"
        }}
    ]
}}

Важно:
- Извлекай только значимые термины, которые встречаются в тексте
- Предлагай естественные переводы на русский
- Указывай точную категорию
- В контексте опиши, где и как используется термин
"""

    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Парсит JSON-ответ от Gemini API."""
        try:
            # Ищем JSON в ответе
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start == -1 or end == 0:
                return []
                
            json_str = response[start:end]
            data = json.loads(json_str)
            
            return data.get('terms', [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response}")
            return []


term_extractor = TermExtractor()
