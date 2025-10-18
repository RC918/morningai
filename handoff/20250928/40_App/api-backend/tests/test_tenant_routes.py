"""
Unit tests for /api/tenant/* endpoints
Tests tenant information retrieval, member management, and role updates
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.routes.tenant import bp as tenant_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(tenant_bp)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    return {
        'user_id': '550e8400-e29b-41d4-a716-446655440000',
        'email': 'test@example.com'
    }


class TestTenantMe:
    """Tests for GET /api/tenant/me endpoint"""
    
    @patch('src.routes.tenant.get_client')
    def test_get_tenant_success(self, mock_get_client, client, mock_auth_user):
        """Test successful tenant info retrieval"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_user_profile_response = Mock()
        mock_user_profile_response.data = [{
            'tenant_id': 'tenant-123',
            'display_name': 'Test User',
            'role': 'member'
        }]
        
        mock_tenant_response = Mock()
        mock_tenant_response.data = [{
            'id': 'tenant-123',
            'name': 'Test Tenant',
            'created_at': '2025-01-01T00:00:00Z'
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_user_profile_response,
            mock_tenant_response
        ]
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            response = client.get('/api/tenant/me', headers={
                'Authorization': 'Bearer fake-token'
            })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['tenant_id'] == 'tenant-123'
        assert data['tenant_name'] == 'Test Tenant'
        assert data['user_role'] == 'member'
    
    @patch('src.routes.tenant.get_client')
    def test_get_tenant_no_user_profile(self, mock_get_client, client, mock_auth_user):
        """Test tenant retrieval when user has no profile"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            response = client.get('/api/tenant/me', headers={
                'Authorization': 'Bearer fake-token'
            })
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not assigned' in data['error']['message'].lower()


class TestTenantMembers:
    """Tests for GET /api/tenant/members endpoint"""
    
    @patch('src.routes.tenant.get_client')
    def test_list_members_success(self, mock_get_client, client, mock_auth_user):
        """Test successful member listing"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_user_profile = Mock()
        mock_user_profile.data = [{'tenant_id': 'tenant-123'}]
        
        mock_members = Mock()
        mock_members.data = [
            {
                'id': 'user-1',
                'display_name': 'Alice',
                'role': 'owner',
                'created_at': '2025-01-01T00:00:00Z'
            },
            {
                'id': 'user-2',
                'display_name': 'Bob',
                'role': 'member',
                'created_at': '2025-01-02T00:00:00Z'
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_user_profile,
            mock_members
        ]
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            response = client.get('/api/tenant/members', headers={
                'Authorization': 'Bearer fake-token'
            })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['members']) == 2
        assert data['members'][0]['display_name'] == 'Alice'
        assert data['members'][0]['role'] == 'owner'


class TestUpdateMemberRole:
    """Tests for PUT /api/tenant/members/<member_id> endpoint"""
    
    @patch('src.routes.tenant.get_client')
    def test_update_role_success_as_owner(self, mock_get_client, client, mock_auth_user):
        """Test successful role update by owner"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_current_user = Mock()
        mock_current_user.data = [{
            'tenant_id': 'tenant-123',
            'role': 'owner'
        }]
        
        mock_target_user = Mock()
        mock_target_user.data = [{
            'tenant_id': 'tenant-123',
            'role': 'member'
        }]
        
        mock_update = Mock()
        mock_update.data = [{'id': 'target-user-id', 'role': 'admin'}]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_current_user,
            mock_target_user
        ]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            mock_request.get_json.return_value = {'role': 'admin'}
            
            response = client.put('/api/tenant/members/target-user-id',
                                 json={'role': 'admin'},
                                 headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['role'] == 'admin'
    
    @patch('src.routes.tenant.get_client')
    def test_update_role_forbidden_as_member(self, mock_get_client, client, mock_auth_user):
        """Test role update fails for non-owner/admin"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_current_user = Mock()
        mock_current_user.data = [{
            'tenant_id': 'tenant-123',
            'role': 'member'
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_current_user
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            response = client.put('/api/tenant/members/target-user-id',
                                 json={'role': 'admin'},
                                 headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'permission' in data['error']['message'].lower()
    
    def test_update_role_invalid_role(self, client, mock_auth_user):
        """Test role update with invalid role"""
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            response = client.put('/api/tenant/members/target-user-id',
                                 json={'role': 'superadmin'},
                                 headers={'Authorization': 'Bearer fake-token'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'valid_roles' in data['error']


class TestTenantInfo:
    """Tests for GET /api/tenant/info endpoint"""
    
    @patch('src.routes.tenant.get_client')
    def test_get_tenant_info_success(self, mock_get_client, client, mock_auth_user):
        """Test successful tenant statistics retrieval"""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        mock_user_profile = Mock()
        mock_user_profile.data = [{'tenant_id': 'tenant-123'}]
        
        mock_tenant = Mock()
        mock_tenant.data = [{
            'id': 'tenant-123',
            'name': 'Test Org',
            'created_at': '2025-01-01T00:00:00Z'
        }]
        
        mock_members_count = Mock()
        mock_members_count.count = 5
        
        mock_tasks_count = Mock()
        mock_tasks_count.count = 42
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_user_profile,
            mock_tenant
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 5
        
        with patch('flask.request') as mock_request:
            mock_request.user_id = mock_auth_user['user_id']
            
            with patch.object(mock_supabase.table.return_value.select.return_value.eq.return_value, 'execute') as mock_exec:
                mock_exec.side_effect = [
                    mock_user_profile,
                    mock_tenant,
                    mock_members_count,
                    mock_tasks_count
                ]
                
                response = client.get('/api/tenant/info', headers={
                    'Authorization': 'Bearer fake-token'
                })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tenant_id' in data
        assert 'member_count' in data or 'task_count' in data
