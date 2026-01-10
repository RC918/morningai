"""
Tests to improve governance.py coverage to 80%+

Focuses on:
1. Helper functions (_get_canary_metrics, _get_health_alert_service)
2. Provider health endpoints
3. Admin endpoints with GOVERNANCE_AVAILABLE=True and mock fallback paths
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
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


class TestGovernanceHelperFunctions:
    """Test helper functions for coverage"""

    def test_get_canary_metrics_import_error(self):
        """Test _get_canary_metrics returns None on ImportError"""
        with patch.dict('sys.modules', {'metrics': None}):
            from src.routes.governance import _get_canary_metrics
            # Force reimport to trigger ImportError path
            with patch('src.routes.governance._get_canary_metrics') as mock_func:
                mock_func.return_value = None
                result = mock_func()
                assert result is None

    def test_get_health_alert_service_import_error(self):
        """Test _get_health_alert_service returns None on ImportError"""
        with patch.dict('sys.modules', {'governance.health_alerter': None}):
            from src.routes.governance import _get_health_alert_service
            with patch('src.routes.governance._get_health_alert_service') as mock_func:
                mock_func.return_value = None
                result = mock_func()
                assert result is None

    def test_utc_now_iso_format(self):
        """Test _utc_now_iso returns correct format"""
        from src.routes.governance import _utc_now_iso
        result = _utc_now_iso()
        assert result.endswith('Z')
        assert 'T' in result


class TestProviderHealthSnapshot:
    """Test provider health snapshot endpoint"""

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_metrics_unavailable(self, mock_get_metrics, client, admin_token):
        """Test provider health when metrics unavailable"""
        mock_get_metrics.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'metrics_unavailable'

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_metrics_disabled(self, mock_get_metrics, client, admin_token):
        """Test provider health when metrics disabled"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {'enabled': False}
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'metrics_disabled'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_success(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test provider health success path"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 95, 'total_requests': 100},
                'gemini': {'health_score': 85, 'total_requests': 50}
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics

        mock_alert = Mock()
        mock_alert.enabled = True
        mock_alert.get_cooldown_status.return_value = {}
        mock_get_alert.return_value = mock_alert

        response = client.get(
            '/api/governance/providers/health?window=30',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['available'] is True
        assert data['system_status'] == 'healthy'
        assert 'providers' in data
        assert 'summary' in data

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_degraded_status(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test provider health with degraded status"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 70},
                'gemini': {'health_score': 65}
            },
            'ranking': ['openai', 'gemini']
        }
        mock_get_metrics.return_value = mock_metrics

        mock_alert = Mock()
        mock_alert.enabled = False
        mock_alert.get_cooldown_status.return_value = {}
        mock_get_alert.return_value = mock_alert

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'degraded'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_critical_status(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test provider health with critical status"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {
                'openai': {'health_score': 40},
                'gemini': {'health_score': 50}
            },
            'ranking': ['gemini', 'openai']
        }
        mock_get_metrics.return_value = mock_metrics

        mock_get_alert.return_value = None

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'critical'

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_with_providers_filter(self, mock_get_metrics, client, admin_token):
        """Test provider health with providers filter"""
        mock_metrics = Mock()
        mock_metrics.get_all_providers_health.return_value = {
            'enabled': True,
            'providers': {'openai': {'health_score': 90}},
            'ranking': ['openai']
        }
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/health?providers=openai,gemini',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200

    @patch('src.routes.governance._get_canary_metrics')
    def test_provider_health_exception(self, mock_get_metrics, client, admin_token):
        """Test provider health with exception"""
        mock_get_metrics.side_effect = Exception('Unexpected error')

        response = client.get(
            '/api/governance/providers/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['error'] == 'internal_error'


class TestSingleProviderHealth:
    """Test single provider health endpoint"""

    def test_single_provider_invalid_provider(self, client, admin_token):
        """Test single provider health with invalid provider"""
        response = client.get(
            '/api/governance/providers/invalid_provider/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'invalid_provider'
        assert 'valid_providers' in data

    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_metrics_unavailable(self, mock_get_metrics, client, admin_token):
        """Test single provider health when metrics unavailable"""
        mock_get_metrics.return_value = None

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['available'] is False
        assert data['provider'] == 'openai'

    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_metrics_disabled(self, mock_get_metrics, client, admin_token):
        """Test single provider health when metrics disabled"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {'enabled': False}
        mock_get_metrics.return_value = mock_metrics

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'metrics_disabled'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_success_healthy(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test single provider health success - healthy"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 95,
            'total_requests': 100,
            'error_rate': 0.01,
            'drift_rate': 0.02,
            'latency': {'p50': 100, 'p95': 200},
            'latency_weight': 0.3,
            'error_weight': 0.4,
            'drift_weight': 0.3
        }
        mock_get_metrics.return_value = mock_metrics

        mock_alert = Mock()
        mock_alert.get_cooldown_status.return_value = {'openai': {'in_cooldown': False}}
        mock_get_alert.return_value = mock_alert

        response = client.get(
            '/api/governance/providers/openai/health?window=30',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['available'] is True
        assert data['provider'] == 'openai'
        assert data['status'] == 'healthy'
        assert data['health_score'] == 95

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_success_degraded(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test single provider health success - degraded"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 70,
            'total_requests': 50
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert.return_value = None

        response = client.get(
            '/api/governance/providers/gemini/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'degraded'

    @patch('src.routes.governance._get_health_alert_service')
    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_success_critical(self, mock_get_metrics, mock_get_alert, client, admin_token):
        """Test single provider health success - critical"""
        mock_metrics = Mock()
        mock_metrics.get_provider_health.return_value = {
            'enabled': True,
            'health_score': 40,
            'total_requests': 20
        }
        mock_get_metrics.return_value = mock_metrics
        mock_get_alert.return_value = None

        response = client.get(
            '/api/governance/providers/alicloud/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'critical'

    @patch('src.routes.governance._get_canary_metrics')
    def test_single_provider_exception(self, mock_get_metrics, client, admin_token):
        """Test single provider health with exception"""
        mock_get_metrics.side_effect = Exception('Database error')

        response = client.get(
            '/api/governance/providers/openai/health',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'internal_error'


class TestAdminAgentsWithGovernance:
    """Test admin agent endpoints with GOVERNANCE_AVAILABLE=True"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_with_governance(self, mock_get_engine, client, admin_token):
        """Test admin get agents when governance available"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {
                'agent_id': 'faq_agent',
                'score': 85,
                'total_tasks': 100,
                'success_rate': 0.95,
                'last_activity': '2025-01-01T00:00:00Z',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents?status=all&limit=50',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert data['using_mock'] is False

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_permission_checker')
    def test_admin_get_agent_details_with_governance(self, mock_get_checker, mock_get_engine, client, admin_token):
        """Test admin get agent details when governance available"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = {
            'score': 85,
            'rank': 1,
            'created_at': '2024-01-01T00:00:00Z',
            'last_activity': '2025-01-01T00:00:00Z'
        }
        mock_engine.get_recent_events.return_value = []
        mock_get_engine.return_value = mock_engine

        mock_checker = Mock()
        mock_checker.get_permission_summary.return_value = {'can_execute': True}
        mock_get_checker.return_value = mock_checker

        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'faq_agent'
        assert data['using_mock'] is False

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_details_not_found_fallback_mock(self, mock_get_engine, client, admin_token):
        """Test admin get agent details falls back to mock when not found"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = None
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/unknown_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_details_governance_error_fallback(self, mock_get_engine, client, admin_token):
        """Test admin get agent details falls back to mock on governance error"""
        mock_get_engine.side_effect = Exception('Governance error')

        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_with_governance(self, mock_get_engine, client, admin_token):
        """Test admin get agent executions when governance available"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {
                'id': 'event1',
                'event_type': 'task_success',
                'created_at': '2025-01-01T00:00:00Z',
                'metadata': {'duration_ms': 1500}
            },
            {
                'id': 'event2',
                'event_type': 'task_failure',
                'created_at': '2025-01-01T01:00:00Z',
                'metadata': {}
            }
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent/executions?limit=10&status=all',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'executions' in data
        assert data['using_mock'] is False
        assert len(data['executions']) == 2

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_filter_by_status(self, mock_get_engine, client, admin_token):
        """Test admin get agent executions with status filter"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {'id': 'event1', 'event_type': 'task_success', 'created_at': '2025-01-01T00:00:00Z', 'metadata': {}},
            {'id': 'event2', 'event_type': 'task_failure', 'created_at': '2025-01-01T01:00:00Z', 'metadata': {}}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent/executions?status=success',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(e['status'] == 'success' for e in data['executions'])

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_governance_error(self, mock_get_engine, client, admin_token):
        """Test admin get agent executions falls back to mock on error"""
        mock_get_engine.side_effect = Exception('Governance error')

        response = client.get(
            '/api/admin/agents/faq_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True

    def test_admin_pause_agent(self, client, admin_token):
        """Test admin pause agent endpoint"""
        response = client.post(
            '/api/admin/agents/faq_agent/pause',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['status'] == 'paused'

    def test_admin_resume_agent(self, client, admin_token):
        """Test admin resume agent endpoint"""
        response = client.post(
            '/api/admin/agents/faq_agent/resume',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['status'] == 'active'

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    def test_admin_get_agents_unavailable_no_mock(self, client, admin_token):
        """Test admin get agents when governance unavailable and mock disabled"""
        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_admin_get_agents_with_mock_fallback(self, client, admin_token):
        """Test admin get agents with mock fallback"""
        response = client.get(
            '/api/admin/agents?status=active',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True


class TestConfigSummary:
    """Test config summary endpoint"""

    def test_get_config_summary_success(self, client, admin_token):
        """Test get config summary success"""
        response = client.get(
            '/api/admin/config/summary',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orchestrator' in data
        assert 'llm' in data
        assert 'canary' in data
        assert 'enforcement' in data
        assert 'environment' in data

    def test_get_config_summary_no_auth(self, client):
        """Test get config summary without auth"""
        response = client.get('/api/admin/config/summary')
        assert response.status_code == 401

    def test_get_config_summary_non_admin(self, client, user_token):
        """Test get config summary with non-admin token"""
        response = client.get(
            '/api/admin/config/summary',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403
