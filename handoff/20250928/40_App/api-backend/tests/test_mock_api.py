import pytest
from flask import Flask
from src.routes.mock_api import mock_api


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(mock_api)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_dashboard_mock_get(client):
    """Test GET /api/dashboard/mock"""
    response = client.get('/api/dashboard/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'widgets' in data
    assert 'recent_decisions' in data
    assert 'system_metrics' in data
    assert 'timestamp' in data


def test_checkout_mock_get(client):
    """Test GET /api/checkout/mock"""
    response = client.get('/api/checkout/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'payment_methods' in data
    assert 'pricing_tiers' in data
    assert 'discounts' in data


def test_checkout_mock_post(client):
    """Test POST /api/checkout/mock"""
    response = client.post('/api/checkout/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'checkout_session' in data
    assert data['success'] is True
    assert 'message' in data


def test_settings_mock_get(client):
    """Test GET /api/settings/mock"""
    response = client.get('/api/settings/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_preferences' in data
    assert 'system_config' in data
    assert 'security_settings' in data
    assert 'integration_settings' in data
    assert 'billing_info' in data


def test_settings_mock_post(client):
    """Test POST /api/settings/mock"""
    settings_data = {
        'theme': 'dark',
        'language': 'en-US'
    }
    response = client.post('/api/settings/mock', json=settings_data)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'message' in data
    assert 'updated_settings' in data
    assert data['updated_settings'] == settings_data


def test_settings_mock_post_no_json(client):
    """Test POST /api/settings/mock without JSON body"""
    response = client.post('/api/settings/mock', 
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_phase9_stripe_mock(client):
    """Test GET /api/phase9/stripe/mock"""
    response = client.get('/api/phase9/stripe/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'stripe_config' in data
    assert 'subscription_flows' in data
    assert 'refund_policies' in data


def test_phase9_tappay_mock(client):
    """Test GET /api/phase9/tappay/mock"""
    response = client.get('/api/phase9/tappay/mock')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'tappay_config' in data
    assert 'payment_flows' in data
    assert 'localization' in data
