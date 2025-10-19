import pytest
import json
import os

from src.main import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success_admin(client):
    """Test successful admin login"""
    response = client.post(
        '/api/auth/login',
        json={'username': 'admin', 'password': os.environ.get('ADMIN_PASSWORD', 'admin123')},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data
    assert data['user']['role'] == 'admin'

def test_login_success_operator(client):
    """Test operator login (should normalize to analyst)"""
    response = client.post(
        '/api/auth/login',
        json={'username': 'operator', 'password': 'operator123'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert data['user']['role'] == 'operator'

def test_login_failure_wrong_password(client):
    """Test login with wrong password"""
    response = client.post(
        '/api/auth/login',
        json={'username': 'admin', 'password': 'wrongpassword'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data

def test_login_failure_nonexistent_user(client):
    """Test login with nonexistent user"""
    response = client.post(
        '/api/auth/login',
        json={'username': 'nonexistent', 'password': 'password'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401

def test_login_missing_credentials(client):
    """Test login with missing credentials"""
    response = client.post(
        '/api/auth/login',
        json={},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400

def test_verify_token_success(client):
    """Test token verification with valid token"""
    login_response = client.post(
        '/api/auth/login',
        json={'username': 'admin', 'password': os.environ.get('ADMIN_PASSWORD', 'admin123')},
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(login_response.data)['token']
    
    response = client.get(
        '/api/auth/verify',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['username'] == 'admin'
    assert data['role'] == 'admin'

def test_verify_token_expired(client):
    """Test token verification with expired token"""
    import jwt
    import datetime
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = {
        'user_id': 1,
        'username': 'admin',
        'role': 'admin',
        'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
    }
    expired_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    
    response = client.get(
        '/api/auth/verify',
        headers={'Authorization': f'Bearer {expired_token}'}
    )
    assert response.status_code == 401

def test_verify_token_missing(client):
    """Test token verification without token"""
    response = client.get('/api/auth/verify')
    assert response.status_code == 401

def test_logout(client):
    """Test logout endpoint"""
    response = client.post('/api/auth/logout')
    assert response.status_code == 200
