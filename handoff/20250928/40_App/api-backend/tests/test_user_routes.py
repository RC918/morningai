"""
Comprehensive tests for user routes
Focus on improving routes/user.py coverage from 41% to 70%+
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    app.config['TESTING'] = True
    return app.test_client()


class TestUserRoutes:
    """Test user CRUD endpoints"""
    
    @patch('src.routes.user.User')
    def test_get_users_success(self, mock_user_class, client):
        """Test successful retrieval of all users"""
        mock_user1 = MagicMock()
        mock_user1.to_dict.return_value = {
            'id': 1,
            'username': 'user1',
            'email': 'user1@example.com'
        }
        mock_user2 = MagicMock()
        mock_user2.to_dict.return_value = {
            'id': 2,
            'username': 'user2',
            'email': 'user2@example.com'
        }
        
        mock_user_class.query.all.return_value = [mock_user1, mock_user2]
        
        response = client.get('/api/users')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['username'] == 'user1'
        assert data[1]['username'] == 'user2'
    
    @patch('src.routes.user.User')
    def test_get_users_empty_list(self, mock_user_class, client):
        """Test retrieval when no users exist"""
        mock_user_class.query.all.return_value = []
        
        response = client.get('/api/users')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @patch('src.routes.user.db')
    @patch('src.routes.user.User')
    def test_create_user_success(self, mock_user_class, mock_db, client):
        """Test successful user creation"""
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'id': 1,
            'username': 'newuser',
            'email': 'newuser@example.com'
        }
        mock_user_class.return_value = mock_user
        
        response = client.post('/api/users', json={
            'username': 'newuser',
            'email': 'newuser@example.com'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['username'] == 'newuser'
        assert data['email'] == 'newuser@example.com'
        
        mock_db.session.add.assert_called_once_with(mock_user)
        mock_db.session.commit.assert_called_once()
    
    @patch('src.routes.user.User')
    def test_get_user_success(self, mock_user_class, client):
        """Test successful retrieval of a single user"""
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        mock_user_class.query.get_or_404.return_value = mock_user
        
        response = client.get('/api/users/1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 1
        assert data['username'] == 'testuser'
        
        mock_user_class.query.get_or_404.assert_called_once_with(1)
    
    @patch('src.routes.user.User')
    def test_get_user_not_found(self, mock_user_class, client):
        """Test retrieval of non-existent user"""
        from werkzeug.exceptions import NotFound
        mock_user_class.query.get_or_404.side_effect = NotFound()
        
        response = client.get('/api/users/999')
        
        assert response.status_code == 404
    
    @patch('src.routes.user.db')
    @patch('src.routes.user.User')
    def test_update_user_success(self, mock_user_class, mock_db, client):
        """Test successful user update"""
        mock_user = MagicMock()
        mock_user.username = 'oldusername'
        mock_user.email = 'old@example.com'
        mock_user.to_dict.return_value = {
            'id': 1,
            'username': 'newusername',
            'email': 'new@example.com'
        }
        mock_user_class.query.get_or_404.return_value = mock_user
        
        response = client.put('/api/users/1', json={
            'username': 'newusername',
            'email': 'new@example.com'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'newusername'
        assert data['email'] == 'new@example.com'
        
        mock_db.session.commit.assert_called_once()
        mock_user_class.query.get_or_404.assert_called_once_with(1)
    
    @patch('src.routes.user.db')
    @patch('src.routes.user.User')
    def test_update_user_partial(self, mock_user_class, mock_db, client):
        """Test partial user update (only username)"""
        mock_user = MagicMock()
        mock_user.username = 'oldusername'
        mock_user.email = 'test@example.com'
        mock_user.to_dict.return_value = {
            'id': 1,
            'username': 'newusername',
            'email': 'test@example.com'
        }
        mock_user_class.query.get_or_404.return_value = mock_user
        
        response = client.put('/api/users/1', json={
            'username': 'newusername'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'newusername'
        
        assert mock_user.email == 'test@example.com'
    
    @patch('src.routes.user.User')
    def test_update_user_not_found(self, mock_user_class, client):
        """Test update of non-existent user"""
        from werkzeug.exceptions import NotFound
        mock_user_class.query.get_or_404.side_effect = NotFound()
        
        response = client.put('/api/users/999', json={
            'username': 'newusername'
        })
        
        assert response.status_code == 404
    
    @patch('src.routes.user.db')
    @patch('src.routes.user.User')
    def test_delete_user_success(self, mock_user_class, mock_db, client):
        """Test successful user deletion"""
        mock_user = MagicMock()
        mock_user_class.query.get_or_404.return_value = mock_user
        
        response = client.delete('/api/users/1')
        
        assert response.status_code == 204
        assert response.data == b''
        
        mock_db.session.delete.assert_called_once_with(mock_user)
        mock_db.session.commit.assert_called_once()
        mock_user_class.query.get_or_404.assert_called_once_with(1)
    
    @patch('src.routes.user.User')
    def test_delete_user_not_found(self, mock_user_class, client):
        """Test deletion of non-existent user"""
        from werkzeug.exceptions import NotFound
        mock_user_class.query.get_or_404.side_effect = NotFound()
        
        response = client.delete('/api/users/999')
        
        assert response.status_code == 404
