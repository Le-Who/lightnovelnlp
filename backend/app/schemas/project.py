from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.project import ProjectGenre


class ProjectBase(BaseModel):
    name: str
    genre: ProjectGenre = ProjectGenre.OTHER


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChapterBase(BaseModel):
    title: str
    original_text: str


class ChapterCreate(ChapterBase):
    pass


class ChapterRead(ChapterBase):
    id: int
    project_id: int
    translated_text: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
