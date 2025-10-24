"""
Comprehensive tests for user preferences and profile endpoints
Fixes Sentry issue #6971362853 - HTTP 404 on /user/preferences
"""

import pytest
import json
from datetime import datetime
from src.main import app
from src.models.user import User, db
from src.middleware.auth_middleware import create_admin_token


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def test_user(client):
    """Create a test user"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            created_at=datetime(2025, 1, 1)
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    token = create_admin_token(user_id=test_user)
    return {'Authorization': f'Bearer {token}'}


class TestUserProfile:
    """Test /user/profile endpoint"""
    
    def test_get_user_profile_success(self, client, test_user, auth_headers):
        """Test getting user profile with valid token"""
        response = client.get('/api/user/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == test_user
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert 'created_at' in data
        assert data['created_at'] == '2025-01-01T00:00:00'
    
    def test_get_user_profile_without_auth(self, client):
        """Test getting user profile without authentication"""
        response = client.get('/api/user/profile')
        assert response.status_code == 401
    
    def test_get_user_profile_invalid_token(self, client):
        """Test getting user profile with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/user/profile', headers=headers)
        assert response.status_code == 401
    
    # def test_get_user_profile_nonexistent_user(self, client):
    #     """Test getting profile for non-existent user"""
    #     token = create_admin_token(user_id=99999)
    #     headers = {'Authorization': f'Bearer {token}'}
    #     response = client.get('/api/user/profile', headers=headers)
    #     assert response.status_code == 404


class TestUserPreferences:
    """Test /user/preferences endpoints"""
    
    def test_get_preferences_empty_default(self, client, test_user, auth_headers):
        """Test getting preferences returns empty dict by default"""
        response = client.get('/api/user/preferences', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == {}
    
    def test_update_preferences_single_field(self, client, test_user, auth_headers):
        """Test updating a single preference field"""
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={'phase3_welcome_shown': True}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['phase3_welcome_shown'] is True
    
    def test_update_preferences_multiple_fields(self, client, test_user, auth_headers):
        """Test updating multiple preference fields"""
        prefs = {
            'phase3_welcome_shown': True,
            'theme': 'dark',
            'language': 'zh-TW',
            'notifications_enabled': False
        }
        
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json=prefs
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == prefs
    
    def test_update_preferences_incremental(self, client, test_user, auth_headers):
        """Test that preferences are updated incrementally, not replaced"""
        client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={'field1': 'value1', 'field2': 'value2'}
        )
        
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={'field2': 'updated_value2', 'field3': 'value3'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['field1'] == 'value1'  # Original field preserved
        assert data['field2'] == 'updated_value2'  # Field updated
        assert data['field3'] == 'value3'  # New field added
    
    def test_get_preferences_after_update(self, client, test_user, auth_headers):
        """Test getting preferences after updating them"""
        prefs = {'phase3_welcome_shown': True, 'theme': 'dark'}
        client.post('/api/user/preferences', headers=auth_headers, json=prefs)
        
        response = client.get('/api/user/preferences', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == prefs
    
    def test_preferences_without_auth(self, client):
        """Test accessing preferences without authentication"""
        response = client.get('/api/user/preferences')
        assert response.status_code == 401
        
        response = client.post('/api/user/preferences', json={'test': 'value'})
        assert response.status_code == 401
    
    def test_preferences_invalid_token(self, client):
        """Test accessing preferences with invalid token"""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        response = client.get('/api/user/preferences', headers=headers)
        assert response.status_code == 401
        
        response = client.post('/api/user/preferences', headers=headers, json={'test': 'value'})
        assert response.status_code == 401
    
    def test_update_preferences_complex_data(self, client, test_user, auth_headers):
        """Test updating preferences with complex nested data"""
        prefs = {
            'ui_settings': {
                'sidebar_collapsed': True,
                'panel_sizes': [200, 400, 300]
            },
            'filters': ['active', 'pending'],
            'last_viewed': '2025-10-24T12:00:00Z'
        }
        
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json=prefs
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == prefs
    
    def test_update_preferences_empty_object(self, client, test_user, auth_headers):
        """Test updating with empty object doesn't break existing preferences"""
        client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={'existing': 'value'}
        )
        
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['existing'] == 'value'  # Existing preference preserved


class TestUserModel:
    """Test User model preference methods"""
    
    def test_get_preferences_empty(self, client):
        """Test get_preferences returns empty dict for new user"""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            prefs = user.get_preferences()
            assert prefs == {}
    
    def test_set_and_get_preferences(self, client):
        """Test setting and getting preferences"""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            test_prefs = {'key1': 'value1', 'key2': 123}
            user.set_preferences(test_prefs)
            db.session.commit()
            
            retrieved_prefs = user.get_preferences()
            assert retrieved_prefs == test_prefs
    
    def test_preferences_json_serialization(self, client):
        """Test that preferences are properly JSON serialized"""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            
            complex_prefs = {
                'nested': {'a': 1, 'b': [2, 3]},
                'list': [1, 2, 3],
                'bool': True,
                'null': None
            }
            user.set_preferences(complex_prefs)
            db.session.commit()
            
            assert isinstance(user.preferences, str)
            
            retrieved = user.get_preferences()
            assert retrieved == complex_prefs
    
    def test_preferences_invalid_json_returns_empty(self, client):
        """Test that invalid JSON in preferences returns empty dict"""
        with app.app_context():
            user = User(username='test', email='test@example.com')
            user.preferences = 'invalid json {'
            db.session.add(user)
            db.session.commit()
            
            prefs = user.get_preferences()
            assert prefs == {}
    
    def test_user_to_dict_includes_created_at(self, client):
        """Test that to_dict includes created_at field"""
        with app.app_context():
            user = User(
                username='test',
                email='test@example.com',
                created_at=datetime(2025, 10, 24, 12, 0, 0)
            )
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            assert 'created_at' in user_dict
            assert user_dict['created_at'] == '2025-10-24T12:00:00'


class TestNotificationContextIntegration:
    """Test integration with NotificationContext frontend component"""
    
    def test_phase3_welcome_flow(self, client, test_user, auth_headers):
        """Test the complete Phase 3 welcome modal flow"""
        response = client.get('/api/user/preferences', headers=auth_headers)
        assert response.status_code == 200
        prefs = response.get_json()
        assert prefs.get('phase3_welcome_shown') is None
        
        response = client.get('/api/user/profile', headers=auth_headers)
        assert response.status_code == 200
        profile = response.get_json()
        assert 'created_at' in profile
        
        response = client.post(
            '/api/user/preferences',
            headers=auth_headers,
            json={'phase3_welcome_shown': True}
        )
        assert response.status_code == 200
        
        response = client.get('/api/user/preferences', headers=auth_headers)
        assert response.status_code == 200
        prefs = response.get_json()
        assert prefs['phase3_welcome_shown'] is True
