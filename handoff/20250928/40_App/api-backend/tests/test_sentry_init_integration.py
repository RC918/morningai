"""Integration tests for Sentry initialization module (src/extensions/sentry.py).

This module provides integration and E2E-style tests for the Sentry initialization
module. These tests verify the interaction between init_sentry(), before_send(),
and the Sentry SDK.

Test Categories:
1. Integration tests with mocked Sentry SDK
2. Logging behavior tests
3. Environment-specific behavior tests
4. before_send edge case tests

See: docs/config/sentry_initialization.md for detailed documentation.

NOTE: This is separate from test_sentry_integration.py which tests
services.sentry_integration module (Issue #1915).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging


class TestSentryInitIntegration:
    """Integration tests for Sentry initialization with Flask app."""

    def _create_mock_settings(self, sentry_dsn="https://test@sentry.io/123",
                               environment="development", app_version="8.0.0"):
        """Create a mock app_settings object for testing."""
        mock_settings = Mock()
        mock_settings.sentry_dsn = sentry_dsn
        mock_settings.environment = environment
        mock_settings.app_version = app_version
        return mock_settings

    def test_sentry_integration_with_flask_integration(self, monkeypatch):
        """Test Sentry integrates correctly with FlaskIntegration."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="staging")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            mock_flask_integration = MagicMock()
            with patch("src.extensions.sentry.FlaskIntegration", return_value=mock_flask_integration):
                result = init_sentry(mock_settings, _as_bool)

                mock_sentry.init.assert_called_once()
                call_kwargs = mock_sentry.init.call_args[1]

                assert call_kwargs["dsn"] == "https://test@sentry.io/123"
                assert call_kwargs["environment"] == "staging"
                assert call_kwargs["release"] == "morningai@8.0.0"
                assert call_kwargs["traces_sample_rate"] == 1.0
                assert mock_flask_integration in call_kwargs["integrations"]
                assert result == "https://test@sentry.io/123"

    def test_sentry_init_captures_before_send_callback(self, monkeypatch):
        """Test that init_sentry passes before_send callback to sentry_sdk.init."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="staging")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry, before_send

        captured_before_send = None

        def capture_init(**kwargs):
            nonlocal captured_before_send
            captured_before_send = kwargs.get("before_send")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            mock_sentry.init.side_effect = capture_init
            with patch("src.extensions.sentry.FlaskIntegration"):
                init_sentry(mock_settings, _as_bool)

        assert captured_before_send is before_send

    def test_captured_before_send_filters_correctly(self, monkeypatch):
        """Test the captured before_send callback filters 400/404 correctly."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="staging")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        captured_before_send = None

        def capture_init(**kwargs):
            nonlocal captured_before_send
            captured_before_send = kwargs.get("before_send")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            mock_sentry.init.side_effect = capture_init
            with patch("src.extensions.sentry.FlaskIntegration"):
                init_sentry(mock_settings, _as_bool)

        assert captured_before_send({'request': {'status_code': 400}}, {}) is None
        assert captured_before_send({'request': {'status_code': 404}}, {}) is None
        assert captured_before_send({'request': {'status_code': 500}}, {}) is not None
        assert captured_before_send({'request': {'status_code': 401}}, {}) is not None

    def test_sentry_init_with_empty_dsn(self, monkeypatch):
        """Test Sentry does not initialize with empty DSN."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(sentry_dsn="")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            mock_sentry.init.assert_not_called()
            assert result is None

    def test_sentry_init_with_none_dsn(self, monkeypatch):
        """Test Sentry does not initialize with None DSN."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(sentry_dsn=None)

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            mock_sentry.init.assert_not_called()
            assert result is None

    def test_sentry_init_with_whitespace_only_dsn(self, monkeypatch):
        """Test Sentry does not initialize with whitespace-only DSN."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(sentry_dsn="   ")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            mock_sentry.init.assert_not_called()
            assert result is None


class TestSentryInitLogging:
    """Test logging behavior during Sentry initialization."""

    def _create_mock_settings(self, sentry_dsn="https://test@sentry.io/123",
                               environment="development", app_version="8.0.0"):
        """Create a mock app_settings object for testing."""
        mock_settings = Mock()
        mock_settings.sentry_dsn = sentry_dsn
        mock_settings.environment = environment
        mock_settings.app_version = app_version
        return mock_settings

    def test_logs_info_on_successful_init(self, monkeypatch, caplog):
        """Test INFO log on successful Sentry initialization."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="staging")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with caplog.at_level(logging.INFO):
            with patch("src.extensions.sentry.sentry_sdk"):
                with patch("src.extensions.sentry.FlaskIntegration"):
                    init_sentry(mock_settings, _as_bool)

        assert "Sentry initialized successfully" in caplog.text
        assert "morningai@8.0.0" in caplog.text

    def test_logs_info_when_disabled_for_testing(self, monkeypatch, caplog):
        """Test INFO log when Sentry is disabled for testing."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="development")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with caplog.at_level(logging.INFO):
            with patch("src.extensions.sentry.sentry_sdk"):
                init_sentry(mock_settings, _as_bool)

        assert "Sentry disabled in testing environment" in caplog.text

    def test_logs_warning_for_production_guard(self, monkeypatch, caplog):
        """Test WARNING log when production guard is triggered."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="production")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with caplog.at_level(logging.WARNING):
            with patch("src.extensions.sentry.sentry_sdk"):
                with patch("src.extensions.sentry.FlaskIntegration"):
                    init_sentry(mock_settings, _as_bool)

        assert "environment is production" in caplog.text
        assert "Sentry will remain enabled" in caplog.text

    def test_logs_warning_on_init_failure(self, monkeypatch, caplog):
        """Test WARNING log when Sentry initialization fails."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="staging")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with caplog.at_level(logging.WARNING):
            with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
                mock_sentry.init.side_effect = Exception("Connection failed")
                with patch("src.extensions.sentry.FlaskIntegration"):
                    result = init_sentry(mock_settings, _as_bool)

        assert "Failed to initialize Sentry" in caplog.text
        assert "Connection failed" in caplog.text
        assert result is None


class TestSentryInitEnvironmentBehavior:
    """Test Sentry behavior across different environments."""

    def _create_mock_settings(self, sentry_dsn="https://test@sentry.io/123",
                               environment="development", app_version="8.0.0"):
        """Create a mock app_settings object for testing."""
        mock_settings = Mock()
        mock_settings.sentry_dsn = sentry_dsn
        mock_settings.environment = environment
        mock_settings.app_version = app_version
        return mock_settings

    @pytest.mark.parametrize("environment", ["development", "staging", "test"])
    def test_sentry_disabled_in_non_production_with_testing_flag(self, monkeypatch, environment):
        """Test Sentry is disabled in non-production environments when TESTING=true."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment=environment)

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            mock_sentry.init.assert_not_called()
            assert result is None

    def test_sentry_enabled_in_production_despite_testing_flag(self, monkeypatch):
        """Test production guard keeps Sentry enabled despite TESTING=true."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment="production")

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                result = init_sentry(mock_settings, _as_bool)

                mock_sentry.init.assert_called_once()
                assert result == "https://test@sentry.io/123"

    def test_environment_defaults_to_development(self, monkeypatch):
        """Test environment defaults to 'development' when None."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(environment=None)

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                init_sentry(mock_settings, _as_bool)

                call_kwargs = mock_sentry.init.call_args[1]
                assert call_kwargs["environment"] == "development"

    def test_app_version_defaults_to_8_0_0(self, monkeypatch):
        """Test app_version defaults to '8.0.0' when None."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        mock_settings = self._create_mock_settings(app_version=None)

        from src.utils.helpers import _as_bool
        from src.extensions.sentry import init_sentry

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                init_sentry(mock_settings, _as_bool)

                call_kwargs = mock_sentry.init.call_args[1]
                assert call_kwargs["release"] == "morningai@8.0.0"


class TestBeforeSendEdgeCases:
    """Test edge cases for before_send callback."""

    def test_before_send_with_exception_code_400(self):
        """Test before_send filters exception with code 400."""
        from src.extensions.sentry import before_send

        error = Exception("Bad request")
        error.code = 400

        event = {}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_with_exception_code_404(self):
        """Test before_send filters exception with code 404."""
        from src.extensions.sentry import before_send

        error = Exception("Not found")
        error.code = 404

        event = {}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_with_exception_code_500(self):
        """Test before_send allows exception with code 500."""
        from src.extensions.sentry import before_send

        error = Exception("Internal server error")
        error.code = 500

        event = {'message': 'test'}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_with_exception_no_code(self):
        """Test before_send allows exception without code attribute."""
        from src.extensions.sentry import before_send

        error = ValueError("Some value error")

        event = {'message': 'test'}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_with_empty_event(self):
        """Test before_send handles empty event."""
        from src.extensions.sentry import before_send

        event = {}
        hint = {}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_with_nested_request_status(self):
        """Test before_send checks nested request.status_code."""
        from src.extensions.sentry import before_send

        event = {'request': {'status_code': 404, 'url': '/api/test'}}
        hint = {}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_with_missing_request_key(self):
        """Test before_send handles missing request key."""
        from src.extensions.sentry import before_send

        event = {'message': 'test error'}
        hint = {}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_with_missing_status_code(self):
        """Test before_send handles missing status_code in request."""
        from src.extensions.sentry import before_send

        event = {'request': {'url': '/api/test'}}
        hint = {}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_with_werkzeug_not_found(self):
        """Test before_send filters Werkzeug NotFound exception."""
        from src.extensions.sentry import before_send
        from werkzeug.exceptions import NotFound

        error = NotFound("Resource not found")

        event = {'message': 'test'}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_with_werkzeug_bad_request(self):
        """Test before_send filters Werkzeug BadRequest exception."""
        from src.extensions.sentry import before_send
        from werkzeug.exceptions import BadRequest

        error = BadRequest("Invalid request")

        event = {'message': 'test'}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_with_werkzeug_internal_server_error(self):
        """Test before_send allows Werkzeug InternalServerError exception."""
        from src.extensions.sentry import before_send
        from werkzeug.exceptions import InternalServerError

        error = InternalServerError("Server error")

        event = {'message': 'test'}
        hint = {'exc_info': (type(error), error, None)}

        result = before_send(event, hint)
        assert result == event
