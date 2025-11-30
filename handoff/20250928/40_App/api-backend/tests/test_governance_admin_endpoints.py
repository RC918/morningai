"""Comprehensive tests for governance admin endpoints to improve coverage to 80%"""
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


class TestAdminGetAgents:
    """Test admin get agents endpoint"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_success(self, mock_get_engine, client, admin_token):
        """Test successful admin get agents with governance available"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {
                'agent_id': 'faq_agent',
                'score': 95,
                'total_tasks': 1234,
                'success_rate': 0.95,
                'last_activity': '2025-10-27T12:00:00Z',
                'created_at': '2025-01-01T00:00:00Z'
            },
            {
                'agent_id': 'dev_agent',
                'score': 88,
                'total_tasks': 567,
                'success_rate': 0.92,
                'last_activity': '2025-10-27T11:00:00Z',
                'created_at': '2025-01-15T00:00:00Z'
            }
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert 'count' in data
        assert data['count'] == 2
        assert data['using_mock'] is False
        assert 'filters' in data
        assert 'timestamp' in data

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_with_status_filter(self, mock_get_engine, client, admin_token):
        """Test admin get agents with status filter"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {'agent_id': 'agent1', 'score': 95, 'total_tasks': 100, 'success_rate': 0.9}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents?status=active&limit=50',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filters']['status'] == 'active'
        assert data['filters']['limit'] == 50

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
        assert 'unavailable' in data['error'].lower()

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_admin_get_agents_with_mock_data(self, client, admin_token):
        """Test admin get agents returns mock data when governance unavailable"""
        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert data['using_mock'] is True
        assert len(data['agents']) > 0

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_error_handling(self, mock_get_engine, client, admin_token):
        """Test admin get agents error handling"""
        mock_get_engine.side_effect = Exception('Database connection failed')

        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_admin_get_agents_no_auth(self, client):
        """Test admin get agents without authentication"""
        response = client.get('/api/admin/agents')
        assert response.status_code == 401

    def test_admin_get_agents_non_admin(self, client, user_token):
        """Test admin get agents with non-admin user"""
        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403


class TestAdminGetAgentDetails:
    """Test admin get agent details endpoint"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_permission_checker')
    def test_admin_get_agent_details_success(
        self, mock_get_checker, mock_get_engine, client, admin_token
    ):
        """Test successful admin get agent details"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = {
            'score': 95,
            'rank': 1,
            'total_tasks': 1234,
            'success_rate': 0.95,
            'created_at': '2025-01-01T00:00:00Z',
            'last_activity': '2025-10-27T12:00:00Z'
        }
        mock_engine.get_recent_events.return_value = [
            {'event_type': 'task_success', 'created_at': '2025-10-27T12:00:00Z'}
        ]
        mock_get_engine.return_value = mock_engine

        mock_checker = Mock()
        mock_checker.get_permission_summary.return_value = {
            'can_execute': True,
            'rate_limit': 100
        }
        mock_get_checker.return_value = mock_checker

        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'faq_agent'
        assert 'reputation' in data
        assert 'permissions' in data
        assert data['using_mock'] is False

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_permission_checker')
    def test_admin_get_agent_details_not_found_uses_mock(
        self, mock_get_checker, mock_get_engine, client, admin_token
    ):
        """Test admin get agent details returns mock when agent not found"""
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
    @patch('src.routes.governance.get_permission_checker')
    def test_admin_get_agent_details_governance_error_uses_mock(
        self, mock_get_checker, mock_get_engine, client, admin_token
    ):
        """Test admin get agent details uses mock on governance error"""
        mock_engine = Mock()
        mock_engine.get_reputation.side_effect = Exception('Database error')
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    def test_admin_get_agent_details_unavailable_no_mock(self, client, admin_token):
        """Test admin get agent details when governance unavailable and mock disabled"""
        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_admin_get_agent_details_with_mock(self, client, admin_token):
        """Test admin get agent details returns mock data"""
        response = client.get(
            '/api/admin/agents/faq_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True
        assert 'reputation' in data
        assert 'permissions' in data


class TestAdminGetAgentExecutions:
    """Test admin get agent executions endpoint"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_success(self, mock_get_engine, client, admin_token):
        """Test successful admin get agent executions"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {
                'id': 'event1',
                'event_type': 'task_success',
                'created_at': '2025-10-27T12:00:00Z',
                'metadata': {'duration_ms': 1500}
            },
            {
                'id': 'event2',
                'event_type': 'task_failure',
                'created_at': '2025-10-27T11:00:00Z',
                'metadata': {'duration_ms': 2000}
            }
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'executions' in data
        assert data['count'] == 2
        assert data['agent_id'] == 'faq_agent'
        assert data['using_mock'] is False

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_with_filters(self, mock_get_engine, client, admin_token):
        """Test admin get agent executions with filters"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {'id': 'event1', 'event_type': 'task_success', 'created_at': '2025-10-27T12:00:00Z', 'metadata': {}}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent/executions?limit=10&status=success',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filters']['limit'] == 10
        assert data['filters']['status'] == 'success'

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agent_executions_governance_error_uses_mock(
        self, mock_get_engine, client, admin_token
    ):
        """Test admin get agent executions uses mock on governance error"""
        mock_engine = Mock()
        mock_engine.get_recent_events.side_effect = Exception('Database error')
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/faq_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    def test_admin_get_agent_executions_unavailable_no_mock(self, client, admin_token):
        """Test admin get agent executions when governance unavailable and mock disabled"""
        response = client.get(
            '/api/admin/agents/faq_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_admin_get_agent_executions_with_mock(self, client, admin_token):
        """Test admin get agent executions returns mock data"""
        response = client.get(
            '/api/admin/agents/faq_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['using_mock'] is True
        assert 'executions' in data


class TestAdminPauseResumeAgent:
    """Test admin pause and resume agent endpoints"""

    def test_admin_pause_agent_success(self, client, admin_token):
        """Test successful admin pause agent"""
        response = client.post(
            '/api/admin/agents/faq_agent/pause',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['agent_id'] == 'faq_agent'
        assert data['status'] == 'paused'
        assert 'message' in data
        assert 'timestamp' in data

    def test_admin_resume_agent_success(self, client, admin_token):
        """Test successful admin resume agent"""
        response = client.post(
            '/api/admin/agents/faq_agent/resume',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['agent_id'] == 'faq_agent'
        assert data['status'] == 'active'
        assert 'message' in data
        assert 'timestamp' in data

    def test_admin_pause_agent_no_auth(self, client):
        """Test admin pause agent without authentication"""
        response = client.post('/api/admin/agents/faq_agent/pause')
        assert response.status_code == 401

    def test_admin_resume_agent_no_auth(self, client):
        """Test admin resume agent without authentication"""
        response = client.post('/api/admin/agents/faq_agent/resume')
        assert response.status_code == 401

    def test_admin_pause_agent_non_admin(self, client, user_token):
        """Test admin pause agent with non-admin user"""
        response = client.post(
            '/api/admin/agents/faq_agent/pause',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403

    def test_admin_resume_agent_non_admin(self, client, user_token):
        """Test admin resume agent with non-admin user"""
        response = client.post(
            '/api/admin/agents/faq_agent/resume',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403


class TestMockDataFunctions:
    """Test mock data helper functions"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_mock_agents_data_structure(self, client, admin_token):
        """Test mock agents data has correct structure"""
        response = client.get(
            '/api/admin/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        for agent in data['agents']:
            assert 'id' in agent
            assert 'name' in agent
            assert 'status' in agent
            assert 'reputation_score' in agent
            assert 'total_executions' in agent
            assert 'success_rate' in agent
            assert 'last_execution' in agent
            assert 'created_at' in agent

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_mock_agent_details_data_structure(self, client, admin_token):
        """Test mock agent details data has correct structure"""
        response = client.get(
            '/api/admin/agents/test_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'id' in data
        assert 'name' in data
        assert 'status' in data
        assert 'reputation' in data
        assert 'permissions' in data
        assert 'metadata' in data

        assert 'score' in data['reputation']
        assert 'can_execute' in data['permissions']

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_mock_executions_data_structure(self, client, admin_token):
        """Test mock executions data has correct structure"""
        response = client.get(
            '/api/admin/agents/test_agent/executions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)

        for execution in data['executions']:
            assert 'id' in execution
            assert 'agent_id' in execution
            assert 'status' in execution
            assert 'started_at' in execution
            assert 'completed_at' in execution
            assert 'duration_ms' in execution
            assert 'metadata' in execution

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_mock_agents_limit_respected(self, client, admin_token):
        """Test mock agents respects limit parameter"""
        response = client.get(
            '/api/admin/agents?limit=2',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['agents']) <= 2

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', True)
    def test_mock_executions_limit_respected(self, client, admin_token):
        """Test mock executions respects limit parameter"""
        response = client.get(
            '/api/admin/agents/test_agent/executions?limit=5',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['executions']) <= 5


class TestGovernanceEndpointsWithGovernanceAvailable:
    """Test governance endpoints when GOVERNANCE_AVAILABLE is True"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_permission_checker')
    def test_get_agent_details_with_all_data(
        self, mock_get_checker, mock_get_engine, client, admin_token
    ):
        """Test get agent details returns all expected fields"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = {
            'score': 95,
            'rank': 1,
            'total_tasks': 100,
            'success_rate': 0.95
        }
        mock_engine.get_recent_events.return_value = [
            {'event': 'task_completed', 'score': 10}
        ]
        mock_get_engine.return_value = mock_engine

        mock_checker = Mock()
        mock_checker.get_permission_summary.return_value = {'can_execute': True}
        mock_get_checker.return_value = mock_checker

        response = client.get(
            '/api/governance/agents/test_agent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agent_id' in data
        assert 'reputation' in data
        assert 'permissions' in data
        assert 'recent_events' in data


class TestGovernanceStatusFilterBranches:
    """Test status filter branches in admin endpoints"""

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_filter_active(self, mock_get_engine, client, admin_token):
        """Test filtering agents by active status"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {'agent_id': 'agent1', 'score': 95, 'total_tasks': 100, 'success_rate': 0.9}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents?status=active',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        for agent in data['agents']:
            assert agent['status'] == 'active'

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_agents_filter_paused(self, mock_get_engine, client, admin_token):
        """Test filtering agents by paused status"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = []
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents?status=paused',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['filters']['status'] == 'paused'

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_executions_filter_success(self, mock_get_engine, client, admin_token):
        """Test filtering executions by success status"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {'id': 'e1', 'event_type': 'task_success', 'created_at': '2025-10-27T12:00:00Z', 'metadata': {}},
            {'id': 'e2', 'event_type': 'task_failure', 'created_at': '2025-10-27T11:00:00Z', 'metadata': {}}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/test_agent/executions?status=success',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        for execution in data['executions']:
            assert execution['status'] == 'success'

    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.ALLOW_GOVERNANCE_MOCK', False)
    @patch('src.routes.governance.get_reputation_engine')
    def test_admin_get_executions_filter_failure(self, mock_get_engine, client, admin_token):
        """Test filtering executions by failure status"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {'id': 'e1', 'event_type': 'task_success', 'created_at': '2025-10-27T12:00:00Z', 'metadata': {}},
            {'id': 'e2', 'event_type': 'task_failure', 'created_at': '2025-10-27T11:00:00Z', 'metadata': {}}
        ]
        mock_get_engine.return_value = mock_engine

        response = client.get(
            '/api/admin/agents/test_agent/executions?status=failure',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        for execution in data['executions']:
            assert execution['status'] == 'failure'
