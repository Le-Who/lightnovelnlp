from app.core.celery_app import celery_app
from app.core.config import settings

def test_celery_config():
    assert celery_app.conf.broker_url == settings.REDIS_URL
    assert celery_app.conf.result_backend == settings.REDIS_URL
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.timezone == settings.GEMINI_API_RESET_TIMEZONE
    print("Celery config verified successfully")

if __name__ == "__main__":
    test_celery_config()
