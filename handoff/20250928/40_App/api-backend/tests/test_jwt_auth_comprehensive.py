"""Comprehensive JWT authentication tests"""
import pytest
import jwt
import os
from datetime import datetime, timedelta, UTC
from flask import Flask
from unittest.mock import patch, Mock, AsyncMock
from src.routes.faq import bp as faq_bp
from src.routes.agent import bp as agent_bp
from src.routes.dashboard import dashboard_bp


@pytest.fixture
def app():
    """Create test Flask app with blueprints"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(faq_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(dashboard_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def expired_token():
    """Generate expired JWT token"""
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = {
        'user_id': 1,
        'username': 'test_user',
        'role': 'user',
        'exp': datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
        'iat': datetime.now(UTC) - timedelta(hours=2)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


@pytest.fixture
def invalid_token():
    """Generate invalid JWT token with wrong secret"""
    payload = {
        'user_id': 1,
        'username': 'test_user',
        'role': 'user',
        'exp': datetime.now(UTC) + timedelta(hours=1),
        'iat': datetime.now(UTC)
    }
    return jwt.encode(payload, 'wrong-secret', algorithm='HS256')


@pytest.fixture
def malformed_token():
    """Generate malformed token"""
    return "not.a.valid.jwt.token"


class TestJWTAuthentication:
    """Test JWT authentication for protected endpoints"""
    
    def test_missing_authorization_header(self, client):
        """Test request without Authorization header returns 401"""
        response = client.get('/api/faq/health')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Authorization header missing' in data['error']
    
    def test_invalid_authorization_format(self, client):
        """Test invalid Authorization header format returns 401"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': 'invalid-format-token'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid authorization format' in data['error']
    
    def test_expired_token(self, client, expired_token):
        """Test expired JWT token returns 401"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {expired_token}'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Token expired' in data['error']
    
    def test_invalid_token_signature(self, client, invalid_token):
        """Test token with invalid signature returns 401"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {invalid_token}'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid token' in data['error']
    
    def test_malformed_token(self, client, malformed_token):
        """Test malformed token returns 401"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {malformed_token}'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_valid_user_token(self, client, auth_headers_user):
        """Test valid user token allows access to user endpoints"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        assert response.status_code in [200, 503]  # 503 if FAQ agent not available
    
    def test_valid_admin_token(self, client, auth_headers_admin):
        """Test valid admin token allows access to admin endpoints"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_admin)
        
        assert response.status_code in [200, 503]
    
    def test_valid_analyst_token(self, client, auth_headers_analyst):
        """Test valid analyst token allows access to analyst endpoints"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_analyst)
        
        assert response.status_code in [200, 503]


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_user_cannot_access_admin_endpoint(self, client, auth_headers_user):
        """Test user role cannot access admin-only endpoints"""
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers=auth_headers_user)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'Insufficient privileges' in data['error']
    
    def test_analyst_cannot_access_admin_endpoint(self, client, auth_headers_analyst):
        """Test analyst role cannot access admin-only endpoints"""
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers=auth_headers_analyst)
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data
        assert 'Insufficient privileges' in data['error']
    
    def test_admin_can_access_admin_endpoint(self, client, auth_headers_admin):
        """Test admin role can access admin-only endpoints"""
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers=auth_headers_admin)
        
        assert response.status_code != 403
    
    def test_user_can_access_user_endpoint(self, client, auth_headers_user):
        """Test user role can access user-level endpoints"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        assert response.status_code != 403
    
    def test_analyst_can_access_analyst_endpoint(self, client, auth_headers_analyst):
        """Test analyst role can access analyst endpoints"""
        response = client.get('/api/agent/debug/queue',
                            headers=auth_headers_analyst)
        
        assert response.status_code != 403
    
    def test_admin_can_access_analyst_endpoint(self, client, auth_headers_admin):
        """Test admin role can access analyst endpoints"""
        response = client.get('/api/agent/debug/queue',
                            headers=auth_headers_admin)
        
        assert response.status_code != 403


class TestTokenPayloadHandling:
    """Test JWT token payload handling"""
    
    def test_token_with_sub_field(self, client):
        """Test token with 'sub' field for user_id"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'sub': 'user-123',  # Using 'sub' instead of 'user_id'
            'username': 'test_user',
            'role': 'user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code in [200, 503]
    
    def test_token_with_email_instead_of_username(self, client):
        """Test token with 'email' field instead of 'username'"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': 1,
            'email': 'test@example.com',  # Using 'email' instead of 'username'
            'role': 'user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code in [200, 503]
    
    def test_token_without_role_defaults_to_user(self, client):
        """Test token without role field defaults to 'user' role"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': 1,
            'username': 'test_user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 403


class TestChineseRoleNames:
    """Test Chinese role name support"""
    
    def test_chinese_admin_role(self, client):
        """Test '超級管理員' (super admin) role"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': 1,
            'username': 'admin_cn',
            'role': '超級管理員',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code != 403
    
    def test_chinese_analyst_role(self, client):
        """Test '分析師' (analyst) role"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': 2,
            'username': 'analyst_cn',
            'role': '分析師',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/agent/debug/queue',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code != 403


class TestAuthorizationHeaderVariations:
    """Test various Authorization header formats"""
    
    def test_bearer_lowercase(self, client, user_token):
        """Test 'bearer' with lowercase - should work since we only split on space"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'bearer {user_token}'})
        
        assert response.status_code in [200, 503]
    
    def test_extra_spaces_in_header(self, client, user_token):
        """Test Authorization header with extra spaces"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer  {user_token}'})
        
        assert response.status_code == 401
    
    def test_no_space_after_bearer(self, client, user_token):
        """Test Authorization header without space after Bearer"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer{user_token}'})
        
        assert response.status_code == 401
