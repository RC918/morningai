"""
Test FAQ API cache invalidation
Tests that CRUD operations properly invalidate cached search results
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
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
def mock_redis():
    """Mock Redis client"""
    with patch('routes.faq.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        mock.scan_iter.return_value = []
        yield mock

@pytest.fixture
def admin_token():
    """Create admin JWT token for testing"""
    from middleware.auth_middleware import create_admin_token
    return create_admin_token()

@pytest.fixture
def user_token():
    """Create user JWT token for testing"""
    from middleware.auth_middleware import create_user_token
    return create_user_token()

@pytest.mark.asyncio
async def test_create_faq_invalidates_search_cache(client, mock_redis, admin_token):
    """Test that creating FAQ invalidates search cache"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.create_faq', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'success': True,
            'faq': {
                'id': 'test-id-123',
                'question': 'Test Q',
                'answer': 'Test A'
            }
        }
        
        response = client.post(
            '/api/faq',
            json={'question': 'Test Q', 'answer': 'Test A'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 201
        
        mock_redis.scan_iter.assert_any_call('faq:search:*')
        mock_redis.scan_iter.assert_any_call('faq:categories:*')

@pytest.mark.asyncio
async def test_update_faq_invalidates_caches(client, mock_redis, admin_token):
    """Test that updating FAQ invalidates both search and item caches"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.update_faq', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            'success': True
        }
        
        response = client.put(
            '/api/faq/test-id-123',
            json={'answer': 'Updated A'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        
        mock_redis.scan_iter.assert_any_call('faq:search:*')
        mock_redis.scan_iter.assert_any_call('faq:item:*')

@pytest.mark.asyncio
async def test_delete_faq_invalidates_caches(client, mock_redis, admin_token):
    """Test that deleting FAQ invalidates both search and item caches"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.delete_faq', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = {
            'success': True
        }
        
        response = client.delete(
            '/api/faq/test-id-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        
        mock_redis.scan_iter.assert_any_call('faq:search:*')
        mock_redis.scan_iter.assert_any_call('faq:item:*')

@pytest.mark.asyncio
async def test_search_caches_results(client, mock_redis, user_token):
    """Test that search results are cached"""
    with patch('agents.faq_agent.tools.faq_search_tool.FAQSearchTool.search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {
            'success': True,
            'results': [{'id': '1', 'question': 'Q1'}],
            'count': 1
        }
        
        response = client.get(
            '/api/faq/search?q=test&page=1&page_size=10',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0].startswith('faq:search:')

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
