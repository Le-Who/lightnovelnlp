from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.db import engine, Base
    from app.models import *  # Импортируем все модели для регистрации
    from app.api import projects, glossary, processing, translation, batch
    from app.core.config import settings
    from app.core.exceptions import RateLimitExceeded, APIKeyExhausted
    
    logger.info("Configuration loaded successfully")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database configured: {bool(settings.DATABASE_URL)}")
    logger.info(f"Redis configured: {bool(settings.REDIS_URL)}")
    logger.info(f"Gemini keys count: {len(settings.GEMINI_API_KEYS)}")
    
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise


def run_migrations():
    """Выполняет автоматические миграции при запуске, если нужные колонки отсутствуют."""
    from sqlalchemy import text, inspect
    
    try:
        inspector = inspect(engine)
        migrations = []
        
        # Миграции для таблицы chapters
        chapter_columns = [col['name'] for col in inspector.get_columns('chapters')]
        
        if 'analysis_status' not in chapter_columns:
            migrations.append(
                "ALTER TABLE chapters ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'idle' NOT NULL"
            )
        if 'analysis_error' not in chapter_columns:
            migrations.append("ALTER TABLE chapters ADD COLUMN analysis_error TEXT")
        if 'translation_status' not in chapter_columns:
            migrations.append(
                "ALTER TABLE chapters ADD COLUMN translation_status VARCHAR(20) DEFAULT 'idle' NOT NULL"
            )
        if 'translation_error' not in chapter_columns:
            migrations.append("ALTER TABLE chapters ADD COLUMN translation_error TEXT")
        
        # Миграции для таблицы projects
        project_columns = [col['name'] for col in inspector.get_columns('projects')]
        
        if 'source_language' not in project_columns:
            migrations.append(
                "ALTER TABLE projects ADD COLUMN source_language VARCHAR(10) DEFAULT 'en' NOT NULL"
            )
        if 'target_language' not in project_columns:
            migrations.append(
                "ALTER TABLE projects ADD COLUMN target_language VARCHAR(10) DEFAULT 'ru' NOT NULL"
            )
        if 'custom_genre_instructions' not in project_columns:
            migrations.append("ALTER TABLE projects ADD COLUMN custom_genre_instructions TEXT")
        if 'embedding_threshold' not in project_columns:
            migrations.append("ALTER TABLE projects ADD COLUMN embedding_threshold FLOAT")
        
        if migrations:
            with engine.connect() as conn:
                for sql in migrations:
                    logger.info(f"Running migration: {sql}")
                    conn.execute(text(sql))
                conn.commit()
            logger.info(f"Migrations completed: added {len(migrations)} columns")
        else:
            logger.info("No migrations needed - all columns exist")
            
    except Exception as e:
        logger.warning(f"Migration check failed (non-critical): {e}")


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
    lifespan=lifespan
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
        status_code=429,
        content={"detail": exc.message},
        headers=headers
    )


@app.exception_handler(APIKeyExhausted)
async def api_key_exhausted_handler(request: Request, exc: APIKeyExhausted):
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message}
    )


@app.get("/")
def read_root():
    return {
        "message": "Light Novel NLP API", 
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {"status": "healthy", "database": "unknown", "redis": "unknown"}
    
    # Check Database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
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
    except Exception as e:
        health_status["redis"] = "disconnected"
        health_status["status"] = "degraded"
        
    if health_status["status"] == "unhealthy":
        from fastapi import Response
        return Response(content='{"status": "unhealthy"}', status_code=503, media_type="application/json")
        
    return health_status

@app.get("/info")
def get_info():
    return {
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "gemini_keys_count": len(settings.GEMINI_API_KEYS)
    }
