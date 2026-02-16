import os
import sys
import io
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.config import settings

def test_upload_chapters_file_too_large(client: TestClient):
    # Set a small limit: 10 bytes
    original_limit = settings.MAX_UPLOAD_SIZE
    settings.MAX_UPLOAD_SIZE = 10

    try:
        # Create a file content larger than 10 bytes
        file_content = b"This file is definitely larger than 10 bytes."
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }

        # Create a project
        response = client.post("/projects/", json={"name": "Test Project Limits", "genre": "test"})
        assert response.status_code == 201
        project_id = response.json()["id"]

        response = client.post(
            f"/projects/{project_id}/upload_chapters",
            files=files,
            data={"chapter_pattern": "Chapter \\d+"}
        )

        # Expect 413 Payload Too Large
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

    finally:
        # Restore limit
        settings.MAX_UPLOAD_SIZE = original_limit

def test_create_chapter_from_file_too_large(client: TestClient):
    # Set a small limit: 10 bytes
    original_limit = settings.MAX_UPLOAD_SIZE
    settings.MAX_UPLOAD_SIZE = 10

    try:
        # Create a file content larger than 10 bytes
        file_content = b"This file is definitely larger than 10 bytes."
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }

        # Create a project
        response = client.post("/projects/", json={"name": "Test Project Limits 2", "genre": "test"})
        assert response.status_code == 201
        project_id = response.json()["id"]

        response = client.post(
            f"/projects/{project_id}/chapters/upload",
            files=files
        )

        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]

    finally:
        settings.MAX_UPLOAD_SIZE = original_limit
