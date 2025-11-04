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
    
    keys_to_delete = list(client.scan_iter("test:agent:task:*"))
    if keys_to_delete:
        client.delete(*keys_to_delete)

def test_scan_performance_vs_keys(redis_client):
    """Test that SCAN performs better than KEYS with many keys"""
    num_keys = 50
    
    pipe = redis_client.pipeline()
    for i in range(num_keys):
        pipe.setex(f"test:agent:task:{i}", 3600, f"value_{i}")
    pipe.execute()
    
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
        keys_to_delete = list(redis_client.scan_iter("test:agent:task:*"))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)

def test_scan_iter_memory_efficiency(redis_client):
    """Test that scan_iter uses less memory than keys"""
    num_keys = 50
    
    pipe = redis_client.pipeline()
    for i in range(num_keys):
        pipe.setex(f"test:agent:task:{i}", 3600, f"value_{i}")
    pipe.execute()
    
    try:
        scan_iter = redis_client.scan_iter("test:agent:task:*", count=100)
        
        first_ten = []
        for i, key in enumerate(scan_iter):
            if i >= 10:
                break
            first_ten.append(key)
        
        assert len(first_ten) == 10
        
    finally:
        keys_to_delete = list(redis_client.scan_iter("test:agent:task:*"))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)

def test_scan_returns_all_keys(redis_client):
    """Test that scan_iter returns all matching keys"""
    test_keys = [f"test:agent:task:{i}" for i in range(50)]
    
    pipe = redis_client.pipeline()
    for key in test_keys:
        pipe.setex(key, 3600, "test_value")
    pipe.execute()
    
    try:
        scan_result = list(redis_client.scan_iter("test:agent:task:*", count=100))
        
        assert len(scan_result) == len(test_keys)
        assert set(scan_result) == set(test_keys)
        
    finally:
        keys_to_delete = list(redis_client.scan_iter("test:agent:task:*"))
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
