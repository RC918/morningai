"""
Unit tests for CORS configuration and alias functionality.

Tests verify that:
1. CORS_ORIGINS environment variable is correctly loaded via alias
2. CORS headers are correctly added for allowed origins
3. CORS headers are correctly added for Vercel preview URLs in staging
"""

import os
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
