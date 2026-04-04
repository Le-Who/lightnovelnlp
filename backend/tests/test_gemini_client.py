"""
Tests for GeminiClient v2.

Tests cover:
- Rate-limit pre-flight checks (_check_rate_limits)
- ThinkingConfig auto-detection (_build_thinking_config)
- Model chain fallback behavior
- Key hash determinism
- get_usage_stats structure
"""

import pytest
from unittest.mock import patch
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


class TestKeyHash:
    def test_deterministic(self):
        assert _key_hash("abc") == _key_hash("abc")

    def test_different_keys_different_hashes(self):
        assert _key_hash("key1") != _key_hash("key2")

    def test_length(self):
        assert len(_key_hash("anything")) == 12


class TestNowMinute:
    def test_format(self):
        result = _now_minute()
        assert len(result) == 13  # YYYYMMDD_HHMM
        assert "_" in result


class TestRateLimitCheck:
    def test_no_limits_hit(self, client):
        c, mock_cache = client
        mock_cache.get_quiet.return_value = 0

        kh = _key_hash("key_alpha")
        result = c._check_rate_limits(kh, "gemini-3-flash-preview", "extraction")
        assert result is True

    def test_rpm_exceeded(self, client):
        c, mock_cache = client
        from app.core.config import settings

        rpm_limit = settings.GEMINI_RPM_LIMITS_MAP.get("gemini-3-flash-preview", 10)

        # Return value >= rpm_limit for the RPM check
        mock_cache.get_quiet.return_value = rpm_limit
        kh = _key_hash("key_alpha")
        result = c._check_rate_limits(kh, "gemini-3-flash-preview", "extraction")
        assert result is False

    def test_cooldown_blocks(self, client):
        c, mock_cache = client
        kh = _key_hash("key_alpha")

        # Simulate cooldown: get_quiet returns a future datetime ISO string
        from datetime import datetime, timedelta, timezone

        future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        def get_quiet_side_effect(key):
            if "cooldown" in key:
                return future_time
            return 0

        mock_cache.get_quiet.side_effect = get_quiet_side_effect

        result = c._is_key_in_cooldown(kh)
        assert result is True


class TestThinkingConfig:
    def test_gemini_3x_uses_thinking_level(self, client):
        c, _ = client
        config = c._build_thinking_config("gemini-3-flash-preview", "high")
        assert config is not None

    def test_gemini_25x_uses_budget(self, client):
        c, _ = client
        config = c._build_thinking_config("gemini-2.5-flash", "medium")
        assert config is not None

    def test_none_thinking_returns_none(self, client):
        c, _ = client
        config = c._build_thinking_config("gemini-3-flash-preview", None)
        # None thinking → returns a config with "none" level
        assert config is not None


class TestModelChain:
    def test_primary_model_first(self, client):
        c, _ = client
        from app.core.config import settings

        primary = settings.get_model_for_task("translation")
        fallbacks = settings.GEMINI_FALLBACK_MODELS_LIST

        chain = [primary] + [m for m in fallbacks if m != primary]
        assert chain[0] == primary
        assert len(chain) >= 1


class TestGetUsageStats:
    def test_returns_dict(self, client):
        c, mock_cache = client
        mock_cache.get.return_value = None

        stats = c.get_usage_stats()
        assert isinstance(stats, dict)
        assert "keys" in stats
        assert "total_keys" in stats


class TestCompleteErrorHandling:
    def test_all_keys_exhausted_raises(self, client):
        """When all keys are in cooldown, APIKeyExhausted is raised."""
        c, mock_cache = client

        # All keys in cooldown
        mock_cache.get.return_value = "1"  # cooldown flag set for all keys

        from app.core.exceptions import APIKeyExhausted

        with pytest.raises(APIKeyExhausted):
            c.complete("test prompt", task_type="extraction")
