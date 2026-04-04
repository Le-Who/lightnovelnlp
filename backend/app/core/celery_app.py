from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "lightnovelnlp", broker=settings.REDIS_URL, backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.GEMINI_API_RESET_TIMEZONE,
    enable_utc=True,
    task_routes={
        "app.tasks.nlp_tasks.*": {"queue": "nlp_queue"},
    },
)
