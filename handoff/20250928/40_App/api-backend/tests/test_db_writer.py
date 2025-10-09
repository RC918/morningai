#!/usr/bin/env python3
"""
Unit tests for agent_tasks database writer
"""
import pytest
import uuid
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_db_writer_module_imports():
    """Test that db_writer module can be imported"""
    try:
        from orchestrator.persistence import db_writer
        
        assert hasattr(db_writer, 'upsert_task_queued')
        assert hasattr(db_writer, 'upsert_task_running')
        assert hasattr(db_writer, 'upsert_task_done')
        assert hasattr(db_writer, 'upsert_task_error')
        
        print("✅ db_writer module imports successfully")
    except ImportError as e:
        pytest.skip(f"db_writer module not available: {e}")

@patch('orchestrator.persistence.db_writer.get_client')
def test_upsert_task_queued(mock_get_client):
    """Test queued task insertion"""
    from orchestrator.persistence.db_writer import upsert_task_queued
    
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None
    mock_get_client.return_value = mock_client
    
    task_id = str(uuid.uuid4())
    trace_id = task_id
    question = "Test question"
    job_id = str(uuid.uuid4())
    
    result = upsert_task_queued(task_id, trace_id, question, job_id)
    
    assert result is True
    mock_client.table.assert_called_with("agent_tasks")
    mock_table.upsert.assert_called_once()
    
    call_args = mock_table.upsert.call_args
    data = call_args[0][0]
    assert data["task_id"] == task_id
    assert data["trace_id"] == trace_id
    assert data["question"] == question
    assert data["status"] == "queued"
    assert data["job_id"] == job_id
    
    print("✅ upsert_task_queued works correctly")

@patch('orchestrator.persistence.db_writer.get_client')
def test_upsert_task_running(mock_get_client):
    """Test running task update"""
    from orchestrator.persistence.db_writer import upsert_task_running
    
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None
    mock_get_client.return_value = mock_client
    
    task_id = str(uuid.uuid4())
    trace_id = task_id
    
    result = upsert_task_running(task_id, trace_id)
    
    assert result is True
    
    call_args = mock_table.upsert.call_args
    data = call_args[0][0]
    assert data["status"] == "running"
    assert "started_at" in data
    
    print("✅ upsert_task_running works correctly")

@patch('orchestrator.persistence.db_writer.get_client')
def test_upsert_task_done(mock_get_client):
    """Test done task update with pr_url"""
    from orchestrator.persistence.db_writer import upsert_task_done
    
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None
    mock_get_client.return_value = mock_client
    
    task_id = str(uuid.uuid4())
    trace_id = task_id
    pr_url = "https://github.com/RC918/morningai/pull/123"
    
    result = upsert_task_done(task_id, trace_id, pr_url)
    
    assert result is True
    
    call_args = mock_table.upsert.call_args
    data = call_args[0][0]
    assert data["status"] == "done"
    assert data["pr_url"] == pr_url
    assert "finished_at" in data
    
    print("✅ upsert_task_done works correctly")

@patch('orchestrator.persistence.db_writer.get_client')
def test_upsert_task_error(mock_get_client):
    """Test error task update with error message"""
    from orchestrator.persistence.db_writer import upsert_task_error
    
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value.execute.return_value = None
    mock_get_client.return_value = mock_client
    
    task_id = str(uuid.uuid4())
    trace_id = task_id
    error_msg = "OpenAI API timeout"
    
    result = upsert_task_error(task_id, trace_id, error_msg)
    
    assert result is True
    
    call_args = mock_table.upsert.call_args
    data = call_args[0][0]
    assert data["status"] == "error"
    assert data["error_msg"] == error_msg
    assert "finished_at" in data
    
    print("✅ upsert_task_error works correctly")

@patch('orchestrator.persistence.db_writer.get_client')
def test_error_handling_graceful_failure(mock_get_client):
    """Test that DB write failures don't crash the app"""
    from orchestrator.persistence.db_writer import upsert_task_queued
    
    mock_get_client.side_effect = Exception("DB connection failed")
    
    task_id = str(uuid.uuid4())
    result = upsert_task_queued(task_id, task_id, "Test question")
    
    assert result is False
    
    print("✅ Error handling works correctly (graceful failure)")

if __name__ == "__main__":
    print("🧪 Running DB Writer Unit Tests")
    print("=" * 50)
    
    test_db_writer_module_imports()
    test_upsert_task_queued()
    test_upsert_task_running()
    test_upsert_task_done()
    test_upsert_task_error()
    test_error_handling_graceful_failure()
    
    print("=" * 50)
    print("🎉 DB writer tests completed!")
