"""
Tests for redis_queue/logger_util.py module

This module tests the structured logging utility for worker operations.
"""
import json
import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from redis_queue.logger_util import log_structured


class TestLogStructured:
    """Tests for log_structured function"""

    @patch("builtins.print")
    def test_basic_log(self, mock_print):
        """Test basic structured log output"""
        log_structured(
            level="INFO",
            message="Test message",
            operation="test_op",
        )

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["operation"] == "test_op"
        assert "timestamp" in log_entry

    @patch("builtins.print")
    def test_log_with_trace_id(self, mock_print):
        """Test log with trace_id"""
        log_structured(
            level="INFO",
            message="Test message",
            operation="test_op",
            trace_id="trace_123",
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["trace_id"] == "trace_123"

    @patch("builtins.print")
    def test_log_with_task_id(self, mock_print):
        """Test log with task_id"""
        log_structured(
            level="INFO",
            message="Test message",
            operation="test_op",
            task_id="task_456",
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["task_id"] == "task_456"

    @patch("builtins.print")
    def test_log_with_elapsed_ms(self, mock_print):
        """Test log with elapsed_ms"""
        log_structured(
            level="INFO",
            message="Test message",
            operation="test_op",
            elapsed_ms=123.456789,
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["elapsed_ms"] == 123.46  # Rounded to 2 decimal places

    @patch("builtins.print")
    def test_log_with_elapsed_ms_zero(self, mock_print):
        """Test log with elapsed_ms of zero"""
        log_structured(
            level="INFO",
            message="Test message",
            operation="test_op",
            elapsed_ms=0,
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["elapsed_ms"] == 0

    @patch("builtins.print")
    def test_log_with_extra_fields(self, mock_print):
        """Test log with extra keyword arguments"""
        log_structured(
            level="ERROR",
            message="Error occurred",
            operation="process",
            error_code="E001",
            retry_count=3,
            details={"key": "value"},
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["error_code"] == "E001"
        assert log_entry["retry_count"] == 3
        assert log_entry["details"] == {"key": "value"}

    @patch("builtins.print")
    def test_log_all_fields(self, mock_print):
        """Test log with all optional fields"""
        log_structured(
            level="WARNING",
            message="Warning message",
            operation="enqueue",
            trace_id="trace_abc",
            task_id="task_xyz",
            elapsed_ms=50.5,
            custom_field="custom_value",
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert log_entry["level"] == "WARNING"
        assert log_entry["message"] == "Warning message"
        assert log_entry["operation"] == "enqueue"
        assert log_entry["trace_id"] == "trace_abc"
        assert log_entry["task_id"] == "task_xyz"
        assert log_entry["elapsed_ms"] == 50.5
        assert log_entry["custom_field"] == "custom_value"

    @patch("builtins.print")
    def test_log_timestamp_format(self, mock_print):
        """Test that timestamp is in valid ISO format with Z suffix (not +00:00Z)"""
        log_structured(
            level="INFO",
            message="Test",
            operation="test",
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        timestamp = log_entry["timestamp"]
        # Must end with Z (UTC indicator)
        assert timestamp.endswith("Z"), f"Timestamp should end with Z, got: {timestamp}"
        # Must NOT have both +00:00 and Z (invalid ISO 8601)
        assert "+00:00" not in timestamp, f"Timestamp should not contain +00:00 when using Z suffix, got: {timestamp}"
        # Verify it's a valid ISO format by parsing
        # Remove the trailing Z for parsing
        datetime.fromisoformat(timestamp.rstrip("Z"))

    @patch("builtins.print")
    def test_log_without_optional_fields(self, mock_print):
        """Test that optional fields are not included when not provided"""
        log_structured(
            level="INFO",
            message="Test",
            operation="test",
        )

        call_args = mock_print.call_args[0][0]
        log_entry = json.loads(call_args)

        assert "trace_id" not in log_entry
        assert "task_id" not in log_entry
        assert "elapsed_ms" not in log_entry

    @patch("builtins.print")
    def test_log_different_levels(self, mock_print):
        """Test logging with different log levels"""
        for level in ["INFO", "ERROR", "WARNING", "DEBUG"]:
            log_structured(
                level=level,
                message="Test",
                operation="test",
            )

            call_args = mock_print.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["level"] == level

    @patch("builtins.print")
    def test_log_different_operations(self, mock_print):
        """Test logging with different operation types"""
        operations = ["enqueue", "process", "complete", "fail", "retry"]

        for op in operations:
            log_structured(
                level="INFO",
                message="Test",
                operation=op,
            )

            call_args = mock_print.call_args[0][0]
            log_entry = json.loads(call_args)
            assert log_entry["operation"] == op
