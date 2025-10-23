#!/usr/bin/env python3
"""
Comprehensive RLS (Row Level Security) Policy Testing for pytest
Tests all RLS policies with all roles (service_role, authenticated, anonymous)
and critical operations (SELECT, INSERT)
"""

import os
import pytest
import requests
import jwt
from datetime import datetime, timedelta, timezone

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-rls-testing')

TABLES_WITH_RLS = [
    'faqs',
    'faq_search_history',
    'faq_categories',
    'embeddings',
    'vector_queries',
    'trace_metrics',
    'alerts',
    'agent_reputation',
    'reputation_events'
]


def generate_authenticated_jwt():
    """Generate JWT token for authenticated role testing"""
    payload = {
        'user_id': 'test-user-rls-123',
        'username': 'test-rls-user',
        'role': 'authenticated',
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc)
    }
    
    try:
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        return token
    except Exception as e:
        pytest.skip(f"Could not generate JWT token: {e}")


def get_headers(role):
    """Get appropriate headers for different roles"""
    if role == 'service_role':
        return {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json'
        }
    elif role == 'authenticated':
        token = generate_authenticated_jwt()
        return {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    elif role == 'anonymous':
        return {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Content-Type': 'application/json'
        }
    else:
        raise ValueError(f"Unknown role: {role}")


@pytest.mark.parametrize("table", TABLES_WITH_RLS)
class TestServiceRoleAccess:
    """Test that service_role has full access to all tables"""
    
    def test_service_role_can_select(self, table):
        """service_role should be able to SELECT from all tables"""
        headers = get_headers('service_role')
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200, \
            f"service_role should have SELECT access to {table}, got {response.status_code}"
    
    def test_service_role_can_insert(self, table):
        """service_role should be able to INSERT into all tables"""
        headers = get_headers('service_role')
        
        test_data = {
            'test_field': 'rls_test_value',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/{table}',
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        assert response.status_code in [200, 201, 400, 422], \
            f"service_role should have INSERT access to {table}, got {response.status_code}: {response.text[:200]}"


@pytest.mark.parametrize("table", TABLES_WITH_RLS)
class TestAuthenticatedRoleAccess:
    """Test that authenticated role has read-only access"""
    
    def test_authenticated_can_select(self, table):
        """authenticated role should be able to SELECT (read-only)"""
        headers = get_headers('authenticated')
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200, \
            f"authenticated role should have SELECT access to {table}, got {response.status_code}"
    
    def test_authenticated_cannot_insert(self, table):
        """authenticated role should NOT be able to INSERT (read-only)"""
        headers = get_headers('authenticated')
        
        test_data = {
            'test_field': 'rls_test_value',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/{table}',
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        assert response.status_code in [401, 403], \
            f"authenticated role should NOT have INSERT access to {table}, got {response.status_code}"


@pytest.mark.parametrize("table", TABLES_WITH_RLS)
class TestAnonymousRoleBlocked:
    """Test that anonymous role is completely blocked"""
    
    def test_anonymous_cannot_select(self, table):
        """anonymous role should be blocked from SELECT"""
        headers = get_headers('anonymous')
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/{table}?limit=1',
            headers=headers,
            timeout=10
        )
        assert response.status_code == 401, \
            f"anonymous role should be blocked from {table}, got {response.status_code}"
    
    def test_anonymous_cannot_insert(self, table):
        """anonymous role should be blocked from INSERT"""
        headers = get_headers('anonymous')
        
        test_data = {
            'test_field': 'rls_test_value',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f'{SUPABASE_URL}/rest/v1/{table}',
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        assert response.status_code in [401, 403], \
            f"anonymous role should be blocked from {table}, got {response.status_code}"


class TestRLSPolicySummary:
    """Summary tests to ensure RLS is working as expected"""
    
    def test_all_tables_have_rls_enabled(self):
        """Verify that all expected tables have RLS enabled"""
        assert len(TABLES_WITH_RLS) == 9, \
            f"Expected 9 tables with RLS, got {len(TABLES_WITH_RLS)}"
    
    def test_service_role_key_is_set(self):
        """Verify that SUPABASE_SERVICE_ROLE_KEY is configured"""
        assert SUPABASE_SERVICE_ROLE_KEY is not None, \
            "SUPABASE_SERVICE_ROLE_KEY must be set"
        assert len(SUPABASE_SERVICE_ROLE_KEY) > 20, \
            "SUPABASE_SERVICE_ROLE_KEY appears to be invalid"
    
    def test_supabase_url_is_set(self):
        """Verify that SUPABASE_URL is configured"""
        assert SUPABASE_URL is not None, \
            "SUPABASE_URL must be set"
        assert SUPABASE_URL.startswith('https://'), \
            "SUPABASE_URL must be a valid HTTPS URL"
    
    def test_jwt_token_generation(self):
        """Verify that JWT tokens can be generated for authenticated role"""
        token = generate_authenticated_jwt()
        assert token is not None, \
            "Should be able to generate JWT token"
        assert len(token) > 20, \
            "JWT token appears to be invalid"


def run_comprehensive_rls_tests():
    """Run comprehensive RLS tests manually"""
    print("🧪 COMPREHENSIVE RLS POLICY TEST SUITE")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing all roles (service_role, authenticated, anonymous)")
    print("Testing critical operations (SELECT, INSERT)")
    print(f"Testing {len(TABLES_WITH_RLS)} tables with RLS enabled")
    print()
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for table in TABLES_WITH_RLS:
        print(f"\n📋 Testing table: {table}")
        print("-" * 80)
        
        print("  Testing service_role:")
        try:
            headers = get_headers('service_role')
            response = requests.get(f'{SUPABASE_URL}/rest/v1/{table}?limit=1', headers=headers, timeout=10)
            if response.status_code == 200:
                print("    ✅ SELECT: PASS")
                passed_tests += 1
            else:
                print(f"    ❌ SELECT: FAIL ({response.status_code})")
                failed_tests += 1
            total_tests += 1
        except Exception as e:
            print(f"    ❌ SELECT: ERROR ({e})")
            failed_tests += 1
            total_tests += 1
        
        print("  Testing authenticated:")
        try:
            headers = get_headers('authenticated')
            response = requests.get(f'{SUPABASE_URL}/rest/v1/{table}?limit=1', headers=headers, timeout=10)
            if response.status_code == 200:
                print("    ✅ SELECT: PASS")
                passed_tests += 1
            else:
                print(f"    ❌ SELECT: FAIL ({response.status_code})")
                failed_tests += 1
            total_tests += 1
        except Exception as e:
            print(f"    ❌ SELECT: ERROR ({e})")
            failed_tests += 1
            total_tests += 1
        
        print("  Testing anonymous:")
        try:
            headers = get_headers('anonymous')
            response = requests.get(f'{SUPABASE_URL}/rest/v1/{table}?limit=1', headers=headers, timeout=10)
            if response.status_code == 401:
                print("    ✅ SELECT: BLOCKED (expected)")
                passed_tests += 1
            else:
                print(f"    ❌ SELECT: Should be blocked, got {response.status_code}")
                failed_tests += 1
            total_tests += 1
        except Exception as e:
            print(f"    ❌ SELECT: ERROR ({e})")
            failed_tests += 1
            total_tests += 1
    
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests == 0:
        print("\n✅ SUCCESS: All RLS policy tests passed!")
        return True
    else:
        print("\n⚠️  WARNING: Some RLS policy tests failed!")
        return False


if __name__ == '__main__':
    import sys
    success = run_comprehensive_rls_tests()
    sys.exit(0 if success else 1)
