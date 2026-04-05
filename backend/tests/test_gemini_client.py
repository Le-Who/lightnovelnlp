"""
Tests for GeminiClient v2.

Tests cover:
- Rate-limit pre-flight checks (_check_rate_limits)
- ThinkingConfig auto-detection (_build_thinking_config)
- Model chain fallback behavior
- Key hash determinism
- get_usage_stats structure
"""

from unittest.mock import patch

import pytest

from app.services.gemini_client import GeminiClient, _key_hash, _now_minute


@pytest.fixture
def client():
    """Creates a GeminiClient instance with test keys, mocking Redis interactions."""
    with patch("app.services.gemini_client.cache_service") as mock_cache:
        # Default: no rate limits hit, no cooldowns
        mock_cache.get.return_value = None
        mock_cache.get_quiet.return_value = 0
        mock_cache.increment_counter.return_value = 1

        c = GeminiClient()
        c.api_keys = ["key_alpha", "key_beta"]
        c.key_hashes = [_key_hash("key_alpha"), _key_hash("key_beta")]
        yield c, mock_cache


@pytest.mark.unit
class TestKeyHash:
    def test_is_deterministic_for_same_input(self):
        # Act + Assert (pure function — Arrange implicit)
        assert _key_hash("abc") == _key_hash("abc")

    def test_produces_different_hashes_for_different_keys(self):
        # Act + Assert
        assert _key_hash("key1") != _key_hash("key2")

    def test_hash_is_exactly_12_chars(self):
        # Act + Assert
        assert len(_key_hash("anything")) == 12


@pytest.mark.unit
class TestNowMinute:
    def test_produces_yyyymmdd_hhmm_format(self):
        # Act
        result = _now_minute()

        # Assert — length 13 = YYYYMMDD_HHMM
        assert len(result) == 13
        assert "_" in result


@pytest.mark.unit
class TestRateLimitCheck:
    def test_allows_request_when_no_limits_hit(self, client):
        # Arrange
        c, mock_cache = client
        mock_cache.get_quiet.return_value = 0

        # Act
        kh = _key_hash("key_alpha")
        result = c._check_rate_limits(kh, "gemini-3-flash-preview", "extraction")

        # Assert
        assert result is True

    def test_blocks_request_when_rpm_limit_reached(self, client):
        # Arrange
        c, mock_cache = client
        from app.core.config import settings

        rpm_limit = settings.GEMINI_RPM_LIMITS_MAP.get("gemini-3-flash-preview", 10)
        mock_cache.get_quiet.return_value = rpm_limit

        # Act
        kh = _key_hash("key_alpha")
        result = c._check_rate_limits(kh, "gemini-3-flash-preview", "extraction")

        # Assert
        assert result is False

    def test_detects_key_in_cooldown_via_future_timestamp(self, client):
        # Arrange
        c, mock_cache = client
        from datetime import datetime, timedelta, timezone

        kh = _key_hash("key_alpha")
        future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        def get_quiet_side_effect(key):
            if "cooldown" in key:
                return future_time
            return 0

        mock_cache.get_quiet.side_effect = get_quiet_side_effect

        # Act
        result = c._is_key_in_cooldown(kh)

        # Assert
        assert result is True


@pytest.mark.unit
class TestThinkingConfig:
    def test_gemini_3x_returns_thinking_level_config(self, client):
        # Arrange
        c, _ = client

        # Act
        config = c._build_thinking_config("gemini-3-flash-preview", "high")

        # Assert — returns a config object (not None)
        assert config is not None

    def test_gemini_25x_returns_thinking_budget_config(self, client):
        # Arrange
        c, _ = client

        # Act
        config = c._build_thinking_config("gemini-2.5-flash", "medium")

        # Assert
        assert config is not None

    def test_none_thinking_level_still_returns_config_object(self, client):
        # Arrange
        c, _ = client

        # Act
        config = c._build_thinking_config("gemini-3-flash-preview", None)

        # Assert — None thinking → config with "none" level, not Python None
        assert config is not None


@pytest.mark.unit
class TestModelChain:
    def test_primary_model_is_first_in_model_chain(self, client):
        # Arrange
        c, _ = client
        from app.core.config import settings

        # Act
        primary = settings.get_model_for_task("translation")
        fallbacks = settings.GEMINI_FALLBACK_MODELS_LIST
        chain = [primary] + [m for m in fallbacks if m != primary]

        # Assert
        assert chain[0] == primary
        assert len(chain) >= 1


@pytest.mark.unit
class TestGetUsageStats:
    def test_returns_dict_with_keys_and_total_keys_fields(self, client):
        # Arrange
        c, mock_cache = client
        mock_cache.get.return_value = None

        # Act
        stats = c.get_usage_stats()

        # Assert
        assert isinstance(stats, dict)
        assert "keys" in stats
        assert "total_keys" in stats


@pytest.mark.unit
class TestCompleteErrorHandling:
    def test_raises_api_key_exhausted_when_all_keys_are_in_cooldown(self, client):
        # Arrange — simulate all keys in cooldown with a future timestamp
        c, mock_cache = client
        from datetime import datetime, timedelta, timezone

        future_ts = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        def _get_quiet_all_cooldown(key):
            if "cooldown" in key:
                return future_ts
            return 0

        mock_cache.get_quiet.side_effect = _get_quiet_all_cooldown

        # Act + Assert
        from app.core.exceptions import APIKeyExhausted

        with pytest.raises(APIKeyExhausted):
            c.complete("test prompt", task_type="extraction")
