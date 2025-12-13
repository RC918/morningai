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
    mock.scan_iter.return_value = iter([])
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
        def scan_iter_side_effect(match=''):
            if match == 'rq:queue:*':
                return iter(['rq:queue:default', 'rq:queue:high'])
            elif match == 'rq:failed:*':
                return iter(['rq:failed:1', 'rq:failed:2'])
            elif match == 'rate_limit:*':
                return iter(['rate_limit:user1'])
            elif match == 'session:*:data':
                return iter(['session:123:data'])
            elif match == 'session:*:commands':
                return iter(['session:123:commands'])
            return iter([])

        mock_redis.scan_iter.side_effect = scan_iter_side_effect
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

    @pytest.mark.parametrize(
        "section,expect_error_key",
        [
            ("api", True),
            ("rate_limit", False),
            ("session_commands", False),
        ],
    )
    def test_section_unavailable_when_redis_missing(self, client, section, expect_error_key):
        """Test metrics sections return unavailable when Redis fails"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data[section]['available'] is False
                if expect_error_key:
                    assert 'error' in data[section]


class TestWindowParameterValidation:
    """Tests for window parameter validation"""

    def test_window_invalid_string_uses_default(self, client):
        """Test invalid window string falls back to default"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?window=invalid')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 15

    def test_window_out_of_range_high_uses_default(self, client):
        """Test window above max range falls back to default"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?window=1000')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 15

    def test_window_out_of_range_low_uses_default(self, client):
        """Test window below min range falls back to default"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?window=0')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 15

    def test_window_valid_range_accepted(self, client):
        """Test valid window values are accepted"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?window=60')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 60


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


class TestReviewFollowUpMetrics:
    """
    Tests for review follow-up metrics collection.

    Issue #2259: Provides aggregate statistics for ReviewFollowUpService tasks.
    """

    def test_review_follow_up_metrics_redis_unavailable(self, client):
        """Test review_follow_up section returns unavailable when Redis fails"""
        with patch('src.routes.metrics._get_redis_client', return_value=None):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert 'review_follow_up' in data
                assert data['review_follow_up']['available'] is False

    def test_review_follow_up_metrics_no_tasks(self, client, mock_redis):
        """Test review_follow_up metrics when no tasks exist"""
        mock_redis.scan_iter.return_value = iter([])

        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['review_follow_up']['available'] is True
                assert data['review_follow_up']['total_tasks'] == 0
                assert data['review_follow_up']['summary']['pending'] == 0
                assert data['review_follow_up']['summary']['completed'] == 0
                assert data['review_follow_up']['summary']['completion_rate'] == 0.0

    def test_review_follow_up_metrics_with_tasks(self, client, mock_redis):
        """Test review_follow_up metrics with existing tasks"""
        import json

        task_data_pending = json.dumps({
            "task_id": "pr123_comment456",
            "status": "pending",
            "action": "auto_fix"
        })
        task_data_completed = json.dumps({
            "task_id": "pr123_comment789",
            "status": "completed",
            "action": "manual_review"
        })
        task_data_failed = json.dumps({
            "task_id": "pr124_comment111",
            "status": "failed",
            "action": "auto_fix"
        })

        def scan_iter_side_effect(match=''):
            if match == 'review_follow_up:task:*':
                return iter([
                    'review_follow_up:task:pr123_comment456',
                    'review_follow_up:task:pr123_comment789',
                    'review_follow_up:task:pr124_comment111',
                ])
            return iter([])

        def get_side_effect(key):
            if key == 'review_follow_up:task:pr123_comment456':
                return task_data_pending
            elif key == 'review_follow_up:task:pr123_comment789':
                return task_data_completed
            elif key == 'review_follow_up:task:pr124_comment111':
                return task_data_failed
            return None

        mock_redis.scan_iter.side_effect = scan_iter_side_effect
        mock_redis.get.side_effect = get_side_effect

        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics')

                assert response.status_code == 200
                data = response.get_json()
                assert data['review_follow_up']['available'] is True
                assert data['review_follow_up']['total_tasks'] == 3
                assert data['review_follow_up']['status_counts']['pending'] == 1
                assert data['review_follow_up']['status_counts']['completed'] == 1
                assert data['review_follow_up']['status_counts']['failed'] == 1
                assert data['review_follow_up']['action_counts']['auto_fix'] == 2
                assert data['review_follow_up']['action_counts']['manual_review'] == 1
                assert data['review_follow_up']['summary']['completion_rate'] == 50.0

    def test_review_follow_up_prometheus_format(self, client, mock_redis):
        """Test review_follow_up metrics in Prometheus format"""
        import json

        task_data = json.dumps({
            "task_id": "pr123_comment456",
            "status": "completed",
            "action": "auto_fix"
        })

        def scan_iter_side_effect(match=''):
            if match == 'review_follow_up:task:*':
                return iter(['review_follow_up:task:pr123_comment456'])
            return iter([])

        mock_redis.scan_iter.side_effect = scan_iter_side_effect
        mock_redis.get.return_value = task_data

        with patch('src.routes.metrics._get_redis_client', return_value=mock_redis):
            with patch('src.routes.metrics._get_orchestrator_metrics', return_value=None):
                response = client.get('/api/metrics?format=prometheus')

                assert response.status_code == 200
                content = response.data.decode('utf-8')
                assert 'morningai_review_follow_up_total 1' in content
                assert 'morningai_review_follow_up_completed 1' in content
                assert 'morningai_review_follow_up_completion_rate 100' in content
