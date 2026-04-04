from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from . import Base


class TermStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TermCategory(str, Enum):
    CHARACTER = "character"
    LOCATION = "location"
    SKILL = "skill"
    ARTIFACT = "artifact"
    OTHER = "other"


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_term = Column(String(255), nullable=False)
    translated_term = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default=TermStatus.PENDING)
    context = Column(Text, nullable=True)
    frequency = Column(Integer, default=1, server_default="1")  # Частота встречаемости
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)  # When the term was approved/rejected

    # New metrics
    first_chapter_id = Column(
        Integer, ForeignKey("chapters.id"), nullable=True, index=True
    )
    last_chapter_id = Column(
        Integer, ForeignKey("chapters.id"), nullable=True, index=True
    )

    # Связи
    project = relationship("Project", back_populates="glossary_terms")
    source_relationships = relationship(
        "TermRelationship",
        foreign_keys="TermRelationship.source_term_id",
        back_populates="source_term",
    )
    target_relationships = relationship(
        "TermRelationship",
        foreign_keys="TermRelationship.target_term_id",
        back_populates="target_term",
    )

    # Chapter relationships
    first_chapter = relationship("Chapter", foreign_keys=[first_chapter_id])
    last_chapter = relationship("Chapter", foreign_keys=[last_chapter_id])

    occurrences = relationship(
        "TermOccurrence", back_populates="term", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_glossary_terms_project_id", "project_id"),
        UniqueConstraint(
            "project_id", "source_term", name="uq_glossary_term_per_project"
        ),
    )


class TermRelationship(Base):
    __tablename__ = "term_relationships"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_term_id = Column(
        Integer, ForeignKey("glossary_terms.id"), nullable=False, index=True
    )
    target_term_id = Column(
        Integer, ForeignKey("glossary_terms.id"), nullable=False, index=True
    )
    relation_type = Column(String(50), nullable=False)
    confidence = Column(Integer, nullable=True)  # 0-100
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Связи
    project = relationship("Project", back_populates="term_relationships")
    source_term = relationship(
        "GlossaryTerm",
        foreign_keys=[source_term_id],
        back_populates="source_relationships",
    )
    target_term = relationship(
        "GlossaryTerm",
        foreign_keys=[target_term_id],
        back_populates="target_relationships",
    )


class GlossaryVersion(Base):
    __tablename__ = "glossary_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    version_name = Column(String(255), nullable=False)  # Название версии
    description = Column(Text, nullable=True)  # Описание изменений
    terms_data = Column(JSON, nullable=False)  # Снимок терминов в JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)  # Кто создал версию

    # Связи
    project = relationship("Project", back_populates="glossary_versions")


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # 'analyze', 'translate', 'process'
    status = Column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Дополнительные данные для разных типов задач
    job_data = Column(JSON, nullable=True)  # Дополнительные параметры

    # Связи
    project = relationship("Project", back_populates="batch_jobs")
    items = relationship(
        "BatchJobItem", back_populates="batch_job", cascade="all, delete-orphan"
    )


class BatchJobItem(Base):
    __tablename__ = "batch_job_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    batch_job_id = Column(
        Integer, ForeignKey("batch_jobs.id"), nullable=False, index=True
    )
    item_type = Column(String(50), nullable=False)  # 'chapter', 'term', etc.
    item_id = Column(Integer, nullable=False)  # ID элемента (главы, термина и т.д.)
    status = Column(
        String(20), default="pending"
    )  # pending, processing, completed, failed
    result = Column(JSON, nullable=True)  # Результат обработки
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Связи
    project = relationship("Project", back_populates="batch_job_items")
    batch_job = relationship("BatchJob", back_populates="items")


class TermOccurrence(Base):
    __tablename__ = "term_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    term_id = Column(
        Integer, ForeignKey("glossary_terms.id"), nullable=False, index=True
    )
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False, index=True)
    frequency = Column(Integer, nullable=False, default=1)

    # Relationships
    project = relationship("Project")
    term = relationship("GlossaryTerm", back_populates="occurrences")
    chapter = relationship("Chapter")

    __table_args__ = (
        UniqueConstraint("term_id", "chapter_id", name="uq_term_occurrence"),
    )
