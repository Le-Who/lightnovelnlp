from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Создаем таблицы
# Base.metadata.create_all(bind=engine)  # Убрано - используем Alembic для миграций

app = FastAPI(
    title="Light Novel NLP API", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
def health_check():
    return {"status": "healthy"}


@app.get("/info")
def get_info():
    return {
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "gemini_keys_count": len(settings.GEMINI_API_KEYS)
    }
