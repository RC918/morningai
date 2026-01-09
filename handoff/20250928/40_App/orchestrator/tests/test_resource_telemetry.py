"""
Tests for Resource Telemetry Module

Issue #3729: Log sanitization helper for user-controlled data
"""
from unittest.mock import patch

from resource_telemetry import (
    _sanitize_for_log,
    _is_telemetry_enabled,
    log_context_file_scan,
    log_context_file_select,
    log_context_token_budget,
)


class TestSanitizeForLog:
    """Tests for _sanitize_for_log helper function (Issue #3729)."""

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert _sanitize_for_log("") == ""

    def test_none_value(self):
        """None value should return empty string."""
        assert _sanitize_for_log(None) == ""

    def test_normal_string(self):
        """Normal string without special chars should pass through."""
        assert _sanitize_for_log("hello world") == "hello world"

    def test_removes_newlines(self):
        """Newlines should be replaced with spaces."""
        assert _sanitize_for_log("line1\nline2") == "line1 line2"
        assert _sanitize_for_log("line1\nline2\nline3") == "line1 line2 line3"

    def test_removes_carriage_returns(self):
        """Carriage returns should be replaced with spaces."""
        assert _sanitize_for_log("line1\rline2") == "line1 line2"

    def test_removes_crlf(self):
        """CRLF sequences should be replaced with spaces."""
        assert _sanitize_for_log("line1\r\nline2") == "line1  line2"

    def test_log_injection_attempt(self):
        """Should prevent log injection attacks."""
        malicious = "normal text\n[FAKE_EVENT] Injected log entry"
        sanitized = _sanitize_for_log(malicious)
        assert "\n" not in sanitized
        assert sanitized == "normal text [FAKE_EVENT] Injected log entry"

    def test_file_path_with_newline(self):
        """File paths with newlines should be sanitized."""
        path = "/path/to/file\nwith/newline"
        assert _sanitize_for_log(path) == "/path/to/file with/newline"

    def test_goal_with_multiline(self):
        """Multi-line goals should be sanitized."""
        goal = "Fix the bug\nthat causes\nthe crash"
        assert _sanitize_for_log(goal) == "Fix the bug that causes the crash"


class TestTelemetryEnabled:
    """Tests for _is_telemetry_enabled function."""

    def test_default_enabled(self):
        """Telemetry should be enabled by default."""
        with patch.dict('os.environ', {}, clear=True):
            assert _is_telemetry_enabled() is True

    def test_explicit_true(self):
        """Telemetry should be enabled when set to 'true'."""
        with patch.dict('os.environ', {'RESOURCE_TELEMETRY_ENABLED': 'true'}):
            assert _is_telemetry_enabled() is True

    def test_explicit_false(self):
        """Telemetry should be disabled when set to 'false'."""
        with patch.dict('os.environ', {'RESOURCE_TELEMETRY_ENABLED': 'false'}):
            assert _is_telemetry_enabled() is False

    def test_zero_disables(self):
        """Telemetry should be disabled when set to '0'."""
        with patch.dict('os.environ', {'RESOURCE_TELEMETRY_ENABLED': '0'}):
            assert _is_telemetry_enabled() is False


class TestLogContextFileScan:
    """Tests for log_context_file_scan with sanitization."""

    @patch('resource_telemetry.logger')
    @patch('resource_telemetry._is_telemetry_enabled', return_value=True)
    @patch('resource_telemetry.get_current_rss_mb', return_value=(100.0, True))
    def test_sanitizes_goal(self, mock_rss, mock_enabled, mock_logger):
        """Goal should be sanitized before logging."""
        goal_with_newline = "Fix the bug\nthat causes issues"

        log_context_file_scan(
            goal=goal_with_newline,
            files_scanned=10,
            search_dirs=["/src"],
            max_scan=100,
            trace_id="test-trace"
        )

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert "\n" not in call_kwargs['extra']['goal_preview']
        assert call_kwargs['extra']['goal_preview'] == "Fix the bug that causes issues"

    @patch('resource_telemetry.logger')
    @patch('resource_telemetry._is_telemetry_enabled', return_value=True)
    @patch('resource_telemetry.get_current_rss_mb', return_value=(100.0, True))
    def test_truncates_long_goal(self, mock_rss, mock_enabled, mock_logger):
        """Goal should be truncated to 100 chars before sanitization."""
        long_goal = "a" * 200

        log_context_file_scan(
            goal=long_goal,
            files_scanned=10,
            search_dirs=["/src"],
            max_scan=100,
            trace_id="test-trace"
        )

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        assert len(call_kwargs['extra']['goal_preview']) == 100


class TestLogContextFileSelect:
    """Tests for log_context_file_select with sanitization."""

    @patch('resource_telemetry.logger')
    @patch('resource_telemetry._is_telemetry_enabled', return_value=True)
    @patch('resource_telemetry.get_current_rss_mb', return_value=(100.0, True))
    def test_sanitizes_file_paths(self, mock_rss, mock_enabled, mock_logger):
        """File paths should be sanitized before logging."""
        files_with_newlines = [
            ("/path/to/file\nwith/newline", 0.9),
            ("/normal/path", 0.8),
        ]

        log_context_file_select(
            selected_files=files_with_newlines,
            max_files=10,
            trace_id="test-trace"
        )

        mock_logger.info.assert_called_once()
        call_kwargs = mock_logger.info.call_args[1]
        file_details = call_kwargs['extra']['selected_files']

        assert file_details[0]['path'] == "/path/to/file with/newline"
        assert file_details[1]['path'] == "/normal/path"


class TestLogContextTokenBudget:
    """Tests for log_context_token_budget with sanitization."""

    @patch('resource_telemetry.logger')
    @patch('resource_telemetry._is_telemetry_enabled', return_value=True)
    @patch('resource_telemetry.get_current_rss_mb', return_value=(100.0, True))
    def test_sanitizes_excluded_files(self, mock_rss, mock_enabled, mock_logger):
        """Excluded file paths should be sanitized before logging."""
        excluded_with_newlines = [
            "/path/to/file\nwith/newline",
            "/normal/path",
        ]

        log_context_token_budget(
            files_included=5,
            files_excluded=2,
            tokens_used=5000,
            max_tokens=10000,
            budget_exceeded=False,
            excluded_files=excluded_with_newlines,
            trace_id="test-trace"
        )

        mock_logger.log.assert_called_once()
        call_kwargs = mock_logger.log.call_args[1]
        excluded = call_kwargs['extra']['excluded_files']

        assert excluded[0] == "/path/to/file with/newline"
        assert excluded[1] == "/normal/path"

    @patch('resource_telemetry.logger')
    @patch('resource_telemetry._is_telemetry_enabled', return_value=True)
    @patch('resource_telemetry.get_current_rss_mb', return_value=(100.0, True))
    def test_handles_none_excluded_files(self, mock_rss, mock_enabled, mock_logger):
        """Should handle None excluded_files gracefully."""
        log_context_token_budget(
            files_included=5,
            files_excluded=0,
            tokens_used=5000,
            max_tokens=10000,
            budget_exceeded=False,
            excluded_files=None,
            trace_id="test-trace"
        )

        mock_logger.log.assert_called_once()
        call_kwargs = mock_logger.log.call_args[1]
        assert call_kwargs['extra']['excluded_files'] == []
