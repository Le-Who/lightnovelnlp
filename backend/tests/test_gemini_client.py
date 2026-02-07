import pytest
from unittest.mock import MagicMock, patch
from app.services.gemini_client import GeminiClient, genai

@pytest.fixture
def mock_genai_client():
    """Mock the genai.Client to prevent actual network calls."""
    with patch("app.services.gemini_client.genai.Client") as mock:
        yield mock

@pytest.fixture
def gemini_client_instance(mock_genai_client):
    """
    Creates a GeminiClient instance with a controlled list of API keys.
    We assume the environment is already set up by conftest or defaults
    such that __init__ doesn't crash.
    """
    # Initialize client
    client = GeminiClient()

    # Override api_keys with our test set
    client.api_keys = ["key1", "key2", "key3"]
    client.current_key_index = 0

    # Reset mock to clear the call made during __init__
    mock_genai_client.reset_mock()

    return client

def test_rotate_key_success(gemini_client_instance, mock_genai_client):
    """Test successful rotation when next key is available."""
    client = gemini_client_instance
    client.current_key_index = 0
    model_name = "gemini-flash-latest"

    # Mock internal checks:
    # key1 (index 0): in cooldown (simulating exhaustion/limit) -> False
    # key2 (index 1): available -> True

    # logic of _find_available_key:
    # it iterates keys.
    # We want it to skip index 0 and pick index 1.

    with patch.object(client, '_is_key_in_cooldown') as mock_cooldown, \
         patch.object(client, '_is_model_at_limit') as mock_limit:

        # Setup side effects
        # _is_key_in_cooldown called with key
        mock_cooldown.side_effect = lambda k: k == "key1" # key1 is in cooldown

        # _is_model_at_limit - let's say no models are at limit for simplicity
        mock_limit.return_value = False

        # Action
        client._rotate_key(model_name)

        # Verify
        assert client.current_key_index == 1

        # Verify genai.Client was re-initialized with key2
        mock_genai_client.assert_called_with(api_key="key2")


def test_rotate_key_all_unavailable(gemini_client_instance):
    """Test rotation fails when no keys are available."""
    client = gemini_client_instance
    model_name = "gemini-flash-latest"

    with patch.object(client, '_is_key_in_cooldown', return_value=True):
         with pytest.raises(Exception) as excinfo:
            client._rotate_key(model_name)

         assert f"No available API keys for model {model_name}" in str(excinfo.value)
         # Index should remain unchanged (or as it was)
         assert client.current_key_index == 0


def test_rotate_key_skips_multiple_bad_keys(gemini_client_instance, mock_genai_client):
    """Test rotation skips multiple bad keys to find a good one."""
    client = gemini_client_instance
    client.current_key_index = 0
    model_name = "gemini-flash-latest"

    # keys: key1(bad), key2(bad), key3(good)

    with patch.object(client, '_is_key_in_cooldown') as mock_cooldown, \
         patch.object(client, '_is_model_at_limit') as mock_limit:

        # key1, key2 in cooldown. key3 not.
        mock_cooldown.side_effect = lambda k: k in ["key1", "key2"]
        mock_limit.return_value = False

        client._rotate_key(model_name)

        assert client.current_key_index == 2
        mock_genai_client.assert_called_with(api_key="key3")


def test_rotate_key_checks_limits(gemini_client_instance, mock_genai_client):
    """Test that rotation respects model limits."""
    client = gemini_client_instance
    client.current_key_index = 0
    model_name = "gemini-flash-latest"

    # key1: not in cooldown, but at limit for this model
    # key2: ok

    with patch.object(client, '_is_key_in_cooldown', return_value=False), \
         patch.object(client, '_is_model_at_limit') as mock_limit:

        # key1 is at limit, others are not
        mock_limit.side_effect = lambda k, m: k == "key1"

        client._rotate_key(model_name)

        assert client.current_key_index == 1
        mock_genai_client.assert_called_with(api_key="key2")
