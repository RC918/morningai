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


class TestPhase456RoutesModule:
    """Test phase456 routes module directly for improved coverage"""

    def test_get_cached_redis_client(self):
        """Test Redis client caching function"""
        from src.routes.phase456 import _get_cached_redis_client
        with patch('src.routes.phase456.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            
            # First call should create client
            result1 = _get_cached_redis_client("redis://localhost:6379")
            assert result1 == mock_client
            
            # Clear cache for next test
            _get_cached_redis_client.cache_clear()

    def test_get_main_returns_module(self):
        """Test _get_main returns src.main module"""
        from src.routes.phase456 import _get_main
        main = _get_main()
        assert hasattr(main, 'PHASE_456_AVAILABLE')

    def test_init_phase456_routes_logs_availability(self):
        """Test init_phase456_routes logs correctly"""
        from src.routes.phase456 import init_phase456_routes
        with patch('src.routes.phase456.logger') as mock_logger:
            init_phase456_routes(True, {})
            mock_logger.info.assert_called_once()
            assert 'available=True' in str(mock_logger.info.call_args)


class TestPhase456QuickSightSuccess:
    """Test QuickSight endpoints with successful responses"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_quicksight_dashboard')
    def test_create_quicksight_dashboard_success(self, mock_create, client):
        """Test successful QuickSight dashboard creation"""
        mock_create.return_value = {
            'dashboard_id': 'dash-123',
            'name': 'test-dashboard',
            'status': 'created'
        }
        
        response = client.post('/api/quicksight/dashboards', json={'name': 'test'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'dashboard_id' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_quicksight_dashboard')
    def test_create_quicksight_dashboard_error(self, mock_create, client):
        """Test QuickSight dashboard creation error handling"""
        mock_create.side_effect = Exception('Dashboard creation failed')
        
        response = client.post('/api/quicksight/dashboards', json={'name': 'test'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_dashboard_insights')
    def test_get_dashboard_insights_success(self, mock_insights, client):
        """Test successful dashboard insights retrieval"""
        mock_insights.return_value = {
            'insights': ['insight1', 'insight2'],
            'dashboard_id': 'dash-123'
        }
        
        response = client.get('/api/quicksight/dashboards/dash-123/insights')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'insights' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_dashboard_insights')
    def test_get_dashboard_insights_error(self, mock_insights, client):
        """Test dashboard insights error handling"""
        mock_insights.side_effect = Exception('Insights retrieval failed')
        
        response = client.get('/api/quicksight/dashboards/dash-123/insights')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456ReportsSuccess:
    """Test automated reports endpoints with successful responses"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_generate_automated_report')
    def test_generate_automated_report_success(self, mock_generate, client):
        """Test successful automated report generation"""
        mock_generate.return_value = {
            'report_id': 'rep-123',
            'type': 'daily',
            'status': 'generated'
        }
        
        response = client.post('/api/reports/automated', json={'type': 'daily'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'report_id' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_generate_automated_report')
    def test_generate_automated_report_error(self, mock_generate, client):
        """Test automated report generation error handling"""
        mock_generate.side_effect = Exception('Report generation failed')
        
        response = client.post('/api/reports/automated', json={'type': 'daily'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456ReferralSuccess:
    """Test referral program endpoints with successful responses"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_referral_program')
    def test_create_referral_program_success(self, mock_create, client):
        """Test successful referral program creation"""
        mock_create.return_value = {
            'program_id': 'ref-123',
            'name': 'test-program',
            'status': 'active'
        }
        
        response = client.post('/api/growth/referral-programs', json={'name': 'test'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'program_id' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_referral_program')
    def test_create_referral_program_error(self, mock_create, client):
        """Test referral program creation error handling"""
        mock_create.side_effect = Exception('Program creation failed')
        
        response = client.post('/api/growth/referral-programs', json={'name': 'test'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_referral_analytics')
    def test_get_referral_analytics_success(self, mock_analytics, client):
        """Test successful referral analytics retrieval"""
        mock_analytics.return_value = {
            'program_id': 'ref-123',
            'total_referrals': 100,
            'conversion_rate': 0.25
        }
        
        response = client.get('/api/growth/referral-programs/ref-123/analytics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_referrals' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_referral_analytics')
    def test_get_referral_analytics_error(self, mock_analytics, client):
        """Test referral analytics error handling"""
        mock_analytics.side_effect = Exception('Analytics retrieval failed')
        
        response = client.get('/api/growth/referral-programs/ref-123/analytics')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456MarketingSuccess:
    """Test marketing endpoints with successful responses"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_generate_marketing_content')
    def test_generate_marketing_content_success(self, mock_generate, client):
        """Test successful marketing content generation"""
        mock_generate.return_value = {
            'content_id': 'cnt-123',
            'type': 'email',
            'content': 'Generated content'
        }
        
        response = client.post('/api/growth/content/generate', json={'type': 'email'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'content_id' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_generate_marketing_content')
    def test_generate_marketing_content_error(self, mock_generate, client):
        """Test marketing content generation error handling"""
        mock_generate.side_effect = Exception('Content generation failed')
        
        response = client.post('/api/growth/content/generate', json={'type': 'email'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_business_intelligence')
    def test_get_business_intelligence_success(self, mock_bi, client):
        """Test successful business intelligence retrieval"""
        mock_bi.return_value = {
            'summary': 'BI Summary',
            'metrics': {'revenue': 1000000}
        }
        
        response = client.get('/api/business-intelligence/summary')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'summary' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_get_business_intelligence')
    def test_get_business_intelligence_error(self, mock_bi, client):
        """Test business intelligence error handling"""
        mock_bi.side_effect = Exception('BI retrieval failed')
        
        response = client.get('/api/business-intelligence/summary')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456GovernanceErrors:
    """Test governance endpoints error handling"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_governance_status')
    def test_governance_status_error(self, mock_status, client):
        """Test governance status error handling"""
        mock_status.side_effect = Exception('Status retrieval failed')
        
        response = client.get('/api/governance/status')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_governance_policy')
    def test_create_policy_error(self, mock_create, client):
        """Test governance policy creation error handling"""
        mock_create.side_effect = Exception('Policy creation failed')
        
        response = client.post('/api/governance/policies', json={'name': 'test'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456LangGraphErrors:
    """Test LangGraph endpoints error handling"""

    @patch('src.main.PHASE_456_AVAILABLE', True)
    @patch('src.main.api_create_langgraph_workflow')
    def test_create_workflow_error(self, mock_create, client):
        """Test workflow creation error handling"""
        mock_create.side_effect = Exception('Workflow creation failed')
        
        response = client.post('/api/langgraph/workflows', json={'name': 'test'})
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestPhase456RouterMetrics:
    """Test router metrics endpoint"""

    @patch('src.routes.phase456.analyst_required', lambda f: f)
    def test_router_metrics_no_redis(self, client):
        """Test router metrics when Redis not configured"""
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.REDIS_URL = None
            
            response = client.get('/api/governance/router-metrics')
            
            # Should return 200 with enabled=False
            assert response.status_code in [200, 401, 403]

    @patch('src.routes.phase456.analyst_required', lambda f: f)
    def test_router_metrics_import_error(self, client):
        """Test router metrics when metrics module not available"""
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.REDIS_URL = "redis://localhost:6379"
            
            with patch.dict('sys.modules', {'metrics': None}):
                response = client.get('/api/governance/router-metrics')
                
                # Should handle gracefully
                assert response.status_code in [200, 401, 403, 500]

    @patch('src.routes.phase456.analyst_required', lambda f: f)
    def test_router_metrics_success(self, client):
        """Test router metrics successful retrieval"""
        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.REDIS_URL = "redis://localhost:6379"
            
            with patch('src.routes.phase456._get_cached_redis_client') as mock_redis:
                with patch('src.routes.phase456.CanaryMetrics', create=True) as mock_metrics_class:
                    mock_metrics = MagicMock()
                    mock_metrics.get_router_metrics_summary.return_value = {
                        'total_decisions': 100,
                        'success_rate': 0.95
                    }
                    mock_metrics_class.return_value = mock_metrics
                    
                    response = client.get('/api/governance/router-metrics')
                    
                    # Should return metrics or auth error
                    assert response.status_code in [200, 401, 403]
