from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# Существующие схемы
class GlossaryTermBase(BaseModel):
    source_term: str = Field(..., min_length=1, max_length=255)
    translated_term: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., max_length=50)
    context: Optional[str] = Field(None, max_length=5000)


class GlossaryTermCreate(GlossaryTermBase):
    project_id: int


class GlossaryTermUpdate(BaseModel):
    source_term: Optional[str] = Field(None, min_length=1, max_length=255)
    translated_term: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    context: Optional[str] = Field(None, max_length=5000)


class GlossaryTermRead(GlossaryTermBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    status: str
    frequency: int
    created_at: datetime
    approved_at: Optional[datetime] = None
    first_chapter_id: Optional[int] = None
    last_chapter_id: Optional[int] = None
    first_chapter_order: Optional[int] = None  # Новое поле: порядковый номер
    last_chapter_order: Optional[int] = None   # Новое поле: порядковый номер
    
    # Visualization metrics
    occurrences_data: Optional[List[Dict[str, int]]] = None  # [{chapter_id: 1, freq: 5}, ...]
    centrality_score: Optional[int] = 0

    # We could add nested chapter info here if we define a schema for it
    # first_chapter: Optional[ChapterInfo] = None 
    # But for now, let's stick to IDs or let frontend handle it if it has the map.
    # actually, let's include a minimal string representation or similar if feasible.



class TermRelationshipBase(BaseModel):
    source_term_id: int
    target_term_id: int
    relation_type: str
    confidence: Optional[int] = None
    context: Optional[str] = None


class TermRelationshipCreate(TermRelationshipBase):
    project_id: int


class TermRelationshipRead(TermRelationshipBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    created_at: datetime


# Новые схемы для версионирования
class GlossaryVersionBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GlossaryVersionCreate(GlossaryVersionBase):
    pass


class GlossaryVersionRead(GlossaryVersionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    version_name: str
    terms_data: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str] = None


class GlossaryVersionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Схемы для пакетной обработки
class BatchJobBase(BaseModel):
    job_type: str
    job_data: Optional[Dict[str, Any]] = None


class BatchJobCreate(BatchJobBase):
    project_id: int


class BatchJobRead(BatchJobBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    progress_percentage: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchJobUpdate(BaseModel):
    status: Optional[str] = None
    processed_items: Optional[int] = None
    failed_items: Optional[int] = None
    progress_percentage: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchJobItemBase(BaseModel):
    item_type: str
    item_id: int


class BatchJobItemCreate(BatchJobItemBase):
    project_id: int
    batch_job_id: int


class BatchJobItemRead(BatchJobItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    batch_job_id: int
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchJobItemUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Схемы для API ответов
class BatchJobStatus(BaseModel):
    job_id: int
    status: str
    progress_percentage: int
    processed_items: int
    total_items: int
    failed_items: int
    estimated_time_remaining: Optional[int] = None  # в секундах


class GlossaryVersionInfo(BaseModel):
    version_id: int
    version_name: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    terms_count: int
    approved_terms_count: int
