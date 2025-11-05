"""
Tests for 2FA Pre-Authentication Flow

Tests the new pre-authentication flow for 2FA enrollment and challenge:
- Login returns next_step + tmp_login_token
- /2fa/enroll endpoint (pre-auth)
- /2fa/verify-enroll endpoint (pre-auth)
- /2fa/challenge endpoint (pre-auth)
- Pre-auth token validation and single-use enforcement
- Rate limiting
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.main import app
from src.utils.pre_auth_token import get_pre_auth_manager


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client for pre-auth tokens"""
    with patch('src.utils.pre_auth_token.get_redis_client') as mock:
        redis_mock = MagicMock()
        redis_mock.hgetall.return_value = {}
        redis_mock.hset.return_value = True
        redis_mock.hincrby.return_value = 1
        redis_mock.expire.return_value = True
        redis_mock.delete.return_value = 1
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('src.routes.auth_enhanced.create_client') as mock_create, \
         patch('src.routes.auth_2fa.create_client') as mock_create_2fa:
        supabase_mock = MagicMock()
        
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = []
        supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        mock_create.return_value = supabase_mock
        mock_create_2fa.return_value = supabase_mock
        
        yield supabase_mock


@pytest.fixture
def mock_totp():
    """Mock TOTP manager"""
    with patch('src.routes.auth_2fa.get_totp_manager') as mock:
        totp_mock = MagicMock()
        totp_mock.generate_secret.return_value = 'BASE32SECRET123'
        totp_mock.encrypt_secret.return_value = 'encrypted_secret'
        totp_mock.decrypt_secret.return_value = 'BASE32SECRET123'
        totp_mock.generate_qr_code.return_value = 'data:image/png;base64,QRCODE'
        totp_mock.verify_totp.return_value = True
        mock.return_value = totp_mock
        yield totp_mock


@pytest.fixture
def mock_backup_codes():
    """Mock backup code manager"""
    with patch('src.routes.auth_2fa.get_backup_manager') as mock:
        backup_mock = MagicMock()
        backup_mock.generate_backup_codes.return_value = [
            'AAAA-BBBB-CCCC-DDDD',
            'EEEE-FFFF-GGGG-HHHH',
            'IIII-JJJJ-KKKK-LLLL'
        ]
        backup_mock.hash_backup_code.return_value = 'hashed_code'
        backup_mock.verify_backup_code.return_value = True
        mock.return_value = backup_mock
        yield backup_mock


class TestLoginWithPreAuth:
    """Test login endpoint with pre-auth flow"""
    
    def test_login_no_2fa_returns_session(self, client, mock_redis, mock_supabase):
        """Test login without 2FA requirement returns session directly"""
        with patch('src.routes.auth_enhanced.check_2fa_required', return_value=False):
            response = client.post('/api/auth/v2/login',
                json={
                    'email': 'owner@morningai.com',
                    'password': 'owner123'
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['next_step'] == 'session'
            assert 'user' in data
            assert 'tokens' in data
            assert 'token' not in data  # No tmp_login_token
    
    def test_login_2fa_not_enrolled_returns_enroll(self, client, mock_redis, mock_supabase):
        """Test login with 2FA required but not enrolled returns enroll_2fa"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        with patch('src.routes.auth_enhanced.check_2fa_required', return_value=True):
            response = client.post('/api/auth/v2/login',
                json={
                    'email': 'owner@morningai.com',
                    'password': 'owner123'
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['requires_2fa'] is True
            assert data['next_step'] == 'enroll_2fa'
            assert 'token' in data
            assert len(data['token']) > 0
            assert 'user' in data
            assert data['user']['email'] == 'owner@morningai.com'
    
    def test_login_2fa_enrolled_returns_challenge(self, client, mock_redis, mock_supabase):
        """Test login with 2FA enrolled returns challenge_2fa"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'user_id': 'user-001',
            'enabled': True,
            'verified_at': '2024-01-01T00:00:00Z',
            'totp_secret': 'encrypted_secret'
        }]
        
        with patch('src.routes.auth_enhanced.check_2fa_required', return_value=True):
            response = client.post('/api/auth/v2/login',
                json={
                    'email': 'owner@morningai.com',
                    'password': 'owner123'
                }
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['requires_2fa'] is True
            assert data['next_step'] == 'challenge_2fa'
            assert 'token' in data
            assert len(data['token']) > 0


class TestPreAuthTokenManager:
    """Test pre-auth token manager"""
    
    def test_generate_token(self, mock_redis):
        """Test generating pre-auth token"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        mock_redis.hset.assert_called()
        mock_redis.expire.assert_called()
    
    def test_verify_token_valid(self, mock_redis):
        """Test verifying valid pre-auth token"""
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        payload = manager.verify_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 'user-001'
        assert payload['email'] == 'test@example.com'
        assert payload['scope'] == 'enroll'
        assert payload['pre_auth'] is True
    
    def test_verify_token_consumed(self, mock_redis):
        """Test verifying consumed token returns None"""
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'True'
        }
        
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        payload = manager.verify_token(token)
        
        assert payload is None
    
    def test_verify_token_max_attempts(self, mock_redis):
        """Test verifying token with max attempts returns None"""
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '5',
            'consumed': 'False'
        }
        
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        payload = manager.verify_token(token)
        
        assert payload is None
    
    def test_consume_token(self, mock_redis):
        """Test consuming token"""
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'consumed': 'False'
        }
        
        manager = get_pre_auth_manager()
        result = manager.consume_token('test-jti')
        
        assert result is True
        mock_redis.hset.assert_called()


class TestEnrollEndpoint:
    """Test /2fa/enroll endpoint"""
    
    def test_enroll_without_token(self, client):
        """Test enroll without pre-auth token returns 401"""
        response = client.post('/api/auth/v2/2fa/enroll')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'TMP_TOKEN_MISSING'
    
    def test_enroll_with_invalid_token(self, client, mock_redis):
        """Test enroll with invalid token returns 401"""
        response = client.post('/api/auth/v2/2fa/enroll',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_enroll_success(self, client, mock_redis, mock_supabase, mock_totp):
        """Test successful 2FA enrollment"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post('/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'secret' in data
        assert 'qr_code' in data
        assert 'backup_codes' not in data  # Should NOT be returned here
        assert data['secret'] == 'BASE32SECRET123'
        assert data['qr_code'].startswith('data:image/png;base64,')


class TestVerifyEnrollEndpoint:
    """Test /2fa/verify-enroll endpoint"""
    
    def test_verify_enroll_without_token(self, client):
        """Test verify-enroll without pre-auth token returns 401"""
        response = client.post('/api/auth/v2/2fa/verify-enroll',
            json={'code': '123456'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_missing_code(self, client, mock_redis):
        """Test verify-enroll without code returns 400"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        response = client.post('/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {token}'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_invalid_code_format(self, client, mock_redis):
        """Test verify-enroll with invalid code format returns 400"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        response = client.post('/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': '12345'}  # Only 5 digits
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_success(self, client, mock_redis, mock_supabase, mock_totp, mock_backup_codes):
        """Test successful 2FA enrollment verification"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret'
        }]
        
        response = client.post('/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 3
        assert 'user' in data
        assert 'tokens' in data
        
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'access_token' in cookie_string
        assert 'refresh_token' in cookie_string


class TestChallengeEndpoint:
    """Test /2fa/challenge endpoint"""
    
    def test_challenge_without_token(self, client):
        """Test challenge without pre-auth token returns 401"""
        response = client.post('/api/auth/v2/2fa/challenge',
            json={'code': '123456'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_missing_code_and_backup(self, client, mock_redis):
        """Test challenge without code or backup_code returns 400"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'challenge')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'challenge',
            'attempts': '0',
            'consumed': 'False'
        }
        
        response = client.post('/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {token}'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_with_totp_success(self, client, mock_redis, mock_supabase, mock_totp):
        """Test successful 2FA challenge with TOTP code"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'challenge')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'challenge',
            'attempts': '0',
            'consumed': 'False'
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'user_id': 'user-001',
            'enabled': True,
            'totp_secret': 'encrypted_secret'
        }]
        
        response = client.post('/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'user' in data
        assert 'tokens' in data
        assert 'backup_codes_remaining' not in data
        
        set_cookie_headers = response.headers.getlist('Set-Cookie')
        cookie_string = ' '.join(set_cookie_headers)
        assert 'access_token' in cookie_string
        assert 'refresh_token' in cookie_string
    
    def test_challenge_with_backup_code_success(self, client, mock_redis, mock_supabase, mock_backup_codes):
        """Test successful 2FA challenge with backup code"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'challenge')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'challenge',
            'attempts': '0',
            'consumed': 'False'
        }
        
        user_2fa_data = [{
            'user_id': 'user-001',
            'enabled': True,
            'totp_secret': 'encrypted_secret'
        }]
        
        backup_codes_data = [{
            'id': 'code-001',
            'user_id': 'user-001',
            'code_hash': 'hashed_code',
            'used': False
        }]
        
        remaining_codes_data = [{'id': 'code-002'}, {'id': 'code-003'}]
        
        def mock_table_select(*args, **kwargs):
            mock_result = MagicMock()
            if args[0] == 'user_2fa':
                mock_result.data = user_2fa_data
            elif args[0] == 'totp_backup_codes':
                if not hasattr(mock_table_select, 'call_count'):
                    mock_table_select.call_count = 0
                mock_table_select.call_count += 1
                
                if mock_table_select.call_count == 1:
                    mock_result.data = backup_codes_data
                else:
                    mock_result.data = remaining_codes_data
            
            return mock_result
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_table_select
        
        response = client.post('/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {token}'},
            json={'backup_code': 'AAAA-BBBB-CCCC-DDDD'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'backup_codes_remaining' in data
        assert data['backup_codes_remaining'] == 2


class TestPreAuthSecurity:
    """Test pre-auth security features"""
    
    def test_scope_enforcement(self, client, mock_redis):
        """Test that enroll scope can't be used for challenge endpoint"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        response = client.post('/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'SCOPE_MISMATCH'
    
    def test_token_single_use(self, client, mock_redis, mock_supabase, mock_totp):
        """Test that pre-auth token can only be used once"""
        manager = get_pre_auth_manager()
        token = manager.generate_token('user-001', 'test@example.com', 'enroll')
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'False'
        }
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response1 = client.post('/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response1.status_code == 200
        
        mock_redis.hgetall.return_value = {
            'user_id': 'user-001',
            'email': 'test@example.com',
            'scope': 'enroll',
            'attempts': '0',
            'consumed': 'True'
        }
        
        response2 = client.post('/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response2.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
