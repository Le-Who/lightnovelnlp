from __future__ import annotations

import json
import logging
import re
from collections import Counter
from typing import Any, Dict, List

import spacy
from spacy.matcher import PhraseMatcher

from app.models.project import ProjectGenre
from app.schemas.nlp import TermExtractionResponse
from app.services.gemini_client import gemini_client

logger = logging.getLogger(__name__)

# ─── Language display names ─────────────────────────────────────────────────
LANG_NAMES = {
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "en": "English",
    "ru": "Russian",
    "other": "Other",
}


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
                    logger.info("Loading spaCy model: en_core_web_sm")
                    self.nlp_models[lang] = spacy.load("en_core_web_sm")
            except OSError:
                logger.error(
                    f"spaCy model for {lang} not found. Please run download_models.py"
                )
                if lang != "en":
                    return self._get_nlp("en")
                raise
        return self.nlp_models[lang]

    def extract_terms(
        self,
        text: str,
        project_genre: ProjectGenre = ProjectGenre.OTHER,
        source_language: str = "en",
        target_language: str = "ru",
        custom_instructions: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract key terms from text via Gemini API.

        Args:
            text: Text to analyze
            project_genre: Project genre for prompt optimization
            source_language: Source language code (zh, ja, ko, en)
            target_language: Target language code (ru, en, etc.)
            custom_instructions: Custom genre instructions

        Returns:
            List[Dict]: Terms with source_term, translated_term, category, context, auto_approve
        """
        prompt = self._build_extraction_prompt(
            text, project_genre, source_language, target_language, custom_instructions
        )

        try:
            response = self.client.complete(
                prompt, task_type="extraction", response_schema=TermExtractionResponse
            )
            logger.info(
                f"Received response from Gemini, type: {type(response).__name__}"
            )
            terms = self._parse_response(response)
            logger.info(f"Extracted {len(terms)} terms from chapter")
            return terms
        except Exception as e:
            logger.error(f"Error extracting terms: {e}", exc_info=True)
            return []

    def count_term_frequency(
        self, text: str, terms: List[str], source_language: str = "en"
    ) -> Dict[str, int]:
        """
        Count term frequency using spaCy PhraseMatcher for supported languages (en, ru)
        to handle lemmatization. Falls back to regex for other languages.
        Uses PhraseMatcher (3-5x faster than Matcher for large terminology lists).
        """
        if not terms or not text:
            return {}

        # For CJK languages, use simple substring count as they don't use spaces
        if source_language in ["zh", "ja", "ko"]:
            return {term: text.count(term) for term in terms}

        # Try to use spaCy PhraseMatcher for lemmatization if supported language
        if source_language in ["en", "ru"]:
            try:
                nlp = self._get_nlp(source_language)

                matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")

                term_patterns = {}
                for term in terms:
                    term_doc = nlp.make_doc(term)
                    for name, proc in nlp.pipeline:
                        if name in ("lemmatizer", "tagger", "attribute_ruler"):
                            term_doc = proc(term_doc)
                    term_patterns[term] = [term_doc]

                for term, patterns in term_patterns.items():
                    matcher.add(term, patterns)

                doc = nlp(text, disable=["ner", "textcat", "parser"])
                matches = matcher(doc)

                counts: Counter[str] = Counter()
                for match_id, start, end in matches:
                    term_name = nlp.vocab.strings[match_id]
                    counts[term_name] += 1

                return {term: counts.get(term, 0) for term in terms}

            except Exception as e:
                logger.warning(
                    f"spaCy frequency count failed for {source_language}: {e}. Fallback to regex."
                )


        text_lower = text.lower()
        frequency = {}

        for term in terms:
            term_lower = term.lower()
            if not term_lower:
                continue
            try:
                pattern = r"\b" + re.escape(term_lower) + r"\b"
                frequency[term] = len(re.findall(pattern, text_lower))
            except Exception:
                frequency[term] = text_lower.count(term_lower)

        return frequency

    def extract_terms_with_frequency(
        self,
        text: str,
        project_genre: ProjectGenre = ProjectGenre.OTHER,
        source_language: str = "en",
        target_language: str = "ru",
        custom_instructions: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Extract terms and count their frequency in the text."""
        terms = self.extract_terms(
            text, project_genre, source_language, target_language, custom_instructions
        )

        term_texts = [term["source_term"] for term in terms]
        frequencies = self.count_term_frequency(text, term_texts, source_language)

        for term in terms:
            term["frequency"] = frequencies.get(term["source_term"], 1)

        return terms

    def _build_extraction_prompt(
        self,
        text: str,
        project_genre: ProjectGenre,
        source_language: str = "en",
        target_language: str = "ru",
        custom_instructions: str | None = None,
    ) -> str:
        """Build XML-delimited extraction prompt with dynamic language support."""

        source_name = LANG_NAMES.get(source_language, source_language)
        target_name = LANG_NAMES.get(target_language, target_language)

        genre_label = "OTHER"
        if isinstance(project_genre, ProjectGenre):
            genre_label = project_genre.value
        elif isinstance(project_genre, str):
            genre_label = project_genre

        if custom_instructions:
            genre_section = f"<genre_context>\nCUSTOM INSTRUCTIONS:\n{custom_instructions}\n</genre_context>"
        else:
            genre_section = f"<genre_context>\n{self._get_genre_instructions(project_genre)}\n</genre_context>"

        language_section = self._get_language_instructions(
            source_language, target_language
        )

        return f"""<system>
You are an expert light novel terminology extractor for {genre_label.upper()} genre.
Extract and translate key terms from {source_name} to {target_name}.
</system>

<language_rules>
{language_section}
</language_rules>

{genre_section}

<categories>
character | location | skill | artifact | organization | cultivation_rank | technique | other
</categories>

<auto_approve_rules>
- character: ALWAYS auto_approve=true
- location/skill/artifact with confidence >= 80: auto_approve=true
- other/organization: auto_approve=false (requires manual review)
</auto_approve_rules>

<example>
{{"terms": [{{"source_term": "Lin Feng", "translated_term": "Линь Фэн", "category": "character", "context": "Main protagonist of the novel", "auto_approve": true, "confidence": 95}}]}}
</example>

<input>
{text}
</input>

Extract only significant, recurring terms. Return JSON:"""

    def _get_language_instructions(
        self, source_language: str, target_language: str = "ru"
    ) -> str:
        """Return language-specific extraction instructions."""
        target_name = LANG_NAMES.get(target_language, target_language)

        base_instructions = {
            "zh": f"""SOURCE: Chinese
- Transliterate names via pinyin → {target_name} script (e.g., 王小明 → Wang Xiaoming)
- Preserve original cultivation rank names alongside translations
- Translate chengyu (成语) preserving meaning""",
            "ja": """SOURCE: Japanese
- Use standard name transliteration (e.g., 田中 → Tanaka)
- Preserve honorifics: -san, -kun, -sama, -sensei
- Translate kanji directly where possible""",
            "ko": """SOURCE: Korean
- Transliterate names (e.g., 김영수 → Kim Yeongsu)
- Preserve polite forms where contextually appropriate
- Translate hangul directly""",
            "en": f"""SOURCE: English
- Transliterate names to {target_name} script
- Translate descriptive names and titles""",
        }
        return base_instructions.get(source_language, base_instructions["en"])

    def _get_genre_instructions(self, genre: ProjectGenre) -> str:
        """Return genre-specific prompt instructions."""

        instructions = {
            ProjectGenre.FANTASY: "GENRE: FANTASY\nFocus: names, magic systems, races, worlds, titles, enchanted items",
            ProjectGenre.SCIFI: "GENRE: SCI-FI\nFocus: technologies, planets, ships, corporations, AI entities",
            ProjectGenre.ROMANCE: "GENRE: ROMANCE\nFocus: character names, date locations, family relationships, emotional terms",
            ProjectGenre.ACTION: "GENRE: ACTION\nFocus: fighters, combat techniques, weapons, factions, battle formations",
            ProjectGenre.MYSTERY: "GENRE: MYSTERY\nFocus: characters, clues, crime scenes, suspects, investigation terms",
            ProjectGenre.HORROR: "GENRE: HORROR\nFocus: monsters, cursed locations, rituals, supernatural entities",
            ProjectGenre.SLICE_OF_LIFE: "GENRE: SLICE OF LIFE\nFocus: families, schools, cafes, festivals, daily-life terms",
            ProjectGenre.ADVENTURE: "GENRE: ADVENTURE\nFocus: travelers, lands, treasures, exploration terms",
            ProjectGenre.WUXIA: "GENRE: WUXIA (武侠)\nFocus: martial arts masters, sects (门派), internal energy (内功), sword/fist techniques, sect ranks, legendary weapons",
            ProjectGenre.XIANXIA: "GENRE: XIANXIA (仙侠) — Immortal Cultivation\nFocus: cultivation ranks (炼气/筑基/金丹/元婴/化神), spiritual roots (灵根), cultivation techniques, artifacts (法宝), sects and clans, heavenly laws (天道), Daoist concepts",
            ProjectGenre.LITRPG: "GENRE: LITRPG\nFocus: character classes, skills and abilities, stats (STR/DEX/INT), levels and XP, items and equipment, quests, system messages",
            ProjectGenre.ISEKAI: "GENRE: ISEKAI (Reincarnation/Transportation)\nFocus: two worlds (old and new), protagonist's unique abilities, local races and factions, magic systems, adventurer ranks",
            ProjectGenre.OTHER: "GENRE: OTHER\nFocus: names, locations, unique terminology, artifacts, organizations",
        }

        try:
            if hasattr(genre, "value"):
                val = str(genre.value).lower()
            else:
                val = str(genre).lower() if genre else "other"
            key = ProjectGenre(val)
        except ValueError:
            key = ProjectGenre.OTHER

        return instructions.get(key, instructions[ProjectGenre.OTHER])

    def _parse_response(self, response: Any) -> List[Dict[str, Any]]:
        """Parse response from Gemini API (Native JSON Mode or Response Schema)."""
        try:
            extracted = []

            # SDK-parsed response
            if hasattr(response, "terms"):
                logger.info(
                    f"Response has 'terms' attribute, extracting {len(response.terms)} terms"
                )
                extracted = [
                    term.model_dump() if hasattr(term, "model_dump") else term.dict()
                    for term in response.terms
                ]

            # String fallback
            elif isinstance(response, str):
                logger.info(f"Response is string, length: {len(response)}")
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
                    if isinstance(data, list):
                        payload = {"terms": data}
                    else:
                        payload = data
                    validated = TermExtractionResponse.model_validate(payload)
                    extracted = [term.model_dump() for term in validated.terms]
                    logger.info(
                        f"Extracted {len(extracted)} terms from string response"
                    )
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {je}")
                    logger.error(
                        f"Failed to parse cleaned response: {clean_response[:200]}..."
                    )
                except Exception as e:
                    logger.error(f"Error validating string response: {e}")

            # Dict response
            elif isinstance(response, dict):
                if "terms" in response:
                    validated = TermExtractionResponse.model_validate(response)
                    extracted = [term.model_dump() for term in validated.terms]
                    logger.info(f"Extracted {len(extracted)} terms from dict response")
                else:
                    extracted = response.get("terms", [])

            else:
                logger.warning(
                    f"Unexpected response type: {type(response)}, value: {str(response)[:200]}"
                )

            if not extracted:
                logger.warning("No terms extracted from response.")
            else:
                logger.info(f"Successfully extracted {len(extracted)} terms")

            # Post-validation: enforce auto_approve rules
            for term in extracted:
                category = term.get("category", "other")
                confidence = term.get("confidence", 0)

                if category == "character":
                    term["auto_approve"] = True
                elif confidence >= 80 and category in ("location", "skill", "artifact"):
                    term["auto_approve"] = True
                elif confidence < 80 or category == "other":
                    term["auto_approve"] = False

            return extracted

        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.error(f"Error parsing/validating response: {e}")
            if hasattr(response, "text"):
                logger.error(f"Raw response text: {response.text}")
            elif isinstance(response, str):
                logger.error(f"Raw response string: {response}")
            return []


term_extractor = TermExtractor()
