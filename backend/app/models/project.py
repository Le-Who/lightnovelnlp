from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from . import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    glossary_terms = relationship("GlossaryTerm", back_populates="project", cascade="all, delete-orphan")
    term_relationships = relationship("TermRelationship", back_populates="project", cascade="all, delete-orphan")
    glossary_versions = relationship("GlossaryVersion", back_populates="project", cascade="all, delete-orphan")
    batch_jobs = relationship("BatchJob", back_populates="project", cascade="all, delete-orphan")
    batch_job_items = relationship("BatchJobItem", back_populates="project", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)  # Добавлено в Этапе 3
    summary = Column(Text, nullable=True)  # Добавлено в Этапе 4
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    project = relationship("Project", back_populates="chapters")
