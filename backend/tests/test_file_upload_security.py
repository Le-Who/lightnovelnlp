import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

def test_upload_file_too_large(client: TestClient):
    # Create a project first
    response = client.post("/projects/", json={"name": "Test Project", "genre": "fantasy"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Create a large dummy file (content > MAX_UPLOAD_SIZE)
    # We don't actually need to create a 10MB string in memory if we mock the file size,
    # but for integration test it's better to be real if possible.
    # However, creating 10MB string is fast enough.

    # Temporarily reduce limit for testing to avoid memory usage
    original_limit = settings.MAX_UPLOAD_SIZE
    settings.MAX_UPLOAD_SIZE = 1024 # 1KB limit

    try:
        large_content = "a" * 2000
        files = {"file": ("large.txt", large_content, "text/plain")}

        # Test create_chapter_from_file
        response = client.post(f"/projects/{project_id}/chapters/upload", files=files)
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

        # Test upload_chapters_from_file
        files = {"file": ("large.txt", large_content, "text/plain")}
        response = client.post(f"/projects/{project_id}/upload_chapters", files=files)
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

    finally:
        settings.MAX_UPLOAD_SIZE = original_limit

def test_upload_chapter_pattern_too_long(client: TestClient):
    # Create a project
    response = client.post("/projects/", json={"name": "Test Project 2", "genre": "fantasy"})
    project_id = response.json()["id"]

    content = "Chapter 1\nText"
    files = {"file": ("chapters.txt", content, "text/plain")}

    # Pattern > 100 chars
    long_pattern = "a" * 101

    response = client.post(
        f"/projects/{project_id}/upload_chapters",
        files=files,
        data={"chapter_pattern": long_pattern}
    )

    assert response.status_code == 400
    assert "Chapter pattern too long" in response.json()["detail"]

def test_upload_too_many_chapters(client: TestClient):
    # Create a project
    response = client.post("/projects/", json={"name": "Test Project 3", "genre": "fantasy"})
    project_id = response.json()["id"]

    # Create content with 501 chapters
    # Use a simple pattern like "C\d"
    # "C1\nText\nC2\nText..."

    chapters = []
    for i in range(501):
        chapters.append(f"\nChapter {i}")

    content = "".join(chapters)
    files = {"file": ("many_chapters.txt", content, "text/plain")}

    response = client.post(
        f"/projects/{project_id}/upload_chapters",
        files=files,
        data={"chapter_pattern": "Chapter \\d+"}
    )

    assert response.status_code == 400
    assert "Too many chapters found" in response.json()["detail"]

def test_valid_upload(client: TestClient):
    # Create a project
    response = client.post("/projects/", json={"name": "Test Project 4", "genre": "fantasy"})
    project_id = response.json()["id"]

    content = "\nChapter 1\nSome text.\nChapter 2\nMore text."
    files = {"file": ("valid.txt", content, "text/plain")}

    response = client.post(
        f"/projects/{project_id}/upload_chapters",
        files=files,
        data={"chapter_pattern": "Chapter \\d+"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["chapters_created"] == 2
