"""Tests for user routes production (Supabase) code paths"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.main import app
from src.middleware.auth_middleware import create_admin_token, create_user_token, generate_jwt_token


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_token():
    """Create admin JWT token"""
    return create_admin_token()


@pytest.fixture
def user_token():
    """Create regular user JWT token"""
    user_data = {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'username': 'testuser',
        'role': 'user'
    }
    return generate_jwt_token(user_data)


class TestUserProfileProduction:
    """Test user profile endpoint in production mode"""
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_profile_production_success(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get profile in production with Supabase"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'display_name': 'Test User',
            'role': 'user',
            'created_at': '2025-01-01T00:00:00Z'
        }
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/profile',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == '550e8400-e29b-41d4-a716-446655440000'
        assert data['display_name'] == 'Test User'
        
        mock_client.table.assert_called_once_with('user_profiles')
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_profile_production_not_found(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get profile when user not found in production"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/profile',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_profile_production_error(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get profile with database error in production"""
        mock_is_prod.return_value = True
        mock_get_client.side_effect = Exception('Database connection failed')
        
        response = client.get(
            '/api/user/profile',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


class TestUserPreferencesProduction:
    """Test user preferences endpoints in production mode"""
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_preferences_production_success(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get preferences in production"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {
            'preferences': '{"theme": "dark", "language": "en"}'
        }
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['theme'] == 'dark'
        assert data['language'] == 'en'
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_preferences_production_empty(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get preferences with empty preferences"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {'preferences': '{}'}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {}
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_preferences_production_null(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get preferences with null preferences"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {'preferences': None}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {}
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_preferences_production_invalid_json(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get preferences with invalid JSON"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {'preferences': 'invalid json {'}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {}
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_get_preferences_production_user_not_found(self, mock_get_client, mock_is_prod, client, user_token):
        """Test get preferences when user not found"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.get(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_update_preferences_production_success(self, mock_get_client, mock_is_prod, client, user_token):
        """Test update preferences in production"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        
        mock_select_response = Mock()
        mock_select_response.data = {'preferences': '{"theme": "light"}'}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_select_response
        
        mock_update_response = Mock()
        mock_update_response.data = {'preferences': '{"theme": "dark", "language": "en"}'}
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        mock_get_client.return_value = mock_client
        
        response = client.post(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'language': 'en', 'theme': 'dark'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['theme'] == 'dark'
        assert data['language'] == 'en'
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_update_preferences_production_incremental(self, mock_get_client, mock_is_prod, client, user_token):
        """Test incremental update of preferences"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        
        mock_select_response = Mock()
        mock_select_response.data = {
            'preferences': '{"theme": "dark", "language": "en", "notifications": true}'
        }
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_select_response
        
        mock_update_response = Mock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        mock_get_client.return_value = mock_client
        
        response = client.post(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'language': 'zh-TW'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['theme'] == 'dark'
        assert data['language'] == 'zh-TW'
        assert data['notifications'] is True
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_update_preferences_production_empty_payload(self, mock_get_client, mock_is_prod, client, user_token):
        """Test update with empty payload"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_select_response = Mock()
        mock_select_response.data = {'preferences': '{"theme": "dark"}'}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_select_response
        
        mock_update_response = Mock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        mock_get_client.return_value = mock_client
        
        response = client.post(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'},
            json={}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['theme'] == 'dark'
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_update_preferences_production_user_not_found(self, mock_get_client, mock_is_prod, client, user_token):
        """Test update when user not found"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = client.post(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'theme': 'dark'}
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.routes.user.is_production')
    @patch('src.routes.user.get_supabase_client')
    def test_update_preferences_production_complex_data(self, mock_get_client, mock_is_prod, client, user_token):
        """Test update with complex nested data"""
        mock_is_prod.return_value = True
        
        mock_client = Mock()
        mock_select_response = Mock()
        mock_select_response.data = {'preferences': '{}'}
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_select_response
        
        mock_update_response = Mock()
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        mock_get_client.return_value = mock_client
        
        complex_prefs = {
            'ui': {
                'theme': 'dark',
                'sidebar': {'collapsed': True, 'width': 250}
            },
            'notifications': {
                'email': True,
                'push': False,
                'frequency': 'daily'
            }
        }
        
        response = client.post(
            '/api/user/preferences',
            headers={'Authorization': f'Bearer {user_token}'},
            json=complex_prefs
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'ui' in data
        assert 'notifications' in data
        assert data['ui']['theme'] == 'dark'


