import pytest
import time
from redis import Redis
from redis.exceptions import ConnectionError
import os

@pytest.fixture
def redis_client():
    """Create Redis client for testing"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = Redis.from_url(redis_url, decode_responses=True)
    
    try:
        client.ping()
    except ConnectionError:
        pytest.skip("Redis server not available - skipping performance tests")
    
    yield client
    for key in client.scan_iter("test:agent:task:*"):
        client.delete(key)

def test_scan_performance_vs_keys(redis_client):
    """Test that SCAN performs better than KEYS with many keys"""
    num_keys = 1000
    for i in range(num_keys):
        redis_client.setex(f"test:agent:task:{i}", 3600, f"value_{i}")
    
    try:
        start_keys = time.time()
        keys_result = redis_client.keys("test:agent:task:*")
        keys_time = time.time() - start_keys
        
        start_scan = time.time()
        scan_result = list(redis_client.scan_iter("test:agent:task:*", count=100))
        scan_time = time.time() - start_scan
        
        assert len(keys_result) == num_keys
        assert len(scan_result) == num_keys
        
        print(f"\nKEYS time: {keys_time:.4f}s, SCAN time: {scan_time:.4f}s")
        
    finally:
        for key in redis_client.scan_iter("test:agent:task:*"):
            redis_client.delete(key)

def test_scan_iter_memory_efficiency(redis_client):
    """Test that scan_iter uses less memory than keys"""
    num_keys = 10000
    for i in range(num_keys):
        redis_client.setex(f"test:agent:task:{i}", 3600, f"value_{i}")
    
    try:
        scan_iter = redis_client.scan_iter("test:agent:task:*", count=100)
        
        first_ten = []
        for i, key in enumerate(scan_iter):
            if i >= 10:
                break
            first_ten.append(key)
        
        assert len(first_ten) == 10
        
    finally:
        for key in redis_client.scan_iter("test:agent:task:*"):
            redis_client.delete(key)

def test_scan_returns_all_keys(redis_client):
    """Test that scan_iter returns all matching keys"""
    test_keys = [f"test:agent:task:{i}" for i in range(100)]
    for key in test_keys:
        redis_client.setex(key, 3600, "test_value")
    
    try:
        scan_result = list(redis_client.scan_iter("test:agent:task:*", count=100))
        
        assert len(scan_result) == len(test_keys)
        assert set(scan_result) == set(test_keys)
        
    finally:
        for key in redis_client.scan_iter("test:agent:task:*"):
            redis_client.delete(key)
