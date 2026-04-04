"""
Integration tests — Project API endpoints.

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - POST /projects/     → 201, response shape, persists to DB.
  - GET  /projects/     → 200, ordering (newest first).
  - GET  /projects/{id} → 200 / 404.
  - DELETE /projects/{id} → 204 / 404.

AAA pattern enforced: Arrange uses factory helpers or DB session directly,
never creates resources through the API in Arrange.
"""

from conftest import make_project


# ── POST /projects/ ────────────────────────────────────────────────────────────


class TestCreateProject:
    def test_returns_201_with_expected_payload(self, client):
        # Act
        response = client.post(
            "/projects/", json={"name": "Sword Art Online", "genre": "fantasy"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sword Art Online"
        assert data["genre"] == "fantasy"
        assert "id" in data

    def test_returns_422_when_name_missing(self, client):
        # Act — name is a required field
        response = client.post("/projects/", json={"genre": "fantasy"})

        # Assert
        assert response.status_code == 422

    def test_persists_project_in_database(self, client, db):
        # Act
        response = client.post(
            "/projects/", json={"name": "Recorded Project", "genre": "scifi"}
        )

        # Assert — verify DB state independently of the response
        from app.models.project import Project

        project_id = response.json()["id"]
        db_project = db.get(Project, project_id)
        assert db_project is not None
        assert db_project.name == "Recorded Project"


# ── GET /projects/ ─────────────────────────────────────────────────────────────


class TestListProjects:
    def test_returns_200_with_empty_list_when_no_projects(self, client):
        # Arrange — DB is clean (no setup needed)

        # Act
        response = client.get("/projects/")

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_projects_ordered_by_creation_descending(self, client, db):
        # Arrange — create two projects directly in DB to control their state
        make_project(db, name="Older Project")
        make_project(db, name="Newer Project")

        # Act
        response = client.get("/projects/")

        # Assert — newest first
        assert response.status_code == 200
        names = [p["name"] for p in response.json()]
        assert names.index("Newer Project") < names.index("Older Project")

    def test_returns_all_existing_projects(self, client, db):
        # Arrange
        make_project(db, name="Alpha")
        make_project(db, name="Beta")

        # Act
        response = client.get("/projects/")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2


# ── GET /projects/{id} ────────────────────────────────────────────────────────


class TestGetProject:
    def test_returns_404_for_nonexistent_project(self, client):
        # Act
        response = client.get("/projects/99999")

        # Assert
        assert response.status_code == 404

    def test_returns_200_with_project_data_for_valid_id(self, client, db):
        # Arrange
        project = make_project(db, name="My Project")

        # Act
        response = client.get(f"/projects/{project.id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == project.id
        assert response.json()["name"] == "My Project"


# ── DELETE /projects/{id} ─────────────────────────────────────────────────────


class TestDeleteProject:
    def test_returns_204_on_successful_deletion(self, client, db):
        # Arrange
        project = make_project(db, name="To Delete")

        # Act
        response = client.delete(f"/projects/{project.id}")

        # Assert
        assert response.status_code == 204

    def test_project_no_longer_exists_after_deletion(self, client, db):
        # Arrange
        project = make_project(db, name="Ephemeral")
        project_id = project.id

        # Act
        client.delete(f"/projects/{project_id}")

        # Assert — subsequent GET returns 404
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404

    def test_returns_404_for_nonexistent_project_deletion(self, client):
        # Act
        response = client.delete("/projects/99999")

        # Assert
        assert response.status_code == 404
