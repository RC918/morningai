import pytest
import json
from unittest.mock import patch, MagicMock

from src.main import app
from src.middleware import create_admin_token, create_analyst_token, create_user_token

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_redis():
    """Mock Redis client for tests that need it"""
    with patch('src.routes.agent.redis_client') as mock_client, \
         patch('src.routes.agent.redis_client_rq') as mock_client_rq:
        mock_client.type.return_value = "hash"
        mock_client.hgetall.return_value = {
            "status": "queued",
            "job_id": "test-job-123",
            "created_at": "2025-10-03T00:00:00",
            "question": "test question"
        }
        mock_client.scan_iter.return_value = iter(["agent:task:test-123"])
        
        mock_client_rq.llen.return_value = 0
        mock_client_rq.lrange.return_value = []
        
        yield mock_client

def test_debug_endpoint_no_token(client):
    """Test debug endpoint without token returns 401"""
    response = client.get('/api/agent/debug/queue')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Authorization header missing'

def test_debug_endpoint_invalid_token(client):
    """Test debug endpoint with invalid token returns 401"""
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_debug_endpoint_user_role(client):
    """Test debug endpoint with user role returns 403"""
    token = create_user_token()
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Insufficient privileges'

def test_debug_endpoint_analyst_role(client, mock_redis):
    """Test debug endpoint with analyst role returns 200"""
    token = create_analyst_token()
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'queue_length' in data
    assert 'timestamp' in data

def test_debug_endpoint_admin_role(client, mock_redis):
    """Test debug endpoint with admin role returns 200"""
    token = create_admin_token()
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'queue_length' in data
    assert 'timestamp' in data

def test_debug_endpoint_expired_token(client, mock_redis):
    """Test debug endpoint with expired token returns 401"""
    import jwt
    import datetime
    import os
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = {
        'user_id': 2,
        'username': 'analyst',
        'role': 'analyst',
        'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),
        'iat': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=2)
    }
    expired_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': f'Bearer {expired_token}'}
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Token expired'

def test_debug_endpoint_malformed_token(client):
    """Test debug endpoint with malformed token returns 401"""
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': 'Bearer malformed.token.here'}
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid token' in data['error']
