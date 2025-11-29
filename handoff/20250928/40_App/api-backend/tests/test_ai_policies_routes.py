"""
Tests for AI Policies API routes (Phase 6 PR-1)
Covers policy CRUD operations, templates, and evaluation
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock


@pytest.fixture
def app():
    """Create Flask app instance for testing"""
    with patch.dict(os.environ, {'SENTRY_DSN': '', 'SECRET_KEY': 'test-secret'}):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']

        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Create authentication headers with JWT token"""
    from src.middleware.auth_middleware import create_user_token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers():
    """Create admin authentication headers with JWT token"""
    from src.middleware.auth_middleware import generate_jwt_token
    admin_data = {
        'id': 1,
        'username': 'admin',
        'role': 'admin'
    }
    token = generate_jwt_token(admin_data)
    return {'Authorization': f'Bearer {token}'}


class TestAIPoliciesListEndpoint:
    """Test AI policies list endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_list_policies_unavailable(self, client, auth_headers):
        """Test list policies when module unavailable"""
        response = client.get('/api/ai-policies', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_list_policies_success(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test successful list policies"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_policy = MagicMock()
        mock_policy.to_dict.return_value = {
            'id': 'policy-1',
            'name': 'Test Policy',
            'policy_type': 'capability_whitelist',
            'status': 'active'
        }
        mock_manager.list_policies.return_value = [mock_policy]
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'policies' in data
        assert 'count' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    def test_list_policies_no_tenant(self, mock_get_tenant, client, auth_headers):
        """Test list policies when tenant not found"""
        mock_get_tenant.return_value = None

        response = client.get('/api/ai-policies', headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_list_policies_with_filters(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test list policies with query filters"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.list_policies.return_value = []
        mock_get_manager.return_value = mock_manager

        response = client.get(
            '/api/ai-policies?limit=10&offset=5&policy_type=rate_limit',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 10
        assert data['offset'] == 5


class TestAIPoliciesGetEndpoint:
    """Test get single policy endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_get_policy_unavailable(self, client, auth_headers):
        """Test get policy when module unavailable"""
        response = client.get('/api/ai-policies/policy-1', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_get_policy_not_found(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test get policy when not found"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.get_policy.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies/non-existent', headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_get_policy_success(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test successful get policy"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_policy = MagicMock()
        mock_policy.tenant_id = 'tenant-123'
        mock_policy.to_dict.return_value = {
            'id': 'policy-1',
            'name': 'Test Policy',
            'policy_type': 'capability_whitelist',
            'tenant_id': 'tenant-123'
        }
        mock_manager.get_policy.return_value = mock_policy
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies/policy-1', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == 'policy-1'

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    @patch('src.routes.ai_policies.PolicyScope')
    def test_get_policy_wrong_tenant(
        self, mock_scope, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test get policy from different tenant returns 404 for security"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_policy = MagicMock()
        mock_policy.tenant_id = 'other-tenant'
        mock_policy.scope = MagicMock()
        mock_scope.PLATFORM = MagicMock()
        mock_manager.get_policy.return_value = mock_policy
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies/policy-1', headers=auth_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


class TestAIPoliciesCreateEndpoint:
    """Test create policy endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_create_policy_unavailable(self, client, admin_headers):
        """Test create policy when module unavailable"""
        response = client.post(
            '/api/ai-policies',
            headers=admin_headers,
            json={'name': 'Test', 'policy_type': 'rate_limit', 'rules': {}}
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_create_policy_success(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test successful create policy"""
        mock_get_profile.return_value = ('tenant-123', 'admin')
        mock_manager = MagicMock()
        mock_policy = MagicMock()
        mock_policy.to_dict.return_value = {
            'id': 'new-policy-1',
            'name': 'New Policy',
            'policy_type': 'rate_limit',
            'rules': {'requests_per_minute': 60}
        }
        mock_manager.create_policy.return_value = mock_policy
        mock_get_manager.return_value = mock_manager

        response = client.post(
            '/api/ai-policies',
            headers=admin_headers,
            json={
                'name': 'New Policy',
                'policy_type': 'rate_limit',
                'rules': {'requests_per_minute': 60}
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['id'] == 'new-policy-1'

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    def test_create_policy_missing_fields(
        self, mock_get_profile, client, admin_headers
    ):
        """Test create policy with missing required fields"""
        mock_get_profile.return_value = ('tenant-123', 'admin')

        response = client.post(
            '/api/ai-policies',
            headers=admin_headers,
            json={'name': 'Test'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    def test_create_policy_invalid_type(
        self, mock_get_profile, client, admin_headers
    ):
        """Test create policy with invalid policy type"""
        mock_get_profile.return_value = ('tenant-123', 'admin')

        response = client.post(
            '/api/ai-policies',
            headers=admin_headers,
            json={
                'name': 'Test',
                'policy_type': 'invalid_type',
                'rules': {}
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_create_policy_db_failure(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test create policy returns 503 when database persistence fails"""
        mock_get_profile.return_value = ('tenant-123', 'admin')
        mock_manager = MagicMock()
        mock_manager.create_policy.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.post(
            '/api/ai-policies',
            headers=admin_headers,
            json={
                'name': 'New Policy',
                'policy_type': 'rate_limit',
                'rules': {'requests_per_minute': 60}
            }
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data
        assert 'persist' in data['error'].lower() or 'database' in data['error'].lower()


class TestAIPoliciesUpdateEndpoint:
    """Test update policy endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_update_policy_unavailable(self, client, admin_headers):
        """Test update policy when module unavailable"""
        response = client.put(
            '/api/ai-policies/policy-1',
            headers=admin_headers,
            json={'name': 'Updated'}
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_update_policy_success(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test successful update policy"""
        mock_get_profile.return_value = ('tenant-123', 'admin')
        mock_manager = MagicMock()

        mock_existing = MagicMock()
        mock_existing.tenant_id = 'tenant-123'
        mock_manager.get_policy.return_value = mock_existing

        mock_updated = MagicMock()
        mock_updated.to_dict.return_value = {
            'id': 'policy-1',
            'name': 'Updated Policy',
            'policy_type': 'rate_limit'
        }
        mock_manager.update_policy.return_value = mock_updated
        mock_get_manager.return_value = mock_manager

        response = client.put(
            '/api/ai-policies/policy-1',
            headers=admin_headers,
            json={'name': 'Updated Policy'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Policy'

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_update_policy_not_found(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test update policy when not found"""
        mock_get_profile.return_value = ('tenant-123', 'admin')
        mock_manager = MagicMock()
        mock_manager.get_policy.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.put(
            '/api/ai-policies/non-existent',
            headers=admin_headers,
            json={'name': 'Updated'}
        )

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


class TestAIPoliciesDeleteEndpoint:
    """Test delete policy endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_delete_policy_unavailable(self, client, admin_headers):
        """Test delete policy when module unavailable"""
        response = client.delete(
            '/api/ai-policies/policy-1',
            headers=admin_headers
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_delete_policy_success(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test successful delete policy (requires owner role)"""
        mock_get_profile.return_value = ('tenant-123', 'owner')
        mock_manager = MagicMock()

        mock_existing = MagicMock()
        mock_existing.tenant_id = 'tenant-123'
        mock_manager.get_policy.return_value = mock_existing
        mock_manager.delete_policy.return_value = True
        mock_get_manager.return_value = mock_manager

        response = client.delete(
            '/api/ai-policies/policy-1',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['policy_id'] == 'policy-1'

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_profile')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_delete_policy_not_found(
        self, mock_get_manager, mock_get_profile, client, admin_headers
    ):
        """Test delete policy when not found (requires owner role)"""
        mock_get_profile.return_value = ('tenant-123', 'owner')
        mock_manager = MagicMock()
        mock_manager.get_policy.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.delete(
            '/api/ai-policies/non-existent',
            headers=admin_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


class TestAIPoliciesTemplatesEndpoint:
    """Test policy templates endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_templates_unavailable(self, client, auth_headers):
        """Test templates when module unavailable"""
        response = client.get('/api/ai-policies/templates', headers=auth_headers)

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_templates_success(self, mock_get_manager, client, auth_headers):
        """Test successful get templates"""
        mock_manager = MagicMock()
        mock_manager.get_policy_templates.return_value = {
            'rate_limit': {
                'name': 'Rate Limiting',
                'description': 'Limit API requests',
                'policy_type': 'rate_limit',
                'rules': {'requests_per_minute': 60}
            }
        }
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies/templates', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'templates' in data
        assert 'rate_limit' in data['templates']


class TestAIPoliciesEvaluateEndpoint:
    """Test policy evaluation endpoint"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False)
    def test_evaluate_unavailable(self, client, auth_headers):
        """Test evaluate when module unavailable"""
        response = client.post(
            '/api/ai-policies/evaluate',
            headers=auth_headers,
            json={'capability': 'code_generation'}
        )

        assert response.status_code == 503
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_evaluate_success_allowed(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test successful evaluate - allowed"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.evaluate_request.return_value = {
            'allowed': True,
            'reason': 'No policies restrict this action',
            'applied_policies': []
        }
        mock_get_manager.return_value = mock_manager

        response = client.post(
            '/api/ai-policies/evaluate',
            headers=auth_headers,
            json={'capability': 'code_generation'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['allowed'] is True

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_evaluate_success_denied(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test successful evaluate - denied"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.evaluate_request.return_value = {
            'allowed': False,
            'reason': 'Capability is blocked',
            'applied_policies': ['policy-1']
        }
        mock_get_manager.return_value = mock_manager

        response = client.post(
            '/api/ai-policies/evaluate',
            headers=auth_headers,
            json={'capability': 'dangerous_action'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['allowed'] is False

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    def test_evaluate_missing_capability(self, mock_get_tenant, client, auth_headers):
        """Test evaluate with missing capability"""
        mock_get_tenant.return_value = 'tenant-123'

        response = client.post(
            '/api/ai-policies/evaluate',
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestAIPoliciesErrorHandling:
    """Test error handling in AI policies routes"""

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_list_policies_exception(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test list policies exception handling"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.list_policies.side_effect = Exception('Database error')
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_get_policy_exception(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test get policy exception handling"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.get_policy.side_effect = Exception('Database error')
        mock_get_manager.return_value = mock_manager

        response = client.get('/api/ai-policies/policy-1', headers=auth_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', True)
    @patch('src.routes.ai_policies.get_user_tenant_id')
    @patch('src.routes.ai_policies.get_ai_policy_manager')
    def test_evaluate_exception(
        self, mock_get_manager, mock_get_tenant, client, auth_headers
    ):
        """Test evaluate exception handling"""
        mock_get_tenant.return_value = 'tenant-123'
        mock_manager = MagicMock()
        mock_manager.evaluate_request.side_effect = Exception('Evaluation error')
        mock_get_manager.return_value = mock_manager

        response = client.post(
            '/api/ai-policies/evaluate',
            headers=auth_headers,
            json={'capability': 'test'}
        )

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
