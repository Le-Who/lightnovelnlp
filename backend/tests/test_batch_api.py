from unittest.mock import patch
from datetime import datetime, timezone
from app.models.project import Project, Chapter
from app.models.glossary import BatchJob

def test_create_batch_analyze_all_chapters(client, db):
    # 1. Setup: Create a Project and Chapters
    project = Project(name="Test Batch Project", genre="fantasy")
    db.add(project)
    db.commit()
    db.refresh(project)

    # Processed chapter (should be ignored)
    processed_chapter = Chapter(
        project_id=project.id,
        title="Chapter 1",
        original_text="This is processed.",
        processed_at=datetime.now(timezone.utc)
    )
    # Unprocessed chapter (should be included)
    unprocessed_chapter = Chapter(
        project_id=project.id,
        title="Chapter 2",
        original_text="This needs analysis.",
        processed_at=None
    )

    db.add(processed_chapter)
    db.add(unprocessed_chapter)
    db.commit()

    # 2. Mock the background task
    # We mock where it is imported in the API module
    with patch("app.api.batch.process_batch_analyze_task") as mock_task:
        # 3. Action: Call the API
        response = client.post(f"/batch/{project.id}/analyze-chapters")

        # 4. Verify Response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "pending"
        assert data["total_items"] == 1
        assert "batch_job_id" in data
        assert data["message"] == "Batch analysis job created"

        batch_job_id = data["batch_job_id"]

        # 5. Verify Background Task was called
        mock_task.assert_called_once_with(batch_job_id)

        # 6. Verify Database State
        batch_job = db.query(BatchJob).filter(BatchJob.id == batch_job_id).first()
        assert batch_job is not None
        assert batch_job.project_id == project.id
        assert batch_job.job_type == "analyze"
        assert batch_job.total_items == 1
        assert batch_job.processed_items == 0
        assert batch_job.failed_items == 0

def test_create_batch_analyze_no_chapters(client, db):
    # 1. Setup: Create a Project with only processed chapters
    project = Project(name="Test Empty Batch Project", genre="scifi")
    db.add(project)
    db.commit()
    db.refresh(project)

    processed_chapter = Chapter(
        project_id=project.id,
        title="Chapter 1",
        original_text="Already done.",
        processed_at=datetime.now(timezone.utc)
    )
    db.add(processed_chapter)
    db.commit()

    # 2. Action: Call the API
    response = client.post(f"/batch/{project.id}/analyze-chapters")

    # 3. Verify Response
    assert response.status_code == 200
    data = response.json()

    assert data["total_items"] == 0
    assert "No unprocessed chapters found" in data["message"]
