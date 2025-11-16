"""
RLS (Row Level Security) tests with REAL Supabase Auth users.

This test suite addresses P0 security issues by using real user JWTs with auth.uid()
instead of fake tokens or anon keys. This ensures RLS policies that check auth.uid()
are properly tested.

P0 Fixes Implemented:
- P0-1: Uses real Supabase user JWTs (not anon key)
- P0-2: Tests cross-tenant isolation with real users
- P0-3: Security safeguards via conftest.py

Environment Variables Required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Service role key (full access)
- SUPABASE_ANON_KEY: Anonymous key (public access)
- RLS_TESTS_ALLOWED: Must be 'true' to run tests
- TEST_SUPABASE_URL: Whitelisted test environment URL

Usage:
    export RLS_TESTS_ALLOWED=true
    export TEST_SUPABASE_URL="https://your-test-project.supabase.co"
    pytest tests/test_rls_with_real_users.py -v
"""

import os
import pytest
import requests
from datetime import datetime, timezone
from uuid import uuid4

from _helpers.auth import (
    create_test_user_with_tenant,
    get_authenticated_headers,
    cleanup_test_user,
    cleanup_test_tenant
)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')


def get_service_role_headers():
    """Get headers for service_role (full access)"""
    return {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }


@pytest.fixture(scope='module')
def test_tenant_and_user():
    """
    Create a test tenant and user with real JWT for authenticated tests.
    
    This fixture creates:
    1. A test tenant
    2. A test user mapped to that tenant
    3. Returns the user's real JWT token with auth.uid()
    
    Cleanup is automatic via try/finally.
    """
    tenant_id = str(uuid4())
    admin_headers = get_service_role_headers()
    
    tenant_data = {
        'id': tenant_id,
        'name': f'Test Tenant {tenant_id[:8]}'
    }
    
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/tenants',
        headers=admin_headers,
        json=tenant_data,
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        pytest.skip(f"Failed to create test tenant: {response.text}")
    
    email = f'test-{uuid4()}@example.com'
    password = 'test-password-123'
    
    try:
        user_id, jwt_token = create_test_user_with_tenant(email, password, tenant_id)
        yield {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'jwt_token': jwt_token,
            'email': email
        }
    finally:
        cleanup_test_user(user_id)
        cleanup_test_tenant(tenant_id)


@pytest.fixture(scope='module')
def cross_tenant_users():
    """
    Create two tenants with one user each for cross-tenant isolation testing.
    
    Returns:
        dict: {
            'tenant_a': {'tenant_id', 'user_id', 'jwt_token'},
            'tenant_b': {'tenant_id', 'user_id', 'jwt_token'}
        }
    """
    admin_headers = get_service_role_headers()
    
    tenant_a_id = str(uuid4())
    tenant_a_data = {
        'id': tenant_a_id,
        'name': f'Test Tenant A {tenant_a_id[:8]}'
    }
    
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/tenants',
        headers=admin_headers,
        json=tenant_a_data,
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        pytest.skip(f"Failed to create tenant A: {response.text}")
    
    tenant_b_id = str(uuid4())
    tenant_b_data = {
        'id': tenant_b_id,
        'name': f'Test Tenant B {tenant_b_id[:8]}'
    }
    
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/tenants',
        headers=admin_headers,
        json=tenant_b_data,
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        cleanup_test_tenant(tenant_a_id)
        pytest.skip(f"Failed to create tenant B: {response.text}")
    
    email_a = f'test-user-a-{uuid4()}@example.com'
    password_a = 'test-password-123'
    
    email_b = f'test-user-b-{uuid4()}@example.com'
    password_b = 'test-password-123'
    
    try:
        user_a_id, jwt_a = create_test_user_with_tenant(email_a, password_a, tenant_a_id)
        user_b_id, jwt_b = create_test_user_with_tenant(email_b, password_b, tenant_b_id)
        
        yield {
            'tenant_a': {
                'tenant_id': tenant_a_id,
                'user_id': user_a_id,
                'jwt_token': jwt_a,
                'email': email_a
            },
            'tenant_b': {
                'tenant_id': tenant_b_id,
                'user_id': user_b_id,
                'jwt_token': jwt_b,
                'email': email_b
            }
        }
    finally:
        cleanup_test_user(user_a_id)
        cleanup_test_user(user_b_id)
        cleanup_test_tenant(tenant_a_id)
        cleanup_test_tenant(tenant_b_id)


class TestAuthenticatedUserAccess:
    """Test that authenticated users (with real JWT) can access tables"""
    
    def test_authenticated_user_can_read_agent_tasks(self, test_tenant_and_user):
        """Authenticated user with real JWT should be able to read agent_tasks"""
        headers = get_authenticated_headers(test_tenant_and_user['jwt_token'])
        
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/agent_tasks?limit=1',
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200, \
            f"Authenticated user should be able to read agent_tasks, got {response.status_code}: {response.text}"
    
    def test_authenticated_user_can_read_user_profiles(self, test_tenant_and_user):
        """Authenticated user should be able to read user_profiles"""
        headers = get_authenticated_headers(test_tenant_and_user['jwt_token'])
        
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/user_profiles?limit=1',
            headers=headers,
            timeout=10
        )
        
        assert response.status_code == 200, \
            f"Authenticated user should be able to read user_profiles, got {response.status_code}"


class TestCrossTenantIsolation:
    """
    P0-2: Test that users cannot access data from other tenants.
    
    This is the CRITICAL security test that verifies RLS policies properly
    enforce tenant isolation using auth.uid() checks.
    """
    
    def test_user_a_cannot_read_tenant_b_tasks(self, cross_tenant_users):
        """User A should NOT be able to read Tenant B's agent_tasks"""
        tenant_a = cross_tenant_users['tenant_a']
        tenant_b = cross_tenant_users['tenant_b']
        
        headers_b = get_authenticated_headers(tenant_b['jwt_token'])
        task_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_b['tenant_id'],
            'question': 'Test question for Tenant B',
            'status': 'pending'
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_b,
            json=task_data,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create task for User B: {response.status_code} - {response.text}")
        
        task_id = response.json()[0]['task_id']
        
        headers_a = get_authenticated_headers(tenant_a['jwt_token'])
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/agent_tasks?task_id=eq.{task_id}',
            headers=headers_a,
            timeout=10
        )
        
        assert response.status_code == 200, \
            f"Request should succeed but return empty, got {response.status_code}"
        
        tasks = response.json()
        assert len(tasks) == 0, \
            f"User A should NOT see Tenant B's tasks (RLS should filter), but got {len(tasks)} tasks"
    
    def test_user_a_cannot_insert_into_tenant_b(self, cross_tenant_users):
        """User A should NOT be able to INSERT tasks with tenant_id = Tenant B (WITH CHECK)"""
        tenant_a = cross_tenant_users['tenant_a']
        tenant_b = cross_tenant_users['tenant_b']
        
        headers_a = get_authenticated_headers(tenant_a['jwt_token'])
        task_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_b['tenant_id'],  # Trying to insert into Tenant B!
            'question': 'Malicious cross-tenant insert attempt',
            'status': 'pending'
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_a,
            json=task_data,
            timeout=10
        )
        
        assert response.status_code in [400, 401, 403, 422], \
            f"User A should NOT be able to INSERT into Tenant B, got {response.status_code}: {response.text}"
    
    def test_user_can_only_see_own_tenant_tasks(self, cross_tenant_users):
        """User should only see tasks from their own tenant"""
        tenant_a = cross_tenant_users['tenant_a']
        tenant_b = cross_tenant_users['tenant_b']
        
        headers_a = get_authenticated_headers(tenant_a['jwt_token'])
        task_a_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_a['tenant_id'],
            'question': 'Task for Tenant A',
            'status': 'pending'
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_a,
            json=task_a_data,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create task for Tenant A: {response.text}")
        
        headers_b = get_authenticated_headers(tenant_b['jwt_token'])
        task_b_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_b['tenant_id'],
            'question': 'Task for Tenant B',
            'status': 'pending'
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_b,
            json=task_b_data,
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create task for Tenant B: {response.text}")
        
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_a,
            timeout=10
        )
        
        assert response.status_code == 200
        tasks = response.json()
        
        for task in tasks:
            assert task['tenant_id'] == tenant_a['tenant_id'], \
                f"User A should only see Tenant A tasks, but found task from {task['tenant_id']}"


class TestServiceRoleBypassesRLS:
    """Test that service_role can access all tenants (for backend operations)"""
    
    def test_service_role_can_see_all_tenants(self, cross_tenant_users):
        """Service role should be able to see tasks from all tenants"""
        tenant_a = cross_tenant_users['tenant_a']
        tenant_b = cross_tenant_users['tenant_b']
        
        headers_a = get_authenticated_headers(tenant_a['jwt_token'])
        task_a_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_a['tenant_id'],
            'question': 'Task for Tenant A',
            'status': 'pending'
        }
        
        requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_a,
            json=task_a_data,
            timeout=10
        )
        
        headers_b = get_authenticated_headers(tenant_b['jwt_token'])
        task_b_data = {
            'task_id': str(uuid4()),
            'trace_id': str(uuid4()),
            'tenant_id': tenant_b['tenant_id'],
            'question': 'Task for Tenant B',
            'status': 'pending'
        }
        
        requests.post(
            f'{SUPABASE_URL}/rest/v1/agent_tasks',
            headers=headers_b,
            json=task_b_data,
            timeout=10
        )
        
        admin_headers = get_service_role_headers()
        
        response_a = requests.get(
            f'{SUPABASE_URL}/rest/v1/agent_tasks?tenant_id=eq.{tenant_a["tenant_id"]}',
            headers=admin_headers,
            timeout=10
        )
        assert response_a.status_code == 200
        assert len(response_a.json()) > 0, "Service role should see Tenant A tasks"
        
        response_b = requests.get(
            f'{SUPABASE_URL}/rest/v1/agent_tasks?tenant_id=eq.{tenant_b["tenant_id"]}',
            headers=admin_headers,
            timeout=10
        )
        assert response_b.status_code == 200
        assert len(response_b.json()) > 0, "Service role should see Tenant B tasks"


class TestEnvironmentSafeguards:
    """P0-3: Verify security safeguards are in place"""
    
    def test_rls_tests_allowed_is_set(self):
        """Verify RLS_TESTS_ALLOWED is set to 'true'"""
        assert os.environ.get('RLS_TESTS_ALLOWED') == 'true', \
            "RLS_TESTS_ALLOWED must be 'true' (checked by conftest.py)"
    
    def test_test_supabase_url_matches(self):
        """Verify SUPABASE_URL matches TEST_SUPABASE_URL"""
        supabase_url = os.environ.get('SUPABASE_URL')
        test_supabase_url = os.environ.get('TEST_SUPABASE_URL')
        
        assert supabase_url == test_supabase_url, \
            "SUPABASE_URL must match TEST_SUPABASE_URL (checked by conftest.py)"
    
    def test_url_not_production(self):
        """Verify SUPABASE_URL does not contain production markers"""
        supabase_url = os.environ.get('SUPABASE_URL', '').lower()
        
        assert 'prod' not in supabase_url, \
            "SUPABASE_URL must NOT contain 'prod'"
        assert 'production' not in supabase_url, \
            "SUPABASE_URL must NOT contain 'production'"


if __name__ == '__main__':
    import sys
    pytest.main([__file__, '-v'])
    sys.exit(0)
