"""
Additional tests for FAQ routes to improve coverage to 80%+

Tests cover:
- Health check endpoint with various states
- Stats endpoint with caching
- Delete endpoint edge cases
- Service unavailable scenarios for all endpoints
- Cache invalidation patterns
- Sentry integration paths
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
        mock.ping.return_value = True
        yield mock


@pytest.fixture
def mock_faq_agent_available():
    """Mock FAQ_AGENT_AVAILABLE to True"""
    with patch('src.routes.faq.FAQ_AGENT_AVAILABLE', True):
        yield


@pytest.fixture
def mock_faq_mgmt_tool(mock_faq_agent_available):
    """Mock FAQManagementTool"""
    mock_class = MagicMock()
    instance = MagicMock()
    instance.get_faq = AsyncMock(return_value={
        'success': True,
        'faq': {'id': 'faq-123', 'question': 'Test?', 'answer': 'Answer'}
    })
    instance.create_faq = AsyncMock(return_value={
        'success': True,
        'faq': {'id': 'faq-new-123'}
    })
    instance.update_faq = AsyncMock(return_value={'success': True})
    instance.delete_faq = AsyncMock(return_value={'success': True})
    instance.get_categories = AsyncMock(return_value={
        'success': True,
        'categories': ['database', 'api'],
        'count': 2
    })
    instance.get_stats = AsyncMock(return_value={
        'success': True,
        'stats': {'total_faqs': 100, 'categories': 5}
    })
    mock_class.return_value = instance

    with patch('src.routes.faq.FAQManagementTool', mock_class, create=True):
        yield mock_class


class TestHealthCheck:
    """Test FAQ health check endpoint"""

    def test_health_check_all_healthy(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Health check returns healthy when all services are up"""
        mock_search_tool = MagicMock()
        mock_search_tool.search = AsyncMock(return_value={'success': True})

        with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
            response = client.get(
                '/api/faq/health',
                headers={'Authorization': f'Bearer {user_token}'}
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['checks']['faq_agent']['available'] is True
        assert data['checks']['redis']['status'] == 'ok'

    def test_health_check_redis_error(self, client, user_token, mock_faq_agent_available):
        """Health check returns degraded when Redis is down"""
        with patch('src.routes.faq.redis_client') as mock_redis:
            mock_redis.ping.side_effect = Exception('Redis connection failed')

            mock_search_tool = MagicMock()
            mock_search_tool.search = AsyncMock(return_value={'success': True})

            with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
                response = client.get(
                    '/api/faq/health',
                    headers={'Authorization': f'Bearer {user_token}'}
                )

        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'degraded'
        assert data['checks']['redis']['status'] == 'error'

    def test_health_check_database_error(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Health check returns degraded when database check fails"""
        mock_search_tool = MagicMock()
        mock_search_tool.search = AsyncMock(return_value={
            'success': False,
            'error': 'Database connection failed'
        })

        with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
            response = client.get(
                '/api/faq/health',
                headers={'Authorization': f'Bearer {user_token}'}
            )

        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'degraded'
        assert data['checks']['database']['status'] == 'error'

    def test_health_check_database_exception(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Health check handles database exception gracefully"""
        mock_search_tool = MagicMock()
        mock_search_tool.search = AsyncMock(side_effect=Exception('Connection timeout'))

        with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
            response = client.get(
                '/api/faq/health',
                headers={'Authorization': f'Bearer {user_token}'}
            )

        assert response.status_code == 503
        data = response.get_json()
        assert data['checks']['database']['status'] == 'error'
        assert 'Connection timeout' in data['checks']['database']['error']

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_health_check_faq_agent_unavailable(self, client, user_token, mock_redis):
        """Health check shows FAQ agent unavailable"""
        response = client.get(
            '/api/faq/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 503
        data = response.get_json()
        assert data['checks']['faq_agent']['available'] is False


class TestStats:
    """Test FAQ stats endpoint"""

    def test_get_stats_success(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get stats returns statistics"""
        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'stats' in data['data']
        assert data['cached'] is False

    def test_get_stats_from_cache(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Get stats returns cached result"""
        cached_data = {
            'stats': {'total_faqs': 50},
            'timestamp': '2025-01-01T00:00:00'
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] is True

    def test_get_stats_fetch_failed(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get stats returns 500 when fetch fails"""
        mock_faq_mgmt_tool.return_value.get_stats = AsyncMock(return_value={
            'success': False,
            'error': 'Database error'
        })

        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'fetch_failed'

    def test_get_stats_exception(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get stats returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.get_stats = AsyncMock(
            side_effect=Exception('Unexpected error')
        )

        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_get_stats_service_unavailable(self, client, user_token):
        """Get stats returns 503 when service unavailable"""
        response = client.get(
            '/api/faq/stats',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 503


class TestDeleteEdgeCases:
    """Test delete FAQ edge cases"""

    def test_delete_faq_generic_error(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Delete FAQ returns 500 for generic errors"""
        mock_faq_mgmt_tool.return_value.delete_faq = AsyncMock(return_value={
            'success': False,
            'error': 'Database constraint violation'
        })

        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'delete_failed'

    def test_delete_faq_exception(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Delete FAQ returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.delete_faq = AsyncMock(
            side_effect=Exception('Connection lost')
        )

        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_delete_faq_service_unavailable(self, client, admin_token):
        """Delete FAQ returns 503 when service unavailable"""
        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 503


class TestCategoriesEdgeCases:
    """Test categories endpoint edge cases"""

    def test_get_categories_fetch_failed(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get categories returns 500 when fetch fails"""
        mock_faq_mgmt_tool.return_value.get_categories = AsyncMock(return_value={
            'success': False,
            'error': 'Database error'
        })

        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'fetch_failed'

    def test_get_categories_exception(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get categories returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.get_categories = AsyncMock(
            side_effect=Exception('Timeout')
        )

        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_get_categories_service_unavailable(self, client, user_token):
        """Get categories returns 503 when service unavailable"""
        response = client.get(
            '/api/faq/categories',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 503


class TestUpdateEdgeCases:
    """Test update FAQ edge cases"""

    def test_update_faq_generic_error(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Update FAQ returns 500 for generic errors"""
        mock_faq_mgmt_tool.return_value.update_faq = AsyncMock(return_value={
            'success': False,
            'error': 'Validation failed'
        })

        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'update_failed'

    def test_update_faq_exception(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Update FAQ returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.update_faq = AsyncMock(
            side_effect=Exception('Network error')
        )

        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_update_faq_service_unavailable(self, client, admin_token):
        """Update FAQ returns 503 when service unavailable"""
        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 503


class TestCreateEdgeCases:
    """Test create FAQ edge cases"""

    def test_create_faq_generic_error(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Create FAQ returns 500 for generic errors"""
        mock_faq_mgmt_tool.return_value.create_faq = AsyncMock(return_value={
            'success': False,
            'error': 'Duplicate entry'
        })

        response = client.post(
            '/api/faq',
            json={'question': 'Test?', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'create_failed'

    def test_create_faq_exception(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Create FAQ returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.create_faq = AsyncMock(
            side_effect=Exception('Database error')
        )

        response = client.post(
            '/api/faq',
            json={'question': 'Test?', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_create_faq_service_unavailable(self, client, admin_token):
        """Create FAQ returns 503 when service unavailable"""
        response = client.post(
            '/api/faq',
            json={'question': 'Test?', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 503


class TestGetFAQEdgeCases:
    """Test get FAQ edge cases"""

    def test_get_faq_generic_error(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get FAQ returns 500 for generic errors"""
        mock_faq_mgmt_tool.return_value.get_faq = AsyncMock(return_value={
            'success': False,
            'error': 'Database timeout'
        })

        response = client.get(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'fetch_failed'

    def test_get_faq_exception(self, client, user_token, mock_redis, mock_faq_mgmt_tool):
        """Get FAQ returns 500 on exception"""
        mock_faq_mgmt_tool.return_value.get_faq = AsyncMock(
            side_effect=Exception('Connection refused')
        )

        response = client.get(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'internal_error'

    @patch('src.routes.faq.FAQ_AGENT_AVAILABLE', False)
    def test_get_faq_service_unavailable(self, client, user_token):
        """Get FAQ returns 503 when service unavailable"""
        response = client.get(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        assert response.status_code == 503


class TestSearchEdgeCases:
    """Test search FAQ edge cases"""

    def test_search_failed_result(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search returns 500 when search fails"""
        mock_search_tool = MagicMock()
        mock_search_tool.search = AsyncMock(return_value={
            'success': False,
            'error': 'Search index unavailable'
        })

        with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
            response = client.get(
                '/api/faq/search?q=test',
                headers={'Authorization': f'Bearer {user_token}'}
            )

        assert response.status_code == 500
        data = response.get_json()
        assert data['error']['code'] == 'search_failed'

    def test_search_with_all_params(self, client, user_token, mock_redis, mock_faq_agent_available):
        """Search with all parameters works"""
        mock_search_tool = MagicMock()
        mock_search_tool.search = AsyncMock(return_value={
            'success': True,
            'results': [{'id': '1', 'question': 'Q', 'answer': 'A'}]
        })

        with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
            response = client.get(
                '/api/faq/search?q=test&page=1&page_size=20&category=api&sort_by=created_at&sort_order=asc',
                headers={'Authorization': f'Bearer {user_token}'}
            )

        assert response.status_code == 200


class TestCacheInvalidation:
    """Test cache invalidation patterns"""

    def test_cache_invalidation_on_create(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Create FAQ invalidates search and categories cache"""
        mock_redis.scan_iter.return_value = ['faq:search:abc', 'faq:search:def']

        response = client.post(
            '/api/faq',
            json={'question': 'New?', 'answer': 'Answer'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 201
        assert mock_redis.scan_iter.called

    def test_cache_invalidation_on_update(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Update FAQ invalidates relevant caches"""
        mock_redis.scan_iter.return_value = ['faq:search:abc', 'faq:item:123']

        response = client.put(
            '/api/faq/faq-123',
            json={'answer': 'Updated'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 200
        assert mock_redis.scan_iter.called

    def test_cache_invalidation_on_delete(self, client, admin_token, mock_redis, mock_faq_mgmt_tool):
        """Delete FAQ invalidates relevant caches"""
        mock_redis.scan_iter.return_value = ['faq:search:abc', 'faq:item:123']

        response = client.delete(
            '/api/faq/faq-123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )

        assert response.status_code == 200
        assert mock_redis.scan_iter.called


class TestSentryIntegration:
    """Test Sentry integration paths"""

    def test_health_check_with_sentry_breadcrumb(self, client, user_token, mock_redis):
        """Health check adds Sentry breadcrumb on failure"""
        with patch('src.routes.faq.FAQ_AGENT_AVAILABLE', True), \
             patch('src.routes.faq.sentry_sdk') as mock_sentry:
            mock_sentry.add_breadcrumb = MagicMock()

            mock_search_tool = MagicMock()
            mock_search_tool.search = AsyncMock(return_value={'success': False, 'error': 'DB error'})

            with patch('src.routes.faq.FAQSearchTool', return_value=mock_search_tool, create=True):
                response = client.get(
                    '/api/faq/health',
                    headers={'Authorization': f'Bearer {user_token}'}
                )

            assert response.status_code == 503
            mock_sentry.add_breadcrumb.assert_called()
