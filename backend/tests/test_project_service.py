import sys
from unittest.mock import MagicMock
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.services.project_service import ProjectService
from app.models.project import Project, Chapter
from app.models.glossary import (
    GlossaryTerm, TermRelationship, GlossaryVersion,
    BatchJob, BatchJobItem
)
from app.schemas.project import ProjectCreate


def test_get_projects():
    print("Testing get_projects...")
    # Mock database session
    db = MagicMock(spec=Session)

    # Mock query chain
    mock_query = db.query.return_value
    mock_outerjoin = mock_query.outerjoin.return_value
    mock_group_by = mock_outerjoin.group_by.return_value
    mock_order_by = mock_group_by.order_by.return_value

    # Setup mock data
    mock_project = MagicMock(spec=Project)
    mock_project.id = 1
    mock_project.name = "Test Project"

    mock_count = 5

    # Return a list of tuples (project, count)
    # The actual query returns [(Project, count), ...]
    mock_order_by.all.return_value = [(mock_project, mock_count)]

    # Call the service method
    projects = ProjectService.get_projects(db)

    # Verify results
    assert len(projects) == 1
    assert projects[0] == mock_project
    assert projects[0].chapters_count == 5
    print("get_projects passed!")


def test_create_project():
    print("Testing create_project...")
    db = MagicMock(spec=Session)
    payload = MagicMock(spec=ProjectCreate)
    payload.name = "New Project"
    payload.genre = "fantasy"
    payload.custom_genre_instructions = "test"

    # Mock existing project check (None found)
    db.query.return_value.filter.return_value.first.return_value = None

    # Mock add/commit/refresh
    def refresh_side_effect(obj):
        obj.id = 1

    db.refresh.side_effect = refresh_side_effect

    project = ProjectService.create_project(db, payload)

    assert project.name == "New Project"
    assert project.genre == "fantasy"
    assert project.id == 1
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    print("create_project passed!")


def test_delete_project():
    print("Testing delete_project...")
    db = MagicMock(spec=Session)
    project_id = 1

    # 1. Test Project Not Found
    # Mock db.get to return None
    db.get.return_value = None

    try:
        ProjectService.delete_project(db, project_id)
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 404
        assert e.detail == "Project not found"

    # Reset mocks for next part
    db.reset_mock()

    # 2. Test Successful Deletion
    mock_project = MagicMock(spec=Project)
    mock_project.id = project_id
    db.get.return_value = mock_project

    # Mock query delete chains
    # db.query(...) returns a mock query object
    mock_query = db.query.return_value
    # filter(...) returns the same mock query object (or another one, typically chained)
    mock_filter = mock_query.filter.return_value
    # delete(...) is called on the filter result

    ProjectService.delete_project(db, project_id)

    # Verify db.get was called
    db.get.assert_called_with(Project, project_id)

    # Verify dependencies deletion
    # We expect multiple calls to db.query().filter().delete()
    # Let's verify that db.query was called with the correct models
    # and subsequent filter/delete calls happened.

    # Verify we queried for each related model
    expected_models = [
        TermRelationship, GlossaryTerm, GlossaryVersion,
        BatchJobItem, BatchJob, Chapter
    ]

    # Check calls to db.query
    # db.query might be called multiple times.
    # We can inspect db.query.call_args_list
    query_calls = [args[0][0] for args in db.query.call_args_list]

    for model in expected_models:
        assert model in query_calls, f"Delete query for {model} not initiated"

    # Verify delete() was called for each query
    # Since we reused the mock chain, mock_filter.delete was likely called multiple times
    assert mock_filter.delete.call_count == len(expected_models)
    # Check arguments for delete calls
    mock_filter.delete.assert_called_with(synchronize_session=False)

    # Verify project deletion
    db.delete.assert_called_with(mock_project)
    db.commit.assert_called_once()

    print("delete_project passed!")


if __name__ == "__main__":
    try:
        test_get_projects()
        test_create_project()
        test_delete_project()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
