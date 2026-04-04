"""
Unit tests — GeminiClient.complete() 429 failover integration.

Level: Unit (all external calls mocked — no real Gemini API, no Redis).

This suite tests the CRITICAL PATH behavior of complete(): what happens when
Key 1 receives a 429 from the Google API during the actual network call,
not just in the pre-flight rate limit check.

The distinction from test_gemini_failover.py (which mocks Redis pre-flight):
  - test_gemini_failover.py → tests cooldown/RPM state managed in Redis.
  - test_gemini_failover_complete.py → tests the exception path inside
    `_try_model_across_keys` when `genai.Client().models.generate_content`
    itself raises a 429-like error.

Critical risk: if the try/except inside _try_model_across_keys does NOT catch
a 429 correctly, Key 1 is never put in cooldown and the system retries Key 1
indefinitely until the API quota is fully exhausted for the day.

Covers:
  - Key 1 raises 429 → Key 2 succeeds → result returned (happy failover).
  - Key 1 raises 429 → Key 2 also raises 429 → APIKeyExhausted raised.
  - Key 1 raises non-429 error → skips to next MODEL (not next key).
  - After 429, _put_key_in_cooldown is called exactly once for Key 1.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import APIKeyExhausted
from app.services.gemini_client import GeminiClient, _key_hash


class _FakeResponse:
    """Minimal stand-in for a successful genai response."""

    def __init__(self, text: str = "Translated text."):
        self.parsed = None
        self.candidates = [
            MagicMock(
                finish_reason="STOP",
                content=MagicMock(parts=[MagicMock(text=text)]),
            )
        ]


@pytest.fixture()
def two_key_client():
    """
    Returns a GeminiClient with:
      - Two deterministic API keys.
      - A fully mocked cache_service (no Redis).
    """
    with patch("app.services.gemini_client.cache_service") as mock_cache:
        mock_cache.get_quiet.return_value = 0  # no RPM/RPD usage, no cooldowns
        mock_cache.get.return_value = None
        mock_cache.increment_counter.return_value = 1
        mock_cache.set.return_value = True

        c = GeminiClient()
        c.api_keys = ["primary_key", "fallback_key"]
        c.key_hashes = [_key_hash("primary_key"), _key_hash("fallback_key")]
        yield c, mock_cache


@pytest.mark.unit
class TestCompleteFailoverOn429:
    def test_falls_back_to_key2_when_key1_receives_429(self, two_key_client):
        """
        Core failover scenario: Key 1 → 429 → Key 2 → success.
        The result from Key 2 must be returned transparently.
        """
        # Arrange
        c, mock_cache = two_key_client

        key1_response = Exception("429 Too Many Requests from Google")
        key2_response = _FakeResponse("Успешный перевод.")

        call_count = {"n": 0}

        def _generate_content_side_effect(**kwargs):
            if call_count["n"] == 0:
                call_count["n"] += 1
                raise key1_response
            return key2_response

        with patch("app.services.gemini_client.genai") as mock_genai:
            mock_client_instance = MagicMock()
            mock_genai.Client.return_value = mock_client_instance
            mock_client_instance.models.generate_content.side_effect = (
                _generate_content_side_effect
            )

            # Act
            result = c.complete("Translate this.", task_type="translation")

        # Assert — result comes from Key 2's response
        assert result == "Успешный перевод."
        # genai.Client was created twice (once per key attempt)
        assert mock_genai.Client.call_count == 2

    def test_key1_put_in_cooldown_after_429(self, two_key_client):
        """
        After Key 1 receives a 429, _put_key_in_cooldown must be called
        with Key 1's hash (not Key 2's hash).
        """
        # Arrange
        c, mock_cache = two_key_client
        key1_hash = c.key_hashes[0]

        def _generate_content_side_effect(**kwargs):
            # Always fail for the first key, succeed for second
            raise Exception("RESOURCE_EXHAUSTED: quota exceeded")

        with patch("app.services.gemini_client.genai") as mock_genai:
            mock_client_instance = MagicMock()
            mock_genai.Client.return_value = mock_client_instance
            mock_client_instance.models.generate_content.side_effect = [
                Exception("429 Too Many Requests"),
                _FakeResponse(),
            ]

            # Act
            c.complete("prompt", task_type="extraction")

        # Assert — cooldown written for key 1 only
        cooldown_calls = [
            call
            for call in mock_cache.set.call_args_list
            if "cooldown" in str(call)
        ]
        assert len(cooldown_calls) == 1
        assert key1_hash in str(cooldown_calls[0])

    def test_raises_api_key_exhausted_when_all_keys_get_429(self, two_key_client):
        """
        Worst case: both keys receive 429. Since there are also fallback models,
        all models × all keys must fail before APIKeyExhausted is raised.
        This test limits the fallback_models list to [] to isolate the key loop.
        """
        # Arrange
        c, _ = two_key_client
        c.fallback_models = []  # disable model fallback for isolation

        with patch("app.services.gemini_client.genai") as mock_genai:
            mock_client_instance = MagicMock()
            mock_genai.Client.return_value = mock_client_instance
            mock_client_instance.models.generate_content.side_effect = Exception(
                "429 Too Many Requests"
            )

            # Act & Assert
            with pytest.raises(APIKeyExhausted):
                c.complete("translate", task_type="translation")

    def test_non_429_error_skips_to_next_model_not_next_key(self, two_key_client):
        """
        A 500-type error on Key 1 must NOT try Key 2 for the same model.
        Instead, _try_model_across_keys returns _SENTINEL immediately and
        the outer loop tries the next model in the fallback chain.
        """
        # Arrange
        c, _ = two_key_client
        c.fallback_models = ["gemini-2.5-flash"]  # one fallback model
        key2_response = _FakeResponse("Ответ второй модели.")

        call_count = {"n": 0}

        def _generate_content_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # First call → primary model, Key 1 → non-429 error
                raise Exception("500 Internal Server Error")
            return key2_response  # fallback model succeeds

        with patch("app.services.gemini_client.genai") as mock_genai:
            mock_client_instance = MagicMock()
            mock_genai.Client.return_value = mock_client_instance
            mock_client_instance.models.generate_content.side_effect = (
                _generate_content_side_effect
            )

            # Act
            result = c.complete("prompt", task_type="translation")

        # Assert — result came from the fallback model's response
        assert result == "Ответ второй модели."
        # Only 2 API calls total: primary-model/key1 (fail), fallback-model/key1 (ok)
        # Key 2 should NOT have been tried for the primary model after a 500
        assert mock_client_instance.models.generate_content.call_count == 2
