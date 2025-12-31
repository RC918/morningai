"""Tests for EPIC I-3b Provider Health Snapshot API endpoints"""
import pytest
import json
from unittest.mock import Mock, patch
from src.main import app
from src.middleware.auth_middleware import create_admin_token, create_user_token


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_token():
    """Create admin JWT token"""
    return create_admin_token()


@pytest.fixture
def user_token():
    """Create regular user JWT token"""
    return create_user_token()


class TestProviderHealthSnapshot:
    """Test provider health snapshot endpoint - EPIC I-3b"""

    def test_provider_health_no_auth(self, client):
        """Test provider health endpoint without authentication"""
        response = client.get('/api/governance/providers/health')
        assert response.status_code == 401

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_metrics_unavailable(
        self, mock_get_metrics, client, user_token
    ):
        """Test provider health when metrics unavailable"""
        mock_get_metrics.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'metrics_unavailable'

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_metrics_disabled(
        self, mock_get_metrics, client, user_token
    ):
        """Test provider health when metrics disabled"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {'enabled': False}
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'metrics_disabled'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_success(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test successful provider health snapshot"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'window_minutes': 15,
            'timestamp': '2025-01-01T00:00:00',
            'providers': {
                'openai': {'health_score': 95.0, 'error_rate': 1.0},
                'gemini': {'health_score': 88.0, 'error_rate': 2.0},
                'alicloud': {'health_score': 75.0, 'error_rate': 5.0},
                'siliconflow': {'health_score': 55.0, 'error_rate': 10.0},
            },
            'ranking': ['openai', 'gemini', 'alicloud', 'siliconflow']
        }
        mock_get_metrics.return_value = mock_metrics

        mock_alert_service = Mock()
        mock_alert_service.enabled = True
        mock_alert_service.get_cooldown_status.return_value = {}
        mock_get_alert_service.return_value = mock_alert_service

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['available'] is True
        assert 'timestamp' in data
        assert 'window_minutes' in data
        assert 'system_status' in data
        assert 'summary' in data
        assert 'providers' in data
        assert 'ranking' in data
        assert 'alerting' in data

        # Check summary structure
        summary = data['summary']
        assert 'average_health' in summary
        assert 'total_providers' in summary
        assert 'healthy' in summary
        assert 'degraded' in summary
        assert 'critical' in summary

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_system_status_healthy(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test system status is healthy when avg health >= 80"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 95.0},
                'gemini': {'health_score': 90.0},
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'healthy'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_system_status_degraded(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test system status is degraded when 60 <= avg health < 80"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 70.0},
                'gemini': {'health_score': 65.0},
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'degraded'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_system_status_critical(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test system status is critical when avg health < 60"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 50.0},
                'gemini': {'health_score': 40.0},
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'critical'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_with_window_param(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test provider health with custom window parameter"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {'openai': {'health_score': 90.0}},
            'ranking': ['openai']
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/health?window=30',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['window_minutes'] == 30

        # Verify the metrics were called with correct window
        mock_metrics.get_all_providers_health.assert_called_once()
        call_args = mock_metrics.get_all_providers_health.call_args
        assert call_args[1]['window_minutes'] == 30

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_with_providers_filter(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test provider health with providers filter"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 90.0},
                'gemini': {'health_score': 85.0}
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/health?providers=openai,gemini',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200

        # Verify the metrics were called with correct providers
        mock_metrics.get_all_providers_health.assert_called_once()
        call_args = mock_metrics.get_all_providers_health.call_args
        assert call_args[1]['providers'] == ['openai', 'gemini']

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_error_handling(
        self, mock_get_metrics, client, user_token
    ):
        """Test provider health error handling"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.side_effect = Exception('Redis error')
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'internal_error'


class TestSingleProviderHealth:
    """Test single provider health endpoint - EPIC I-3b"""

    def test_single_provider_health_no_auth(self, client):
        """Test single provider health endpoint without authentication"""
        response = client.get('/api/governance/providers/openai/health')
        assert response.status_code == 401

    def test_single_provider_health_invalid_provider(self, client, user_token):
        """Test single provider health with invalid provider name"""
        response = client.get(
            '/api/governance/providers/invalid_provider/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'invalid_provider'
        assert 'valid_providers' in data

    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_metrics_unavailable(
        self, mock_get_metrics, client, user_token
    ):
        """Test single provider health when metrics unavailable"""
        mock_get_metrics.return_value = None

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['provider'] == 'openai'
        assert data['error'] == 'metrics_unavailable'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_success(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test successful single provider health"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'provider': 'openai',
            'health_score': 92.5,
            'total_requests': 1000,
            'error_rate': 2.5,
            'drift_rate': 1.0,
            'latency': {'p50': 100, 'p95': 250, 'p99': 500},
            'latency_weight': 0.3,
            'error_weight': 0.4,
            'drift_weight': 0.3,
        }
        mock_get_metrics.return_value = mock_metrics

        mock_alert_service = Mock()
        mock_alert_service.get_cooldown_status.return_value = {
            'openai': {'in_cooldown': False}
        }
        mock_get_alert_service.return_value = mock_alert_service

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['available'] is True
        assert data['provider'] == 'openai'
        assert data['status'] == 'healthy'
        assert data['health_score'] == 92.5
        assert 'metrics' in data
        assert 'weights' in data
        assert 'alert_cooldown' in data

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_status_healthy(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test single provider status is healthy when score >= 80"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 85.0,
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_status_degraded(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test single provider status is degraded when 60 <= score < 80"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 70.0,
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/gemini/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'degraded'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_status_critical(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test single provider status is critical when score < 60"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 45.0,
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/alicloud/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'critical'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_with_window_param(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test single provider health with custom window parameter"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 90.0,
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        response = client.get(
            '/api/governance/providers/openai/health?window=45',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['window_minutes'] == 45

        # Verify the metrics were called with correct window
        mock_metrics.get_provider_health.assert_called_once()
        call_args = mock_metrics.get_provider_health.call_args
        assert call_args[1]['window_minutes'] == 45

    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_health_error_handling(
        self, mock_get_metrics, client, user_token
    ):
        """Test single provider health error handling"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.side_effect = Exception('Redis error')
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['provider'] == 'openai'
        assert data['error'] == 'internal_error'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_all_valid_providers(
        self, mock_get_metrics, mock_get_alert_service, client, user_token
    ):
        """Test all valid provider names work"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 90.0,
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert_service.return_value = None

        valid_providers = ['openai', 'gemini', 'alicloud', 'siliconflow']
        for provider in valid_providers:
            response = client.get(
                f'/api/governance/providers/{provider}/health',
                headers={'Authorization': f'Bearer {user_token}'}
            )
            assert response.status_code == 200, f"Failed for provider: {provider}"
            data = json.loads(response.data)
            assert data['provider'] == provider
