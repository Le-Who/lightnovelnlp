from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client
from app.schemas.nlp import RelationshipResponse
from app.models.glossary import GlossaryTerm

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "en": "English",
    "ru": "Russian",
    "other": "Other",
}


class RelationshipAnalyzer:
    def __init__(self):
        self.client = gemini_client

    def analyze_relationships(
        self,
        text: str,
        terms: List[GlossaryTerm],
        project_genre: str = "other",
        target_language: str = "ru",
    ) -> List[Dict[str, Any]]:
        """
        Analyze relationships between terms in text.

        Args:
            text: Text to analyze
            terms: List of glossary terms
            project_genre: Project genre
            target_language: Target language for context descriptions

        Returns:
            List[Dict]: List of relationships
        """
        logger.info(
            f"[REL] Starting relationship analysis for {len(terms)} terms (Genre: {project_genre})"
        )

        if len(terms) < 2:
            logger.info("[REL] Less than 2 terms, skipping")
            return []

        prompt = self._build_relationship_prompt(
            text, terms, project_genre, target_language
        )
        logger.info(f"[REL] Built prompt, length: {len(prompt)} chars")

        try:
            logger.info("[REL] Calling Gemini API...")
            response = self.client.complete(
                prompt, task_type="relationships", response_schema=RelationshipResponse
            )
            result = self._parse_relationship_response(response)

            # Filter low confidence results
            filtered_result = [r for r in result if r.get("confidence", 0) >= 70]

            logger.info(
                f"[REL] Parsed {len(result)} relationships, kept {len(filtered_result)} after filtering"
            )
            return filtered_result
        except Exception as e:
            logger.error(f"[REL] Error analyzing relationships: {e}", exc_info=True)
            return []

    def _build_relationship_prompt(
        self,
        text: str,
        terms: List[GlossaryTerm],
        project_genre: str = "other",
        target_language: str = "ru",
    ) -> str:
        """Build XML-delimited relationship analysis prompt."""

        target_name = LANG_NAMES.get(target_language, target_language)

        def cat_label(term):
            cat = getattr(term, "category", None)
            return getattr(cat, "value", cat)

        terms_text = "\n".join(
            [f"- {term.source_term} ({cat_label(term)})" for term in terms]
        )

        genre_block = ""
        genre_lower = project_genre.lower() if project_genre else "other"
        if genre_lower in ("xianxia", "wuxia"):
            genre_block = "<genre_notes>\nImportant relationship types for this genre: master-disciple (shifu), fellow disciples, sect membership, clan rivalries.\n</genre_notes>\n"
        elif genre_lower == "romance":
            genre_block = "<genre_notes>\nFocus on emotional connections, romantic interests, family bonds, love triangles.\n</genre_notes>\n"

        return f"""<system>
You are a narrative relationship analyst specializing in {project_genre.upper()} light novels.
Write context descriptions in {target_name}. Output JSON.
</system>

<task>
Identify SIGNIFICANT plot relationships between the listed terms.
Only report relationships with explicit textual evidence — not mere co-occurrence.
</task>

<constraints>
- Simple mention in the same paragraph is NOT a relationship
- confidence 90-100: direct interaction, dialogue, explicit description
- confidence 70-89: indirect interaction, strong contextual implication
- Below 70: do not include
</constraints>

{genre_block}<terms>
{terms_text}
</terms>

<text>
{text}
</text>

<relationship_types>
friend/ally | enemy/rival | family | master_student | superior_subordinate | lovers | member_of | other
</relationship_types>

<output_schema>
{{
    "relationships": [
        {{
            "source_term": "<term A>",
            "target_term": "<term B>",
            "relation_type": "<type from list above>",
            "confidence": <integer 70-100>,
            "context": "<brief description of the relationship>"
        }}
    ]
}}
</output_schema>

Return JSON with found relationships:"""

    def _parse_relationship_response(self, response: Any) -> List[Dict[str, Any]]:
        """Parse response from Gemini API (Native JSON Mode or Response Schema)."""
        try:
            # SDK-parsed response
            if hasattr(response, "relationships"):
                return [
                    rel.model_dump() if hasattr(rel, "model_dump") else rel.dict()
                    for rel in response.relationships
                ]

            # String fallback
            if isinstance(response, str):
                clean = response.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()

                data = json.loads(clean)
                if isinstance(data, list):
                    payload = {"relationships": data}
                else:
                    payload = data
                validated = RelationshipResponse.model_validate(payload)
                return [rel.model_dump() for rel in validated.relationships]

            # Dict response
            if isinstance(response, dict):
                if "relationships" in response:
                    validated = RelationshipResponse.model_validate(response)
                    return [rel.model_dump() for rel in validated.relationships]
                return response.get("relationships", [])

            logger.error(f"Unexpected response type: {type(response)}")
            return []

        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.error(f"Error parsing/validating response: {e}")
            logger.debug(f"Raw response type: {type(response)}")
            return []


relationship_analyzer = RelationshipAnalyzer()
