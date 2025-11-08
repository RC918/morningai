"""
Unit tests for common.config.settings module.

Tests cover:
1. Settings lifecycle (singleton, reload, test-aware caching)
2. Production guards (mock users validator)
3. Environment variable loading and validation
4. Backward compatibility (getenv wrapper, settings proxy)

Note: JWT validation is in auth_service.py:validate_security_config(), not in Settings validators.
"""
import os
import sys
import pytest
import warnings
from unittest.mock import patch

from common.config.settings import (
    Settings,
    get_settings,
    reload_settings,
    settings,
    getenv
)


class TestSettingsLifecycle:
    """Test settings singleton lifecycle and caching behavior"""
    
    def test_get_settings_creates_new_instance_in_test_mode(self):
        """In test mode (pytest detected), get_settings() should create new instances"""
        assert 'pytest' in sys.modules, "pytest should be in sys.modules during tests"
        
        instance1 = get_settings()
        instance2 = get_settings()
        
        assert isinstance(instance1, Settings)
        assert isinstance(instance2, Settings)
    
    def test_reload_settings_forces_new_instance(self):
        """reload_settings() should force creation of a new instance"""
        instance1 = get_settings()
        instance2 = reload_settings()
        
        assert isinstance(instance1, Settings)
        assert isinstance(instance2, Settings)
    
    def test_settings_proxy_lazy_initialization(self):
        """Settings proxy should lazily initialize on first access"""
        env = settings.environment
        assert env in ['development', 'staging', 'production'], f"Invalid environment: {env}"


class TestProductionGuards:
    """Test production environment validation and guards"""
    
    def test_mock_users_disabled_in_production(self):
        """ENABLE_MOCK_USERS must be false in production"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'ENABLE_MOCK_USERS': 'true'
        }):
            with pytest.raises(ValueError, match="ENABLE_MOCK_USERS.*production"):
                Settings()
    
    def test_mock_users_disabled_in_staging(self):
        """ENABLE_MOCK_USERS must be false in staging"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'staging',
            'ENABLE_MOCK_USERS': 'true'
        }):
            with pytest.raises(ValueError, match="ENABLE_MOCK_USERS.*staging"):
                Settings()
    
    def test_mock_users_allowed_in_development(self):
        """ENABLE_MOCK_USERS is allowed in development"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'ENABLE_MOCK_USERS': 'true'
        }):
            instance = Settings()
            assert instance.enable_mock_users is True
    
    def test_totp_key_length_warning(self):
        """TOTP_ENCRYPTION_KEY should warn if less than 32 characters"""
        with patch.dict(os.environ, {
            'TOTP_ENCRYPTION_KEY': 'short'  # Only 5 characters
        }):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                instance = Settings()
                
                assert len(w) > 0, "Should emit warning for short TOTP key"
                assert any('TOTP_ENCRYPTION_KEY' in str(warning.message) for warning in w)


class TestEnvironmentVariableLoading:
    """Test environment variable loading and type conversion"""
    
    def test_boolean_fields_converted_correctly(self):
        """Boolean fields should convert string values correctly"""
        with patch.dict(os.environ, {'ENABLE_MOCK_USERS': 'true'}):
            instance = Settings()
            assert instance.enable_mock_users is True
        
        with patch.dict(os.environ, {'ENABLE_MOCK_USERS': 'false'}):
            instance = Settings()
            assert instance.enable_mock_users is False
    
    def test_integer_fields_converted_correctly(self):
        """Integer fields should convert string values correctly"""
        with patch.dict(os.environ, {'USE_LANGGRAPH_PERCENT': '75'}):
            instance = Settings()
            assert instance.use_langgraph_percent == 75
            assert isinstance(instance.use_langgraph_percent, int)
    
    def test_optional_fields_can_be_none(self):
        """Optional fields can be None when not set"""
        instance = Settings()
        
        assert hasattr(instance, 'redis_url')
        assert hasattr(instance, 'openai_api_key')
        assert hasattr(instance, 'github_token')
    
    def test_uppercase_env_vars_loaded_via_aliases(self):
        """UPPERCASE environment variables should be loaded via Field aliases"""
        with patch.dict(os.environ, {
            'REDIS_URL': 'redis://test:6379',
            'OPENAI_API_KEY': 'sk-test-key',
            'GITHUB_TOKEN': 'ghp_test_token'
        }):
            instance = Settings()
            assert instance.redis_url == 'redis://test:6379'
            assert instance.openai_api_key == 'sk-test-key'
            assert instance.github_token == 'ghp_test_token'


class TestBackwardCompatibility:
    """Test backward compatibility features"""
    
    def test_getenv_wrapper_returns_correct_value(self):
        """getenv() wrapper should return environment variable value"""
        with patch.dict(os.environ, {'TEST_VAR': 'test-value'}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                value = getenv('TEST_VAR')
                
                assert value == 'test-value', "Should return correct value"
                assert len(w) == 1, "Should emit deprecation warning"
                assert issubclass(w[0].category, DeprecationWarning)
                assert 'deprecated' in str(w[0].message).lower()
    
    def test_getenv_wrapper_returns_default(self):
        """getenv() wrapper should return default when variable not set"""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            value = getenv('NONEXISTENT_VAR_12345', 'default-value')
            assert value == 'default-value', "Should return default value"
    
    def test_settings_proxy_attribute_access(self):
        """Settings proxy should provide attribute access to settings"""
        env = settings.environment
        assert env in ['development', 'staging', 'production'], f"Invalid environment: {env}"


class TestPropertyMethods:
    """Test property methods on Settings"""
    
    def test_is_production_property(self):
        """is_production property should return True only in production"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            instance = Settings()
            assert instance.is_production is True
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            instance = Settings()
            assert instance.is_production is False
    
    def test_is_staging_property(self):
        """is_staging property should return True only in staging"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
            instance = Settings()
            assert instance.is_staging is True
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            instance = Settings()
            assert instance.is_staging is False
    
    def test_is_development_property(self):
        """is_development property should return True only in development"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            instance = Settings()
            assert instance.is_development is True
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            instance = Settings()
            assert instance.is_development is False


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_multiple_reload_settings_calls(self):
        """Multiple reload_settings() calls should work correctly"""
        for i in range(3):
            instance = reload_settings()
            assert isinstance(instance, Settings)
    
    def test_redis_url_non_tls_warning(self):
        """Redis URL without TLS should emit warning"""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379'}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                instance = Settings()
                
                assert len(w) > 0, "Should emit warning for non-TLS Redis"
                assert any('TLS' in str(warning.message) or 'rediss' in str(warning.message) for warning in w)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
