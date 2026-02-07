import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate
from app.models.project import ProjectGenre, Project

def test_create_project_success(db: Session):
    # Setup
    payload = ProjectCreate(
        name="Test Project",
        genre="fantasy",
        custom_genre_instructions="No dragons"
    )

    # Execute
    project = ProjectService.create_project(db, payload)

    # Verify
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.genre == "fantasy"
    assert project.custom_genre_instructions == "No dragons"

    # Verify in DB
    db_project = db.query(Project).filter(Project.id == project.id).first()
    assert db_project is not None
    assert db_project.name == "Test Project"


def test_create_project_duplicate_name(db: Session):
    # Setup
    payload1 = ProjectCreate(name="Unique Project", genre="scifi")
    ProjectService.create_project(db, payload1)

    payload2 = ProjectCreate(name="Unique Project", genre="romance")

    # Execute & Verify
    with pytest.raises(HTTPException) as excinfo:
        ProjectService.create_project(db, payload2)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Project with this name already exists"


def test_create_project_genre_handling(db: Session):
    # Test with Enum member if possible, though Pydantic model expects str.
    # Since ProjectGenre is a str enum, it works directly.

    # Case 1: Enum member
    payload_enum = ProjectCreate(name="Enum Project", genre=ProjectGenre.HORROR)
    project_enum = ProjectService.create_project(db, payload_enum)
    assert project_enum.genre == "horror"

    # Case 2: String value
    payload_str = ProjectCreate(name="String Project", genre="mystery")
    project_str = ProjectService.create_project(db, payload_str)
    assert project_str.genre == "mystery"
