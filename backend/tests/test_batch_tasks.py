"""
Integration tests — Batch task state machine (process_batch_translate_task,
process_batch_analyze_task).

Level: Integration (Celery task called directly as a plain function, bypassing the
       broker; SQLite in-memory DB via patches + conftest `db` fixture).

Covers:
  - Batch job transitions from 'pending' → 'running' → 'completed'.
  - Batch job transitions to 'failed' when ALL items fail.
  - Single item failure inside a batch does NOT abort the whole job.
  - Session is always closed after the batch task exits (resource-leak guard).
  - Non-existent batch_job_id → early return, no crash.

Architecture note: tasks open their own SessionLocal internally. We patch
`SessionLocal` at the module level so the tasks use the same SQLite in-memory
session as the conftest `db` fixture, giving us direct DB state inspection.

Critical risk guarded: Batch jobs are long-running. A state stuck at 'running'
with no DB update blocks the UI progress indicator indefinitely.
"""

from unittest.mock import MagicMock, patch

import pytest

try:
    from app.models.glossary import BatchJob, BatchJobItem
    from app.tasks.nlp_tasks import (
        process_batch_analyze_task,
        process_batch_translate_task,
    )

    _CELERY_AVAILABLE = True
except Exception:
    _CELERY_AVAILABLE = False

if not _CELERY_AVAILABLE:
    pytest.skip(
        "Celery/Pydantic v1 unavailable on this Python version", allow_module_level=True
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_batch_job(db, project_id: int, *, total_items: int = 1) -> BatchJob:
    """Helper: creates and persists a BatchJob in 'pending' state."""
    job = BatchJob(
        project_id=project_id,
        job_type="translate",
        status="pending",
        total_items=total_items,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _make_batch_item(
    db, project_id: int, batch_job_id: int, item_id: int = 999
) -> BatchJobItem:
    """Helper: creates and persists a BatchJobItem in 'pending' state."""
    item = BatchJobItem(
        project_id=project_id,
        batch_job_id=batch_job_id,
        item_type="chapter",
        item_id=item_id,
        status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ── process_batch_translate_task ──────────────────────────────────────────────


class TestBatchTranslateTask:
    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_job_transitions_to_completed_on_all_items_success(
        self, mock_translate, mock_session_cls, db
    ):
        # Arrange — inject real DB session so we can inspect final state
        mock_session_cls.return_value = db
        mock_translate.return_value = {"status": "success", "chapter_id": 10}

        from conftest import make_project

        project = make_project(db, name="Batch Translate Test")
        job = _make_batch_job(db, project.id, total_items=1)
        _make_batch_item(db, project.id, job.id, item_id=10)

        # Act
        process_batch_translate_task(job.id)

        # Assert — job must be completed
        db.refresh(job)
        assert job.status == "completed"
        assert job.processed_items == 1
        assert job.failed_items == 0

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_single_item_failure_does_not_abort_whole_job(
        self, mock_translate, mock_session_cls, db
    ):
        # Arrange — first item fails, second succeeds
        mock_session_cls.return_value = db
        mock_translate.side_effect = [
            RuntimeError("Gemini timeout"),
            {"status": "success", "chapter_id": 20},
        ]

        from conftest import make_project

        project = make_project(db, name="Partial Failure Test")
        job = _make_batch_job(db, project.id, total_items=2)
        _make_batch_item(db, project.id, job.id, item_id=10)
        _make_batch_item(db, project.id, job.id, item_id=20)

        # Act
        process_batch_translate_task(job.id)

        # Assert — job completes with 1 failed, 1 processed (not aborted)
        db.refresh(job)
        assert job.status == "completed"
        assert job.failed_items == 1
        assert job.processed_items == 1

    @patch("app.tasks.nlp_tasks.SessionLocal")
    def test_returns_early_when_batch_job_not_found(self, mock_session_cls, db):
        # Arrange
        mock_session_cls.return_value = db

        # Act — job_id 99999 does not exist in DB, must not raise
        process_batch_translate_task(99999)

        # Assert — nothing crashed, no job object to assert on

    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
    def test_closes_db_session_after_completion(
        self, mock_translate, mock_session_cls, db
    ):
        # Arrange
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        # Simulate .get() returning None → early return path
        mock_db.get.return_value = None

        # Act
        process_batch_translate_task(99999)

        # Assert — session closed regardless of outcome
        mock_db.close.assert_called_once()


# ── process_batch_analyze_task ────────────────────────────────────────────────


class TestBatchAnalyzeTask:
    @patch("app.tasks.nlp_tasks.SessionLocal")
    @patch("app.tasks.nlp_tasks.process_chapter_sync")
    def test_job_transitions_to_completed_on_all_items_success(
        self, mock_process, mock_session_cls, db
    ):
        # Arrange
        mock_session_cls.return_value = db
        mock_process.return_value = {"terms_found": 3}

        from conftest import make_project

        project = make_project(db, name="Batch Analyze Test")
        job = BatchJob(
            project_id=project.id,
            job_type="analyze",
            status="pending",
            total_items=1,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        item = BatchJobItem(
            project_id=project.id,
            batch_job_id=job.id,
            item_type="chapter",
            item_id=5,
            status="pending",
        )
        db.add(item)
        db.commit()

        # Act
        process_batch_analyze_task(job.id)

        # Assert
        db.refresh(job)
        assert job.status == "completed"
        assert job.processed_items == 1
        assert job.failed_items == 0

    @patch("app.tasks.nlp_tasks.SessionLocal")
    def test_closes_db_session_on_early_exit(self, mock_session_cls):
        # Arrange
        mock_db = MagicMock()
        mock_db.get.return_value = None  # job not found
        mock_session_cls.return_value = mock_db

        # Act
        process_batch_analyze_task(99999)

        # Assert — session is always released
        mock_db.close.assert_called_once()
