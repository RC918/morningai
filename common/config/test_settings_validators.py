"""
Unit tests for Settings validators.

Tests case-insensitive validation for log_level and gunicorn_log_level fields.
"""

import os
import pytest
from pydantic import ValidationError
from common.config.settings import reload_settings


class TestLogLevelValidator:
    """Test case-insensitive validation for log_level field."""

    def test_log_level_uppercase(self):
        """Test that uppercase log levels are accepted."""
        os.environ['LOG_LEVEL'] = 'INFO'
        settings = reload_settings()
        assert settings.log_level == 'INFO'

    def test_log_level_lowercase(self):
        """Test that lowercase log levels are normalized to uppercase."""
        os.environ['LOG_LEVEL'] = 'info'
        settings = reload_settings()
        assert settings.log_level == 'INFO'

    def test_log_level_mixed_case(self):
        """Test that mixed case log levels are normalized to uppercase."""
        os.environ['LOG_LEVEL'] = 'Info'
        settings = reload_settings()
        assert settings.log_level == 'INFO'

    def test_log_level_with_whitespace(self):
        """Test that log levels with whitespace are trimmed and normalized."""
        os.environ['LOG_LEVEL'] = '  info  '
        settings = reload_settings()
        assert settings.log_level == 'INFO'

    def test_log_level_all_valid_values(self):
        """Test all valid log level values in different cases."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in valid_levels:
            os.environ['LOG_LEVEL'] = level
            settings = reload_settings()
            assert settings.log_level == level

            os.environ['LOG_LEVEL'] = level.lower()
            settings = reload_settings()
            assert settings.log_level == level

            os.environ['LOG_LEVEL'] = level.capitalize()
            settings = reload_settings()
            assert settings.log_level == level

    def test_log_level_invalid_value(self):
        """Test that invalid log levels raise ValidationError."""
        os.environ['LOG_LEVEL'] = 'INVALID'
        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert 'log_level' in str(exc_info.value).lower()

    def test_log_level_default(self):
        """Test that default log level is INFO when not set."""
        if 'LOG_LEVEL' in os.environ:
            del os.environ['LOG_LEVEL']
        settings = reload_settings()
        assert settings.log_level == 'INFO'


class TestGunicornLogLevelValidator:
    """Test case-insensitive validation for gunicorn_log_level field."""

    def test_gunicorn_log_level_lowercase(self):
        """Test that lowercase gunicorn log levels are accepted."""
        os.environ['GUNICORN_LOG_LEVEL'] = 'info'
        settings = reload_settings()
        assert settings.gunicorn_log_level == 'info'

    def test_gunicorn_log_level_uppercase(self):
        """Test that uppercase gunicorn log levels are normalized to lowercase."""
        os.environ['GUNICORN_LOG_LEVEL'] = 'INFO'
        settings = reload_settings()
        assert settings.gunicorn_log_level == 'info'

    def test_gunicorn_log_level_mixed_case(self):
        """Test that mixed case gunicorn log levels are normalized to lowercase."""
        os.environ['GUNICORN_LOG_LEVEL'] = 'Info'
        settings = reload_settings()
        assert settings.gunicorn_log_level == 'info'

    def test_gunicorn_log_level_with_whitespace(self):
        """Test that gunicorn log levels with whitespace are trimmed and normalized."""
        os.environ['GUNICORN_LOG_LEVEL'] = '  INFO  '
        settings = reload_settings()
        assert settings.gunicorn_log_level == 'info'

    def test_gunicorn_log_level_all_valid_values(self):
        """Test all valid gunicorn log level values in different cases."""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']

        for level in valid_levels:
            os.environ['GUNICORN_LOG_LEVEL'] = level
            settings = reload_settings()
            assert settings.gunicorn_log_level == level

            os.environ['GUNICORN_LOG_LEVEL'] = level.upper()
            settings = reload_settings()
            assert settings.gunicorn_log_level == level

            os.environ['GUNICORN_LOG_LEVEL'] = level.capitalize()
            settings = reload_settings()
            assert settings.gunicorn_log_level == level

    def test_gunicorn_log_level_invalid_value(self):
        """Test that invalid gunicorn log levels raise ValidationError."""
        os.environ['GUNICORN_LOG_LEVEL'] = 'INVALID'
        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert 'gunicorn_log_level' in str(exc_info.value).lower()

    def test_gunicorn_log_level_default(self):
        """Test that default gunicorn log level is info when not set."""
        if 'GUNICORN_LOG_LEVEL' in os.environ:
            del os.environ['GUNICORN_LOG_LEVEL']
        settings = reload_settings()
        assert settings.gunicorn_log_level == 'info'


class TestSettingsIntegration:
    """Integration tests for Settings with case-insensitive validators."""

    def test_both_log_levels_different_cases(self):
        """Test that both log level fields can be set with different cases."""
        os.environ['LOG_LEVEL'] = 'debug'
        os.environ['GUNICORN_LOG_LEVEL'] = 'WARNING'
        settings = reload_settings()

        assert settings.log_level == 'DEBUG'
        assert settings.gunicorn_log_level == 'warning'

    def test_production_scenario(self):
        """Test the production scenario that caused the original bug."""
        os.environ['LOG_LEVEL'] = 'info'  # lowercase as it was in production

        settings = reload_settings()
        assert settings.log_level == 'INFO'

    def teardown_method(self):
        """Clean up environment variables after each test."""
        for key in ['LOG_LEVEL', 'GUNICORN_LOG_LEVEL']:
            if key in os.environ:
                del os.environ[key]
