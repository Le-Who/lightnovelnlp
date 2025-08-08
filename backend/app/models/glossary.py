from datetime import datetime
from typing import List

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db import Base


class TermStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"


class TermCategory(enum.Enum):
    CHARACTER = "character"
    LOCATION = "location"
    SKILL = "skill"
    ARTIFACT = "artifact"
    OTHER = "other"


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source_term: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    translated_term: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[TermCategory] = mapped_column(Enum(TermCategory), nullable=False)
    status: Mapped[TermStatus] = mapped_column(Enum(TermStatus), default=TermStatus.PENDING, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)  # Контекст извлечения
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    project: Mapped["Project"] = relationship("Project", back_populates="glossary_terms")
    source_relationships: Mapped[List["TermRelationship"]] = relationship(
        "TermRelationship", 
        foreign_keys="TermRelationship.source_term_id",
        back_populates="source_term"
    )
    target_relationships: Mapped[List["TermRelationship"]] = relationship(
        "TermRelationship", 
        foreign_keys="TermRelationship.target_term_id",
        back_populates="target_term"
    )


class TermRelationship(Base):
    __tablename__ = "term_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source_term_id: Mapped[int] = mapped_column(ForeignKey("glossary_terms.id", ondelete="CASCADE"), index=True)
    target_term_id: Mapped[int] = mapped_column(ForeignKey("glossary_terms.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "friend", "enemy", "location", etc.
    confidence: Mapped[float] = mapped_column(Integer, nullable=True)  # Уверенность в связи (0-100)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)  # Контекст связи
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    project: Mapped["Project"] = relationship("Project")
    source_term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm", 
        foreign_keys=[source_term_id],
        back_populates="source_relationships"
    )
    target_term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm", 
        foreign_keys=[target_term_id],
        back_populates="target_relationships"
    )
