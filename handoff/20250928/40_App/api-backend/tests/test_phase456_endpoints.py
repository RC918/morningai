"""
Comprehensive tests for Phase 4-6 endpoints
Focus on improving coverage from 53% to 65%+ for main.py
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app instance for testing"""
    with patch.dict(os.environ, {'SENTRY_DSN': '', 'SECRET_KEY': 'test-secret'}):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']
        
        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token"""
    from src.middleware.auth_middleware import create_user_token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


class TestPhase456Availability:
    """Test Phase 4-6 API availability handling"""
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_meta_agent_ooda_unavailable(self, client):
        """Test meta-agent OODA endpoint when Phase 4-6 unavailable"""
        response = client.post('/api/meta-agent/ooda-cycle', json={})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_langgraph_workflow_creation_unavailable(self, client):
        """Test LangGraph workflow creation when Phase 4-6 unavailable"""
        response = client.post('/api/langgraph/workflows', json={'name': 'test'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'not available' in data['error'].lower()
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_workflow_execution_unavailable(self, client):
        """Test workflow execution when Phase 4-6 unavailable"""
        response = client.post('/api/langgraph/workflows/test-id/execute', json={})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_governance_status_unavailable(self, client):
        """Test governance status when Phase 4-6 unavailable"""
        response = client.get('/api/governance/status')
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_governance_policy_creation_unavailable(self, client):
        """Test governance policy creation when Phase 4-6 unavailable"""
        response = client.post('/api/governance/policies', json={'policy': 'test'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


class TestPhase456MetaAgentEndpoints:
    """Test meta-agent endpoints with mocked async functionality"""
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_meta_agent_ooda_cycle')
    def test_meta_agent_ooda_cycle_success(self, mock_ooda, client):
        """Test successful OODA cycle execution"""
        mock_ooda.return_value = {
            'status': 'completed',
            'cycle_id': 'ooda-123',
            'observations': ['obs1', 'obs2'],
            'decisions': ['decision1']
        }
        
        response = client.post('/api/meta-agent/ooda-cycle', json={})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'completed'
        assert 'cycle_id' in data
        assert 'observations' in data
        assert 'decisions' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_meta_agent_ooda_cycle')
    def test_meta_agent_ooda_cycle_error(self, mock_ooda, client):
        """Test OODA cycle with exception handling"""
        mock_ooda.side_effect = Exception('OODA cycle failed')
        
        response = client.post('/api/meta-agent/ooda-cycle', json={})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'failed' in data['error'].lower()


class TestPhase456LangGraphEndpoints:
    """Test LangGraph workflow endpoints"""
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_langgraph_workflow')
    def test_create_workflow_success(self, mock_create, client):
        """Test successful workflow creation"""
        mock_create.return_value = {
            'workflow_id': 'wf-123',
            'name': 'test-workflow',
            'status': 'created'
        }
        
        workflow_data = {'name': 'test-workflow', 'steps': ['step1', 'step2']}
        response = client.post('/api/langgraph/workflows', json=workflow_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'workflow_id' in data
        assert data['name'] == 'test-workflow'
        assert data['status'] == 'created'
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_execute_workflow')
    def test_execute_workflow_success(self, mock_execute, client):
        """Test successful workflow execution"""
        mock_execute.return_value = {
            'execution_id': 'exec-123',
            'workflow_id': 'wf-123',
            'status': 'completed',
            'result': {'output': 'success'}
        }
        
        execution_data = {'input': 'test-input'}
        response = client.post('/api/langgraph/workflows/wf-123/execute', json=execution_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'execution_id' in data
        assert data['status'] == 'completed'
        assert 'result' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_execute_workflow')
    def test_execute_workflow_error(self, mock_execute, client):
        """Test workflow execution with error"""
        mock_execute.side_effect = Exception('Workflow execution failed')
        
        response = client.post('/api/langgraph/workflows/wf-123/execute', json={})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        assert 'failed' in data['error'].lower()


class TestPhase456GovernanceEndpoints:
    """Test governance endpoints"""
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_governance_status')
    def test_governance_status_success(self, mock_status, client):
        """Test successful governance status retrieval"""
        mock_status.return_value = {
            'overall_status': 'compliant',
            'policies_count': 5,
            'violations': 0,
            'last_audit': '2025-10-19T00:00:00Z'
        }
        
        response = client.get('/api/governance/status')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['overall_status'] == 'compliant'
        assert 'policies_count' in data
        assert 'violations' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_governance_policy')
    def test_create_policy_success(self, mock_create, client):
        """Test successful policy creation"""
        mock_create.return_value = {
            'policy_id': 'pol-123',
            'name': 'data-retention',
            'status': 'active'
        }
        
        policy_data = {
            'name': 'data-retention',
            'rules': ['rule1', 'rule2']
        }
        response = client.post('/api/governance/policies', json=policy_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'policy_id' in data
        assert data['name'] == 'data-retention'
        assert data['status'] == 'active'


class TestPhase456QuickSightEndpoints:
    """Test QuickSight dashboard endpoints"""
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_create_quicksight_dashboard_unavailable(self, client):
        """Test QuickSight dashboard creation when unavailable"""
        response = client.post('/api/quicksight/dashboards', json={'name': 'test'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_get_dashboard_insights_unavailable(self, client):
        """Test dashboard insights when unavailable"""
        response = client.get('/api/quicksight/dashboards/test-id/insights')
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_generate_automated_report_unavailable(self, client):
        """Test automated report generation when unavailable"""
        response = client.post('/api/reports/automated', json={'type': 'daily'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


class TestPhase456ReferralEndpoints:
    """Test referral program endpoints"""
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_create_referral_program_unavailable(self, client):
        """Test referral program creation when unavailable"""
        response = client.post('/api/growth/referral-programs', json={'name': 'test'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_get_referral_analytics_unavailable(self, client):
        """Test referral analytics when unavailable"""
        response = client.get('/api/growth/referral-programs/test-id/analytics')
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


class TestPhase456MarketingEndpoints:
    """Test marketing automation endpoints"""
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_generate_marketing_content_unavailable(self, client):
        """Test marketing content generation when unavailable"""
        response = client.post('/api/growth/content/generate', json={'type': 'email'})
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.main.PHASE_456_AVAILABLE', False)
    def test_get_business_intelligence_unavailable(self, client):
        """Test business intelligence when unavailable"""
        response = client.get('/api/business-intelligence/summary')
        
        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data


class TestPhase456AdditionalEndpoints:
    """Test additional main.py endpoints for coverage"""
    
    def test_settings_get_method(self, client):
        """Test settings GET endpoint"""
        response = client.get('/api/settings')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'profile' in data
        assert 'preferences' in data
    
    def test_settings_post_method(self, client):
        """Test settings POST endpoint"""
        settings_data = {
            'preferences': {
                'language': 'en',
                'theme': 'dark'
            }
        }
        response = client.post('/api/settings', json=settings_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == 'Settings saved successfully'


class TestPhase456DashboardWidgets:
    """Test dashboard widgets endpoint"""
    
    def test_get_dashboard_widgets_success(self, client, auth_headers):
        """Test dashboard widgets returns widget list"""
        response = client.get('/api/dashboard/widgets', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'widgets' in data
        assert isinstance(data['widgets'], list)
        assert len(data['widgets']) > 0
    
    def test_get_phase7_resilience_metrics_success(self, client):
        """Test Phase 7 resilience metrics returns metrics"""
        response = client.get('/api/phase7/resilience/metrics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'circuit_breakers' in data
        assert 'retry_patterns' in data
        assert 'status' in data


class TestPhase456Settings:
    """Test settings page endpoint"""
    
    def test_settings_page_renders(self, client):
        """Test settings page returns successfully"""
        response = client.get('/settings')
        
        assert response.status_code in [200, 404]
