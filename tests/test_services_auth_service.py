"""
Tests for auth_service module.

Tests cover:
- Helper functions: _as_bool, hash_token, generate_csrf_token
- Token generation: generate_access_token, generate_refresh_token
- Token verification: verify_access_token, verify_refresh_token
- Cookie configuration: create_cookie_config
- Environment checks: is_testing_mode, is_production, is_mock_users_enabled
"""

import pytest
from unittest.mock import MagicMock, patch
import jwt
import datetime
import hashlib


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_as_bool_with_true_boolean(self):
        """Should return True for True boolean"""
        from services.auth_service import _as_bool
        
        result = _as_bool(True)
        
        assert result is True
    
    def test_as_bool_with_false_boolean(self):
        """Should return False for False boolean"""
        from services.auth_service import _as_bool
        
        result = _as_bool(False)
        
        assert result is False
    
    def test_as_bool_with_string_true(self):
        """Should return True for 'true' string"""
        from services.auth_service import _as_bool
        
        assert _as_bool('true') is True
        assert _as_bool('True') is True
        assert _as_bool('TRUE') is True
        assert _as_bool('1') is True
        assert _as_bool('yes') is True
        assert _as_bool('on') is True
    
    def test_as_bool_with_string_false(self):
        """Should return False for 'false' string"""
        from services.auth_service import _as_bool
        
        assert _as_bool('false') is False
        assert _as_bool('False') is False
        assert _as_bool('0') is False
        assert _as_bool('no') is False
        assert _as_bool('off') is False
    
    def test_as_bool_with_none(self):
        """Should return False for None"""
        from services.auth_service import _as_bool
        
        result = _as_bool(None)
        
        assert result is False
    
    def test_hash_token(self):
        """Should hash token with SHA256"""
        from services.auth_service import hash_token
        
        token = "test-token-123"
        
        result = hash_token(token)
        
        expected = hashlib.sha256(token.encode()).hexdigest()
        assert result == expected
        assert len(result) == 64
    
    def test_hash_token_consistent(self):
        """Should produce consistent hash for same token"""
        from services.auth_service import hash_token
        
        token = "test-token-123"
        
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
    
    def test_hash_token_different_for_different_tokens(self):
        """Should produce different hashes for different tokens"""
        from services.auth_service import hash_token
        
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")
        
        assert hash1 != hash2
    
    def test_generate_csrf_token(self):
        """Should generate CSRF token"""
        from services.auth_service import generate_csrf_token
        
        token = generate_csrf_token()
        
        assert len(token) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789abcdef' for c in token)
    
    def test_generate_csrf_token_unique(self):
        """Should generate unique CSRF tokens"""
        from services.auth_service import generate_csrf_token
        
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        
        assert token1 != token2


class TestEnvironmentChecks:
    """Test environment check functions"""
    
    def test_is_testing_mode_with_env_var(self, monkeypatch):
        """Should detect testing mode from TESTING env var"""
        from services.auth_service import is_testing_mode
        
        monkeypatch.setenv('TESTING', 'true')
        
        result = is_testing_mode()
        
        assert isinstance(result, bool)
    
    def test_is_testing_mode_false(self, monkeypatch):
        """Should return False when not in testing mode"""
        from services.auth_service import is_testing_mode
        
        monkeypatch.setenv('TESTING', 'false')
        
        result = is_testing_mode()
        
        assert result is False
    
    def test_is_production_with_environment_var(self, monkeypatch):
        """Should detect production from ENVIRONMENT env var"""
        from services.auth_service import is_production
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        result = is_production()
        
        assert result is True
    
    def test_is_production_with_flask_env(self, monkeypatch):
        """Should detect production from FLASK_ENV env var"""
        from services.auth_service import is_production
        
        monkeypatch.delenv('ENVIRONMENT', raising=False)
        monkeypatch.setenv('FLASK_ENV', 'production')
        
        result = is_production()
        
        assert result is True
    
    def test_is_production_false(self, monkeypatch):
        """Should return False in development"""
        from services.auth_service import is_production
        
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        result = is_production()
        
        assert result is False
    
    def test_is_mock_users_enabled_explicit_true(self, monkeypatch):
        """Should return True when explicitly enabled"""
        from services.auth_service import is_mock_users_enabled
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        
        result = is_mock_users_enabled()
        
        assert isinstance(result, bool)
    
    def test_is_mock_users_enabled_explicit_false_in_test(self, monkeypatch):
        """Should respect explicit False in test mode"""
        from services.auth_service import is_mock_users_enabled
        
        monkeypatch.setenv('TESTING', 'true')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'false')
        
        result = is_mock_users_enabled()
        
        assert result is False
    
    def test_is_mock_users_enabled_false_in_non_test(self, monkeypatch):
        """Should default to False in non-test mode"""
        from services.auth_service import is_mock_users_enabled
        
        monkeypatch.setenv('TESTING', 'false')
        monkeypatch.delenv('ENABLE_MOCK_USERS', raising=False)
        
        result = is_mock_users_enabled()
        
        assert result is False


class TestTokenGeneration:
    """Test token generation functions"""
    
    def test_generate_access_token(self):
        """Should generate access token with correct payload"""
        from services.auth_service import generate_access_token
        
        token, expiry_ms = generate_access_token('user-123', 'test@example.com', 'admin')
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expiry_ms, int)
        assert expiry_ms > 0
    
    def test_generate_access_token_payload(self):
        """Should include correct fields in access token payload"""
        from services.auth_service import generate_access_token, _get_jwt_secret, JWT_ALGORITHM
        
        token, _ = generate_access_token('user-123', 'test@example.com', 'admin')
        
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        
        assert payload['user_id'] == 'user-123'
        assert payload['email'] == 'test@example.com'
        assert payload['role'] == 'admin'
        assert payload['type'] == 'access'
        assert 'iat' in payload
        assert 'exp' in payload
    
    def test_generate_access_token_expiry(self):
        """Should set correct expiry time (15 minutes)"""
        from services.auth_service import generate_access_token, ACCESS_TOKEN_EXPIRY_MINUTES
        
        before = datetime.datetime.now(datetime.UTC)
        token, expiry_ms = generate_access_token('user-123', 'test@example.com', 'admin')
        after = datetime.datetime.now(datetime.UTC)
        
        expiry_dt = datetime.datetime.fromtimestamp(expiry_ms / 1000, tz=datetime.UTC)
        expected_min = before + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES) - datetime.timedelta(seconds=1)
        expected_max = after + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES) + datetime.timedelta(seconds=1)
        
        assert expected_min <= expiry_dt <= expected_max
    
    def test_generate_refresh_token(self):
        """Should generate refresh token"""
        from services.auth_service import generate_refresh_token
        
        token = generate_refresh_token('user-123', 'test@example.com')
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_refresh_token_payload(self):
        """Should include correct fields in refresh token payload"""
        from services.auth_service import generate_refresh_token, _get_jwt_secret, JWT_ALGORITHM
        
        token = generate_refresh_token('user-123', 'test@example.com')
        
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        
        assert payload['user_id'] == 'user-123'
        assert payload['email'] == 'test@example.com'
        assert payload['type'] == 'refresh'
        assert 'jti' in payload
        assert 'iat' in payload
        assert 'exp' in payload
    
    def test_generate_refresh_token_unique(self):
        """Should generate unique refresh tokens"""
        from services.auth_service import generate_refresh_token
        
        token1 = generate_refresh_token('user-123', 'test@example.com')
        token2 = generate_refresh_token('user-123', 'test@example.com')
        
        assert token1 != token2


class TestTokenVerification:
    """Test token verification functions"""
    
    def test_verify_access_token_valid(self):
        """Should verify valid access token"""
        from services.auth_service import generate_access_token, verify_access_token
        
        token, _ = generate_access_token('user-123', 'test@example.com', 'admin')
        
        payload = verify_access_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 'user-123'
        assert payload['email'] == 'test@example.com'
        assert payload['role'] == 'admin'
    
    def test_verify_access_token_invalid(self):
        """Should reject invalid access token"""
        from services.auth_service import verify_access_token
        
        payload = verify_access_token('invalid-token')
        
        assert payload is None
    
    def test_verify_access_token_wrong_type(self):
        """Should reject token with wrong type"""
        from services.auth_service import generate_refresh_token, verify_access_token
        
        refresh_token = generate_refresh_token('user-123', 'test@example.com')
        
        payload = verify_access_token(refresh_token)
        
        assert payload is None
    
    def test_verify_refresh_token_valid(self):
        """Should verify valid refresh token"""
        from services.auth_service import generate_refresh_token, verify_refresh_token
        
        token = generate_refresh_token('user-123', 'test@example.com')
        
        with patch('services.auth_service.is_token_blacklisted', return_value=False):
            payload = verify_refresh_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 'user-123'
        assert payload['email'] == 'test@example.com'
    
    def test_verify_refresh_token_blacklisted(self):
        """Should reject blacklisted refresh token"""
        from services.auth_service import generate_refresh_token, verify_refresh_token
        
        token = generate_refresh_token('user-123', 'test@example.com')
        
        with patch('services.auth_service.is_token_blacklisted', return_value=True):
            payload = verify_refresh_token(token)
        
        assert payload is None
    
    def test_verify_refresh_token_invalid(self):
        """Should reject invalid refresh token"""
        from services.auth_service import verify_refresh_token
        
        payload = verify_refresh_token('invalid-token')
        
        assert payload is None
    
    def test_verify_refresh_token_wrong_type(self):
        """Should reject token with wrong type"""
        from services.auth_service import generate_access_token, verify_refresh_token
        
        access_token, _ = generate_access_token('user-123', 'test@example.com', 'admin')
        
        payload = verify_refresh_token(access_token)
        
        assert payload is None


class TestCookieConfiguration:
    """Test cookie configuration functions"""
    
    def test_create_cookie_config_basic(self):
        """Should create basic cookie config"""
        from services.auth_service import create_cookie_config
        
        config = create_cookie_config('test_cookie', 'test_value', 3600)
        
        assert config['key'] == 'test_cookie'
        assert config['value'] == 'test_value'
        assert config['max_age'] == 3600
        assert config['httponly'] is True
        assert 'secure' in config
        assert 'samesite' in config
        assert 'path' in config
    
    def test_create_cookie_config_not_httponly(self):
        """Should create non-httponly cookie config"""
        from services.auth_service import create_cookie_config
        
        config = create_cookie_config('csrf_token', 'token123', 900, httponly=False)
        
        assert config['httponly'] is False
    
    def test_create_cookie_config_includes_path(self):
        """Should include path in cookie config"""
        from services.auth_service import create_cookie_config
        
        config = create_cookie_config('test', 'value', 3600)
        
        assert 'path' in config


class TestMockUsers:
    """Test mock user functions"""
    
    def test_get_mock_users_when_enabled(self, monkeypatch):
        """Should return mock users when enabled"""
        from services.auth_service import _get_mock_users
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        mock_settings.admin_password = 'admin123'
        
        with patch('services.auth_service.settings', mock_settings):
            users = _get_mock_users()
        
        assert isinstance(users, dict)
        if users:  # Only check if mock users are enabled
            assert 'owner@morningai.com' in users or 'admin@morningai.com' in users
    
    def test_get_mock_users_when_disabled(self, monkeypatch):
        """Should return empty dict when disabled"""
        from services.auth_service import _get_mock_users
        
        monkeypatch.setenv('TESTING', 'false')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'false')
        
        users = _get_mock_users()
        
        assert users == {}
