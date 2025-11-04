"""
Integration tests for TOTP API endpoints.

Tests the Flask API routes for 2FA/TOTP functionality including:
- TOTP setup
- TOTP verification
- TOTP status
- Error handling
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app


@pytest.fixture
def client():
    """Create Flask test client with application context."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_user_id():
    """Mock user ID for testing."""
    return "test-user-123"


@pytest.fixture
def auth_headers(mock_user_id):
    """Generate valid JWT authentication headers."""
    from src.middleware.auth_middleware import create_admin_token
    token = create_admin_token(user_id=mock_user_id, username='testuser')
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_jwt_decode(monkeypatch, mock_user_id):
    """Mock JWT decode to bypass authentication in tests."""
    def fake_decode(token, secret, algorithms):
        return {
            'user_id': mock_user_id,
            'sub': mock_user_id,
            'username': 'testuser',
            'role': 'admin'
        }
    
    monkeypatch.setattr('src.middleware.auth_middleware.jwt.decode', fake_decode)


@pytest.fixture(autouse=True)
def enable_2fa_feature(monkeypatch):
    """Enable 2FA feature flag for all tests."""
    monkeypatch.setenv('FEATURE_2FA_ENABLED', 'true')


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('src.routes.totp.create_client') as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{}]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
        
        yield mock_client


class TestTOTPSetup:
    """Test TOTP setup endpoint."""
    
    @patch('src.routes.totp.get_totp_manager')
    @patch('src.routes.totp.get_backup_manager')
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.check_password_hash')
    def test_setup_totp_success(self, mock_check_password, mock_get_user, mock_backup_manager, mock_totp_manager, client, mock_supabase, mock_user_id):
        """Test successful TOTP setup."""
        mock_totp = MagicMock()
        mock_totp.generate_secret.return_value = 'TEST_SECRET_BASE32'
        mock_totp.encrypt_secret.return_value = 'ENCRYPTED_SECRET'
        mock_totp.generate_qr_code.return_value = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        mock_totp_manager.return_value = mock_totp
        
        mock_backup = MagicMock()
        mock_backup.generate_backup_codes.return_value = ['CODE1-CODE1-CODE1-CODE1', 'CODE2-CODE2-CODE2-CODE2', 'CODE3-CODE3-CODE3-CODE3', 'CODE4-CODE4-CODE4-CODE4', 'CODE5-CODE5-CODE5-CODE5', 'CODE6-CODE6-CODE6-CODE6', 'CODE7-CODE7-CODE7-CODE7', 'CODE8-CODE8-CODE8-CODE8']
        mock_backup.hash_backup_code.return_value = 'HASHED_CODE'
        mock_backup_manager.return_value = mock_backup
        
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com',
            'password_hash': 'hashed_password'
        }
        mock_check_password.return_value = True
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            '/api/auth/v2/totp/setup',
            json={'password': 'correct_password'},
            headers={'Authorization': 'Bearer mock-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'secret' in data
        assert 'qr_code' in data
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 8
        assert data['qr_code'].startswith('data:image/png;base64,')
    
    @patch('src.routes.totp.get_user_by_id')
    def test_setup_totp_missing_password(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test TOTP setup with missing password."""
        response = client.post(
            '/api/auth/v2/totp/setup',
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Password confirmation required' in data['error']
    
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.check_password_hash')
    def test_setup_totp_invalid_password(self, mock_check_password, mock_get_user, client, mock_user_id, auth_headers):
        """Test TOTP setup with invalid password."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com',
            'password_hash': 'hashed_password'
        }
        mock_check_password.return_value = False
        
        response = client.post(
            '/api/auth/v2/totp/setup',
            json={'password': 'wrong_password'},
            headers=auth_headers
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid password' in data['error']


class TestTOTPVerifySetup:
    """Test TOTP verification endpoint."""
    
    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_invalid_code_format(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test TOTP verification with invalid code format."""
        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': 'ABCDEF'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid TOTP code format' in data['error']
    
    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_wrong_length(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test TOTP verification with wrong code length."""
        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '12345'},  # Only 5 digits
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_not_setup(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test TOTP verification when 2FA not set up."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '123456'},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '2FA not set up' in data['error']


class TestTOTPStatus:
    """Test TOTP status endpoint."""
    
    def test_get_status_not_enabled(self, client, mock_supabase, mock_user_id, auth_headers):
        """Test getting status when 2FA not enabled."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.get(
            '/api/auth/v2/totp/status',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['enabled'] is False
        assert data['verified_at'] is None
        assert data['backup_codes_remaining'] == 0
    
    def test_get_status_enabled(self, client, mock_supabase, mock_user_id, auth_headers):
        """Test getting status when 2FA is enabled."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True,
            'verified_at': '2025-11-03T12:00:00'
        }]
        
        backup_codes_response = MagicMock()
        backup_codes_response.data = [{'id': 1}, {'id': 2}, {'id': 3}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = backup_codes_response
        
        response = client.get(
            '/api/auth/v2/totp/status',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['enabled'] is True
        assert data['verified_at'] == '2025-11-03T12:00:00'
        assert data['backup_codes_remaining'] == 3


class TestTOTPUtilityFunctions:
    """Test TOTP utility functions used by routes."""
    
    @patch('src.routes.totp.get_totp_manager')
    def test_verify_totp_for_login_success(self, mock_totp_manager, mock_supabase):
        """Test successful TOTP verification for login."""
        from src.routes.totp import verify_totp_for_login
        
        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = True
        mock_totp_manager.return_value = mock_manager
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'secret_encrypted': 'encrypted_secret'
        }]
        
        result = verify_totp_for_login('user-123', '123456')
        
        assert result is True
        mock_manager.verify_totp.assert_called_once_with('TEST_SECRET', '123456', valid_window=1)
    
    @patch('src.routes.totp.get_totp_manager')
    def test_verify_totp_for_login_invalid_code(self, mock_totp_manager, mock_supabase):
        """Test TOTP verification with invalid code."""
        from src.routes.totp import verify_totp_for_login
        
        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = False
        mock_totp_manager.return_value = mock_manager
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
            'secret_encrypted': 'encrypted_secret'
        }]
        
        result = verify_totp_for_login('user-123', '999999')
        
        assert result is False
    
    def test_check_2fa_required_enabled(self, mock_supabase):
        """Test checking if 2FA is required when enabled."""
        from src.routes.totp import check_2fa_required
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True
        }]
        
        result = check_2fa_required('user-123')
        
        assert result is True
    
    def test_check_2fa_required_disabled(self, mock_supabase):
        """Test checking if 2FA is required when disabled."""
        from src.routes.totp import check_2fa_required
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': False
        }]
        
        result = check_2fa_required('user-123')
        
        assert result is False


class TestTOTPEdgeCases:
    """Test edge cases and error handling."""
    
    @patch('src.routes.totp.get_user_by_id')
    def test_setup_user_not_found(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test TOTP setup when user not found."""
        mock_get_user.return_value = None
        
        response = client.post(
            '/api/auth/v2/totp/setup',
            json={'password': 'password'},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'User not found' in data['error']
    
    def test_verify_setup_empty_code(self, client, mock_user_id, auth_headers):
        """Test TOTP verification with empty code."""
        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': ''},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
