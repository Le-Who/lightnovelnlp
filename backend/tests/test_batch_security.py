from unittest.mock import patch
from datetime import datetime, timezone
from app.models.project import Project, Chapter
from app.models.glossary import BatchJob

def test_create_batch_analyze_job_cross_project_vulnerability(client, db):
    """
    Test that ensures a batch job cannot be created for Project A using a Chapter from Project B.
    Currently, this test expects 404 (Security Fix) but would get 200 (Vulnerable) without the fix.
    """
    # 1. Setup: Create two projects
    project_a = Project(name="Project A", genre="fantasy")
    project_b = Project(name="Project B", genre="scifi")
    db.add(project_a)
    db.add(project_b)
    db.commit()
    db.refresh(project_a)
    db.refresh(project_b)

    # Create a chapter in Project B
    chapter_b = Chapter(
        project_id=project_b.id,
        title="Chapter B",
        original_text="Content B",
        order=1
    )
    db.add(chapter_b)
    db.commit()
    db.refresh(chapter_b)

    # 2. Action: Try to create a batch job for Project A using Chapter from Project B
    # We mock the background task to avoid actual execution if it accidentally succeeds
    with patch("app.api.batch.process_batch_analyze_task"):
        response = client.post(
            f"/batch/{project_a.id}/analyze",
            json=[chapter_b.id]
        )

    # 3. Verify: Should fail because chapter does not belong to Project A
    # If vulnerable, this would return 200. We want 404 or 400.
    assert response.status_code == 404, f"Expected 404, but got {response.status_code}. Response: {response.json()}"

    # Also verify no job was created for Project A
    job_a = db.query(BatchJob).filter(BatchJob.project_id == project_a.id).first()
    assert job_a is None, "Batch job should not be created for Project A"

def test_create_batch_translate_job_cross_project_vulnerability(client, db):
    """
    Similar test for translation batch job.
    """
    # 1. Setup
    project_a = Project(name="Project A", genre="fantasy")
    project_b = Project(name="Project B", genre="scifi")
    db.add(project_a)
    db.add(project_b)
    db.commit()
    db.refresh(project_a)
    db.refresh(project_b)

    chapter_b = Chapter(
        project_id=project_b.id,
        title="Chapter B",
        original_text="Content B",
        order=1
    )
    db.add(chapter_b)
    db.commit()
    db.refresh(chapter_b)

    # 2. Action
    with patch("app.api.batch.process_batch_translate_task"):
        response = client.post(
            f"/batch/{project_a.id}/translate",
            json=[chapter_b.id]
        )

    # 3. Verify
    assert response.status_code == 404, f"Expected 404, but got {response.status_code}. Response: {response.json()}"
