import pytest

try:
    import celery  # noqa: F401
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False


@pytest.mark.skipif(not HAS_CELERY, reason="celery not installed")
def test_celery_config():
    from app.core.celery_app import celery_app
    from app.core.config import settings

    assert celery_app.conf.broker_url == settings.REDIS_URL
    assert celery_app.conf.result_backend == settings.REDIS_URL
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.timezone == settings.GEMINI_API_RESET_TIMEZONE
