"""Test governance API routes"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    with patch('src.middleware.auth_middleware.jwt_required', lambda f: f), \
         patch('src.middleware.auth_middleware.admin_required', lambda f: f):
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        from src.routes.governance import bp
        app.register_blueprint(bp)
        
        return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication"""
    return 'Bearer mock_jwt_token'


@pytest.fixture
def mock_governance_modules():
    """Mock governance modules"""
    with patch('src.routes.governance.GOVERNANCE_AVAILABLE', True), \
         patch('src.routes.governance.get_reputation_engine') as mock_reputation, \
         patch('src.routes.governance.get_cost_tracker') as mock_cost, \
         patch('src.routes.governance.get_permission_checker') as mock_permission, \
         patch('src.routes.governance.get_violation_detector') as mock_violation:
        
        mock_reputation_engine = Mock()
        mock_reputation_engine.get_leaderboard.return_value = [
            {'agent_id': 'agent1', 'score': 95},
            {'agent_id': 'agent2', 'score': 85}
        ]
        mock_reputation_engine.get_reputation.return_value = {
            'score': 95,
            'rank': 1,
            'total_tasks': 100
        }
        mock_reputation_engine.get_recent_events.return_value = [
            {'event_type': 'task_completed', 'score_change': 5}
        ]
        mock_reputation_engine.get_statistics.return_value = {
            'total_agents': 10,
            'average_score': 75
        }
        mock_reputation_engine._get_supabase.return_value = None
        
        mock_cost_tracker_instance = Mock()
        mock_cost_tracker_instance.get_cost_summary.return_value = {
            'total_cost': 100.0,
            'daily': {'usage': {}}
        }
        mock_cost_tracker_instance.get_budget_status.return_value = {
            'used': 50.0,
            'limit': 100.0
        }
        mock_cost_tracker_instance.redis = True
        
        mock_permission_checker_instance = Mock()
        mock_permission_checker_instance.get_permission_summary.return_value = {
            'level': 'prod_full_access',
            'allowed_tools': ['read', 'write']
        }
        
        mock_violation_detector_instance = Mock()
        mock_violation_detector_instance.get_recent_violations.return_value = [
            {'violation_type': 'unauthorized_access', 'timestamp': '2025-10-24'}
        ]
        
        mock_reputation.return_value = mock_reputation_engine
        mock_cost.return_value = mock_cost_tracker_instance
        mock_permission.return_value = mock_permission_checker_instance
        mock_violation.return_value = mock_violation_detector_instance
        
        yield {
            'reputation': mock_reputation_engine,
            'cost': mock_cost_tracker_instance,
            'permission': mock_permission_checker_instance,
            'violation': mock_violation_detector_instance
        }


class TestGovernanceAPIRoutes:
    """Test governance API endpoints"""
    
    def test_get_agents_success(self, client, mock_governance_modules):
        """Test GET /api/governance/agents returns agent list"""
        response = client.get('/api/governance/agents')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'agents' in data
        assert 'count' in data
        assert data['count'] == 2
        assert len(data['agents']) == 2
    
    def test_get_agents_governance_unavailable(self, client):
        """Test GET /api/governance/agents when governance is unavailable"""
        with patch('src.routes.governance.GOVERNANCE_AVAILABLE', False):
            response = client.get('/api/governance/agents')
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error']
    
    def test_get_agents_exception(self, client, mock_governance_modules):
        """Test GET /api/governance/agents handles exceptions"""
        mock_governance_modules['reputation'].get_leaderboard.side_effect = Exception('Database error')
        
        response = client.get('/api/governance/agents')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_get_agent_details_success(self, client, mock_governance_modules):
        """Test GET /api/governance/agents/<agent_id> returns agent details"""
        response = client.get('/api/governance/agents/agent1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'agent_id' in data
        assert 'reputation' in data
        assert 'permissions' in data
        assert 'recent_events' in data
        assert data['agent_id'] == 'agent1'
    
    def test_get_agent_details_not_found(self, client, mock_governance_modules):
        """Test GET /api/governance/agents/<agent_id> when agent not found"""
        mock_governance_modules['reputation'].get_reputation.return_value = None
        
        response = client.get('/api/governance/agents/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error']
    
    def test_get_events_all(self, client, mock_governance_modules):
        """Test GET /api/governance/events returns all events"""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [
            {'event_type': 'task_completed', 'agent_id': 'agent1'},
            {'event_type': 'task_failed', 'agent_id': 'agent2'}
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_response
        mock_governance_modules['reputation']._get_supabase.return_value = mock_supabase
        
        response = client.get('/api/governance/events')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'events' in data
        assert 'count' in data
        assert data['count'] == 2
    
    def test_get_events_by_agent(self, client, mock_governance_modules):
        """Test GET /api/governance/events with agent_id filter"""
        response = client.get('/api/governance/events?agent_id=agent1&limit=10')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'events' in data
        assert 'count' in data
    
    def test_get_events_database_unavailable(self, client, mock_governance_modules):
        """Test GET /api/governance/events when database is unavailable"""
        mock_governance_modules['reputation']._get_supabase.return_value = None
        
        response = client.get('/api/governance/events')
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    def test_get_costs_all(self, client, mock_governance_modules):
        """Test GET /api/governance/costs with period=all"""
        response = client.get('/api/governance/costs?period=all')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_cost' in data
    
    def test_get_costs_daily(self, client, mock_governance_modules):
        """Test GET /api/governance/costs with period=daily"""
        response = client.get('/api/governance/costs?period=daily')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'used' in data
        assert 'limit' in data
    
    def test_get_costs_with_trace_id(self, client, mock_governance_modules):
        """Test GET /api/governance/costs with trace_id"""
        response = client.get('/api/governance/costs?trace_id=trace123&period=daily')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'used' in data
    
    def test_get_violations_all(self, client, mock_governance_modules):
        """Test GET /api/governance/violations returns all violations"""
        response = client.get('/api/governance/violations')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'violations' in data
        assert 'count' in data
        assert data['count'] == 1
    
    def test_get_violations_by_agent(self, client, mock_governance_modules):
        """Test GET /api/governance/violations with agent_id filter"""
        response = client.get('/api/governance/violations?agent_id=agent1&limit=20')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'violations' in data
    
    def test_get_statistics_success(self, client, mock_governance_modules):
        """Test GET /api/governance/statistics returns system statistics"""
        response = client.get('/api/governance/statistics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'reputation' in data
        assert 'costs' in data
        assert 'timestamp' in data
    
    def test_get_leaderboard_default_limit(self, client, mock_governance_modules):
        """Test GET /api/governance/leaderboard with default limit"""
        response = client.get('/api/governance/leaderboard')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'leaderboard' in data
        assert 'count' in data
    
    def test_get_leaderboard_custom_limit(self, client, mock_governance_modules):
        """Test GET /api/governance/leaderboard with custom limit"""
        response = client.get('/api/governance/leaderboard?limit=5')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'leaderboard' in data
    
    def test_health_check_governance_available(self, client, mock_governance_modules):
        """Test GET /api/governance/health when governance is available"""
        response = client.get('/api/governance/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'governance_available' in data
        assert 'components' in data
        assert data['governance_available'] is True
    
    def test_health_check_governance_unavailable(self, client):
        """Test GET /api/governance/health when governance is unavailable"""
        with patch('src.routes.governance.GOVERNANCE_AVAILABLE', False):
            response = client.get('/api/governance/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['governance_available'] is False
    
    def test_health_check_component_status(self, client, mock_governance_modules):
        """Test GET /api/governance/health includes component status"""
        response = client.get('/api/governance/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'components' in data
        assert 'cost_tracker' in data['components']
        assert 'reputation_engine' in data['components']
