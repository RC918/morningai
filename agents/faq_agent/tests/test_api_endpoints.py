"""
Test suite for FAQ REST API endpoints
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_search_tool():
    """Mock FAQSearchTool"""
    with patch('src.routes.faq.FAQSearchTool') as mock:
        tool_instance = AsyncMock()
        mock.return_value = tool_instance
        yield tool_instance


@pytest.fixture
def mock_mgmt_tool():
    """Mock FAQManagementTool"""
    with patch('src.routes.faq.FAQManagementTool') as mock:
        tool_instance = AsyncMock()
        mock.return_value = tool_instance
        yield tool_instance


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.routes.faq.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.scan_iter.return_value = []
        mock.delete.return_value = 0
        yield mock


class TestFAQSearchEndpoint:
    """Tests for GET /api/faq/search"""

    def test_search_success(self, client, mock_search_tool, mock_redis):
        """Test successful FAQ search"""
        mock_search_tool.search.return_value = {
            'success': True,
            'results': [
                {
                    'id': '123',
                    'question': 'Test question',
                    'answer': 'Test answer',
                    'score': 0.95
                }
            ],
            'count': 1
        }

        response = client.get('/api/faq/search?q=test')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['query'] == 'test'
        assert data['count'] == 1
        assert len(data['results']) == 1
        assert data['results'][0]['question'] == 'Test question'

    def test_search_missing_query(self, client):
        """Test search with missing query parameter"""
        response = client.get('/api/faq/search')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error']['code'] == 'invalid_input'

    def test_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.get('/api/faq/search?q=')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_search_with_limit(self, client, mock_search_tool, mock_redis):
        """Test search with custom limit"""
        mock_search_tool.search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }

        response = client.get('/api/faq/search?q=test&limit=5')
        
        assert response.status_code == 200
        mock_search_tool.search.assert_called_with(
            query='test',
            limit=5,
            category=None
        )

    def test_search_with_category(self, client, mock_search_tool, mock_redis):
        """Test search with category filter"""
        mock_search_tool.search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }

        response = client.get('/api/faq/search?q=test&category=billing')
        
        assert response.status_code == 200
        mock_search_tool.search.assert_called_with(
            query='test',
            limit=10,
            category='billing'
        )

    def test_search_cache_hit(self, client, mock_redis):
        """Test search returns cached result"""
        cached_data = {
            'query': 'test',
            'results': [{'id': '123', 'question': 'Cached'}],
            'count': 1,
            'cached': False
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        response = client.get('/api/faq/search?q=test')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['cached'] == True
        assert data['results'][0]['question'] == 'Cached'


class TestGetFAQEndpoint:
    """Tests for GET /api/faq/{id}"""

    def test_get_faq_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful FAQ retrieval"""
        mock_mgmt_tool.get_faq.return_value = {
            'success': True,
            'faq': {
                'id': '123',
                'question': 'Test question',
                'answer': 'Test answer',
                'category': 'general',
                'tags': ['test']
            }
        }

        response = client.get('/api/faq/123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'faq' in data
        assert data['faq']['id'] == '123'

    def test_get_faq_not_found(self, client, mock_mgmt_tool, mock_redis):
        """Test FAQ not found"""
        mock_mgmt_tool.get_faq.return_value = {
            'success': False,
            'error': 'FAQ not found'
        }

        response = client.get('/api/faq/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error']['code'] == 'not_found'


class TestCreateFAQEndpoint:
    """Tests for POST /api/faq"""

    def test_create_faq_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful FAQ creation"""
        mock_mgmt_tool.create_faq.return_value = {
            'success': True,
            'faq_id': '123'
        }

        response = client.post('/api/faq', json={
            'question': 'New question',
            'answer': 'New answer',
            'category': 'billing',
            'tags': ['payment']
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['faq_id'] == '123'
        assert 'message' in data

    def test_create_faq_missing_fields(self, client):
        """Test create FAQ with missing required fields"""
        response = client.post('/api/faq', json={
            'question': 'Test'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'invalid_input'

    def test_create_faq_empty_question(self, client):
        """Test create FAQ with empty question"""
        response = client.post('/api/faq', json={
            'question': '',
            'answer': 'Test answer'
        })
        
        assert response.status_code == 400

    def test_create_faq_cache_invalidation(self, client, mock_mgmt_tool, mock_redis):
        """Test that cache is invalidated after creation"""
        mock_mgmt_tool.create_faq.return_value = {
            'success': True,
            'faq_id': '123'
        }

        client.post('/api/faq', json={
            'question': 'Test',
            'answer': 'Test'
        })
        
        mock_redis.scan_iter.assert_called()


class TestUpdateFAQEndpoint:
    """Tests for PUT /api/faq/{id}"""

    def test_update_faq_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful FAQ update"""
        mock_mgmt_tool.update_faq.return_value = {
            'success': True
        }

        response = client.put('/api/faq/123', json={
            'question': 'Updated question'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['faq_id'] == '123'

    def test_update_faq_not_found(self, client, mock_mgmt_tool, mock_redis):
        """Test update non-existent FAQ"""
        mock_mgmt_tool.update_faq.return_value = {
            'success': False,
            'error': 'FAQ not found'
        }

        response = client.put('/api/faq/nonexistent', json={
            'answer': 'Updated'
        })
        
        assert response.status_code == 404

    def test_update_faq_no_fields(self, client):
        """Test update with no fields"""
        response = client.put('/api/faq/123', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No fields to update' in data['error']['message']


class TestDeleteFAQEndpoint:
    """Tests for DELETE /api/faq/{id}"""

    def test_delete_faq_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful FAQ deletion"""
        mock_mgmt_tool.delete_faq.return_value = {
            'success': True
        }

        response = client.delete('/api/faq/123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['faq_id'] == '123'

    def test_delete_faq_not_found(self, client, mock_mgmt_tool, mock_redis):
        """Test delete non-existent FAQ"""
        mock_mgmt_tool.delete_faq.return_value = {
            'success': False,
            'error': 'FAQ not found'
        }

        response = client.delete('/api/faq/nonexistent')
        
        assert response.status_code == 404


class TestCategoriesEndpoint:
    """Tests for GET /api/faq/categories"""

    def test_get_categories_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful categories retrieval"""
        mock_mgmt_tool.get_categories.return_value = {
            'success': True,
            'categories': [
                {'name': 'billing', 'count': 10},
                {'name': 'technical', 'count': 5}
            ],
            'count': 2
        }

        response = client.get('/api/faq/categories')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 2
        assert len(data['categories']) == 2


class TestStatsEndpoint:
    """Tests for GET /api/faq/stats"""

    def test_get_stats_success(self, client, mock_mgmt_tool, mock_redis):
        """Test successful stats retrieval"""
        mock_mgmt_tool.get_stats.return_value = {
            'success': True,
            'stats': {
                'total_faqs': 100,
                'total_categories': 5,
                'avg_answer_length': 250
            }
        }

        response = client.get('/api/faq/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'stats' in data
        assert data['stats']['total_faqs'] == 100


@pytest.fixture
def client():
    """Create Flask test client"""
    from flask import Flask
    from src.routes.faq import bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(bp)
    
    with patch('src.routes.faq.FAQ_AGENT_AVAILABLE', True):
        with app.test_client() as client:
            yield client
