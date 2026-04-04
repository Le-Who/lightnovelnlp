from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class NLPBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Term(NLPBaseModel):
    source_term: str = Field(..., description="Оригинальный термин")
    translated_term: str = Field(..., description="Предложенный перевод")
    category: Literal["character", "location", "skill", "artifact", "other"] = Field(
        ..., description="Категория термина"
    )
    context: Optional[str] = Field(None, description="Контекст извлечения")
    auto_approve: bool = Field(False, description="Флаг автоматического утверждения")
    confidence: int = Field(50, ge=0, le=100, description="Уверенность модели")


class TermExtractionResponse(NLPBaseModel):
    terms: List[Term] = Field(default_factory=list)


class Relationship(NLPBaseModel):
    source_term: str
    target_term: str
    relation_type: str
    confidence: int = Field(50, ge=0, le=100)
    context: Optional[str] = None


class RelationshipResponse(NLPBaseModel):
    relationships: List[Relationship] = Field(default_factory=list)
