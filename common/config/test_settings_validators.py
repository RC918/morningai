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


class TestProviderHealthWeightsValidator:
    """Test soft validation for provider health scoring weights (EPIC I-2, #3352)."""

    def teardown_method(self):
        """Clean up environment variables after each test."""
        for key in [
            'PROVIDER_HEALTH_LATENCY_WEIGHT',
            'PROVIDER_HEALTH_ERROR_WEIGHT',
            'PROVIDER_HEALTH_DRIFT_WEIGHT'
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_default_weights_sum_to_one(self):
        """Test that default weights (0.3, 0.4, 0.3) sum to 1.0."""
        settings = reload_settings()
        weights_sum = (
            settings.provider_health_latency_weight +
            settings.provider_health_error_weight +
            settings.provider_health_drift_weight
        )
        assert abs(weights_sum - 1.0) < 0.001

    def test_valid_weights_no_normalization(self):
        """Test that valid weights summing to 1.0 are not modified."""
        os.environ['PROVIDER_HEALTH_LATENCY_WEIGHT'] = '0.2'
        os.environ['PROVIDER_HEALTH_ERROR_WEIGHT'] = '0.5'
        os.environ['PROVIDER_HEALTH_DRIFT_WEIGHT'] = '0.3'
        settings = reload_settings()

        assert abs(settings.provider_health_latency_weight - 0.2) < 0.001
        assert abs(settings.provider_health_error_weight - 0.5) < 0.001
        assert abs(settings.provider_health_drift_weight - 0.3) < 0.001

    def test_weights_exceeding_one_normalized(self):
        """Test that weights summing to >1.0 are normalized with warning."""
        os.environ['PROVIDER_HEALTH_LATENCY_WEIGHT'] = '0.5'
        os.environ['PROVIDER_HEALTH_ERROR_WEIGHT'] = '0.5'
        os.environ['PROVIDER_HEALTH_DRIFT_WEIGHT'] = '0.5'

        with pytest.warns(UserWarning, match="weights sum to 1.500"):
            settings = reload_settings()

        weights_sum = (
            settings.provider_health_latency_weight +
            settings.provider_health_error_weight +
            settings.provider_health_drift_weight
        )
        assert abs(weights_sum - 1.0) < 0.001
        assert abs(settings.provider_health_latency_weight - 1 / 3) < 0.001

    def test_weights_below_one_normalized(self):
        """Test that weights summing to <1.0 are normalized with warning."""
        os.environ['PROVIDER_HEALTH_LATENCY_WEIGHT'] = '0.1'
        os.environ['PROVIDER_HEALTH_ERROR_WEIGHT'] = '0.2'
        os.environ['PROVIDER_HEALTH_DRIFT_WEIGHT'] = '0.2'

        with pytest.warns(UserWarning, match="weights sum to 0.500"):
            settings = reload_settings()

        weights_sum = (
            settings.provider_health_latency_weight +
            settings.provider_health_error_weight +
            settings.provider_health_drift_weight
        )
        assert abs(weights_sum - 1.0) < 0.001
        assert abs(settings.provider_health_latency_weight - 0.2) < 0.001
        assert abs(settings.provider_health_error_weight - 0.4) < 0.001
        assert abs(settings.provider_health_drift_weight - 0.4) < 0.001

    def test_normalization_preserves_relative_weights(self):
        """Test that normalization preserves relative weight proportions."""
        os.environ['PROVIDER_HEALTH_LATENCY_WEIGHT'] = '0.4'
        os.environ['PROVIDER_HEALTH_ERROR_WEIGHT'] = '0.8'
        os.environ['PROVIDER_HEALTH_DRIFT_WEIGHT'] = '0.8'

        with pytest.warns(UserWarning, match="weights sum to 2.000"):
            settings = reload_settings()

        latency = settings.provider_health_latency_weight
        error = settings.provider_health_error_weight
        drift = settings.provider_health_drift_weight

        assert abs(error / latency - 2.0) < 0.001
        assert abs(drift / latency - 2.0) < 0.001

    def test_zero_weights_no_division_error(self):
        """Test that all-zero weights don't cause division by zero."""
        os.environ['PROVIDER_HEALTH_LATENCY_WEIGHT'] = '0.0'
        os.environ['PROVIDER_HEALTH_ERROR_WEIGHT'] = '0.0'
        os.environ['PROVIDER_HEALTH_DRIFT_WEIGHT'] = '0.0'

        with pytest.warns(UserWarning, match="weights sum to 0.000"):
            settings = reload_settings()

        assert settings.provider_health_latency_weight == 0.0
        assert settings.provider_health_error_weight == 0.0
        assert settings.provider_health_drift_weight == 0.0
