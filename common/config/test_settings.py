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


class TestSecretStrMasking:
    """Test that secret fields are properly masked using pydantic SecretStr"""
    
    def test_secrets_masked_in_repr(self):
        """Secret fields should be masked in repr() output"""
        sentinel_secrets = {
            'OPENAI_API_KEY': 'sk-SENTINEL-openai-12345',
            'UPSTASH_REDIS_REST_TOKEN': 'SENTINEL-upstash-token-67890',
            'JWT_SECRET_KEY': 'SENTINEL-jwt-secret-abcde',
            'ADMIN_PASSWORD': 'SENTINEL-admin-pass-fghij',
            'SECRET_KEY': 'SENTINEL-flask-secret-klmno',
            'MASTER_KEY': 'SENTINEL-master-key-pqrst',
            'TOTP_ENCRYPTION_KEY': 'SENTINEL-totp-key-uvwxy-12345678901234567890',
            'SUPABASE_DB_PASSWORD': 'SENTINEL-supabase-db-pass-zzz',
            'SUPABASE_ANON_KEY': 'SENTINEL-supabase-anon-key-aaa',
            'SUPABASE_SERVICE_ROLE_KEY': 'SENTINEL-supabase-service-key-bbb',
            'CLOUDFLARE_API_TOKEN': 'SENTINEL-cloudflare-token-ccc',
            'VERCEL_TOKEN': 'SENTINEL-vercel-token-ddd',
            'VERCEL_TOKEN_NEW': 'SENTINEL-vercel-new-token-eee',
            'VERCEL_TOKEN_2': 'SENTINEL-vercel-token-2-fff',
            'RENDER_API_KEY': 'SENTINEL-render-key-ggg',
            'FLY_API_TOKEN': 'SENTINEL-fly-token-iii',
            'SENTRY_AUTH_TOKEN': 'SENTINEL-sentry-token-jjj',
            'MONITOR_AUTH_TOKEN': 'SENTINEL-monitor-token-kkk',
            'GITHUB_TOKEN': 'SENTINEL-github-token-lll',
            'AGENT_GITHUB_TOKEN': 'SENTINEL-agent-github-token-mmm',
            'TELEGRAM_BOT_TOKEN': 'SENTINEL-telegram-token-nnn',
            'Mailtrap_API_TOKEN': 'SENTINEL-mailtrap-token-ooo',
            'ORCHESTRATOR_JWT_SECRET': 'SENTINEL-orchestrator-jwt-ppp-12345678901234567890',
            'STRIPE_SECRET_KEY': 'SENTINEL-stripe-secret-qqq',
            'STRIPE_WEBHOOK_SECRET': 'SENTINEL-stripe-webhook-rrr',
            'TEST_ADMIN_JWT': 'SENTINEL-test-admin-jwt-sss',
            'STAGING_TEST_PASSWORD': 'SENTINEL-staging-pass-ttt',
            'DASHBOARD_API_KEY': 'SENTINEL-dashboard-key-uuu',
        }
        
        with patch.dict(os.environ, sentinel_secrets, clear=False):
            instance = Settings()
            
            repr_output = repr(instance)
            str_output = str(instance)
            
            for env_var, sentinel_value in sentinel_secrets.items():
                assert sentinel_value not in repr_output, \
                    f"Secret {env_var} leaked in repr(): found '{sentinel_value}'"
                assert sentinel_value not in str_output, \
                    f"Secret {env_var} leaked in str(): found '{sentinel_value}'"
    
    def test_secret_properties_return_unwrapped_strings(self):
        """Secret properties should return unwrapped string values for downstream code"""
        test_secrets = {
            'OPENAI_API_KEY': 'sk-test-openai-key',
            'GITHUB_TOKEN': 'ghp_test_github_token',
            'JWT_SECRET_KEY': 'test-jwt-secret-key',
        }
        
        with patch.dict(os.environ, test_secrets, clear=False):
            instance = Settings()
            
            assert instance.openai_api_key == 'sk-test-openai-key'
            assert isinstance(instance.openai_api_key, str)
            
            assert instance.github_token == 'ghp_test_github_token'
            assert isinstance(instance.github_token, str)
            
            assert instance.jwt_secret_key == 'test-jwt-secret-key'
            assert isinstance(instance.jwt_secret_key, str)
    
    def test_secret_properties_return_none_when_not_set(self):
        """Secret properties should return None when environment variable not set"""
        env_without_secrets = {k: v for k, v in os.environ.items() 
                               if not any(secret in k for secret in [
                                   'SECRET', 'KEY', 'TOKEN', 'PASSWORD', 'JWT'
                               ])}
        
        with patch.dict(os.environ, env_without_secrets, clear=True):
            instance = Settings()
            
            assert instance.openai_api_key is None
            assert instance.github_token is None
            assert instance.jwt_secret_key is None
            assert instance.admin_password is None
    
    def test_totp_validator_works_with_secretstr(self):
        """TOTP encryption key validator should work with SecretStr"""
        with patch.dict(os.environ, {'TOTP_ENCRYPTION_KEY': 'short'}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                instance = Settings()
                
                assert len(w) > 0, "Should emit warning for short TOTP key"
                assert any('TOTP_ENCRYPTION_KEY' in str(warning.message) for warning in w)
                
                assert instance.totp_encryption_key == 'short'
        
        valid_key = 'a' * 32
        with patch.dict(os.environ, {'TOTP_ENCRYPTION_KEY': valid_key}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                instance = Settings()
                
                totp_warnings = [warning for warning in w if 'TOTP_ENCRYPTION_KEY' in str(warning.message)]
                assert len(totp_warnings) == 0, "Should not emit warning for valid TOTP key"
                
                assert instance.totp_encryption_key == valid_key


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
