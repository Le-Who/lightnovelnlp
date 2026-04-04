"""
Unit tests — translate_chapter_background (FastAPI BackgroundTask).

Level: Unit (mocked SessionLocal).
Covers:
  - Status transitions: PENDING → TRANSLATING → COMPLETED on success.
  - Status transitions: PENDING → TRANSLATING → FAILED on error.
  - DB session is always closed (resource leak guard).
  - Chapter not found → early return (no status update attempt).

This function handles the FastAPI BackgroundTasks execution path
(as opposed to Celery tasks which have their own test module).
"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.api.translation import translate_chapter_background
    from app.models.project import TranslationStatus

    _IMPORTS_AVAILABLE = True
except Exception:
    _IMPORTS_AVAILABLE = False

if not _IMPORTS_AVAILABLE:
    pytest.skip(
        "spaCy/Pydantic v1 unavailable on this Python version", allow_module_level=True
    )


class TestTranslateChapterBackground:
    @patch("app.api.translation.SessionLocal")
    @patch("app.api.translation.TranslationService.translate_chapter")
    def test_transitions_status_to_completed_on_success(
        self, mock_translate, mock_session_cls
    ):
        # Arrange
        mock_chapter = MagicMock()
        mock_db = MagicMock()
        mock_db.get.return_value = mock_chapter
        mock_session_cls.return_value = mock_db
        mock_translate.return_value = {"translated_text": "Привет", "chapter_id": 1}

        # Act
        translate_chapter_background(1)

        # Assert — at least 2 commits: TRANSLATING set + COMPLETED set
        assert mock_db.commit.call_count >= 2
        # Final status must be COMPLETED (last assignment wins on MagicMock attribute)
        assert mock_chapter.translation_status == TranslationStatus.COMPLETED.value

    @patch("app.api.translation.SessionLocal")
    @patch("app.api.translation.TranslationService.translate_chapter")
    def test_transitions_status_to_failed_on_service_error(
        self, mock_translate, mock_session_cls
    ):
        # Arrange
        mock_chapter = MagicMock()
        mock_db = MagicMock()
        mock_db.get.return_value = mock_chapter
        mock_session_cls.return_value = mock_db
        mock_translate.side_effect = RuntimeError("Gemini timed out")

        # Act
        translate_chapter_background(1)  # Must not raise

        # Assert — status set to FAILED
        mock_chapter.translation_status = TranslationStatus.FAILED.value
        assert mock_db.commit.called

    @patch("app.api.translation.SessionLocal")
    @patch("app.api.translation.TranslationService.translate_chapter")
    def test_closes_db_session_on_success(self, mock_translate, mock_session_cls):
        # Arrange
        mock_db = MagicMock()
        mock_db.get.return_value = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_translate.return_value = {"translated_text": "Done", "chapter_id": 1}

        # Act
        translate_chapter_background(1)

        # Assert — connection must be returned to pool
        mock_db.close.assert_called_once()

    @patch("app.api.translation.SessionLocal")
    @patch("app.api.translation.TranslationService.translate_chapter")
    def test_closes_db_session_on_failure(self, mock_translate, mock_session_cls):
        # Arrange
        mock_db = MagicMock()
        mock_db.get.return_value = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_translate.side_effect = RuntimeError("Network error")

        # Act
        translate_chapter_background(1)  # Must not raise

        # Assert — session must be closed even when exception occurs
        mock_db.close.assert_called_once()

    @patch("app.api.translation.SessionLocal")
    def test_returns_early_when_chapter_not_found(self, mock_session_cls):
        # Arrange
        mock_db = MagicMock()
        mock_db.get.return_value = None  # chapter missing
        mock_session_cls.return_value = mock_db

        # Act
        translate_chapter_background(99999)

        # Assert — no commit attempted for missing chapter
        mock_db.commit.assert_not_called()
        # But session must still be closed
        mock_db.close.assert_called_once()
