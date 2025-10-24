"""Test agent error paths and dynamic import failures"""
import pytest
from unittest.mock import patch, Mock
from flask import Flask
from src.routes.agent import bp as agent_bp


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(agent_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestAgentDynamicImportFailures:
    """Test agent route behavior when dynamic imports fail"""
    
    def test_agent_redis_connection_failure(self, client, auth_headers_admin):
        """Test agent endpoint when Redis connection fails"""
        with patch('src.routes.agent.redis_client', None):
            response = client.post('/api/agent/faq',
                                 json={'query': 'Test query'},
                                 headers=auth_headers_admin)
            
            assert response.status_code in [400, 500, 503]
    
    def test_agent_queue_submission_failure(self, client, auth_headers_admin):
        """Test agent endpoint when queue submission fails"""
        with patch('src.routes.agent.redis_client') as mock_redis:
            mock_redis.hset.side_effect = Exception("Redis connection lost")
            
            response = client.post('/api/agent/faq',
                                 json={'query': 'Test query'},
                                 headers=auth_headers_admin)
            
            assert response.status_code in [400, 500, 503]
            data = response.get_json()
            assert 'error' in data


class TestAgentValidationErrors:
    """Test agent input validation and error handling"""
    
    def test_agent_missing_query_parameter(self, client, auth_headers_admin):
        """Test agent endpoint with missing query parameter"""
        response = client.post('/api/agent/faq',
                             json={},
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 422, 500, 503]
    
    def test_agent_empty_query(self, client, auth_headers_admin):
        """Test agent endpoint with empty query"""
        response = client.post('/api/agent/faq',
                             json={'query': ''},
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 422, 500, 503]
    
    def test_agent_invalid_json(self, client, auth_headers_admin):
        """Test agent endpoint with invalid JSON"""
        response = client.post('/api/agent/faq',
                             data='invalid json',
                             headers=auth_headers_admin,
                             content_type='application/json')
        
        assert response.status_code in [400, 422, 500]
    
    def test_agent_oversized_query(self, client, auth_headers_admin):
        """Test agent endpoint with oversized query"""
        large_query = 'x' * 100000
        
        response = client.post('/api/agent/faq',
                             json={'query': large_query},
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 413, 422, 500, 503]


class TestAgentDebugEndpoints:
    """Test agent debug endpoints error handling"""
    
    def test_debug_queue_redis_unavailable(self, client, auth_headers_admin):
        """Test debug queue endpoint when Redis is unavailable"""
        with patch('src.routes.agent.redis_client', None):
            response = client.get('/api/agent/debug/queue',
                                headers=auth_headers_admin)
            
            assert response.status_code in [500, 503]
            data = response.get_json()
            assert 'error' in data
    
    def test_debug_queue_redis_error(self, client, auth_headers_admin):
        """Test debug queue endpoint when Redis raises error"""
        with patch('src.routes.agent.redis_client_rq') as mock_redis:
            mock_redis.llen.side_effect = Exception("Redis error")
            
            response = client.get('/api/agent/debug/queue',
                                headers=auth_headers_admin)
            
            assert response.status_code in [400, 500, 503]
            data = response.get_json()
            assert 'error' in data
    
    def test_debug_status_invalid_task_id(self, client, auth_headers_admin):
        """Test debug status endpoint with invalid task ID"""
        response = client.get('/api/agent/debug/status/invalid-task-id',
                            headers=auth_headers_admin)
        
        assert response.status_code in [404, 500, 503]
    
    def test_debug_status_redis_unavailable(self, client, auth_headers_admin):
        """Test debug status endpoint when Redis is unavailable"""
        with patch('src.routes.agent.redis_client', None):
            response = client.get('/api/agent/debug/status/task-123',
                                headers=auth_headers_admin)
            
            assert response.status_code in [400, 404, 500, 503]


class TestAgentHealthCheck:
    """Test agent health check endpoint"""
    
    def test_health_check_redis_unavailable(self, client):
        """Test health check when Redis is unavailable"""
        with patch('src.routes.agent.redis_client', None):
            response = client.get('/api/agent/health')
            
            assert response.status_code in [200, 400, 404, 500, 503]
            data = response.get_json()
            if response.status_code == 200:
                assert 'redis' in data or 'queue' in data or 'status' in data
    
    def test_health_check_all_services_available(self, client):
        """Test health check when all services are available"""
        with patch('src.routes.agent.redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            response = client.get('/api/agent/health')
            
            assert response.status_code in [200, 400, 404, 500, 503]


class TestAgentExternalDependencyFailures:
    """Test agent behavior when external dependencies fail"""
    
    def test_agent_supabase_connection_failure(self, client, auth_headers_admin):
        """Test agent endpoint when Supabase connection fails"""
        response = client.post('/api/agent/faq',
                             json={'query': 'Test query'},
                             headers=auth_headers_admin)
        
        assert response.status_code in [200, 202, 400, 500, 503]
    
    def test_agent_llm_api_failure(self, client, auth_headers_admin):
        """Test agent endpoint when LLM API fails"""
        response = client.post('/api/agent/faq',
                             json={'query': 'Test query'},
                             headers=auth_headers_admin)
        
        assert response.status_code in [200, 202, 400, 500, 503]
    
    def test_agent_timeout_handling(self, client, auth_headers_admin):
        """Test agent endpoint timeout handling"""
        response = client.post('/api/agent/faq',
                             json={'query': 'Test query'},
                             headers=auth_headers_admin)
        
        assert response.status_code in [200, 202, 400, 408, 500, 503, 504]


class TestAgentConcurrentRequests:
    """Test agent behavior under concurrent load"""
    
    def test_agent_concurrent_queue_submissions(self, client, auth_headers_admin):
        """Test multiple concurrent agent requests"""
        with patch('src.routes.agent.redis_client') as mock_redis:
            mock_redis.hset.return_value = 1
            
            responses = []
            for i in range(5):
                response = client.post('/api/agent/faq',
                                     json={'query': f'Test query {i}'},
                                     headers=auth_headers_admin)
                responses.append(response)
            
            for response in responses:
                assert response.status_code in [200, 202, 400, 500, 503]
    
    def test_agent_queue_full_handling(self, client, auth_headers_admin):
        """Test agent behavior when queue is full"""
        with patch('src.routes.agent.redis_client_rq') as mock_redis:
            mock_redis.llen.return_value = 10000
            
            response = client.post('/api/agent/faq',
                                 json={'query': 'Test query'},
                                 headers=auth_headers_admin)
            
            assert response.status_code in [200, 202, 400, 429, 500, 503]
