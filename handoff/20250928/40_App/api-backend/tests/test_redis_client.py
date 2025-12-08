"""Tests for Redis client skip_ping behavior with testing flag"""
import logging
import pytest
from unittest.mock import patch, MagicMock, Mock

from utils.redis_client import UpstashRedisAdapter


class FakeUpstashClient:
    """Fake Upstash client for testing UpstashRedisAdapter."""

    def __init__(self, responses_by_cursor, mget_responses=None):
        """
        Initialize fake client with predefined responses.

        Args:
            responses_by_cursor: Dict mapping cursor values to (new_cursor, keys) tuples
            mget_responses: Dict mapping keys to values for mget
        """
        self.responses_by_cursor = responses_by_cursor
        self.scan_calls = []
        self.mget_calls = []
        self._mget_responses = mget_responses or {}

    def scan(self, cursor=0, match=None, count=None):
        """Fake scan method that returns predefined responses."""
        self.scan_calls.append((cursor, match, count))
        return self.responses_by_cursor.get(cursor, (0, []))

    def mget(self, *keys):
        """Fake mget method that returns predefined responses."""
        self.mget_calls.append(keys)
        if not self._mget_responses:
            return [None for _ in keys]
        return [self._mget_responses.get(k) for k in keys]

    def ping(self):
        """Fake ping method."""
        return True


class TestUpstashRedisAdapter:
    """Tests for UpstashRedisAdapter compatibility layer."""

    def test_scan_iter_single_page(self):
        """Test scan_iter with a single page of results."""
        responses = {
            0: (0, ["key1", "key2", "key3"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter(match="prefix:*", count=100))

        assert keys == ["key1", "key2", "key3"]
        assert client.scan_calls == [(0, "prefix:*", 100)]

    def test_scan_iter_multi_page(self):
        """Test scan_iter with multiple pages of results."""
        responses = {
            0: (1, ["key1", "key2"]),
            1: (2, ["key3", "key4"]),
            2: (0, ["key5"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter(match="prefix:*", count=100))

        assert keys == ["key1", "key2", "key3", "key4", "key5"]
        assert client.scan_calls == [
            (0, "prefix:*", 100),
            (1, "prefix:*", 100),
            (2, "prefix:*", 100),
        ]

    def test_scan_iter_string_cursor_zero(self):
        """Test scan_iter terminates on string cursor '0'."""
        responses = {
            0: (1, ["key1"]),
            1: ("0", ["key2"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter())

        assert keys == ["key1", "key2"]
        assert len(client.scan_calls) == 2

    def test_scan_iter_bytes_cursor_zero(self):
        """Test scan_iter terminates on bytes cursor b'0'."""
        responses = {
            0: (1, ["key1"]),
            1: (b"0", ["key2"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter())

        assert keys == ["key1", "key2"]
        assert len(client.scan_calls) == 2

    def test_scan_iter_string_cursor_conversion(self):
        """Test scan_iter converts string cursor to int."""
        responses = {
            0: ("5", ["key1"]),
            5: (0, ["key2"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter())

        assert keys == ["key1", "key2"]
        assert client.scan_calls == [(0, None, None), (5, None, None)]

    def test_scan_iter_invalid_cursor_value_error(self, caplog):
        """Test scan_iter handles ValueError on invalid cursor gracefully."""
        responses = {
            0: ("not-an-int", ["key1"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        with caplog.at_level(logging.WARNING):
            keys = list(adapter.scan_iter())

        assert keys == ["key1"]
        assert any(
            "Unexpected cursor value" in record.message
            for record in caplog.records
        )

    def test_scan_iter_unexpected_format(self, caplog):
        """Test scan_iter handles unexpected result format gracefully."""
        responses = {
            0: "unexpected_string",
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        with caplog.at_level(logging.WARNING):
            keys = list(adapter.scan_iter())

        assert keys == []
        assert any(
            "Unexpected scan result format" in record.message
            for record in caplog.records
        )

    def test_scan_iter_empty_results(self):
        """Test scan_iter with no keys."""
        responses = {
            0: (0, []),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        keys = list(adapter.scan_iter())

        assert keys == []

    def test_mget_varargs(self):
        """Test mget with varargs style."""
        mget_responses = {"key1": "value1", "key2": "value2"}
        client = FakeUpstashClient({}, mget_responses)
        adapter = UpstashRedisAdapter(client)

        result = adapter.mget("key1", "key2")

        assert result == ["value1", "value2"]
        assert client.mget_calls == [("key1", "key2")]

    def test_mget_list_style(self):
        """Test mget with list style (redis-py compatibility)."""
        mget_responses = {"key1": "value1", "key2": "value2"}
        client = FakeUpstashClient({}, mget_responses)
        adapter = UpstashRedisAdapter(client)

        result = adapter.mget(["key1", "key2"])

        assert result == ["value1", "value2"]
        assert client.mget_calls == [("key1", "key2")]

    def test_mget_missing_keys(self):
        """Test mget returns None for missing keys."""
        mget_responses = {"key1": "value1"}
        client = FakeUpstashClient({}, mget_responses)
        adapter = UpstashRedisAdapter(client)

        result = adapter.mget("key1", "key2")

        assert result == ["value1", None]

    def test_getattr_delegation(self):
        """Test __getattr__ delegates to underlying client."""
        client = FakeUpstashClient({})
        adapter = UpstashRedisAdapter(client)

        result = adapter.ping()

        assert result is True

    def test_scan_iter_bytes_cursor_decode_error(self, caplog):
        """Test scan_iter handles bytes cursor decode error gracefully."""
        responses = {
            0: (b"\xff\xfe", ["key1"]),
        }
        client = FakeUpstashClient(responses)
        adapter = UpstashRedisAdapter(client)

        with caplog.at_level(logging.WARNING):
            keys = list(adapter.scan_iter())

        assert keys == ["key1"]
        assert any(
            "Unexpected bytes cursor value" in record.message
            for record in caplog.records
        )


class TestRedisClientSkipPing:
    """Test Redis client skip_ping behavior respects get_settings().testing"""

    def test_get_redis_client_respects_testing_flag_true(self):
        """Verify skip_ping uses get_settings().testing when testing=True"""
        mock_settings = MagicMock()
        mock_settings.testing = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None

                from utils.redis_client import get_redis_client
                client = get_redis_client()

                assert client is not None
                mock_from_url.assert_called_once()
                mock_client.ping.assert_not_called()

    def test_get_redis_client_respects_testing_flag_false(self):
        """Verify skip_ping uses get_settings().testing when testing=False"""
        mock_settings = MagicMock()
        mock_settings.testing = False
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None

                from utils.redis_client import get_redis_client
                client = get_redis_client()

                assert client is not None
                mock_from_url.assert_called_once()
                mock_client.ping.assert_called_once()

    def test_create_redis_client_with_skip_ping_true(self):
        """Verify create_redis_client respects skip_ping=True parameter"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=True)

                assert client is not None
                mock_client.ping.assert_not_called()

    def test_create_redis_client_with_skip_ping_false(self):
        """Verify create_redis_client respects skip_ping=False parameter"""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=False)

                assert client is not None
                mock_client.ping.assert_called_once()

    def test_create_redis_client_upstash_with_skip_ping_true(self):
        """Verify create_redis_client respects skip_ping=True for Upstash"""
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.upstash_redis_rest_token = "test_token"

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('upstash_redis.Redis') as mock_upstash_redis:
                mock_client = MagicMock()
                mock_upstash_redis.return_value = mock_client

                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=True)

                assert client is not None
                mock_client.ping.assert_not_called()

    def test_create_redis_client_upstash_with_skip_ping_false(self):
        """Verify create_redis_client respects skip_ping=False for Upstash"""
        mock_settings = MagicMock()
        mock_settings.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.upstash_redis_rest_token = "test_token"

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('upstash_redis.Redis') as mock_upstash_redis:
                mock_client = MagicMock()
                mock_upstash_redis.return_value = mock_client

                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=False)

                assert client is not None
                mock_client.ping.assert_called_once()

    def test_get_redis_client_singleton_behavior(self):
        """Verify get_redis_client returns the same instance on subsequent calls"""
        mock_settings = MagicMock()
        mock_settings.testing = True
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.upstash_redis_rest_url = None

        with patch('utils.redis_client.get_settings', return_value=mock_settings):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                import utils.redis_client as redis_client_module
                redis_client_module.redis_client = None

                from utils.redis_client import get_redis_client
                client1 = get_redis_client()
                client2 = get_redis_client()

                assert client1 is client2
                assert mock_from_url.call_count == 1
