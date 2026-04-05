"""
Integration tests — Glossary term Pydantic schema validation.

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - POST /glossary/terms with a valid payload → 201.
  - POST /glossary/terms with source_term exceeding 255 chars → 422.
  - POST /glossary/terms with translated_term exceeding 255 chars → 422.
  - POST /glossary/terms with category exceeding 50 chars → 422.

AAA pattern enforced. Project is created via the factory helper in Arrange
(not via the API) so that Arrange does not depend on the correctness of the
project-creation flow — separation of concerns between test suites.
"""

import pytest

from conftest import make_project


@pytest.mark.integration
class TestCreateGlossaryTermValidation:
    def test_returns_201_for_valid_term_payload(self, client, db):
        # Arrange
        project = make_project(db, name="Valid Term Test Project")
        payload = {
            "project_id": project.id,
            "source_term": "valid",
            "translated_term": "valid",
            "category": "other",
        }

        # Act
        response = client.post("/glossary/terms", json=payload)

        # Assert
        assert response.status_code == 201

    def test_returns_422_when_source_term_exceeds_255_chars(self, client, db):
        # Arrange
        project = make_project(db, name="Source Too Long Project")
        payload = {
            "project_id": project.id,
            "source_term": "a" * 256,
            "translated_term": "valid",
            "category": "other",
        }

        # Act
        response = client.post("/glossary/terms", json=payload)

        # Assert
        assert response.status_code == 422

    def test_returns_422_when_translated_term_exceeds_255_chars(self, client, db):
        # Arrange
        project = make_project(db, name="Translated Too Long Project")
        payload = {
            "project_id": project.id,
            "source_term": "valid",
            "translated_term": "a" * 256,
            "category": "other",
        }

        # Act
        response = client.post("/glossary/terms", json=payload)

        # Assert
        assert response.status_code == 422

    def test_returns_422_when_category_exceeds_50_chars(self, client, db):
        # Arrange
        project = make_project(db, name="Category Too Long Project")
        payload = {
            "project_id": project.id,
            "source_term": "valid",
            "translated_term": "valid",
            "category": "a" * 51,
        }

        # Act
        response = client.post("/glossary/terms", json=payload)

        # Assert
        assert response.status_code == 422
