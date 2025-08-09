from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

# Создаем движок базы данных
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,            # Проверяем соединение перед использованием
    pool_recycle=180,              # Пересоздаем соединения чаще (3 минуты) для free-tier прокси
    pool_size=5,                   # Маленький пул на free-tier
    max_overflow=5,
    pool_timeout=10,
    echo=settings.is_development   # Логируем SQL только в разработке
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
