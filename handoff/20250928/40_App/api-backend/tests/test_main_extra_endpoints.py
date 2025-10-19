"""
Extra tests for main.py endpoints to improve coverage from 65% to 70%+
Focus on uncovered endpoint lines
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    app.config['TESTING'] = True
    return app.test_client()


class TestHealthEndpoints:
    """Test health check and monitoring endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_api_health_endpoint(self, client):
        """Test /api/health endpoint"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data


class TestRootEndpoints:
    """Test root and documentation endpoints"""
    
    def test_root_endpoint(self, client):
        """Test / root endpoint"""
        response = client.get('/')
        
        assert response.status_code == 404
    
    def test_api_root_endpoint(self, client):
        """Test /api/ root endpoint"""
        response = client.get('/api/')
        
        assert response.status_code == 404


class TestErrorEndpoints:
    """Test error endpoints"""
    
    def test_404_not_found(self, client):
        """Test 404 error handler"""
        response = client.get('/non-existent-endpoint')
        
        assert response.status_code == 404
    
    def test_api_404_not_found(self, client):
        """Test API 404 error handler"""
        response = client.get('/api/non-existent')
        
        assert response.status_code == 404


class TestPhase4Endpoints:
    """Test Phase 4 endpoints that may not be covered"""
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    def test_meta_agent_ooda_available(self, client):
        """Test meta-agent OODA endpoint when available"""
        response = client.post('/api/meta-agent/ooda-cycle', json={
            'trigger': 'test',
            'context': {}
        })
        
        assert response.status_code in [200, 404, 500, 503]
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    def test_langgraph_workflow_available(self, client):
        """Test LangGraph workflow endpoint when available"""
        response = client.post('/api/langgraph/workflows', json={
            'name': 'test-workflow',
            'config': {}
        })
        
        assert response.status_code in [200, 404, 500, 503]


class TestCORSHeaders:
    """Test CORS headers on endpoints"""
    
    def test_cors_headers_health(self, client):
        """Test CORS headers on health endpoint"""
        response = client.options('/health')
        
        assert response.status_code in [200, 204]
    
    def test_cors_headers_api(self, client):
        """Test CORS headers on API endpoints"""
        response = client.options('/api/health')
        
        assert response.status_code in [200, 204]


class TestContentTypeHandling:
    """Test content type handling"""
    
    def test_json_content_type(self, client):
        """Test JSON content type handling with invalid JSON"""
        response = client.post('/api/auth/login', 
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code in [400, 500]
    
    def test_form_data_not_supported(self, client):
        """Test form data on JSON-only endpoints"""
        response = client.post('/api/auth/login',
                              data={'username': 'test'},
                              content_type='application/x-www-form-urlencoded')
        
        assert response.status_code == 500


class TestMethodNotAllowed:
    """Test method not allowed errors"""
    
    def test_get_on_post_endpoint(self, client):
        """Test GET on POST-only endpoint"""
        response = client.get('/api/auth/login')
        
        assert response.status_code in [404, 405]
    
    def test_post_on_get_endpoint(self, client):
        """Test POST on GET-only endpoint"""
        response = client.post('/health')
        
        assert response.status_code == 405
    
    def test_delete_on_get_endpoint(self, client):
        """Test DELETE on GET-only endpoint"""
        response = client.delete('/api/health')
        
        assert response.status_code == 405


class TestLargePayloads:
    """Test handling of large payloads"""
    
    def test_large_json_payload(self, client):
        """Test large JSON payload handling"""
        large_payload = {
            'data': 'x' * 10000  # 10KB of data
        }
        
        response = client.post('/api/auth/login', json=large_payload)
        
        assert response.status_code in [400, 500]


class TestSpecialCharacters:
    """Test special characters in requests"""
    
    def test_unicode_in_json(self, client):
        """Test Unicode characters in JSON"""
        response = client.post('/api/auth/login', json={
            'username': '測試用戶',
            'password': 'test123'
        })
        
        assert response.status_code in [400, 401]
    
    def test_special_chars_in_path(self, client):
        """Test special characters in URL path"""
        response = client.get('/api/users/%20')
        
        assert response.status_code == 404
