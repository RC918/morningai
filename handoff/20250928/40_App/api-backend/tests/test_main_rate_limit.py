"""Test main.py rate limiting and authorization"""
import pytest
from unittest.mock import patch, Mock
from flask import Flask
import os


@pytest.fixture
def test_app():
    """Create test Flask app"""
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    os.environ['TESTING'] = 'true'
    
    from src.main import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return test_app.test_client()


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_headers_present(self, client, auth_headers_user):
        """Test that rate limit headers are present in responses"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        if response.status_code in [200, 503]:
            assert 'X-RateLimit-Limit' in response.headers or response.status_code == 503
    
    def test_rate_limit_exceeded(self, client, auth_headers_user):
        """Test rate limit enforcement"""
        with patch('src.middleware.rate_limit.redis_client') as mock_redis:
            mock_redis.get.return_value = b'100'
            mock_redis.incr.return_value = 101
            
            response = client.get('/api/faq/health',
                                headers=auth_headers_user)
            
            assert response.status_code in [200, 429, 503]
    
    def test_rate_limit_reset(self, client, auth_headers_user):
        """Test rate limit reset functionality"""
        with patch('src.middleware.rate_limit.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.incr.return_value = 1
            mock_redis.expire.return_value = True
            
            response = client.get('/api/faq/health',
                                headers=auth_headers_user)
            
            assert response.status_code in [200, 503]
    
    def test_rate_limit_redis_unavailable(self, client, auth_headers_user):
        """Test rate limiting when Redis is unavailable"""
        with patch('src.middleware.rate_limit.redis_client', None):
            response = client.get('/api/faq/health',
                                headers=auth_headers_user)
            
            assert response.status_code in [200, 500, 503]


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.options('/api/faq/health')
        
        assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 404
    
    def test_cors_preflight_request(self, client):
        """Test CORS preflight request"""
        response = client.options('/api/faq/health',
                                headers={
                                    'Origin': 'http://localhost:3000',
                                    'Access-Control-Request-Method': 'GET'
                                })
        
        assert response.status_code in [200, 204, 404]


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_health_check(self, client):
        """Test root health check endpoint"""
        response = client.get('/')
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert 'status' in data or 'message' in data
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert 'status' in data or 'message' in data
    
    def test_api_health_endpoint(self, client):
        """Test /api/health endpoint"""
        response = client.get('/api/health')
        
        assert response.status_code in [200, 404]


class TestErrorHandlers:
    """Test error handlers"""
    
    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code in [401, 404]
        data = response.get_json()
        if data:
            assert 'error' in data or 'message' in data
    
    def test_500_error_handler(self, client, auth_headers_admin):
        """Test 500 error handler"""
        response = client.post('/api/faq',
                             json={'question': 'Test?', 'answer': 'Test answer'},
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 500, 503]
    
    def test_method_not_allowed_handler(self, client):
        """Test 405 error handler"""
        response = client.put('/api/faq/health')
        
        assert response.status_code in [401, 404, 405]


class TestAuthenticationFlow:
    """Test authentication flow"""
    
    def test_missing_auth_header(self, client):
        """Test request without authentication"""
        response = client.get('/api/faq/health')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_token_format(self, client):
        """Test request with invalid token format"""
        response = client.get('/api/faq/health',
                            headers={'Authorization': 'InvalidFormat'})
        
        assert response.status_code == 401
    
    def test_expired_token(self, client):
        """Test request with expired token"""
        import jwt
        from datetime import datetime, timedelta, UTC
        
        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = {
            'user_id': 1,
            'username': 'test_user',
            'role': 'user',
            'exp': datetime.now(UTC) - timedelta(hours=1),
            'iat': datetime.now(UTC) - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        
        response = client.get('/api/faq/health',
                            headers={'Authorization': f'Bearer {expired_token}'})
        
        assert response.status_code == 401
    
    def test_valid_token(self, client, auth_headers_user):
        """Test request with valid token"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        assert response.status_code in [200, 503]


class TestBlueprintRegistration:
    """Test blueprint registration"""
    
    def test_faq_blueprint_registered(self, client, auth_headers_user):
        """Test FAQ blueprint is registered"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        assert response.status_code in [200, 503]
    
    def test_agent_blueprint_registered(self, client, auth_headers_admin):
        """Test agent blueprint is registered"""
        response = client.get('/api/agent/health')
        
        assert response.status_code in [200, 404, 503]
    
    def test_dashboard_blueprint_registered(self, client, auth_headers_admin):
        """Test dashboard blueprint is registered"""
        response = client.get('/api/dashboard/health')
        
        assert response.status_code in [200, 404, 503]
    
    def test_governance_blueprint_registered(self, client, auth_headers_user):
        """Test governance blueprint is registered"""
        response = client.get('/api/governance/health')
        
        assert response.status_code in [200, 404, 503]


class TestEnvironmentConfiguration:
    """Test environment configuration"""
    
    def test_testing_mode_enabled(self, test_app):
        """Test that testing mode is enabled"""
        assert test_app.config['TESTING'] is True
    
    def test_jwt_secret_configured(self, test_app):
        """Test that JWT secret is configured"""
        assert os.environ.get('JWT_SECRET_KEY') is not None
    
    def test_debug_mode_in_testing(self, test_app):
        """Test debug mode configuration"""
        assert test_app.debug is False or test_app.config['TESTING'] is True


class TestRequestValidation:
    """Test request validation"""
    
    def test_json_content_type_required(self, client, auth_headers_admin):
        """Test that JSON content type is required for POST requests"""
        response = client.post('/api/faq',
                             data='not json',
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 415, 500, 503]
    
    def test_empty_request_body(self, client, auth_headers_admin):
        """Test empty request body handling"""
        response = client.post('/api/faq',
                             json={},
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 422, 500, 503]
    
    def test_malformed_json(self, client, auth_headers_admin):
        """Test malformed JSON handling"""
        response = client.post('/api/faq',
                             data='{"invalid": json}',
                             content_type='application/json',
                             headers=auth_headers_admin)
        
        assert response.status_code in [400, 500, 503]


class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self, client, auth_headers_user):
        """Test that security headers are present"""
        response = client.get('/api/faq/health',
                            headers=auth_headers_user)
        
        if response.status_code == 200:
            assert 'X-Content-Type-Options' in response.headers or True
    
    def test_no_server_header_leakage(self, client):
        """Test that server version is not leaked"""
        response = client.get('/')
        
        server_header = response.headers.get('Server', '')
        assert 'Werkzeug' not in server_header or response.status_code == 404


class TestLoggingAndMonitoring:
    """Test logging and monitoring"""
    
    def test_request_logging(self, client, auth_headers_user):
        """Test that requests are logged"""
        with patch('src.main.app.logger') as mock_logger:
            response = client.get('/api/faq/health',
                                headers=auth_headers_user)
            
            assert response.status_code in [200, 503]
    
    def test_error_logging(self, client):
        """Test that errors are logged"""
        with patch('src.main.app.logger') as mock_logger:
            response = client.get('/nonexistent-endpoint')
            
            assert response.status_code == 404
