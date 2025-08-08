from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.glossary import TermStatus, TermCategory


class GlossaryTermBase(BaseModel):
    source_term: str
    translated_term: str
    category: TermCategory


class GlossaryTermCreate(GlossaryTermBase):
    project_id: int
    context: Optional[str] = None


class GlossaryTermUpdate(BaseModel):
    translated_term: Optional[str] = None
    category: Optional[TermCategory] = None
    status: Optional[TermStatus] = None


class GlossaryTermRead(GlossaryTermBase):
    id: int
    project_id: int
    status: TermStatus
    context: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TermRelationshipBase(BaseModel):
    source_term_id: int
    target_term_id: int
    relation_type: str
    confidence: Optional[float] = None
    context: Optional[str] = None


class TermRelationshipCreate(TermRelationshipBase):
    project_id: int


class TermRelationshipRead(TermRelationshipBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
