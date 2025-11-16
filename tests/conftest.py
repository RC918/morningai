<<<<<<< HEAD
"""
Pytest configuration and fixtures for RLS testing.

This module provides session-level safety guards to prevent accidental
execution of destructive RLS tests against production environments.
"""

import os
import pytest


@pytest.fixture(scope='session', autouse=True)
def verify_test_environment():
    """
    Verify that RLS tests are running in a safe test environment.
    
    This fixture runs automatically before any tests and enforces:
    1. RLS_TESTS_ALLOWED must be explicitly set to 'true'
    2. SUPABASE_URL must exactly match TEST_SUPABASE_URL (whitelist)
    3. SUPABASE_URL must NOT contain production markers
    
    Note: This fixture is skipped for migration idempotency tests
    (controlled by IDEMPOTENCY_TESTS_ALLOWED environment variable).
    
    Raises:
        pytest.skip: If environment is not configured for RLS tests
        ValueError: If SUPABASE_URL appears to be a production environment
    """
    idempotency_tests_allowed = os.environ.get('IDEMPOTENCY_TESTS_ALLOWED', 'false')
    if idempotency_tests_allowed == 'true':
        return
    
    supabase_url = os.environ.get('SUPABASE_URL', '')
    test_supabase_url = os.environ.get('TEST_SUPABASE_URL', '')
    rls_tests_allowed = os.environ.get('RLS_TESTS_ALLOWED', 'false')
    
    if rls_tests_allowed != 'true':
        pytest.skip(
            "RLS_TESTS_ALLOWED must be set to 'true' to run RLS tests. "
            "This prevents accidental execution against production."
        )
    
    if not test_supabase_url:
        pytest.skip(
            "TEST_SUPABASE_URL must be set to run RLS tests. "
            "This whitelists the allowed test environment."
        )
    
    if supabase_url != test_supabase_url:
        pytest.skip(
            f"SUPABASE_URL ({supabase_url}) does not match TEST_SUPABASE_URL ({test_supabase_url}). "
            "RLS tests can only run against the whitelisted test environment."
        )
    
    production_markers = ['prod', 'production']
    for marker in production_markers:
        if marker in supabase_url.lower():
            raise ValueError(
                f"REFUSING TO RUN RLS TESTS AGAINST PRODUCTION! "
                f"SUPABASE_URL contains '{marker}': {supabase_url}"
            )
    
    test_markers = ['test', 'staging', 'dev']
    if not any(marker in supabase_url.lower() for marker in test_markers):
        print(f"\n⚠️  WARNING: SUPABASE_URL does not contain typical test markers (test/staging/dev): {supabase_url}")
        print(f"   Proceeding because TEST_SUPABASE_URL is explicitly set to this URL.")
    
    print(f"\n✅ RLS test environment verified: {supabase_url}")
||||||| 8a33b660
=======
"""
Pytest configuration and fixtures for RLS testing.

This module provides session-level safety guards to prevent accidental
execution of destructive RLS tests against production environments.
"""

import os
import pytest


@pytest.fixture(scope='session', autouse=True)
def verify_test_environment():
    """
    Verify that RLS tests are running in a safe test environment.
    
    This fixture runs automatically before any tests and enforces:
    1. RLS_TESTS_ALLOWED must be explicitly set to 'true'
    2. SUPABASE_URL must exactly match TEST_SUPABASE_URL (whitelist)
    3. SUPABASE_URL must NOT contain production markers
    
    Raises:
        pytest.skip: If environment is not configured for RLS tests
        ValueError: If SUPABASE_URL appears to be a production environment
    """
    supabase_url = os.environ.get('SUPABASE_URL', '')
    test_supabase_url = os.environ.get('TEST_SUPABASE_URL', '')
    rls_tests_allowed = os.environ.get('RLS_TESTS_ALLOWED', 'false')
    
    if rls_tests_allowed != 'true':
        pytest.skip(
            "RLS_TESTS_ALLOWED must be set to 'true' to run RLS tests. "
            "This prevents accidental execution against production."
        )
    
    if not test_supabase_url:
        pytest.skip(
            "TEST_SUPABASE_URL must be set to run RLS tests. "
            "This whitelists the allowed test environment."
        )
    
    if supabase_url != test_supabase_url:
        pytest.skip(
            f"SUPABASE_URL ({supabase_url}) does not match TEST_SUPABASE_URL ({test_supabase_url}). "
            "RLS tests can only run against the whitelisted test environment."
        )
    
    production_markers = ['prod', 'production']
    for marker in production_markers:
        if marker in supabase_url.lower():
            raise ValueError(
                f"REFUSING TO RUN RLS TESTS AGAINST PRODUCTION! "
                f"SUPABASE_URL contains '{marker}': {supabase_url}"
            )
    
    test_markers = ['test', 'staging', 'dev']
    if not any(marker in supabase_url.lower() for marker in test_markers):
        print(f"\n⚠️  WARNING: SUPABASE_URL does not contain typical test markers (test/staging/dev): {supabase_url}")
        print(f"   Proceeding because TEST_SUPABASE_URL is explicitly set to this URL.")
    
    print(f"\n✅ RLS test environment verified: {supabase_url}")
>>>>>>> origin/main
