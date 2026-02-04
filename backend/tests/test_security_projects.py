from fastapi.testclient import TestClient
import pytest

def test_upload_chapters_redos_prevention(client: TestClient):
    # 1. Create a project
    response = client.post("/projects/", json={
        "name": "Security Test Project",
        "genre": "fantasy"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]

    # 2. Prepare a malicious payload (long regex)
    # 200 characters is enough to trigger our limit, even if not enough for actual DoS
    long_pattern = "a" * 200

    files = {
        "file": ("test.txt", "Some content", "text/plain")
    }

    # 3. Send request with long pattern
    # Note: query parameters are used for chapter_pattern in the API definition
    response = client.post(
        f"/projects/{project_id}/upload_chapters?chapter_pattern={long_pattern}",
        files=files
    )

    # 4. Assert it is rejected
    assert response.status_code == 400
    assert "Chapter pattern is too long" in response.json()["detail"]

def test_upload_chapters_empty_pattern_prevention(client: TestClient):
    # 1. Create a project
    response = client.post("/projects/", json={
        "name": "Security Test Project 2",
        "genre": "fantasy"
    })
    assert response.status_code == 201
    project_id = response.json()["id"]

    files = {
        "file": ("test.txt", "Some content", "text/plain")
    }

    # 2. Send request with empty pattern
    response = client.post(
        f"/projects/{project_id}/upload_chapters?chapter_pattern=",
        files=files
    )

    # 3. Assert it is rejected
    assert response.status_code == 400
    assert "Chapter pattern cannot be empty" in response.json()["detail"]
