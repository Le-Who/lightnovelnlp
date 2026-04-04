from sqlalchemy.orm import declarative_base

# Создаем единый Base для всех моделей
Base = declarative_base()


# Импортируем все модели для регистрации (после установки Base)
from .glossary import (  # noqa: E402
    BatchJob,
    BatchJobItem,
    GlossaryTerm,
    GlossaryVersion,
    TermRelationship,
)
from .project import Chapter, Project  # noqa: E402

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
