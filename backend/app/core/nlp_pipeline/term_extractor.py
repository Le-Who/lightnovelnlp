from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client
from app.models.project import ProjectGenre
from app.schemas.nlp import TermExtractionResponse

logger = logging.getLogger(__name__)



import spacy
from spacy.matcher import Matcher
from collections import Counter

class TermExtractor:
    def __init__(self):
        self.client = gemini_client
        self.nlp_models = {}

    def _get_nlp(self, lang: str):
        """Lazy load spaCy models to avoid startup overhead."""
        if lang not in self.nlp_models:
            try:
                if lang == "ru":
                    logger.info("Loading spaCy model: ru_core_news_sm")
                    self.nlp_models[lang] = spacy.load("ru_core_news_sm")
                else:
                    # Default to English for everything else for now, or add specific models
                    logger.info("Loading spaCy model: en_core_web_sm")
                    self.nlp_models[lang] = spacy.load("en_core_web_sm")
            except OSError:
                logger.error(f"spaCy model for {lang} not found. Please run download_models.py")
                # Fallback to English or blank
                if lang != "en":
                     return self._get_nlp("en")
                raise
        return self.nlp_models[lang]

    def extract_terms(
        self, 
        text: str, 
        project_genre: ProjectGenre = ProjectGenre.OTHER,
        source_language: str = "en",
        custom_instructions: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Извлекает ключевые термины из текста с помощью Gemini API.
        
        Args:
            text: Текст для анализа
            project_genre: Жанр проекта для оптимизации промптов
            source_language: Язык оригинала (zh, ja, ko, en)
            custom_instructions: Кастомные инструкции для жанра
            
        Returns:
            List[Dict]: Список терминов с полями:
                - source_term: оригинальный термин
                - translated_term: предложенный перевод
                - category: категория (character, location, skill, artifact, other)
                - context: контекст извлечения
                - auto_approve: флаг автоматического утверждения
        """
        # JSON Mode configuration with response_schema
        prompt = self._build_extraction_prompt(text, project_genre, source_language, custom_instructions)
        
        try:
            # Используем новую поддержку response_schema в GeminiClient
            response = self.client.complete(
                prompt, 
                max_tokens=8192,  # Увеличиваем лимит для больших глав
                response_schema=TermExtractionResponse
            )
            logger.info(f"Received response from Gemini, type: {type(response).__name__}")
            terms = self._parse_response(response)
            logger.info(f"Extracted {len(terms)} terms from chapter")
            return terms
        except Exception as e:
            logger.error(f"Error extracting terms: {e}", exc_info=True)
            return []

    def count_term_frequency(self, text: str, terms: List[str], source_language: str = "en") -> Dict[str, int]:
        """
        Count term frequency using spaCy Matcher for supported languages (en, ru)
        to handle lemmatization (e.g., "cats" -> "cat", "Кошки" -> "Кошка").
        Falls back to regex for other languages or if spaCy fails.
        
        Args:
            text: Text to analyze
            terms: List of terms to count
            source_language: Language code (ru, en, etc.)
            
        Returns:
            Dict[str, int]: Dictionary {term: frequency}
        """
        if not terms or not text:
            return {}
        
        # For CJK languages, use simple substring count as they don't use spaces
        if source_language in ["zh", "ja", "ko"]:
             return {term: text.count(term) for term in terms}

        # Try to use spaCy for lemmatization if supported language
        if source_language in ["en", "ru"]:
            try:
                nlp = self._get_nlp(source_language)
                matcher = Matcher(nlp.vocab)

                # Create patterns for each term based on lemmas
                # Use nlp.pipe for efficiency, disabling unnecessary components
                # We need 'tagger' and 'attribute_ruler' for accurate lemmatization usually,
                # but 'ner' and 'parser' can be disabled.
                # However, _get_nlp loads 'en_core_web_sm' which has these.
                # Disabling them for term processing speeds it up.
                term_docs = list(nlp.pipe(terms, disable=["ner", "parser", "textcat"]))

                for term, term_doc in zip(terms, term_docs):
                    if not term_doc:
                        continue
                    # Create a pattern matching the sequence of lemmas
                    pattern = [{"LEMMA": token.lemma_.lower()} for token in term_doc]
                    matcher.add(term, [pattern])

                # Process the text
                # We need lemmatization, so we keep tagger/attribute_ruler
                # Optimize: Disable parser as it's not needed for basic lemmatization (~30% speedup)
                doc = nlp(text, disable=["ner", "textcat", "parser"])

                matches = matcher(doc)

                # Count matches
                # matches is a list of (match_id, start, end)
                # match_id is the hash of the term string
                counts = Counter()
                for match_id, start, end in matches:
                    term = nlp.vocab.strings[match_id]
                    counts[term] += 1

                # Ensure all terms are in result (even with 0 count)
                return {term: counts[term] for term in terms}

            except Exception as e:
                logger.warning(f"spaCy frequency count failed for {source_language}: {e}. Fallback to regex.")
                # Fallthrough to regex

        import re
        text_lower = text.lower()
        frequency = {}

        for term in terms:
            term_lower = term.lower()
            if not term_lower:
                continue
                
            try:
                # Use word boundaries for Latin/Cyrillic
                pattern = r'\b' + re.escape(term_lower) + r'\b'
                frequency[term] = len(re.findall(pattern, text_lower))
            except Exception:
                 # Fallback to simple count on regex error
                 frequency[term] = text_lower.count(term_lower)

        return frequency

    def extract_terms_with_frequency(
        self, 
        text: str, 
        project_genre: ProjectGenre = ProjectGenre.OTHER,
        source_language: str = "en",
        custom_instructions: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Извлекает термины и подсчитывает их частоту встречаемости.
        
        Args:
            text: Текст для анализа
            project_genre: Жанр проекта для оптимизации промптов
            source_language: Язык оригинала
            
        Returns:
            List[Dict]: Список терминов с дополнительным полем frequency
        """
        # Извлекаем термины
        terms = self.extract_terms(text, project_genre, source_language, custom_instructions)
        
        # Подсчитываем частоту для каждого термина
        term_texts = [term["source_term"] for term in terms]
        frequencies = self.count_term_frequency(text, term_texts, source_language)
        
        # Добавляем частоту к каждому термину
        for term in terms:
            term["frequency"] = frequencies.get(term["source_term"], 1)
        
        return terms

    def _build_extraction_prompt(
        self, 
        text: str, 
        project_genre: ProjectGenre,
        source_language: str = "en",
        custom_instructions: str | None = None
    ) -> str:
        """Строит оптимизированный промпт для извлечения терминов."""
        
        # Жанр-специфичные инструкции (или кастомные)
        if custom_instructions:
            genre_instructions = f"КАСТОМНЫЕ ИНСТРУКЦИИ:\n{custom_instructions}"
        else:
            genre_instructions = self._get_genre_instructions(project_genre)
        
        # Язык-специфичные инструкции
        language_instructions = self._get_language_instructions(source_language)
        
        # Получаем строковое представление жанра
        genre_label = "OTHER"
        if isinstance(project_genre, ProjectGenre):
            genre_label = project_genre.value
        elif isinstance(project_genre, str):
            genre_label = project_genre
        
        # Оптимизированный промпт с few-shot примером
        return f"""Извлеки термины из текста ранобэ ({str(genre_label).upper()}).

{language_instructions}
{genre_instructions}

ПРИМЕР ВЫВОДА:
{{"terms": [{{"source_term": "Lin Feng", "translated_term": "Линь Фэн", "category": "character", "context": "Главный герой произведения", "auto_approve": true, "confidence": 95}}]}}

ТЕКСТ:
{text}

КАТЕГОРИИ: character (персонажи), location (локации), skill (умения), artifact (артефакты), organization (организации), cultivation_rank (ранги культивации), technique (техники), other.

ПРАВИЛА auto_approve:
- character: ВСЕГДА true
- location/skill/artifact с confidence >= 80: true
- other/organization: false (ручная проверка)

Извлекай только значимые термины. JSON output:"""

    def _get_language_instructions(self, source_language: str) -> str:
        """Возвращает язык-специфичные инструкции."""
        instructions = {
            "zh": """ЯЗЫК: КИТАЙСКИЙ
- Транслитерируй имена пиньинем → кириллицей (王小明 → Ван Сяомин)
- Сохраняй оригинальные названия рангов культивации
- Переводи чэнъюй (成语) с сохранением смысла""",
            
            "ja": """ЯЗЫК: ЯПОНСКИЙ
- Используй стандартную транслитерацию имён (田中 → Танака)
- Сохраняй honorfics: -сан, -кун, -сама, -сенсей
- Переводи кандзи напрямую где возможно""",
            
            "ko": """ЯЗЫК: КОРЕЙСКИЙ
- Транслитерируй имена (김영수 → Ким Ёнсу)
- Сохраняй вежливые формы где уместно
- Переводи хангыль напрямую""",
            
            "en": """ЯЗЫК: АНГЛИЙСКИЙ
- Транскрибируй имена кириллицей
- Переводи описательные названия"""
        }
        return instructions.get(source_language, instructions["en"])

    def _get_genre_instructions(self, genre: ProjectGenre) -> str:
        """Возвращает жанр-специфичные инструкции для промпта."""
        
        instructions = {
            ProjectGenre.FANTASY: """ЖАНР: ФЭНТЕЗИ
Фокус: имена, магия, расы, миры, титулы""",
            
            ProjectGenre.SCIFI: """ЖАНР: SCI-FI
Фокус: технологии, планеты, корабли, корпорации""",
            
            ProjectGenre.ROMANCE: """ЖАНР: РОМАНТИКА
Фокус: имена героев, места свиданий, семейные отношения""",
            
            ProjectGenre.ACTION: """ЖАНР: БОЕВИК
Фокус: бойцы, техники, оружие, группировки""",
            
            ProjectGenre.MYSTERY: """ЖАНР: ДЕТЕКТИВ
Фокус: персонажи, улики, места преступлений""",
            
            ProjectGenre.HORROR: """ЖАНР: УЖАСЫ
Фокус: монстры, проклятые места, ритуалы""",
            
            ProjectGenre.SLICE_OF_LIFE: """ЖАНР: ПОВСЕДНЕВНОСТЬ
Фокус: семьи, школы, кафе, праздники""",
            
            ProjectGenre.ADVENTURE: """ЖАНР: ПРИКЛЮЧЕНИЯ
Фокус: путешественники, земли, сокровища""",
            
            ProjectGenre.WUXIA: """ЖАНР: УСЯ (武侠)
Фокус: мастера боевых искусств, секты (门派), внутренняя энергия (内功), техники меча/кулака, звания в сектах, легендарное оружие""",
            
            ProjectGenre.XIANXIA: """ЖАНР: СЯНЬСИЯ (仙侠) — КУЛЬТИВАЦИЯ БЕССМЕРТИЯ
Фокус: ранги культивации (炼气/筑基/金丹/元婴/化神), духовные корни (灵根), техники культивации, артефакты (法宝), секты и кланы, небесные законы (天道), даосские концепции""",
            
            ProjectGenre.LITRPG: """ЖАНР: ЛИТРПГ
Фокус: классы персонажей, навыки и умения, характеристики (STR/DEX/INT), уровни и опыт, предметы и экипировка, квесты, системные сообщения""",
            
            ProjectGenre.ISEKAI: """ЖАНР: ИСЕКАЙ (ПОПАДАНЦЫ)
Фокус: два мира (старый и новый), уникальные способности протагониста, местные расы и фракции, системы магии, ранги авантюристов""",
            
            ProjectGenre.OTHER: """ЖАНР: ДРУГОЙ
Фокус: имена, локации, уникальные термины, артефакты, организации"""
        }
        
        # Нормализация жанра (case-insensitive)
        try:
            if hasattr(genre, "value"):
                val = str(genre.value).lower()
            else:
                val = str(genre).lower() if genre else "other"

            # Пробуем найти соответствующий Enum
            key = ProjectGenre(val)
        except ValueError:
            key = ProjectGenre.OTHER
            
        return instructions.get(key, instructions[ProjectGenre.OTHER])

    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        """Парсит ответ от Gemini API (Native JSON Mode или Response Schema)."""
        try:
            results = []
            extracted = []
            
            # Debug: log response type and content preview
            logger.info(f"Parsing response of type: {type(response).__name__}")
            
            # Если ответ уже спарсен SDK
            if hasattr(response, 'terms'):
                logger.info(f"Response has 'terms' attribute, extracting {len(response.terms)} terms")
                extracted = [term.model_dump() if hasattr(term, 'model_dump') else term.dict() for term in response.terms]
            
            # Если это строка (fallback)
            elif isinstance(response, str):
                logger.info(f"Response is string, length: {len(response)}")
                
                # CLEANUP: Remove Markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.startswith("```"):
                     clean_response = clean_response[3:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                try:
                    data = json.loads(clean_response)
                    logger.info(f"JSON parsed successfully, type: {type(data).__name__}")
                    if isinstance(data, list):
                        payload = {"terms": data}
                    else:
                        payload = data
                    validated = TermExtractionResponse.model_validate(payload)
                    extracted = [term.model_dump() for term in validated.terms]
                    logger.info(f"Extracted {len(extracted)} terms from string response")
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {je}")
                    logger.error(f"Failed to parse cleaned response: {clean_response[:200]}...")
                except Exception as e:
                    logger.error(f"Error validating string response: {e}")
            
            # Если это словарь
            elif isinstance(response, dict):
                logger.info(f"Response is dict with keys: {list(response.keys())}")
                if 'terms' in response:
                    validated = TermExtractionResponse.model_validate(response)
                    extracted = [term.model_dump() for term in validated.terms]
                    logger.info(f"Extracted {len(extracted)} terms from dict response")
                else:
                    extracted = response.get('terms', [])
                    logger.warning(f"Dict has no 'terms' key, got empty list")
            
            else:
                logger.warning(f"Unexpected response type: {type(response)}, value: {str(response)[:200]}")
            
            if not extracted:
                logger.warning("No terms extracted from response.")
                if hasattr(response, 'text'):
                     logger.warning(f"Raw response text: {response.text}")
                elif isinstance(response, str):
                     logger.warning(f"Raw response (first 500 chars): {response[:500]}")
            else:
                logger.info(f"Successfully extracted {len(extracted)} terms")
            
            # Post-validation: enforce auto_approve rules
            for term in extracted:
                category = term.get("category", "other")
                confidence = term.get("confidence", 0)
                
                # Characters are ALWAYS auto-approved
                if category == "character":
                    term["auto_approve"] = True
                # High confidence (>= 80) terms in key categories get auto-approved
                elif confidence >= 80 and category in ("location", "skill", "artifact"):
                    term["auto_approve"] = True
                # Low confidence or 'other' category requires manual review
                elif confidence < 80 or category == "other":
                    term["auto_approve"] = False
            
            return extracted

        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.error(f"Error parsing/validating response: {e}")
            if hasattr(response, 'text'):
                 logger.error(f"Raw response text: {response.text}")
            elif isinstance(response, str):
                 logger.error(f"Raw response string: {response}")
            return []



term_extractor = TermExtractor()
