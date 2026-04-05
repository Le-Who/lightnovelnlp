"""
Unit tests — ContextSummarizer.create_project_summary.

Level: Unit (pure function, no DB or network).
Covers:
  - Small project (≤ window) → only RECENT EVENTS section, no PREVIOUSLY block.
  - Large project (> window) → both PREVIOUSLY and RECENT EVENTS sections present.
  - Empty chapter list → empty string returned (no exception).
  - Chapters with missing 'summary' key → gracefully omitted (no 'None' in output).
"""

import pytest

from app.core.nlp_pipeline.context_summarizer import context_summarizer


@pytest.mark.unit
class TestContextSummarizerCreateProjectSummary:
    def test_small_project_produces_only_recent_events_section(self):
        # Arrange
        chapters = [
            {"title": "1", "summary": "Intro"},
            {"title": "2", "summary": "Meeting"},
        ]

        # Act
        summary = context_summarizer.create_project_summary(chapters, window_size=3)

        # Assert
        assert "RECENT EVENTS" in summary
        assert "PREVIOUSLY" not in summary
        assert "Intro" in summary
        assert "Meeting" in summary

    def test_large_project_produces_both_previously_and_recent_sections(self):
        # Arrange — 5 chapters, window = 2 → first 3 go to PREVIOUSLY
        chapters = [
            {"title": "1", "summary": "Ch1"},
            {"title": "2", "summary": "Ch2"},
            {"title": "3", "summary": "Ch3"},
            {"title": "4", "summary": "Ch4"},
            {"title": "5", "summary": "Ch5"},
        ]

        # Act
        summary = context_summarizer.create_project_summary(chapters, window_size=2)

        # Assert — backstory block references chapters 1-3
        assert "PREVIOUSLY (Chapters 1-3)" in summary
        assert "RECENT EVENTS" in summary
        assert "Ch1" in summary  # in backstory
        assert "Ch5" in summary  # in recent events

    def test_empty_chapter_list_returns_empty_string(self):
        # Act
        result = context_summarizer.create_project_summary([])

        # Assert
        assert result == ""

    def test_chapter_with_missing_summary_field_does_not_produce_none_in_output(self):
        # Arrange — first chapter has no 'summary' key; second has real content
        chapters = [
            {"title": "1"},  # no 'summary' key
            {"title": "2", "summary": "Real summary"},
        ]

        # Act
        summary = context_summarizer.create_project_summary(chapters, window_size=1)

        # Assert — 'None' must never appear as literal text in the output
        assert "Real summary" in summary
        assert "None" not in summary
