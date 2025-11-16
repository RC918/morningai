"""
Pytest configuration and fixtures for RLS testing and unit tests.

This module provides:
1. Session-level safety guards to prevent accidental execution of destructive RLS tests
2. Shared mock fixtures for unit tests (Flask, auth_middleware, etc.)
"""

import os
import pytest
from unittest.mock import MagicMock
import sys
from pathlib import Path


class MockJsonifyResult:
    """Mock Flask jsonify result that supports get_json() method."""
    def __init__(self, data):
        self.data = data
    
    def get_json(self):
        return self.data
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __contains__(self, key):
        return key in self.data


def mock_jsonify(data):
    """Mock Flask jsonify function."""
    return MockJsonifyResult(data)


# Setup Flask and common module mocks at module level (before test collection)
if 'flask' not in sys.modules or not isinstance(sys.modules.get('flask'), MagicMock):
    mock_flask = MagicMock()
    mock_flask.jsonify = mock_jsonify
    
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.cookies = {}
    mock_flask.request = mock_request
    
    mock_g = MagicMock()
    mock_flask.g = mock_g
    
    sys.modules['flask'] = mock_flask

if 'common' not in sys.modules or not isinstance(sys.modules.get('common'), MagicMock):
    sys.modules['common'] = MagicMock()
    sys.modules['common.config'] = MagicMock()
    sys.modules['common.config.settings'] = MagicMock()
    
    mock_settings = MagicMock()
    mock_settings.jwt_secret_key = 'test-secret-key-for-testing'
    sys.modules['common.config.settings'].get_settings.return_value = mock_settings

middleware_path = str(Path(__file__).parent.parent / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src')
if middleware_path not in sys.path:
    sys.path.insert(0, middleware_path)


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


@pytest.fixture(autouse=True)
def reset_flask_request_mock():
    """
    Reset Flask request mock before each test.
    
    This fixture runs before each test and ensures that the mock request object
    is in a clean state, preventing test pollution.
    
    IMPORTANT: We modify the existing mock_request object in-place instead of
    replacing it, because auth_middleware has a reference to the original object
    from its module-level import (from flask import request).
    """
    if 'flask' in sys.modules:
        mock_flask = sys.modules['flask']
        
        mock_flask.request.headers = {}
        mock_flask.request.cookies = {}
        
        mock_flask.g = MagicMock()
    
    yield
