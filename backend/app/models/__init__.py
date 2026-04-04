from sqlalchemy.orm import declarative_base

# Создаем единый Base для всех моделей
Base = declarative_base()


# Импортируем все модели для регистрации
from .glossary import (
    BatchJob,
    BatchJobItem,
    GlossaryTerm,
    GlossaryVersion,
    TermRelationship,
)
from .project import Chapter, Project

__all__ = [
    "Base",
    "Project",
    "Chapter",
    "GlossaryTerm",
    "TermRelationship",
    "GlossaryVersion",
    "BatchJob",
    "BatchJobItem",
]
