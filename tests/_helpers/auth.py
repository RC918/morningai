"""
Authentication helpers for RLS testing.

This module provides utilities for creating test users with real Supabase Auth JWTs
and mapping them to tenants for multi-tenant isolation testing.
"""

import os
import time
from uuid import uuid4
import requests


SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')


def create_test_user_with_tenant(email, password, tenant_id, role='member', max_retries=3):
    """
    Create a test user via Supabase Auth Admin API and map to tenant.
    
    Args:
        email: User email address
        password: User password
        tenant_id: UUID of tenant to assign user to
        role: User role ('owner', 'admin', 'member', 'viewer')
        max_retries: Maximum number of retries for eventual consistency
    
    Returns:
        tuple: (user_id, jwt_token)
    
    Raises:
        Exception: If user creation or authentication fails
    """
    admin_headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f'{SUPABASE_URL}/auth/v1/admin/users',
        headers=admin_headers,
        json={
            'email': email,
            'password': password,
            'email_confirm': True
        },
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create user: {response.status_code} - {response.text}")
    
    user_id = response.json()['id']
    
    time.sleep(0.5)
    
    profile_data = {
        'id': user_id,
        'tenant_id': tenant_id,
        'role': role
    }
    
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/user_profiles',
        headers=admin_headers,
        json=profile_data,
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        cleanup_test_user(user_id)
        raise Exception(f"Failed to create user profile: {response.status_code} - {response.text}")
    
    jwt_token = None
    for attempt in range(max_retries):
        time.sleep(0.5 * (attempt + 1))  # 0.5s, 1s, 1.5s
        
        anon_headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/auth/v1/token?grant_type=password',
            headers=anon_headers,
            json={'email': email, 'password': password},
            timeout=10
        )
        
        if response.status_code == 200:
            jwt_token = response.json()['access_token']
            break
    
    if not jwt_token:
        cleanup_test_user(user_id)
        raise Exception(f"Failed to sign in user after {max_retries} attempts")
    
    return user_id, jwt_token


def get_authenticated_headers(jwt_token):
    """
    Get headers for authenticated user requests.
    
    IMPORTANT: Must include both apikey (anon key) and Authorization (user JWT).
    The anon key is the project public API key, the Bearer token is the user's identity.
    
    Args:
        jwt_token: User's JWT access token
    
    Returns:
        dict: Headers for authenticated requests
    """
    return {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }


def cleanup_test_user(user_id):
    """
    Delete test user and all related data.
    
    Cleanup order (to avoid FK violations):
    1. Delete agent_tasks (references user via tenant_id)
    2. Delete user_profiles (references auth.users)
    3. Delete auth user
    
    Args:
        user_id: UUID of user to delete
    """
    admin_headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }
    
    try:
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/user_profiles?id=eq.{user_id}&select=tenant_id',
            headers=admin_headers,
            timeout=10
        )
        
        if response.status_code == 200 and response.json():
            tenant_id = response.json()[0]['tenant_id']
            
            requests.delete(
                f'{SUPABASE_URL}/rest/v1/agent_tasks?tenant_id=eq.{tenant_id}',
                headers=admin_headers,
                timeout=10
            )
        
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/user_profiles?id=eq.{user_id}',
            headers=admin_headers,
            timeout=10
        )
        
        requests.delete(
            f'{SUPABASE_URL}/auth/v1/admin/users/{user_id}',
            headers=admin_headers,
            timeout=10
        )
    except Exception as e:
        print(f"Warning: Failed to cleanup user {user_id}: {e}")


def cleanup_test_tenant(tenant_id):
    """
    Delete test tenant and all related data.
    
    Cleanup order:
    1. Delete agent_tasks
    2. Delete user_profiles
    3. Delete tenant
    
    Args:
        tenant_id: UUID of tenant to delete
    """
    admin_headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    }
    
    try:
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/agent_tasks?tenant_id=eq.{tenant_id}',
            headers=admin_headers,
            timeout=10
        )
        
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/user_profiles?tenant_id=eq.{tenant_id}',
            headers=admin_headers,
            timeout=10
        )
        
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/tenants?id=eq.{tenant_id}',
            headers=admin_headers,
            timeout=10
        )
    except Exception as e:
        print(f"Warning: Failed to cleanup tenant {tenant_id}: {e}")
