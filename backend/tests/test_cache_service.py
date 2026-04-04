"""
Unit tests — CacheService.

Level: Unit (all Redis clients mocked; no real network calls).
AAA pattern strictly followed throughout.

Issues fixed from prior version:
  - H-1: service.__init__() anti-pattern removed; each test gets a
          fresh CacheService() instance constructed inside a patch context.
  - H-2: Weak `call_count == 2` assertion replaced with explicit flow
          assertions that catch real regressions.
"""

from unittest.mock import MagicMock, patch, call

from app.services.cache_service import CacheService


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_service_with_tcp_only(mock_tcp_client):
    """Return a CacheService configured for TCP-only (no Upstash credentials)."""
    with (
        patch("app.services.cache_service.settings") as mock_settings,
        patch(
            "app.services.cache_service.redis.from_url", return_value=mock_tcp_client
        ),
    ):
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.UPSTASH_REDIS_REST_URL = None
        mock_settings.UPSTASH_REDIS_REST_TOKEN = None
        mock_settings.GEMINI_API_RESET_TIMEZONE = "UTC"
        service = CacheService()
    return service


def _make_service_with_rest_and_tcp(mock_rest_client, mock_tcp_client):
    """Return a CacheService configured with both REST and TCP clients."""

    with (
        patch("app.services.cache_service.settings") as mock_settings,
        patch(
            "app.services.cache_service.redis.from_url", return_value=mock_tcp_client
        ),
        patch("app.services.cache_service.UpstashRedis", return_value=mock_rest_client),
    ):
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.UPSTASH_REDIS_REST_URL = "https://upstash.io"
        mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_settings.GEMINI_API_RESET_TIMEZONE = "UTC"
        mock_rest_client.ping.return_value = True  # health check passes
        service = CacheService()
    return service


# ── Initialization ────────────────────────────────────────────────────────────


class TestCacheServiceInit:
    def test_initializes_tcp_only_when_upstash_credentials_missing(self):
        # Arrange + Act
        mock_tcp = MagicMock()
        service = _make_service_with_tcp_only(mock_tcp)

        # Assert
        assert service.rest_client is None
        assert service.redis_client is mock_tcp

    def test_initializes_rest_client_when_upstash_credentials_present(self):
        # Arrange + Act
        mock_rest = MagicMock()
        mock_tcp = MagicMock()
        service = _make_service_with_rest_and_tcp(mock_rest, mock_tcp)

        # Assert
        assert service.rest_client is mock_rest


# ── Get Values (Fallback Logic) ───────────────────────────────────────────────


class TestCacheServiceGet:
    def test_returns_value_from_rest_client_when_configured(self):
        # Arrange
        mock_rest = MagicMock()
        mock_tcp = MagicMock()
        service = _make_service_with_rest_and_tcp(mock_rest, mock_tcp)
        mock_rest.get.return_value = '{"data": "success"}'

        # Act
        result = service.get("test_key")

        # Assert
        assert result == {"data": "success"}
        mock_rest.get.assert_called_once_with("test_key")
        mock_tcp.get.assert_not_called()  # TCP not used when REST succeeds

    def test_falls_back_to_tcp_when_rest_client_raises(self):
        # Arrange
        mock_rest = MagicMock()
        mock_tcp = MagicMock()
        service = _make_service_with_rest_and_tcp(mock_rest, mock_tcp)
        mock_rest.get.side_effect = Exception("REST Timeout")
        mock_tcp.ping.return_value = True
        mock_tcp.get.return_value = b'{"data": "tcp_success"}'

        # Act
        result = service.get("test_key")

        # Assert
        assert result == {"data": "tcp_success"}
        mock_rest.get.assert_called_once_with("test_key")  # REST was tried
        mock_tcp.get.assert_called_once_with("test_key")  # TCP was the fallback

    def test_returns_none_when_both_clients_fail(self):
        # Arrange
        mock_rest = MagicMock()
        mock_tcp = MagicMock()
        service = _make_service_with_rest_and_tcp(mock_rest, mock_tcp)

        mock_rest.get.side_effect = Exception("REST Crash")
        # Simulate: first get() fails, ping() succeeds (no reconnect), retry get() also fails
        mock_tcp.ping.return_value = True
        mock_tcp.get.side_effect = Exception("TCP Crash")

        # Act
        result = service.get("test_key")

        # Assert
        assert result is None
        # Verify both REST and TCP were attempted (REST first, then TCP with one retry)
        mock_rest.get.assert_called_once_with("test_key")
        # TCP.get is called twice: initial attempt + retry after sleep
        assert mock_tcp.get.call_count == 2
        assert mock_tcp.get.call_args_list == [call("test_key"), call("test_key")]


# ── Counter Operations ────────────────────────────────────────────────────────


class TestIncrementCounter:
    def test_increments_and_sets_ttl_on_first_call(self):
        # Arrange
        mock_tcp = MagicMock()
        service = _make_service_with_tcp_only(mock_tcp)
        mock_tcp.incr.return_value = 1  # counter did not exist before

        # Act
        result = service.increment_counter("limit_key", ttl=60)

        # Assert
        assert result == 1
        mock_tcp.expire.assert_called_once_with("limit_key", 60)

    def test_does_not_set_ttl_on_subsequent_increments(self):
        # Arrange
        mock_tcp = MagicMock()
        service = _make_service_with_tcp_only(mock_tcp)
        mock_tcp.incr.return_value = 5  # counter already exists

        # Act
        result = service.increment_counter("limit_key", ttl=60)

        # Assert
        assert result == 5
        mock_tcp.expire.assert_not_called()
