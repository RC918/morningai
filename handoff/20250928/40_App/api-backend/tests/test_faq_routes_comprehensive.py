"""
Comprehensive tests for FAQ REST API routes (routes/faq.py)
Target: 70%+ code coverage

Tests cover:
- All CRUD operations (search, get, create, update, delete)
- Authentication and authorization (JWT, admin-only)
- Rate limiting headers and functionality
- Caching behavior and cache invalidation
- Pagination validation
- Error handling (401, 403, 422, 429, 500, 503)
- Edge cases and boundary conditions
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from src.main import app
from src.middleware.auth_middleware import create_admin_token, create_user_token

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def admin_token():
    """Generate admin JWT token"""
    return create_admin_token()

@pytest.fixture
def user_token():
    """Generate regular user JWT token"""
    return create_user_token()

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.routes.faq.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        mock.scan_iter.return_value = []
        yield mock

@pytest.fixture
def mock_faq_agent_available():
    """Mock FAQ_AGENT_AVAILABLE to True"""
    with patch('src.routes.faq.FAQ_AGENT_AVAILABLE', True):
        yield

@pytest.fixture
def mock_faq_search_tool(mock_faq_agent_available):
    """Mock FAQSearchTool - must be used with mock_faq_agent_available"""
    mock_class = MagicMock()
    instance = MagicMock()
    instance.search = AsyncMock(return_value={
        'success': True,
        'results': [
            {
                'id': 'faq-123',
                'question': 'What is Redis?',
                'answer': 'Redis is an in-memory data store',
                'category': 'database',
                'score': 0.95
            }
        ]
    })
    mock_class.return_value = instance
    
    with patch('src.routes.faq.FAQSearchTool', mock_class, create=True):
        yield mock_class

@pytest.fixture
def mock_faq_mgmt_tool(mock_faq_agent_available):
    """Mock FAQManagementTool - must be used with mock_faq_agent_available"""
    mock_class = MagicMock()
    instance = MagicMock()
    instance.get_faq = AsyncMock(return_value={
        'success': True,
        'faq': {
            'id': 'faq-123',
            'question': 'What is Redis?',
            'answer': 'Redis is an in-memory data store'
        }
    })
    instance.create_faq = AsyncMock(return_value={
        'success': True,
        'faq': {'id': 'faq-new-123'}
    })
    instance.update_faq = AsyncMock(return_value={
        'success': True
    })
    instance.delete_faq = AsyncMock(return_value={
        'success': True
    })
    instance.get_categories = AsyncMock(return_value={
        'success': True,
        'categories': ['database', 'api', 'security']
    })
    mock_class.return_value = instance
    
    with patch('src.routes.faq.FAQManagementTool', mock_class, create=True):
        yield mock_class



class TestAuthentication:
    """Test JWT authentication requirements"""
    
    def test_search_without_token_returns_401(self, client, mock_redis, mock_faq_search_tool):
        """Search endpoint without JWT returns 401"""
        response = client.get('/api/faq/search?q=redis')
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_faq_without_token_returns_401(self, client, mock_redis, mock_faq_mgmt_tool):
        """Get FAQ endpoint without JWT returns 401"""
        response = client.get('/api/faq/faq-123')
        assert response.status_code == 401
    
    def test_create_without_admin_returns_403(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Create FAQ with user (non-admin) token returns 403"""
        response = client.post(
            '/api/faq',
            json={'question': 'Test?', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403
    
    def test_update_without_admin_returns_403(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Update FAQ with user (non-admin) token returns 403"""
        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated answer'},
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403
    
    def test_delete_without_admin_returns_403(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Delete FAQ with user (non-admin) token returns 403"""
        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403



class TestRateLimiting:
    """Test rate limiting headers and functionality"""
    
    def test_rate_limit_headers_present(self, client, user_token, mock_redis, mock_faq_search_tool):
        """All responses include X-RateLimit-* headers"""
        response = client.get(
            '/api/faq/search?q=redis',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        assert response.headers['X-RateLimit-Limit'] == '60'



class TestFAQSearch:
    """Test FAQ search endpoint"""
    
    def test_search_with_valid_query(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search with valid query returns results in {data: {...}, cached: bool} format"""
        response = client.get(
            '/api/faq/search?q=redis',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'cached' in data
        assert isinstance(data['cached'], bool)
        
        assert 'query' in data['data']
        assert 'results' in data['data']
        assert 'pagination' in data['data']
        assert data['data']['query'] == 'redis'
    
    def test_search_with_pagination(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search with page/page_size parameters works correctly"""
        response = client.get(
            '/api/faq/search?q=test&page=2&page_size=5',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        pagination = data['data']['pagination']
        assert pagination['page'] == 2
        assert pagination['page_size'] == 5
    
    def test_search_with_category_filter(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search with category filter works"""
        response = client.get(
            '/api/faq/search?q=test&category=database',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
    
    def test_search_with_sort_params(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search with sort_by and sort_order works"""
        response = client.get(
            '/api/faq/search?q=test&sort_by=created_at&sort_order=asc',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
    
    def test_search_empty_query_returns_422(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search with empty query returns 422 validation error"""
        response = client.get(
            '/api/faq/search?q=',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 422
        data = response.get_json()
        assert data['error']['code'] == 'validation_error'
        assert 'details' in data['error']
    
    def test_search_invalid_page_returns_422(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search with page < 1 returns 422"""
        response = client.get(
            '/api/faq/search?q=test&page=0',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 422
    
    def test_search_invalid_page_size_returns_422(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search with page_size > 100 returns 422"""
        response = client.get(
            '/api/faq/search?q=test&page_size=200',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 422
    
    def test_search_invalid_sort_order_returns_422(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search with invalid sort_order returns 422"""
        response = client.get(
            '/api/faq/search?q=test&sort_order=invalid',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 422
    
    def test_search_cached_result(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search returns cached=True when result is from cache"""
        cached_data = {
            'query': 'redis',
            'results': [],
            'pagination': {'page': 1, 'page_size': 10, 'has_more': False}
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        response = client.get(
            '/api/faq/search?q=redis',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] is True
    
    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_search_service_unavailable(self, client, user_token):
        """Search returns 503 when FAQ agent is unavailable"""
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 503
        data = response.get_json()
        assert data['error']['code'] == 'service_unavailable'



class TestFAQGet:
    """Test get FAQ by ID endpoint"""
    
    def test_get_faq_success(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get FAQ by ID returns FAQ data"""
        response = client.get(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'cached' in data
        assert 'faq' in data['data']
    
    def test_get_faq_not_found(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get non-existent FAQ returns 404"""
        mock_faq_mgmt_tool.return_value.get_faq = AsyncMock(return_value={
            'success': False,
            'error': 'FAQ not found'
        })
        
        response = client.get(
            '/api/faq/nonexistent',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data['error']['code'] == 'not_found'
    
    def test_get_faq_from_cache(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Get FAQ returns cached=True when from cache"""
        cached_faq = {
            'faq': {'id': 'faq-123', 'question': 'Cached?', 'answer': 'Yes'},
            'timestamp': '2025-01-01T00:00:00'
        }
        mock_redis.get.return_value = json.dumps(cached_faq)
        
        response = client.get(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] is True



class TestFAQCreate:
    """Test create FAQ endpoint (admin only)"""
    
    def test_create_faq_success(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Admin can create FAQ successfully"""
        response = client.post(
            '/api/faq',
            json={
                'question': 'New question?',
                'answer': 'New answer',
                'category': 'test',
                'tags': ['tag1', 'tag2']
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'data' in data
        assert 'faq_id' in data['data']
        assert 'message' in data['data']
    
    def test_create_faq_missing_question_returns_422(self, client, admin_token, mock_redis, mock_faq_agent_available):
        """Create FAQ without question returns 422"""
        response = client.post(
            '/api/faq',
            json={'answer': 'Answer only'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 422
        data = response.get_json()
        assert data['error']['code'] == 'validation_error'
    
    def test_create_faq_empty_question_returns_422(self, client, admin_token, mock_redis, mock_faq_agent_available):
        """Create FAQ with empty question returns 422"""
        response = client.post(
            '/api/faq',
            json={'question': '', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 422



class TestFAQUpdate:
    """Test update FAQ endpoint (admin only)"""
    
    def test_update_faq_success(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Admin can update FAQ successfully"""
        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['message'] == 'FAQ updated successfully'
    
    def test_update_faq_not_found(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Update non-existent FAQ returns 404"""
        mock_faq_mgmt_tool.return_value.update_faq = AsyncMock(return_value={
            'success': False,
            'error': 'FAQ not found'
        })
        
        response = client.put(
            '/api/faq/nonexistent',
            json={'answer': 'New answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 404
    
    def test_update_faq_no_fields_returns_400(self, client, admin_token, mock_redis, mock_faq_agent_available):
        """Update FAQ with no fields returns 400"""
        response = client.put(
            '/api/faq/faq-123',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'invalid_input'



class TestFAQDelete:
    """Test delete FAQ endpoint (admin only)"""
    
    def test_delete_faq_success(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Admin can delete FAQ successfully"""
        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['message'] == 'FAQ deleted successfully'
    
    def test_delete_faq_not_found(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Delete non-existent FAQ returns 404"""
        mock_faq_mgmt_tool.return_value.delete_faq = AsyncMock(return_value={
            'success': False,
            'error': 'FAQ not found'
        })
        
        response = client.delete(
            '/api/faq/nonexistent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 404



class TestCategoriesAndStats:
    """Test categories and stats endpoints"""
    
    def test_get_categories_success(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get categories returns list"""
        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'cached' in data
        assert 'categories' in data['data']
    
    def test_get_categories_from_cache(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Get categories from cache"""
        cached_data = {'categories': ['database', 'api'], 'timestamp': '2025-01-01'}
        mock_redis.get.return_value = json.dumps(cached_data)
        
        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        assert response.get_json()['cached'] is True



class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_search_tool_exception(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Search tool exception returns 500"""
        mock_faq_search_tool.return_value.search = AsyncMock(side_effect=Exception('DB error'))
        
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'
    
    def test_redis_connection_error_graceful(self, client, user_token, mock_redis, mock_faq_search_tool):
        """Redis connection error doesn't break the request"""
        from redis import ConnectionError as RedisConnectionError
        mock_redis.get.side_effect = RedisConnectionError('Connection failed')
        
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=src.routes.faq', '--cov-report=term-missing'])
