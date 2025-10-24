"""
Test FAQ API authorization
Tests JWT authentication and role-based access control
"""
import pytest
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
api_backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'handoff', '20250928', '40_App', 'api-backend')
sys.path.insert(0, os.path.join(api_backend_path, 'src'))
sys.path.insert(0, api_backend_path)

@pytest.fixture
def app():
    """Create test Flask app"""
    from flask import Flask
    from routes.faq import bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(bp)
    
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def admin_token():
    """Create admin JWT token"""
    from middleware.auth_middleware import create_admin_token
    return create_admin_token()

@pytest.fixture
def user_token():
    """Create user JWT token"""
    from middleware.auth_middleware import create_user_token
    return create_user_token()

def test_search_requires_jwt(client):
    """Test that search endpoint requires JWT authentication"""
    response = client.get('/api/faq/search?q=test')
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
    assert 'Authorization' in data['error'] or 'authorization' in data['error'].lower()

def test_search_with_invalid_jwt(client):
    """Test that search endpoint rejects invalid JWT"""
    response = client.get(
        '/api/faq/search?q=test',
        headers={'Authorization': 'Bearer invalid-token'}
    )
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data

@pytest.mark.asyncio
async def test_search_with_valid_jwt(client, user_token):
    """Test that search works with valid user JWT"""
    with patch('agents.faq_agent.tools.faq_search_tool.FAQSearchTool.search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {
            'success': True,
            'results': [],
            'count': 0
        }
        
        response = client.get(
            '/api/faq/search?q=test',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        
        assert response.status_code == 200

def test_get_faq_requires_jwt(client):
    """Test that get FAQ endpoint requires JWT"""
    response = client.get('/api/faq/test-id')
    
    assert response.status_code == 401

def test_categories_requires_jwt(client):
    """Test that categories endpoint requires JWT"""
    response = client.get('/api/faq/categories')
    
    assert response.status_code == 401

def test_stats_requires_jwt(client):
    """Test that stats endpoint requires JWT"""
    response = client.get('/api/faq/stats')
    
    assert response.status_code == 401

def test_create_requires_admin(client, user_token):
    """Test that create FAQ requires admin role"""
    response = client.post(
        '/api/faq',
        json={'question': 'Q', 'answer': 'A'},
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'admin' in data['error'].lower() or 'privileges' in data['error'].lower()

def test_update_requires_admin(client, user_token):
    """Test that update FAQ requires admin role"""
    response = client.put(
        '/api/faq/test-id',
        json={'answer': 'New A'},
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 403

def test_delete_requires_admin(client, user_token):
    """Test that delete FAQ requires admin role"""
    response = client.delete(
        '/api/faq/test-id',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_with_admin_token(client, admin_token):
    """Test that admin can create FAQ"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.create_faq', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'success': True,
            'faq': {'id': 'new-id', 'question': 'Q', 'answer': 'A'}
        }
        
        response = client.post(
            '/api/faq',
            json={'question': 'Q', 'answer': 'A'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 201

@pytest.mark.asyncio
async def test_update_with_admin_token(client, admin_token):
    """Test that admin can update FAQ"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.update_faq', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {'success': True}
        
        response = client.put(
            '/api/faq/test-id',
            json={'answer': 'New A'},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_with_admin_token(client, admin_token):
    """Test that admin can delete FAQ"""
    with patch('agents.faq_agent.tools.faq_management_tool.FAQManagementTool.delete_faq', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = {'success': True}
        
        response = client.delete(
            '/api/faq/test-id',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
