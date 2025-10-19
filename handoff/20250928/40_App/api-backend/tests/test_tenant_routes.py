"""
Tests for tenant.py routes to improve coverage from 21% to 40%+
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client"""
    from src.main import app
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token"""
    return "Bearer test_token_12345"


class TestGetCurrentUserTenant:
    """Test /api/tenant/me endpoint"""
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_current_tenant_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful tenant retrieval"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = {
            'tenant_id': 'tenant123',
            'tenants': {
                'id': 'tenant123',
                'name': 'Test Tenant',
                'created_at': '2024-01-01T00:00:00Z'
            }
        }
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        response = client.get('/api/tenant/me', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['tenant_id'] == 'tenant123'
        assert data['tenant_name'] == 'Test Tenant'
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_current_tenant_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test when user profile is not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = None
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        response = client.get('/api/tenant/me', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_current_tenant_no_tenant_data(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test when tenant data is missing"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = {'tenant_id': 'tenant123', 'tenants': None}
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response
        
        response = client.get('/api/tenant/me', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_current_tenant_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test server error handling"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_get_client.side_effect = Exception("Database error")
        
        response = client.get('/api/tenant/me', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 500


class TestGetTenantMembers:
    """Test /api/tenant/members endpoint"""
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful members retrieval"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}
        
        mock_members_response = MagicMock()
        mock_members_response.data = [
            {'id': 'user1', 'display_name': 'User 1', 'role': 'admin', 'created_at': '2024-01-01'},
            {'id': 'user2', 'display_name': 'User 2', 'role': 'member', 'created_at': '2024-01-02'}
        ]
        
        mock_count_response = MagicMock()
        mock_count_response.count = 2
        
        mock_auth_user = MagicMock()
        mock_auth_user.user.email = 'test@example.com'
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response
        mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.execute.return_value = mock_members_response
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_client.auth.admin.get_user_by_id.return_value = mock_auth_user
        
        response = client.get('/api/tenant/members', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'members' in data
        assert data['total'] == 2
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_with_pagination(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test members retrieval with pagination"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}
        
        mock_members_response = MagicMock()
        mock_members_response.data = []
        
        mock_count_response = MagicMock()
        mock_count_response.count = 0
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response
        mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.execute.return_value = mock_members_response
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        response = client.get('/api/tenant/members?limit=10&offset=5', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 10
        assert data['offset'] == 5
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_invalid_limit(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test invalid limit parameter"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        response = client.get('/api/tenant/members?limit=invalid', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 400


class TestUpdateMemberRole:
    """Test /api/tenant/members/<member_id> endpoint"""
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful role update"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_current_user = MagicMock()
        mock_current_user.data = {'tenant_id': 'tenant123', 'role': 'admin'}
        
        mock_member = MagicMock()
        mock_member.data = {'tenant_id': 'tenant123', 'role': 'member'}
        
        mock_update = MagicMock()
        mock_update.data = {'id': 'member456', 'role': 'viewer'}
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_current_user, mock_member
        ]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update
        
        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'viewer'},
            headers={'Authorization': mock_jwt_token}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['member_id'] == 'member456'
        assert data['new_role'] == 'viewer'
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_invalid_role(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update with invalid role"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'superuser'},
            headers={'Authorization': mock_jwt_token}
        )
        
        assert response.status_code == 400
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_insufficient_permissions(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update with insufficient permissions"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_current_user = MagicMock()
        mock_current_user.data = {'tenant_id': 'tenant123', 'role': 'member'}
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_current_user
        
        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'admin'},
            headers={'Authorization': mock_jwt_token}
        )
        
        assert response.status_code == 403
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_member_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update when member not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_current_user = MagicMock()
        mock_current_user.data = {'tenant_id': 'tenant123', 'role': 'admin'}
        
        mock_member = MagicMock()
        mock_member.data = None
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_current_user, mock_member
        ]
        
        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'viewer'},
            headers={'Authorization': mock_jwt_token}
        )
        
        assert response.status_code == 404
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_member_different_tenant(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update when member is in different tenant"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_current_user = MagicMock()
        mock_current_user.data = {'tenant_id': 'tenant123', 'role': 'admin'}
        
        mock_member = MagicMock()
        mock_member.data = {'tenant_id': 'tenant999', 'role': 'member'}
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_current_user, mock_member
        ]
        
        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'viewer'},
            headers={'Authorization': mock_jwt_token}
        )
        
        assert response.status_code == 403


class TestGetTenantInfo:
    """Test /api/tenant/info endpoint"""
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_tenant_info_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful tenant info retrieval"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}
        
        mock_tenant_response = MagicMock()
        mock_tenant_response.data = {
            'id': 'tenant123',
            'name': 'Test Tenant',
            'created_at': '2024-01-01',
            'updated_at': '2024-01-02'
        }
        
        mock_member_count = MagicMock()
        mock_member_count.count = 5
        
        mock_task_count = MagicMock()
        mock_task_count.count = 10
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_user_response, mock_tenant_response
        ]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            mock_member_count, mock_task_count
        ]
        
        response = client.get('/api/tenant/info', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['tenant_id'] == 'tenant123'
        assert data['member_count'] == 5
        assert data['task_count'] == 10
    
    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_tenant_info_tenant_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test when tenant is not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}
        
        mock_tenant_response = MagicMock()
        mock_tenant_response.data = None
        
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_user_response, mock_tenant_response
        ]
        
        response = client.get('/api/tenant/info', headers={'Authorization': mock_jwt_token})
        
        assert response.status_code == 404
