"""
Unit tests for middleware/auth_middleware.py decorator functions

Tests the JWT decorators, request handling, and error responses.
This is a security-critical component requiring comprehensive test coverage.
"""

import pytest
import jwt as pyjwt
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path
import os
from datetime import datetime, timedelta

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

class MockJsonifyResult:
    def __init__(self, data):
        self.data = data
    
    def get_json(self):
        return self.data
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __contains__(self, key):
        return key in self.data

def mock_jsonify(data):
    return MockJsonifyResult(data)

mock_flask = MagicMock()
mock_request = MagicMock()
mock_g = MagicMock()

mock_flask.request = mock_request
mock_flask.jsonify = mock_jsonify
mock_flask.g = mock_g

sys.modules['flask'] = mock_flask

sys.modules['common'] = MagicMock()
sys.modules['common.config'] = MagicMock()
sys.modules['common.config.settings'] = MagicMock()

mock_settings = MagicMock()
mock_settings.jwt_secret_key = 'test-secret-key-for-testing'
sys.modules['common.config.settings'].get_settings.return_value = mock_settings

sys.path.insert(0, str(Path(__file__).parent.parent / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src'))

from middleware import auth_middleware


def create_valid_token(user_id='user123', role='user', username='testuser'):
    """Helper to create valid JWT tokens for testing."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    return pyjwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')


def create_expired_token(user_id='user123', role='user'):
    """Helper to create expired JWT tokens for testing."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() - timedelta(hours=1),
        'iat': datetime.utcnow() - timedelta(hours=2)
    }
    return pyjwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')


class TestParseBearerToken:
    """Test _parse_bearer_token helper function."""
    
    def test_valid_bearer_token(self):
        """Test parsing valid Bearer token."""
        token, error = auth_middleware._parse_bearer_token('Bearer abc123')
        
        assert token == 'abc123'
        assert error is None
    
    def test_missing_header(self):
        """Test with missing Authorization header."""
        token, error = auth_middleware._parse_bearer_token(None)
        
        assert token is None
        assert error is not None
        assert error[1] == 401
        error_data = error[0].get_json() if hasattr(error[0], 'get_json') else error[0]
        assert 'Authorization header missing' in error_data['error']
    
    def test_invalid_format_no_bearer(self):
        """Test with invalid format (no 'Bearer' prefix)."""
        token, error = auth_middleware._parse_bearer_token('abc123')
        
        assert token is None
        assert error is not None
        assert error[1] == 401
        error_data = error[0].get_json() if hasattr(error[0], 'get_json') else error[0]
        assert 'Invalid authorization format' in error_data['error']
    
    def test_invalid_format_wrong_prefix(self):
        """Test with wrong prefix."""
        token, error = auth_middleware._parse_bearer_token('Basic abc123')
        
        assert token is None
        assert error is not None
        assert error[1] == 401
    
    def test_empty_token(self):
        """Test with empty token after Bearer."""
        token, error = auth_middleware._parse_bearer_token('Bearer ')
        
        assert token == ''
        assert error is None  # Empty string is technically valid format


class TestErrorResponseFromException:
    """Test _error_response_from_exception helper function."""
    
    def test_expired_signature_error(self):
        """Test error response for expired token."""
        error = pyjwt.ExpiredSignatureError('Token expired')
        response, status = auth_middleware._error_response_from_exception(error)
        
        assert status == 401
        response_data = response.get_json() if hasattr(response, 'get_json') else response
        assert response_data['error'] == 'Token expired'
        assert 'expired' in response_data['message'].lower()
    
    def test_invalid_token_error(self):
        """Test error response for invalid token."""
        error = pyjwt.InvalidTokenError('Invalid token')
        response, status = auth_middleware._error_response_from_exception(error)
        
        assert status == 401
        response_data = response.get_json() if hasattr(response, 'get_json') else response
        assert response_data['error'] == 'Invalid token'
        assert 'invalid' in response_data['message'].lower()
    
    def test_generic_exception(self):
        """Test error response for generic exception."""
        error = Exception('Something went wrong')
        response, status = auth_middleware._error_response_from_exception(error)
        
        assert status == 401
        response_data = response.get_json() if hasattr(response, 'get_json') else response
        assert response_data['error'] == 'Authentication failed'


class TestTryDecodeToken:
    """Test _try_decode_token helper function."""
    
    def test_valid_token(self):
        """Test decoding valid token."""
        token = create_valid_token()
        payload, error = auth_middleware._try_decode_token(token, 'test-secret-key-for-testing')
        
        assert payload is not None
        assert error is None
        assert payload['user_id'] == 'user123'
    
    def test_expired_token(self):
        """Test decoding expired token."""
        token = create_expired_token()
        payload, error = auth_middleware._try_decode_token(token, 'test-secret-key-for-testing')
        
        assert payload is None
        assert error is not None
        assert isinstance(error, pyjwt.ExpiredSignatureError)
    
    def test_invalid_token(self):
        """Test decoding invalid token."""
        payload, error = auth_middleware._try_decode_token('invalid-token', 'test-secret-key-for-testing')
        
        assert payload is None
        assert error is not None
        assert isinstance(error, pyjwt.InvalidTokenError)
    
    def test_wrong_secret(self):
        """Test decoding with wrong secret."""
        token = create_valid_token()
        payload, error = auth_middleware._try_decode_token(token, 'wrong-secret')
        
        assert payload is None
        assert error is not None


class TestDecodeJwtWithFallback:
    """Test _decode_jwt_with_fallback function."""
    
    def test_valid_authorization_header(self):
        """Test successful decode from Authorization header."""
        token = create_valid_token()
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        payload, error = auth_middleware._decode_jwt_with_fallback()
        
        assert payload is not None
        assert error is None
        assert payload['user_id'] == 'user123'
    
    def test_fallback_to_x_access_token(self):
        """Test fallback to X-Access-Token header."""
        token = create_valid_token()
        mock_request.headers = {
            'Authorization': 'Bearer invalid-token',
            'X-Access-Token': token
        }
        mock_request.cookies = {}
        
        payload, error = auth_middleware._decode_jwt_with_fallback()
        
        assert payload is not None
        assert error is None
        assert payload['user_id'] == 'user123'
    
    def test_fallback_to_cookie(self):
        """Test fallback to access_token cookie."""
        token = create_valid_token()
        mock_request.headers = {'Authorization': 'Bearer invalid-token'}
        mock_request.cookies = {'access_token': token}
        
        payload, error = auth_middleware._decode_jwt_with_fallback()
        
        assert payload is not None
        assert error is None
        assert payload['user_id'] == 'user123'
    
    def test_no_token_provided(self):
        """Test error when no token provided."""
        mock_request.headers = {}
        mock_request.cookies = {}
        
        payload, error = auth_middleware._decode_jwt_with_fallback()
        
        assert payload is None
        assert error is not None
        assert error[1] == 401
    
    def test_expired_token_no_fallback(self):
        """Test expired token with no valid fallback."""
        expired = create_expired_token()
        mock_request.headers = {'Authorization': f'Bearer {expired}'}
        mock_request.cookies = {}
        
        payload, error = auth_middleware._decode_jwt_with_fallback()
        
        assert payload is None
        assert error is not None
        assert error[1] == 401
        error_data = error[0].get_json() if hasattr(error[0], 'get_json') else error[0]
        assert 'expired' in error_data['error'].lower()


class TestJwtRequiredDecorator:
    """Test jwt_required decorator."""
    
    def test_valid_token_allows_access(self):
        """Test that valid token allows access to protected endpoint."""
        token = create_valid_token(user_id='user123', role='user', username='testuser')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.jwt_required
        def protected_endpoint():
            return {'message': 'success'}
        
        result = protected_endpoint()
        
        assert result == {'message': 'success'}
        assert hasattr(mock_request, 'current_user')
        assert mock_request.current_user['user_id'] == 'user123'
        assert mock_request.current_user['role'] == 'user'
    
    def test_missing_token_denies_access(self):
        """Test that missing token denies access."""
        mock_request.headers = {}
        mock_request.cookies = {}
        
        @auth_middleware.jwt_required
        def protected_endpoint():
            return {'message': 'success'}
        
        result = protected_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 401
    
    def test_expired_token_denies_access(self):
        """Test that expired token denies access."""
        expired = create_expired_token()
        mock_request.headers = {'Authorization': f'Bearer {expired}'}
        mock_request.cookies = {}
        
        @auth_middleware.jwt_required
        def protected_endpoint():
            return {'message': 'success'}
        
        result = protected_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 401
    
    def test_invalid_token_denies_access(self):
        """Test that invalid token denies access."""
        mock_request.headers = {'Authorization': 'Bearer invalid-token'}
        mock_request.cookies = {}
        
        @auth_middleware.jwt_required
        def protected_endpoint():
            return {'message': 'success'}
        
        result = protected_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 401
    
    def test_sets_user_context(self):
        """Test that decorator sets user context correctly."""
        token = create_valid_token(user_id='user456', role='analyst', username='analyst_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.jwt_required
        def protected_endpoint():
            return {'user': mock_request.current_user}
        
        result = protected_endpoint()
        
        assert result['user']['user_id'] == 'user456'
        assert result['user']['username'] == 'analyst_user'
        assert result['user']['role'] == 'analyst'


class TestAdminRequiredDecorator:
    """Test admin_required decorator."""
    
    def test_admin_role_allows_access(self):
        """Test that admin role allows access."""
        token = create_valid_token(user_id='admin1', role='admin', username='admin_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.admin_required
        def admin_endpoint():
            return {'message': 'admin access granted'}
        
        result = admin_endpoint()
        
        assert result == {'message': 'admin access granted'}
    
    def test_user_role_denies_access(self):
        """Test that user role denies access."""
        token = create_valid_token(user_id='user1', role='user', username='regular_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.admin_required
        def admin_endpoint():
            return {'message': 'admin access granted'}
        
        result = admin_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 403
        result_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
        assert 'Insufficient privileges' in result_data['error']
    
    def test_analyst_role_denies_access(self):
        """Test that analyst role denies access."""
        token = create_valid_token(user_id='analyst1', role='analyst', username='analyst_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.admin_required
        def admin_endpoint():
            return {'message': 'admin access granted'}
        
        result = admin_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 403
    
    def test_super_admin_chinese_role_allows_access(self):
        """Test that Chinese super admin role allows access."""
        payload = {
            'user_id': 'superadmin1',
            'username': 'superadmin',
            'role': '超級管理員',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        token = pyjwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.admin_required
        def admin_endpoint():
            return {'message': 'admin access granted'}
        
        result = admin_endpoint()
        
        assert result == {'message': 'admin access granted'}
    
    def test_missing_token_denies_access(self):
        """Test that missing token denies access."""
        mock_request.headers = {}
        mock_request.cookies = {}
        
        @auth_middleware.admin_required
        def admin_endpoint():
            return {'message': 'admin access granted'}
        
        result = admin_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 401


class TestAnalystRequiredDecorator:
    """Test analyst_required decorator."""
    
    def test_analyst_role_allows_access(self):
        """Test that analyst role allows access."""
        token = create_valid_token(user_id='analyst1', role='analyst', username='analyst_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.analyst_required
        def analyst_endpoint():
            return {'message': 'analyst access granted'}
        
        result = analyst_endpoint()
        
        assert result == {'message': 'analyst access granted'}
    
    def test_admin_role_allows_access(self):
        """Test that admin role allows access (higher privilege)."""
        token = create_valid_token(user_id='admin1', role='admin', username='admin_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.analyst_required
        def analyst_endpoint():
            return {'message': 'analyst access granted'}
        
        result = analyst_endpoint()
        
        assert result == {'message': 'analyst access granted'}
    
    def test_user_role_denies_access(self):
        """Test that user role denies access."""
        token = create_valid_token(user_id='user1', role='user', username='regular_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.analyst_required
        def analyst_endpoint():
            return {'message': 'analyst access granted'}
        
        result = analyst_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 403
        result_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
        assert 'Insufficient privileges' in result_data['error']
    
    def test_chinese_analyst_role_allows_access(self):
        """Test that Chinese analyst role allows access."""
        payload = {
            'user_id': 'analyst1',
            'username': 'analyst',
            'role': '分析師',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        token = pyjwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.analyst_required
        def analyst_endpoint():
            return {'message': 'analyst access granted'}
        
        result = analyst_endpoint()
        
        assert result == {'message': 'analyst access granted'}


class TestRolesRequiredDecorator:
    """Test roles_required decorator."""
    
    def test_single_role_match(self):
        """Test with single matching role."""
        token = create_valid_token(user_id='admin1', role='admin', username='admin_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.roles_required('admin')
        def protected_endpoint():
            return {'message': 'access granted'}
        
        result = protected_endpoint()
        
        assert result == {'message': 'access granted'}
    
    def test_multiple_roles_one_matches(self):
        """Test with multiple allowed roles, one matches."""
        token = create_valid_token(user_id='analyst1', role='analyst', username='analyst_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.roles_required('admin', 'analyst', 'user')
        def protected_endpoint():
            return {'message': 'access granted'}
        
        result = protected_endpoint()
        
        assert result == {'message': 'access granted'}
    
    def test_no_role_match_denies_access(self):
        """Test that non-matching role denies access."""
        token = create_valid_token(user_id='user1', role='user', username='regular_user')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.roles_required('admin', 'analyst')
        def protected_endpoint():
            return {'message': 'access granted'}
        
        result = protected_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 403
        result_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
        assert 'Insufficient privileges' in result_data['error']
        assert 'admin' in result_data['message']
        assert 'analyst' in result_data['message']
    
    def test_super_admin_bypasses_role_check(self):
        """Test that super admin bypasses role requirements."""
        payload = {
            'user_id': 'superadmin1',
            'username': 'superadmin',
            'role': '超級管理員',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        token = pyjwt.encode(payload, 'test-secret-key-for-testing', algorithm='HS256')
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.cookies = {}
        
        @auth_middleware.roles_required('some_specific_role')
        def protected_endpoint():
            return {'message': 'access granted'}
        
        result = protected_endpoint()
        
        assert result == {'message': 'access granted'}
    
    def test_missing_token_denies_access(self):
        """Test that missing token denies access."""
        mock_request.headers = {}
        mock_request.cookies = {}
        
        @auth_middleware.roles_required('admin')
        def protected_endpoint():
            return {'message': 'access granted'}
        
        result = protected_endpoint()
        
        assert isinstance(result, tuple)
        assert result[1] == 401


class TestExtractJwtFromRequest:
    """Test _extract_jwt_from_request function."""
    
    def test_extract_from_authorization_header(self):
        """Test extracting token from Authorization header."""
        mock_request.headers = {'Authorization': 'Bearer test-token-123'}
        mock_request.cookies = {}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'test-token-123'
        assert error is None
    
    def test_extract_from_x_access_token_header(self):
        """Test extracting token from X-Access-Token header."""
        mock_request.headers = {'X-Access-Token': 'test-token-456'}
        mock_request.cookies = {}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'test-token-456'
        assert error is None
    
    def test_extract_from_cookie(self):
        """Test extracting token from cookie."""
        mock_request.headers = {}
        mock_request.cookies = {'access_token': 'test-token-789'}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'test-token-789'
        assert error is None
    
    def test_priority_authorization_over_header(self):
        """Test that Authorization header has priority over X-Access-Token."""
        mock_request.headers = {
            'Authorization': 'Bearer priority-token',
            'X-Access-Token': 'fallback-token'
        }
        mock_request.cookies = {}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'priority-token'
        assert error is None
    
    def test_priority_header_over_cookie(self):
        """Test that X-Access-Token has priority over cookie."""
        mock_request.headers = {'X-Access-Token': 'header-token'}
        mock_request.cookies = {'access_token': 'cookie-token'}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'header-token'
        assert error is None
    
    def test_fallback_on_invalid_authorization(self):
        """Test fallback to X-Access-Token when Authorization is invalid."""
        mock_request.headers = {
            'Authorization': 'InvalidFormat',
            'X-Access-Token': 'valid-token'
        }
        mock_request.cookies = {}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token == 'valid-token'
        assert error is None
    
    def test_no_token_returns_error(self):
        """Test that missing all token sources returns error."""
        mock_request.headers = {}
        mock_request.cookies = {}
        
        token, error = auth_middleware._extract_jwt_from_request()
        
        assert token is None
        assert error is not None
        assert error[1] == 401


class TestDecoratorFunctionMetadata:
    """Test that decorators preserve function metadata."""
    
    def test_jwt_required_preserves_name(self):
        """Test that jwt_required preserves function name."""
        @auth_middleware.jwt_required
        def my_endpoint():
            """My endpoint docstring."""
            return {'result': 'ok'}
        
        assert my_endpoint.__name__ == 'my_endpoint'
        assert my_endpoint.__doc__ == 'My endpoint docstring.'
    
    def test_admin_required_preserves_name(self):
        """Test that admin_required preserves function name."""
        @auth_middleware.admin_required
        def admin_endpoint():
            """Admin endpoint docstring."""
            return {'result': 'ok'}
        
        assert admin_endpoint.__name__ == 'admin_endpoint'
        assert admin_endpoint.__doc__ == 'Admin endpoint docstring.'
    
    def test_roles_required_preserves_name(self):
        """Test that roles_required preserves function name."""
        @auth_middleware.roles_required('admin', 'analyst')
        def role_endpoint():
            """Role endpoint docstring."""
            return {'result': 'ok'}
        
        assert role_endpoint.__name__ == 'role_endpoint'
        assert role_endpoint.__doc__ == 'Role endpoint docstring.'
