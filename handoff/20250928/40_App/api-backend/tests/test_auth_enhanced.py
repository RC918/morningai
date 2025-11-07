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
    """Mock Redis client using fakeredis for stateful behavior"""
    from fakeredis import FakeRedis
    import src.utils.pre_auth_token
    
    src.utils.pre_auth_token._pre_auth_manager = None
    
    redis_client = FakeRedis(decode_responses=True)
    with patch('src.services.auth_service.get_redis_client') as mock1, \
         patch('src.utils.redis_client.get_redis_client') as mock2, \
         patch('src.utils.pre_auth_token.get_redis_client') as mock3:
        mock1.return_value = redis_client
        mock2.return_value = redis_client
        mock3.return_value = redis_client
        
        yield redis_client
        
        src.utils.pre_auth_token._pre_auth_manager = None
        redis_client.flushall()


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
        assert mock_redis.exists(key) == 1
    
    def test_is_token_blacklisted(self, mock_redis):
        """Test checking if token is blacklisted"""
        token = generate_refresh_token('user-001', 'test@example.com')
        
        assert is_token_blacklisted(token) is False
        
        blacklist_refresh_token(token)
        assert is_token_blacklisted(token) is True
    
    def test_rotate_refresh_token(self, mock_redis):
        """Test refresh token rotation"""
        old_token = generate_refresh_token('user-001', 'test@example.com')
        
        new_token = rotate_refresh_token(old_token, 'user-001', 'test@example.com')
        
        assert new_token is not None
        assert new_token != old_token
        
        old_token_hash = hash_token(old_token)
        assert mock_redis.exists(f"blacklist:refresh:{old_token_hash}") == 1


class TestAuthEndpoints:
    """Test auth endpoints"""
    
    def test_login_success(self, client, mock_redis):
        """Test successful login"""
        response = client.post('/api/auth/v2/login',
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
        response = client.post('/api/auth/v2/login',
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
        response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_refresh_token_success(self, client, mock_redis):
        """Test successful token refresh"""
        login_response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        refresh_response = client.post('/api/auth/v2/refresh')
        
        assert refresh_response.status_code == 200
        data = json.loads(refresh_response.data)
        
        assert 'tokens' in data
        assert 'expiresAt' in data['tokens']
        
        set_cookie_headers = refresh_response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'access_token' in cookie_string
        assert 'refresh_token' in cookie_string
    
    def test_refresh_token_missing(self, client):
        """Test refresh without token"""
        response = client.post('/api/auth/v2/refresh')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        client.set_cookie('refresh_token', 'invalid-token')
        
        response = client.post('/api/auth/v2/refresh')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_logout_success(self, client, mock_redis):
        """Test successful logout"""
        login_response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        logout_response = client.post('/api/auth/v2/logout')
        
        assert logout_response.status_code == 200
        data = json.loads(logout_response.data)
        assert 'message' in data
        
        set_cookie_headers = logout_response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'max-age=0' in cookie_string.lower() or 'Max-Age=0' in cookie_string
    
    def test_get_current_user_success(self, client, mock_redis):
        """Test getting current user"""
        login_response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        me_response = client.get('/api/auth/v2/me')
        
        assert me_response.status_code == 200
        data = json.loads(me_response.data)
        
        assert data['email'] == 'owner@morningai.com'
        assert data['role'] == 'owner'
        assert 'id' in data
        assert 'name' in data
    
    def test_get_current_user_not_authenticated(self, client):
        """Test getting current user without authentication"""
        response = client.get('/api/auth/v2/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_verify_token_with_cookie(self, client, mock_redis):
        """Test token verification with cookie"""
        login_response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        verify_response = client.get('/api/auth/v2/verify')
        
        assert verify_response.status_code == 200
        data = json.loads(verify_response.data)
        
        assert data['email'] == 'owner@morningai.com'
        assert data['role'] == 'owner'
    
    def test_verify_token_with_header(self, client):
        """Test that enhanced auth endpoints use cookies, not headers"""
        token, _ = generate_access_token('user-001', 'test@example.com', 'owner')
        
        response = client.get('/api/auth/v2/verify',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 401


class TestTokenRotationFlow:
    """Test complete token rotation flow"""
    
    def test_complete_auth_flow(self, client, mock_redis):
        """Test complete authentication flow: login -> refresh -> logout"""
        login_response = client.post('/api/auth/v2/login',
            json={
                'email': 'owner@morningai.com',
                'password': 'owner123'
            }
        )
        assert login_response.status_code == 200
        
        login_cookies = ' '.join(login_response.headers.getlist('Set-Cookie'))
        assert 'access_token' in login_cookies
        assert 'refresh_token' in login_cookies
        
        me_response = client.get('/api/auth/v2/me')
        assert me_response.status_code == 200
        
        refresh_response = client.post('/api/auth/v2/refresh')
        assert refresh_response.status_code == 200
        
        refresh_cookies = ' '.join(refresh_response.headers.getlist('Set-Cookie'))
        assert 'access_token' in refresh_cookies
        assert 'refresh_token' in refresh_cookies
        
        me_response_2 = client.get('/api/auth/v2/me')
        assert me_response_2.status_code == 200
        
        logout_response = client.post('/api/auth/v2/logout')
        assert logout_response.status_code == 200


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
        
        payload = verify_refresh_token(token)
        assert payload is not None
        
        blacklist_refresh_token(token)
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


class Test2FAIntegration:
    """Test 2FA integration with login flow"""
    
    def test_is_2fa_feature_enabled_in_test_mode(self, client):
        """Test that 2FA is disabled when Flask TESTING=True"""
        from src.routes.totp import is_2fa_feature_enabled
        
        with client.application.app_context():
            client.application.config['TESTING'] = True
            result = is_2fa_feature_enabled()
            assert result is False
    
    def test_is_2fa_feature_enabled_production_mode(self):
        """Test that 2FA respects env var when TESTING=False"""
        from src.routes.totp import is_2fa_feature_enabled
        import os
        
        with patch.dict(os.environ, {'FEATURE_2FA_ENABLED': 'true'}):
            result = is_2fa_feature_enabled()
            assert result is True
        
        with patch.dict(os.environ, {'FEATURE_2FA_ENABLED': 'false'}):
            result = is_2fa_feature_enabled()
            assert result is False
    
    def test_check_2fa_required_owner_role(self):
        """Test that Owner role always requires 2FA"""
        from src.routes.totp import check_2fa_required
        
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_enabled:
            mock_enabled.return_value = True
            
            with patch('src.routes.totp.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = {'id': 'user-001', 'role': 'owner'}
                
                result = check_2fa_required('user-001')
                assert result is True
    
    def test_check_2fa_required_non_owner_enabled(self):
        """Test that non-owner with 2FA enabled requires 2FA"""
        from src.routes.totp import check_2fa_required
        
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_enabled:
            mock_enabled.return_value = True
            
            with patch('src.routes.totp.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = {'id': 'user-002', 'role': 'user'}
                
                with patch('src.routes.totp.create_client') as mock_supabase:
                    mock_client = MagicMock()
                    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                        {'enabled': True}
                    ]
                    mock_supabase.return_value = mock_client
                    
                    result = check_2fa_required('user-002')
                    assert result is True
    
    def test_check_2fa_required_non_owner_disabled(self):
        """Test that non-owner without 2FA enabled does not require 2FA"""
        from src.routes.totp import check_2fa_required
        
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_enabled:
            mock_enabled.return_value = True
            
            with patch('src.routes.totp.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = {'id': 'user-003', 'role': 'user'}
                
                with patch('src.routes.totp.create_client') as mock_supabase:
                    mock_client = MagicMock()
                    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
                    mock_supabase.return_value = mock_client
                    
                    result = check_2fa_required('user-003')
                    assert result is False
    
    def test_login_requires_2fa_response(self, client, mock_redis):
        """Test that login returns requires_2fa when 2FA is needed"""
        with patch('src.routes.auth_enhanced.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'id': 'user-001',
                'email': 'owner@example.com',
                'role': 'owner',
                'name': 'Owner User',
                'tenant_id': 'tenant-001'
            }
            
            with patch('src.routes.totp.check_2fa_required') as mock_2fa:
                mock_2fa.return_value = True
                
                response = client.post('/api/auth/v2/login',
                    json={
                        'email': 'owner@example.com',
                        'password': 'test_password'
                    }
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data.get('requires_2fa') is True
                assert 'user' in data
                assert data['user']['id'] == 'user-001'
                assert data['user']['email'] == 'owner@example.com'
                
                set_cookie_header = response.headers.get('Set-Cookie', '')
                assert 'access_token' not in set_cookie_header
                assert 'refresh_token' not in set_cookie_header
    
    def test_verify_login_missing_totp_and_backup_code(self, client, mock_redis):
        """Test that verify-login returns 400 when both totp_code and backup_code are missing"""
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_feature:
            mock_feature.return_value = True
            
            response = client.post('/api/auth/v2/totp/verify-login',
                json={
                    'email': 'owner@example.com',
                    'password': 'test_password'
                }
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_verify_login_missing_credentials(self, client, mock_redis):
        """Test that verify-login returns 400 when email or password is missing"""
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_feature:
            mock_feature.return_value = True
            
            response = client.post('/api/auth/v2/totp/verify-login',
                json={
                    'totp_code': '123456'
                }
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_check_2fa_required_exception_handling(self, client, mock_redis):
        """Test that check_2fa_required returns False on exception"""
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_feature:
            mock_feature.return_value = True
            
            with patch('src.routes.totp.create_client') as mock_client:
                mock_client.side_effect = Exception('Database error')
                
                from src.routes.totp import check_2fa_required
                result = check_2fa_required('user-123')
                
                assert result is False
    
    def test_verify_login_feature_disabled(self, client, mock_redis):
        """Test that verify-login returns 403 when 2FA feature is disabled"""
        response = client.post('/api/auth/v2/totp/verify-login',
            json={
                'email': 'owner@example.com',
                'password': 'test_password',
                'totp_code': '123456'
            }
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_login_invalid_totp_format(self, client, mock_redis):
        """Test that verify-login returns 400 for invalid TOTP format"""
        with patch('src.routes.totp.is_2fa_feature_enabled') as mock_feature:
            mock_feature.return_value = True
            
            with patch('src.services.auth_service.authenticate_user') as mock_auth:
                mock_auth.return_value = {
                    'id': 'user-001',
                    'email': 'owner@example.com',
                    'role': 'owner'
                }
                
                with patch('src.routes.totp.check_2fa_required') as mock_2fa:
                    mock_2fa.return_value = True
                    
                    response = client.post('/api/auth/v2/totp/verify-login',
                        json={
                            'email': 'owner@example.com',
                            'password': 'test_password',
                            'totp_code': 'abc123'
                        }
                    )
                    
                    assert response.status_code == 400
                    data = json.loads(response.data)
                    assert 'error' in data
    
    def test_check_2fa_required_feature_disabled(self, client, mock_redis):
        """Test that check_2fa_required returns False when feature is disabled"""
        from src.routes.totp import check_2fa_required
        
        result = check_2fa_required('user-123')
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
