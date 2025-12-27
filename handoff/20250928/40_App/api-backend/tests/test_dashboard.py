import pytest
from flask import Flask
from src.routes.dashboard import dashboard_bp
from src.middleware.auth_middleware import create_user_token


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


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token"""
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


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


def test_get_dashboard_layout(client, auth_headers):
    """Test GET /api/dashboard/layouts"""
    response = client.get('/api/dashboard/layouts', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_id' in data
    assert 'widgets' in data
    assert 'updated_at' in data
    assert isinstance(data['widgets'], list)


def test_get_dashboard_layout_no_auth(client):
    """Test GET /api/dashboard/layouts without authentication"""
    response = client.get('/api/dashboard/layouts')
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_save_dashboard_layout(client, auth_headers):
    """Test POST /api/dashboard/layouts"""
    layout_data = {
        'layout': {
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}}
            ]
        }
    }
    response = client.post('/api/dashboard/layouts', json=layout_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'user_id' in data
    assert 'updated_at' in data


def test_save_dashboard_layout_no_auth(client):
    """Test POST /api/dashboard/layouts without authentication"""
    layout_data = {
        'layout': {
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}}
            ]
        }
    }
    response = client.post('/api/dashboard/layouts', json=layout_data)
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_get_available_widgets(client, auth_headers):
    """Test GET /api/dashboard/widgets"""
    response = client.get('/api/dashboard/widgets', headers=auth_headers)
    
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


def test_get_available_widgets_no_auth(client):
    """Test GET /api/dashboard/widgets without authentication"""
    response = client.get('/api/dashboard/widgets')
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


# Track C MVP: Redis/Fallback path tests
def test_metrics_has_source_header(client):
    """Test GET /api/dashboard/metrics returns X-MorningAI-Metrics-Source header"""
    response = client.get('/api/dashboard/metrics')

    assert response.status_code == 200
    assert 'X-MorningAI-Metrics-Source' in response.headers
    source = response.headers['X-MorningAI-Metrics-Source']
    assert source in ['redis', 'fallback']


def test_metrics_fallback_returns_valid_schema(client, monkeypatch):
    """Test /metrics returns valid schema when Redis unavailable (fallback path)"""
    import src.utils.redis_client as redis_client_mod
    monkeypatch.setattr(redis_client_mod, 'get_redis_client', lambda: None)

    response = client.get('/api/dashboard/metrics')

    assert response.status_code == 200
    assert response.headers.get('X-MorningAI-Metrics-Source') == 'fallback'

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

    assert isinstance(data['cpu_usage'], (int, float))
    assert isinstance(data['memory_usage'], (int, float))
    assert isinstance(data['response_time'], (int, float))
    assert isinstance(data['error_rate'], (int, float))
