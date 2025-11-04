"""
Integration tests for 2FA with Pre-Auth Token.

Tests the complete login flow:
1. Login with Owner account → receives pre_auth_token cookie
2. Verify with TOTP using pre_auth_token
3. Verify backward compatibility (password fallback)
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.app import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_owner_user():
    """Mock Owner user with 2FA enabled"""
    return {
        'id': 'owner-001',
        'email': 'owner@test.com',
        'name': 'Test Owner',
        'role': 'owner',
        'tenant_id': 'tenant-001',
        'hashed_password': 'hashed_password_here'
    }


class TestPreAuthTokenIntegration:
    """Integration tests for pre-auth token flow"""
    
    @patch('src.routes.auth_enhanced.authenticate_user')
    @patch('src.routes.auth_enhanced.check_2fa_required')
    @patch('src.config.FEATURE_2FA_PREAUTH', True)
    @patch('src.utils.preauth_token.get_redis_client')
    def test_login_issues_preauth_token(
        self, mock_redis, mock_check_2fa, mock_auth, client, mock_owner_user
    ):
        """Test that login issues pre-auth token when 2FA required"""
        # Mock authentication
        mock_auth.return_value = mock_owner_user
        mock_check_2fa.return_value = True
        
        # Mock Redis
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        # Login
        response = client.post(
            '/api/auth/v2/login',
            json={'email': 'owner@test.com', 'password': 'password123'},
            content_type='application/json'
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['requires_2fa'] is True
        assert data['user']['id'] == 'owner-001'
        
        # Assert pre_auth_token cookie is set
        cookies = response.headers.getlist('Set-Cookie')
        pre_auth_cookie = [c for c in cookies if 'pre_auth_token=' in c]
        assert len(pre_auth_cookie) == 1
        assert 'HttpOnly' in pre_auth_cookie[0]
        assert 'SameSite=Lax' in pre_auth_cookie[0]
        assert 'Path=/api/auth/v2/totp' in pre_auth_cookie[0]
        
        # Assert Redis setex was called
        assert mock_redis_instance.setex.called
    
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.verify_totp_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.routes.totp.is_2fa_feature_enabled')
    @patch('src.config.FEATURE_2FA_PREAUTH', True)
    @patch('src.utils.preauth_token.get_redis_client')
    @patch('src.routes.totp.generate_access_token')
    @patch('src.routes.totp.generate_refresh_token')
    def test_verify_with_preauth_token(
        self,
        mock_gen_refresh,
        mock_gen_access,
        mock_redis,
        mock_2fa_enabled,
        mock_check_2fa,
        mock_verify_totp,
        mock_get_user,
        client,
        mock_owner_user
    ):
        """Test TOTP verification using pre-auth token"""
        # Setup mocks
        mock_2fa_enabled.return_value = True
        mock_check_2fa.return_value = True
        mock_verify_totp.return_value = True
        mock_get_user.return_value = mock_owner_user
        mock_gen_access.return_value = ("access_token", 1234567890000)
        mock_gen_refresh.return_value = "refresh_token"
        
        # Mock Redis for pre-auth token validation
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        token = "test-preauth-token"
        nonce = "test-nonce"
        redis_key = f"preauth:owner-001:{nonce}"
        
        stored_data = {
            "token": token,
            "issued_at": "2025-11-04T10:00:00",
            "attempts": 0,
            "email": "owner@test.com",
            "nonce": nonce
        }
        
        mock_redis_instance.scan_iter.return_value = [redis_key]
        mock_redis_instance.get.return_value = json.dumps(stored_data)
        
        # Verify with TOTP using pre-auth token
        client.set_cookie('localhost', 'pre_auth_token', token)
        
        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={'code': '123456'},
            content_type='application/json'
        )
        
        # Assert success
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['id'] == 'owner-001'
        
        # Assert pre-auth token was consumed (deleted)
        mock_redis_instance.delete.assert_called_once_with(redis_key)
        
        # Assert pre_auth_token cookie is cleared
        cookies = response.headers.getlist('Set-Cookie')
        clear_cookie = [c for c in cookies if 'pre_auth_token=;' in c or 'pre_auth_token="";' in c]
        assert len(clear_cookie) >= 1
    
    @patch('src.routes.totp.authenticate_user')
    @patch('src.routes.totp.verify_totp_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.routes.totp.is_2fa_feature_enabled')
    @patch('src.config.FEATURE_2FA_PREAUTH', True)
    @patch('src.routes.totp.generate_access_token')
    @patch('src.routes.totp.generate_refresh_token')
    def test_verify_fallback_to_password(
        self,
        mock_gen_refresh,
        mock_gen_access,
        mock_2fa_enabled,
        mock_check_2fa,
        mock_verify_totp,
        mock_auth,
        client,
        mock_owner_user
    ):
        """Test TOTP verification falls back to password when no pre-auth token"""
        # Setup mocks
        mock_2fa_enabled.return_value = True
        mock_check_2fa.return_value = True
        mock_verify_totp.return_value = True
        mock_auth.return_value = mock_owner_user
        mock_gen_access.return_value = ("access_token", 1234567890000)
        mock_gen_refresh.return_value = "refresh_token"
        
        # Verify with TOTP using email + password (no pre-auth token)
        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'owner@test.com',
                'password': 'password123',
                'code': '123456'
            },
            content_type='application/json'
        )
        
        # Assert success (backward compatibility)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['id'] == 'owner-001'
        
        # Assert authenticate_user was called (password fallback)
        mock_auth.assert_called_once_with('owner@test.com', 'password123')
    
    @patch('src.routes.totp.is_2fa_feature_enabled')
    @patch('src.config.FEATURE_2FA_PREAUTH', True)
    def test_verify_requires_preauth_or_password(self, mock_2fa_enabled, client):
        """Test that verify-login requires either pre-auth token or email/password"""
        mock_2fa_enabled.return_value = True
        
        # Attempt to verify without pre-auth token or password
        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={'code': '123456'},
            content_type='application/json'
        )
        
        # Assert error
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Pre-auth token or email/password required' in data['error']


class TestPreAuthTokenDisabled:
    """Test behavior when pre-auth token feature is disabled"""
    
    @patch('src.routes.auth_enhanced.authenticate_user')
    @patch('src.routes.auth_enhanced.check_2fa_required')
    @patch('src.config.FEATURE_2FA_PREAUTH', False)
    def test_login_no_preauth_when_disabled(
        self, mock_check_2fa, mock_auth, client, mock_owner_user
    ):
        """Test that login does not issue pre-auth token when feature disabled"""
        # Mock authentication
        mock_auth.return_value = mock_owner_user
        mock_check_2fa.return_value = True
        
        # Login
        response = client.post(
            '/api/auth/v2/login',
            json={'email': 'owner@test.com', 'password': 'password123'},
            content_type='application/json'
        )
        
        # Assert response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['requires_2fa'] is True
        
        # Assert NO pre_auth_token cookie is set
        cookies = response.headers.getlist('Set-Cookie')
        pre_auth_cookie = [c for c in cookies if 'pre_auth_token=' in c]
        assert len(pre_auth_cookie) == 0
