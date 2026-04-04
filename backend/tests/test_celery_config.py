"""
Unit tests — Celery application configuration.

Level: Unit (no DB, no network; imports real app config).
Covers:
  - broker_url matches REDIS_URL from settings.
  - result_backend matches REDIS_URL from settings.
  - task_serializer is JSON (required for cross-environment compatibility).
  - timezone matches GEMINI_API_RESET_TIMEZONE (RPD reset uses same timezone).

AAA fixes applied over the original:
  - Separated Arrange (import), Act (inspect), Assert (verify) sections explicitly.
  - Each config property is now a dedicated test for isolated failure signals.
"""

import pytest

try:
    import celery  # noqa: F401

    _CELERY_AVAILABLE = True
except ImportError:
    _CELERY_AVAILABLE = False


@pytest.mark.skipif(not _CELERY_AVAILABLE, reason="celery not installed")
@pytest.mark.unit
class TestCeleryConfiguration:
    def test_broker_url_matches_redis_url_from_settings(self):
        # Arrange
        from app.core.celery_app import celery_app
        from app.core.config import settings

        # Act
        broker = celery_app.conf.broker_url

        # Assert
        assert broker == settings.REDIS_URL

    def test_result_backend_matches_redis_url_from_settings(self):
        # Arrange
        from app.core.celery_app import celery_app
        from app.core.config import settings

        # Act
        backend = celery_app.conf.result_backend

        # Assert
        assert backend == settings.REDIS_URL

    def test_task_serializer_is_json(self):
        # Arrange
        from app.core.celery_app import celery_app

        # Act
        serializer = celery_app.conf.task_serializer

        # Assert
        assert serializer == "json"

    def test_timezone_matches_gemini_reset_timezone(self):
        # Arrange
        from app.core.celery_app import celery_app
        from app.core.config import settings

        # Act
        tz = celery_app.conf.timezone

        # Assert
        assert tz == settings.GEMINI_API_RESET_TIMEZONE
