from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.project import ProjectGenre


class ProjectBase(BaseModel):
    name: str
    genre: str = "other"


class ProjectCreate(ProjectBase):
    custom_genre_instructions: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChapterBase(BaseModel):
    title: str
    original_text: str


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None


class ChapterRead(ChapterBase):
    id: int
    project_id: int
    order: int
    translated_text: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    analysis_status: str = "idle"
    analysis_error: Optional[str] = None
    translation_status: str = "idle"
    translation_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
