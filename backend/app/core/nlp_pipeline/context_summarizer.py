from __future__ import annotations

import logging
from typing import List, Dict, Any

from app.services.gemini_client import gemini_client

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "en": "English", "ru": "Russian", "other": "Other",
}


class ContextSummarizer:
    def __init__(self):
        self.client = gemini_client

    def summarize_context(
        self,
        text: str,
        chapter_title: str | None = None,
        previous_summary: str | None = None,
        target_language: str = "ru",
    ) -> str:
        """
        Create a concise context summary for a chapter.

        Args:
            text: Chapter text
            chapter_title: Chapter title (optional)
            previous_summary: Summary of previous chapters (optional)
            target_language: Language for the summary output

        Returns:
            str: Concise context summary
        """
        prompt = self._build_summary_prompt(
            text, chapter_title, previous_summary, target_language
        )

        try:
            response = self.client.complete(prompt, task_type="summarization")
            return response.strip()
        except Exception as e:
            logger.error(f"Error summarizing context: {e}")
            return ""

    def _build_summary_prompt(
        self,
        text: str,
        chapter_title: str | None = None,
        previous_summary: str | None = None,
        target_language: str = "ru",
    ) -> str:
        """Build XML-delimited summary prompt with dynamic language."""

        target_name = LANG_NAMES.get(target_language, target_language)

        previous_block = ""
        if previous_summary:
            previous_block = f"""
<previous_context>
{previous_summary}
</previous_context>
"""

        title_attr = f' title="{chapter_title}"' if chapter_title else ""

        return f"""<system>
You are a concise narrative analyst for light novel chapters.
Respond in {target_name}.
</system>

<task>
Create a brief summary (2-3 sentences) of the key events in this chapter.
</task>

<focus>
- Character actions and motivations
- Important dialogue or decisions
- New locations, artifacts, or abilities introduced
- Plot progression and cliffhangers
</focus>
{previous_block}
<chapter{title_attr}>
{text}
</chapter>"""

    def create_project_summary(
        self,
        chapters: List[Dict[str, Any]],
        window_size: int = 3
    ) -> str:
        """
        Create hierarchical project summary:
        1. "Previously" (compressed summary of older chapters)
        2. "Recent events" (detailed summary of last N chapters)

        Args:
            chapters: List of all chapters with summary
            window_size: Number of recent chapters for detailed context

        Returns:
            str: Structured summary for translation context
        """
        if not chapters:
            return ""

        total_chapters = len(chapters)

        recent_chapters = chapters[-window_size:]
        old_chapters = chapters[:-window_size] if total_chapters > window_size else []

        summary_parts = []

        if old_chapters:
            old_summary_text = "\n".join([ch.get('summary', '') for ch in old_chapters if ch.get('summary')])
            if old_summary_text:
                summary_parts.append(f"PREVIOUSLY (Chapters 1-{len(old_chapters)}):\n{old_summary_text[:2000]}...")

        if recent_chapters:
            recent_text = "\n\n".join([
                f"Chapter {ch.get('title')}: {ch.get('summary')}"
                for ch in recent_chapters
                if ch.get('summary')
            ])
            summary_parts.append(f"RECENT EVENTS:\n{recent_text}")

        return "\n\n".join(summary_parts)


context_summarizer = ContextSummarizer()
