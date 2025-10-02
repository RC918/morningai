#!/usr/bin/env python3
"""
Test suite for worker health check and fallback mechanisms
"""

import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../orchestrator'))

def test_worker_health_check():
    """Test worker health check function"""
    try:
        from redis_queue.worker import check_worker_health
        
        health = check_worker_health()
        
        assert 'status' in health
        assert 'redis' in health
        assert 'worker_id' in health
        assert 'demo_mode' in health
        assert 'timestamp' in health
        
        print(f"✅ Worker health check returns proper structure: {health}")
        
    except ImportError as e:
        pytest.skip(f"Worker module not available: {e}")

def test_demo_mode_fallback():
    """Test DEMO_MODE fallback behavior"""
    try:
        with patch.dict(os.environ, {'DEMO_MODE': 'true'}):
            from redis_queue import worker
            
            steps = ['step1', 'step2']
            job_ids = worker.enqueue(steps)
            
            assert len(job_ids) == len(steps)
            assert all('demo-job-' in jid for jid in job_ids)
            
            print(f"✅ DEMO_MODE fallback works: {job_ids}")
            
    except ImportError as e:
        pytest.skip(f"Worker module not available: {e}")

def test_structured_logging():
    """Test structured logging utility"""
    try:
        from redis_queue.logger_util import log_structured
        
        log_structured(
            "INFO",
            "Test message",
            "test",
            trace_id="test-trace",
            task_id="test-task",
            elapsed_ms=123.45
        )
        
        print("✅ Structured logging works")
        
    except ImportError as e:
        pytest.skip(f"Logger utility not available: {e}")

if __name__ == "__main__":
    print("🧪 Running Worker Health and Fallback Tests")
    print("=" * 50)
    
    test_worker_health_check()
    test_demo_mode_fallback()
    test_structured_logging()
    
    print("=" * 50)
    print("🎉 Worker health tests completed!")
