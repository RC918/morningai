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


class TestValidateSecurityConfig:
    """Test validate_security_config function"""
    
    def test_validate_security_config_production_no_jwt_secret(self, monkeypatch):
        """Should raise RuntimeError in production without JWT secret"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = None
        mock_settings.is_production = True
        mock_settings.environment = 'production'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with pytest.raises(RuntimeError, match="Invalid JWT secret"):
                validate_security_config()
    
    def test_validate_security_config_production_weak_jwt_secret(self, monkeypatch):
        """Should raise RuntimeError in production with weak JWT secret"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'short'
        mock_settings.is_production = True
        mock_settings.environment = 'production'
        mock_settings.cookie_secure = True
        mock_settings.cookie_samesite = 'Lax'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with pytest.raises(RuntimeError, match="at least 32 characters"):
                validate_security_config()
    
    def test_validate_security_config_production_default_jwt_secret(self, monkeypatch):
        """Should raise RuntimeError in production with default JWT secret"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'test-secret-key-for-testing'
        mock_settings.is_production = True
        mock_settings.environment = 'production'
        mock_settings.cookie_secure = True
        mock_settings.cookie_samesite = 'Lax'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with pytest.raises(RuntimeError, match="weak/default value"):
                validate_security_config()
    
    def test_validate_security_config_production_mock_users_enabled(self, monkeypatch):
        """Should raise SystemExit in production with mock users enabled"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'a' * 32
        mock_settings.is_production = True
        mock_settings.environment = 'production'
        mock_settings.cookie_secure = True
        mock_settings.cookie_samesite = 'Lax'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with pytest.raises(SystemExit, match="Security configuration validation failed"):
                validate_security_config()
    
    def test_validate_security_config_samesite_none_without_secure(self, monkeypatch):
        """Should raise SystemExit when SameSite=None without Secure"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'a' * 32
        mock_settings.is_production = False
        mock_settings.environment = 'development'
        mock_settings.cookie_secure = False
        mock_settings.cookie_samesite = 'None'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with patch('services.auth_service.COOKIE_SAMESITE', 'None'):
                with patch('services.auth_service.COOKIE_SECURE', False):
                    with pytest.raises(SystemExit, match="COOKIE_SAMESITE=None requires COOKIE_SECURE=True"):
                        validate_security_config()
    
    def test_validate_security_config_invalid_samesite(self, monkeypatch):
        """Should raise SystemExit with invalid SameSite value"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'a' * 32
        mock_settings.is_production = False
        mock_settings.environment = 'development'
        mock_settings.cookie_secure = True
        mock_settings.cookie_samesite = 'Invalid'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            with patch('services.auth_service.COOKIE_SAMESITE', 'Invalid'):
                with pytest.raises(SystemExit, match="must be 'Strict', 'Lax', or 'None'"):
                    validate_security_config()
    
    def test_validate_security_config_success(self, monkeypatch):
        """Should pass validation with correct config"""
        from services.auth_service import validate_security_config
        
        monkeypatch.setenv('ENVIRONMENT', 'development')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'false')
        
        mock_settings = MagicMock()
        mock_settings.jwt_secret_key = 'a' * 32
        mock_settings.is_production = False
        mock_settings.environment = 'development'
        mock_settings.cookie_secure = True
        mock_settings.cookie_samesite = 'Lax'
        mock_settings.cookie_domain = None
        mock_settings.cookie_path = '/'
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            validate_security_config()


class TestTokenBlacklist:
    """Test token blacklist functions"""
    
    def test_is_token_blacklisted_true(self):
        """Should return True for blacklisted token"""
        from services.auth_service import is_token_blacklisted
        
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            result = is_token_blacklisted('test-token')
        
        assert result is True
    
    def test_is_token_blacklisted_false(self):
        """Should return False for non-blacklisted token"""
        from services.auth_service import is_token_blacklisted
        
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            result = is_token_blacklisted('test-token')
        
        assert result is False
    
    def test_is_token_blacklisted_no_redis(self):
        """Should return False when Redis unavailable"""
        from services.auth_service import is_token_blacklisted
        
        with patch('services.auth_service.get_redis_client', return_value=None):
            result = is_token_blacklisted('test-token')
        
        assert result is False
    
    def test_is_token_blacklisted_redis_error(self):
        """Should return False on Redis error"""
        from services.auth_service import is_token_blacklisted
        
        mock_redis = MagicMock()
        mock_redis.exists.side_effect = Exception("Redis error")
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            result = is_token_blacklisted('test-token')
        
        assert result is False
    
    def test_blacklist_refresh_token_success(self):
        """Should successfully blacklist token"""
        from services.auth_service import blacklist_refresh_token
        
        mock_redis = MagicMock()
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            result = blacklist_refresh_token('test-token')
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_blacklist_refresh_token_no_redis(self):
        """Should fail when Redis unavailable"""
        from services.auth_service import blacklist_refresh_token
        
        with patch('services.auth_service.get_redis_client', return_value=None):
            result = blacklist_refresh_token('test-token')
        
        assert result is False
    
    def test_blacklist_refresh_token_redis_error(self):
        """Should fail on Redis error"""
        from services.auth_service import blacklist_refresh_token
        
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis error")
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            result = blacklist_refresh_token('test-token')
        
        assert result is False
    
    def test_rotate_refresh_token_success(self):
        """Should successfully rotate token"""
        from services.auth_service import rotate_refresh_token
        
        mock_redis = MagicMock()
        
        with patch('services.auth_service.get_redis_client', return_value=mock_redis):
            new_token = rotate_refresh_token('old-token', 'user-123', 'test@example.com')
        
        assert new_token is not None
        assert isinstance(new_token, str)
        assert len(new_token) > 0
    
    def test_rotate_refresh_token_blacklist_failure(self):
        """Should fail when blacklist fails"""
        from services.auth_service import rotate_refresh_token
        
        with patch('services.auth_service.get_redis_client', return_value=None):
            new_token = rotate_refresh_token('old-token', 'user-123', 'test@example.com')
        
        assert new_token is None


class TestCookieManagement:
    """Test cookie management functions"""
    
    def test_set_auth_cookies(self):
        """Should set auth cookies on response"""
        from services.auth_service import set_auth_cookies
        
        mock_response = MagicMock()
        
        set_auth_cookies(mock_response, 'access-token', 'refresh-token', 900000)
        
        assert mock_response.set_cookie.call_count >= 2
    
    def test_set_auth_cookies_with_csrf(self):
        """Should set CSRF cookie when SameSite=None"""
        from services.auth_service import set_auth_cookies
        
        mock_response = MagicMock()
        
        with patch('services.auth_service.COOKIE_SAMESITE', 'None'):
            set_auth_cookies(mock_response, 'access-token', 'refresh-token', 900000)
        
        assert mock_response.set_cookie.call_count >= 3
    
    def test_set_auth_cookies_with_explicit_csrf(self):
        """Should use provided CSRF token"""
        from services.auth_service import set_auth_cookies
        
        mock_response = MagicMock()
        
        set_auth_cookies(mock_response, 'access-token', 'refresh-token', 900000, csrf_token='csrf-123')
        
        assert mock_response.set_cookie.call_count >= 3
    
    def test_clear_auth_cookies(self):
        """Should clear all auth cookies"""
        from services.auth_service import clear_auth_cookies
        
        mock_response = MagicMock()
        
        clear_auth_cookies(mock_response)
        
        assert mock_response.set_cookie.call_count == 3
        calls = mock_response.set_cookie.call_args_list
        assert any('access_token' in str(call) for call in calls)
        assert any('refresh_token' in str(call) for call in calls)
        assert any('csrf_token' in str(call) for call in calls)


class TestAuthenticateUser:
    """Test authenticate_user function"""
    
    def test_authenticate_user_mock_success(self, monkeypatch):
        """Should authenticate with mock users"""
        from services.auth_service import authenticate_user
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        mock_settings.admin_password = 'admin123'
        
        with patch('services.auth_service.settings', mock_settings):
            user = authenticate_user('owner@morningai.com', 'owner123')
        
        if user:
            assert user['email'] == 'owner@morningai.com'
            assert user['role'] == 'owner'
    
    def test_authenticate_user_mock_wrong_password(self, monkeypatch):
        """Should reject wrong password"""
        from services.auth_service import authenticate_user
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        
        with patch('services.auth_service.settings', mock_settings):
            user = authenticate_user('owner@morningai.com', 'wrong-password')
        
        assert user is None
    
    def test_authenticate_user_mock_user_not_found(self, monkeypatch):
        """Should return None for unknown user"""
        from services.auth_service import authenticate_user
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        
        with patch('services.auth_service.settings', mock_settings):
            user = authenticate_user('unknown@example.com', 'password')
        
        assert user is None
    
    def test_authenticate_user_production_mock_enabled(self, monkeypatch):
        """Should reject mock users in production"""
        from services.auth_service import authenticate_user
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        
        user = authenticate_user('owner@morningai.com', 'owner123')
        
        assert user is None
    
    def test_authenticate_user_supabase_missing_config(self, monkeypatch):
        """Should return None when Supabase config missing"""
        from services.auth_service import authenticate_user
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'false')
        monkeypatch.setenv('TESTING', 'false')
        
        mock_settings = MagicMock()
        mock_settings.supabase_url = None
        mock_settings.supabase_anon_key = None
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            user = authenticate_user('test@example.com', 'password')
        
        assert user is None


class TestGetUserById:
    """Test get_user_by_id function"""
    
    def test_get_user_by_id_mock_success(self, monkeypatch):
        """Should get user by ID from mock users"""
        from services.auth_service import get_user_by_id
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        
        with patch('services.auth_service.settings', mock_settings):
            user = get_user_by_id('owner-001')
        
        if user:
            assert user['id'] == 'owner-001'
            assert user['email'] == 'owner@morningai.com'
    
    def test_get_user_by_id_mock_not_found(self, monkeypatch):
        """Should return None for unknown user ID"""
        from services.auth_service import get_user_by_id
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        monkeypatch.setenv('ENVIRONMENT', 'development')
        
        mock_settings = MagicMock()
        mock_settings.owner_password = 'owner123'
        
        with patch('services.auth_service.settings', mock_settings):
            user = get_user_by_id('unknown-id')
        
        assert user is None
    
    def test_get_user_by_id_production_mock_enabled(self, monkeypatch):
        """Should reject mock users in production"""
        from services.auth_service import get_user_by_id
        
        monkeypatch.setenv('ENVIRONMENT', 'production')
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'true')
        
        user = get_user_by_id('owner-001')
        
        assert user is None
    
    def test_get_user_by_id_supabase_missing_config(self, monkeypatch):
        """Should return None when Supabase config missing"""
        from services.auth_service import get_user_by_id
        
        monkeypatch.setenv('ENABLE_MOCK_USERS', 'false')
        monkeypatch.setenv('TESTING', 'false')
        
        mock_settings = MagicMock()
        mock_settings.supabase_url = None
        mock_settings.supabase_service_role_key = None
        
        with patch('services.auth_service.get_settings', return_value=mock_settings):
            user = get_user_by_id('user-123')
        
        assert user is None
