"""
Comprehensive tests for dashboard endpoints
Focus on improving coverage to 60%+
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    app.config['TESTING'] = True
    return app.test_client()


class TestDashboardMetrics:
    """Test dashboard metrics endpoints"""
    
    def test_get_system_metrics_success(self, client):
        """Test successful retrieval of system metrics"""
        response = client.get('/api/dashboard/metrics')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'cpu_usage' in data
        assert 'memory_usage' in data
        assert 'response_time' in data
        assert 'error_rate' in data
        assert 'active_strategies' in data
        assert 'pending_approvals' in data
        assert 'cost_today' in data
        assert 'cost_saved' in data
        assert 'timestamp' in data
        
        assert 60 <= data['cpu_usage'] <= 90
        assert 50 <= data['memory_usage'] <= 80
        assert isinstance(data['active_strategies'], int)
    
    def test_get_performance_history_default(self, client):
        """Test performance history with default parameters"""
        response = client.get('/api/dashboard/performance-history')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 12  # 6 hours * 2 data points per hour
        
        first_point = data[0]
        assert 'time' in first_point
        assert 'cpu' in first_point
        assert 'memory' in first_point
        assert 'response_time' in first_point
        assert 'timestamp' in first_point
    
    def test_get_performance_history_custom_hours(self, client):
        """Test performance history with custom hours parameter"""
        response = client.get('/api/dashboard/performance-history?hours=12')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 24  # 12 hours * 2 data points per hour
    
    def test_get_recent_decisions_default(self, client):
        """Test recent decisions with default limit"""
        response = client.get('/api/dashboard/recent-decisions')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        assert len(data) == 10  # default limit
        
        decision = data[0]
        assert 'id' in decision
        assert 'timestamp' in decision
        assert 'strategy' in decision
        assert 'status' in decision
        assert 'impact' in decision
        assert 'confidence' in decision
        assert decision['status'] in ['executed', 'pending', 'failed']
    
    def test_get_recent_decisions_custom_limit(self, client):
        """Test recent decisions with custom limit"""
        response = client.get('/api/dashboard/recent-decisions?limit=5')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert len(data) == 5
    
    def test_get_system_health_success(self, client):
        """Test system health endpoint"""
        response = client.get('/api/dashboard/system-health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'overall_status' in data
        assert 'components' in data
        assert 'last_check_time' in data
        
        components = data['components']
        assert 'ai_gateway' in components
        assert 'learning_system' in components
        assert 'decision_simulator' in components
        assert 'database' in components
        
        for component in components.values():
            assert 'status' in component
            assert 'last_check' in component
    
    def test_get_active_alerts_success(self, client):
        """Test active alerts endpoint"""
        response = client.get('/api/dashboard/alerts')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert isinstance(data, list)
        if data:
            alert = data[0]
            assert 'id' in alert
            assert 'type' in alert
            assert 'message' in alert
            assert 'severity' in alert
            assert 'timestamp' in alert
            assert 'acknowledged' in alert
            assert alert['severity'] in ['warning', 'error', 'critical']
    
    def test_get_cost_analysis_today(self, client):
        """Test cost analysis for today"""
        response = client.get('/api/dashboard/cost-analysis?period=today')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_cost' in data
        assert 'ai_service_cost' in data
        assert 'infrastructure_cost' in data
        assert 'storage_cost' in data
        assert 'savings' in data
        assert 'breakdown' in data
        
        breakdown = data['breakdown']
        assert isinstance(breakdown, list)
        assert len(breakdown) > 0
        
        for service in breakdown:
            assert 'service' in service
            assert 'cost' in service
    
    def test_get_cost_analysis_week(self, client):
        """Test cost analysis for week"""
        response = client.get('/api/dashboard/cost-analysis?period=week')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_cost' in data
        assert 'savings' in data
        assert data['total_cost'] > 100  # rough check
    
    def test_get_cost_analysis_month(self, client):
        """Test cost analysis for month"""
        response = client.get('/api/dashboard/cost-analysis?period=month')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_cost' in data
        assert 'savings' in data
        assert data['total_cost'] > 500  # rough check


class TestDashboardErrorHandling:
    """Test error handling in dashboard endpoints"""
    
    @patch('src.routes.dashboard.random.uniform')
    def test_get_system_metrics_error_handling(self, mock_random, client):
        """Test error handling in system metrics"""
        mock_random.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/metrics')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.dashboard.request')
    def test_get_performance_history_error_handling(self, mock_request, client):
        """Test error handling in performance history"""
        mock_request.args.get.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/performance-history')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.dashboard.random.choice')
    def test_get_recent_decisions_error_handling(self, mock_choice, client):
        """Test error handling in recent decisions"""
        mock_choice.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/recent-decisions')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.dashboard.datetime')
    def test_get_system_health_error_handling(self, mock_datetime, client):
        """Test error handling in system health"""
        mock_datetime.datetime.now.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/system-health')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.dashboard.random.choice')
    def test_get_active_alerts_error_handling(self, mock_choice, client):
        """Test error handling in active alerts"""
        mock_choice.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/alerts')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.dashboard.request')
    def test_get_cost_analysis_error_handling(self, mock_request, client):
        """Test error handling in cost analysis"""
        mock_request.args.get.side_effect = Exception('Test error')
        
        response = client.get('/api/dashboard/cost-analysis')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
