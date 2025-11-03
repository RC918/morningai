"""
Tests for admin routes (SystemMonitoring and AgentGovernance endpoints)
P0-3: Real API Connection for Owner Console
"""
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from src.routes.admin import bp as admin_bp
from src.routes.governance import admin_bp as admin_agents_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_agents_bp)
    return app


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
