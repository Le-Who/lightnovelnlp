import unittest
from unittest.mock import MagicMock, patch

from app.services.cache_service import CacheService


class TestCacheService(unittest.TestCase):
    def setUp(self):
        # Patch settings
        self.settings_patcher = patch("app.services.cache_service.settings")
        self.mock_settings = self.settings_patcher.start()

        # Patch UpstashRedis
        self.upstash_patcher = patch("app.services.cache_service.UpstashRedis")
        self.mock_upstash_cls = self.upstash_patcher.start()

        # Patch redis (TCP)
        self.redis_patcher = patch("app.services.cache_service.redis")
        self.mock_redis_module = self.redis_patcher.start()
        self.mock_tcp_client = MagicMock()
        self.mock_redis_module.from_url.return_value = self.mock_tcp_client

        # Setup default settings
        self.mock_settings.REDIS_URL = "redis://localhost:6379/0"
        self.mock_settings.UPSTASH_REDIS_REST_URL = None
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = None

    def tearDown(self):
        self.settings_patcher.stop()
        self.upstash_patcher.stop()
        self.redis_patcher.stop()

    def test_init_tcp_only(self):
        """Test initialization with only TCP Redis configured."""
        service = CacheService()

        self.assertIsNone(service.rest_client)
        self.assertEqual(service.redis_client, self.mock_tcp_client)

    def test_get_rest_fail_tcp_retry_success(self):
        """Test get fallback to TCP with retry when REST fails and TCP initially fails."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()

        # REST fails
        mock_rest_client.get.side_effect = Exception("REST error")

        # TCP fails once then succeeds
        self.mock_tcp_client.get.side_effect = [Exception("TCP error"), b"123"]
        # TCP ping succeeds (simplifying to avoid side_effect exhaustion issues)
        self.mock_tcp_client.ping.return_value = True

        result = service.get("key")

        self.assertEqual(result, 123)
        mock_rest_client.get.assert_called_with("key")
        # Should be called twice: initial + retry
        self.assertEqual(self.mock_tcp_client.get.call_count, 2)
        # Should have attempted reconnection
        self.assertTrue(self.mock_tcp_client.ping.call_count >= 1)

    def test_get_all_fail(self):
        """Test get returns None when all clients fail."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()

        # REST fails
        mock_rest_client.get.side_effect = Exception("REST error")

        # TCP fails always
        self.mock_tcp_client.get.side_effect = Exception("TCP error")
        self.mock_tcp_client.ping.return_value = True

        result = service.get("key")

        self.assertIsNone(result)
        mock_rest_client.get.assert_called_with("key")
        # Should be called twice: initial + retry
        self.assertEqual(self.mock_tcp_client.get.call_count, 2)

    def test_get_rest_success(self):
        """Test get using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.get.return_value = '{"foo": "bar"}'

        result = service.get("key")

        self.assertEqual(result, {"foo": "bar"})
        mock_rest_client.get.assert_called_with("key")
        self.mock_tcp_client.get.assert_not_called()

    def test_get_rest_fail_tcp_success(self):
        """Test get fallback to TCP when REST fails."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.get.side_effect = Exception("REST error")
        self.mock_tcp_client.get.return_value = b'{"foo": "bar"}'

        result = service.get("key")

        self.assertEqual(result, {"foo": "bar"})
        self.mock_tcp_client.get.assert_called_with("key")

    def test_get_tcp_retry(self):
        """Test get retry logic when TCP fails initially."""
        service = CacheService()  # Only TCP

        # First call fails, second call succeeds
        self.mock_tcp_client.get.side_effect = [Exception("Connection error"), b"123"]
        # Ping must fail to trigger reconnection
        self.mock_tcp_client.ping.side_effect = [Exception("Ping failed"), True]

        result = service.get("key")

        self.assertEqual(result, 123)
        self.assertEqual(self.mock_tcp_client.get.call_count, 2)
        # Should have reconnected
        self.assertTrue(self.mock_redis_module.from_url.call_count > 1)

    def test_get_deserialization(self):
        """Test get deserialization for different types."""
        service = CacheService()

        # Int
        self.mock_tcp_client.get.return_value = b"42"
        self.assertEqual(service.get("key"), 42)

        # JSON
        self.mock_tcp_client.get.return_value = b'{"a": 1}'
        self.assertEqual(service.get("key"), {"a": 1})

        # String (if not valid json or int)
        self.mock_tcp_client.get.return_value = b"some string"
        self.assertEqual(service.get("key"), "some string")

        # None
        self.mock_tcp_client.get.return_value = None
        self.assertIsNone(service.get("key"))

    def test_set_rest_success(self):
        """Test set using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.set.return_value = True

        result = service.set("key", {"a": 1}, ttl=60)

        self.assertTrue(result)
        mock_rest_client.set.assert_called_with("key", '{"a": 1}', ex=60)

    def test_set_tcp_fallback(self):
        """Test set fallback to TCP."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.set.side_effect = Exception("REST error")
        self.mock_tcp_client.setex.return_value = True

        result = service.set("key", 123)

        self.assertTrue(result)
        self.mock_tcp_client.setex.assert_called_with("key", 3600, "123")  # Default TTL

    def test_delete_rest_success(self):
        """Test delete using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.delete.return_value = 1

        result = service.delete("key")

        self.assertTrue(result)
        mock_rest_client.delete.assert_called_with("key")

    def test_delete_tcp_fallback(self):
        """Test delete fallback to TCP."""
        service = CacheService()
        self.mock_tcp_client.delete.return_value = 1

        result = service.delete("key")

        self.assertTrue(result)
        self.mock_tcp_client.delete.assert_called_with("key")
        self.mock_redis_module.from_url.assert_called_with(
            "redis://localhost:6379/0",
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )

    def test_increment_counter_rest_success(self):
        """Test increment_counter using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()

        # First increment
        mock_rest_client.incr.return_value = 1

        result = service.increment_counter("key", ttl=60)

        self.assertEqual(result, 1)
        mock_rest_client.incr.assert_called_with("key")
        mock_rest_client.expire.assert_called_with("key", 60)

        # Subsequent increment
        mock_rest_client.incr.return_value = 2
        mock_rest_client.expire.reset_mock()

        result = service.increment_counter("key", ttl=60)

        self.assertEqual(result, 2)
        mock_rest_client.expire.assert_not_called()

    def test_increment_counter_tcp_fallback(self):
        """Test increment_counter fallback to TCP."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.incr.side_effect = Exception("REST error")
        self.mock_tcp_client.incr.return_value = 1

        result = service.increment_counter("key", ttl=60)

        self.assertEqual(result, 1)
        self.mock_tcp_client.incr.assert_called_with("key")
        self.mock_tcp_client.expire.assert_called_with("key", 60)

    def test_delete_pattern_rest_success(self):
        """Test delete_pattern using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()
        mock_rest_client.keys.return_value = ["key1", "key2"]
        mock_rest_client.delete.return_value = 2

        result = service.delete_pattern("pattern*")

        self.assertEqual(result, 2)
        mock_rest_client.keys.assert_called_with("pattern*")
        mock_rest_client.delete.assert_called_with("key1", "key2")

    def test_delete_pattern_tcp_fallback(self):
        """Test delete_pattern fallback to TCP."""
        service = CacheService()
        self.mock_tcp_client.keys.return_value = ["key1", "key2"]
        self.mock_tcp_client.delete.return_value = 2

        result = service.delete_pattern("pattern*")

        self.assertEqual(result, 2)
        self.mock_tcp_client.keys.assert_called_with("pattern*")
        self.mock_tcp_client.delete.assert_called_with("key1", "key2")

    def test_translation_cache(self):
        """Test translation caching methods."""
        service = CacheService()
        self.mock_tcp_client.get.return_value = b"translation"
        self.mock_tcp_client.setex.return_value = True
        self.mock_tcp_client.keys.return_value = ["key"]
        self.mock_tcp_client.delete.return_value = 1

        # Test get
        self.assertEqual(service.get_cached_translation(1, "hash"), "translation")
        self.mock_tcp_client.get.assert_called_with("lightnovel:translation:1:hash")

        # Test cache
        service.cache_translation(1, "hash", "translation")
        self.mock_tcp_client.setex.assert_called_with(
            "lightnovel:translation:1:hash", 86400, '"translation"'
        )

        # Test invalidate
        service.invalidate_translation_cache(1)
        self.mock_tcp_client.keys.assert_called_with("lightnovel:translation:1:*")
        self.mock_tcp_client.delete.assert_called()

    def test_glossary_cache(self):
        """Test glossary caching methods."""
        service = CacheService()
        self.mock_tcp_client.get.return_value = b'[{"term": "a"}]'
        self.mock_tcp_client.setex.return_value = True
        self.mock_tcp_client.delete.return_value = 1

        # Test get
        self.assertEqual(service.get_cached_glossary(1), [{"term": "a"}])
        self.mock_tcp_client.get.assert_called_with("lightnovel:glossary:1")

        # Test cache
        service.cache_glossary(1, [{"term": "a"}])
        self.mock_tcp_client.setex.assert_called_with(
            "lightnovel:glossary:1", 3600, '[{"term": "a"}]'
        )

        # Test invalidate
        service.invalidate_glossary_cache(1)
        self.mock_tcp_client.delete.assert_called_with("lightnovel:glossary:1")

    def test_summary_cache(self):
        """Test summary caching methods."""
        service = CacheService()
        self.mock_tcp_client.get.return_value = b"summary"
        self.mock_tcp_client.setex.return_value = True
        self.mock_tcp_client.delete.return_value = 1

        # Test get
        self.assertEqual(service.get_cached_summary(1), "summary")
        self.mock_tcp_client.get.assert_called_with("lightnovel:summary:1")

        # Test cache
        service.cache_summary(1, "summary")
        self.mock_tcp_client.setex.assert_called_with(
            "lightnovel:summary:1", 7200, '"summary"'
        )

        # Test invalidate
        service.invalidate_summary_cache(1)
        self.mock_tcp_client.delete.assert_called_with("lightnovel:summary:1")

    def test_relationships_cache(self):
        """Test relationships caching methods."""
        service = CacheService()
        self.mock_tcp_client.get.return_value = b'[{"rel": "a"}]'
        self.mock_tcp_client.setex.return_value = True
        self.mock_tcp_client.delete.return_value = 1

        # Test get
        self.assertEqual(service.get_cached_relationships(1), [{"rel": "a"}])
        self.mock_tcp_client.get.assert_called_with("lightnovel:relationships:1")

        # Test cache
        service.cache_relationships(1, [{"rel": "a"}])
        self.mock_tcp_client.setex.assert_called_with(
            "lightnovel:relationships:1", 3600, '[{"rel": "a"}]'
        )

        # Test invalidate
        service.invalidate_relationships_cache(1)
        self.mock_tcp_client.delete.assert_called_with("lightnovel:relationships:1")

    def test_generate_glossary_hash(self):
        """Test glossary hash generation."""
        service = CacheService()

        terms1 = [
            {"source_term": "a", "target_term": "b"},
            {"source_term": "c", "target_term": "d"},
        ]
        terms2 = [
            {"source_term": "c", "target_term": "d"},
            {"source_term": "a", "target_term": "b"},
        ]

        # Order shouldn't matter
        hash1 = service.generate_glossary_hash(terms1)
        hash2 = service.generate_glossary_hash(terms2)

        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertTrue(len(hash1) > 0)

    def test_get_cache_stats_tcp(self):
        """Test cache stats using TCP client."""
        service = CacheService()
        self.mock_tcp_client.info.return_value = {
            "used_memory_human": "1M",
            "connected_clients": 10,
            "total_commands_processed": 100,
            "keyspace_hits": 50,
            "keyspace_misses": 50,
        }

        stats = service.get_cache_stats()

        self.assertFalse(stats["rest_client"])
        self.assertEqual(stats["used_memory"], "1M")
        self.assertEqual(stats["keyspace_hits"], 50)

    def test_get_cache_stats_rest(self):
        """Test cache stats using REST client."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"
        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()

        stats = service.get_cache_stats()

        self.assertTrue(stats["rest_client"])
        self.assertTrue(stats["connected"])

    def test_init_with_upstash(self):
        """Test initialization with Upstash REST configured."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"

        mock_rest_client = MagicMock()
        self.mock_upstash_cls.return_value = mock_rest_client

        service = CacheService()

        self.assertEqual(service.rest_client, mock_rest_client)
        self.mock_upstash_cls.assert_called_with(
            url="https://example.upstash.io", token="token"
        )
        mock_rest_client.ping.assert_called_once()

    def test_init_upstash_fail_fallback(self):
        """Test fallback to TCP when Upstash init fails."""
        self.mock_settings.UPSTASH_REDIS_REST_URL = "https://example.upstash.io"
        self.mock_settings.UPSTASH_REDIS_REST_TOKEN = "token"

        # Simulate Upstash init failure
        self.mock_upstash_cls.side_effect = Exception("Connection error")

        service = CacheService()

        self.assertIsNone(service.rest_client)
        self.assertEqual(service.redis_client, self.mock_tcp_client)

    def test_set_tcp_retry(self):
        """Test set retry logic when TCP fails initially."""
        service = CacheService()  # Only TCP

        # First call fails, second call succeeds
        self.mock_tcp_client.setex.side_effect = [Exception("Connection error"), True]

        # Ping must fail to trigger reconnection
        self.mock_tcp_client.ping.side_effect = [Exception("Ping failed"), True]

        result = service.set("key", 123)

        self.assertTrue(result)
        # setex called twice: once for initial attempt, once for retry
        self.assertEqual(self.mock_tcp_client.setex.call_count, 2)
        # Verify arguments (key, ttl, serialized value)
        self.mock_tcp_client.setex.assert_called_with("key", 3600, "123")
        # Should have reconnected
        self.assertTrue(self.mock_redis_module.from_url.call_count > 1)

    def test_set_full_failure(self):
        """Test set returns False when all attempts fail."""
        service = CacheService()  # Only TCP

        # All calls fail
        self.mock_tcp_client.setex.side_effect = Exception("Connection error")
        self.mock_tcp_client.ping.side_effect = Exception("Ping failed")

        result = service.set("key", 123)

        self.assertFalse(result)
        # setex called twice: initial + retry
        self.assertEqual(self.mock_tcp_client.setex.call_count, 2)
        # Verify arguments
        self.mock_tcp_client.setex.assert_called_with("key", 3600, "123")
