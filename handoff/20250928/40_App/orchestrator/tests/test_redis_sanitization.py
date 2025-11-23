"""
Unit tests for Redis mapping sanitization in worker.py

Tests the sanitize_redis_mapping function that filters None values
from dictionaries before passing them to Redis commands.
"""


def sanitize_redis_mapping(mapping: dict) -> dict:
    """
    Remove None values from Redis mapping to prevent DataError.
    
    This is a copy of the function from worker.py for testing purposes.
    Redis commands like hset() require values to be bytes, string, int, or float.
    Passing None causes: redis.exceptions.DataError: Invalid input of type: 'NoneType'
    
    Args:
        mapping: Dictionary with potential None values
        
    Returns:
        Dictionary with None values filtered out
    """
    return {k: v for k, v in mapping.items() if v is not None}


def test_sanitize_redis_mapping_removes_none_values():
    """Test that None values are filtered out"""
    mapping = {
        "status": "done",
        "question": "test question",
        "trace_id": "trace-123",
        "job_id": "job-456",
        "pr_url": None,  # This should be removed
        "state": None,   # This should be removed
        "updated_at": "2025-11-22T15:00:00Z"
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert "pr_url" not in result
    assert "state" not in result
    assert result["status"] == "done"
    assert result["question"] == "test question"
    assert result["trace_id"] == "trace-123"
    assert result["job_id"] == "job-456"
    assert result["updated_at"] == "2025-11-22T15:00:00Z"


def test_sanitize_redis_mapping_preserves_all_valid_values():
    """Test that all non-None values are preserved"""
    mapping = {
        "status": "running",
        "question": "test question",
        "trace_id": "trace-123",
        "job_id": "job-456",
        "updated_at": "2025-11-22T15:00:00Z"
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert result == mapping
    assert len(result) == 5


def test_sanitize_redis_mapping_handles_empty_dict():
    """Test that empty dictionary is handled correctly"""
    mapping = {}
    
    result = sanitize_redis_mapping(mapping)
    
    assert result == {}
    assert len(result) == 0


def test_sanitize_redis_mapping_handles_all_none_values():
    """Test that dictionary with all None values returns empty dict"""
    mapping = {
        "field1": None,
        "field2": None,
        "field3": None
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert result == {}
    assert len(result) == 0


def test_sanitize_redis_mapping_preserves_empty_strings():
    """Test that empty strings are preserved (not treated as None)"""
    mapping = {
        "status": "done",
        "pr_url": "",  # Empty string should be preserved
        "state": None  # None should be removed
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert "pr_url" in result
    assert result["pr_url"] == ""
    assert "state" not in result
    assert result["status"] == "done"


def test_sanitize_redis_mapping_preserves_zero_values():
    """Test that zero values are preserved (not treated as None)"""
    mapping = {
        "status": "done",
        "count": 0,  # Zero should be preserved
        "value": None  # None should be removed
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert "count" in result
    assert result["count"] == 0
    assert "value" not in result
    assert result["status"] == "done"


def test_sanitize_redis_mapping_preserves_false_values():
    """Test that False values are preserved (not treated as None)"""
    mapping = {
        "status": "done",
        "enabled": False,  # False should be preserved
        "value": None  # None should be removed
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert "enabled" in result
    assert result["enabled"] is False
    assert "value" not in result
    assert result["status"] == "done"


def test_sanitize_redis_mapping_real_world_running_status():
    """Test with real-world 'running' status mapping"""
    mapping = {
        "status": "running",
        "question": "How do I fix this bug?",
        "trace_id": "task-abc-123",
        "job_id": "task-abc-123",
        "updated_at": "2025-11-22T15:37:54.123456+00:00"
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert result == mapping
    assert len(result) == 5


def test_sanitize_redis_mapping_real_world_done_status():
    """Test with real-world 'done' status mapping that may have None values"""
    mapping = {
        "status": "done",
        "question": "How do I fix this bug?",
        "trace_id": "trace-xyz-789",
        "job_id": "task-abc-123",
        "pr_url": None,  # May be None if PR creation failed
        "state": None,   # May be None if state is unknown
        "updated_at": "2025-11-22T15:38:24.123456+00:00"
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert "pr_url" not in result
    assert "state" not in result
    assert result["status"] == "done"
    assert result["question"] == "How do I fix this bug?"
    assert result["trace_id"] == "trace-xyz-789"
    assert result["job_id"] == "task-abc-123"
    assert result["updated_at"] == "2025-11-22T15:38:24.123456+00:00"


def test_sanitize_redis_mapping_real_world_error_status():
    """Test with real-world 'error' status mapping"""
    mapping = {
        "status": "error",
        "question": "How do I fix this bug?",
        "trace_id": "task-abc-123",
        "job_id": "task-abc-123",
        "error_code": "ORCHESTRATOR_FAILED",
        "error_message": "Redis DataError: Invalid input of type: 'NoneType'",
        "updated_at": "2025-11-22T15:37:55.123456+00:00"
    }
    
    result = sanitize_redis_mapping(mapping)
    
    assert result == mapping
    assert len(result) == 7
