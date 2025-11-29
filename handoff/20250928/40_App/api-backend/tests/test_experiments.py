"""Tests for experiments API endpoints (Phase 5 PR-6)"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock

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


def test_list_experiments(client, auth_headers):
    """Test GET /api/experiments"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'experiments' in data
            assert 'environment' in data
            assert 'active_experiments' in data
            assert 'total_experiments' in data
            assert 'timestamp' in data


def test_get_experiment_summary(client, auth_headers):
    """Test GET /api/experiments/summary"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments/summary', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'summary' in data
            assert 'timestamp' in data


def test_get_experiment_detail(client, auth_headers):
    """Test GET /api/experiments/<name>"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments/planner_gemini', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'experiment' in data
            assert 'timestamp' in data
            exp = data['experiment']
            assert exp['name'] == 'planner_gemini'
            assert 'description' in exp
            assert 'treatment_percent' in exp
            assert 'active_in_current_env' in exp


def test_get_experiment_not_found(client, auth_headers):
    """Test GET /api/experiments/<name> with non-existent experiment"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments/nonexistent', headers=auth_headers)

            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data


def test_get_variant(client, auth_headers):
    """Test GET /api/experiments/<name>/variant"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get(
                '/api/experiments/planner_gemini/variant?trace_id=test123',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['experiment_name'] == 'planner_gemini'
            assert data['trace_id'] == 'test123'
            assert 'variant' in data
            assert 'provider' in data
            assert 'timestamp' in data


def test_get_variant_missing_trace_id(client, auth_headers):
    """Test GET /api/experiments/<name>/variant without trace_id"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get(
                '/api/experiments/planner_gemini/variant',
                headers=auth_headers
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data


def test_get_variant_experiment_not_found(client, auth_headers):
    """Test GET /api/experiments/<name>/variant with non-existent experiment"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get(
                '/api/experiments/nonexistent/variant?trace_id=test123',
                headers=auth_headers
            )

            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data


def test_health_check(client):
    """Test GET /api/experiments/health (no auth required)"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments/health')

            assert response.status_code == 200
            data = response.get_json()
            assert 'experiment_manager_available' in data
            assert 'components' in data


def test_get_experiment_comparison(client, auth_headers):
    """Test GET /api/experiments/comparison"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', True):
        with patch('src.routes.experiments._get_manager', return_value=StubExperimentManager()):
            response = client.get('/api/experiments/comparison', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'comparisons' in data
            assert 'environment' in data
            assert 'active_experiments' in data
            assert 'timestamp' in data


def test_list_experiments_unavailable(client, auth_headers):
    """Test GET /api/experiments when manager unavailable"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
        response = client.get('/api/experiments', headers=auth_headers)
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


def test_get_experiment_summary_unavailable(client, auth_headers):
    """Test GET /api/experiments/summary when manager unavailable"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
        response = client.get('/api/experiments/summary', headers=auth_headers)
        assert response.status_code == 503


def test_get_experiment_detail_unavailable(client, auth_headers):
    """Test GET /api/experiments/<name> when manager unavailable"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
        response = client.get('/api/experiments/planner_gemini', headers=auth_headers)
        assert response.status_code == 503


def test_get_variant_unavailable(client, auth_headers):
    """Test GET /api/experiments/<name>/variant when manager unavailable"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
        response = client.get(
            '/api/experiments/planner_gemini/variant?trace_id=test123',
            headers=auth_headers
        )
        assert response.status_code == 503


def test_get_experiment_comparison_unavailable(client, auth_headers):
    """Test GET /api/experiments/comparison when manager unavailable"""
    with patch('src.routes.experiments.EXPERIMENT_MANAGER_AVAILABLE', False):
        response = client.get('/api/experiments/comparison', headers=auth_headers)
        assert response.status_code == 503


def test_list_experiments_no_auth(client):
    """Test GET /api/experiments without authentication"""
    response = client.get('/api/experiments')
    assert response.status_code == 401


def test_get_experiment_summary_no_auth(client):
    """Test GET /api/experiments/summary without authentication"""
    response = client.get('/api/experiments/summary')
    assert response.status_code == 401


def test_get_experiment_detail_no_auth(client):
    """Test GET /api/experiments/<name> without authentication"""
    response = client.get('/api/experiments/planner_gemini')
    assert response.status_code == 401


def test_get_variant_no_auth(client):
    """Test GET /api/experiments/<name>/variant without authentication"""
    response = client.get('/api/experiments/planner_gemini/variant?trace_id=test123')
    assert response.status_code == 401


def test_get_experiment_comparison_no_auth(client):
    """Test GET /api/experiments/comparison without authentication"""
    response = client.get('/api/experiments/comparison')
    assert response.status_code == 401
