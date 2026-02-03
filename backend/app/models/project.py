from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from . import Base


class ProjectGenre(str, Enum):
    FANTASY = "fantasy"
    SCIFI = "scifi"
    ROMANCE = "romance"
    ACTION = "action"
    MYSTERY = "mystery"
    HORROR = "horror"
    SLICE_OF_LIFE = "slice_of_life"
    ADVENTURE = "adventure"
    WUXIA = "wuxia"           # Китайское боевое фэнтези
    XIANXIA = "xianxia"       # Культивация бессмертия
    LITRPG = "litrpg"         # Игровые механики
    ISEKAI = "isekai"         # Попаданцы
    OTHER = "other"


class SourceLanguage(str, Enum):
    """Язык оригинала произведения."""
    CHINESE = "zh"      # 中文
    JAPANESE = "ja"     # 日本語
    KOREAN = "ko"       # 한국어
    ENGLISH = "en"      # English
    OTHER = "other"


class AnalysisStatus(str, Enum):
    """Статус анализа главы."""
    IDLE = "idle"              # Не запущен
    PENDING = "pending"        # Ожидает в очереди
    EXTRACTING = "extracting"  # Извлечение терминов
    RELATIONSHIPS = "relationships"  # Анализ связей
    SUMMARIZING = "summarizing"  # Создание саммари
    COMPLETED = "completed"    # Завершен
    FAILED = "failed"          # Ошибка


class TranslationStatus(str, Enum):
    """Статус перевода главы."""
    IDLE = "idle"
    PENDING = "pending"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    genre = Column(String(50), default=ProjectGenre.OTHER.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Новые поля для улучшенного NLP
    source_language = Column(String(10), default=SourceLanguage.ENGLISH.value, nullable=False)
    target_language = Column(String(10), default="ru", nullable=False)  # Целевой язык перевода
    custom_genre_instructions = Column(Text, nullable=True)  # Кастомные инструкции для жанра
    
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
    translated_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    order = Column(Integer, default=0, nullable=False)  # Порядок главы в проекте
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    
    # Статусы для отслеживания async операций
    analysis_status = Column(String(20), default=AnalysisStatus.IDLE.value, nullable=False)
    analysis_error = Column(Text, nullable=True)
    translation_status = Column(String(20), default=TranslationStatus.IDLE.value, nullable=False)
    translation_error = Column(Text, nullable=True)
    
    # Связи
    project = relationship("Project", back_populates="chapters")

    __table_args__ = (
        Index("ix_chapters_project_id", "project_id"),
        Index("ix_chapters_order", "project_id", "order"),  # Индекс для сортировки
    )

