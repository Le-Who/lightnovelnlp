import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.api import batch, glossary, processing, projects, translation
    from app.core.config import settings
    from app.core.exceptions import APIKeyExhausted, RateLimitExceeded
    from app.db import engine
    from app.deps import get_db
    import app.models  # noqa: F401  # Импортируем все модели для регистрации

    logger.info("Configuration loaded successfully")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database configured: {bool(settings.DATABASE_URL)}")
    logger.info(f"Redis configured: {bool(settings.REDIS_URL)}")
    logger.info(f"Gemini keys count: {len(settings.GEMINI_API_KEYS)}")

except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise


def run_migrations() -> None:
    """
    Run one-off column additions not yet tracked by Alembic.

    Design constraints:
    - IDEMPOTENT: uses ADD COLUMN IF NOT EXISTS; each statement runs in its own
      transaction so a concurrent pod adding the same column is harmless.
    - SAFE FOR PARALLEL DEPLOYS: no read-then-write (TOCTOU) pattern.
    - NON-BLOCKING: individual failures are logged but do NOT crash startup.

    Long-term goal: graduate these to proper numbered Alembic migrations.
    """
    from sqlalchemy import text

    # (table, column, type+constraints)
    COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
        ("chapters", "analysis_status", "VARCHAR(20) DEFAULT 'idle' NOT NULL"),
        ("chapters", "analysis_error", "TEXT"),
        ("chapters", "translation_status", "VARCHAR(20) DEFAULT 'idle' NOT NULL"),
        ("chapters", "translation_error", "TEXT"),
        ("projects", "source_language", "VARCHAR(10) DEFAULT 'en' NOT NULL"),
        ("projects", "target_language", "VARCHAR(10) DEFAULT 'ru' NOT NULL"),
        ("projects", "custom_genre_instructions", "TEXT"),
        ("projects", "embedding_threshold", "FLOAT"),
    ]

    for table, column, definition in COLUMN_MIGRATIONS:
        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}"
        try:
            with engine.begin() as conn:  # auto-commits on clean exit
                conn.execute(text(sql))
            logger.debug(f"[MIGRATION] Applied: {table}.{column}")
        except Exception as e:
            # Expected on SQLite (no IF NOT EXISTS for ADD COLUMN) or if the
            # column was added by a concurrent process between our checks.
            logger.info(f"[MIGRATION] Skipped {table}.{column}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup
    run_migrations()
    yield
    # Shutdown (nothing needed)


# Создаем таблицы
# Base.metadata.create_all(bind=engine)  # Убрано - используем Alembic для миграций

app = FastAPI(
    title="Light Novel NLP API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(glossary.router, prefix="/glossary", tags=["glossary"])
app.include_router(processing.router, prefix="/processing", tags=["processing"])
app.include_router(translation.router, prefix="/translation", tags=["translation"])
app.include_router(batch.router, prefix="/batch", tags=["batch"])


# Exception handlers for custom service exceptions
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=429, content={"detail": exc.message}, headers=headers
    )


@app.exception_handler(APIKeyExhausted)
async def api_key_exhausted_handler(request: Request, exc: APIKeyExhausted):
    return JSONResponse(status_code=503, content={"detail": exc.message})


@app.get("/")
def read_root():
    return {
        "message": "Light Novel NLP API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {"status": "healthy", "database": "unknown", "redis": "unknown"}

    # Check Database
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"

    # Check Redis
    try:
        from app.services.cache_service import cache_service

        # Use existing ping checking mechanism or just get a dummy key
        res = cache_service.redis_client.ping() if cache_service.redis_client else False
        health_status["redis"] = "connected" if res else "disconnected"
        if not res:
            health_status["status"] = "degraded"
    except Exception:
        health_status["redis"] = "disconnected"
        health_status["status"] = "degraded"

    if health_status["status"] == "unhealthy":
        from fastapi import Response

        return Response(
            content='{"status": "unhealthy"}',
            status_code=503,
            media_type="application/json",
        )

    return health_status


@app.get("/info")
def get_info():
    return {
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "gemini_keys_count": len(settings.GEMINI_API_KEYS),
    }
