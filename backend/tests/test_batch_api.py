"""
Integration tests — Batch API endpoints.

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - POST /batch/{project_id}/analyze-chapters → creates batch job with correct counts.
  - POST /batch/{project_id}/analyze-chapters with no unprocessed chapters → returns 0 total.
  - Batch job is persisted to DB with correct metadata.
  - Background task is dispatched exactly once with the batch_job_id.

AAA pattern enforced throughout. Arrange uses factory helpers or direct DB inserts —
resources are never created through the API in Arrange.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.models.glossary import BatchJob
from app.models.project import Chapter
from conftest import make_project


# ── POST /batch/{project_id}/analyze-chapters ─────────────────────────────────


@pytest.mark.integration
class TestBatchAnalyzeChapters:
    def test_creates_batch_job_for_unprocessed_chapters(self, client, db):
        # Arrange
        project = make_project(db, name="Batch API Test Project")
        db.add(
            Chapter(
                project_id=project.id,
                title="Chapter 1",
                original_text="Already analysed text.",
                processed_at=datetime.now(timezone.utc),  # already done
            )
        )
        db.add(
            Chapter(
                project_id=project.id,
                title="Chapter 2",
                original_text="This needs analysis.",
                processed_at=None,  # unprocessed → should be included
            )
        )
        db.commit()

        # Act
        with patch("app.api.batch.process_batch_analyze_task") as mock_task:
            response = client.post(f"/batch/{project.id}/analyze-chapters")

        # Assert — response contract
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_items"] == 1  # only the unprocessed chapter
        assert "batch_job_id" in data
        assert data["message"] == "Batch analysis job created"

        # Assert — background task dispatched exactly once with the correct job id
        mock_task.assert_called_once_with(data["batch_job_id"])

    def test_persists_batch_job_to_database_with_correct_metadata(self, client, db):
        # Arrange
        project = make_project(db, name="Batch DB Persistence Test")
        db.add(
            Chapter(
                project_id=project.id,
                title="Chapter 1",
                original_text="Needs work.",
                processed_at=None,
            )
        )
        db.commit()

        # Act
        with patch("app.api.batch.process_batch_analyze_task"):
            response = client.post(f"/batch/{project.id}/analyze-chapters")

        batch_job_id = response.json()["batch_job_id"]

        # Assert — DB state reflects the API response
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        assert batch_job is not None
        assert batch_job.project_id == project.id
        assert batch_job.job_type == "analyze"
        assert batch_job.total_items == 1
        assert batch_job.processed_items == 0
        assert batch_job.failed_items == 0

    def test_returns_zero_total_when_all_chapters_are_already_processed(
        self, client, db
    ):
        # Arrange
        project = make_project(db, name="All Processed Project")
        db.add(
            Chapter(
                project_id=project.id,
                title="Chapter 1",
                original_text="Already done.",
                processed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        # Act
        response = client.post(f"/batch/{project.id}/analyze-chapters")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert "No unprocessed chapters found" in data["message"]
