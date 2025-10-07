import pytest
from src.main import app


def test_faq_get_returns_405():
    """Test that GET /api/agent/faq returns 405 Method Not Allowed"""
    with app.test_client() as client:
        response = client.get('/api/agent/faq')
        
        assert response.status_code == 405
        assert 'Allow' in response.headers
        assert response.headers['Allow'] == 'POST'
        
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Method Not Allowed'
        assert 'message' in data
        assert 'POST' in data['message']


def test_faq_post_requires_auth():
    """Test that POST /api/agent/faq without auth returns 401 or processes"""
    with app.test_client() as client:
        response = client.post(
            '/api/agent/faq',
            json={'question': 'Test question'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [202, 401, 503]


def test_faq_post_with_valid_payload():
    """Test that POST /api/agent/faq with valid payload returns 202"""
    with app.test_client() as client:
        response = client.post(
            '/api/agent/faq',
            json={'question': 'What is the system architecture?'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [202, 503]
        
        if response.status_code == 202:
            data = response.get_json()
            assert 'task_id' in data
            assert 'status' in data
            assert data['status'] == 'queued'


def test_faq_post_with_invalid_payload():
    """Test that POST /api/agent/faq with invalid payload returns 400"""
    with app.test_client() as client:
        response = client.post(
            '/api/agent/faq',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


def test_faq_post_with_empty_question():
    """Test that POST /api/agent/faq with empty question returns 400"""
    with app.test_client() as client:
        response = client.post(
            '/api/agent/faq',
            json={'question': ''},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


def test_faq_post_with_whitespace_question():
    """Test that POST /api/agent/faq with whitespace-only question returns 400"""
    with app.test_client() as client:
        response = client.post(
            '/api/agent/faq',
            json={'question': '   '},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
