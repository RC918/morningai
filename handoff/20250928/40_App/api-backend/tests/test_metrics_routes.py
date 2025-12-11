"""
Tests for Metrics API routes (System Observability Endpoints)
Epic #2311 Phase 1: API Latency & Error Metrics + /metrics endpoint
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app for testing"""
    with patch.dict(os.environ, {
        'TESTING': 'true',
        'JWT_SECRET_KEY': 'test-secret-key-that-is-at-least-32-characters-long',
        'FLASK_SECRET_KEY': 'test-flask-secret-key-at-least-32-chars',
        'SENTRY_DSN': ''
    }):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']

        from src.main import app as flask_app
        from src.models.user import db

        flask_app.config['TESTING'] = True
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with flask_app.app_context():
            db.create_all()
            yield flask_app
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    mock = MagicMock()
    mock.keys.return_value = []
    mock.llen.return_value = 0
    mock.get.return_value = None
    return mock


class TestMetricsEndpoint:
    """Tests for GET /api/metrics endpoint"""

    def test_metrics_json_format_default(self, client):
        """Test GET /api/metrics returns JSON by default"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert 'timestamp' in data
                assert 'window_minutes' in data
                assert data['window_minutes'] == 15
                assert 'api' in data
                assert 'rate_limit' in data
                assert 'session_commands' in data
                assert 'orchestrator' in data

    def test_metrics_json_format_explicit(self, client):
        """Test GET /api/metrics?format=json returns JSON"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=json')

                assert response.status_code == 200
                assert response.content_type == 'application/json'
                data = response.get_json()
                assert 'timestamp' in data

    def test_metrics_prometheus_format(self, client):
        """Test GET /api/metrics?format=prometheus returns Prometheus format"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=prometheus')

                assert response.status_code == 200
                assert 'text/plain' in response.content_type
                content = response.data.decode('utf-8')
                assert 'morningai_up 1' in content
                assert '# HELP' in content
                assert '# TYPE' in content

    def test_metrics_custom_window(self, client):
        """Test GET /api/metrics?window=30 uses custom window"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?window=30')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 30

    def test_metrics_with_redis_available(self, client, mock_redis):
        """Test GET /api/metrics with Redis available"""
        mock_redis.keys.side_effect = [
            ['rq:queue:default', 'rq:queue:high'],
            ['rq:failed:1', 'rq:failed:2'],
            ['rate_limit:user1'],
            ['session:123:data'],
            ['session:123:commands'],
        ]
        mock_redis.llen.side_effect = [5, 3, 2]

        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['api']['available'] is True
                assert data['api']['queue_depth'] == 8
                assert data['api']['failed_jobs'] == 2

    def test_metrics_with_orchestrator_metrics(self, client):
        """Test GET /api/metrics with OrchestratorMetrics available"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_comprehensive_summary.return_value = {
            "enabled": True,
            "window_minutes": 15,
            "workflow": {"started": 10, "success": 8, "error": 2, "success_rate": 80.0},
            "nodes": {"planner": {"started": 10, "success": 9, "failure": 1}},
            "decisions": {"approve": 5, "needs_fix": 3, "total": 8},
            "fixer": {"attempts": 3, "success": 2, "failure": 1},
        }

        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch(
                'src.routes.metrics._get_orchestrator_metrics',
                return_value=mock_orchestrator
            ):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['orchestrator']['enabled'] is True
                assert data['orchestrator']['workflow']['started'] == 10
                assert data['orchestrator']['workflow']['success_rate'] == 80.0

    def test_metrics_prometheus_with_orchestrator(self, client):
        """Test Prometheus format includes orchestrator metrics"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_comprehensive_summary.return_value = {
            "enabled": True,
            "window_minutes": 15,
            "workflow": {"started": 10, "success": 8, "error": 2, "success_rate": 80.0},
            "nodes": {"planner": {"started": 10, "success": 9, "failure": 1}},
            "decisions": {"approve": 5, "needs_fix": 3, "total": 8},
            "fixer": {"attempts": 3, "success": 2, "failure": 1},
        }

        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch(
                'src.routes.metrics._get_orchestrator_metrics',
                return_value=mock_orchestrator
            ):
                response = client.get('/api/metrics?format=prometheus')

                assert response.status_code == 200
                content = response.data.decode('utf-8')
                assert 'morningai_workflow_started 10' in content
                assert 'morningai_workflow_success 8' in content
                assert 'morningai_workflow_error 2' in content
                assert 'morningai_decision_approve 5' in content
                assert 'morningai_fixer_attempts 3' in content


class TestMetricsHealthEndpoint:
    """Tests for GET /api/metrics/health endpoint"""

    def test_metrics_health_redis_unavailable(self, client):
        """Test GET /api/metrics/health when Redis is unavailable"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'degraded'
                assert data['components']['redis'] == 'unavailable'
                assert 'timestamp' in data

    def test_metrics_health_redis_available(self, client, mock_redis):
        """Test GET /api/metrics/health when Redis is available"""
        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'healthy'
                assert data['components']['redis'] == 'available'

    def test_metrics_health_orchestrator_available(self, client, mock_redis):
        """Test GET /api/metrics/health when OrchestratorMetrics is available"""
        mock_orchestrator = MagicMock()

        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch(
                'src.routes.metrics._get_orchestrator_metrics',
                return_value=mock_orchestrator
            ):
                response = client.get('/api/metrics/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['components']['orchestrator_metrics'] == 'available'


class TestMetricsRedisUnavailable:
    """Tests for metrics collection when Redis is unavailable"""

    def test_api_metrics_redis_unavailable(self, client):
        """Test API metrics returns unavailable when Redis fails"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['api']['available'] is False
                assert 'error' in data['api']

    def test_rate_limit_metrics_redis_unavailable(self, client):
        """Test rate limit metrics returns unavailable when Redis fails"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['rate_limit']['available'] is False

    def test_session_metrics_redis_unavailable(self, client):
        """Test session metrics returns unavailable when Redis fails"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['session_commands']['available'] is False


class TestPrometheusFormatDetails:
    """Tests for Prometheus format output details"""

    def test_prometheus_help_and_type_annotations(self, client):
        """Test Prometheus output includes HELP and TYPE annotations"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=prometheus')

                content = response.data.decode('utf-8')
                assert '# HELP morningai_up' in content
                assert '# TYPE morningai_up gauge' in content

    def test_prometheus_up_metric_always_present(self, client):
        """Test Prometheus output always includes up metric"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=prometheus')

                content = response.data.decode('utf-8')
                assert 'morningai_up 1' in content

    def test_prometheus_content_type(self, client):
        """Test Prometheus response has correct content type"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=prometheus')

                assert 'text/plain' in response.content_type
                assert 'version=0.0.4' in response.content_type
