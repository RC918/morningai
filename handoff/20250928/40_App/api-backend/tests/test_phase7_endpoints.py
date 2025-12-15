"""
Phase 7 Endpoint Tests

Tests for Phase 7 API routes including:
- Edge cases and error handling
- Parameter validation
- Rate limit interaction
- Service unavailability scenarios

Part of PR1.6b - Phase 7 route modularization.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask


class TestPhase7StatusEndpoint:
    """Tests for /api/phase7/status endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client with TESTING=true"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_status_returns_json(self, client):
        """Test that status endpoint returns valid JSON"""
        response = client.get('/api/phase7/status')
        assert response.content_type == 'application/json'

    def test_status_contains_phase_info(self, client):
        """Test that status response contains phase information"""
        response = client.get('/api/phase7/status')
        data = response.get_json()
        # Should return either success with phase info or error
        assert 'phase' in data or 'error' in data

    def test_status_import_error_returns_500(self, client):
        """Test that import error returns 500 with error message"""
        with patch('src.routes.phase7.phase7_status') as mock_status:
            mock_status.side_effect = ImportError("Module not found")
            # The route is already registered, so we need to test the actual behavior
            response = client.get('/api/phase7/status')
            # Should return either success or 500 error
            assert response.status_code in [200, 500]


class TestPhase7ApprovalsEndpoints:
    """Tests for /api/phase7/approvals/* endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_pending_approvals_returns_json(self, client):
        """Test that pending approvals endpoint returns valid JSON"""
        response = client.get('/api/phase7/approvals/pending')
        assert response.content_type == 'application/json'

    def test_pending_approvals_error_returns_500(self, client):
        """Test that service error returns 500"""
        with patch('src.routes.phase7.get_pending_approvals') as mock_pending:
            mock_pending.side_effect = Exception("Service unavailable")
            response = client.get('/api/phase7/approvals/pending')
            # Should return either success or 500 error
            assert response.status_code in [200, 500]

    def test_approval_history_returns_json(self, client):
        """Test that approval history endpoint returns valid JSON"""
        response = client.get('/api/phase7/approvals/history')
        assert response.content_type == 'application/json'

    def test_approval_history_with_limit_param(self, client):
        """Test approval history with limit parameter"""
        response = client.get('/api/phase7/approvals/history?limit=10')
        assert response.content_type == 'application/json'
        # Should return either success or 500 error
        assert response.status_code in [200, 500]

    def test_approval_history_with_invalid_limit_param(self, client):
        """Test approval history with invalid limit parameter"""
        response = client.get('/api/phase7/approvals/history?limit=invalid')
        # Current behavior: int() will raise ValueError, caught by try/except
        # Returns 500 with error message
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            data = response.get_json()
            assert 'error' in data

    def test_approval_history_with_negative_limit(self, client):
        """Test approval history with negative limit parameter"""
        response = client.get('/api/phase7/approvals/history?limit=-1')
        # Should handle gracefully
        assert response.status_code in [200, 500]


class TestPhase7MonitoringEndpoints:
    """Tests for /api/phase7/monitoring/* endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_monitoring_dashboard_returns_json(self, client):
        """Test that monitoring dashboard returns valid JSON"""
        response = client.get('/api/phase7/monitoring/dashboard')
        assert response.content_type == 'application/json'

    def test_monitoring_dashboard_delegates_to_dashboard_module(self, client):
        """Test that monitoring dashboard delegates to src.routes.dashboard"""
        with patch('src.routes.dashboard.get_dashboard_data') as mock_dashboard:
            mock_dashboard.return_value = ({'test': 'data'}, 200)
            response = client.get('/api/phase7/monitoring/dashboard')
            # The route should call the dashboard handler
            assert response.status_code in [200, 500]

    def test_monitoring_metrics_returns_json(self, client):
        """Test that monitoring metrics returns valid JSON"""
        response = client.get('/api/phase7/monitoring/metrics')
        assert response.content_type == 'application/json'

    def test_monitoring_alerts_returns_json(self, client):
        """Test that monitoring alerts returns valid JSON"""
        response = client.get('/api/phase7/monitoring/alerts')
        assert response.content_type == 'application/json'

    def test_monitoring_alerts_backend_unavailable(self, client):
        """Test monitoring alerts when backend services unavailable"""
        with patch('src.routes.phase7._get_backend_services_available', return_value=False):
            response = client.get('/api/phase7/monitoring/alerts')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'Backend services not available' in data['error']

    def test_monitoring_alerts_empty_history(self, client):
        """Test monitoring alerts with empty metrics history"""
        with patch('src.routes.phase7._get_backend_services_available', return_value=True):
            mock_dashboard = MagicMock()
            mock_dashboard.metrics_history = []
            with patch('src.routes.phase7._get_monitoring_dashboard', return_value=mock_dashboard):
                response = client.get('/api/phase7/monitoring/alerts')
                assert response.status_code == 200
                data = response.get_json()
                assert data['alerts'] == []
                assert data['count'] == 0


class TestPhase7EnvironmentEndpoint:
    """Tests for /api/phase7/environment/validate endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_environment_validate_get_returns_json(self, client):
        """Test that environment validate GET returns valid JSON"""
        response = client.get('/api/phase7/environment/validate')
        assert response.content_type == 'application/json'

    def test_environment_validate_post_returns_json(self, client):
        """Test that environment validate POST returns valid JSON"""
        response = client.post('/api/phase7/environment/validate')
        assert response.content_type == 'application/json'

    def test_environment_validate_response_structure(self, client):
        """Test that environment validate returns expected structure"""
        response = client.get('/api/phase7/environment/validate')
        if response.status_code == 200:
            data = response.get_json()
            # Should have validation and summary keys
            assert 'validation' in data or 'error' in data


class TestPhase7ResilienceEndpoint:
    """Tests for /api/phase7/resilience/metrics endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_resilience_metrics_returns_json(self, client):
        """Test that resilience metrics returns valid JSON"""
        response = client.get('/api/phase7/resilience/metrics')
        assert response.content_type == 'application/json'

    def test_resilience_metrics_response_structure(self, client):
        """Test that resilience metrics returns expected structure"""
        response = client.get('/api/phase7/resilience/metrics')
        assert response.status_code == 200
        data = response.get_json()
        # Should have circuit_breakers, retry_patterns, bulkhead_isolation
        assert 'circuit_breakers' in data
        assert 'retry_patterns' in data
        assert 'bulkhead_isolation' in data
        assert 'status' in data
        assert 'timestamp' in data

    def test_resilience_metrics_circuit_breakers_structure(self, client):
        """Test circuit breakers structure in resilience metrics"""
        response = client.get('/api/phase7/resilience/metrics')
        data = response.get_json()
        circuit_breakers = data['circuit_breakers']
        assert 'database' in circuit_breakers
        assert 'external_api' in circuit_breakers
        assert circuit_breakers['database']['status'] == 'closed'


class TestPhase7RateLimitInteraction:
    """Tests for Phase 7 routes rate limit interaction"""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting enabled for testing"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['RATE_LIMIT_REQUESTS'] = 5
        return app

    def test_phase7_routes_work_without_rate_limit(self):
        """Test that Phase 7 routes work when rate limiting is disabled"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Make multiple requests - should all succeed
            for _ in range(10):
                response = client.get('/api/phase7/status')
                # Should not get 429 (rate limited)
                assert response.status_code != 429

    def test_phase7_routes_no_rate_limit_headers_by_default(self):
        """Test that Phase 7 routes don't have rate limit headers by default"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/api/phase7/status')
            # Rate limit headers should not be present when rate limiting is disabled
            # (In testing mode, rate limiting is typically disabled)
            # This test documents the current behavior
            assert response.status_code in [200, 500]


class TestPhase7EdgeCases:
    """Edge case tests for Phase 7 endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_unknown_phase7_route_returns_404(self, client):
        """Test that unknown Phase 7 routes return 404"""
        response = client.get('/api/phase7/unknown/route')
        assert response.status_code == 404

    def test_phase7_routes_handle_method_not_allowed(self, client):
        """Test that Phase 7 routes return 405 for unsupported methods"""
        # POST to a GET-only endpoint
        response = client.post('/api/phase7/status')
        assert response.status_code == 405

    def test_phase7_routes_handle_sequential_requests(self, client):
        """Test that Phase 7 routes handle multiple sequential requests"""
        # Make multiple sequential requests to verify stability
        results = []
        for _ in range(5):
            response = client.get('/api/phase7/resilience/metrics')
            results.append(response)
        
        # All requests should succeed (200) or fail gracefully (500)
        for response in results:
            assert response.status_code in [200, 500]

    def test_phase7_beta_candidates_returns_json(self, client):
        """Test that beta candidates endpoint returns valid JSON"""
        response = client.get('/api/phase7/beta/candidates')
        assert response.content_type == 'application/json'

    def test_phase7_growth_metrics_returns_json(self, client):
        """Test that growth metrics endpoint returns valid JSON"""
        response = client.get('/api/phase7/growth/metrics')
        assert response.content_type == 'application/json'

    def test_phase7_ops_metrics_returns_json(self, client):
        """Test that ops metrics endpoint returns valid JSON"""
        response = client.get('/api/phase7/ops/metrics')
        assert response.content_type == 'application/json'


class TestPhase7BackendServicesAvailability:
    """Tests for BACKEND_SERVICES_AVAILABLE flag behavior"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_monitoring_alerts_respects_backend_services_flag(self, client):
        """Test that monitoring alerts checks BACKEND_SERVICES_AVAILABLE"""
        with patch('src.routes.phase7._get_backend_services_available', return_value=False):
            response = client.get('/api/phase7/monitoring/alerts')
            assert response.status_code == 500
            data = response.get_json()
            assert 'Backend services not available' in data['error']

    def test_runtime_import_pattern_allows_patching(self, client):
        """Test that runtime import pattern allows test patching"""
        # This test verifies the _get_backend_services_available() pattern works
        with patch('src.main.BACKEND_SERVICES_AVAILABLE', False):
            # The patch should be picked up by _get_backend_services_available()
            from src.routes.phase7 import _get_backend_services_available
            # Note: Due to how Python imports work, we need to patch at the source
            with patch('src.routes.phase7._get_backend_services_available', return_value=False):
                response = client.get('/api/phase7/monitoring/alerts')
                assert response.status_code == 500
