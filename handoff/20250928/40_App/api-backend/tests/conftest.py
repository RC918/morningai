"""
Pytest configuration for API backend tests.

This module sets up the Python path, provides common fixtures,
and enables new fixtures from the fixtures/ directory.
"""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch

# Add src to path first for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from utils.repo_root import get_api_backend_root

# Setup Python path for imports
backend_dir = get_api_backend_root()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

orchestrator_dir = backend_dir.parent / "orchestrator"
if orchestrator_dir.exists() and str(orchestrator_dir) not in sys.path:
    sys.path.insert(0, str(orchestrator_dir))

# Enable fixtures from fixtures/ directory (RFC #619 Phase 1)
pytest_plugins = [
    "tests.fixtures.auth",
    "tests.fixtures.database",
]


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


@pytest.fixture(autouse=True)
def reset_settings_after_test():
    """
    Reset settings cache after each test to prevent cross-test pollution.
    
    This fixture runs automatically for all tests (autouse=True) and ensures
    that any settings modifications made during a test don't leak to other tests.
    
    Why this is needed:
    - Tests may modify environment variables to test different configurations
    - The settings module caches its instance for performance
    - Without reset, a test modifying JWT_SECRET_KEY could affect subsequent tests
    
    Part of PR0 (#2375) - Phase 0 stability guards.
    
    Note: We clear the cache WITHOUT re-validating because tests may have set
    invalid env values (e.g., ENVIRONMENT='test') that would fail validation.
    The next test that needs settings will trigger a fresh load with its own env.
    
    Example usage in tests:
        def test_custom_setting(monkeypatch):
            monkeypatch.setenv('JWT_SECRET_KEY', 'test-key')
            # Settings cache will be cleared after this test completes
    """
    yield
    # Clear settings cache after test completes (without re-validating)
    try:
        import common.config.settings as settings_module
        # Clear the cached instance without creating a new one
        # This avoids validation errors from invalid test env values
        settings_module._settings_instance = None
    except (ImportError, AttributeError):
        # Settings module not available or doesn't have _settings_instance
        pass


# Legacy fixtures (maintained for backward compatibility)
# These will be deprecated in RFC #619 Phase 2
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
