from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client
from app.models.glossary import GlossaryTerm, TermStatus

logger = logging.getLogger(__name__)

# ─── Language display names ──────────────────────────────────────────────────
LANG_NAMES = {
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "en": "English", "ru": "Russian", "other": "Other",
}

# ─── Genre-specific style instructions ───────────────────────────────────────
GENRE_STYLES: dict[str, str] = {
    "wuxia": "Style: martial-arts genre. Elevated tone, archaic diction. Preserve technique names and sect titles.",
    "xianxia": "Style: Daoist cultivation genre. Elevated tone, heavenly law references. Preserve cultivation ranks and technique names.",
    "scifi": "Style: science-fiction. Precise technical language, futuristic terminology.",
    "romance": "Style: romance. Emphasis on emotional nuance, character feelings and inner monologues.",
    "litrpg": "Style: LitRPG. Preserve game terminology (stats, skills, levels) and system-message formatting.",
    "isekai": "Style: isekai/reincarnation. Contrast between worlds, highlight protagonist's unique abilities.",
    "horror": "Style: horror. Tense, atmospheric prose. Preserve unsettling descriptors.",
    "mystery": "Style: mystery. Maintain suspense and clue placement. Preserve investigative terminology.",
    "action": "Style: action. Dynamic pacing, impactful fight descriptions.",
    "adventure": "Style: adventure. Vivid world descriptions, sense of exploration.",
    "slice_of_life": "Style: slice of life. Natural, everyday dialogue. Preserve cultural references.",
    "fantasy": "Style: fantasy. Rich world-building terminology. Preserve magic system terms.",
}


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
        target_language: str = "ru",
        custom_genre_instructions: str | None = None,
        previous_context: str | None = None,
    ) -> str:
        """
        Translate text using glossary, context, and genre settings.

        Args:
            text: Original text to translate
            glossary_terms: List of approved glossary terms
            context_summary: Current chapter summary (optional)
            project_summary: Overall project summary (optional)
            relationships: Character relationships (optional)
            genre: Project genre for style adaptation
            source_language: Source language code (zh, ja, ko, en)
            target_language: Target language code (ru, en, etc.)
            custom_genre_instructions: Custom style instructions
            previous_context: End of previous chapter for continuity

        Returns:
            str: Translated text
        """
        prompt = self._build_translation_prompt(
            text, glossary_terms, context_summary, project_summary,
            relationships, genre, source_language, target_language,
            custom_genre_instructions, previous_context,
        )

        try:
            response = self.client.complete(prompt, task_type="translation")
            return response.strip()
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            raise

    def normalize_text(self, text: str) -> str:
        """Normalize text: unify line endings and collapse excessive blank lines."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = [ln.rstrip() for ln in normalized.split("\n")]
        compact_lines: list[str] = []
        prev_empty = False
        for ln in lines:
            if not ln:
                if not prev_empty:
                    compact_lines.append("")
                prev_empty = True
            else:
                compact_lines.append(ln)
                prev_empty = False

        return "\n".join(compact_lines).strip()

    def _build_translation_prompt(
        self,
        text: str,
        glossary_terms: List[GlossaryTerm],
        context_summary: str | None = None,
        project_summary: str | None = None,
        relationships: List[Dict[str, Any]] | None = None,
        genre: str | None = None,
        source_language: str = "en",
        target_language: str = "ru",
        custom_genre_instructions: str | None = None,
        previous_context: str | None = None,
    ) -> str:
        """Build XML-delimited translation prompt with dynamic language support."""

        normalized_text = self.normalize_text(text)

        source_name = LANG_NAMES.get(source_language, source_language)
        target_name = LANG_NAMES.get(target_language, target_language)

        glossary_text = self._format_glossary_for_prompt(glossary_terms) if glossary_terms else "(no approved terms)"

        # ── Style section ─────────────────────────────────────────────────
        style_lines: list[str] = []
        if custom_genre_instructions:
            style_lines.append(custom_genre_instructions)
        elif genre:
            genre_key = str(genre).lower()
            if genre_key in GENRE_STYLES:
                style_lines.append(GENRE_STYLES[genre_key])

        style_section = ""
        if style_lines:
            style_section = f"\n<style>\n{chr(10).join(style_lines)}\n</style>\n"

        # ── Relationships section ─────────────────────────────────────────
        rels_section = ""
        if relationships:
            rels_text = "\n".join([
                f"- {r.get('source_term', r.get('source', '?'))} ↔ {r.get('target_term', r.get('target', '?'))}: "
                f"{r.get('relation_type', r.get('type', '?'))} ({r.get('context', r.get('description', ''))})"
                for r in relationships
            ])
            rels_section = f"\n<character_relationships>\n{rels_text}\n</character_relationships>\n"

        # ── Context sections ──────────────────────────────────────────────
        context_parts: list[str] = []
        if project_summary:
            context_parts.append(f"<project_context>\n{project_summary}\n</project_context>")
        if context_summary:
            context_parts.append(f"<chapter_context>\n{context_summary}\n</chapter_context>")
        if previous_context:
            context_parts.append(f"<previous_chapter>\n...\n{previous_context}\n...\n</previous_chapter>")

        context_section = ""
        if context_parts:
            context_section = "\n<narrative_context>\n" + "\n".join(context_parts) + "\n</narrative_context>\n"

        return f"""<system>
You are a professional literary translator specializing in light novels.
Translate from {source_name} to {target_name}.
Produce natural, publication-quality prose that reads as if originally written in {target_name}.
</system>

<glossary mandatory="true">
{glossary_text}
</glossary>
{rels_section}{context_section}{style_section}
<constraints>
- Use EXACT glossary translations for all matched terms — no synonyms, no alternatives
- Preserve paragraph structure and dialogue formatting
- Maintain emotional tone, narrative voice, and pacing
- Do NOT add translator notes, commentary, or explanations
- Preserve honorifics and cultural markers per language conventions
</constraints>

<input>
{normalized_text}
</input>

Translation:"""

    def _format_glossary_for_prompt(self, glossary_terms: List[GlossaryTerm]) -> str:
        """Format glossary terms grouped by category for the prompt."""
        if not glossary_terms:
            return "No glossary terms."

        categories: dict[str, list[GlossaryTerm]] = {}
        for term in glossary_terms:
            if term.status != TermStatus.APPROVED:
                continue
            cat = getattr(term, "category", None)
            cat = getattr(cat, "value", cat)
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(term)

        lines: list[str] = []
        for category, terms in categories.items():
            label = self._get_category_label(category)
            lines.append(f"{label}:")
            for term in terms:
                lines.append(f"  {term.source_term} → {term.translated_term}")
            lines.append("")

        return "\n".join(lines)

    def _get_category_label(self, category: str) -> str:
        """Return human-readable category labels."""
        labels = {
            "character": "Characters",
            "location": "Locations",
            "skill": "Skills",
            "artifact": "Artifacts",
            "organization": "Organizations",
            "cultivation_rank": "Cultivation Ranks",
            "technique": "Techniques",
            "other": "Other Terms",
        }
        return labels.get(category, category or "Other Terms")


translation_engine = TranslationEngine()
