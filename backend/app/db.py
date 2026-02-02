from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

# Создаем движок базы данных
engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 180,
    "echo": settings.is_development
}

if "sqlite" not in settings.DATABASE_URL:
    engine_args.update({
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 10,
    })
else:
    # SQLite-specific args
    engine_args.update({
        "connect_args": {"check_same_thread": False}
    })

engine = create_engine(
    settings.DATABASE_URL,
    **engine_args
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
