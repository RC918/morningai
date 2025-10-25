"""
Test FAQ API pagination and validation
Tests page/page_size validation and 422 error responses
"""
import pytest
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
api_backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'handoff', '20250928', '40_App', 'api-backend')
sys.path.insert(0, os.path.join(api_backend_path, 'src'))
sys.path.insert(0, api_backend_path)

@pytest.fixture
def app():
    """Create test Flask app"""
    from flask import Flask
    from routes.faq import bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(bp)
    
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def user_token():
    """Create user JWT token"""
    from middleware.auth_middleware import create_user_token
    return create_user_token()

def test_search_pagination_default(client, user_token):
    """Test search with default pagination"""
    with patch('src.routes.faq.FAQSearchTool') as mock_tool_class:
        mock_instance = AsyncMock()
        mock_tool_class.return_value = mock_instance
        mock_instance.search.return_value = {
            'success': True,
            'results': [{'id': str(i)} for i in range(10)],
            'count': 10
        }
        
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'pagination' in data['data']
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['page_size'] == 10

def test_search_pagination_custom(client, user_token):
    """Test search with custom pagination"""
    with patch('src.routes.faq.FAQSearchTool') as mock_tool_class:
        mock_instance = AsyncMock()
        mock_tool_class.return_value = mock_instance
        mock_instance.search.return_value = {
            'success': True,
            'results': [{'id': str(i)} for i in range(25)],
            'count': 25
        }
        
        response = client.get(
            '/api/faq/search?q=test&page=2&page_size=5',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['pagination']['page'] == 2
        assert data['data']['pagination']['page_size'] == 5

def test_search_page_size_exceeds_max(client, user_token):
    """Test that page_size > 100 returns validation error"""
    response = client.get(
        '/api/faq/search?q=test&page_size=101',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 422
    data = response.get_json()
    assert 'error' in data
    assert data['error']['code'] == 'validation_error'
    assert 'details' in data['error']

def test_search_page_negative(client, user_token):
    """Test that negative page returns validation error"""
    response = client.get(
        '/api/faq/search?q=test&page=0',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['error']['code'] == 'validation_error'

def test_search_page_size_negative(client, user_token):
    """Test that negative page_size returns validation error"""
    response = client.get(
        '/api/faq/search?q=test&page_size=0',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 422

def test_search_empty_query(client, user_token):
    """Test that empty query returns validation error"""
    response = client.get(
        '/api/faq/search?q=',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 422
    data = response.get_json()
    assert 'validation_error' in data['error']['code']

def test_search_missing_query(client, user_token):
    """Test that missing query returns validation error"""
    response = client.get(
        '/api/faq/search',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code in [400, 422]

def test_search_has_more_flag(client, user_token):
    """Test that has_more flag is set correctly"""
    from unittest.mock import MagicMock, patch
    from routes import faq as faq_mod
    
    mock_rpc_response = MagicMock()
    mock_rpc_response.data = [
        {
            'id': str(i),
            'question': f'Question {i}',
            'answer': f'Answer {i}',
            'category': 'test',
            'similarity': 0.9
        }
        for i in range(11)
    ]
    
    def mock_create_client(*args, **kwargs):
        mock_client = MagicMock()
        mock_client.rpc.return_value.execute.return_value = mock_rpc_response
        return mock_client
    
    with patch.object(faq_mod, 'get_cached_result', return_value=None), \
         patch.object(faq_mod, 'set_cached_result', return_value=None), \
         patch('agents.faq_agent.tools.faq_search_tool.create_client', side_effect=mock_create_client):
        response = client.get(
            '/api/faq/search?q=has-more-pagination-test&page=1&page_size=10',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert not data.get('cached', False)
        assert data['data']['pagination']['has_more'] == True

def test_create_faq_empty_question(client):
    """Test that empty question returns 422"""
    from middleware.auth_middleware import create_admin_token
    admin_token = create_admin_token()
    
    response = client.post(
        '/api/faq',
        json={'question': '', 'answer': 'A'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 422
    data = response.get_json()
    assert data['error']['code'] == 'validation_error'

def test_create_faq_empty_answer(client):
    """Test that empty answer returns 422"""
    from middleware.auth_middleware import create_admin_token
    admin_token = create_admin_token()
    
    response = client.post(
        '/api/faq',
        json={'question': 'Q', 'answer': ''},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 422

def test_create_faq_missing_fields(client):
    """Test that missing required fields returns 422"""
    from middleware.auth_middleware import create_admin_token
    admin_token = create_admin_token()
    
    response = client.post(
        '/api/faq',
        json={'question': 'Q'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 422

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
