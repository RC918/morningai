"""
Redis Integration Tests (Non-Mock)

These tests verify actual Redis connectivity and operations.
They are skipped in CI environments without Redis access.

To run locally:
    export REDIS_URL="redis://localhost:6379"
    pytest tests/test_redis_integration.py -v

To run in CI with Redis:
    Ensure REDIS_URL secret is configured in GitHub Actions
"""
import os
import pytest
import time


# Skip all tests if REDIS_URL is not configured
pytestmark = pytest.mark.skipif(
    not os.environ.get('REDIS_URL') and not os.environ.get('UPSTASH_REDIS_REST_URL'),
    reason="Redis not configured (REDIS_URL or UPSTASH_REDIS_REST_URL not set)"
)


class TestRedisRealConnection:
    """Test actual Redis connection and basic operations"""

    def test_redis_ping(self):
        """Test Redis connection with ping"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=False)
        assert client is not None

        # For standard Redis client
        if hasattr(client, 'ping'):
            result = client.ping()
            assert result is True or result == 'PONG'

    def test_redis_set_get(self):
        """Test Redis SET and GET operations"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=True)
        test_key = f"test:integration:{int(time.time())}"
        test_value = "integration_test_value"

        try:
            client.set(test_key, test_value)
            result = client.get(test_key)

            if isinstance(result, bytes):
                result = result.decode("utf-8")

            assert result == test_value
        finally:
            if hasattr(client, 'delete'):
                client.delete(test_key)

    def test_redis_expire(self):
        """Test Redis key expiration"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=True)
        test_key = f"test:expire:{int(time.time())}"
        test_value = "expire_test"

        try:
            if hasattr(client, 'setex'):
                # Standard Redis with SETEX
                client.setex(test_key, 60, test_value)
                ttl = client.ttl(test_key)
                assert ttl > 0 and ttl <= 60
            else:
                # Upstash or other client
                client.set(test_key, test_value, ex=60)
                ttl = client.ttl(test_key)
                assert ttl > 0 and ttl <= 60
        finally:
            if hasattr(client, 'delete'):
                client.delete(test_key)

    def test_redis_hash_operations(self):
        """Test Redis hash operations"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=True)
        test_key = f"test:hash:{int(time.time())}"

        try:
            if hasattr(client, 'hset'):
                # HSET
                client.hset(test_key, "field1", "value1")
                client.hset(test_key, "field2", "value2")

                # HGET
                result = client.hget(test_key, "field1")
                assert result == "value1"

                # HGETALL
                all_fields = client.hgetall(test_key)
                assert "field1" in all_fields or b"field1" in all_fields
        finally:
            if hasattr(client, 'delete'):
                client.delete(test_key)

    def test_redis_list_operations(self):
        """Test Redis list operations"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=True)
        test_key = f"test:list:{int(time.time())}"

        try:
            if hasattr(client, 'rpush'):
                # RPUSH
                client.rpush(test_key, "item1", "item2", "item3")

                # LRANGE
                items = client.lrange(test_key, 0, -1)
                assert len(items) == 3

                # LPOP
                first = client.lpop(test_key)
                assert first == "item1" or first == b"item1"
        finally:
            if hasattr(client, 'delete'):
                client.delete(test_key)


class TestRedisConnectionResilience:
    """Test Redis connection error handling and resilience"""

    def test_connection_info_matches_actual(self):
        """Test that connection info reflects actual connection type"""
        from src.utils.redis_client import get_redis_connection_info

        info = get_redis_connection_info()

        # Should have valid connection info
        assert info['type'] in ['upstash', 'redis', 'none']
        assert 'tls_enabled' in info
        assert 'protocol' in info

    def test_security_check_returns_valid_status(self):
        """Test that security check returns valid status for real connection"""
        from src.utils.redis_client import check_redis_security

        result = check_redis_security()

        # Should return valid status
        assert result['status'] in ['secure', 'vulnerable', 'unknown', 'error']
        assert 'cve_2025_49844_risk' in result
        assert 'recommendations' in result

    def test_client_singleton_consistency(self):
        """Test that get_redis_client returns consistent singleton"""
        from src.utils.redis_client import get_redis_client

        # Reset singleton for test
        import src.utils.redis_client as redis_module
        redis_module.redis_client = None

        client1 = get_redis_client()
        client2 = get_redis_client()

        # Should be the same instance
        assert client1 is client2


class TestRedisPerformance:
    """Test Redis performance characteristics"""

    def test_connection_latency(self):
        """Test Redis connection latency is acceptable"""
        from src.utils.redis_client import create_redis_client

        start = time.time()
        create_redis_client(skip_ping=False)
        latency = time.time() - start

        # Connection should complete within 5 seconds
        assert latency < 5.0, f"Connection took {latency:.2f}s, expected < 5s"

    def test_operation_latency(self):
        """Test Redis operation latency is acceptable"""
        from src.utils.redis_client import create_redis_client

        client = create_redis_client(skip_ping=True)
        test_key = f"test:latency:{int(time.time())}"

        try:
            # Measure SET latency (call directly, fail if method missing)
            start = time.time()
            client.set(test_key, "latency_test")
            set_latency = time.time() - start

            # Measure GET latency (call directly, fail if method missing)
            start = time.time()
            client.get(test_key)
            get_latency = time.time() - start

            # Operations should complete within 2 seconds each
            # (allowing for network latency with cloud Redis)
            assert set_latency < 2.0, f"SET took {set_latency:.2f}s"
            assert get_latency < 2.0, f"GET took {get_latency:.2f}s"
        finally:
            if hasattr(client, 'delete'):
                client.delete(test_key)
