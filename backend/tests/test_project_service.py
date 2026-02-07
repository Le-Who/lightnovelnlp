import sys
from unittest.mock import MagicMock
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.project_service import ProjectService
from app.models.project import Project, Chapter
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


if __name__ == "__main__":
    try:
        test_get_projects()
        test_create_project()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
