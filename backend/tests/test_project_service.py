"""
Unit tests — ProjectService.

Level: Unit (MagicMock DB session, no real DB connection).
Covers:
  - get_projects: returns projects with chapter counts.
  - create_project: creates, commits, returns project.
  - delete_project: 404 on missing, cascades deletions, commits on success.

Original issues:
  - Multiple independent behaviors tested inside single functions (delete_project).
  - `if __name__ == "__main__"` block in test file (not a pytest pattern).
  - `sys.path.append` hack (unnecessary when running via pytest from the project root).
  - `print()` debug statements scattered through the test body.
  - Two scenarios in test_delete_project share state via db.reset_mock() which is fragile.
"""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.services.project_service import ProjectService
from app.models.project import Project, Chapter
from app.models.glossary import (
    GlossaryTerm,
    TermRelationship,
    GlossaryVersion,
    BatchJob,
    BatchJobItem,
)
from app.schemas.project import ProjectCreate


# ── get_projects ──────────────────────────────────────────────────────────────


class TestGetProjects:
    def test_returns_list_of_projects(self):
        # Arrange
        db = MagicMock(spec=Session)
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.name = "Test Project"

        (
            db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.all.return_value
        ) = [(mock_project, 5)]

        # Act
        result = ProjectService.get_projects(db)

        # Assert
        assert len(result) == 1
        assert result[0] == mock_project

    def test_annotates_project_with_chapters_count(self):
        # Arrange
        db = MagicMock(spec=Session)
        mock_project = MagicMock(spec=Project)

        (
            db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.all.return_value
        ) = [(mock_project, 7)]

        # Act
        ProjectService.get_projects(db)

        # Assert
        assert mock_project.chapters_count == 7

    def test_returns_empty_list_when_no_projects_exist(self):
        # Arrange
        db = MagicMock(spec=Session)
        (
            db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.all.return_value
        ) = []

        # Act
        result = ProjectService.get_projects(db)

        # Assert
        assert result == []


# ── create_project ────────────────────────────────────────────────────────────


class TestCreateProject:
    def _make_payload(self, name="New Project", genre="fantasy"):
        payload = MagicMock(spec=ProjectCreate)
        payload.name = name
        payload.genre = genre
        payload.custom_genre_instructions = None
        return payload

    def test_returns_project_with_correct_attributes(self):
        # Arrange
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        def _set_id(obj):
            obj.id = 42

        db.refresh.side_effect = _set_id
        payload = self._make_payload(name="Xianxia Novel", genre="xianxia")

        # Act
        result = ProjectService.create_project(db, payload)

        # Assert
        assert result.name == "Xianxia Novel"
        assert result.genre == "xianxia"
        assert result.id == 42

    def test_persists_project_via_add_commit_refresh(self):
        # Arrange
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        payload = self._make_payload()

        # Act
        ProjectService.create_project(db, payload)

        # Assert
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()


# ── delete_project ────────────────────────────────────────────────────────────


class TestDeleteProject:
    def test_raises_404_when_project_does_not_exist(self):
        # Arrange
        db = MagicMock(spec=Session)
        db.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            ProjectService.delete_project(db, project_id=999)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    def test_cascades_deletion_to_all_related_models(self):
        # Arrange
        db = MagicMock(spec=Session)
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        db.get.return_value = mock_project

        # Act
        ProjectService.delete_project(db, project_id=1)

        # Assert — every related model must have had its records deleted
        queried_models = [call_args[0][0] for call_args in db.query.call_args_list]
        expected_models = [
            TermRelationship,
            GlossaryTerm,
            GlossaryVersion,
            BatchJobItem,
            BatchJob,
            Chapter,
        ]
        for model in expected_models:
            assert model in queried_models, (
                f"Expected delete cascade for {model.__name__}"
            )

    def test_deletes_the_project_itself_and_commits(self):
        # Arrange
        db = MagicMock(spec=Session)
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        db.get.return_value = mock_project

        # Act
        ProjectService.delete_project(db, project_id=1)

        # Assert
        db.delete.assert_called_once_with(mock_project)
        db.commit.assert_called_once()
