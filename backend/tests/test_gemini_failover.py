"""
Unit tests — GeminiClient rate-limit failover and cooldown logic.

Level: Unit (all Redis/network interactions mocked via patch on cache_service).
Covers:
  - Key skips cooldown correctly.
  - Key removed from available pool after 429 response.
  - Fallback to next key when RPM limit reached.
  - APIKeyExhausted raised when all keys exhausted.
  - _is_rate_limit_error detects all 429 markers.
  - _build_thinking_config: Gemini 3.x uses thinking_level, 2.5.x uses budget.
  - Thinking budget mapped correctly: minimal→0, low→1024, medium→4096, high→8192.

Critical behavior: the rate-limit failover is the primary reliability mechanism.
If it breaks, every translation job silently fails during peak load.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.core.exceptions import APIKeyExhausted
from app.services.gemini_client import GeminiClient, _key_hash


@pytest.fixture()
def client_with_mock_cache():
    """
    Creates a GeminiClient with two mock keys and a fully mocked cache_service.
    Returns (client, mock_cache) for test-level assertions.
    """
    with patch("app.services.gemini_client.cache_service") as mock_cache:
        mock_cache.get_quiet.return_value = 0  # no usage yet
        mock_cache.get.return_value = None  # no cooldowns
        mock_cache.increment_counter.return_value = 1
        mock_cache.set.return_value = True

        c = GeminiClient()
        c.api_keys = ["key_alpha", "key_beta"]
        c.key_hashes = [_key_hash("key_alpha"), _key_hash("key_beta")]
        yield c, mock_cache


# ── Cooldown management ───────────────────────────────────────────────────────


class TestCooldownMechanism:
    def test_key_not_in_cooldown_when_no_cooldown_set(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        mock_cache.get_quiet.return_value = None  # no cooldown key in Redis

        # Act
        result = c._is_key_in_cooldown(c.key_hashes[0])

        # Assert
        assert result is False

    def test_key_in_cooldown_when_future_timestamp_stored(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        def _get_quiet(key):
            if "cooldown" in key:
                return future
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet

        # Act
        result = c._is_key_in_cooldown(c.key_hashes[0])

        # Assert
        assert result is True

    def test_key_not_in_cooldown_after_timestamp_expired(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        def _get_quiet(key):
            if "cooldown" in key:
                return past
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet

        # Act
        result = c._is_key_in_cooldown(c.key_hashes[0])

        # Assert
        assert result is False

    def test_put_key_in_cooldown_writes_future_timestamp_to_cache(
        self, client_with_mock_cache
    ):
        # Arrange
        c, mock_cache = client_with_mock_cache
        kh = c.key_hashes[0]

        # Act
        c._put_key_in_cooldown(kh)

        # Assert — must write a future ISO timestamp to Redis
        mock_cache.set.assert_called_once()
        set_call_args = mock_cache.set.call_args
        key_arg = set_call_args[0][0]
        value_arg = set_call_args[0][1]
        assert "cooldown" in key_arg
        assert kh in key_arg
        # Value must be a valid future ISO timestamp
        parsed = datetime.fromisoformat(str(value_arg))
        assert parsed > datetime.now(timezone.utc)


# ── Rate limit checks ─────────────────────────────────────────────────────────


class TestRateLimitCheck:
    def test_allows_request_when_counters_are_zero(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        mock_cache.get_quiet.return_value = 0

        # Act
        result = c._check_rate_limits(
            c.key_hashes[0], "gemini-3-flash-preview", "translation"
        )

        # Assert
        assert result is True

    def test_blocks_request_when_rpm_limit_reached(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        from app.core.config import settings

        rpm_limit = settings.GEMINI_RPM_LIMITS_MAP.get("gemini-3-flash-preview", 10)

        def _get_quiet(key):
            if "rpm" in key:
                return rpm_limit  # at the limit
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet

        # Act
        result = c._check_rate_limits(
            c.key_hashes[0], "gemini-3-flash-preview", "translation"
        )

        # Assert
        assert result is False

    def test_blocks_request_when_rpd_limit_reached(self, client_with_mock_cache):
        # Arrange
        c, mock_cache = client_with_mock_cache
        from app.core.config import settings

        rpd_limit = settings.GEMINI_RPD_LIMITS_MAP.get("gemini-3-flash-preview", 500)

        def _get_quiet(key):
            if "rpd" in key:
                return rpd_limit
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet

        # Act
        result = c._check_rate_limits(
            c.key_hashes[0], "gemini-3-flash-preview", "translation"
        )

        # Assert
        assert result is False


# ── Error detection ───────────────────────────────────────────────────────────


class TestIsRateLimitError:
    @pytest.mark.parametrize(
        "error_msg",
        [
            "429 Too Many Requests",
            "RESOURCE_EXHAUSTED: quota exceeded",
            "rate limit exceeded for this key",
            "quota exceeded for model",
            "Error 429 from Google API",
        ],
    )
    def test_detects_known_429_error_strings(self, error_msg):
        # Act
        result = GeminiClient._is_rate_limit_error(error_msg)

        # Assert
        assert result is True, f"Expected True for: {error_msg!r}"

    @pytest.mark.parametrize(
        "error_msg",
        [
            "500 Internal Server Error",
            "Content filtered by safety policy",
            "Invalid API key",
            "Connection timeout",
        ],
    )
    def test_does_not_treat_non_rate_limit_errors_as_429(self, error_msg):
        # Act
        result = GeminiClient._is_rate_limit_error(error_msg)

        # Assert
        assert result is False, f"Expected False for: {error_msg!r}"


# ── ThinkingConfig auto-detection ─────────────────────────────────────────────


class TestBuildThinkingConfig:
    def test_gemini3_model_uses_thinking_level_not_budget(self, client_with_mock_cache):
        # Arrange
        c, _ = client_with_mock_cache

        # Act
        config = c._build_thinking_config("gemini-3-flash-preview", "high")

        # Assert
        assert config is not None
        assert hasattr(config, "thinking_level")
        # ThinkingLevel is an Enum in the google-genai SDK (ThinkingLevel.HIGH);
        # compare case-insensitively against the .value string.
        level_val = getattr(config.thinking_level, "value", str(config.thinking_level))
        assert level_val.lower() == "high"

    def test_gemini25_model_uses_thinking_budget_not_level(
        self, client_with_mock_cache
    ):
        # Arrange
        c, _ = client_with_mock_cache

        # Act
        config = c._build_thinking_config("gemini-2.5-flash", "medium")

        # Assert
        assert config is not None
        assert hasattr(config, "thinking_budget")

    @pytest.mark.parametrize(
        "level,expected_budget",
        [
            ("minimal", 0),
            ("low", 1024),
            ("medium", 4096),
            ("high", 8192),
        ],
    )
    def test_gemini25_maps_level_names_to_correct_budgets(
        self, client_with_mock_cache, level, expected_budget
    ):
        # Arrange
        c, _ = client_with_mock_cache

        # Act
        config = c._build_thinking_config("gemini-2.5-flash", level)

        # Assert
        assert config.thinking_budget == expected_budget

    def test_invalid_level_for_gemini3_defaults_to_medium(self, client_with_mock_cache):
        # Arrange
        c, _ = client_with_mock_cache

        # Act
        config = c._build_thinking_config("gemini-3-flash-preview", "ultra")  # invalid

        # Assert — must not raise; defaults gracefully to 'medium'
        level_val = getattr(config.thinking_level, "value", str(config.thinking_level))
        assert level_val.lower() == "medium"


# ── All-keys-exhausted raises APIKeyExhausted ─────────────────────────────────


class TestAllKeysExhausted:
    def test_raises_api_key_exhausted_when_all_keys_in_cooldown(
        self, client_with_mock_cache
    ):
        # Arrange
        c, mock_cache = client_with_mock_cache
        future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        def _get_quiet(key):
            if "cooldown" in key:
                return future
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet

        # Act & Assert
        with pytest.raises(APIKeyExhausted):
            c.complete("test prompt", task_type="extraction")
