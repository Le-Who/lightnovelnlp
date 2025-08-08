from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict


# Существующие схемы
class GlossaryTermBase(BaseModel):
    source_term: str
    translated_term: str
    category: str
    context: Optional[str] = None


class GlossaryTermCreate(GlossaryTermBase):
    pass


class GlossaryTermUpdate(BaseModel):
    translated_term: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class GlossaryTermRead(GlossaryTermBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    status: str
    created_at: datetime


class TermRelationshipBase(BaseModel):
    source_term_id: int
    target_term_id: int
    relation_type: str
    confidence: Optional[int] = None
    context: Optional[str] = None


class TermRelationshipCreate(TermRelationshipBase):
    pass


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
    version_number: int
    terms_snapshot: Dict[str, Any]
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
    pass


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
    pass


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
    version_number: int
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    terms_count: int
    approved_terms_count: int
