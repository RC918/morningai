"""
Unit tests for PR4 Settings Unification (#2379).

Tests cover:
1. Boolean parsing for feature flags ('true', 'True', '1', 'false', 'False', '0', empty string)
2. Default fallback behavior for missing/empty values
3. Feature flag combinations (2FA, mock users, rate limit, CORS debug)
4. model_fields_set behavior for conditional config setting

These tests validate the contract between environment variables and settings behavior
after the os.getenv() to settings.* migration.
"""

import os
import pytest
from unittest.mock import patch

from common.config.settings import Settings, reload_settings, get_settings


class TestBooleanParsing:
    """Test boolean field parsing for various string representations."""

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ])
    def test_cors_debug_boolean_parsing(self, env_value, expected):
        """CORS_DEBUG should accept various boolean string representations."""
        with patch.dict(os.environ, {'CORS_DEBUG': env_value}, clear=False):
            instance = Settings()
            assert instance.cors_debug is expected, \
                f"CORS_DEBUG='{env_value}' should be {expected}"

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ])
    def test_testing_boolean_parsing(self, env_value, expected):
        """TESTING should accept various boolean string representations."""
        with patch.dict(os.environ, {'TESTING': env_value}, clear=False):
            instance = Settings()
            assert instance.testing is expected, \
                f"TESTING='{env_value}' should be {expected}"

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ])
    def test_enable_rate_limit_in_tests_boolean_parsing(self, env_value, expected):
        """ENABLE_RATE_LIMIT_IN_TESTS should accept various boolean string representations."""
        with patch.dict(os.environ, {'ENABLE_RATE_LIMIT_IN_TESTS': env_value}, clear=False):
            instance = Settings()
            assert instance.enable_rate_limit_in_tests is expected, \
                f"ENABLE_RATE_LIMIT_IN_TESTS='{env_value}' should be {expected}"

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ])
    def test_feature_2fa_enabled_boolean_parsing(self, env_value, expected):
        """FEATURE_2FA_ENABLED should accept various boolean string representations."""
        with patch.dict(os.environ, {'FEATURE_2FA_ENABLED': env_value}, clear=False):
            instance = Settings()
            assert instance.feature_2fa_enabled is expected, \
                f"FEATURE_2FA_ENABLED='{env_value}' should be {expected}"

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("0", False),
    ])
    def test_force_enable_2fa_in_tests_boolean_parsing(self, env_value, expected):
        """FORCE_ENABLE_2FA_IN_TESTS should accept various boolean string representations."""
        with patch.dict(os.environ, {'FORCE_ENABLE_2FA_IN_TESTS': env_value}, clear=False):
            instance = Settings()
            assert instance.force_enable_2fa_in_tests is expected, \
                f"FORCE_ENABLE_2FA_IN_TESTS='{env_value}' should be {expected}"


class TestDefaultFallbackBehavior:
    """Test default values when environment variables are not set."""

    def test_cors_debug_defaults_to_false(self):
        """CORS_DEBUG should default to False when not set."""
        env_without_cors_debug = {k: v for k, v in os.environ.items() if k != 'CORS_DEBUG'}
        with patch.dict(os.environ, env_without_cors_debug, clear=True):
            instance = Settings()
            assert instance.cors_debug is False

    def test_testing_defaults_to_false(self):
        """TESTING should default to False when not set."""
        env_without_testing = {k: v for k, v in os.environ.items() if k != 'TESTING'}
        with patch.dict(os.environ, env_without_testing, clear=True):
            instance = Settings()
            assert instance.testing is False

    def test_enable_mock_users_defaults_to_false(self):
        """ENABLE_MOCK_USERS should default to False when not set."""
        env_without_mock = {k: v for k, v in os.environ.items() if k != 'ENABLE_MOCK_USERS'}
        with patch.dict(os.environ, env_without_mock, clear=True):
            instance = Settings()
            assert instance.enable_mock_users is False

    def test_enable_rate_limit_in_tests_defaults_to_false(self):
        """ENABLE_RATE_LIMIT_IN_TESTS should default to False when not set."""
        env_without_rate_limit = {
            k: v for k, v in os.environ.items() if k != 'ENABLE_RATE_LIMIT_IN_TESTS'
        }
        with patch.dict(os.environ, env_without_rate_limit, clear=True):
            instance = Settings()
            assert instance.enable_rate_limit_in_tests is False

    def test_rate_limit_requests_defaults_to_60(self):
        """RATE_LIMIT_REQUESTS should default to 60 when not set."""
        env_without_rate_limit = {
            k: v for k, v in os.environ.items() if k != 'RATE_LIMIT_REQUESTS'
        }
        with patch.dict(os.environ, env_without_rate_limit, clear=True):
            instance = Settings()
            assert instance.rate_limit_requests == 60

    def test_feature_2fa_enabled_defaults_to_true(self):
        """FEATURE_2FA_ENABLED should default to True when not set."""
        env_without_2fa = {k: v for k, v in os.environ.items() if k != 'FEATURE_2FA_ENABLED'}
        with patch.dict(os.environ, env_without_2fa, clear=True):
            instance = Settings()
            assert instance.feature_2fa_enabled is True

    def test_force_enable_2fa_in_tests_defaults_to_false(self):
        """FORCE_ENABLE_2FA_IN_TESTS should default to False when not set."""
        env_without_force = {k: v for k, v in os.environ.items() 
                             if k != 'FORCE_ENABLE_2FA_IN_TESTS'}
        with patch.dict(os.environ, env_without_force, clear=True):
            instance = Settings()
            assert instance.force_enable_2fa_in_tests is False

    def test_github_repo_defaults_to_rc918_morningai(self):
        """GITHUB_REPO should default to 'RC918/morningai' when not set."""
        env_without_repo = {k: v for k, v in os.environ.items() if k != 'GITHUB_REPO'}
        with patch.dict(os.environ, env_without_repo, clear=True):
            instance = Settings()
            assert instance.github_repo == 'RC918/morningai'


class TestModelFieldsSet:
    """Test model_fields_set behavior for conditional config setting."""

    def test_rate_limit_requests_in_fields_set_when_provided(self):
        """rate_limit_requests should be in model_fields_set when explicitly set."""
        with patch.dict(os.environ, {'RATE_LIMIT_REQUESTS': '100'}, clear=False):
            instance = Settings()
            assert 'rate_limit_requests' in instance.model_fields_set
            assert instance.rate_limit_requests == 100

    def test_rate_limit_requests_not_in_fields_set_when_default(self):
        """rate_limit_requests should NOT be in model_fields_set when using default."""
        env_without_rate_limit = {
            k: v for k, v in os.environ.items() if k != 'RATE_LIMIT_REQUESTS'
        }
        with patch.dict(os.environ, env_without_rate_limit, clear=True):
            instance = Settings()
            assert 'rate_limit_requests' not in instance.model_fields_set
            assert instance.rate_limit_requests == 60

    def test_cors_debug_in_fields_set_when_provided(self):
        """cors_debug should be in model_fields_set when explicitly set."""
        with patch.dict(os.environ, {'CORS_DEBUG': 'true'}, clear=False):
            instance = Settings()
            assert 'cors_debug' in instance.model_fields_set
            assert instance.cors_debug is True

    def test_testing_in_fields_set_when_provided(self):
        """testing should be in model_fields_set when explicitly set."""
        with patch.dict(os.environ, {'TESTING': 'true'}, clear=False):
            instance = Settings()
            assert 'testing' in instance.model_fields_set
            assert instance.testing is True

    def test_enable_mock_users_in_fields_set_when_provided(self):
        """enable_mock_users should be in model_fields_set when explicitly set."""
        with patch.dict(os.environ, {
            'ENABLE_MOCK_USERS': 'true',
            'ENVIRONMENT': 'development'
        }, clear=False):
            instance = Settings()
            assert 'enable_mock_users' in instance.model_fields_set
            assert instance.enable_mock_users is True

    def test_enable_mock_users_not_in_fields_set_when_default(self):
        """enable_mock_users should NOT be in model_fields_set when using default.
        
        This is critical for test mode behavior: auth_service.is_mock_users_enabled()
        checks if 'ENABLE_MOCK_USERS' key exists in Flask config. If the key doesn't
        exist, test mode defaults to True. We preserve this by only setting the
        Flask config key when the env var is explicitly provided.
        """
        env_without_mock = {
            k: v for k, v in os.environ.items() if k != 'ENABLE_MOCK_USERS'
        }
        with patch.dict(os.environ, env_without_mock, clear=True):
            instance = Settings()
            assert 'enable_mock_users' not in instance.model_fields_set
            assert instance.enable_mock_users is False


class TestFeatureFlagCombinations:
    """Test feature flag combinations for 2FA, mock users, and rate limiting."""

    def test_2fa_disabled_in_test_mode_by_default(self):
        """2FA should be effectively disabled in test mode unless forced."""
        with patch.dict(os.environ, {
            'TESTING': 'true',
            'FEATURE_2FA_ENABLED': 'true',
            'FORCE_ENABLE_2FA_IN_TESTS': 'false'
        }, clear=False):
            instance = Settings()
            assert instance.testing is True
            assert instance.feature_2fa_enabled is True
            assert instance.force_enable_2fa_in_tests is False

    def test_2fa_enabled_in_test_mode_when_forced(self):
        """2FA should be enabled in test mode when FORCE_ENABLE_2FA_IN_TESTS is true."""
        with patch.dict(os.environ, {
            'TESTING': 'true',
            'FEATURE_2FA_ENABLED': 'true',
            'FORCE_ENABLE_2FA_IN_TESTS': 'true'
        }, clear=False):
            instance = Settings()
            assert instance.testing is True
            assert instance.feature_2fa_enabled is True
            assert instance.force_enable_2fa_in_tests is True

    def test_rate_limit_disabled_in_tests_by_default(self):
        """Rate limiting should be disabled in test mode by default."""
        with patch.dict(os.environ, {
            'TESTING': 'true',
            'ENABLE_RATE_LIMIT_IN_TESTS': 'false'
        }, clear=False):
            instance = Settings()
            assert instance.testing is True
            assert instance.enable_rate_limit_in_tests is False

    def test_rate_limit_enabled_in_tests_when_configured(self):
        """Rate limiting should be enabled in test mode when configured."""
        with patch.dict(os.environ, {
            'TESTING': 'true',
            'ENABLE_RATE_LIMIT_IN_TESTS': 'true',
            'RATE_LIMIT_REQUESTS': '30'
        }, clear=False):
            instance = Settings()
            assert instance.testing is True
            assert instance.enable_rate_limit_in_tests is True
            assert instance.rate_limit_requests == 30

    def test_mock_users_with_testing_mode(self):
        """Mock users can be enabled alongside testing mode in development."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'TESTING': 'true',
            'ENABLE_MOCK_USERS': 'true'
        }, clear=False):
            instance = Settings()
            assert instance.testing is True
            assert instance.enable_mock_users is True

    def test_cors_debug_only_effective_in_non_production(self):
        """CORS_DEBUG should be settable but only effective in non-production."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'CORS_DEBUG': 'true'
        }, clear=False):
            instance = Settings()
            assert instance.cors_debug is True
            assert instance.is_production is False


class TestGitHubSettings:
    """Test GitHub-related settings."""

    def test_github_repo_can_be_overridden(self):
        """GITHUB_REPO should be overridable via environment variable."""
        with patch.dict(os.environ, {'GITHUB_REPO': 'custom/repo'}, clear=False):
            instance = Settings()
            assert instance.github_repo == 'custom/repo'

    def test_github_token_returns_string_when_set(self):
        """github_token property should return string value when set."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_test_token_123'}, clear=False):
            instance = Settings()
            token = instance.github_token
            assert token == 'ghp_test_token_123'
            assert isinstance(token, str)

    def test_github_token_returns_none_when_not_set(self):
        """github_token property should return None when not set."""
        env_without_token = {k: v for k, v in os.environ.items() if k != 'GITHUB_TOKEN'}
        with patch.dict(os.environ, env_without_token, clear=True):
            instance = Settings()
            assert instance.github_token is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
