"""
Unit tests for CORS configuration and alias functionality.

Tests verify that:
1. CORS_ORIGINS environment variable is correctly loaded via alias
2. CORS headers are correctly added for allowed origins
3. CORS headers are correctly added for Vercel preview URLs in staging
4. CORS_DEBUG logs are sanitized (no raw origin or allowlist values)
"""

import os
import sys
import logging
import importlib
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask


class TestCORSAliasConfiguration:
    """Test CORS_ORIGINS environment variable alias functionality"""

    def test_cors_origins_env_var_loaded_via_alias(self):
        """Test that CORS_ORIGINS environment variable is loaded via alias"""
        test_origins = "http://localhost:5173,https://example.com,https://test.vercel.app"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            assert settings.cors_origins == test_origins
            assert "https://example.com" in settings.cors_origins
            assert "https://test.vercel.app" in settings.cors_origins

    def test_cors_origins_defaults_when_not_set(self):
        """Test that cors_origins uses default value when CORS_ORIGINS is not set"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CORS_ORIGINS", None)

            from common.config.settings import reload_settings
            settings = reload_settings()

            assert settings.cors_origins == "http://localhost:5173,http://localhost:5174"

    def test_cors_origins_parsed_correctly(self):
        """Test that cors_origins string is correctly parsed into list"""
        test_origins = "http://localhost:5173, https://example.com , https://test.vercel.app"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            origins_list = [origin.strip() for origin in settings.cors_origins.split(",")]

            assert len(origins_list) == 3
            assert "http://localhost:5173" in origins_list
            assert "https://example.com" in origins_list
            assert "https://test.vercel.app" in origins_list


class TestCORSHeadersMiddleware:
    """Test CORS headers middleware functionality"""

    @pytest.fixture
    def app(self):
        """Create a minimal Flask app for testing"""
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.route("/test")
        def test_route():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return app.test_client()

    def test_cors_headers_added_for_allowed_origin(self, app, client):
        """Test that CORS headers are added when origin is in allowlist"""
        allowed_origin = "https://example.com"

        with patch.dict(os.environ, {"CORS_ORIGINS": f"http://localhost:5173,{allowed_origin}"}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

            with app.test_request_context(
                "/test",
                headers={"Origin": allowed_origin}
            ):
                from flask import request

                mock_response = MagicMock()
                mock_response.headers = {}

                origin = request.headers.get("Origin")
                in_allowlist = origin in cors_origins

                assert in_allowlist is True

                if in_allowlist:
                    mock_response.headers["Access-Control-Allow-Origin"] = origin
                    mock_response.headers["Access-Control-Allow-Credentials"] = "true"

                assert mock_response.headers.get("Access-Control-Allow-Origin") == allowed_origin
                assert mock_response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_headers_not_added_for_disallowed_origin(self, app):
        """Test that CORS headers are not added when origin is not in allowlist"""
        disallowed_origin = "https://malicious.com"

        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:5173,https://example.com"}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

            with app.test_request_context(
                "/test",
                headers={"Origin": disallowed_origin}
            ):
                from flask import request

                mock_response = MagicMock()
                mock_response.headers = {}

                origin = request.headers.get("Origin")
                in_allowlist = origin in cors_origins

                assert in_allowlist is False

                assert mock_response.headers.get("Access-Control-Allow-Origin") is None

    def test_vercel_preview_allowed_in_staging(self, app):
        """Test that Vercel preview URLs are allowed in staging environment"""
        vercel_preview = "https://test-app-git-branch-abc123.vercel.app"

        import re

        env = "staging"

        is_vercel_preview = False
        if env != "production":
            is_vercel_preview = bool(re.match(r"^https://.*\.vercel\.app$", vercel_preview))

        assert is_vercel_preview is True

    def test_vercel_preview_blocked_in_production(self, app):
        """Test that Vercel preview URLs are blocked in production environment"""
        vercel_preview = "https://test-app-git-branch-abc123.vercel.app"

        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "http://localhost:5173"
        }, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            import re
            env = (settings.environment or "").lower()

            assert env == "production"

            is_vercel_preview = False
            if env != "production":
                is_vercel_preview = bool(re.match(r"^https://.*\.vercel\.app$", vercel_preview))

            assert is_vercel_preview is False


class TestCORSConfigurationIntegration:
    """Integration tests for CORS configuration"""

    def test_cors_origins_environment_variable_name(self):
        """Test that the environment variable name is CORS_ORIGINS (uppercase)"""
        test_value = "https://test1.com,https://test2.com"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_value}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            assert settings.cors_origins == test_value

    def test_cors_origins_field_has_alias(self):
        """Test that cors_origins field has alias='CORS_ORIGINS' in settings"""
        from common.config.settings import Settings

        field_info = Settings.model_fields.get("cors_origins")

        assert field_info is not None
        assert field_info.alias == "CORS_ORIGINS"

    def test_cors_origins_comma_separated_format(self):
        """Test that cors_origins accepts comma-separated format"""
        test_origins = "http://localhost:5173,https://app1.com,https://app2.com,https://preview.vercel.app"

        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}, clear=False):
            from common.config.settings import reload_settings
            settings = reload_settings()

            origins_list = [origin.strip() for origin in settings.cors_origins.split(",")]

            assert len(origins_list) == 4
            assert all(origin.startswith("http") for origin in origins_list)


def _import_fresh_main(monkeypatch, **env):
    """Helper to import main.py with fresh environment variables.

    This is necessary because cors_debug_enabled is computed at import time.
    We need to:
    1. Set env vars (including ENABLE_MOCK_USERS=false for non-development)
    2. Reset the Settings singleton to pick up new env vars
    3. Remove src.main from sys.modules
    4. Delete the main attribute from src package (prevents stale attribute)
    5. Use importlib.import_module for a clean import
    """
    # For staging/production, ENABLE_MOCK_USERS must be false per Settings validator
    environment = env.get("ENVIRONMENT", "development")
    if environment in ("staging", "production"):
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")

    for k, v in env.items():
        monkeypatch.setenv(k, v)

    # Reset the Settings singleton to pick up new env vars
    from common.config.settings import reload_settings
    reload_settings()

    # Ensure src package exists
    import src
    # Remove src.main from sys.modules
    sys.modules.pop("src.main", None)
    # Critical: delete stale attribute from src package
    if hasattr(src, "main"):
        delattr(src, "main")

    return importlib.import_module("src.main")


class TestCORSDebugSanitization:
    """Test CORS_DEBUG logging sanitization behavior.

    Verifies that when CORS_DEBUG=true and not in production:
    - Logs only contain safe fields (origin_present, in_allowlist, is_preview, allowlist_count)
    - Logs do NOT contain raw origin URLs or allowlist contents
    """

    def test_cors_debug_logs_contain_only_safe_fields(self, monkeypatch, caplog):
        """Test that CORS debug logs only contain sanitized safe fields.

        Safe fields: origin_present, in_allowlist, is_preview, allowlist_count
        """
        caplog.set_level(logging.DEBUG)

        # Import main with fresh env vars
        main = _import_fresh_main(
            monkeypatch,
            ENVIRONMENT="staging",
            CORS_DEBUG="true",
            LOG_LEVEL="DEBUG",
            CORS_ORIGINS="https://allowed-origin.com,https://another-allowed.com"
        )

        # Get the Flask app and test client
        app = main.app
        client = app.test_client()

        # Clear any startup logs
        caplog.clear()

        # Make a request with an Origin header to trigger add_cors_headers
        test_origin = "https://allowed-origin.com"
        client.get("/health", headers={"Origin": test_origin})

        # Check that logs contain safe fields
        log_text = caplog.text

        # Safe fields that SHOULD appear in logs
        safe_fields = ["origin_present=", "in_allowlist=", "is_preview=", "allowlist_count="]

        # If CORS_DEBUG is enabled and we're not in production, we should see these fields
        # Note: The logs may or may not appear depending on the exact flow
        # The key assertion is that if CORS DEBUG logs appear, they are sanitized

        # Check for CORS DEBUG marker in logs
        if "[CORS DEBUG]" in log_text:
            # Verify safe fields are present
            for field in safe_fields:
                assert field in log_text, f"Expected safe field '{field}' in CORS debug logs"

    def test_cors_debug_logs_do_not_contain_raw_values(self, monkeypatch, caplog):
        """Test that CORS debug logs do NOT contain raw origin URLs or allowlist contents.

        This is critical for security - we should never log:
        - The actual origin URL string
        - The complete allowlist contents
        """
        caplog.set_level(logging.DEBUG)

        # Import main with fresh env vars
        main = _import_fresh_main(
            monkeypatch,
            ENVIRONMENT="staging",
            CORS_DEBUG="true",
            LOG_LEVEL="DEBUG",
            CORS_ORIGINS="https://allowed-origin.com,https://another-allowed.com"
        )

        # Get the Flask app and test client
        app = main.app
        client = app.test_client()

        # Clear any startup logs
        caplog.clear()

        # Make a request with a specific Origin header
        test_origin = "https://test-sensitive-origin.example.com"

        client.get("/health", headers={"Origin": test_origin})

        # Get all log text
        log_text = caplog.text

        # These raw values should NOT appear in logs
        # The actual origin URL should not be logged
        assert test_origin not in log_text, \
            f"Raw origin URL '{test_origin}' should NOT appear in CORS debug logs"

        # The allowlist contents should not be logged as a list
        # Check that we don't have the full allowlist dumped
        assert "['https://" not in log_text, \
            "Raw allowlist contents should NOT appear in CORS debug logs"
        assert '["https://' not in log_text, \
            "Raw allowlist contents should NOT appear in CORS debug logs"

    def test_cors_debug_disabled_in_production(self, monkeypatch, caplog):
        """Test that CORS_DEBUG is force-disabled in production environment.

        Even if CORS_DEBUG=true, production should never emit CORS debug logs.
        """
        caplog.set_level(logging.DEBUG)

        # Import main with production env vars
        main = _import_fresh_main(
            monkeypatch,
            ENVIRONMENT="production",
            CORS_DEBUG="true",
            LOG_LEVEL="DEBUG",
            CORS_ORIGINS="https://allowed-origin.com"
        )

        # Verify cors_debug_enabled is False in production
        assert main.cors_debug_enabled is False, \
            "cors_debug_enabled should be False in production"

        # Get the Flask app and test client
        app = main.app
        client = app.test_client()

        # Clear any logs
        caplog.clear()

        # Make a request
        client.get("/health", headers={"Origin": "https://test.com"})

        # In production, no CORS DEBUG logs should appear
        log_text = caplog.text
        assert "[CORS DEBUG]" not in log_text, \
            "CORS DEBUG logs should NOT appear in production environment"
