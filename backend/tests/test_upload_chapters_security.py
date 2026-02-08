
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.deps import get_db
from app.models.project import Project, Chapter
from app.api.projects import MAX_CHAPTERS_PER_UPLOAD, MAX_PATTERN_LENGTH

client = TestClient(app)

def test_upload_chapters_too_long_pattern():
    """Test that overly long regex pattern is rejected."""
    project_id = 1
    long_pattern = "a" * (MAX_PATTERN_LENGTH + 1)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    # Mock project existence
    mock_db.get.return_value = Project(id=project_id, name="Test")

    files = {"file": ("test.txt", "content", "text/plain")}
    data = {"chapter_pattern": long_pattern}

    response = client.post(f"/projects/{project_id}/upload_chapters", files=files, data=data)

    assert response.status_code == 400
    assert "Regex pattern is too long" in response.json()["detail"]

def test_upload_chapters_too_many_matches():
    """Test that matching too many chapters is rejected."""
    project_id = 1
    # Create content that will match "Chapter" many times
    # We want to exceed MAX_CHAPTERS_PER_UPLOAD
    match_count = MAX_CHAPTERS_PER_UPLOAD + 10
    # Include content between chapters so they are not empty
    content = "\nChapter\nSome content.\n" * match_count

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.get.return_value = Project(id=project_id, name="Test")

    # Pattern matching "Chapter"
    # Note: the API wraps pattern in \n({pattern}), so we just need "Chapter"
    pattern = "Chapter"

    files = {"file": ("test.txt", content, "text/plain")}
    data = {"chapter_pattern": pattern}

    # The API should find matches > MAX_CHAPTERS_PER_UPLOAD and reject
    response = client.post(f"/projects/{project_id}/upload_chapters", files=files, data=data)

    assert response.status_code == 400
    assert "Too many chapters found" in response.json()["detail"]
    assert str(MAX_CHAPTERS_PER_UPLOAD) in response.json()["detail"]

def test_upload_chapters_valid_limit():
    """Test that uploading close to limit is allowed."""
    project_id = 1
    match_count = 10
    # Include content between chapters so they are not empty
    content = "\nChapter\nSome content.\n" * match_count

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.get.return_value = Project(id=project_id, name="Test")
    # Mock max order
    mock_db.query.return_value.filter.return_value.scalar.return_value = 0

    pattern = "Chapter"

    files = {"file": ("test.txt", content, "text/plain")}
    data = {"chapter_pattern": pattern}

    response = client.post(f"/projects/{project_id}/upload_chapters", files=files, data=data)

    assert response.status_code == 200
    assert response.json()["chapters_created"] == match_count

def test_upload_chapters_exact_limit():
    """Test that uploading EXACTLY limit is allowed."""
    project_id = 1
    match_count = MAX_CHAPTERS_PER_UPLOAD
    content = "\nChapter\nSome content.\n" * match_count

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.get.return_value = Project(id=project_id, name="Test")
    mock_db.query.return_value.filter.return_value.scalar.return_value = 0

    pattern = "Chapter"

    files = {"file": ("test.txt", content, "text/plain")}
    data = {"chapter_pattern": pattern}

    response = client.post(f"/projects/{project_id}/upload_chapters", files=files, data=data)

    # Should succeed because 500 is allowed
    assert response.status_code == 200
    assert response.json()["chapters_created"] == match_count
