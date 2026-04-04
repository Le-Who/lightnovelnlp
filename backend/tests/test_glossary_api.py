"""
Integration tests — Glossary API pagination endpoints.

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - GET /glossary/{project_id}/terms → default limit of 50 terms enforced.
  - GET /glossary/{project_id}/terms?limit=10 → overrides default limit.
  - GET /glossary/{project_id}/terms?limit=100 → respects explicit large limit.

AAA fixes applied over the original:
  - Removed print() debug statements (not part of test assertions).
  - Removed time.time() timing measurements (fragile, not a behavioral assertion).
  - Extracted repeated glossary population into a helper function.
  - Separated Arrange sections from Act.
"""

import pytest
from conftest import make_project

from app.models.glossary import GlossaryTerm, TermStatus


def _populate_glossary(db, project_id: int, count: int) -> None:
    """Adds `count` approved glossary terms to the DB for the given project."""
    terms = [
        GlossaryTerm(
            project_id=project_id,
            source_term=f"Term {i}",
            translated_term=f"Translation {i}",
            category="other",
            status=TermStatus.APPROVED,
        )
        for i in range(count)
    ]
    db.add_all(terms)
    db.commit()


@pytest.mark.integration
class TestGlossaryTermsPagination:
    def test_default_limit_returns_50_terms_when_150_exist(self, client, db):
        # Arrange
        project = make_project(db, name="Pagination Test Project")
        _populate_glossary(db, project.id, count=150)

        # Act
        response = client.get(f"/glossary/{project.id}/terms")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 50

    def test_explicit_limit_10_returns_exactly_10_terms(self, client, db):
        # Arrange
        project = make_project(db, name="Limit=10 Test Project")
        _populate_glossary(db, project.id, count=150)

        # Act
        response = client.get(f"/glossary/{project.id}/terms?limit=10")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 10

    def test_explicit_limit_100_returns_exactly_100_terms(self, client, db):
        # Arrange
        project = make_project(db, name="Limit=100 Test Project")
        _populate_glossary(db, project.id, count=150)

        # Act
        response = client.get(f"/glossary/{project.id}/terms?limit=100")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 100
