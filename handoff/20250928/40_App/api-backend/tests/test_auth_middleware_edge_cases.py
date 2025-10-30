"""
Comprehensive tests for auth_middleware edge cases and error paths
Focus on improving coverage for exception handling and edge cases
"""
import pytest
import jwt
import os
from datetime import datetime, timedelta, UTC
from flask import Flask
from src.middleware.auth_middleware import (
    jwt_required,
    admin_required,
    analyst_required,
    roles_required,
    normalize_role,
    generate_jwt_token,
    create_admin_token,
    create_analyst_token,
    create_user_token
)


@pytest.fixture
def jwt_secret(monkeypatch):
    """Pin JWT_SECRET_KEY for consistent testing"""
    test_secret = 'test-secret-key-for-testing'
    monkeypatch.setenv('JWT_SECRET_KEY', test_secret)
    return test_secret


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/test')
    @jwt_required
    def test_endpoint():
        from flask import request
        return {
            'message': 'success',
            'user_id': request.current_user.get('user_id'),
            'role': request.current_user.get('role')
        }, 200
    
    @app.route('/admin')
    @admin_required
    def admin_endpoint():
        from flask import request
        return {
            'message': 'admin success',
            'user_id': request.current_user.get('user_id'),
            'role': request.current_user.get('role')
        }, 200
    
    @app.route('/analyst')
    @analyst_required
    def analyst_endpoint():
        from flask import request
        return {
            'message': 'analyst success',
            'user_id': request.current_user.get('user_id'),
            'role': request.current_user.get('role')
        }, 200
    
    @app.route('/roles')
    @roles_required('admin', 'analyst')
    def roles_endpoint():
        from flask import request
        return {
            'message': 'roles success',
            'user_id': request.current_user.get('user_id'),
            'role': request.current_user.get('role')
        }, 200
    
    @app.route('/analyst-only')
    @roles_required('analyst')
    def analyst_only_endpoint():
        from flask import request
        return {
            'message': 'analyst only success',
            'user_id': request.current_user.get('user_id'),
            'role': request.current_user.get('role')
        }, 200
    
    return app


class TestJWTRequiredExceptions:
    """Test exception handling in jwt_required decorator"""
    
    def test_generic_exception_handling(self, app):
        """Test generic Exception catch block in jwt_required"""
        client = app.test_client()
        
        malformed_token = "not.a.valid.jwt.token.structure"
        
        response = client.get('/test', headers={
            'Authorization': f'Bearer {malformed_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] in ['Invalid token', 'Authentication failed']


class TestAdminRequiredExceptions:
    """Test exception handling in admin_required decorator"""
    
    def test_admin_required_expired_token(self, app):
        """Test admin_required with expired token"""
        client = app.test_client()
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        expired_payload = {
            'user_id': 1,
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.now(UTC) - timedelta(hours=1),
            'iat': datetime.now(UTC) - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/admin', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Token expired'
    
    def test_admin_required_invalid_token(self, app):
        """Test admin_required with invalid token"""
        client = app.test_client()
        
        wrong_token = jwt.encode({'user_id': 1, 'role': 'admin'}, 'wrong-secret', algorithm='HS256')
        
        response = client.get('/admin', headers={
            'Authorization': f'Bearer {wrong_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid token'
    
    def test_admin_required_generic_exception(self, app):
        """Test admin_required generic exception handling"""
        client = app.test_client()
        
        response = client.get('/admin', headers={
            'Authorization': 'Bearer malformed.token'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data


class TestAnalystRequiredExceptions:
    """Test exception handling in analyst_required decorator"""
    
    def test_analyst_required_expired_token(self, app):
        """Test analyst_required with expired token"""
        client = app.test_client()
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        expired_payload = {
            'user_id': 2,
            'username': 'analyst',
            'role': 'analyst',
            'exp': datetime.now(UTC) - timedelta(hours=1),
            'iat': datetime.now(UTC) - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/analyst', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Token expired'
    
    def test_analyst_required_invalid_token(self, app):
        """Test analyst_required with invalid token"""
        client = app.test_client()
        
        wrong_token = jwt.encode({'user_id': 2, 'role': 'analyst'}, 'wrong-secret', algorithm='HS256')
        
        response = client.get('/analyst', headers={
            'Authorization': f'Bearer {wrong_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid token'
    
    def test_analyst_required_generic_exception(self, app):
        """Test analyst_required generic exception handling"""
        client = app.test_client()
        
        response = client.get('/analyst', headers={
            'Authorization': 'Bearer malformed.token'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_analyst_required_missing_auth_header(self, app):
        """Test analyst_required without authorization header"""
        client = app.test_client()
        
        response = client.get('/analyst')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authorization header missing'
    
    def test_analyst_required_invalid_auth_format(self, app):
        """Test analyst_required with invalid authorization format"""
        client = app.test_client()
        
        response = client.get('/analyst', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid authorization format'


class TestRolesRequiredExceptions:
    """Test exception handling in roles_required decorator"""
    
    def test_roles_required_expired_token(self, app):
        """Test roles_required with expired token"""
        client = app.test_client()
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        expired_payload = {
            'user_id': 1,
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.now(UTC) - timedelta(hours=1),
            'iat': datetime.now(UTC) - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Token expired'
    
    def test_roles_required_invalid_token(self, app):
        """Test roles_required with invalid token"""
        client = app.test_client()
        
        wrong_token = jwt.encode({'user_id': 1, 'role': 'admin'}, 'wrong-secret', algorithm='HS256')
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {wrong_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid token'
    
    def test_roles_required_generic_exception(self, app):
        """Test roles_required generic exception handling"""
        client = app.test_client()
        
        response = client.get('/roles', headers={
            'Authorization': 'Bearer malformed.token'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_roles_required_missing_auth_header(self, app):
        """Test roles_required without authorization header"""
        client = app.test_client()
        
        response = client.get('/roles')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authorization header missing'
    
    def test_roles_required_invalid_auth_format(self, app):
        """Test roles_required with invalid authorization format"""
        client = app.test_client()
        
        response = client.get('/roles', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid authorization format'


class TestNormalizeRole:
    """Test normalize_role function edge cases"""
    
    def test_normalize_chinese_roles(self):
        """Test normalization of Chinese role names"""
        assert normalize_role('超級管理員') == 'admin'
        assert normalize_role('分析師') == 'analyst'
        assert normalize_role('操作員') == 'analyst'
        assert normalize_role('查看者') == 'user'
    
    def test_normalize_legacy_roles(self):
        """Test normalization of legacy role names"""
        assert normalize_role('operator') == 'analyst'
        assert normalize_role('viewer') == 'user'
    
    def test_normalize_unknown_role(self):
        """Test normalization of unknown role returns original"""
        assert normalize_role('unknown_role') == 'unknown_role'
        assert normalize_role('custom_role') == 'custom_role'


class TestTokenGeneration:
    """Test token generation functions"""
    
    def test_generate_jwt_token_with_role_normalization(self):
        """Test generate_jwt_token normalizes roles"""
        user_data = {
            'id': 1,
            'username': 'test',
            'role': 'operator'  # Legacy role
        }
        
        token = generate_jwt_token(user_data)
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        assert payload['role'] == 'analyst'  # Normalized
    
    def test_generate_jwt_token_custom_expiry(self):
        """Test generate_jwt_token with custom expiry"""
        user_data = {
            'id': 1,
            'username': 'test',
            'role': 'user'
        }
        
        token = generate_jwt_token(user_data, expires_hours=1)
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        exp_time = datetime.fromtimestamp(payload['exp'], UTC)
        now = datetime.now(UTC)
        time_diff = (exp_time - now).total_seconds()
        
        assert 3500 < time_diff < 3700  # ~1 hour (with some tolerance)
    
    def test_create_admin_token_custom_params(self):
        """Test create_admin_token with custom user_id and username"""
        token = create_admin_token(user_id=999, username='custom_admin')
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        assert payload['user_id'] == 999
        assert payload['username'] == 'custom_admin'
        assert payload['role'] == 'admin'
    
    def test_create_analyst_token(self):
        """Test create_analyst_token"""
        token = create_analyst_token()
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        assert payload['user_id'] == 2
        assert payload['username'] == 'analyst'
        assert payload['role'] == 'analyst'
    
    def test_create_user_token(self):
        """Test create_user_token"""
        token = create_user_token()
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        
        assert payload['user_id'] == 3
        assert payload['username'] == 'user'
        assert payload['role'] == 'user'


class TestP0RequiredTests:
    """P0 - Must complete before merge"""
    
    def test_jwt_required_missing_authorization_header(self, app, jwt_secret):
        """Test jwt_required: missing Authorization header"""
        client = app.test_client()
        
        response = client.get('/test')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authorization header missing'
        assert 'Access denied' in data['message']
    
    def test_jwt_required_invalid_authorization_format(self, app, jwt_secret):
        """Test jwt_required: invalid authorization format"""
        client = app.test_client()
        
        response = client.get('/test', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid authorization format'
        assert 'Bearer' in data['message']
    
    def test_admin_required_missing_authorization_header(self, app, jwt_secret):
        """Test admin_required: missing Authorization header"""
        client = app.test_client()
        
        response = client.get('/admin')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Authorization header missing'
    
    def test_admin_required_invalid_authorization_format(self, app, jwt_secret):
        """Test admin_required: invalid authorization format"""
        client = app.test_client()
        
        response = client.get('/admin', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid authorization format'
    
    def test_admin_required_user_role_returns_403(self, app, jwt_secret):
        """Test admin_required: valid token with role='user' → 403"""
        client = app.test_client()
        
        user_token = create_user_token()
        
        response = client.get('/admin', headers={
            'Authorization': f'Bearer {user_token}'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Insufficient privileges'
        assert 'Admin access required' in data['message']
    
    def test_analyst_required_user_role_returns_403(self, app, jwt_secret):
        """Test analyst_required: valid token with role='user' → 403"""
        client = app.test_client()
        
        user_token = create_user_token()
        
        response = client.get('/analyst', headers={
            'Authorization': f'Bearer {user_token}'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Insufficient privileges'
        assert 'Analyst access' in data['message']
    
    def test_roles_required_user_role_returns_403(self, app, jwt_secret):
        """Test roles_required: valid token with role='user' → 403"""
        client = app.test_client()
        
        user_token = create_user_token()
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {user_token}'
        })
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['error'] == 'Insufficient privileges'
        assert 'Access denied' in data['message']
    
    def test_jwt_required_happy_path(self, app, jwt_secret):
        """Test jwt_required: Happy-path (200 + request.current_user)"""
        client = app.test_client()
        
        user_token = create_user_token()
        
        response = client.get('/test', headers={
            'Authorization': f'Bearer {user_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'success'
        assert data['user_id'] == 3
        assert data['role'] == 'user'
    
    def test_admin_required_happy_path(self, app, jwt_secret):
        """Test admin_required: Happy-path (200 + request.current_user)"""
        client = app.test_client()
        
        admin_token = create_admin_token()
        
        response = client.get('/admin', headers={
            'Authorization': f'Bearer {admin_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'admin success'
        assert data['user_id'] == 1
        assert data['role'] == 'admin'
    
    def test_analyst_required_happy_path(self, app, jwt_secret):
        """Test analyst_required: Happy-path (200 + request.current_user)"""
        client = app.test_client()
        
        analyst_token = create_analyst_token()
        
        response = client.get('/analyst', headers={
            'Authorization': f'Bearer {analyst_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'analyst success'
        assert data['user_id'] == 2
        assert data['role'] == 'analyst'
    
    def test_roles_required_happy_path_admin(self, app, jwt_secret):
        """Test roles_required: Happy-path with admin role (200 + request.current_user)"""
        client = app.test_client()
        
        admin_token = create_admin_token()
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {admin_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'roles success'
        assert data['user_id'] == 1
        assert data['role'] == 'admin'
    
    def test_roles_required_happy_path_analyst(self, app, jwt_secret):
        """Test roles_required: Happy-path with analyst role (200 + request.current_user)"""
        client = app.test_client()
        
        analyst_token = create_analyst_token()
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {analyst_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'roles success'
        assert data['user_id'] == 2
        assert data['role'] == 'analyst'


class TestP1RecommendedTests:
    """P1 - Recommended before merge"""
    
    def test_roles_required_super_admin_bypass(self, app, jwt_secret):
        """Test roles_required: '超級管理員' bypass behavior
        
        This test verifies that a token with Chinese role '超級管理員' 
        (Super Admin) can bypass role restrictions and access endpoints.
        The token contains the Chinese role name directly, not normalized.
        """
        client = app.test_client()
        
        payload = {
            'user_id': 999,
            'username': 'super_admin',
            'role': '超級管理員',  # Chinese role name in token
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        super_admin_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {super_admin_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'roles success'
        assert data['user_id'] == 999
        assert data['role'] == 'admin'
    
    def test_roles_required_chinese_analyst_normalized(self, app, jwt_secret):
        """Test roles_required: '分析師' normalized to 'analyst'
        
        This test verifies that a token with Chinese role '分析師' 
        (Analyst) is normalized to 'analyst' and can access analyst endpoints.
        The token contains the Chinese role name directly, not normalized.
        """
        client = app.test_client()
        
        payload = {
            'user_id': 888,
            'username': 'chinese_analyst',
            'role': '分析師',  # Chinese role name in token
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        analyst_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/roles', headers={
            'Authorization': f'Bearer {analyst_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'roles success'
        assert data['user_id'] == 888
        # The middleware normalizes '分析師' to 'analyst'
        assert data['role'] == 'analyst'
    
    def test_super_admin_bypass_truly_bypasses(self, app, jwt_secret):
        """Test that '超級管理員' truly bypasses role restrictions
        
        This test verifies that a super admin with Chinese role '超級管理員'
        can access analyst-only endpoints even though they are not in the
        allowed_roles list. This tests the bypass logic fix.
        
        Before fix: Would fail because normalized_role was checked
        After fix: Should pass because original user_role is checked
        """
        client = app.test_client()
        
        payload = {
            'user_id': 999,
            'username': 'super_admin',
            'role': '超級管理員',  # Chinese super admin role
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        super_admin_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/analyst-only', headers={
            'Authorization': f'Bearer {super_admin_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'analyst only success'
        assert data['user_id'] == 999
        assert data['role'] == 'admin'
