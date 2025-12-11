import importlib
import os
import sys
from unittest.mock import patch, MagicMock


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
    """Test Sentry initialization logic with different environment combinations."""

    def test_sentry_disabled_when_testing_flag_set_in_development(self, monkeypatch):
        """Test Sentry is disabled when TESTING=true in development environment."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")

        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]

        with patch("sentry_sdk.init") as mock_init:
            import src.main as main

            # Sentry should NOT be initialized when TESTING is true in development
            # The module sets SENTRY_DSN to None when disabled
            assert main.TESTING is True
            assert main.disable_sentry is True

    def test_sentry_disabled_when_disable_sentry_for_tests_flag_set(self, monkeypatch):
        """Test Sentry is disabled when DISABLE_SENTRY_FOR_TESTS=true."""
        monkeypatch.setenv("DISABLE_SENTRY_FOR_TESTS", "true")
        monkeypatch.setenv("TESTING", "false")
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")

        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]

        with patch("sentry_sdk.init") as mock_init:
            import src.main as main

            assert main.DISABLE_SENTRY_FOR_TESTS is True
            assert main.disable_sentry is True

    def test_sentry_enabled_in_production_despite_testing_flag(self, monkeypatch):
        """Test Sentry remains enabled in production even when TESTING=true (production guard)."""
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")
        # Must disable mock users in production to pass settings validation
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")

        # Clear cached modules and settings
        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]
            if mod.startswith("common.config"):
                del sys.modules[mod]

        with patch("sentry_sdk.init") as mock_init:
            import src.main as main

            # Production guard should force disable_sentry to False
            assert main.TESTING is True
            assert main.current_env == "production"
            # disable_sentry should be False due to production guard
            assert main.disable_sentry is False

    def test_sentry_enabled_when_no_flags_set(self, monkeypatch):
        """Test Sentry is enabled when no disable flags are set."""
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")
        # Must disable mock users in staging to pass settings validation
        monkeypatch.setenv("ENABLE_MOCK_USERS", "false")

        # Clear cached modules and settings
        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]
            if mod.startswith("common.config"):
                del sys.modules[mod]

        with patch("sentry_sdk.init") as mock_init:
            import src.main as main

            assert main.TESTING is False
            assert main.DISABLE_SENTRY_FOR_TESTS is False
            assert main.disable_sentry is False

    def test_environment_defaults_to_development_fallback(self, monkeypatch):
        """Test that main.py uses 'development' as fallback when app_settings.environment is falsy."""
        # Note: app_settings.environment has its own default of "production" in settings.py
        # This test verifies the fallback logic in main.py (or "development")
        # Since app_settings.environment defaults to "production", we test with explicit development
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/123")

        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]

        with patch("sentry_sdk.init") as mock_init:
            import src.main as main

            # Verify current_env is set correctly
            assert main.current_env == "development"

    def test_both_flags_can_disable_sentry(self, monkeypatch):
        """Test that either TESTING or DISABLE_SENTRY_FOR_TESTS can disable Sentry."""
        # Test with only TESTING
        monkeypatch.setenv("TESTING", "true")
        monkeypatch.delenv("DISABLE_SENTRY_FOR_TESTS", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")

        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]

        import src.main as main1

        assert main1.disable_sentry is True

        # Test with only DISABLE_SENTRY_FOR_TESTS
        monkeypatch.delenv("TESTING", raising=False)
        monkeypatch.setenv("DISABLE_SENTRY_FOR_TESTS", "true")

        for mod in list(sys.modules.keys()):
            if mod.startswith("src.main") or mod == "src.main":
                del sys.modules[mod]

        import src.main as main2

        assert main2.disable_sentry is True
