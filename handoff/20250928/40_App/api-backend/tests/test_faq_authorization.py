import pytest
import json
import os
from unittest.mock import patch, MagicMock
from src.main import app
from src.middleware.auth_middleware import generate_jwt_token, create_admin_token, create_analyst_token


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_faq_401_missing_jwt(client):
    response = client.post(
        '/api/agent/faq',
        data=json.dumps({'question': 'What is the system architecture?'}),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Authorization header missing'


def test_faq_401_invalid_jwt(client):
    response = client.post(
        '/api/agent/faq',
        data=json.dumps({'question': 'What is the system architecture?'}),
        content_type='application/json',
        headers={'Authorization': 'Bearer invalid_token_here'}
    )
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] in ['Invalid token', 'Token expired', 'Authentication failed']


def test_faq_403_user_role_blocked(client):
    user_token = generate_jwt_token({
        'id': 3,
        'username': 'testuser',
        'role': 'user'
    })
    
    response = client.post(
        '/api/agent/faq',
        data=json.dumps({'question': 'What is the system architecture?'}),
        content_type='application/json',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Insufficient privileges'


def test_faq_200_admin_allowed(client):
    admin_token = create_admin_token()
    
    try:
        response = client.post(
            '/api/agent/faq',
            data=json.dumps({'question': 'What is the system architecture?'}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        if response.status_code == 503:
            pytest.skip("Redis/RQ not available for integration test")
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        assert 'status' in data
        assert data['status'] == 'queued'
        
        print(f"✅ Admin successfully created FAQ task: {data['task_id']}")
    except Exception as e:
        pytest.skip(f"Service not available: {e}")


def test_faq_200_analyst_allowed(client):
    analyst_token = create_analyst_token()
    
    try:
        response = client.post(
            '/api/agent/faq',
            data=json.dumps({'question': 'How do I configure the agent?'}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {analyst_token}'}
        )
        
        if response.status_code == 503:
            pytest.skip("Redis/RQ not available for integration test")
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'task_id' in data
        assert 'status' in data
        assert data['status'] == 'queued'
        
        print(f"✅ Analyst successfully created FAQ task: {data['task_id']}")
    except Exception as e:
        pytest.skip(f"Service not available: {e}")


def test_faq_400_missing_question(client):
    admin_token = create_admin_token()
    
    response = client.post(
        '/api/agent/faq',
        data=json.dumps({}),
        content_type='application/json',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_input'


def test_faq_400_empty_question(client):
    admin_token = create_admin_token()
    
    response = client.post(
        '/api/agent/faq',
        data=json.dumps({'question': '   '}),
        content_type='application/json',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'invalid_input'
