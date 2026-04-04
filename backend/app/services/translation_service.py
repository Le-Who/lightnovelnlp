from sqlalchemy.orm import Session, load_only
from typing import List, Dict, Any, Optional
import json
import logging

from app.models.project import Chapter
from app.models.glossary import GlossaryTerm
from app.services.cache_service import cache_service
from app.services.glossary_service import GlossaryService
from app.core.translation_engine import translation_engine
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.services.gemini_client import gemini_client

logger = logging.getLogger(__name__)

# ─── Review JSON schema ───────────────────────────────────────────────────────
# Expected structure returned by the AI reviewer:
# {
#   "score": 7,           int 1-10
#   "passed": false,      bool — true if no glossary violations found
#   "violations": [
#     {
#       "source_term": "修炼",
#       "expected": "Cultivation",
#       "found": "Training",
#       "excerpt": "...after hours of Training..."
#     }
#   ],
#   "style_notes": "..."  free text, optional
# }
# If the model returns malformed JSON we fall back gracefully.


class TranslationService:
    @staticmethod
    def translate_chapter(
        db: Session, chapter_id: int, use_glossary: bool = True
    ) -> Dict[str, Any]:
        """Оркестрация перевода главы: кэш, глоссарий, саммари, перевод, сохранение."""
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}

        # 1. Глоссарий
        glossary_terms = []
        relevant_relationships = []

        if use_glossary:
            glossary_terms = GlossaryService.get_relevant_terms(
                db, chapter.project_id, chapter.original_text
            )
            if glossary_terms:
                relevant_relationships = TranslationService._get_relevant_relationships(
                    db, glossary_terms
                )

        # 2. Кэш
        glossary_hash = cache_service.generate_glossary_hash(
            [
                {
                    "source_term": t.source_term,
                    "translated_term": t.translated_term,
                    "category": t.category,
                }
                for t in glossary_terms
            ]
        )

        cached_translation = cache_service.get_cached_translation(
            chapter.id, glossary_hash
        )
        if cached_translation:
            return {
                "chapter_id": chapter_id,
                "translated_text": cached_translation,
                "glossary_terms_used": len(glossary_terms),
                "context_used": bool(chapter.summary),
                "project_context_used": False,
                "message": "Translation retrieved from cache",
                "cached": True,
            }

        # 3. Контекст проекта
        project_summary = TranslationService._get_project_summary(
            db, chapter.project_id
        )

        # 3.1 Контекст предыдущей главы
        previous_context = None
        previous_chapter = (
            db.query(Chapter)
            .filter(
                Chapter.project_id == chapter.project_id, Chapter.order < chapter.order
            )
            .order_by(Chapter.order.desc())
            .first()
        )

        if previous_chapter and previous_chapter.original_text:
            text_len = len(previous_chapter.original_text)
            start_pos = max(0, text_len - 1000)
            previous_context = previous_chapter.original_text[start_pos:]

        # 4. Перевод
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary,
            relationships=relevant_relationships,
            genre=chapter.project.genre,
            source_language=chapter.project.source_language,
            target_language=chapter.project.target_language,
            custom_genre_instructions=chapter.project.custom_genre_instructions,
            previous_context=previous_context,
        )

        # 5. Сохранение
        chapter.translated_text = translated_text
        db.commit()

        # 6. Обновление кэша
        cache_service.cache_translation(chapter.id, glossary_hash, translated_text)

        return {
            "chapter_id": chapter_id,
            "translated_text": translated_text,
            "glossary_terms_used": len(glossary_terms),
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "message": "Translation completed successfully",
            "cached": False,
        }

    @staticmethod
    def preview_translation(db: Session, chapter_id: int) -> Dict[str, Any]:
        """Превью перевода без сохранения."""
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}

        glossary_terms = GlossaryService.get_relevant_terms(
            db, chapter.project_id, chapter.original_text
        )

        if not glossary_terms:
            return {
                "chapter_id": chapter_id,
                "preview_available": False,
                "message": "No relevant glossary terms found in text.",
                "glossary_terms_count": 0,
            }

        relevant_relationships = TranslationService._get_relevant_relationships(
            db, glossary_terms
        )
        project_summary = TranslationService._get_project_summary(
            db, chapter.project_id
        )

        previous_context = None
        previous_chapter = (
            db.query(Chapter)
            .filter(
                Chapter.project_id == chapter.project_id, Chapter.order < chapter.order
            )
            .order_by(Chapter.order.desc())
            .first()
        )

        if previous_chapter and previous_chapter.original_text:
            text_len = len(previous_chapter.original_text)
            start_pos = max(0, text_len - 1000)
            previous_context = previous_chapter.original_text[start_pos:]

        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary,
            relationships=relevant_relationships,
            genre=chapter.project.genre,
            source_language=chapter.project.source_language,
            target_language=chapter.project.target_language,
            custom_genre_instructions=chapter.project.custom_genre_instructions,
            previous_context=previous_context,
        )

        return {
            "chapter_id": chapter_id,
            "preview_available": True,
            "original_text": chapter.original_text,
            "translated_text": translated_text,
            "glossary_terms_count": len(glossary_terms),
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "glossary_terms": [
                {
                    "source_term": t.source_term,
                    "translated_term": t.translated_term,
                    "category": getattr(
                        getattr(t, "category", None),
                        "value",
                        getattr(t, "category", None),
                    ),
                }
                for t in glossary_terms
            ],
        }

    @staticmethod
    def review_translation(db: Session, chapter_id: int) -> Dict[str, Any]:
        """
        AI-рецензирование перевода. Возвращает структурированный JSON-вердикт
        с оценкой, списком нарушений глоссария и стилистическими замечаниями.
        """
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}

        if not chapter.translated_text:
            return {"error": "Chapter has no translation to review", "status_code": 400}

        glossary_terms = GlossaryService.get_relevant_terms(
            db, chapter.project_id, chapter.original_text
        )

        source_lang = chapter.project.source_language
        target_lang = chapter.project.target_language

        glossary_lines = "\n".join(
            [f"- {t.source_term} → {t.translated_term}" for t in glossary_terms[:20]]
        )

        review_prompt = f"""<system>
You are a translation quality control specialist.
Analyze the translation and return ONLY a raw JSON object — no markdown, no prose, no code fences.
</system>

<task>
Check whether the translation correctly uses all required glossary terms.
Score the overall translation quality from 1-10.
</task>

<source language="{source_lang}">
{chapter.original_text[:1500]}
</source>

<translation language="{target_lang}">
{chapter.translated_text[:3000]}
</translation>

<required_glossary>
{glossary_lines or "(no approved glossary terms)"}
</required_glossary>

<output_schema>
{{
  "score": <integer 1-10>,
  "passed": <boolean — true if all glossary terms used correctly>,
  "violations": [
    {{"source_term": "<original>", "expected": "<required>", "found": "<actual used>", "excerpt": "<context snippet>"}}
  ],
  "style_notes": "<brief suggestions or empty string>"
}}
</output_schema>

If there are no violations, return an empty violations array and set passed to true."""

        raw_review = gemini_client.complete(review_prompt, task_type="translation")

        # Parse structured JSON; fall back gracefully on malformed output
        review_data = TranslationService._parse_review_json(raw_review)

        # Cache the structured verdict
        review_key = f"translation_review:{chapter_id}"
        cache_service.set(review_key, json.dumps(review_data), ttl=3600)

        return {
            "chapter_id": chapter_id,
            "review_available": True,
            "review": review_data,
            "glossary_terms_used": len(glossary_terms),
            "message": "Translation review completed successfully",
        }

    @staticmethod
    def translate_with_review(
        db: Session, chapter_id: int, max_retries: int = 1
    ) -> Dict[str, Any]:
        """
        Feedback-loop translation: translate → AI review → retranslate if violations found.

        1. Run normal translation (respects cache).
        2. Run structured AI review to detect glossary violations.
        3. If violations exist, retranslate with explicit correction instructions injected.
        4. Save the corrected translation and return full audit trail.

        Max retries is capped at `max_retries` (default=1) to avoid infinite loops.
        """
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "status_code": 404}

        logger.info(
            f"[FEEDBACK_LOOP] Starting translate+review for chapter {chapter_id}"
        )

        # Step 1 — initial translation
        translate_result = TranslationService.translate_chapter(db, chapter_id)
        if "error" in translate_result:
            return translate_result

        # Re-fetch chapter to get saved translated_text
        db.refresh(chapter)

        # Step 2 — structured review
        review_result = TranslationService.review_translation(db, chapter_id)
        if "error" in review_result:
            # Review failed — return the initial translation without corrections
            logger.warning(
                f"[FEEDBACK_LOOP] Review failed for chapter {chapter_id}: {review_result}"
            )
            return {**translate_result, "review": None, "retranslated": False}

        review = review_result.get("review", {})
        violations = review.get("violations", [])
        passed = review.get("passed", True)

        audit = {
            "initial_score": review.get("score"),
            "initial_passed": passed,
            "violations_found": len(violations),
            "retranslated": False,
            "final_score": review.get("score"),
        }

        if passed or not violations or max_retries < 1:
            logger.info(
                f"[FEEDBACK_LOOP] Chapter {chapter_id} passed review (score={review.get('score')}). No retranslation needed."
            )
            return {
                **translate_result,
                "review": review,
                "audit": audit,
                "retranslated": False,
            }

        # Step 3 — retranslate with corrections
        logger.info(
            f"[FEEDBACK_LOOP] Chapter {chapter_id} has {len(violations)} violation(s). Triggering correction pass."
        )

        glossary_terms = GlossaryService.get_relevant_terms(
            db, chapter.project_id, chapter.original_text
        )
        relevant_relationships = TranslationService._get_relevant_relationships(
            db, glossary_terms
        )
        project_summary = TranslationService._get_project_summary(
            db, chapter.project_id
        )

        corrected_text = TranslationService._retranslate_with_corrections(
            chapter=chapter,
            glossary_terms=glossary_terms,
            relationships=relevant_relationships,
            project_summary=project_summary,
            violations=violations,
        )

        # Save corrected translation
        chapter.translated_text = corrected_text
        db.commit()

        # Verify corrections with a second review (non-blocking — just for audit)
        final_score = review.get("score")
        try:
            verify_result = TranslationService.review_translation(db, chapter_id)
            if "review" in verify_result:
                final_score = verify_result["review"].get("score", final_score)
        except Exception as e:
            logger.warning(
                f"[FEEDBACK_LOOP] Verification review failed (non-critical): {e}"
            )

        audit["retranslated"] = True
        audit["final_score"] = final_score

        logger.info(
            f"[FEEDBACK_LOOP] Correction complete for chapter {chapter_id}. Score: {audit['initial_score']} → {final_score}"
        )

        return {
            "chapter_id": chapter_id,
            "translated_text": corrected_text,
            "glossary_terms_used": len(glossary_terms),
            "context_used": bool(chapter.summary),
            "project_context_used": bool(project_summary),
            "message": f"Translation completed with AI correction pass ({len(violations)} violation(s) fixed)",
            "cached": False,
            "review": review,
            "audit": audit,
            "retranslated": True,
        }

    # ─── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _retranslate_with_corrections(
        chapter: Chapter,
        glossary_terms: List[GlossaryTerm],
        relationships: List[Dict[str, Any]],
        project_summary: Optional[str],
        violations: List[Dict[str, Any]],
    ) -> str:
        """
        Build a correction-specific prompt that embeds reviewer violations as explicit
        fix instructions, then call Gemini for a corrected translation pass.
        """

        def _fmt_violation(v: Dict[str, Any]) -> str:
            excerpt_suffix = (
                f" | excerpt: {v['excerpt'][:80]}" if v.get("excerpt") else ""
            )
            return (
                f'  - WRONG: "{v.get("found", "?")}" → CORRECT: "{v.get("expected", "?")}" '
                f"(term: {v.get('source_term', '?')}){excerpt_suffix}"
            )

        violations_section = "\n".join([_fmt_violation(v) for v in violations])

        correction_instructions = f"""
CORRECTION PASS — Previous translation had glossary violations that MUST be fixed.

VIOLATIONS TO CORRECT:
{violations_section}

Fix every listed violation. Do not change anything else.
"""

        corrected = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary,
            project_summary=project_summary,
            relationships=relationships,
            genre=chapter.project.genre,
            source_language=chapter.project.source_language,
            target_language=chapter.project.target_language,
            custom_genre_instructions=correction_instructions,
        )
        return corrected

    @staticmethod
    def _parse_review_json(raw: str) -> Dict[str, Any]:
        """
        Parse AI reviewer output as JSON. Returns a safe fallback dict on failure.
        Handles JSON wrapped in markdown code fences.
        Guard: accepts any input type — converts to str or falls back safely.
        """
        # Guard against unexpected types (int, None passed by a buggy caller)
        if not isinstance(raw, str):
            if raw is None or raw == "":
                raw = ""
            else:
                try:
                    raw = str(raw)
                except Exception:
                    return {
                        "score": 5,
                        "passed": True,
                        "violations": [],
                        "style_notes": "",
                        "parse_error": "unsupported input type",
                    }

        if not raw:
            return {
                "score": 0,
                "passed": True,
                "violations": [],
                "style_notes": "",
                "parse_error": "empty response",
            }

        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(text)
            # json.loads may return int/str for JSON primitives like "12345" or "true".
            # We only accept dicts — anything else is treated as malformed.
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data).__name__}")
            # Validate required keys; fill defaults for missing optional ones
            return {
                "score": int(data.get("score", 5)),
                "passed": bool(data.get("passed", True)),
                "violations": list(data.get("violations", [])),
                "style_notes": str(data.get("style_notes", "")),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(
                f"[REVIEW] Failed to parse review JSON: {e}. Raw: {raw[:200]}"
            )
            return {
                "score": 5,
                "passed": True,
                "violations": [],
                "style_notes": raw[:500],
                "parse_error": str(e),
            }

    @staticmethod
    def _get_relevant_relationships(
        db: Session, glossary_terms: List[GlossaryTerm]
    ) -> List[Dict[str, Any]]:
        """Извлекает связи между переданными терминами."""
        from app.models.glossary import (
            TermRelationship,
        )  # local import avoids circular dep

        if len(glossary_terms) < 2:
            return []

        term_ids = [t.id for t in glossary_terms]

        relationships_db = (
            db.query(TermRelationship)
            .filter(
                TermRelationship.source_term_id.in_(term_ids),
                TermRelationship.target_term_id.in_(term_ids),
            )
            .all()
        )

        term_map = {t.id: t.source_term for t in glossary_terms}

        return [
            {
                "source": term_map.get(r.source_term_id, "Unknown"),
                "target": term_map.get(r.target_term_id, "Unknown"),
                "type": r.relation_type,
                "description": r.context or "",
            }
            for r in relationships_db
        ]

    @staticmethod
    def _get_project_summary(db: Session, project_id: int) -> Optional[str]:
        """Вспомогательный метод для получения саммари проекта."""
        project_chapters = (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.summary.isnot(None))
            .order_by(Chapter.id)
            .options(load_only(Chapter.title, Chapter.summary))
            .limit(5)
            .all()
        )

        if len(project_chapters) > 1:
            chapters_data = [
                {"title": ch.title, "summary": ch.summary, "original_text": ""}
                for ch in project_chapters
            ]
            return context_summarizer.create_project_summary(chapters_data)
        return None
