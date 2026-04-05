"""
Integration tests — Chapter API endpoints (CRUD).

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - GET  /projects/{id}/chapters → 200, returns chapter list.
  - POST /projects/{id}/chapters → 201, creates chapter with auto-assigned order.
  - POST /projects/{id}/chapters → 404 for non-existent project.
  - GET  /projects/chapters/{id} → 200 / 404.
  - DELETE /projects/chapters/{id} → 204 / 404.
  - PUT  /projects/chapters/{id} → 200, updates title field.

AAA pattern enforced. All Arrange uses factory helpers — no resources created
through the API in Arrange blocks.
"""

import pytest

from conftest import make_chapter, make_project


# ── GET /projects/{project_id}/chapters ───────────────────────────────────────


@pytest.mark.integration
class TestListChapters:
    def test_returns_200_with_empty_list_when_no_chapters(self, client, db):
        # Arrange
        project = make_project(db, name="Empty Project")

        # Act
        response = client.get(f"/projects/{project.id}/chapters")

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_chapters_for_project(self, client, db):
        # Arrange
        project = make_project(db, name="Multi-Chapter Project")
        make_chapter(db, project.id, original_text="Chapter One text")
        make_chapter(db, project.id, original_text="Chapter Two text")

        # Act
        response = client.get(f"/projects/{project.id}/chapters")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_does_not_return_chapters_from_other_projects(self, client, db):
        # Arrange
        project_a = make_project(db, name="Project A")
        project_b = make_project(db, name="Project B")
        make_chapter(db, project_a.id, original_text="Project A chapter")

        # Act
        response = client.get(f"/projects/{project_b.id}/chapters")

        # Assert — project B has no chapters
        assert response.status_code == 200
        assert response.json() == []


# ── POST /projects/{project_id}/chapters ──────────────────────────────────────


@pytest.mark.integration
class TestCreateChapter:
    def test_returns_201_with_chapter_data_on_success(self, client, db):
        # Arrange
        project = make_project(db, name="New Chapter Project")
        payload = {"title": "Chapter 1", "original_text": "Once upon a time..."}

        # Act
        response = client.post(f"/projects/{project.id}/chapters", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Chapter 1"
        assert data["original_text"] == "Once upon a time..."
        assert "id" in data

    def test_assigns_sequential_order_to_new_chapters(self, client, db):
        # Arrange
        project = make_project(db, name="Order Test Project")

        # Act — create two chapters sequentially
        first = client.post(
            f"/projects/{project.id}/chapters",
            json={"title": "First", "original_text": "Text A"},
        )
        second = client.post(
            f"/projects/{project.id}/chapters",
            json={"title": "Second", "original_text": "Text B"},
        )

        # Assert — second chapter has a higher order than the first
        assert second.json()["order"] > first.json()["order"]

    def test_returns_404_when_project_does_not_exist(self, client):
        # Act
        response = client.post(
            "/projects/99999/chapters",
            json={"title": "Lost Chapter", "original_text": "Nowhere"},
        )

        # Assert
        assert response.status_code == 404


# ── GET /projects/chapters/{chapter_id} ───────────────────────────────────────


@pytest.mark.integration
class TestGetChapter:
    def test_returns_200_with_chapter_data_for_valid_id(self, client, db):
        # Arrange
        project = make_project(db, name="Get Chapter Project")
        chapter = make_chapter(db, project.id, original_text="Detailed chapter text")

        # Act
        response = client.get(f"/projects/chapters/{chapter.id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == chapter.id

    def test_returns_404_for_nonexistent_chapter(self, client):
        # Act
        response = client.get("/projects/chapters/99999")

        # Assert
        assert response.status_code == 404


# ── DELETE /projects/chapters/{chapter_id} ────────────────────────────────────


@pytest.mark.integration
class TestDeleteChapter:
    def test_returns_204_on_successful_deletion(self, client, db):
        # Arrange
        project = make_project(db, name="Delete Chapter Project")
        chapter = make_chapter(db, project.id, original_text="To be deleted")

        # Act
        response = client.delete(f"/projects/chapters/{chapter.id}")

        # Assert
        assert response.status_code == 204

    def test_chapter_is_gone_after_deletion(self, client, db):
        # Arrange
        project = make_project(db, name="Gone Chapter Project")
        chapter = make_chapter(db, project.id, original_text="Temporary text")
        chapter_id = chapter.id

        # Act
        client.delete(f"/projects/chapters/{chapter_id}")

        # Assert — subsequent GET returns 404
        get_response = client.get(f"/projects/chapters/{chapter_id}")
        assert get_response.status_code == 404

    def test_returns_404_for_nonexistent_chapter(self, client):
        # Act
        response = client.delete("/projects/chapters/99999")

        # Assert
        assert response.status_code == 404


# ── PUT /projects/chapters/{chapter_id} ───────────────────────────────────────


@pytest.mark.integration
class TestUpdateChapter:
    def test_returns_200_with_updated_title(self, client, db):
        # Arrange
        project = make_project(db, name="Update Chapter Project")
        chapter = make_chapter(db, project.id, original_text="Original text")

        # Act
        response = client.put(
            f"/projects/chapters/{chapter.id}",
            json={"title": "Updated Title"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_returns_404_for_nonexistent_chapter(self, client):
        # Act
        response = client.put(
            "/projects/chapters/99999",
            json={"title": "Will Not Apply"},
        )

        # Assert
        assert response.status_code == 404
