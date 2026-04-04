from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    genre: str = Field("other", max_length=50)


class ProjectCreate(ProjectBase):
    custom_genre_instructions: Optional[str] = Field(None, max_length=5000)
    source_language: str = Field("en", max_length=10)
    target_language: str = Field("ru", max_length=10)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=50)
    custom_genre_instructions: Optional[str] = Field(None, max_length=5000)
    source_language: Optional[str] = Field(None, max_length=10)
    target_language: Optional[str] = Field(None, max_length=10)


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    chapters_count: int = 0
    source_language: str = "en"
    target_language: str = "ru"
    custom_genre_instructions: Optional[str] = None
    embedding_threshold: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ChapterBase(BaseModel):
    title: str = Field(..., max_length=255)
    original_text: str = Field(..., max_length=200000)


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    original_text: Optional[str] = Field(None, max_length=200000)
    translated_text: Optional[str] = Field(None, max_length=200000)


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


class ChapterList(BaseModel):
    id: int
    project_id: int
    title: str
    order: int
    original_text_length: int
    translated_text_length: Optional[int] = None
    analysis_status: str
    translation_status: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
