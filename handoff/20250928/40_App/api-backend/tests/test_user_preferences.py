import pytest
import json
from src.main import app, db
from src.models.user_preferences import UserPreferences


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


class TestUserPreferencesEndpoint:
    """Test suite for /api/user/preferences endpoint"""
    
    def test_get_preferences_creates_default(self, client):
        """Test GET /api/user/preferences creates default preferences"""
        response = client.get('/api/user/preferences?user_id=test_user')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'test_user'
        assert data['show_welcome_modal'] == True
        assert data['theme'] == 'light'
        assert data['language'] == 'zh-TW'
        assert data['email_notifications'] == True
        assert data['push_notifications'] == True
    
    def test_get_preferences_anonymous_default(self, client):
        """Test GET /api/user/preferences without user_id defaults to anonymous"""
        response = client.get('/api/user/preferences')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'anonymous'
    
    def test_update_preferences(self, client):
        """Test PUT /api/user/preferences updates preferences"""
        client.get('/api/user/preferences?user_id=test_user')
        
        update_data = {
            'user_id': 'test_user',
            'show_welcome_modal': False,
            'theme': 'dark',
            'language': 'en-US',
            'email_notifications': False
        }
        
        response = client.put(
            '/api/user/preferences',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['show_welcome_modal'] == False
        assert data['theme'] == 'dark'
        assert data['language'] == 'en-US'
        assert data['email_notifications'] == False
        assert data['welcome_modal_completed_at'] is not None
    
    def test_update_preferences_creates_if_not_exists(self, client):
        """Test PUT /api/user/preferences creates preferences if they don't exist"""
        update_data = {
            'user_id': 'new_user',
            'theme': 'dark'
        }
        
        response = client.put(
            '/api/user/preferences',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == 'new_user'
        assert data['theme'] == 'dark'
    
    def test_update_preferences_with_dashboard_layout(self, client):
        """Test PUT /api/user/preferences with dashboard_layout"""
        layout = {
            'widgets': [
                {'id': 'widget1', 'position': {'x': 0, 'y': 0}},
                {'id': 'widget2', 'position': {'x': 1, 'y': 0}}
            ]
        }
        
        update_data = {
            'user_id': 'test_user',
            'dashboard_layout': layout
        }
        
        response = client.put(
            '/api/user/preferences',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['dashboard_layout'] == layout
    
    def test_update_preferences_invalid_request(self, client):
        """Test PUT /api/user/preferences with invalid request"""
        response = client.put(
            '/api/user/preferences',
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_preferences(self, client):
        """Test DELETE /api/user/preferences"""
        client.get('/api/user/preferences?user_id=test_user')
        
        response = client.delete('/api/user/preferences?user_id=test_user')
        
        assert response.status_code == 204
        
        response = client.get('/api/user/preferences?user_id=test_user')
        data = json.loads(response.data)
        assert data['show_welcome_modal'] == True  # Back to default
    
    def test_delete_preferences_not_found(self, client):
        """Test DELETE /api/user/preferences for non-existent user"""
        response = client.delete('/api/user/preferences?user_id=nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_preferences_missing_user_id(self, client):
        """Test DELETE /api/user/preferences without user_id"""
        response = client.delete('/api/user/preferences')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_patch_preferences(self, client):
        """Test PATCH /api/user/preferences (should work same as PUT)"""
        update_data = {
            'user_id': 'test_user',
            'theme': 'dark'
        }
        
        response = client.patch(
            '/api/user/preferences',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['theme'] == 'dark'
    
    def test_preferences_persistence(self, client):
        """Test that preferences persist across requests"""
        update_data = {
            'user_id': 'persistent_user',
            'theme': 'dark',
            'show_welcome_modal': False
        }
        
        client.put(
            '/api/user/preferences',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        response = client.get('/api/user/preferences?user_id=persistent_user')
        data = json.loads(response.data)
        
        assert data['theme'] == 'dark'
        assert data['show_welcome_modal'] == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
