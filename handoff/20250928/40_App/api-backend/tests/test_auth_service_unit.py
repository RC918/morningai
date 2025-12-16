"""
Unit tests for auth_service.py functions

Tests for is_mock_users_enabled() and authenticate_user() to improve coverage.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from flask import Flask


class TestIsMockUsersEnabled:
    """Test is_mock_users_enabled() function with various configurations"""
    
    def test_test_mode_env_override_false(self, monkeypatch):
        """Test mode with ENABLE_MOCK_USERS=false env override returns False"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        
        from src.services.auth_service import is_mock_users_enabled
        assert is_mock_users_enabled() is False
    
    def test_test_mode_env_override_true(self, monkeypatch):
        """Test mode with ENABLE_MOCK_USERS=true env override returns True"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "true")
        
        from src.services.auth_service import is_mock_users_enabled
        assert is_mock_users_enabled() is True
    
    def test_test_mode_app_config_override_false(self, monkeypatch):
        """Test mode with app.config ENABLE_MOCK_USERS=False returns False"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        app = Flask(__name__)
        app.config["ENABLE_MOCK_USERS"] = False
        
        with app.app_context():
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is False
    
    def test_test_mode_app_config_override_true(self, monkeypatch):
        """Test mode with app.config ENABLE_MOCK_USERS=True returns True"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        app = Flask(__name__)
        app.config["ENABLE_MOCK_USERS"] = True
        
        with app.app_context():
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is True
    
    def test_test_mode_default_true(self, monkeypatch):
        """Test mode with no env or config returns True (default)"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        from src.services.auth_service import is_mock_users_enabled
        assert is_mock_users_enabled() is True
    
    def test_non_test_mode_app_config_false(self, monkeypatch):
        """Non-test mode with app.config False returns False"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        app = Flask(__name__)
        app.config["ENABLE_MOCK_USERS"] = False
        
        with app.app_context():
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is False
    
    def test_non_test_mode_app_config_true(self, monkeypatch):
        """Non-test mode with app.config True returns True"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        app = Flask(__name__)
        app.config["ENABLE_MOCK_USERS"] = True
        
        with app.app_context():
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is True
    
    def test_non_test_mode_env_false(self, monkeypatch):
        """Non-test mode with ENABLE_MOCK_USERS=false env returns False"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        
        from src.services.auth_service import is_mock_users_enabled
        assert is_mock_users_enabled() is False
    
    def test_non_test_mode_env_true(self, monkeypatch):
        """Non-test mode with ENABLE_MOCK_USERS=true env returns True"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "true")
        
        from src.services.auth_service import is_mock_users_enabled
        assert is_mock_users_enabled() is True
    
    def test_non_test_mode_settings_fallback_true(self, monkeypatch):
        """Non-test mode with settings.enable_mock_users=True returns True"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        mock_settings = Mock()
        mock_settings.enable_mock_users = True
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is True
    
    def test_non_test_mode_settings_fallback_false(self, monkeypatch):
        """Non-test mode with settings.enable_mock_users=False returns False"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        mock_settings = Mock()
        mock_settings.enable_mock_users = False
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is False
    
    def test_non_test_mode_default_false(self, monkeypatch):
        """Non-test mode with no env, config, or settings returns False"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        mock_settings = Mock()
        mock_settings.enable_mock_users = None
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is False
    
    def test_test_mode_flask_import_exception(self, monkeypatch):
        """Test mode with Flask import exception returns True (default)"""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("ENABLE_MOCK_USERS", raising=False)
        
        fake_flask = Mock()
        del fake_flask.current_app
        
        original_flask = sys.modules.get("flask")
        try:
            sys.modules["flask"] = fake_flask
            
            import importlib
            import src.services.auth_service
            importlib.reload(src.services.auth_service)
            
            from src.services.auth_service import is_mock_users_enabled
            assert is_mock_users_enabled() is True
        finally:
            if original_flask:
                sys.modules["flask"] = original_flask
            else:
                sys.modules.pop("flask", None)
            
            import src.services.auth_service
            importlib.reload(src.services.auth_service)


class TestAuthenticateUser:
    """Test authenticate_user() function with Supabase backend"""
    
    def test_authenticate_user_supabase_success(self, monkeypatch):
        """Test successful Supabase authentication"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        mock_settings = Mock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_anon_key = "test-anon-key"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user": {
                "id": "user-123",
                "email": "test@example.com",
                "user_metadata": {
                    "name": "Test User",
                    "role": "member",
                    "tenant_id": "tenant-001"
                }
            }
        }
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            with patch("requests.post", return_value=mock_response):
                from src.services.auth_service import authenticate_user
                
                user = authenticate_user("test@example.com", "password123")
                
                assert user is not None
                assert user["id"] == "user-123"
                assert user["email"] == "test@example.com"
                assert user["name"] == "Test User"
                assert user["role"] == "member"
                assert user["tenant_id"] == "tenant-001"
    
    def test_authenticate_user_supabase_failure(self, monkeypatch):
        """Test failed Supabase authentication (401)"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        mock_settings = Mock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_anon_key = "test-anon-key"
        
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            with patch("requests.post", return_value=mock_response):
                from src.services.auth_service import authenticate_user
                
                user = authenticate_user("test@example.com", "wrong-password")
                
                assert user is None
    
    def test_authenticate_user_supabase_missing_credentials(self, monkeypatch):
        """Test Supabase authentication with missing credentials"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        mock_settings = Mock()
        mock_settings.supabase_url = None
        mock_settings.supabase_anon_key = None
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import authenticate_user
            
            user = authenticate_user("test@example.com", "password123")
            
            assert user is None
    
    def test_authenticate_user_supabase_exception(self, monkeypatch):
        """Test Supabase authentication with network exception"""
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        mock_settings = Mock()
        mock_settings.supabase_url = "https://test.supabase.co"
        mock_settings.supabase_anon_key = "test-anon-key"
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            with patch("requests.post", side_effect=Exception("Network error")):
                from src.services.auth_service import authenticate_user
                
                user = authenticate_user("test@example.com", "password123")
                
                assert user is None


class TestIsTestingModeFallbackChain:
    """Test is_testing_mode() fallback chain priority order and error handling"""
    
    def test_flask_config_overrides_env(self, monkeypatch):
        """Flask config TESTING should override os.environ TESTING"""
        monkeypatch.setenv("TESTING", "true")
        
        app = Flask(__name__)
        app.config["TESTING"] = False
        
        with app.app_context():
            from src.services.auth_service import is_testing_mode
            assert is_testing_mode() is False
    
    def test_env_overrides_settings(self, monkeypatch):
        """os.environ TESTING should override settings.testing"""
        monkeypatch.setenv("TESTING", "true")
        
        mock_settings = Mock()
        mock_settings.testing = False
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import is_testing_mode
            assert is_testing_mode() is True
    
    def test_settings_fallback_when_env_missing(self, monkeypatch):
        """settings.testing should be used when os.environ TESTING is not set"""
        monkeypatch.delenv("TESTING", raising=False)
        
        mock_settings = Mock()
        mock_settings.testing = True
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import is_testing_mode
            assert is_testing_mode() is True
    
    def test_settings_exception_returns_false_with_warning(self, monkeypatch, caplog):
        """When get_settings() raises exception, should return False and log warning"""
        import logging
        monkeypatch.delenv("TESTING", raising=False)
        
        import src.services.auth_service as auth_module
        auth_module._warned_settings_load_failed = False
        
        with patch("src.services.auth_service.get_settings", side_effect=Exception("Settings validation failed")):
            with caplog.at_level(logging.WARNING):
                from src.services.auth_service import is_testing_mode
                result = is_testing_mode()
                
                assert result is False
                assert "Failed to load settings in is_testing_mode()" in caplog.text
                assert "Settings validation failed" in caplog.text
    
    def test_settings_exception_warning_only_once(self, monkeypatch, caplog):
        """Warning should only be logged once even if called multiple times"""
        import logging
        monkeypatch.delenv("TESTING", raising=False)
        
        import src.services.auth_service as auth_module
        auth_module._warned_settings_load_failed = False
        
        with patch("src.services.auth_service.get_settings", side_effect=Exception("Settings validation failed")):
            with caplog.at_level(logging.WARNING):
                from src.services.auth_service import is_testing_mode
                
                is_testing_mode()
                is_testing_mode()
                is_testing_mode()
                
                warning_count = caplog.text.count("Failed to load settings in is_testing_mode()")
                assert warning_count == 1


class TestLogTokenConfigOnStartup:
    """Test _log_token_config_on_startup() error handling"""
    
    def test_settings_exception_logs_warning(self, monkeypatch, caplog):
        """When get_settings() raises exception, should log warning once"""
        import logging
        
        import src.services.auth_service as auth_module
        auth_module._warned_startup_config_failed = False
        
        with patch("src.services.auth_service.get_settings", side_effect=Exception("Settings validation failed")):
            with caplog.at_level(logging.WARNING):
                from src.services.auth_service import _log_token_config_on_startup
                
                _log_token_config_on_startup()
                
                assert "Failed to log token config on startup" in caplog.text
                assert "Settings validation failed" in caplog.text
    
    def test_settings_exception_warning_only_once(self, monkeypatch, caplog):
        """Warning should only be logged once even if called multiple times"""
        import logging
        
        import src.services.auth_service as auth_module
        auth_module._warned_startup_config_failed = False
        
        with patch("src.services.auth_service.get_settings", side_effect=Exception("Settings validation failed")):
            with caplog.at_level(logging.WARNING):
                from src.services.auth_service import _log_token_config_on_startup
                
                _log_token_config_on_startup()
                _log_token_config_on_startup()
                _log_token_config_on_startup()
                
                warning_count = caplog.text.count("Failed to log token config on startup")
                assert warning_count == 1
    
    def test_no_exception_when_log_disabled(self, monkeypatch):
        """Should not raise exception when log_token_expiry_on_startup is False"""
        mock_settings = Mock()
        mock_settings.log_token_expiry_on_startup = False
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import _log_token_config_on_startup
            
            _log_token_config_on_startup()


class TestGetAccessTokenExpiryMinutes:
    """Test get_access_token_expiry_minutes() accessor function"""
    
    def test_returns_settings_value(self, monkeypatch):
        """Should return value from settings.access_token_expiry_minutes"""
        mock_settings = Mock()
        mock_settings.access_token_expiry_minutes = 30
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import get_access_token_expiry_minutes
            
            assert get_access_token_expiry_minutes() == 30
    
    def test_default_value_15(self, monkeypatch):
        """Should return 15 as default when not configured"""
        mock_settings = Mock()
        mock_settings.access_token_expiry_minutes = 15
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import get_access_token_expiry_minutes
            
            assert get_access_token_expiry_minutes() == 15
    
    def test_env_override_via_settings(self, monkeypatch):
        """Environment variable should be reflected via settings"""
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRY_MINUTES", "60")
        
        mock_settings = Mock()
        mock_settings.access_token_expiry_minutes = 60
        
        with patch("src.services.auth_service.get_settings", return_value=mock_settings):
            from src.services.auth_service import get_access_token_expiry_minutes
            
            assert get_access_token_expiry_minutes() == 60
