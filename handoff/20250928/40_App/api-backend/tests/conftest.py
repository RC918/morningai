"""
Pytest configuration for API backend tests.

This module sets up the Python path and provides common fixtures for all tests.
"""
import sys
import os
from pathlib import Path
import pytest

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
