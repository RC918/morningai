"""Patch Target Contract Tests for Phase 1 refactoring.

These tests verify that patch targets work correctly after refactoring.
When symbols are moved to new modules and re-exported from src.main,
tests should still be able to patch them via src.main.

Part of Phase 1 pre-work for main.py refactoring.
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import pytest
from unittest.mock import patch


class TestPatchTargets:
    """Verify patch targets work correctly after refactoring."""
    
    def test_patch_as_bool_via_main(self):
        """Verify _as_bool can be patched via src.main."""
        with patch('src.main._as_bool', return_value=True):
            from src.main import _as_bool
            # The patched function should return True regardless of input
            assert _as_bool('false') is True
    
    def test_patch_backend_services_available(self):
        """Verify BACKEND_SERVICES_AVAILABLE can be patched."""
        with patch('src.main.BACKEND_SERVICES_AVAILABLE', False):
            import src.main
            # Need to access via module to see patched value
            assert src.main.BACKEND_SERVICES_AVAILABLE is False
    
    def test_patch_phase_456_available(self):
        """Verify PHASE_456_AVAILABLE can be patched."""
        with patch('src.main.PHASE_456_AVAILABLE', False):
            import src.main
            # Need to access via module to see patched value
            assert src.main.PHASE_456_AVAILABLE is False
    
    def test_patch_security_available(self):
        """Verify SECURITY_AVAILABLE can be patched."""
        with patch('src.main.SECURITY_AVAILABLE', False):
            import src.main
            # Need to access via module to see patched value
            assert src.main.SECURITY_AVAILABLE is False
    
    def test_patch_is_vercel_preview(self):
        """Verify is_vercel_preview can be patched via src.main."""
        with patch('src.main.is_vercel_preview', return_value=True):
            from src.main import is_vercel_preview
            assert is_vercel_preview('test-origin') is True
    
    def test_patch_add_cors_headers(self):
        """Verify add_cors_headers can be patched via src.main."""
        mock_response = object()
        with patch('src.main.add_cors_headers', return_value=mock_response):
            from src.main import add_cors_headers
            result = add_cors_headers(None)
            assert result is mock_response
    
    def test_patch_get_health_payload(self):
        """Verify get_health_payload can be patched via src.main."""
        mock_payload = {'status': 'mocked'}
        with patch('src.main.get_health_payload', return_value=mock_payload):
            from src.main import get_health_payload
            result = get_health_payload()
            assert result == mock_payload
    
    def test_patch_handle_exception(self):
        """Verify handle_exception can be patched via src.main."""
        mock_response = ('mocked', 500)
        with patch('src.main.handle_exception', return_value=mock_response):
            from src.main import handle_exception
            result = handle_exception(Exception('test'))
            assert result == mock_response
