import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app
from src.middleware import create_admin_token, generate_jwt_token

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

def create_operator_token():
    """Create operator JWT token for testing"""
    operator_data = {
        'id': 2,
        'username': 'operator',
        'role': 'operator'
    }
    return generate_jwt_token(operator_data)

def create_viewer_token():
    """Create viewer JWT token for testing"""
    viewer_data = {
        'id': 3,
        'username': 'viewer',
        'role': 'viewer'
    }
    return generate_jwt_token(viewer_data)

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

def test_debug_endpoint_viewer_role(client):
    """Test debug endpoint with viewer role returns 403"""
    token = create_viewer_token()
    response = client.get(
        '/api/agent/debug/queue',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Insufficient privileges'

def test_debug_endpoint_operator_role(client, mock_redis):
    """Test debug endpoint with operator role returns 200"""
    token = create_operator_token()
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
