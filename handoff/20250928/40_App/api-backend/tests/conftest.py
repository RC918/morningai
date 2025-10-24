"""
Pytest configuration for API backend tests.

This module sets up the Python path and provides common fixtures for all tests.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

orchestrator_dir = backend_dir.parent / "orchestrator"
if orchestrator_dir.exists() and str(orchestrator_dir) not in sys.path:
    sys.path.insert(0, str(orchestrator_dir))


@pytest.fixture(autouse=True)
def disable_sentry_in_tests(monkeypatch):
    """
    Disable Sentry during tests to prevent test errors from being sent to production.
    
    This fixture runs automatically for all tests (autouse=True) and removes
    SENTRY_DSN from the environment, effectively disabling Sentry error reporting.
    
    Why this is needed:
    - Tests intentionally trigger errors to verify error handling
    - These test errors should not pollute production Sentry
    - Example: test_get_current_tenant_server_error triggers "Database error"
    """
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.setenv("SENTRY_ENABLED", "false")
    monkeypatch.setenv("TESTING", "true")


@pytest.fixture
def admin_token():
    """Generate admin JWT token for testing"""
    from src.middleware.auth_middleware import create_admin_token
    return create_admin_token()


@pytest.fixture
def analyst_token():
    """Generate analyst JWT token for testing"""
    from src.middleware.auth_middleware import create_analyst_token
    return create_analyst_token()


@pytest.fixture
def user_token():
    """Generate user JWT token for testing"""
    from src.middleware.auth_middleware import create_user_token
    return create_user_token()


@pytest.fixture
def auth_headers_admin(admin_token):
    """Generate Authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_analyst(analyst_token):
    """Generate Authorization headers with analyst token"""
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def auth_headers_user(user_token):
    """Generate Authorization headers with user token"""
    return {"Authorization": f"Bearer {user_token}"}
