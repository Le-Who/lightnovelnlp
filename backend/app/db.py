from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Создаем движок базы данных
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    pool_recycle=300,    # Пересоздаем соединения каждые 5 минут
    echo=settings.is_development  # Логируем SQL только в разработке
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()
