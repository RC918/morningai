"""Additional tests for tenant routes to improve coverage from 63% to 80%+"""
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


class TestGetTenantUsage:
    """Test /api/tenant/usage endpoint"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_usage_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful usage retrieval"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        with patch('src.utils.tenant_quota.get_quota_manager') as mock_quota:
            mock_manager = MagicMock()
            mock_manager.get_usage_summary.return_value = {
                'plan_tier': 'pro',
                'quotas': {'api_requests_per_day': 10000},
                'usage': {'api_requests_per_day': 5000},
                'remaining': {'api_requests_per_day': 5000}
            }
            mock_quota.return_value = mock_manager

            response = client.get('/api/tenant/usage', headers={'Authorization': mock_jwt_token})

            assert response.status_code == 200
            data = response.get_json()
            assert data['tenant_id'] == 'tenant123'
            assert data['plan_tier'] == 'pro'

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_usage_quota_not_available(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test usage retrieval when quota module not available"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        with patch('src.utils.tenant_quota.get_quota_manager', side_effect=ImportError("Module not found")):
            response = client.get('/api/tenant/usage', headers={'Authorization': mock_jwt_token})

            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_usage_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test usage retrieval when profile not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        response = client.get('/api/tenant/usage', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 404

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_usage_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test usage retrieval server error"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Database error")

        response = client.get('/api/tenant/usage', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 500


class TestGetTenantQuota:
    """Test /api/tenant/quota endpoint"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_quota_success(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test successful quota retrieval"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        with patch('src.utils.tenant_quota.get_quota_manager') as mock_quota:
            mock_manager = MagicMock()
            mock_tenant_quota = MagicMock()
            mock_tenant_quota.plan_tier = 'pro'
            mock_tenant_quota.api_requests_per_minute = 100
            mock_tenant_quota.api_requests_per_hour = 1000
            mock_tenant_quota.api_requests_per_day = 10000
            mock_tenant_quota.max_concurrent_tasks = 10
            mock_tenant_quota.max_tasks_per_day = 500
            mock_tenant_quota.max_task_duration_seconds = 3600
            mock_tenant_quota.max_storage_bytes = 1073741824
            mock_tenant_quota.max_documents = 1000
            mock_tenant_quota.max_embeddings = 10000
            mock_tenant_quota.max_llm_tokens_per_day = 100000
            mock_tenant_quota.max_llm_requests_per_hour = 500
            mock_tenant_quota.max_prs_per_day = 50
            mock_tenant_quota.max_code_generations_per_hour = 100
            mock_manager.get_tenant_quota.return_value = mock_tenant_quota
            mock_quota.return_value = mock_manager

            response = client.get('/api/tenant/quota', headers={'Authorization': mock_jwt_token})

            assert response.status_code == 200
            data = response.get_json()
            assert data['tenant_id'] == 'tenant123'
            assert data['plan_tier'] == 'pro'
            assert 'limits' in data

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_quota_not_available(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test quota retrieval when quota module not available"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        with patch('src.utils.tenant_quota.get_quota_manager', side_effect=ImportError("Module not found")):
            response = client.get('/api/tenant/quota', headers={'Authorization': mock_jwt_token})

            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_quota_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test quota retrieval when profile not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        response = client.get('/api/tenant/quota', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 404

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_quota_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test quota retrieval server error"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Database error")

        response = client.get('/api/tenant/quota', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 500


class TestTenantMembersEdgeCases:
    """Test edge cases for tenant members endpoint"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test members retrieval when profile not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        response = client.get('/api/tenant/members', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 404

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test members retrieval server error"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Database error")

        response = client.get('/api/tenant/members', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 500

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_email_fetch_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test members retrieval when email fetch fails"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = {'tenant_id': 'tenant123'}

        mock_members_response = MagicMock()
        mock_members_response.data = [
            {'id': 'user1', 'display_name': 'User 1', 'role': 'admin', 'created_at': '2024-01-01'}
        ]

        mock_count_response = MagicMock()
        mock_count_response.count = 1

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response
        mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.execute.return_value = mock_members_response
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_client.auth.admin.get_user_by_id.side_effect = Exception("Auth error")

        response = client.get('/api/tenant/members', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 200
        data = response.get_json()
        assert data['members'][0]['email'] is None

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_members_limit_capped(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test members retrieval with limit capped at 100"""
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

        response = client.get('/api/tenant/members?limit=200', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 100


class TestUpdateMemberRoleEdgeCases:
    """Test edge cases for update member role endpoint"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_missing_body(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update role with missing body"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        response = client.put(
            '/api/tenant/members/member456',
            headers={'Authorization': mock_jwt_token}
        )

        assert response.status_code == 400

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update role when current user profile not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_current_user = MagicMock()
        mock_current_user.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_current_user

        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'admin'},
            headers={'Authorization': mock_jwt_token}
        )

        assert response.status_code == 404

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update role server error"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Database error")

        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'admin'},
            headers={'Authorization': mock_jwt_token}
        )

        assert response.status_code == 500

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_update_role_update_failed(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test update role when update fails"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_current_user = MagicMock()
        mock_current_user.data = {'tenant_id': 'tenant123', 'role': 'admin'}

        mock_member = MagicMock()
        mock_member.data = {'tenant_id': 'tenant123', 'role': 'member'}

        mock_update = MagicMock()
        mock_update.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = [
            mock_current_user, mock_member
        ]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update

        response = client.put(
            '/api/tenant/members/member456',
            json={'role': 'viewer'},
            headers={'Authorization': mock_jwt_token}
        )

        assert response.status_code == 500


class TestGetTenantInfoEdgeCases:
    """Test edge cases for get tenant info endpoint"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_info_profile_not_found(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test get info when profile not found"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user_response = MagicMock()
        mock_user_response.data = None

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_user_response

        response = client.get('/api/tenant/info', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 404

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_get_info_server_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test get info server error"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Database error")

        response = client.get('/api/tenant/info', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 500


class TestSupabaseClientError:
    """Test Supabase client error handling"""

    @patch('src.routes.tenant.get_supabase_client')
    @patch('src.middleware.auth_middleware.jwt.decode')
    def test_supabase_client_error(self, mock_decode, mock_get_client, client, mock_jwt_token):
        """Test when Supabase client fails to initialize"""
        mock_decode.return_value = {'sub': 'user123', 'role': 'authenticated'}

        mock_get_client.side_effect = Exception("Failed to get Supabase client")

        response = client.get('/api/tenant/me', headers={'Authorization': mock_jwt_token})

        assert response.status_code == 500
