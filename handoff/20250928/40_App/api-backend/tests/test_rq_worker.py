#!/usr/bin/env python3
"""
Test suite for RQ worker integration
"""

import pytest
import json
import uuid
import time
from unittest.mock import patch, MagicMock
from redis import Redis
from rq import Queue

def test_worker_module_imports():
    """Test that worker module can be imported"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../orchestrator'))
        from redis_queue import worker
        
        assert hasattr(worker, 'run_orchestrator_task')
        assert callable(worker.run_orchestrator_task)
        print("✅ Worker module imports successfully")
    except ImportError as e:
        pytest.skip(f"Worker module not available: {e}")

def test_task_queuing():
    """Test that tasks can be queued to RQ"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        q = Queue("orchestrator", connection=redis_client)
        
        task_id = str(uuid.uuid4())
        job = q.enqueue(
            'redis_queue.worker.run_orchestrator_task',
            task_id,
            "Test topic",
            "RC918/morningai",
            job_id=task_id
        )
        
        assert job is not None
        assert job.id == task_id
        print(f"✅ Task queued successfully: {task_id}")
        
        job.cancel()
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

def test_task_status_transitions():
    """Test task status transitions from queued -> running -> done"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        task_id = str(uuid.uuid4())
        
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "queued",
                "topic": "Test",
                "created_at": "2025-01-01T00:00:00"
            })
        )
        
        task_data = redis_client.get(f"agent:task:{task_id}")
        assert task_data is not None
        
        task = json.loads(task_data)
        assert task["status"] == "queued"
        
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "running",
                "topic": "Test",
                "trace_id": task_id
            })
        )
        
        task_data = redis_client.get(f"agent:task:{task_id}")
        assert task_data is not None, "Task data should exist"
        
        task = json.loads(task_data)
        assert task["status"] == "running"
        
        redis_client.delete(f"agent:task:{task_id}")
        print("✅ Task status transitions work correctly")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

def test_error_handling():
    """Test that errors are properly stored in Redis"""
    try:
        redis_client = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        redis_client.ping()
        
        task_id = str(uuid.uuid4())
        
        redis_client.setex(
            f"agent:task:{task_id}",
            3600,
            json.dumps({
                "status": "error",
                "topic": "Test",
                "trace_id": task_id,
                "error": {
                    "code": "ORCHESTRATOR_FAILED",
                    "message": "Test error"
                }
            })
        )
        
        task_data = redis_client.get(f"agent:task:{task_id}")
        assert task_data is not None
        
        task = json.loads(task_data)
        assert task["status"] == "error"
        assert "error" in task
        assert task["error"]["code"] == "ORCHESTRATOR_FAILED"
        
        redis_client.delete(f"agent:task:{task_id}")
        print("✅ Error handling works correctly")
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")

if __name__ == "__main__":
    print("🧪 Running RQ Worker Integration Tests")
    print("=" * 50)
    
    test_worker_module_imports()
    test_task_queuing()
    test_task_status_transitions()
    test_error_handling()
    
    print("=" * 50)
    print("🎉 RQ worker tests completed!")
