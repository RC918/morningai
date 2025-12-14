"""Import Contract Tests for Phase 1 refactoring.

These tests verify that all public symbols remain importable from src.main
during and after the Phase 1 refactoring. This ensures backward compatibility
for any external code that imports from src.main.

Part of Phase 1 pre-work for main.py refactoring.
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import pytest


class TestImportContract:
    """Verify all public symbols remain importable from src.main.
    
    This test ensures backward compatibility during Phase 1 refactoring.
    Any symbol listed here MUST remain importable from src.main even after
    being moved to a new module (via re-export).
    """
    
    # Public symbols that MUST remain importable from src.main
    PUBLIC_SYMBOLS = [
        'app',                      # Flask app instance
        '_as_bool',                 # Helper function
        'is_vercel_preview',        # CORS helper
        'add_cors_headers',         # CORS middleware
        'before_send',              # Sentry hook
        'get_health_payload',       # Health check helper
        'handle_exception',         # Error handler
        'BACKEND_SERVICES_AVAILABLE',  # Feature flag
        'PHASE_456_AVAILABLE',      # Feature flag
        'SECURITY_AVAILABLE',       # Feature flag
        'SENTRY_DSN',               # Config value
    ]
    
    @pytest.mark.parametrize('symbol', PUBLIC_SYMBOLS)
    def test_symbol_importable(self, symbol):
        """Verify each public symbol can be imported from src.main."""
        import src.main
        assert hasattr(src.main, symbol), f"Symbol '{symbol}' not found in src.main"
    
    def test_app_is_flask_instance(self):
        """Verify app is a Flask instance."""
        from src.main import app
        from flask import Flask
        assert isinstance(app, Flask)
    
    def test_backend_services_is_bool(self):
        """Verify BACKEND_SERVICES_AVAILABLE is a boolean."""
        from src.main import BACKEND_SERVICES_AVAILABLE
        assert isinstance(BACKEND_SERVICES_AVAILABLE, bool)
    
    def test_phase_456_is_bool(self):
        """Verify PHASE_456_AVAILABLE is a boolean."""
        from src.main import PHASE_456_AVAILABLE
        assert isinstance(PHASE_456_AVAILABLE, bool)
    
    def test_security_is_bool(self):
        """Verify SECURITY_AVAILABLE is a boolean."""
        from src.main import SECURITY_AVAILABLE
        assert isinstance(SECURITY_AVAILABLE, bool)
    
    def test_as_bool_is_callable(self):
        """Verify _as_bool is a callable function."""
        from src.main import _as_bool
        assert callable(_as_bool)
    
    def test_is_vercel_preview_is_callable(self):
        """Verify is_vercel_preview is a callable function."""
        from src.main import is_vercel_preview
        assert callable(is_vercel_preview)
    
    def test_add_cors_headers_is_callable(self):
        """Verify add_cors_headers is a callable function."""
        from src.main import add_cors_headers
        assert callable(add_cors_headers)
    
    def test_before_send_is_callable(self):
        """Verify before_send is a callable function."""
        from src.main import before_send
        assert callable(before_send)
    
    def test_get_health_payload_is_callable(self):
        """Verify get_health_payload is a callable function."""
        from src.main import get_health_payload
        assert callable(get_health_payload)
    
    def test_handle_exception_is_callable(self):
        """Verify handle_exception is a callable function."""
        from src.main import handle_exception
        assert callable(handle_exception)
