from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.project import Project, Chapter
from app.models.glossary import BatchJob, BatchJobItem
from app.deps import get_db

def test_batch_create_idor(client: TestClient, db: Session):
    # Create two projects
    p1 = Project(name="Project 1", source_language="en", target_language="ru")
    p2 = Project(name="Project 2", source_language="en", target_language="fr")
    db.add(p1)
    db.add(p2)
    db.commit()
    db.refresh(p1)
    db.refresh(p2)

    # Create chapters for each
    c1 = Chapter(project_id=p1.id, title="Ch1 P1", order=1, original_text="Text 1")
    c2 = Chapter(project_id=p2.id, title="Ch1 P2", order=1, original_text="Text 2")
    db.add(c1)
    db.add(c2)
    db.commit()
    db.refresh(c1)
    db.refresh(c2)

    # Try to create a batch job for Project 1 but including Chapter 2 (from Project 2)
    # The endpoint is POST /batch/{project_id}/analyze
    response = client.post(
        f"/batch/{p1.id}/analyze",
        json=[c1.id, c2.id]
    )

    # Assert that the request is rejected with 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    data = response.json()
    assert "does not belong to project" in data["detail"]

    # Verify NO job was created
    jobs = db.query(BatchJob).all()
    assert len(jobs) == 0

def test_batch_create_translate_idor(client: TestClient, db: Session):
    # Same check for translation endpoint
    p1 = Project(name="Project 1", source_language="en", target_language="ru")
    p2 = Project(name="Project 2", source_language="en", target_language="fr")
    db.add(p1)
    db.add(p2)
    db.commit()

    c1 = Chapter(project_id=p1.id, title="Ch1", order=1, original_text="Text")
    c2 = Chapter(project_id=p2.id, title="Ch2", order=1, original_text="Text")
    db.add(c1)
    db.add(c2)
    db.commit()

    response = client.post(
        f"/batch/{p1.id}/translate",
        json=[c1.id, c2.id]
    )

    assert response.status_code == 400
    assert "does not belong to project" in response.json()["detail"]

    jobs = db.query(BatchJob).all()
    assert len(jobs) == 0
