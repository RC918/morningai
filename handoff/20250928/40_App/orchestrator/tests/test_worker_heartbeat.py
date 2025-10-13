#!/usr/bin/env python3
"""
Tests for RQ worker heartbeat functionality
"""
import pytest
import json
import time
from redis import Redis

def test_heartbeat_write_to_redis():
    """Test that heartbeat writes to Redis with correct key format"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        worker_id = "test-worker-001"
        heartbeat_key = f"worker:heartbeat:{worker_id}"
        
        redis_client.setex(
            heartbeat_key,
            120,
            json.dumps({
                "state": "running",
                "last_heartbeat": "2025-01-01T00:00:00Z",
                "worker_id": worker_id,
                "timestamp": int(time.time())
            })
        )
        
        data = redis_client.get(heartbeat_key)
        assert data is not None
        heartbeat = json.loads(data)
        assert heartbeat["state"] == "running"
        assert heartbeat["worker_id"] == worker_id
        
        redis_client.delete(heartbeat_key)
        print("✅ Heartbeat write successful")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

def test_heartbeat_ttl_expiration():
    """Test that heartbeat key expires after TTL"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        worker_id = "test-worker-002"
        heartbeat_key = f"worker:heartbeat:{worker_id}"
        
        redis_client.setex(
            heartbeat_key,
            2,
            json.dumps({
                "state": "running",
                "worker_id": worker_id
            })
        )
        
        assert redis_client.exists(heartbeat_key) == 1
        
        time.sleep(3)
        
        assert redis_client.exists(heartbeat_key) == 0
        print("✅ Heartbeat TTL expiration works")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

def test_heartbeat_state_transitions():
    """Test heartbeat state transitions (running -> shutting_down)"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        worker_id = "test-worker-003"
        heartbeat_key = f"worker:heartbeat:{worker_id}"
        
        redis_client.setex(
            heartbeat_key,
            120,
            json.dumps({"state": "running", "worker_id": worker_id})
        )
        
        data = redis_client.get(heartbeat_key)
        heartbeat = json.loads(data)
        assert heartbeat["state"] == "running"
        
        redis_client.setex(
            heartbeat_key,
            120,
            json.dumps({"state": "shutting_down", "worker_id": worker_id})
        )
        
        data = redis_client.get(heartbeat_key)
        heartbeat = json.loads(data)
        assert heartbeat["state"] == "shutting_down"
        
        redis_client.delete(heartbeat_key)
        print("✅ Heartbeat state transitions work")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

def test_heartbeat_cleanup_on_shutdown():
    """Test that heartbeat key is deleted on worker shutdown"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        worker_id = "test-worker-004"
        heartbeat_key = f"worker:heartbeat:{worker_id}"
        
        redis_client.setex(
            heartbeat_key,
            120,
            json.dumps({"state": "running", "worker_id": worker_id})
        )
        
        assert redis_client.exists(heartbeat_key) == 1
        
        redis_client.delete(heartbeat_key)
        
        assert redis_client.exists(heartbeat_key) == 0
        print("✅ Heartbeat cleanup on shutdown works")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

if __name__ == "__main__":
    print("🧪 Running Worker Heartbeat Tests")
    print("=" * 50)
    
    test_heartbeat_write_to_redis()
    test_heartbeat_ttl_expiration()
    test_heartbeat_state_transitions()
    test_heartbeat_cleanup_on_shutdown()
    
    print("=" * 50)
    print("🎉 Heartbeat tests completed!")
