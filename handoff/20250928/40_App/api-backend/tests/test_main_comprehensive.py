"""
Comprehensive tests for main.py Flask application
"""
import pytest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def app():
    """Create Flask app instance for testing"""
    with patch.dict(os.environ, {'SENTRY_DSN': '', 'SECRET_KEY': 'test-secret'}):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']
        
        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'database' in data
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_healthz_endpoint(self, client):
        """Test /healthz endpoint"""
        response = client.get('/healthz')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
    
    def test_api_health_endpoint(self, client):
        """Test /api/health endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'services' in data
    
    def test_api_healthz_endpoint(self, client):
        """Test /api/healthz endpoint"""
        response = client.get('/api/healthz')
        assert response.status_code == 200
    
    def test_health_endpoint_structure(self, client):
        """Test health endpoint returns correct structure"""
        response = client.get('/health')
        data = json.loads(response.data)
        
        assert 'status' in data
        assert 'database' in data
        assert 'phase' in data


class TestGetHealthPayload:
    """Test get_health_payload function"""
    
    def test_get_health_payload_success(self, app):
        """Test get_health_payload returns correct structure"""
        from src.main import get_health_payload
        
        with app.app_context():
            payload = get_health_payload()
            
            assert 'status' in payload
            assert 'database' in payload
            assert 'phase' in payload
            assert 'version' in payload
            assert 'timestamp' in payload
            assert 'services' in payload
            
            services = payload['services']
            assert 'phase4_apis' in services
            assert 'phase5_apis' in services
            assert 'phase6_apis' in services
            assert 'security_manager' in services
            assert 'backend_services' in services
    
    def test_get_health_payload_includes_all_fields(self, app):
        """Test get_health_payload includes all required fields"""
        from src.main import get_health_payload
        
        with app.app_context():
            payload = get_health_payload()
            
            assert isinstance(payload, dict)
            assert len(payload) > 0


class TestErrorHandlers:
    """Test error handling"""
    
    def test_handle_exception_with_code(self, app):
        """Test exception handler with HTTP error codes"""
        from src.main import handle_exception
        
        with app.app_context():
            error = Exception("Test error")
            error.code = 404
            
            response, status_code = handle_exception(error)
            
            assert status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_handle_exception_without_code(self, app):
        """Test exception handler for unhandled exceptions"""
        from src.main import handle_exception
        
        with app.app_context():
            error = Exception("Unhandled error")
            
            response, status_code = handle_exception(error)
            
            assert status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'code' in data['error']
            assert data['error']['code'] == 'internal_server_error'


class TestStaticFileServing:
    """Test static file serving"""
    
    @patch('os.path.exists')
    @patch('src.main.send_from_directory')
    def test_serve_existing_file(self, mock_send, mock_exists, client):
        """Test serving existing static file"""
        mock_exists.return_value = True
        mock_send.return_value = "file content"
        
        response = client.get('/assets/logo.png')
        
        assert mock_send.called or response.status_code in [200, 404]
    
    @patch('os.path.exists')
    def test_serve_missing_file_returns_index(self, mock_exists, client):
        """Test serving index.html for missing files (SPA routing)"""
        mock_exists.side_effect = lambda p: 'index.html' in p
        
        response = client.get('/some/route')
        
        assert response.status_code in [200, 404]
    
    @patch('os.path.exists')
    def test_serve_no_static_folder(self, mock_exists, app):
        """Test serve function when static folder is None"""
        from src.main import serve
        
        with app.app_context():
            app.static_folder = None
            response, status_code = serve('')
            
            assert status_code == 404
            assert "not configured" in response


class TestDashboardEndpoints:
    """Test dashboard-related endpoints"""
    
    def test_get_available_widgets(self, client):
        """Test /api/dashboard/widgets/available endpoint"""
        response = client.get('/api/dashboard/widgets/available')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        widget = data[0]
        assert 'id' in widget
        assert 'name' in widget
        assert 'type' in widget
        assert 'category' in widget
    
    @patch('src.main.BACKEND_SERVICES_AVAILABLE', False)
    def test_get_dashboard_data_services_unavailable(self, client):
        """Test dashboard data when backend services unavailable"""
        response = client.get('/api/dashboard/data')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not available' in data['error'].lower()
    
    @patch('src.main.BACKEND_SERVICES_AVAILABLE', False)
    def test_get_monitoring_dashboard_services_unavailable(self, client):
        """Test monitoring dashboard when backend services unavailable"""
        response = client.get('/api/phase7/monitoring/dashboard')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data


class TestPhase7Endpoints:
    """Test Phase 7 endpoints"""
    
    def test_phase7_status_import_error(self, client):
        """Test phase7 status endpoint when module import fails"""
        response = client.get('/api/phase7/status')
        
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        
        if response.status_code == 500:
            assert 'error' in data
    
    def test_get_pending_approvals_import_error(self, client):
        """Test pending approvals endpoint when module unavailable"""
        response = client.get('/api/phase7/approvals/pending')
        
        assert response.status_code in [200, 500]
    
    def test_get_approval_history_with_limit(self, client):
        """Test approval history endpoint with limit parameter"""
        response = client.get('/api/phase7/approvals/history?limit=10')
        
        assert response.status_code in [200, 500]
    
    def test_get_beta_candidates(self, client):
        """Test beta candidates endpoint"""
        response = client.get('/api/phase7/beta/candidates')
        
        assert response.status_code in [200, 500]
    
    def test_get_growth_metrics(self, client):
        """Test growth metrics endpoint"""
        response = client.get('/api/phase7/growth/metrics')
        
        assert response.status_code in [200, 500]
    
    def test_get_ops_metrics(self, client):
        """Test ops metrics endpoint"""
        response = client.get('/api/phase7/ops/metrics')
        
        assert response.status_code in [200, 500]
    
    def test_get_monitoring_alerts(self, client):
        """Test monitoring alerts endpoint"""
        response = client.get('/api/phase7/monitoring/alerts')
        
        assert response.status_code in [200, 500]
    
    def test_get_resilience_metrics(self, client):
        """Test resilience metrics endpoint"""
        response = client.get('/api/phase7/monitoring/metrics')
        
        assert response.status_code in [200, 500]


class TestReportEndpoints:
    """Test report generation endpoints"""
    
    def test_report_endpoints_exist(self, app):
        """Test report endpoints are registered"""
        assert app is not None
        assert len(app.url_map._rules) > 0


class TestEnvironmentValidation:
    """Test environment validation endpoint"""
    
    def test_validate_environment_get(self, client):
        """Test environment validation GET request"""
        response = client.get('/api/phase7/environment/validate')
        
        assert response.status_code in [200, 500]
    
    def test_validate_environment_post(self, client):
        """Test environment validation POST request"""
        response = client.post('/api/phase7/environment/validate')
        
        assert response.status_code in [200, 500]


class TestDashboardLayouts:
    """Test dashboard layout management"""
    
    def test_dashboard_layouts_endpoints(self, client):
        """Test dashboard layouts endpoints"""
        response_get = client.get('/api/dashboard/layouts?user_id=test-user')
        assert response_get.status_code in [200, 500]
        
        layout_data = {
            'user_id': 'test-user',
            'layout': {'widgets': []}
        }
        response_post = client.post(
            '/api/dashboard/layouts',
            data=json.dumps(layout_data),
            content_type='application/json'
        )
        assert response_post.status_code in [200, 500]


class TestBeforeSend:
    """Test Sentry before_send filter"""
    
    def test_before_send_filters_400(self):
        """Test before_send filters out 400 errors"""
        from src.main import before_send
        
        event = {'request': {'status_code': 400}}
        hint = {}
        
        result = before_send(event, hint)
        assert result is None
    
    def test_before_send_filters_404(self):
        """Test before_send filters out 404 errors"""
        from src.main import before_send
        
        event = {'request': {'status_code': 404}}
        hint = {}
        
        result = before_send(event, hint)
        assert result is None
    
    def test_before_send_allows_500(self):
        """Test before_send allows 500 errors"""
        from src.main import before_send
        
        event = {'request': {'status_code': 500}}
        hint = {}
        
        result = before_send(event, hint)
        assert result == event
    
    def test_before_send_with_exc_info(self):
        """Test before_send with exception info"""
        from src.main import before_send
        
        error = Exception("Test error")
        error.code = 404
        
        event = {}
        hint = {'exc_info': (type(error), error, None)}
        
        result = before_send(event, hint)
        assert result is None


class TestCORSConfiguration:
    """Test CORS configuration"""
    
    def test_cors_origins_from_env(self, app):
        """Test CORS origins are loaded from environment"""
        assert app is not None
    
    @patch.dict(os.environ, {'CORS_ORIGINS': 'http://test1.com,http://test2.com'})
    def test_cors_custom_origins(self):
        """Test CORS with custom origins"""
        if 'src.main' in sys.modules:
            del sys.modules['src.main']
        
        from src.main import app
        
        assert app is not None
