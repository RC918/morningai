"""
Tests for Enhanced Authentication System
Task 1: Enhanced Token Security

Tests:
- Login with HttpOnly cookies
- Token refresh with rotation
- Logout with blacklist
- Token verification
- Blacklist functionality
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.main import app
from src.services.auth_service import (
    generate_access_token,
    generate_refresh_token,
    verify_access_token,
    verify_refresh_token,
    blacklist_refresh_token,
    is_token_blacklisted,
    rotate_refresh_token,
    hash_token
)


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.services.auth_service.get_redis_client') as mock:
        redis_mock = MagicMock()
        redis_mock.exists.return_value = 0
        redis_mock.setex.return_value = True
        mock.return_value = redis_mock
        yield redis_mock


class TestAuthService:
    """Test auth service functions"""
    
    def test_generate_access_token(self):
        """Test access token generation"""
        token, expiry_ms = generate_access_token('user-001', 'test@example.com', 'owner')
        
        assert token is not None
        assert isinstance(token, str)
        assert expiry_ms > 0
        
        payload = verify_access_token(token)
        assert payload is not None
        assert payload['user_id'] == 'user-001'
        assert payload['email'] == 'test@example.com'
        assert payload['role'] == 'owner'
        assert payload['type'] == 'access'
    
    def test_generate_refresh_token(self):
        """Test refresh token generation"""
        token = generate_refresh_token('user-001', 'test@example.com')
        
        assert token is not None
        assert isinstance(token, str)
        
        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload['user_id'] == 'user-001'
        assert payload['email'] == 'test@example.com'
        assert payload['type'] == 'refresh'
    
    def test_verify_expired_access_token(self):
        """Test verification of expired access token"""
        payload = verify_access_token('invalid-token')
        assert payload is None
    
    def test_blacklist_token(self, mock_redis):
        """Test token blacklisting"""
        token = generate_refresh_token('user-001', 'test@example.com')
        
        result = blacklist_refresh_token(token)
        assert result is True
        
        token_hash = hash_token(token)
        key = f"blacklist:refresh:{token_hash}"
        mock_redis.setex.assert_called_once()
        assert mock_redis.setex.call_args[0][0] == key
    
    def test_is_token_blacklisted(self, mock_redis):
        """Test checking if token is blacklisted"""
        token = generate_refresh_token('user-001', 'test@example.com')
        
        mock_redis.exists.return_value = 0
        assert is_token_blacklisted(token) is False
        
        mock_redis.exists.return_value = 1
        assert is_token_blacklisted(token) is True
    
    def test_rotate_refresh_token(self, mock_redis):
        """Test refresh token rotation"""
        old_token = generate_refresh_token('user-001', 'test@example.com')
        
        new_token = rotate_refresh_token(old_token, 'user-001', 'test@example.com')
        
        assert new_token is not None
        assert new_token != old_token
        
        mock_redis.setex.assert_called_once()


class TestAuthEndpoints:
    """Test auth endpoints"""
    
    def test_login_success(self, client, mock_redis):
        """Test successful login"""
        response = client.post('/api/auth/login', 
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'user' in data
        assert 'tokens' in data
        assert data['user']['email'] == 'owner@morningai.com'
        assert data['user']['role'] == 'owner'
        assert 'expiresAt' in data['tokens']
        
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'access_token' in cookie_string
        assert 'refresh_token' in cookie_string
        assert 'HttpOnly' in cookie_string
        assert 'Path=/' in cookie_string
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'wrong-password'
            }
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_refresh_token_success(self, client, mock_redis):
        """Test successful token refresh"""
        login_response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        refresh_response = client.post('/api/auth/refresh')
        
        assert refresh_response.status_code == 200
        data = json.loads(refresh_response.data)
        
        assert 'tokens' in data
        assert 'expiresAt' in data['tokens']
        
        set_cookie_headers = refresh_response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'access_token' in cookie_string
        assert 'refresh_token' in cookie_string
        
        mock_redis.setex.assert_called()
    
    def test_refresh_token_missing(self, client):
        """Test refresh without token"""
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        client.set_cookie('refresh_token', 'invalid-token')
        
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_logout_success(self, client, mock_redis):
        """Test successful logout"""
        login_response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        logout_response = client.post('/api/auth/logout')
        
        assert logout_response.status_code == 200
        data = json.loads(logout_response.data)
        assert 'message' in data
        
        mock_redis.setex.assert_called()
        
        set_cookie_headers = logout_response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'max-age=0' in cookie_string.lower() or 'Max-Age=0' in cookie_string
    
    def test_get_current_user_success(self, client, mock_redis):
        """Test getting current user"""
        login_response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        me_response = client.get('/api/auth/me')
        
        assert me_response.status_code == 200
        data = json.loads(me_response.data)
        
        assert data['email'] == 'owner@morningai.com'
        assert data['role'] == 'owner'
        assert 'id' in data
        assert 'name' in data
    
    def test_get_current_user_not_authenticated(self, client):
        """Test getting current user without authentication"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_verify_token_with_cookie(self, client, mock_redis):
        """Test token verification with cookie"""
        login_response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        verify_response = client.get('/api/auth/verify')
        
        assert verify_response.status_code == 200
        data = json.loads(verify_response.data)
        
        assert data['email'] == 'owner@morningai.com'
        assert data['role'] == 'owner'
    
    def test_verify_token_with_header(self, client):
        """Test that enhanced auth endpoints use cookies, not headers"""
        token, _ = generate_access_token('user-001', 'test@example.com', 'owner')
        
        response = client.get('/api/auth/verify',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 401


class TestTokenRotationFlow:
    """Test complete token rotation flow"""
    
    def test_complete_auth_flow(self, client, mock_redis):
        """Test complete authentication flow: login -> refresh -> logout"""
        login_response = client.post('/api/auth/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        login_cookies = ' '.join(login_response.headers.getlist('Set-Cookie'))
        assert 'access_token' in login_cookies
        assert 'refresh_token' in login_cookies
        
        me_response = client.get('/api/auth/me')
        assert me_response.status_code == 200
        
        refresh_response = client.post('/api/auth/refresh')
        assert refresh_response.status_code == 200
        
        refresh_cookies = ' '.join(refresh_response.headers.getlist('Set-Cookie'))
        assert 'access_token' in refresh_cookies
        assert 'refresh_token' in refresh_cookies
        
        me_response_2 = client.get('/api/auth/me')
        assert me_response_2.status_code == 200
        
        logout_response = client.post('/api/auth/logout')
        assert logout_response.status_code == 200
        
        assert mock_redis.setex.call_count >= 2


class TestSecurityFeatures:
    """Test security features"""
    
    def test_token_type_validation(self):
        """Test that access tokens can't be used as refresh tokens and vice versa"""
        access_token, _ = generate_access_token('user-001', 'test@example.com', 'owner')
        refresh_token = generate_refresh_token('user-001', 'test@example.com')
        
        payload = verify_refresh_token(access_token)
        assert payload is None
        
        payload = verify_access_token(refresh_token)
        assert payload is None
    
    def test_blacklisted_token_rejected(self, mock_redis):
        """Test that blacklisted tokens are rejected"""
        token = generate_refresh_token('user-001', 'test@example.com')
        
        mock_redis.exists.return_value = 0
        payload = verify_refresh_token(token)
        assert payload is not None
        
        mock_redis.exists.return_value = 1
        payload = verify_refresh_token(token)
        assert payload is None
    
    def test_token_hash_consistency(self):
        """Test that token hashing is consistent"""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 character hex string


class TestErrorHandling:
    """Test error handling"""
    
    def test_redis_unavailable_graceful_degradation(self):
        """Test graceful degradation when Redis is unavailable"""
        with patch('src.services.auth_service.get_redis_client') as mock:
            mock.return_value = None
            
            token = generate_refresh_token('user-001', 'test@example.com')
            
            result = blacklist_refresh_token(token)
            assert result is False
            
            result = is_token_blacklisted(token)
            assert result is False
    
    def test_invalid_json_in_login(self, client):
        """Test login with invalid JSON"""
        response = client.post('/api/auth/login',
            data='invalid-json',
            content_type='application/json'
        )
        
        assert response.status_code >= 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
