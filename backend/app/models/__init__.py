from sqlalchemy.ext.declarative import declarative_base

# Создаем единый Base для всех моделей
Base = declarative_base()

# Импортируем все модели для регистрации
from .project import Project, Chapter
from .glossary import (
    GlossaryTerm, 
    TermRelationship, 
    GlossaryVersion, 
    BatchJob, 
    BatchJobItem
)

__all__ = [
    'Base',
    'Project',
    'Chapter', 
    'GlossaryTerm',
    'TermRelationship',
    'GlossaryVersion',
    'BatchJob',
    'BatchJobItem'
]
