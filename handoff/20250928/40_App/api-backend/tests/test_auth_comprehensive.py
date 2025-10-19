"""
Comprehensive tests for auth endpoints
Focus on improving auth.py coverage from 83% to 95%+
"""
import pytest
import jwt
import datetime
from unittest.mock import patch, MagicMock
import os


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    app.config['TESTING'] = True
    return app.test_client()


class TestAuthLogin:
    """Test login endpoint comprehensively"""
    
    def test_login_success_admin(self, client):
        """Test successful login with admin credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'admin123')
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert 'token' in data
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
    
    def test_login_missing_username(self, client):
        """Test login with missing username"""
        response = client.post('/api/auth/login', json={
            'password': 'test123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'message' in data
    
    def test_login_missing_password(self, client):
        """Test login with missing password"""
        response = client.post('/api/auth/login', json={
            'username': 'admin'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'message' in data
    
    def test_login_invalid_user(self, client):
        """Test login with non-existent user"""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'test123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    @patch('src.routes.auth.request')
    def test_login_exception_handling(self, mock_request, client):
        """Test login exception handling"""
        mock_request.get_json.side_effect = Exception('Test error')
        
        response = client.post('/api/auth/login', json={})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'message' in data


class TestAuthVerify:
    """Test token verification endpoint"""
    
    def test_verify_missing_auth_header(self, client):
        """Test verify without Authorization header"""
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    def test_verify_invalid_auth_format(self, client):
        """Test verify with invalid auth format"""
        response = client.get('/api/auth/verify', headers={
            'Authorization': 'InvalidFormat'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    def test_verify_valid_token(self, client):
        """Test verify with valid token"""
        login_response = client.post('/api/auth/login', json={
            'username': 'admin',
            'password': os.environ.get('ADMIN_PASSWORD', 'admin123')
        })
        token = login_response.get_json()['token']
        
        response = client.get('/api/auth/verify', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'username' in data
        assert data['username'] == 'admin'
    
    def test_verify_expired_token(self, client):
        """Test verify with expired token"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        expired_token = jwt.encode({
            'user_id': 1,
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
        }, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/auth/verify', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
        assert 'expired' in data['message'].lower() or 'token' in data['message'].lower()
    
    def test_verify_invalid_token(self, client):
        """Test verify with invalid token"""
        response = client.get('/api/auth/verify', headers={
            'Authorization': 'Bearer invalid.token.here'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    def test_verify_nonexistent_user(self, client):
        """Test verify with token for non-existent user"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        token = jwt.encode({
            'user_id': 999,
            'username': 'nonexistent',
            'role': 'admin',
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        }, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/auth/verify', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'message' in data
    
    @patch('src.routes.auth.request')
    def test_verify_exception_handling(self, mock_request, client):
        """Test verify exception handling"""
        mock_request.headers.get.side_effect = Exception('Test error')
        
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'message' in data


class TestAuthLogout:
    """Test logout endpoint"""
    
    def test_logout_success(self, client):
        """Test logout endpoint"""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data


class TestAuthMultipleUsers:
    """Test authentication with different user roles"""
    
    def test_login_operator(self, client):
        """Test login with operator credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'operator',
            'password': 'operator123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['role'] == 'operator'
    
    def test_login_viewer(self, client):
        """Test login with viewer credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'viewer',
            'password': 'viewer123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['role'] == 'viewer'
