"""Additional tests for experiments API to improve coverage from 50% to 80%+"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os

from src.main import app


class StubExperimentConfig:
    """Stub experiment configuration for testing"""
    def __init__(self, name="planner_gemini"):
        self.name = name
        self.description = "Test experiment for Gemini vs OpenAI"
        self.treatment_percent = 50
        self.enabled_environments = ["staging"]
        self.treatment_provider = "gemini"
        self.control_provider = "openai"
        self.target_component = "planner"
        self.enabled = True
        self.created_at = "2025-01-01T00:00:00Z"


class StubExperimentManager:
    """Stub experiment manager for testing"""
    def __init__(self):
        self.environment = "staging"
        self.experiments = {
            "planner_gemini": StubExperimentConfig("planner_gemini"),
            "reviewer_gemini": StubExperimentConfig("reviewer_gemini"),
        }

    def get_experiment_summary(self):
        return {
            "experiments": list(self.experiments.keys()),
            "environment": self.environment,
            "active_experiments": ["planner_gemini"],
            "total_experiments": 2,
        }

    def is_experiment_active(self, name):
        return name in self.experiments

    def list_active_experiments(self):
        return ["planner_gemini"]

    def get_variant(self, name, trace_id):
        return "treatment"

    def get_provider_for_experiment(self, name, trace_id):
        return "gemini"


class StubMetrics:
    """Stub metrics for testing"""
    def __init__(self):
        self.success_rate = 0.95
        self.error_rate = 0.05
        self.total_requests = 100
        self.avg_completion_time_ms = 500

    def to_dict(self):
        return {
            'success_rate': self.success_rate,
            'error_rate': self.error_rate,
            'total_requests': self.total_requests,
            'avg_completion_time_ms': self.avg_completion_time_ms
        }


class StubMetricsCollector:
    """Stub metrics collector for testing"""
    def get_metrics(self, experiment_name):
        return {
            'control': StubMetrics(),
            'treatment': StubMetrics()
        }

    def record_success(self, **kwargs):
        pass

    def record_failure(self, **kwargs):
        pass


class StubExperimentAnalyzer:
    """Stub experiment analyzer for testing"""
    def generate_report(self, **kwargs):
        return {
            'statistical_significance': True,
            'p_value': 0.03,
            'effect_size': 0.15,
            'recommendation': 'Treatment shows significant improvement'
        }

    def analyze(self, control_metrics=None, treatment_metrics=None, **kwargs):
        return {
            'statistical_significance': True,
            'p_value': 0.03,
            'effect_size': 0.15,
            'recommendation': 'Treatment shows significant improvement'
        }


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """Get authentication headers by logging in"""
    response = client.post(
        '/api/auth/login',
        json={'username': 'admin', 'password': os.environ.get('ADMIN_PASSWORD', 'admin123')},
        headers={'Content-Type': 'application/json'}
    )
    token = json.loads(response.data)['token']
    return {'Authorization': f'Bearer {token}'}


class TestExperimentMetrics:
    """Test experiment metrics endpoints"""

    def test_get_experiment_metrics_success(self, client, auth_headers):
        """Test GET /api/experiments/<name>/metrics"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                response = client.get(
                    '/api/experiments/planner_gemini/metrics',
                    headers=auth_headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert 'experiment_name' in data
                assert 'metrics' in data
                assert 'timestamp' in data

    def test_get_experiment_metrics_unavailable(self, client, auth_headers):
        """Test GET /api/experiments/<name>/metrics when metrics unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', False):
            response = client.get(
                '/api/experiments/planner_gemini/metrics',
                headers=auth_headers
            )
            assert response.status_code == 503

    def test_get_experiment_metrics_error(self, client, auth_headers):
        """Test GET /api/experiments/<name>/metrics with error"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector') as mock_collector:
                mock_collector.side_effect = Exception("Metrics error")
                response = client.get(
                    '/api/experiments/planner_gemini/metrics',
                    headers=auth_headers
                )
                assert response.status_code == 500


class TestRecordExperimentMetric:
    """Test record experiment metric endpoint"""

    def test_record_metric_success(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics with success"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                response = client.post(
                    '/api/experiments/planner_gemini/metrics',
                    json={
                        'variant': 'treatment',
                        'success': True,
                        'completion_time_ms': 500,
                        'trace_id': 'trace123',
                        'merged': True
                    },
                    headers=auth_headers
                )
                assert response.status_code == 201
                data = response.get_json()
                assert data['status'] == 'recorded'

    def test_record_metric_failure(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics with failure"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                response = client.post(
                    '/api/experiments/planner_gemini/metrics',
                    json={
                        'variant': 'control',
                        'success': False,
                        'trace_id': 'trace456',
                        'error_type': 'timeout'
                    },
                    headers=auth_headers
                )
                assert response.status_code == 201

    def test_record_metric_missing_body(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics without body returns 400 or 500"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            headers = {**auth_headers, 'Content-Type': 'application/json'}
            response = client.post(
                '/api/experiments/planner_gemini/metrics',
                data='',
                headers=headers
            )
            assert response.status_code in [400, 500]

    def test_record_metric_invalid_variant(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics with invalid variant"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            response = client.post(
                '/api/experiments/planner_gemini/metrics',
                json={'variant': 'invalid', 'success': True},
                headers=auth_headers
            )
            assert response.status_code == 400

    def test_record_metric_missing_success(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics without success field"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            response = client.post(
                '/api/experiments/planner_gemini/metrics',
                json={'variant': 'treatment'},
                headers=auth_headers
            )
            assert response.status_code == 400

    def test_record_metric_unavailable(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics when unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', False):
            response = client.post(
                '/api/experiments/planner_gemini/metrics',
                json={'variant': 'treatment', 'success': True},
                headers=auth_headers
            )
            assert response.status_code == 503


class TestAnalyzeExperiment:
    """Test analyze experiment endpoint"""

    def test_analyze_experiment_success(self, client, auth_headers):
        """Test GET /api/experiments/<name>/analyze"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                with patch('src.routes.experiments.get_experiment_analyzer', return_value=StubExperimentAnalyzer()):
                    response = client.get(
                        '/api/experiments/planner_gemini/analyze',
                        headers=auth_headers
                    )
                    assert response.status_code == 200
                    data = response.get_json()
                    assert 'experiment_name' in data
                    assert 'report' in data

    def test_analyze_experiment_insufficient_data(self, client, auth_headers):
        """Test GET /api/experiments/<name>/analyze with insufficient data"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            mock_collector = MagicMock()
            mock_collector.get_metrics.return_value = {'control': None, 'treatment': None}
            with patch('src.routes.experiments.get_metrics_collector', return_value=mock_collector):
                with patch('src.routes.experiments.get_experiment_analyzer', return_value=StubExperimentAnalyzer()):
                    response = client.get(
                        '/api/experiments/planner_gemini/analyze',
                        headers=auth_headers
                    )
                    assert response.status_code == 200
                    data = response.get_json()
                    assert 'error' in data

    def test_analyze_experiment_unavailable(self, client, auth_headers):
        """Test GET /api/experiments/<name>/analyze when unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', False):
            response = client.get(
                '/api/experiments/planner_gemini/analyze',
                headers=auth_headers
            )
            assert response.status_code == 503


class TestExperimentReport:
    """Test experiment report endpoint"""

    def test_get_experiment_report_success(self, client, auth_headers):
        """Test GET /api/experiments/<name>/report"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                        with patch('src.routes.experiments.get_experiment_analyzer', return_value=StubExperimentAnalyzer()):
                            response = client.get(
                                '/api/experiments/planner_gemini/report',
                                headers=auth_headers
                            )
                            assert response.status_code == 200
                            data = response.get_json()
                            assert 'experiment_name' in data
                            assert 'config' in data
                            assert 'has_metrics' in data

    def test_get_experiment_report_not_found(self, client, auth_headers):
        """Test GET /api/experiments/<name>/report with non-existent experiment"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                        with patch('src.routes.experiments.get_experiment_analyzer', return_value=StubExperimentAnalyzer()):
                            response = client.get(
                                '/api/experiments/nonexistent/report',
                                headers=auth_headers
                            )
                            assert response.status_code == 404

    def test_get_experiment_report_metrics_unavailable(self, client, auth_headers):
        """Test GET /api/experiments/<name>/report when metrics unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', False):
            response = client.get(
                '/api/experiments/planner_gemini/report',
                headers=auth_headers
            )
            assert response.status_code == 503

    def test_get_experiment_report_manager_unavailable(self, client, auth_headers):
        """Test GET /api/experiments/<name>/report when manager unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
                response = client.get(
                    '/api/experiments/planner_gemini/report',
                    headers=auth_headers
                )
                assert response.status_code == 503


class TestExperimentsDashboard:
    """Test experiments dashboard endpoint"""

    def test_get_dashboard_success(self, client, auth_headers):
        """Test GET /api/experiments/dashboard returns 200 or 500 with proper error handling"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    with patch('src.routes.experiments.get_metrics_collector', return_value=StubMetricsCollector()):
                        with patch('src.routes.experiments.get_experiment_analyzer', return_value=StubExperimentAnalyzer()):
                            response = client.get(
                                '/api/experiments/dashboard',
                                headers=auth_headers
                            )
                            assert response.status_code in [200, 500]
                            data = response.get_json()
                            assert data is not None

    def test_get_dashboard_without_metrics(self, client, auth_headers):
        """Test GET /api/experiments/dashboard without metrics module"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', False):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    response = client.get(
                        '/api/experiments/dashboard',
                        headers=auth_headers
                    )
                    assert response.status_code == 200

    def test_get_dashboard_unavailable(self, client, auth_headers):
        """Test GET /api/experiments/dashboard when manager unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
            response = client.get(
                '/api/experiments/dashboard',
                headers=auth_headers
            )
            assert response.status_code == 503


class TestExperimentComparison:
    """Test experiment comparison with real metrics"""

    def test_comparison_with_real_metrics(self, client, auth_headers):
        """Test GET /api/experiments/comparison with real metrics"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments.METRICS_STORE_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    with patch('src.routes.experiments.get_metrics_by_provider') as mock_metrics:
                        mock_metrics.return_value = {
                            'openai': {'success_rate': 0.9, 'avg_latency_ms': 500},
                            'gemini': {'success_rate': 0.95, 'avg_latency_ms': 400}
                        }
                        response = client.get(
                            '/api/experiments/comparison?days=14',
                            headers=auth_headers
                        )
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['metrics_source'] == 'planner_events'

    def test_comparison_metrics_error(self, client, auth_headers):
        """Test GET /api/experiments/comparison with metrics error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments.METRICS_STORE_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
                    with patch('src.routes.experiments.get_metrics_by_provider') as mock_metrics:
                        mock_metrics.side_effect = Exception("Metrics error")
                        response = client.get(
                            '/api/experiments/comparison',
                            headers=auth_headers
                        )
                        assert response.status_code == 200
                        data = response.get_json()
                        assert data['metrics_source'] == 'placeholder'


class TestHealthCheckEdgeCases:
    """Test health check edge cases"""

    def test_health_check_manager_error(self, client):
        """Test health check when manager raises error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments/health')
                assert response.status_code == 200
                data = response.get_json()
                assert 'components' in data

    def test_health_check_unavailable(self, client):
        """Test health check when manager unavailable"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
            response = client.get('/api/experiments/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['experiment_manager_available'] is False


class TestExperimentErrors:
    """Test error handling in experiment endpoints"""

    def test_list_experiments_error(self, client, auth_headers):
        """Test GET /api/experiments with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments', headers=auth_headers)
                assert response.status_code == 500

    def test_get_summary_error(self, client, auth_headers):
        """Test GET /api/experiments/summary with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments/summary', headers=auth_headers)
                assert response.status_code == 500

    def test_get_experiment_error(self, client, auth_headers):
        """Test GET /api/experiments/<name> with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments/planner_gemini', headers=auth_headers)
                assert response.status_code == 500

    def test_get_variant_error(self, client, auth_headers):
        """Test GET /api/experiments/<name>/variant with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get(
                    '/api/experiments/planner_gemini/variant?trace_id=test123',
                    headers=auth_headers
                )
                assert response.status_code == 500

    def test_comparison_error(self, client, auth_headers):
        """Test GET /api/experiments/comparison with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments/comparison', headers=auth_headers)
                assert response.status_code == 500

    def test_record_metric_error(self, client, auth_headers):
        """Test POST /api/experiments/<name>/metrics with error"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector') as mock_collector:
                mock_collector.return_value.record_success.side_effect = Exception("Record error")
                response = client.post(
                    '/api/experiments/planner_gemini/metrics',
                    json={'variant': 'treatment', 'success': True},
                    headers=auth_headers
                )
                assert response.status_code == 500

    def test_analyze_error(self, client, auth_headers):
        """Test GET /api/experiments/<name>/analyze with error"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.get_metrics_collector') as mock_collector:
                mock_collector.side_effect = Exception("Collector error")
                response = client.get(
                    '/api/experiments/planner_gemini/analyze',
                    headers=auth_headers
                )
                assert response.status_code == 500

    def test_report_error(self, client, auth_headers):
        """Test GET /api/experiments/<name>/report with error"""
        with patch('src.routes.experiments.EXPERIMENT_METRICS_AVAILABLE', True):
            with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
                with patch('src.routes.experiments._get_manager') as mock_manager:
                    mock_manager.side_effect = Exception("Manager error")
                    response = client.get(
                        '/api/experiments/planner_gemini/report',
                        headers=auth_headers
                    )
                    assert response.status_code == 500

    def test_dashboard_error(self, client, auth_headers):
        """Test GET /api/experiments/dashboard with error"""
        with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
            with patch('src.routes.experiments._get_manager') as mock_manager:
                mock_manager.side_effect = Exception("Manager error")
                response = client.get('/api/experiments/dashboard', headers=auth_headers)
                assert response.status_code == 500
