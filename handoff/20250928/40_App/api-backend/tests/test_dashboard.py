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


def test_get_dashboard_layout(client):
    """Test GET /api/dashboard/layouts"""
    response = client.get('/api/dashboard/layouts?user_id=test_user')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_id' in data
    assert 'widgets' in data
    assert 'updated_at' in data
    assert isinstance(data['widgets'], list)


def test_save_dashboard_layout(client):
    """Test POST /api/dashboard/layouts"""
    layout_data = {
        'user_id': 'test_user',
        'layout': {
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}}
            ]
        }
    }
    response = client.post('/api/dashboard/layouts', json=layout_data)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'user_id' in data
    assert 'updated_at' in data


def test_get_available_widgets(client):
    """Test GET /api/dashboard/widgets"""
    response = client.get('/api/dashboard/widgets')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'widgets' in data
    assert isinstance(data['widgets'], list)
    assert len(data['widgets']) > 0
    
    widget = data['widgets'][0]
    assert 'id' in widget
    assert 'name' in widget
    assert 'description' in widget
    assert 'category' in widget
    assert 'icon' in widget
    assert 'size' in widget


def test_get_dashboard_data(client):
    """Test GET /api/dashboard/data"""
    response = client.get('/api/dashboard/data')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'metrics' in data
    assert 'timestamp' in data
    assert 'cpu_usage' in data['metrics']
    assert 'memory_usage' in data['metrics']
    assert 'response_time' in data['metrics']
