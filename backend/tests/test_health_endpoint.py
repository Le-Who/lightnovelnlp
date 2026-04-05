"""
Integration tests — Health, root, and info endpoints.

Level: Integration (FastAPI TestClient + SQLite in-memory).
Covers:
  - GET / → 200, returns message/version/environment fields.
  - GET /health → 200, database=connected when DB is up.
  - GET /health → redis field is a string (connected/disconnected).
  - GET /health → 200 with status=degraded when Redis is unavailable.
  - GET /info → 200, returns configuration boolean flags.

Critical behavior: /health is used by Docker/Kubernetes liveness probes.
A 503 or unexpected exception kills the instance.

Design note: Redis is mocked inside the endpoint's import scope
(app.services.cache_service.cache_service) because in-memory tests have no
real Redis. The test patches the module-level singleton that the endpoint
imports at call time.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.integration
class TestRootEndpoint:
    def test_returns_200_with_required_fields(self, client):
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "environment" in data

    def test_message_identifies_the_application(self, client):
        # Act
        response = client.get("/")

        # Assert
        data = response.json()
        assert "Light Novel" in data["message"] or "NLP" in data["message"]


@pytest.mark.integration
class TestHealthEndpoint:
    def _make_redis_mock(self, *, ping_returns: bool):
        """Build a cache_service mock with a redis_client that returns ping_returns."""
        mock_cache = MagicMock()
        mock_cache.redis_client = MagicMock()
        mock_cache.redis_client.ping.return_value = ping_returns
        return mock_cache

    def test_returns_200_when_db_connected_and_redis_connected(self, client):
        # Arrange
        mock_cache = self._make_redis_mock(ping_returns=True)

        with patch("app.main.cache_service", mock_cache):
            # Act
            response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected"
        assert data["redis"] == "connected"
        assert data["status"] == "healthy"

    def test_returns_200_with_degraded_status_when_redis_unavailable(self, client):
        # Arrange — redis_client.ping() returns False → degraded, not unhealthy
        mock_cache = self._make_redis_mock(ping_returns=False)

        with patch("app.main.cache_service", mock_cache):
            # Act
            response = client.get("/health")

        # Assert — HTTP 200, but status=degraded (not unhealthy, DB is still up)
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected"
        assert data["redis"] == "disconnected"
        assert data["status"] == "degraded"

    def test_redis_field_is_always_a_string(self, client):
        # Arrange — simulate exception inside Redis ping
        mock_cache = MagicMock()
        mock_cache.redis_client.ping.side_effect = Exception("timeout")

        with patch("app.main.cache_service", mock_cache):
            # Act
            response = client.get("/health")

        # Assert — redis must be string even when exception thrown
        data = response.json()
        assert "redis" in data
        assert isinstance(data["redis"], str)


@pytest.mark.integration
class TestInfoEndpoint:
    def test_returns_200_with_all_required_configuration_fields(self, client):
        # Act
        response = client.get("/info")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "database_configured" in data
        assert "redis_configured" in data
        assert "gemini_keys_count" in data

    def test_gemini_keys_count_is_a_non_negative_integer(self, client):
        # Act
        response = client.get("/info")

        # Assert
        data = response.json()
        count = data["gemini_keys_count"]
        assert isinstance(count, int)
        assert count >= 0

    def test_database_configured_is_true_when_database_url_set(self, client):
        # Arrange — conftest uses SQLite in-memory (DATABASE_URL is set in env)

        # Act
        response = client.get("/info")

        # Assert
        assert response.json()["database_configured"] is True
