import pytest
import os
from src.utils.env_schema_validator import validate_environment, REQUIRED_ENV_VARS, OPTIONAL_ENV_VARS


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment for testing"""
    for var in list(REQUIRED_ENV_VARS.keys()) + list(OPTIONAL_ENV_VARS.keys()):
        monkeypatch.delenv(var, raising=False)


def test_validate_environment_with_all_required_vars(monkeypatch):
    """Test validation passes when all required vars are set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')
    
    result = validate_environment()
    
    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert len(result['warnings']) == 0


def test_validate_environment_missing_required_var(clean_env, monkeypatch):
    """Test validation fails when required var is missing"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    
    result = validate_environment()
    
    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'APP_VERSION' in result['errors'][0]


def test_validate_environment_all_missing(clean_env):
    """Test validation fails when all required vars are missing"""
    result = validate_environment()
    
    assert result['valid'] is False
    assert len(result['errors']) == 2


def test_validate_environment_with_optional_vars(monkeypatch):
    """Test validation passes with optional vars set"""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    monkeypatch.setenv('APP_VERSION', '1.0.0')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test123')
    
    result = validate_environment()
    
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_environment_empty_required_var(clean_env, monkeypatch):
    """Test validation fails when required var is empty string"""
    monkeypatch.setenv('DATABASE_URL', '')
    monkeypatch.setenv('APP_VERSION', '1.0.0')
    
    result = validate_environment()
    
    assert result['valid'] is False
    assert len(result['errors']) == 1
    assert 'DATABASE_URL' in result['errors'][0]


def test_required_env_vars_constant():
    """Test REQUIRED_ENV_VARS constant is defined"""
    assert 'DATABASE_URL' in REQUIRED_ENV_VARS
    assert 'APP_VERSION' in REQUIRED_ENV_VARS


def test_optional_env_vars_constant():
    """Test OPTIONAL_ENV_VARS constant is defined"""
    assert 'REDIS_URL' in OPTIONAL_ENV_VARS
    assert 'OPENAI_API_KEY' in OPTIONAL_ENV_VARS
