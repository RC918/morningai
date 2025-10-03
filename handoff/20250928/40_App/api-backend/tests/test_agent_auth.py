import pytest
import json
from src.main import app
from src.middleware import create_admin_token, generate_jwt_token

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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

def test_debug_endpoint_operator_role(client):
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

def test_debug_endpoint_admin_role(client):
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
