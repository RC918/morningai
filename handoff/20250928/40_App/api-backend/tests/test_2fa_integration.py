"""
Integration Tests for 2FA Pre-Auth Endpoints

Tests the complete integration of 2FA endpoints with pre-auth tokens:
- /api/auth/v2/2fa/enroll with pre-auth token
- /api/auth/v2/2fa/verify-enroll with pre-auth token
- /api/auth/v2/2fa/challenge with pre-auth token
- Scope enforcement (enroll token can't call challenge endpoint)

These tests verify the full request/response cycle including:
- Pre-auth token validation
- Endpoint authorization
- Response format
- Cookie handling
- Error scenarios
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app


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
    with patch('src.utils.redis_client.get_redis_client') as mock1, \
         patch('src.utils.pre_auth_token.get_redis_client') as mock2, \
         patch('src.services.auth_service.get_redis_client') as mock3:
        mock1.return_value = redis_client
        mock2.return_value = redis_client
        mock3.return_value = redis_client
        
        yield redis_client
        
        src.utils.pre_auth_token._pre_auth_manager = None
        redis_client.flushall()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    import os
    with patch.dict(os.environ, {
        "SUPABASE_URL": "http://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key"
    }, clear=False), \
         patch("supabase.create_client") as mock_create:
        supabase_mock = MagicMock()
        
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = []
        supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        mock_create.return_value = supabase_mock
        
        yield supabase_mock


@pytest.fixture
def mock_totp():
    """Mock TOTP manager"""
    with patch("src.routes.auth_2fa.get_totp_manager") as mock:
        totp_mock = MagicMock()
        totp_mock.generate_secret.return_value = "BASE32SECRET123"
        totp_mock.encrypt_secret.return_value = "encrypted_secret"
        totp_mock.decrypt_secret.return_value = "BASE32SECRET123"
        totp_mock.generate_qr_code.return_value = "data:image/png;base64,QRCODE"
        totp_mock.verify_totp.return_value = True
        mock.return_value = totp_mock
        yield totp_mock


@pytest.fixture
def mock_backup_codes():
    """Mock backup code manager"""
    with patch("src.routes.auth_2fa.get_backup_manager") as mock:
        backup_mock = MagicMock()
        backup_mock.generate_codes.return_value = [
            "ABCD-EFGH-IJKL-MNOP",
            "QRST-UVWX-YZ12-3456",
            "7890-ABCD-EFGH-IJKL",
            "MNOP-QRST-UVWX-YZ12",
            "3456-7890-ABCD-EFGH",
            "IJKL-MNOP-QRST-UVWX",
            "YZ12-3456-7890-ABCD",
            "EFGH-IJKL-MNOP-QRST"
        ]
        backup_mock.verify_code.return_value = True
        mock.return_value = backup_mock
        yield backup_mock


@pytest.fixture
def mock_get_user():
    """Mock get_user_by_id"""
    with patch("src.routes.auth_2fa.get_user_by_id") as mock:
        mock.return_value = {
            "id": "user-001",
            "email": "test@example.com",
            "name": "Test User",
            "role": "owner",
            "tenant_id": "tenant-001",
        }
        yield mock


@pytest.fixture
def pre_auth_token_enroll(mock_redis):
    """Generate a valid pre-auth token with enroll scope"""
    from src.utils.pre_auth_token import get_pre_auth_manager
    
    manager = get_pre_auth_manager()
    token = manager.generate_token(
        user_id="user-001",
        scope="enroll",
        ttl=300
    )
    return token


@pytest.fixture
def pre_auth_token_challenge(mock_redis):
    """Generate a valid pre-auth token with challenge scope"""
    from src.utils.pre_auth_token import get_pre_auth_manager
    
    manager = get_pre_auth_manager()
    token = manager.generate_token(
        user_id="user-001",
        scope="challenge",
        ttl=300
    )
    return token


class TestEnrollEndpointIntegration:
    """Integration tests for /api/auth/v2/2fa/enroll endpoint"""
    
    def test_enroll_with_valid_preauth_token(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp, 
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test successful enrollment with valid pre-auth token"""
        response = client.post(
            '/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'secret' in data
        assert 'qr_code' in data
        assert data['secret'] == "BASE32SECRET123"
        assert data['qr_code'].startswith("data:image/png;base64,")
        
        mock_totp.generate_secret.assert_called_once()
        mock_totp.generate_qr_code.assert_called_once()
    
    def test_enroll_without_token(self, client, mock_redis, mock_supabase):
        """Test enrollment fails without pre-auth token"""
        response = client.post('/api/auth/v2/2fa/enroll')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_enroll_with_invalid_token(self, client, mock_redis, mock_supabase):
        """Test enrollment fails with invalid pre-auth token"""
        response = client.post(
            '/api/auth/v2/2fa/enroll',
            headers={'Authorization': 'Bearer invalid-token-xyz'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_enroll_with_wrong_scope(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test enrollment fails with challenge scope token"""
        response = client.post(
            '/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'scope' in data['error'].lower() or 'forbidden' in data['error'].lower()
    
    def test_enroll_already_enabled(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test enrollment fails if 2FA already enabled"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': True
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        response = client.post(
            '/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestVerifyEnrollEndpointIntegration:
    """Integration tests for /api/auth/v2/2fa/verify-enroll endpoint"""
    
    def test_verify_enroll_success(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_backup_codes,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test successful enrollment verification"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': False
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 8
        assert 'user' in data
        assert data['user']['id'] == 'user-001'
        
        assert 'Set-Cookie' in response.headers
        
        mock_totp.verify_totp.assert_called_once()
        mock_backup_codes.generate_codes.assert_called_once()
    
    def test_verify_enroll_without_token(self, client, mock_redis, mock_supabase):
        """Test verify-enroll fails without pre-auth token"""
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            json={'code': '123456'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_missing_code(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test verify-enroll fails without TOTP code"""
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_invalid_code_format(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test verify-enroll fails with invalid code format"""
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': 'invalid'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_enroll_wrong_code(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test verify-enroll fails with wrong TOTP code"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': False
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        mock_totp.verify_totp.return_value = False
        
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data


class TestChallengeEndpointIntegration:
    """Integration tests for /api/auth/v2/2fa/challenge endpoint"""
    
    def test_challenge_with_totp_success(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test successful challenge with TOTP code"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': True
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['id'] == 'user-001'
        
        assert 'Set-Cookie' in response.headers
        
        mock_totp.verify_totp.assert_called_once()
    
    def test_challenge_with_backup_code_success(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_backup_codes,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test successful challenge with backup code"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': True
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        backup_codes_mock = MagicMock()
        backup_codes_mock.data = [
            {'code_hash': 'hash1', 'is_used': False},
            {'code_hash': 'hash2', 'is_used': False}
        ]
        
        def mock_table_chain(*args, **kwargs):
            if args[0] == 'user_backup_codes':
                return MagicMock(
                    select=MagicMock(return_value=MagicMock(
                        eq=MagicMock(return_value=MagicMock(
                            execute=MagicMock(return_value=backup_codes_mock)
                        ))
                    ))
                )
            return mock_supabase.table(*args, **kwargs)
        
        mock_supabase.table.side_effect = mock_table_chain
        
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={'backup_code': 'ABCD-EFGH-IJKL-MNOP'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'backup_codes_remaining' in data
    
    def test_challenge_without_token(self, client, mock_redis, mock_supabase):
        """Test challenge fails without pre-auth token"""
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            json={'code': '123456'}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_missing_code_and_backup(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test challenge fails without code or backup_code"""
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_with_wrong_scope(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test challenge fails with enroll scope token"""
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'scope' in data['error'].lower() or 'forbidden' in data['error'].lower()


class TestScopeEnforcement:
    """Integration tests for scope enforcement across endpoints"""
    
    def test_enroll_token_cannot_call_challenge(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test that enroll-scoped token cannot call challenge endpoint"""
        response = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_token_cannot_call_enroll(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test that challenge-scoped token cannot call enroll endpoint"""
        response = client.post(
            '/api/auth/v2/2fa/enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_challenge_token_cannot_call_verify_enroll(
        self, 
        client, 
        mock_redis, 
        mock_supabase,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test that challenge-scoped token cannot call verify-enroll endpoint"""
        response = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={'code': '123456'}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data


class TestTokenSingleUse:
    """Integration tests for token single-use enforcement"""
    
    def test_enroll_token_consumed_after_verify(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_backup_codes,
        mock_get_user,
        pre_auth_token_enroll
    ):
        """Test that pre-auth token is consumed after successful verify-enroll"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': False
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        response1 = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response1.status_code == 200
        
        response2 = client.post(
            '/api/auth/v2/2fa/verify-enroll',
            headers={'Authorization': f'Bearer {pre_auth_token_enroll}'},
            json={'code': '123456'}
        )
        
        assert response2.status_code == 401
        data = json.loads(response2.data)
        assert 'error' in data
    
    def test_challenge_token_consumed_after_use(
        self, 
        client, 
        mock_redis, 
        mock_supabase, 
        mock_totp,
        mock_get_user,
        pre_auth_token_challenge
    ):
        """Test that pre-auth token is consumed after successful challenge"""
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = [{
            'user_id': 'user-001',
            'totp_secret': 'encrypted_secret',
            'is_verified': True
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = user_2fa_mock
        
        response1 = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={'code': '123456'}
        )
        
        assert response1.status_code == 200
        
        response2 = client.post(
            '/api/auth/v2/2fa/challenge',
            headers={'Authorization': f'Bearer {pre_auth_token_challenge}'},
            json={'code': '123456'}
        )
        
        assert response2.status_code == 401
        data = json.loads(response2.data)
        assert 'error' in data
