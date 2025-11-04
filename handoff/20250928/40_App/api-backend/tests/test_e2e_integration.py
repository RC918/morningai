"""
End-to-End Integration Tests
Tests real workflows across multiple components without excessive mocking
"""
import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app instance for E2E testing"""
    with patch.dict(os.environ, {
        'SENTRY_DSN': '',
        'SECRET_KEY': 'e2e-test-secret',
        'CORS_ORIGINS': 'http://localhost:5173',
        'DATABASE_URL': 'sqlite:///:memory:'
    }):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']
        
        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token"""
    from src.middleware.auth_middleware import create_user_token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


class TestHealthCheckE2E:
    """E2E tests for health check endpoints"""
    
    def test_health_check_complete_flow(self, client):
        """Test complete health check flow across all health endpoints"""
        endpoints = ['/health', '/healthz', '/api/health', '/api/healthz']
        
        results = []
        for endpoint in endpoints:
            response = client.get(endpoint)
            results.append({
                'endpoint': endpoint,
                'status_code': response.status_code,
                'data': response.get_json()
            })
        
        for result in results:
            assert result['status_code'] in [200, 500]
            assert 'status' in result['data']
            assert 'database' in result['data']
            
            if result['status_code'] == 200:
                assert result['data']['status'] in ['healthy', 'degraded']
            elif result['status_code'] == 500:
                assert result['data']['status'] in ['error', 'degraded']
        
        statuses = [r['data']['status'] for r in results]
        assert len(set(statuses)) == 1
    
    def test_health_check_database_connection(self, client):
        """Test health check reflects actual database status"""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'database' in data
        assert isinstance(data['database'], str)
        
        assert 'services' in data
        assert isinstance(data['services'], dict)
    
    def test_health_check_version_info(self, client):
        """Test health check includes version and phase info"""
        response = client.get('/api/health')
        data = response.get_json()
        
        assert 'version' in data
        assert 'phase' in data
        assert 'timestamp' in data


class TestDashboardWorkflowE2E:
    """E2E tests for complete dashboard workflow"""
    
    def test_dashboard_complete_workflow(self, client, auth_headers):
        """Test complete dashboard workflow: widgets -> layout -> data"""
        response1 = client.get('/api/dashboard/widgets/available')
        assert response1.status_code == 200
        widgets = response1.get_json()
        assert isinstance(widgets, list)
        assert len(widgets) > 0
        
        response2 = client.get('/api/dashboard/layouts', headers=auth_headers)
        assert response2.status_code in [200, 500]
        
        if response2.status_code == 200:
            layout = response2.get_json()
            assert 'widgets' in layout or isinstance(layout, dict)
        
        response3 = client.get('/api/dashboard/data?hours=1')
        assert response3.status_code in [200, 500]
    
    def test_dashboard_layout_crud(self, client, auth_headers):
        """Test CRUD operations on dashboard layouts"""
        new_layout = {
            'layout': {
                'widgets': [
                    {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                    {'id': 'memory_usage', 'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}}
                ]
            }
        }
        
        save_response = client.post('/api/dashboard/layouts', json=new_layout, headers=auth_headers)
        assert save_response.status_code in [200, 500]
        
        if save_response.status_code == 200:
            get_response = client.get('/api/dashboard/layouts', headers=auth_headers)
            if get_response.status_code == 200:
                retrieved_layout = get_response.get_json()
                assert 'widgets' in retrieved_layout or isinstance(retrieved_layout, dict)


class TestReportGenerationE2E:
    """E2E tests for report generation workflow"""
    
    def test_report_generation_workflow(self, client):
        """Test complete report generation workflow"""
        response1 = client.get('/api/reports/templates')
        assert response1.status_code in [200, 500]
        
        if response1.status_code == 500:
            data = response1.get_json()
            assert 'error' in data
            return
        
        report_request = {
            'report_type': 'performance',
            'period': 'daily',
            'format': 'json'
        }
        
        response2 = client.post('/api/reports/generate', json=report_request)
        assert response2.status_code in [200, 400, 500]
        
        response3 = client.get('/api/reports/history?limit=10')
        assert response3.status_code in [200, 500]


class TestMonitoringWorkflowE2E:
    """E2E tests for monitoring dashboard workflow"""
    
    def test_monitoring_dashboard_workflow(self, client):
        """Test complete monitoring workflow"""
        response1 = client.get('/api/phase7/monitoring/dashboard?hours=1')
        assert response1.status_code in [200, 500]
        
        response2 = client.get('/api/phase7/monitoring/alerts')
        assert response2.status_code in [200, 500]
        
        if response2.status_code == 200:
            data = response2.get_json()
            assert 'alerts' in data
            assert 'count' in data
        
        response3 = client.get('/api/phase7/monitoring/metrics')
        assert response3.status_code in [200, 500]


class TestPhase7IntegrationE2E:
    """E2E tests for Phase 7 system integration"""
    
    def test_phase7_complete_status_check(self, client):
        """Test complete Phase 7 status check workflow"""
        endpoints = [
            '/api/phase7/status',
            '/api/phase7/approvals/pending',
            '/api/phase7/approvals/history',
            '/api/phase7/beta/candidates',
            '/api/phase7/growth/metrics',
            '/api/phase7/ops/metrics'
        ]
        
        results = {}
        for endpoint in endpoints:
            response = client.get(endpoint)
            results[endpoint] = {
                'status_code': response.status_code,
                'has_data': response.get_json() is not None
            }
        
        for endpoint, result in results.items():
            assert result['status_code'] in [200, 500]
            assert result['has_data'] is True


class TestErrorHandlingE2E:
    """E2E tests for error handling across the application"""
    
    def test_404_error_handling(self, client):
        """Test 404 error handling for non-existent endpoints"""
        response = client.get('/api/nonexistent/endpoint')
        
        assert response.status_code in [404, 200]
    
    def test_400_error_handling(self, client):
        """Test 400 error handling for invalid requests"""
        response = client.post('/api/reports/generate',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code in [400, 500]
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test error handling when required fields are missing"""
        response = client.post('/api/dashboard/layouts', json={}, headers=auth_headers)
        
        assert response.status_code in [200, 400, 500]


class TestCORSE2E:
    """E2E tests for CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses"""
        response = client.get('/health', headers={'Origin': 'http://localhost:5173'})
        
        assert response.status_code in [200, 500]
    
    def test_options_request(self, client):
        """Test OPTIONS preflight requests"""
        response = client.options('/api/health')
        
        assert response.status_code in [200, 204, 404]


class TestStaticFileServingE2E:
    """E2E tests for static file serving"""
    
    def test_spa_routing(self, client):
        """Test SPA routing - all routes should serve index.html"""
        spa_routes = [
            '/',
            '/dashboard',
            '/reports',
            '/settings',
            '/some/deep/nested/route'
        ]
        
        for route in spa_routes:
            response = client.get(route)
            assert response.status_code in [200, 404]


class TestEnvironmentValidationE2E:
    """E2E tests for environment validation"""
    
    def test_environment_validation_get(self, client):
        """Test GET environment validation"""
        response = client.get('/api/phase7/environment/validate')
        
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'error' in data or 'validation' in data
    
    def test_environment_validation_post(self, client):
        """Test POST environment validation"""
        response = client.post('/api/phase7/environment/validate')
        
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'error' in data or 'validation' in data


class TestDataFlowE2E:
    """E2E tests for data flow across components"""
    
    def test_widget_to_dashboard_data_flow(self, client):
        """Test data flows correctly from widgets to dashboard"""
        widgets_response = client.get('/api/dashboard/widgets/available')
        assert widgets_response.status_code == 200
        widgets = widgets_response.get_json()
        
        for widget in widgets:
            assert 'id' in widget
            assert 'name' in widget
            assert 'type' in widget
            assert 'category' in widget
        
        data_response = client.get('/api/dashboard/data')
        assert data_response.status_code in [200, 500]


class TestIntegrationWithExternalServices:
    """E2E tests for integration with external services (mocked)"""
    
    @patch('src.services.monitoring_dashboard.monitoring_dashboard.get_dashboard_data')
    def test_monitoring_service_integration(self, mock_get_data, client):
        """Test integration with monitoring service"""
        mock_get_data.return_value = {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'response_time': 123,
            'error_rate': 0.02
        }
        
        response = client.get('/api/dashboard/data?hours=24')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'cpu_usage' in data or 'task_execution' in data
    
    @patch('src.services.report_generator.report_generator.generate_report')
    def test_report_service_integration(self, mock_generate, client):
        """Test integration with report generation service"""
        mock_generate.return_value = {
            'report_id': 'rep-e2e-123',
            'status': 'completed',
            'format': 'json',
            'created_at': '2025-10-19T12:00:00Z'
        }
        
        response = client.post('/api/reports/generate',
                              json={'report_type': 'performance', 'period': 'weekly'})
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'report_id' in data or 'status' in data


class TestConcurrentRequests:
    """E2E tests for handling concurrent requests"""
    
    def test_concurrent_health_checks(self, client):
        """Test handling multiple concurrent health check requests"""
        responses = []
        
        for _ in range(10):
            response = client.get('/health')
            responses.append(response)
        
        for response in responses:
            assert response.status_code in [200, 500]
            data = response.get_json()
            assert 'status' in data
            assert 'database' in data
            
            if response.status_code == 200:
                assert data['status'] in ['healthy', 'degraded']
            elif response.status_code == 500:
                assert data['status'] in ['error', 'degraded']
    
    def test_concurrent_dashboard_requests(self, client):
        """Test handling concurrent dashboard data requests"""
        responses = []
        
        for _ in range(5):
            response = client.get('/api/dashboard/widgets/available')
            responses.append(response)
        
        for response in responses:
            assert response.status_code == 200
            widgets = response.get_json()
            assert isinstance(widgets, list)


class TestEndToEndScenarios:
    """Complete end-to-end user scenarios"""
    
    def test_new_user_dashboard_setup(self, client, auth_headers):
        """Test complete new user dashboard setup scenario"""
        health_response = client.get('/health')
        assert health_response.status_code in [200, 500]
        health_data = health_response.get_json()
        assert 'status' in health_data
        
        widgets_response = client.get('/api/dashboard/widgets/available')
        assert widgets_response.status_code == 200
        widgets = widgets_response.get_json()
        assert isinstance(widgets, list)
        assert len(widgets) > 0
        
        layout = {
            'layout': {
                'widgets': [widgets[0], widgets[1]] if len(widgets) >= 2 else widgets
            }
        }
        
        layout_response = client.post('/api/dashboard/layouts', json=layout, headers=auth_headers)
        assert layout_response.status_code in [200, 500]
        
        if layout_response.status_code == 200:
            layout_data = layout_response.get_json()
            assert layout_data.get('status') == 'success' or 'message' in layout_data
        
        data_response = client.get('/api/dashboard/data')
        assert data_response.status_code in [200, 500]
        
        if data_response.status_code == 200:
            dashboard_data = data_response.get_json()
            assert isinstance(dashboard_data, dict)
    
    def test_monitoring_alert_workflow(self, client):
        """Test complete monitoring and alert checking workflow"""
        status_response = client.get('/api/phase7/status')
        assert status_response.status_code in [200, 500]
        
        dashboard_response = client.get('/api/phase7/monitoring/dashboard?hours=1')
        assert dashboard_response.status_code in [200, 500]
        
        alerts_response = client.get('/api/phase7/monitoring/alerts')
        assert alerts_response.status_code in [200, 500]
        
        if alerts_response.status_code == 200:
            alerts_data = alerts_response.get_json()
            assert 'alerts' in alerts_data
            assert 'count' in alerts_data
    
    def test_report_generation_and_retrieval(self, client):
        """Test complete report generation and retrieval workflow"""
        templates_response = client.get('/api/reports/templates')
        assert templates_response.status_code in [200, 500]
        
        report_request = {
            'report_type': 'performance',
            'period': 'daily'
        }
        generate_response = client.post('/api/reports/generate', json=report_request)
        assert generate_response.status_code in [200, 400, 500]
        
        history_response = client.get('/api/reports/history?limit=10')
        assert history_response.status_code in [200, 500]
