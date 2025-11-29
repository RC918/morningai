#!/usr/bin/env python3
"""
Tests for Failure Memory Module - Phase 5 PR-4

Tests the save_failure_to_memory helper and recall functions.
"""

import sys
import os
import json
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGenerateFailureKey:
    """Tests for _generate_failure_key function"""

    def test_generate_key_with_trace_id_only(self):
        """Test generating key with only trace_id"""
        from failure_memory import _generate_failure_key

        key = _generate_failure_key("trace-123")
        assert key == "failure:trace-123"

    def test_generate_key_with_error_type(self):
        """Test generating key with error_type creates category key"""
        from failure_memory import _generate_failure_key

        key = _generate_failure_key("trace-123", error_type="timeout")
        assert key.startswith("failure:timeout:")
        assert len(key.split(":")) == 3

    def test_generate_key_with_error_type_and_timestamp(self):
        """Test generating key with error_type and custom timestamp"""
        from failure_memory import _generate_failure_key

        key = _generate_failure_key(
            "trace-123",
            error_type="ci_failure",
            timestamp="20251129120000"
        )
        assert key == "failure:ci_failure:20251129120000"


class TestSerializeFailureForMemory:
    """Tests for _serialize_failure_for_memory function"""

    def test_serialize_basic_failure(self):
        """Test serializing a basic failure record"""
        from failure_memory import _serialize_failure_for_memory

        failure_dict = {
            "goal": "Fix the bug",
            "error_type": "timeout",
            "task_type": "bug_fix",
            "fixer_retries": 2,
            "status": "error"
        }

        text = _serialize_failure_for_memory(failure_dict)

        assert "Goal: Fix the bug" in text
        assert "Error Type: timeout" in text
        assert "Task Type: bug_fix" in text
        assert "Fixer Retries: 2" in text
        assert "Status: error" in text

    def test_serialize_failure_with_error_message(self):
        """Test serializing failure with error message"""
        from failure_memory import _serialize_failure_for_memory

        failure_dict = {
            "goal": "Test goal",
            "error_type": "exception",
            "error_message": "Connection timeout after 30 seconds",
            "status": "error"
        }

        text = _serialize_failure_for_memory(failure_dict)

        assert "Error Message: Connection timeout" in text

    def test_serialize_failure_with_metadata(self):
        """Test serializing failure with metadata"""
        from failure_memory import _serialize_failure_for_memory

        failure_dict = {
            "goal": "Test goal",
            "error_type": "security",
            "status": "error",
            "metadata": {
                "security_risk": "high",
                "governance_risk": "medium"
            }
        }

        text = _serialize_failure_for_memory(failure_dict)

        assert "Security Risk: high" in text
        assert "Governance Risk: medium" in text

    def test_serialize_failure_truncates_long_error_message(self):
        """Test that long error messages are truncated"""
        from failure_memory import _serialize_failure_for_memory

        long_message = "x" * 500
        failure_dict = {
            "goal": "Test",
            "error_type": "error",
            "error_message": long_message,
            "status": "error"
        }

        text = _serialize_failure_for_memory(failure_dict)

        assert len(text) < len(long_message) + 200


class TestSaveFailureToMemory:
    """Tests for save_failure_to_memory function"""

    def test_save_failure_with_dict(self):
        """Test saving failure from dictionary"""
        from failure_memory import save_failure_to_memory

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        failure_dict = {
            "id": "fail-123",
            "trace_id": "trace-456",
            "goal": "Fix the bug",
            "error_type": "timeout",
            "task_type": "bug_fix",
            "fixer_retries": 1,
            "status": "error",
            "created_at": "2025-11-29T12:00:00",
            "env": "staging"
        }

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            result = save_failure_to_memory(failure_dict)

        assert result == "failure:trace-456"
        assert mock_client.table.called
        assert mock_table.insert.called

    def test_save_failure_with_failure_record(self):
        """Test saving failure from FailureRecord instance"""
        from failure_memory import save_failure_to_memory
        from failure_recorder import FailureRecord

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        failure = FailureRecord(
            trace_id="trace-789",
            goal="Implement feature",
            error_type="ci_failure"
        )

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            result = save_failure_to_memory(failure)

        assert result == "failure:trace-789"

    def test_save_failure_without_supabase_client(self):
        """Test saving failure when Supabase client is not available"""
        from failure_memory import save_failure_to_memory

        failure_dict = {
            "trace_id": "trace-123",
            "goal": "Test",
            "error_type": "error"
        }

        with patch("failure_memory._get_supabase_client", return_value=None):
            result = save_failure_to_memory(failure_dict)

        assert result is None

    def test_save_failure_without_trace_id(self):
        """Test saving failure without trace_id returns None"""
        from failure_memory import save_failure_to_memory

        failure_dict = {
            "goal": "Test",
            "error_type": "error"
        }

        result = save_failure_to_memory(failure_dict)

        assert result is None

    def test_save_failure_with_invalid_type(self):
        """Test saving failure with invalid type returns None"""
        from failure_memory import save_failure_to_memory

        result = save_failure_to_memory("invalid")

        assert result is None

    def test_save_failure_creates_category_key(self):
        """Test that category key is created when include_category_key=True"""
        from failure_memory import save_failure_to_memory

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        failure_dict = {
            "trace_id": "trace-123",
            "goal": "Test",
            "error_type": "timeout",
            "created_at": "2025-11-29T12:00:00"
        }

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            save_failure_to_memory(failure_dict, include_category_key=True)

        assert mock_table.insert.call_count == 2

    def test_save_failure_skips_category_key_when_disabled(self):
        """Test that category key is skipped when include_category_key=False"""
        from failure_memory import save_failure_to_memory

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock()

        failure_dict = {
            "trace_id": "trace-123",
            "goal": "Test",
            "error_type": "timeout"
        }

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            save_failure_to_memory(failure_dict, include_category_key=False)

        assert mock_table.insert.call_count == 1


class TestRecallFailuresByPrefix:
    """Tests for recall_failures_by_prefix function"""

    def test_recall_failures_by_prefix(self):
        """Test recalling failures by key prefix"""
        from failure_memory import recall_failures_by_prefix

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": 1,
                "key": "failure:trace-123",
                "text": "Goal: Test",
                "metadata": json.dumps({"error_type": "timeout"})
            }
        ]
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            results = recall_failures_by_prefix("failure:trace-123")

        assert len(results) == 1
        assert results[0]["key"] == "failure:trace-123"
        assert results[0]["metadata"]["error_type"] == "timeout"

    def test_recall_failures_without_supabase_client(self):
        """Test recalling failures when Supabase client is not available"""
        from failure_memory import recall_failures_by_prefix

        with patch("failure_memory._get_supabase_client", return_value=None):
            results = recall_failures_by_prefix("failure:")

        assert results == []

    def test_recall_failures_handles_invalid_metadata(self):
        """Test that invalid metadata JSON is handled gracefully"""
        from failure_memory import recall_failures_by_prefix

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": 1,
                "key": "failure:trace-123",
                "text": "Goal: Test",
                "metadata": "invalid json"
            }
        ]
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            results = recall_failures_by_prefix("failure:")

        assert len(results) == 1
        assert results[0]["metadata"] == {}


class TestRecallFailuresByTraceId:
    """Tests for recall_failures_by_trace_id function"""

    def test_recall_by_trace_id(self):
        """Test recalling failures by trace_id"""
        from failure_memory import recall_failures_by_trace_id

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.data = [
            {"id": 1, "key": "failure:trace-123", "text": "Test", "metadata": "{}"}
        ]
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            results = recall_failures_by_trace_id("trace-123")

        assert len(results) == 1
        mock_table.like.assert_called_with("key", "failure:trace-123%")


class TestRecallFailuresByErrorType:
    """Tests for recall_failures_by_error_type function"""

    def test_recall_by_error_type(self):
        """Test recalling failures by error type"""
        from failure_memory import recall_failures_by_error_type

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.data = [
            {"id": 1, "key": "failure:timeout:20251129", "text": "Test", "metadata": "{}"}
        ]
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            results = recall_failures_by_error_type("timeout")

        assert len(results) == 1
        mock_table.like.assert_called_with("key", "failure:timeout:%")


class TestRecallRecentFailures:
    """Tests for recall_recent_failures function"""

    def test_recall_recent_failures(self):
        """Test recalling recent failures"""
        from failure_memory import recall_recent_failures

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.data = [
            {"id": 1, "key": "failure:trace-1", "text": "Test 1", "metadata": "{}"},
            {"id": 2, "key": "failure:trace-2", "text": "Test 2", "metadata": "{}"}
        ]
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            results = recall_recent_failures(limit=10)

        assert len(results) == 2
        mock_table.limit.assert_called_with(10)

    def test_recall_recent_failures_without_client(self):
        """Test recalling recent failures without Supabase client"""
        from failure_memory import recall_recent_failures

        with patch("failure_memory._get_supabase_client", return_value=None):
            results = recall_recent_failures()

        assert results == []


class TestGetFailureMemoryStats:
    """Tests for get_failure_memory_stats function"""

    def test_get_stats_without_client(self):
        """Test getting stats when Supabase client is not available"""
        from failure_memory import get_failure_memory_stats

        with patch("failure_memory._get_supabase_client", return_value=None):
            stats = get_failure_memory_stats()

        assert stats["enabled"] is False
        assert "error" in stats

    def test_get_stats_with_client(self):
        """Test getting stats with Supabase client"""
        from failure_memory import get_failure_memory_stats

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.like.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table

        mock_result = MagicMock()
        mock_result.count = 10
        mock_result.data = []
        mock_table.execute.return_value = mock_result

        with patch("failure_memory._get_supabase_client", return_value=mock_client):
            with patch("failure_memory.recall_recent_failures", return_value=[]):
                stats = get_failure_memory_stats()

        assert stats["enabled"] is True
        assert "total_records" in stats
