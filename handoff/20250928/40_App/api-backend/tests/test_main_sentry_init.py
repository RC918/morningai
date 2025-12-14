import importlib
import os
import sys
from unittest.mock import patch, MagicMock, Mock


def test_main_import_triggers_sentry_block(monkeypatch):
    # 設一個 dummy DSN，避免網路呼叫（sentry_sdk.init 只做本地配置）
    monkeypatch.setenv("SENTRY_DSN", "https://examplePublicKey@o0.ingest.sentry.io/0")
    # 確保每次都重新執行 module-level 邏輯
    if "src.main" in sys.modules:
        del sys.modules["src.main"]
    m = importlib.import_module("src.main")
    # 斷言 app 物件存在（代表 Flask app 與 blueprint 註冊流程已執行）
    assert hasattr(m, "app")


class TestAsBoolFunction:
    """Test the _as_bool helper function behavior."""

    def test_as_bool_with_true_string(self):
        """Test _as_bool returns True for truthy string values."""
        from src.main import _as_bool

        assert _as_bool("true") is True
        assert _as_bool("True") is True
        assert _as_bool("TRUE") is True
        assert _as_bool("1") is True
        assert _as_bool("yes") is True
        assert _as_bool("Yes") is True
        assert _as_bool("on") is True
        assert _as_bool("ON") is True

    def test_as_bool_with_false_string(self):
        """Test _as_bool returns False for falsy string values."""
        from src.main import _as_bool

        assert _as_bool("false") is False
        assert _as_bool("False") is False
        assert _as_bool("0") is False
        assert _as_bool("no") is False
        assert _as_bool("off") is False
        assert _as_bool("") is False
        assert _as_bool("random") is False

    def test_as_bool_with_none(self):
        """Test _as_bool returns False for None."""
        from src.main import _as_bool

        assert _as_bool(None) is False

    def test_as_bool_with_bool(self):
        """Test _as_bool returns the same value for bool input."""
        from src.main import _as_bool

        assert _as_bool(True) is True
        assert _as_bool(False) is False

    def test_as_bool_with_whitespace(self):
        """Test _as_bool handles whitespace correctly."""
        from src.main import _as_bool

        assert _as_bool("  true  ") is True
        assert _as_bool("  1  ") is True
        assert _as_bool("  yes  ") is True


class TestSentryInitializationLogic:
    """Test Sentry initialization logic with different environment combinations.
    
    NOTE: As of PR1f, Sentry initialization logic has been moved to src/extensions/sentry.py.
    These tests now test the init_sentry() function directly instead of checking module-level
    variables in src.main. This is the correct approach as TESTING, DISABLE_SENTRY_FOR_TESTS,
    disable_sentry, and current_env are implementation details, not part of the public API.
    """

    def _create_mock_settings(self, sentry_dsn="https://test@sentry.io/123",
                               environment="development", app_version="8.0.0"):
        """Create a mock app_settings object for testing."""
        mock_settings = Mock()
        mock_settings.sentry_dsn = sentry_dsn
        mock_settings.environment = environment
        mock_settings.app_version = app_version
        return mock_settings

    def test_sentry_disabled_when_testing_flag_set_in_development(self, monkeypatch):
        """Test Sentry is disabled when TESTING=true in development environment."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        mock_settings = self._create_mock_settings(environment="development")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            # Sentry should NOT be initialized when TESTING is true in development
            mock_sentry.init.assert_not_called()
            assert result is None

    def test_sentry_disabled_when_disable_sentry_for_tests_flag_set(self, monkeypatch):
        """Test Sentry is disabled when DISABLE_SENTRY_FOR_TESTS=true."""
        monkeypatch.setenv("DISABLE_SENTRY_FOR_TESTS", "true")
        monkeypatch.delenv("TESTING", raising=False)

        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        mock_settings = self._create_mock_settings(environment="development")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result = init_sentry(mock_settings, _as_bool)

            # Sentry should NOT be initialized when DISABLE_SENTRY_FOR_TESTS is true
            mock_sentry.init.assert_not_called()
            assert result is None

    def test_sentry_enabled_in_production_despite_testing_flag(self, monkeypatch):
        """Test Sentry remains enabled in production even when TESTING=true (production guard)."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        mock_settings = self._create_mock_settings(environment="production")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                result = init_sentry(mock_settings, _as_bool)

                # Production guard should force Sentry to be enabled
                mock_sentry.init.assert_called_once()
                assert result == "https://test@sentry.io/123"

    def test_sentry_enabled_when_no_flags_set(self, monkeypatch):
        """Test Sentry is enabled when no disable flags are set."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        mock_settings = self._create_mock_settings(environment="staging")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                result = init_sentry(mock_settings, _as_bool)

                # Sentry should be initialized when no disable flags are set
                mock_sentry.init.assert_called_once()
                assert result == "https://test@sentry.io/123"

    def test_environment_defaults_to_development_fallback(self, monkeypatch):
        """Test that init_sentry uses 'development' as fallback when environment is falsy."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        # Create settings with None environment to test fallback
        mock_settings = self._create_mock_settings(environment=None)

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            with patch("src.extensions.sentry.FlaskIntegration"):
                result = init_sentry(mock_settings, _as_bool)

                # Verify sentry_sdk.init was called with environment="development"
                mock_sentry.init.assert_called_once()
                call_kwargs = mock_sentry.init.call_args[1]
                assert call_kwargs["environment"] == "development"

    def test_both_flags_can_disable_sentry(self, monkeypatch):
        """Test that either TESTING or DISABLE_SENTRY_FOR_TESTS can disable Sentry."""
        from src.extensions.sentry import init_sentry
        from src.utils.helpers import _as_bool

        mock_settings = self._create_mock_settings(environment="development")

        # Test with only TESTING
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result1 = init_sentry(mock_settings, _as_bool)
            mock_sentry.init.assert_not_called()
            assert result1 is None

        # Test with only DISABLE_SENTRY_FOR_TESTS
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.setenv("DISABLE_SENTRY_FOR_TESTS", "true")

        with patch("src.extensions.sentry.sentry_sdk") as mock_sentry:
            result2 = init_sentry(mock_settings, _as_bool)
            mock_sentry.init.assert_not_called()
            assert result2 is None
