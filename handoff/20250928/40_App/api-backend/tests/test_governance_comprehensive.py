"""Comprehensive tests for governance routes"""
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


class TestGovernanceUnavailable:
    """Test governance endpoints when system is unavailable"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_agents_unavailable(self, client, admin_token):
        """Test get agents when governance unavailable"""
        response = client.get(
            '/api/governance/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not available' in data['error'].lower()
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_agent_details_unavailable(self, client, admin_token):
        """Test get agent details when governance unavailable"""
        response = client.get(
            '/api/governance/agents/agent123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_events_unavailable(self, client, admin_token):
        """Test get events when governance unavailable"""
        response = client.get(
            '/api/governance/events',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_costs_unavailable(self, client, admin_token):
        """Test get costs when governance unavailable"""
        response = client.get(
            '/api/governance/costs',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_violations_unavailable(self, client, admin_token):
        """Test get violations when governance unavailable"""
        response = client.get(
            '/api/governance/violations',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_statistics_unavailable(self, client, admin_token):
        """Test get statistics when governance unavailable"""
        response = client.get(
            '/api/governance/statistics',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_get_leaderboard_unavailable(self, client, admin_token):
        """Test get leaderboard when governance unavailable"""
        response = client.get(
            '/api/governance/leaderboard',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503


class TestGovernanceAgents:
    """Test agent-related endpoints"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_agents_success(self, mock_get_engine, client, admin_token):
        """Test successful get agents"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {'agent_id': 'agent1', 'score': 95},
            {'agent_id': 'agent2', 'score': 85}
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'agents' in data
        assert 'count' in data
        assert data['count'] == 2
        assert len(data['agents']) == 2
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_agents_empty(self, mock_get_engine, client, admin_token):
        """Test get agents with no agents"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = []
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_agents_error(self, mock_get_engine, client, admin_token):
        """Test get agents with error"""
        mock_get_engine.side_effect = Exception('Database error')
        
        response = client.get(
            '/api/governance/agents',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_agents_no_auth(self, client):
        """Test get agents without authentication"""
        response = client.get('/api/governance/agents')
        assert response.status_code == 401


class TestGovernanceAgentDetails:
    """Test agent details endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_permission_checker')
    def test_get_agent_details_success(self, mock_get_checker, mock_get_engine, client, admin_token):
        """Test successful get agent details"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = {'score': 95, 'rank': 1}
        mock_engine.get_recent_events.return_value = [
            {'event': 'task_completed', 'score': 10}
        ]
        mock_get_engine.return_value = mock_engine
        
        mock_checker = Mock()
        mock_checker.get_permission_summary.return_value = {'can_execute': True}
        mock_get_checker.return_value = mock_checker
        
        response = client.get(
            '/api/governance/agents/agent123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['agent_id'] == 'agent123'
        assert 'reputation' in data
        assert 'permissions' in data
        assert 'recent_events' in data
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_agent_details_not_found(self, mock_get_engine, client, admin_token):
        """Test get agent details for non-existent agent"""
        mock_engine = Mock()
        mock_engine.get_reputation.return_value = None
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/agents/nonexistent',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()


class TestGovernanceEvents:
    """Test events endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_events_with_agent_id(self, mock_get_engine, client, admin_token):
        """Test get events for specific agent"""
        mock_engine = Mock()
        mock_engine.get_recent_events.return_value = [
            {'event': 'task_completed', 'agent_id': 'agent123'}
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/events?agent_id=agent123&limit=10',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        assert 'count' in data
        assert data['count'] == 1
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_events_all(self, mock_get_engine, client, admin_token):
        """Test get all events"""
        mock_engine = Mock()
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [
            {'event': 'task_completed', 'agent_id': 'agent1'},
            {'event': 'task_failed', 'agent_id': 'agent2'}
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_engine._get_supabase.return_value = mock_supabase
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/events',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 2
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_events_no_database(self, mock_get_engine, client, admin_token):
        """Test get events when database unavailable"""
        mock_engine = Mock()
        mock_engine._get_supabase.return_value = None
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/events',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'error' in data


class TestGovernanceCosts:
    """Test costs endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_cost_tracker')
    def test_get_costs_summary(self, mock_get_tracker, client, admin_token):
        """Test get cost summary"""
        mock_tracker = Mock()
        mock_tracker.get_cost_summary.return_value = {
            'total': 100.50,
            'by_agent': {'agent1': 50.25}
        }
        mock_get_tracker.return_value = mock_tracker
        
        response = client.get(
            '/api/governance/costs?period=all',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data
        assert data['total'] == 100.50
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_cost_tracker')
    def test_get_costs_budget_status(self, mock_get_tracker, client, admin_token):
        """Test get budget status"""
        mock_tracker = Mock()
        mock_tracker.get_budget_status.return_value = {
            'budget': 1000,
            'spent': 250,
            'remaining': 750
        }
        mock_get_tracker.return_value = mock_tracker
        
        response = client.get(
            '/api/governance/costs?period=daily&trace_id=test123',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'budget' in data
        assert data['spent'] == 250


class TestGovernanceViolations:
    """Test violations endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_violation_detector')
    def test_get_violations_all(self, mock_get_detector, client, admin_token):
        """Test get all violations"""
        mock_detector = Mock()
        mock_detector.get_recent_violations.return_value = [
            {'type': 'budget_exceeded', 'agent_id': 'agent1'},
            {'type': 'unauthorized_action', 'agent_id': 'agent2'}
        ]
        mock_get_detector.return_value = mock_detector
        
        response = client.get(
            '/api/governance/violations',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'violations' in data
        assert data['count'] == 2
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_violation_detector')
    def test_get_violations_by_agent(self, mock_get_detector, client, admin_token):
        """Test get violations for specific agent"""
        mock_detector = Mock()
        mock_detector.get_recent_violations.return_value = [
            {'type': 'budget_exceeded', 'agent_id': 'agent123'}
        ]
        mock_get_detector.return_value = mock_detector
        
        response = client.get(
            '/api/governance/violations?agent_id=agent123&limit=10',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1


class TestGovernanceStatistics:
    """Test statistics endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    @patch('src.routes.governance.get_cost_tracker')
    def test_get_statistics_success(self, mock_get_tracker, mock_get_engine, client, admin_token):
        """Test get statistics"""
        mock_engine = Mock()
        mock_engine.get_statistics.return_value = {
            'total_agents': 10,
            'avg_score': 75.5
        }
        mock_get_engine.return_value = mock_engine
        
        mock_tracker = Mock()
        mock_tracker.get_cost_summary.return_value = {
            'total': 500,
            'daily': {'usage': {'timestamp': '2025-10-27'}}
        }
        mock_get_tracker.return_value = mock_tracker
        
        response = client.get(
            '/api/governance/statistics',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reputation' in data
        assert 'costs' in data
        assert data['reputation']['total_agents'] == 10


class TestGovernanceLeaderboard:
    """Test leaderboard endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_leaderboard_default_limit(self, mock_get_engine, client, admin_token):
        """Test get leaderboard with default limit"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {'agent_id': f'agent{i}', 'score': 100 - i} for i in range(10)
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/leaderboard',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'leaderboard' in data
        assert data['count'] == 10
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_reputation_engine')
    def test_get_leaderboard_custom_limit(self, mock_get_engine, client, admin_token):
        """Test get leaderboard with custom limit"""
        mock_engine = Mock()
        mock_engine.get_leaderboard.return_value = [
            {'agent_id': f'agent{i}', 'score': 100 - i} for i in range(5)
        ]
        mock_get_engine.return_value = mock_engine
        
        response = client.get(
            '/api/governance/leaderboard?limit=5',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 5


class TestGovernanceHealthCheck:
    """Test health check endpoint"""
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', False)
    def test_health_check_unavailable(self, client):
        """Test health check when governance unavailable"""
        response = client.get('/api/governance/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['governance_available'] is False
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_cost_tracker')
    @patch('src.routes.governance.get_reputation_engine')
    def test_health_check_all_available(self, mock_get_engine, mock_get_tracker, client):
        """Test health check when all components available"""
        mock_tracker = Mock()
        mock_tracker.redis = Mock()
        mock_get_tracker.return_value = mock_tracker
        
        mock_engine = Mock()
        mock_engine._get_supabase.return_value = Mock()
        mock_get_engine.return_value = mock_engine
        
        response = client.get('/api/governance/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['governance_available'] is True
        assert 'components' in data
        assert data['components']['cost_tracker'] == 'available'
        assert data['components']['reputation_engine'] == 'available'
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_cost_tracker')
    @patch('src.routes.governance.get_reputation_engine')
    def test_health_check_degraded(self, mock_get_engine, mock_get_tracker, client):
        """Test health check with degraded components"""
        mock_tracker = Mock()
        mock_tracker.redis = None
        mock_get_tracker.return_value = mock_tracker
        
        mock_engine = Mock()
        mock_engine._get_supabase.return_value = None
        mock_get_engine.return_value = mock_engine
        
        response = client.get('/api/governance/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['components']['cost_tracker'] == 'degraded'
        assert data['components']['reputation_engine'] == 'degraded'
    
    @patch('src.routes.governance.GOVERNANCE_AVAILABLE', True)
    @patch('src.routes.governance.get_cost_tracker')
    def test_health_check_component_error(self, mock_get_tracker, client):
        """Test health check when component raises error"""
        mock_get_tracker.side_effect = Exception('Connection failed')
        
        response = client.get('/api/governance/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['components']['cost_tracker'] == 'unavailable'
