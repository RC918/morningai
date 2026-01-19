"""
Comprehensive tests for TOTP routes to achieve 80% coverage.

This test file covers:
- validate_and_consume_preauth_token function
- disable_totp endpoint
- regenerate_backup_codes endpoint
- verify_backup_code_for_login function
- check_2fa_required with owner role
- verify_totp_login endpoint (full flow)
- Error paths and edge cases

Fixes #4225
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
    monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'true')


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


class TestValidateAndConsumePreAuthToken:
    """Test validate_and_consume_preauth_token function."""

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_valid_token_consumed_successfully(self, mock_get_manager):
        """Test successful token validation and consumption."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'scope': 'challenge',
            'jti': 'token-jti-123'
        }
        mock_manager.consume_token_atomic.return_value = True
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('valid-token')

        assert result is not None
        assert result['id'] == 'user-123'
        assert result['email'] == 'test@example.com'
        mock_manager.consume_token_atomic.assert_called_once_with('token-jti-123')

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_invalid_token_returns_none(self, mock_get_manager):
        """Test invalid token returns None."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.return_value = None
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('invalid-token')

        assert result is None

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_wrong_scope_returns_none(self, mock_get_manager):
        """Test token with wrong scope returns None."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'scope': 'login',
            'jti': 'token-jti-123'
        }
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('wrong-scope-token')

        assert result is None

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_missing_jti_returns_none(self, mock_get_manager):
        """Test token without jti returns None."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'scope': 'challenge'
        }
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('no-jti-token')

        assert result is None

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_consume_failure_returns_none(self, mock_get_manager):
        """Test failed token consumption returns None."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'scope': 'challenge',
            'jti': 'token-jti-123'
        }
        mock_manager.consume_token_atomic.return_value = False
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('already-consumed-token')

        assert result is None

    @patch('src.routes.totp.get_pre_auth_manager')
    def test_exception_returns_none(self, mock_get_manager):
        """Test exception during validation returns None."""
        from src.routes.totp import validate_and_consume_preauth_token

        mock_manager = MagicMock()
        mock_manager.verify_token.side_effect = Exception("Token verification failed")
        mock_get_manager.return_value = mock_manager

        result = validate_and_consume_preauth_token('error-token')

        assert result is None


class TestDisableTOTP:
    """Test disable_totp endpoint."""

    @patch('src.routes.totp.get_totp_manager')
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_disable_totp_success(self, mock_authenticate, mock_get_user, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test successful TOTP disable."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = True
        mock_totp_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True,
            'secret_encrypted': 'encrypted_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'correct_password', 'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['enabled'] is False

    @patch('src.routes.totp.get_user_by_id')
    def test_disable_totp_missing_password(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test disable TOTP with missing password."""
        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.totp.get_user_by_id')
    def test_disable_totp_missing_totp_code(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test disable TOTP with missing TOTP code."""
        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.totp.get_user_by_id')
    def test_disable_totp_invalid_code_format(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test disable TOTP with invalid code format."""
        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password', 'totp_code': 'ABCDEF'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.totp.get_user_by_id')
    def test_disable_totp_user_not_found(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test disable TOTP when user not found."""
        mock_get_user.return_value = None

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password', 'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'User not found' in data['error']

    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_disable_totp_invalid_password(self, mock_authenticate, mock_get_user, client, mock_user_id, auth_headers):
        """Test disable TOTP with invalid password."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = None

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'wrong_password', 'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid password' in data['error']

    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_disable_totp_not_enabled(self, mock_authenticate, mock_get_user, client, mock_supabase, mock_user_id, auth_headers):
        """Test disable TOTP when 2FA is not enabled."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password', 'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '2FA is not enabled' in data['error']

    @patch('src.routes.totp.get_totp_manager')
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_disable_totp_invalid_totp_code(self, mock_authenticate, mock_get_user, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test disable TOTP with invalid TOTP code."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = False
        mock_totp_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True,
            'secret_encrypted': 'encrypted_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password', 'totp_code': '999999'},
            headers=auth_headers
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid TOTP code' in data['error']


class TestRegenerateBackupCodes:
    """Test regenerate_backup_codes endpoint."""

    @patch('src.routes.totp.get_backup_manager')
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_regenerate_backup_codes_success(self, mock_authenticate, mock_get_user, mock_backup_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test successful backup codes regeneration."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_manager = MagicMock()
        mock_manager.generate_backup_codes.return_value = [
            'CODE1-CODE1-CODE1-CODE1',
            'CODE2-CODE2-CODE2-CODE2',
            'CODE3-CODE3-CODE3-CODE3',
            'CODE4-CODE4-CODE4-CODE4',
            'CODE5-CODE5-CODE5-CODE5',
            'CODE6-CODE6-CODE6-CODE6',
            'CODE7-CODE7-CODE7-CODE7',
            'CODE8-CODE8-CODE8-CODE8'
        ]
        mock_manager.hash_backup_code.return_value = 'HASHED_CODE'
        mock_backup_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True
        }]

        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={'password': 'correct_password'},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'backup_codes' in data
        assert len(data['backup_codes']) == 8

    @patch('src.routes.totp.get_user_by_id')
    def test_regenerate_backup_codes_missing_password(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test regenerate backup codes with missing password."""
        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Password confirmation required' in data['error']

    @patch('src.routes.totp.get_user_by_id')
    def test_regenerate_backup_codes_user_not_found(self, mock_get_user, client, mock_user_id, auth_headers):
        """Test regenerate backup codes when user not found."""
        mock_get_user.return_value = None

        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={'password': 'password'},
            headers=auth_headers
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'User not found' in data['error']

    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_regenerate_backup_codes_invalid_password(self, mock_authenticate, mock_get_user, client, mock_user_id, auth_headers):
        """Test regenerate backup codes with invalid password."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = None

        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={'password': 'wrong_password'},
            headers=auth_headers
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid password' in data['error']

    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_regenerate_backup_codes_2fa_not_enabled(self, mock_authenticate, mock_get_user, client, mock_supabase, mock_user_id, auth_headers):
        """Test regenerate backup codes when 2FA is not enabled."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={'password': 'password'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '2FA is not enabled' in data['error']


class TestVerifyBackupCodeForLogin:
    """Test verify_backup_code_for_login function."""

    @patch('src.routes.totp.get_backup_manager')
    def test_verify_backup_code_success(self, mock_backup_manager, mock_supabase):
        """Test successful backup code verification."""
        from src.routes.totp import verify_backup_code_for_login

        mock_manager = MagicMock()
        mock_manager.verify_backup_code.return_value = True
        mock_backup_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {'code_hash': 'hash1', 'used': False},
            {'code_hash': 'hash2', 'used': False}
        ]

        is_valid, remaining = verify_backup_code_for_login('user-123', 'ABCD-EFGH-IJKL-MNOP')

        assert is_valid is True

    @patch('src.routes.totp.get_backup_manager')
    def test_verify_backup_code_invalid(self, mock_backup_manager, mock_supabase):
        """Test invalid backup code verification."""
        from src.routes.totp import verify_backup_code_for_login

        mock_manager = MagicMock()
        mock_manager.verify_backup_code.return_value = False
        mock_backup_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {'code_hash': 'hash1', 'used': False}
        ]

        is_valid, remaining = verify_backup_code_for_login('user-123', 'INVALID-CODE')

        assert is_valid is False

    def test_verify_backup_code_no_codes_available(self, mock_supabase):
        """Test backup code verification when no codes available."""
        from src.routes.totp import verify_backup_code_for_login

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        is_valid, remaining = verify_backup_code_for_login('user-123', 'ABCD-EFGH-IJKL-MNOP')

        assert is_valid is False
        assert remaining == 0


class TestCheck2FARequiredWithOwnerRole:
    """Test check_2fa_required function with owner role."""

    @patch('src.routes.totp.get_user_by_id')
    def test_check_2fa_required_owner_role(self, mock_get_user, mock_supabase):
        """Test 2FA is always required for owner role."""
        from src.routes.totp import check_2fa_required

        result = check_2fa_required('user-123', user_role='owner')

        assert result is True

    @patch('src.routes.totp.get_user_by_id')
    def test_check_2fa_required_owner_role_fetched(self, mock_get_user, mock_supabase):
        """Test 2FA required when owner role is fetched from user."""
        from src.routes.totp import check_2fa_required

        mock_get_user.return_value = {'id': 'user-123', 'role': 'owner'}

        result = check_2fa_required('user-123')

        assert result is True

    @patch('src.routes.totp.get_user_by_id')
    def test_check_2fa_required_admin_role_enabled(self, mock_get_user, mock_supabase):
        """Test 2FA required for admin when explicitly enabled."""
        from src.routes.totp import check_2fa_required

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True
        }]

        result = check_2fa_required('user-123', user_role='admin')

        assert result is True

    @patch('src.routes.totp.get_user_by_id')
    def test_check_2fa_required_admin_role_disabled(self, mock_get_user, mock_supabase):
        """Test 2FA not required for admin when disabled."""
        from src.routes.totp import check_2fa_required

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': False
        }]

        result = check_2fa_required('user-123', user_role='admin')

        assert result is False

    @patch('src.routes.totp.get_user_by_id')
    def test_check_2fa_required_no_2fa_record(self, mock_get_user, mock_supabase):
        """Test 2FA not required when no 2FA record exists."""
        from src.routes.totp import check_2fa_required

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        result = check_2fa_required('user-123', user_role='admin')

        assert result is False


class TestVerifyTOTPLogin:
    """Test verify_totp_login endpoint."""

    @patch('src.services.auth_service.set_auth_cookies')
    @patch('src.services.auth_service.generate_refresh_token')
    @patch('src.services.auth_service.generate_access_token')
    @patch('src.routes.totp.verify_totp_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_with_email_password(self, mock_authenticate, mock_check_2fa, mock_verify_totp, mock_access, mock_refresh, mock_set_cookies, client):
        """Test TOTP login with email/password."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'admin',
            'tenant_id': 'tenant-1',
            'avatar': None
        }
        mock_check_2fa.return_value = True
        mock_verify_totp.return_value = True
        mock_access.return_value = ('access-token', 1234567890000)
        mock_refresh.return_value = 'refresh-token'

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'totp_code': '123456'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user_id'] == 'user-123'

    def test_verify_totp_login_missing_code(self, client):
        """Test TOTP login with missing code."""
        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Either TOTP code or backup code is required' in data['error']

    def test_verify_totp_login_missing_credentials(self, client):
        """Test TOTP login with missing credentials."""
        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'totp_code': '123456'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Authorization header with JWT token or email/password required' in data['error']

    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_invalid_credentials(self, mock_authenticate, client):
        """Test TOTP login with invalid credentials."""
        mock_authenticate.return_value = None

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'wrong_password',
                'totp_code': '123456'
            }
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid email or password' in data['error']

    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_2fa_not_enabled(self, mock_authenticate, mock_check_2fa, client):
        """Test TOTP login when 2FA is not enabled for user."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        mock_check_2fa.return_value = False

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'totp_code': '123456'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '2FA is not enabled for this user' in data['error']

    @patch('src.routes.totp.verify_totp_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_invalid_totp_code(self, mock_authenticate, mock_check_2fa, mock_verify_totp, client):
        """Test TOTP login with invalid TOTP code."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        mock_check_2fa.return_value = True
        mock_verify_totp.return_value = False

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'totp_code': '999999'
            }
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid TOTP code' in data['error']

    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_invalid_code_format(self, mock_authenticate, mock_check_2fa, client):
        """Test TOTP login with invalid code format."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        mock_check_2fa.return_value = True

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'totp_code': 'ABCDEF'
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid TOTP code format' in data['error']

    @patch('src.services.auth_service.set_auth_cookies')
    @patch('src.services.auth_service.generate_refresh_token')
    @patch('src.services.auth_service.generate_access_token')
    @patch('src.routes.totp.verify_backup_code_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_with_backup_code(self, mock_authenticate, mock_check_2fa, mock_verify_backup, mock_access, mock_refresh, mock_set_cookies, client):
        """Test TOTP login with backup code."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'admin',
            'tenant_id': 'tenant-1',
            'avatar': None
        }
        mock_check_2fa.return_value = True
        mock_verify_backup.return_value = (True, 7)
        mock_access.return_value = ('access-token', 1234567890000)
        mock_refresh.return_value = 'refresh-token'

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'backup_code': 'ABCD-EFGH-IJKL-MNOP'
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['backup_codes_remaining'] == 7

    @patch('src.routes.totp.verify_backup_code_for_login')
    @patch('src.routes.totp.check_2fa_required')
    @patch('src.services.auth_service.authenticate_user')
    def test_verify_totp_login_invalid_backup_code(self, mock_authenticate, mock_check_2fa, mock_verify_backup, client):
        """Test TOTP login with invalid backup code."""
        mock_authenticate.return_value = {
            'id': 'user-123',
            'email': 'test@example.com'
        }
        mock_check_2fa.return_value = True
        mock_verify_backup.return_value = (False, 8)

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'backup_code': 'INVALID-CODE'
            }
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid backup code' in data['error']


class TestIs2FAFeatureEnabled:
    """Test is_2fa_feature_enabled function."""

    def test_feature_enabled_in_production(self, monkeypatch):
        """Test 2FA feature enabled in production."""
        from src.routes.totp import is_2fa_feature_enabled

        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'true')

        result = is_2fa_feature_enabled()

        assert result is True

    def test_feature_disabled_in_production(self, monkeypatch):
        """Test 2FA feature disabled in production."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        from importlib import reload
        import src.routes.totp as totp_module
        reload(totp_module)

        result = totp_module.is_2fa_feature_enabled()

        assert result is False


class TestTOTPSetupAlreadyEnabled:
    """Test TOTP setup when already enabled."""

    @patch('src.routes.totp.get_totp_manager')
    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_setup_totp_already_enabled(self, mock_authenticate, mock_get_user, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test TOTP setup when 2FA is already enabled."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True,
            'secret_encrypted': 'existing_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/setup',
            json={'password': 'correct_password'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '2FA is already enabled' in data['error']


class TestVerifySetupAlreadyEnabled:
    """Test verify setup when already enabled."""

    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_already_enabled(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test verify setup when 2FA is already enabled."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': True,
            'secret_encrypted': 'existing_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert '2FA is already enabled' in data['error']


class TestVerifySetupSuccess:
    """Test successful verify setup."""

    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_success(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test successful TOTP verification during setup."""
        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = True
        mock_totp_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': False,
            'secret_encrypted': 'encrypted_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['enabled'] is True


class TestVerifySetupInvalidCode:
    """Test verify setup with invalid code."""

    @patch('src.routes.totp.get_totp_manager')
    def test_verify_setup_invalid_code(self, mock_totp_manager, client, mock_supabase, mock_user_id, auth_headers):
        """Test TOTP verification with invalid code during setup."""
        mock_manager = MagicMock()
        mock_manager.decrypt_secret.return_value = 'TEST_SECRET'
        mock_manager.verify_totp.return_value = False
        mock_totp_manager.return_value = mock_manager

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'enabled': False,
            'secret_encrypted': 'encrypted_secret'
        }]

        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '999999'},
            headers=auth_headers
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid TOTP code' in data['error']


class TestTOTPStatusException:
    """Test TOTP status with exception."""

    def test_get_status_exception(self, client, mock_user_id, auth_headers):
        """Test getting status when exception occurs."""
        with patch('src.routes.totp.create_client') as mock_create:
            mock_create.side_effect = Exception("Database error")

            response = client.get(
                '/api/auth/v2/totp/status',
                headers=auth_headers
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'Internal server error' in data['error']


class TestSetupTOTPException:
    """Test setup TOTP with exception."""

    @patch('src.routes.totp.get_user_by_id')
    @patch('src.routes.totp.authenticate_user')
    def test_setup_totp_exception(self, mock_authenticate, mock_get_user, client, mock_user_id, auth_headers):
        """Test TOTP setup when exception occurs."""
        mock_get_user.return_value = {
            'id': mock_user_id,
            'email': 'test@example.com'
        }
        mock_authenticate.return_value = {'id': mock_user_id, 'email': 'test@example.com'}

        with patch('src.routes.totp.create_client') as mock_create:
            mock_create.side_effect = Exception("Database error")

            response = client.post(
                '/api/auth/v2/totp/setup',
                json={'password': 'password'},
                headers=auth_headers
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'Internal server error' in data['error']


class TestVerifyTOTPForLoginException:
    """Test verify_totp_for_login with exception."""

    def test_verify_totp_for_login_exception(self):
        """Test TOTP verification for login when exception occurs."""
        from src.routes.totp import verify_totp_for_login

        with patch('src.routes.totp.create_client') as mock_create:
            mock_create.side_effect = Exception("Database error")

            result = verify_totp_for_login('user-123', '123456')

            assert result is False


class TestCheck2FARequiredException:
    """Test check_2fa_required with exception."""

    def test_check_2fa_required_exception(self):
        """Test 2FA requirement check when exception occurs."""
        from src.routes.totp import check_2fa_required

        with patch('src.routes.totp.create_client') as mock_create:
            mock_create.side_effect = Exception("Database error")

            result = check_2fa_required('user-123', user_role='admin')

            assert result is False


class TestVerifyBackupCodeException:
    """Test verify_backup_code_for_login with exception."""

    def test_verify_backup_code_exception(self):
        """Test backup code verification when exception occurs."""
        from src.routes.totp import verify_backup_code_for_login

        with patch('src.routes.totp.create_client') as mock_create:
            mock_create.side_effect = Exception("Database error")

            is_valid, remaining = verify_backup_code_for_login('user-123', 'ABCD-EFGH-IJKL-MNOP')

            assert is_valid is False
            assert remaining == 0


class TestFeatureDisabled:
    """Test endpoints when 2FA feature is disabled."""

    def test_setup_totp_feature_disabled(self, client, auth_headers, monkeypatch):
        """Test TOTP setup when feature is disabled."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        response = client.post(
            '/api/auth/v2/totp/setup',
            json={'password': 'password'},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert '2FA feature is not enabled' in data['error']

    def test_verify_setup_feature_disabled(self, client, auth_headers, monkeypatch):
        """Test verify setup when feature is disabled."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        response = client.post(
            '/api/auth/v2/totp/verify-setup',
            json={'code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert '2FA feature is not enabled' in data['error']

    def test_disable_totp_feature_disabled(self, client, auth_headers, monkeypatch):
        """Test disable TOTP when feature is disabled."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        response = client.post(
            '/api/auth/v2/totp/disable',
            json={'password': 'password', 'totp_code': '123456'},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert '2FA feature is not enabled' in data['error']

    def test_regenerate_backup_codes_feature_disabled(self, client, auth_headers, monkeypatch):
        """Test regenerate backup codes when feature is disabled."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        response = client.post(
            '/api/auth/v2/totp/backup-codes/regenerate',
            json={'password': 'password'},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert '2FA feature is not enabled' in data['error']

    def test_verify_login_feature_disabled(self, client, monkeypatch):
        """Test verify login when feature is disabled."""
        monkeypatch.setenv('FEATURE_2FA_ENABLED', 'false')
        monkeypatch.setenv('FORCE_ENABLE_2FA_IN_TESTS', 'false')

        response = client.post(
            '/api/auth/v2/totp/verify-login',
            json={
                'email': 'test@example.com',
                'password': 'password',
                'totp_code': '123456'
            }
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert '2FA feature is not enabled' in data['error']
