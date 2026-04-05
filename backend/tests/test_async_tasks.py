"""
Integration tests — Celery async tasks.

Level: Integration (Celery task called directly as a function, bypassing broker).
Covers:
  - translate_chapter_task: delegates to TranslationService and closes DB session.
  - analyze_chapter_task:  delegates to process_chapter_sync and closes DB session.
  - Retry semantics: self.retry() called with correct exc and countdown on failure.
  - Session lifecycle: db.close() always called (no resource leaks).

Note: Celery + pydantic.v1 are incompatible with Python 3.14. Tests are guarded
with module-level skip; they run normally on Python 3.12 (production).
"""

from unittest.mock import MagicMock, patch

import pytest

try:
    from app.tasks.nlp_tasks import analyze_chapter_task, translate_chapter_task

    _CELERY_AVAILABLE = True
except Exception:
    _CELERY_AVAILABLE = False

if not _CELERY_AVAILABLE:
    pytest.skip(
        "Celery/Pydantic v1 unavailable on this Python version", allow_module_level=True
    )


# ── translate_chapter_task ────────────────────────────────────────────────────


class TestTranslateChapterTask:
    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_delegates_to_translation_service_and_returns_result(
        self, mock_translate, mock_session
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_translate.return_value = {"status": "success", "chapter_id": 1}

        # Act — bypass broker, call the underlying un-wrapped code via run()
        result = translate_chapter_task.run(1)

        # Assert
        mock_translate.assert_called_once_with(mock_db, 1)
        assert result == {"status": "success", "chapter_id": 1}

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_closes_db_session_after_successful_translation(
        self, mock_translate, mock_session
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_translate.return_value = {"status": "success", "chapter_id": 1}

        # Act
        translate_chapter_task.run(1)

        # Assert — session must be closed even on success to prevent connection leaks
        mock_db.close.assert_called_once()

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_retries_on_exception_and_closes_db_session(
        self, mock_translate, mock_session
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        exception = RuntimeError("Gemini offline")
        mock_translate.side_effect = exception

        from celery.exceptions import Retry

        # Act
        with patch.object(translate_chapter_task, "retry", side_effect=Retry("Task is being retried")) as mock_retry:
            with pytest.raises(Retry):
                translate_chapter_task.run(1)

            # Assert — retry called with correct parameters
            mock_retry.assert_called_once_with(exc=exception, countdown=60)
        # Assert — session always closed (prevents resource leaks)
        mock_db.close.assert_called_once()


# ── analyze_chapter_task ──────────────────────────────────────────────────────


class TestAnalyzeChapterTask:
    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.process_chapter_sync")
    def test_delegates_to_process_chapter_sync_and_returns_result(
        self, mock_process, mock_session
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_process.return_value = {
            "chapter_id": 5,
            "extracted_terms": 12,
            "status": "completed",
        }

        # Act
        result = analyze_chapter_task.run(5)

        # Assert
        mock_process.assert_called_once_with(5, mock_db)
        assert result["status"] == "completed"
        assert result["chapter_id"] == 5

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.process_chapter_sync")
    def test_returns_error_dict_when_sync_returns_error_key(
        self, mock_process, mock_session
    ):
        # Arrange — process_chapter_sync returns an error dict (not a raise)
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_process.return_value = {"error": "Chapter not found", "chapter_id": 99}

        # Act
        result = analyze_chapter_task.run(99)

        # Assert — task returns error dict without retrying (process_chapter_sync handled it)
        assert result["status"] == "error"
        assert result["error"] == "Chapter not found"

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.process_chapter_sync")
    def test_closes_db_session_after_successful_analysis(
        self, mock_process, mock_session
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_process.return_value = {"chapter_id": 5, "extracted_terms": 3}

        # Act
        analyze_chapter_task.run(5)

        # Assert — session closed even on success
        mock_db.close.assert_called_once()

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.process_chapter_sync")
    def test_retries_on_exception_and_closes_db_session(
        self, mock_process, mock_session
    ):
        # Arrange — simulate a transient Gemini API failure
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        exception = ConnectionError("Gemini API timeout")
        mock_process.side_effect = exception

        from celery.exceptions import Retry

        # Act
        with patch.object(analyze_chapter_task, "retry", side_effect=Retry("Task is being retried")) as mock_retry:
            with pytest.raises(Retry):
                analyze_chapter_task.run(5)

            # Assert — retry called with correct parameters
            mock_retry.assert_called_once_with(exc=exception, countdown=60)
        # Assert — session always closed (prevents resource leaks)
        mock_db.close.assert_called_once()
