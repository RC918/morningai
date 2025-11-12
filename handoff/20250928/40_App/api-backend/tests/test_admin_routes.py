"""
Tests for admin routes (SystemMonitoring and AgentGovernance endpoints)
P0-3: Real API Connection for Owner Console
"""
import pytest
from unittest.mock import patch, MagicMock
from src.main import app as flask_app
from src.models.user import db


@pytest.fixture
def app():
    """Create Flask app for testing"""
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


class TestSystemMonitoringEndpoints:
    """Tests for SystemMonitoring endpoints"""
    
    def test_get_system_health_success(self, client, auth_headers_admin):
        """Test GET /api/admin/system/health returns health status"""
        response = client.get('/api/admin/system/health', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['healthy', 'degraded', 'unhealthy']
        assert 'uptime_seconds' in data
        assert 'uptime_hours' in data
        assert 'services' in data
        assert 'timestamp' in data
        
        services = data['services']
        assert 'database' in services
        assert 'redis' in services
        assert 'api' in services
    
    def test_get_system_health_no_auth(self, client):
        """Test GET /api/admin/system/health without authentication returns 401"""
        response = client.get('/api/admin/system/health')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_system_metrics_success(self, client, auth_headers_admin):
        """Test GET /api/admin/system/metrics returns system metrics"""
        response = client.get('/api/admin/system/metrics', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'cpu' in data
        assert 'memory' in data
        assert 'disk' in data
        assert 'requests' in data
        assert 'timestamp' in data
        
        cpu = data['cpu']
        assert 'usage_percent' in cpu
        assert 'count' in cpu
        assert isinstance(cpu['usage_percent'], (int, float))
        assert isinstance(cpu['count'], int)
        
        memory = data['memory']
        assert 'usage_percent' in memory
        assert 'used_gb' in memory
        assert 'total_gb' in memory
        
        disk = data['disk']
        assert 'usage_percent' in disk
        assert 'used_gb' in disk
        assert 'total_gb' in disk
    
    def test_get_system_metrics_no_auth(self, client):
        """Test GET /api/admin/system/metrics without authentication returns 401"""
        response = client.get('/api/admin/system/metrics')
        
        assert response.status_code == 401
    
    def test_get_system_logs_success(self, client, auth_headers_admin):
        """Test GET /api/admin/system/logs returns logs"""
        response = client.get('/api/admin/system/logs', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'logs' in data
        assert 'count' in data
        assert 'filters' in data
        assert 'timestamp' in data
        assert isinstance(data['logs'], list)
    
    def test_get_system_logs_with_filters(self, client, auth_headers_admin):
        """Test GET /api/admin/system/logs with query parameters"""
        response = client.get(
            '/api/admin/system/logs?level=ERROR&limit=50',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'logs' in data
        assert 'filters' in data
        
        filters = data['filters']
        assert filters['level'] == 'ERROR'
        assert filters['limit'] == 50
    
    def test_get_system_logs_no_auth(self, client):
        """Test GET /api/admin/system/logs without authentication returns 401"""
        response = client.get('/api/admin/system/logs')
        
        assert response.status_code == 401


class TestAgentGovernanceEndpoints:
    """Tests for AgentGovernance admin endpoints"""
    
    def test_get_agents_success(self, client, auth_headers_admin):
        """Test GET /api/admin/agents returns agent list"""
        response = client.get('/api/admin/agents', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'agents' in data
        assert 'count' in data
        assert 'filters' in data
        assert 'timestamp' in data
        assert isinstance(data['agents'], list)
        
        if len(data['agents']) > 0:
            agent = data['agents'][0]
            assert 'id' in agent
            assert 'name' in agent
            assert 'status' in agent
            assert 'reputation_score' in agent
            assert 'total_executions' in agent
            assert 'success_rate' in agent
    
    def test_get_agents_with_filters(self, client, auth_headers_admin):
        """Test GET /api/admin/agents with query parameters"""
        response = client.get(
            '/api/admin/agents?status=active&limit=50',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'agents' in data
        assert 'filters' in data
        
        filters = data['filters']
        assert filters['status'] == 'active'
        assert filters['limit'] == 50
    
    def test_get_agents_no_auth(self, client):
        """Test GET /api/admin/agents without authentication returns 401"""
        response = client.get('/api/admin/agents')
        
        assert response.status_code == 401
    
    def test_get_agent_details_success(self, client, auth_headers_admin):
        """Test GET /api/admin/agents/:id returns agent details"""
        agent_id = 'faq_agent'
        response = client.get(f'/api/admin/agents/{agent_id}', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
        assert 'name' in data
        assert 'status' in data
        assert 'reputation' in data or 'metadata' in data
    
    def test_get_agent_details_no_auth(self, client):
        """Test GET /api/admin/agents/:id without authentication returns 401"""
        response = client.get('/api/admin/agents/faq_agent')
        
        assert response.status_code == 401
    
    def test_get_agent_executions_success(self, client, auth_headers_admin):
        """Test GET /api/admin/agents/:id/executions returns execution history"""
        agent_id = 'faq_agent'
        response = client.get(
            f'/api/admin/agents/{agent_id}/executions',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'executions' in data
        assert 'count' in data
        assert 'agent_id' in data
        assert 'filters' in data
        assert 'timestamp' in data
        assert isinstance(data['executions'], list)
    
    def test_get_agent_executions_with_filters(self, client, auth_headers_admin):
        """Test GET /api/admin/agents/:id/executions with query parameters"""
        agent_id = 'faq_agent'
        response = client.get(
            f'/api/admin/agents/{agent_id}/executions?status=success&limit=20',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'executions' in data
        assert 'filters' in data
        
        filters = data['filters']
        assert filters['status'] == 'success'
        assert filters['limit'] == 20
    
    def test_get_agent_executions_no_auth(self, client):
        """Test GET /api/admin/agents/:id/executions without authentication returns 401"""
        response = client.get('/api/admin/agents/faq_agent/executions')
        
        assert response.status_code == 401
    
    def test_pause_agent_success(self, client, auth_headers_admin):
        """Test POST /api/admin/agents/:id/pause pauses an agent"""
        agent_id = 'faq_agent'
        response = client.post(
            f'/api/admin/agents/{agent_id}/pause',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['agent_id'] == agent_id
        assert data['status'] == 'paused'
        assert 'message' in data
        assert 'timestamp' in data
    
    def test_pause_agent_no_auth(self, client):
        """Test POST /api/admin/agents/:id/pause without authentication returns 401"""
        response = client.post('/api/admin/agents/faq_agent/pause')
        
        assert response.status_code == 401
    
    def test_resume_agent_success(self, client, auth_headers_admin):
        """Test POST /api/admin/agents/:id/resume resumes an agent"""
        agent_id = 'faq_agent'
        response = client.post(
            f'/api/admin/agents/{agent_id}/resume',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['agent_id'] == agent_id
        assert data['status'] == 'active'
        assert 'message' in data
        assert 'timestamp' in data
    
    def test_resume_agent_no_auth(self, client):
        """Test POST /api/admin/agents/:id/resume without authentication returns 401"""
        response = client.post('/api/admin/agents/faq_agent/resume')
        
        assert response.status_code == 401


class TestAgentExecutionLogsEndpoint:
    """Tests for Agent Execution Logs endpoint (Task 8)"""
    
    def test_get_agent_execution_logs_success(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs returns execution logs"""
        response = client.get('/api/admin/agent-execution-logs', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'execution_logs' in data
        assert 'pagination' in data
        assert 'filters' in data
        assert 'summary' in data
        assert 'timestamp' in data
        assert isinstance(data['execution_logs'], list)
        
        pagination = data['pagination']
        assert 'page' in pagination
        assert 'page_size' in pagination
        assert 'total_items' in pagination
        assert 'total_pages' in pagination
        
        summary = data['summary']
        assert 'total_executions' in summary
        assert 'status_counts' in summary
        assert 'success_rate' in summary
    
    def test_get_agent_execution_logs_with_status_filter(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with status filter"""
        response = client.get(
            '/api/admin/agent-execution-logs?status=completed',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['status'] == 'completed'
    
    def test_get_agent_execution_logs_with_agent_id_filter(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with agent_id filter"""
        agent_id = 'test-agent-123'
        response = client.get(
            f'/api/admin/agent-execution-logs?agent_id={agent_id}',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['agent_id'] == agent_id
    
    def test_get_agent_execution_logs_with_pagination(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with pagination parameters"""
        response = client.get(
            '/api/admin/agent-execution-logs?page=2&page_size=25',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        pagination = data['pagination']
        assert pagination['page'] == 2
        assert pagination['page_size'] == 25
    
    def test_get_agent_execution_logs_with_date_range(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with date range filters"""
        start_date = '2025-11-01T00:00:00Z'
        end_date = '2025-11-12T23:59:59Z'
        response = client.get(
            f'/api/admin/agent-execution-logs?start_date={start_date}&end_date={end_date}',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['start_date'] == start_date
        assert data['filters']['end_date'] == end_date
    
    def test_get_agent_execution_logs_with_sorting(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with sorting parameters"""
        response = client.get(
            '/api/admin/agent-execution-logs?sort_by=completed_at&sort_order=asc',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['sort_by'] == 'completed_at'
        assert data['filters']['sort_order'] == 'asc'
    
    def test_get_agent_execution_logs_invalid_status(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with invalid status returns 400"""
        response = client.get(
            '/api/admin/agent-execution-logs?status=invalid_status',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid status parameter' in data['error']
    
    def test_get_agent_execution_logs_invalid_sort_by(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with invalid sort_by returns 400"""
        response = client.get(
            '/api/admin/agent-execution-logs?sort_by=invalid_field',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid sort_by parameter' in data['error']
    
    def test_get_agent_execution_logs_invalid_sort_order(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with invalid sort_order returns 400"""
        response = client.get(
            '/api/admin/agent-execution-logs?sort_order=invalid_order',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid sort_order parameter' in data['error']
    
    def test_get_agent_execution_logs_invalid_start_date(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with invalid start_date returns 400"""
        response = client.get(
            '/api/admin/agent-execution-logs?start_date=invalid-date',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid start_date parameter' in data['error']
    
    def test_get_agent_execution_logs_no_auth(self, client):
        """Test GET /api/admin/agent-execution-logs without authentication returns 401"""
        response = client.get('/api/admin/agent-execution-logs')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_agent_execution_logs_max_page_size(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs respects max page_size of 200"""
        response = client.get(
            '/api/admin/agent-execution-logs?page_size=500',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        pagination = data['pagination']
        assert pagination['page_size'] == 200
    
    def test_get_agent_execution_logs_combined_filters(self, client, auth_headers_admin):
        """Test GET /api/admin/agent-execution-logs with multiple filters"""
        response = client.get(
            '/api/admin/agent-execution-logs?status=completed&task_type=faq&page=1&page_size=10&sort_by=created_at&sort_order=desc',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = response.get_json()
        filters = data['filters']
        assert filters['status'] == 'completed'
        assert filters['task_type'] == 'faq'
        assert filters['sort_by'] == 'created_at'
        assert filters['sort_order'] == 'desc'


class TestAdminEndpointsIntegration:
    """Integration tests for admin endpoints"""
    
    def test_system_monitoring_flow(self, client, auth_headers_admin):
        """Test complete system monitoring flow"""
        health_response = client.get('/api/admin/system/health', headers=auth_headers_admin)
        assert health_response.status_code == 200
        
        metrics_response = client.get('/api/admin/system/metrics', headers=auth_headers_admin)
        assert metrics_response.status_code == 200
        
        logs_response = client.get('/api/admin/system/logs', headers=auth_headers_admin)
        assert logs_response.status_code == 200
    
    def test_agent_governance_flow(self, client, auth_headers_admin):
        """Test complete agent governance flow"""
        agents_response = client.get('/api/admin/agents', headers=auth_headers_admin)
        assert agents_response.status_code == 200
        agents_data = agents_response.get_json()
        
        if len(agents_data['agents']) > 0:
            agent_id = agents_data['agents'][0]['id']
            
            details_response = client.get(
                f'/api/admin/agents/{agent_id}',
                headers=auth_headers_admin
            )
            assert details_response.status_code == 200
            
            executions_response = client.get(
                f'/api/admin/agents/{agent_id}/executions',
                headers=auth_headers_admin
            )
            assert executions_response.status_code == 200
            
            pause_response = client.post(
                f'/api/admin/agents/{agent_id}/pause',
                headers=auth_headers_admin
            )
            assert pause_response.status_code == 200
            
            resume_response = client.post(
                f'/api/admin/agents/{agent_id}/resume',
                headers=auth_headers_admin
            )
            assert resume_response.status_code == 200
    
    def test_agent_execution_logs_flow(self, client, auth_headers_admin):
        """Test agent execution logs endpoint flow"""
        response = client.get('/api/admin/agent-execution-logs', headers=auth_headers_admin)
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'execution_logs' in data
        assert 'summary' in data
        
        summary = data['summary']
        assert 'total_executions' in summary
        assert 'status_counts' in summary
        assert 'success_rate' in summary
