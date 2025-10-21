import pytest
from flask import Flask
from src.routes.dashboard import dashboard_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_get_system_metrics(client):
    """Test GET /api/dashboard/metrics"""
    response = client.get('/api/dashboard/metrics')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'cpu_usage' in data
    assert 'memory_usage' in data
    assert 'response_time' in data
    assert 'error_rate' in data
    assert 'timestamp' in data


def test_get_performance_history_default(client):
    """Test GET /api/dashboard/performance-history with default hours"""
    response = client.get('/api/dashboard/performance-history')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 12


def test_get_performance_history_custom_hours(client):
    """Test GET /api/dashboard/performance-history with custom hours"""
    response = client.get('/api/dashboard/performance-history?hours=3')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 6


def test_get_recent_decisions_default(client):
    """Test GET /api/dashboard/recent-decisions with default limit"""
    response = client.get('/api/dashboard/recent-decisions')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 10


def test_get_recent_decisions_custom_limit(client):
    """Test GET /api/dashboard/recent-decisions with custom limit"""
    response = client.get('/api/dashboard/recent-decisions?limit=5')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 5


def test_get_system_health(client):
    """Test GET /api/dashboard/system-health"""
    response = client.get('/api/dashboard/system-health')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'overall_status' in data
    assert 'components' in data
    assert 'last_check_time' in data


def test_get_active_alerts(client):
    """Test GET /api/dashboard/alerts"""
    response = client.get('/api/dashboard/alerts')
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_get_cost_analysis_today(client):
    """Test GET /api/dashboard/cost-analysis with period=today"""
    response = client.get('/api/dashboard/cost-analysis?period=today')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_cost' in data
    assert 'ai_service_cost' in data
    assert 'breakdown' in data


def test_get_cost_analysis_week(client):
    """Test GET /api/dashboard/cost-analysis with period=week"""
    response = client.get('/api/dashboard/cost-analysis?period=week')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_cost' in data
    assert 'ai_service_cost' in data


def test_get_cost_analysis_month(client):
    """Test GET /api/dashboard/cost-analysis with period=month"""
    response = client.get('/api/dashboard/cost-analysis?period=month')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_cost' in data
