import pytest
from flask import Flask
from src.routes.billing import bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_get_plans(client):
    """Test GET /api/billing/plans returns plan list"""
    response = client.get('/api/billing/plans')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'plans' in data
    assert len(data['plans']) == 3
    
    plan_ids = [p['id'] for p in data['plans']]
    assert 'starter' in plan_ids
    assert 'pro' in plan_ids
    assert 'enterprise' in plan_ids


def test_checkout_session_default_plan(client):
    """Test POST /api/billing/checkout/session with default plan"""
    response = client.post('/api/billing/checkout/session', json={})
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'session_id' in data
    assert data['plan_id'] == 'starter'
    assert data['status'] == 'created'
    assert 'redirect_url' in data


def test_checkout_session_with_plan(client):
    """Test POST /api/billing/checkout/session with specific plan"""
    response = client.post('/api/billing/checkout/session', json={'plan_id': 'pro'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['plan_id'] == 'pro'
    assert 'session_id' in data


def test_checkout_session_no_json(client):
    """Test POST /api/billing/checkout/session without JSON body"""
    response = client.post('/api/billing/checkout/session')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['plan_id'] == 'starter'
