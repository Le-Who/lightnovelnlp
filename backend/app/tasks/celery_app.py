from __future__ import annotations

from celery import Celery

from app.core.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    "lightnovel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.process_chapter",
        "app.tasks.batch_processor"
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 час
    task_always_eager=False,  # В продакшене False
    task_eager_propagates=True,
)
