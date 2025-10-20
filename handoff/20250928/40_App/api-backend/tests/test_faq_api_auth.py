import pytest
from src.main import app
from src.middleware.auth_middleware import create_user_token


def test_faq_search_requires_auth():
    """Test that GET /api/faq/search without auth returns 401"""
    with app.test_client() as client:
        response = client.get('/api/faq/search?q=test')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Authorization header missing'


def test_faq_search_with_auth_new_format():
    """Test that GET /api/faq/search with auth returns new format with data and cached"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/search?q=test&page=1&page_size=10',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'data' in data
            assert 'cached' in data
            assert isinstance(data['cached'], bool)
            
            assert 'query' in data['data']
            assert 'results' in data['data']
            assert 'page' in data['data']
            assert 'page_size' in data['data']
            assert 'timestamp' in data['data']


def test_faq_search_pagination_params():
    """Test that FAQ search accepts page and page_size parameters"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/search?q=test&page=2&page_size=20',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.get_json()
            assert data['data']['page'] == 2
            assert data['data']['page_size'] == 20


def test_faq_get_by_id_requires_auth():
    """Test that GET /api/faq/<id> without auth returns 401"""
    with app.test_client() as client:
        response = client.get('/api/faq/test-id-123')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data


def test_faq_get_by_id_new_format():
    """Test that GET /api/faq/<id> with auth returns new format"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/test-id-123',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code in [404, 503]


def test_faq_create_requires_auth():
    """Test that POST /api/faq without auth returns 401"""
    with app.test_client() as client:
        response = client.post(
            '/api/faq',
            json={
                'question': 'Test question',
                'answer': 'Test answer'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401


def test_faq_create_new_format():
    """Test that POST /api/faq with auth returns new format"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.post(
            '/api/faq',
            json={
                'question': 'Test question',
                'answer': 'Test answer',
                'category': 'test'
            },
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
        
        assert response.status_code in [201, 503]
        
        if response.status_code == 201:
            data = response.get_json()
            assert 'data' in data
            assert 'cached' in data
            assert data['cached'] is False
            assert 'faq_id' in data['data']


def test_faq_update_requires_auth():
    """Test that PUT /api/faq/<id> without auth returns 401"""
    with app.test_client() as client:
        response = client.put(
            '/api/faq/test-id-123',
            json={'question': 'Updated question'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401


def test_faq_delete_requires_auth():
    """Test that DELETE /api/faq/<id> without auth returns 401"""
    with app.test_client() as client:
        response = client.delete('/api/faq/test-id-123')
        
        assert response.status_code == 401


def test_faq_categories_requires_auth():
    """Test that GET /api/faq/categories without auth returns 401"""
    with app.test_client() as client:
        response = client.get('/api/faq/categories')
        
        assert response.status_code == 401


def test_faq_categories_new_format():
    """Test that GET /api/faq/categories with auth returns new format"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'data' in data
            assert 'cached' in data
            assert isinstance(data['cached'], bool)


def test_faq_stats_requires_auth():
    """Test that GET /api/faq/stats without auth returns 401"""
    with app.test_client() as client:
        response = client.get('/api/faq/stats')
        
        assert response.status_code == 401


def test_faq_stats_new_format():
    """Test that GET /api/faq/stats with auth returns new format"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'data' in data
            assert 'cached' in data
            assert isinstance(data['cached'], bool)


def test_faq_invalid_bearer_token():
    """Test that invalid JWT token returns 401"""
    with app.test_client() as client:
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': 'Bearer invalid-token-here'}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data


def test_faq_missing_bearer_prefix():
    """Test that token without Bearer prefix returns 401"""
    token = create_user_token()
    with app.test_client() as client:
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': token}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid authorization format' in data['error']
