"""
Tests for env_schema_validator utility.

Tests cover:
- validate_environment function
- Required environment variable validation
- Optional environment variable validation
"""

import pytest
from unittest.mock import patch
import os


class TestValidateEnvironment:
    """Test validate_environment function"""
    
    def test_validate_with_all_required_vars(self, monkeypatch):
        """Should pass validation when all required vars present"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        
        result = validate_environment()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_with_missing_required_var(self, monkeypatch):
        """Should fail validation when required var missing"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.delenv('APP_VERSION', raising=False)
        
        result = validate_environment()
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert any('APP_VERSION' in error for error in result['errors'])
    
    def test_validate_with_all_missing_required_vars(self, monkeypatch):
        """Should fail validation when all required vars missing"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.delenv('APP_VERSION', raising=False)
        
        result = validate_environment()
        
        assert result['valid'] is False
        assert len(result['errors']) == 2
    
    def test_validate_with_optional_vars(self, monkeypatch):
        """Should pass validation with optional vars present"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('OPENAI_API_KEY', 'sk-test123')
        
        result = validate_environment()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_without_optional_vars(self, monkeypatch):
        """Should pass validation without optional vars"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        monkeypatch.delenv('REDIS_URL', raising=False)
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        
        result = validate_environment()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_returns_warnings_list(self, monkeypatch):
        """Should return warnings list in result"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        
        result = validate_environment()
        
        assert 'warnings' in result
        assert isinstance(result['warnings'], list)
    
    def test_validate_result_structure(self, monkeypatch):
        """Should return result with correct structure"""
        from utils.env_schema_validator import validate_environment
        
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/db')
        monkeypatch.setenv('APP_VERSION', '1.0.0')
        
        result = validate_environment()
        
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert isinstance(result['valid'], bool)
        assert isinstance(result['errors'], list)
        assert isinstance(result['warnings'], list)


class TestRequiredEnvVars:
    """Test REQUIRED_ENV_VARS constant"""
    
    def test_has_database_url(self):
        """Should require DATABASE_URL"""
        from utils.env_schema_validator import REQUIRED_ENV_VARS
        
        assert 'DATABASE_URL' in REQUIRED_ENV_VARS
        assert REQUIRED_ENV_VARS['DATABASE_URL'] == str
    
    def test_has_app_version(self):
        """Should require APP_VERSION"""
        from utils.env_schema_validator import REQUIRED_ENV_VARS
        
        assert 'APP_VERSION' in REQUIRED_ENV_VARS
        assert REQUIRED_ENV_VARS['APP_VERSION'] == str


class TestOptionalEnvVars:
    """Test OPTIONAL_ENV_VARS constant"""
    
    def test_has_redis_url(self):
        """Should have REDIS_URL as optional"""
        from utils.env_schema_validator import OPTIONAL_ENV_VARS
        
        assert 'REDIS_URL' in OPTIONAL_ENV_VARS
        assert OPTIONAL_ENV_VARS['REDIS_URL'] == str
    
    def test_has_openai_api_key(self):
        """Should have OPENAI_API_KEY as optional"""
        from utils.env_schema_validator import OPTIONAL_ENV_VARS
        
        assert 'OPENAI_API_KEY' in OPTIONAL_ENV_VARS
        assert OPTIONAL_ENV_VARS['OPENAI_API_KEY'] == str
    
    def test_has_sentry_dsn(self):
        """Should have SENTRY_DSN as optional"""
        from utils.env_schema_validator import OPTIONAL_ENV_VARS
        
        assert 'SENTRY_DSN' in OPTIONAL_ENV_VARS
    
    def test_has_flask_env(self):
        """Should have FLASK_ENV as optional"""
        from utils.env_schema_validator import OPTIONAL_ENV_VARS
        
        assert 'FLASK_ENV' in OPTIONAL_ENV_VARS
    
    def test_has_cors_origins(self):
        """Should have CORS_ORIGINS as optional"""
        from utils.env_schema_validator import OPTIONAL_ENV_VARS
        
        assert 'CORS_ORIGINS' in OPTIONAL_ENV_VARS
