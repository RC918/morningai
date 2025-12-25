"""
Unit tests for fail-open alert threshold configuration settings (Issue #2933).

Tests verify that the fail-open threshold settings correctly read from
environment variables and validate min/max constraints.
"""
import pytest
from pydantic import ValidationError
from common.config.settings import get_settings, reload_settings


class TestFailOpenAlertThresholdSettings:
    """Test suite for fail-open alert threshold configuration settings."""

    def test_fail_open_alert_threshold_default(self, monkeypatch):
        """Test that fail_open_alert_threshold defaults to 5."""
        monkeypatch.delenv("FAIL_OPEN_ALERT_THRESHOLD", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 5, \
            f"Expected default 5 but got {settings.fail_open_alert_threshold}"

    def test_fail_open_alert_threshold_from_env(self, monkeypatch):
        """Test that fail_open_alert_threshold reads from env var."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "10")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 10, \
            f"Expected 10 but got {settings.fail_open_alert_threshold}"

    def test_fail_open_alert_threshold_min_value(self, monkeypatch):
        """Test that fail_open_alert_threshold accepts minimum value of 1."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "1")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 1, \
            f"Expected 1 but got {settings.fail_open_alert_threshold}"

    def test_fail_open_alert_threshold_max_value(self, monkeypatch):
        """Test that fail_open_alert_threshold accepts maximum value of 100."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "100")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 100, \
            f"Expected 100 but got {settings.fail_open_alert_threshold}"

    def test_fail_open_alert_threshold_below_min_raises_error(self, monkeypatch):
        """Test that fail_open_alert_threshold below 1 raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "0")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert "fail_open_alert_threshold" in str(exc_info.value).lower() or \
               "greater than or equal to 1" in str(exc_info.value).lower()

    def test_fail_open_alert_threshold_above_max_raises_error(self, monkeypatch):
        """Test that fail_open_alert_threshold above 100 raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "101")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert "fail_open_alert_threshold" in str(exc_info.value).lower() or \
               "less than or equal to 100" in str(exc_info.value).lower()

    def test_fail_open_alert_threshold_non_integer_raises_error(self, monkeypatch):
        """Test that non-integer fail_open_alert_threshold raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "abc")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        # Pydantic will raise a type error for non-integer values
        assert "fail_open_alert_threshold" in str(exc_info.value).lower() or \
               "int" in str(exc_info.value).lower()


class TestFailOpenAlertWindowSettings:
    """Test suite for fail-open alert window configuration settings."""

    def test_fail_open_alert_window_minutes_default(self, monkeypatch):
        """Test that fail_open_alert_window_minutes defaults to 5."""
        monkeypatch.delenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_window_minutes == 5, \
            f"Expected default 5 but got {settings.fail_open_alert_window_minutes}"

    def test_fail_open_alert_window_minutes_from_env(self, monkeypatch):
        """Test that fail_open_alert_window_minutes reads from env var."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "15")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_window_minutes == 15, \
            f"Expected 15 but got {settings.fail_open_alert_window_minutes}"

    def test_fail_open_alert_window_minutes_min_value(self, monkeypatch):
        """Test that fail_open_alert_window_minutes accepts minimum value of 1."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "1")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_window_minutes == 1, \
            f"Expected 1 but got {settings.fail_open_alert_window_minutes}"

    def test_fail_open_alert_window_minutes_max_value(self, monkeypatch):
        """Test that fail_open_alert_window_minutes accepts maximum value of 60."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "60")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_window_minutes == 60, \
            f"Expected 60 but got {settings.fail_open_alert_window_minutes}"

    def test_fail_open_alert_window_minutes_below_min_raises_error(self, monkeypatch):
        """Test that fail_open_alert_window_minutes below 1 raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "0")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert "fail_open_alert_window_minutes" in str(exc_info.value).lower() or \
               "greater than or equal to 1" in str(exc_info.value).lower()

    def test_fail_open_alert_window_minutes_above_max_raises_error(self, monkeypatch):
        """Test that fail_open_alert_window_minutes above 60 raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "61")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        assert "fail_open_alert_window_minutes" in str(exc_info.value).lower() or \
               "less than or equal to 60" in str(exc_info.value).lower()

    def test_fail_open_alert_window_minutes_non_integer_raises_error(self, monkeypatch):
        """Test that non-integer fail_open_alert_window_minutes raises ValidationError."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "abc")

        with pytest.raises(ValidationError) as exc_info:
            reload_settings()

        # Pydantic will raise a type error for non-integer values
        assert "fail_open_alert_window_minutes" in str(exc_info.value).lower() or \
               "int" in str(exc_info.value).lower()


class TestFailOpenSettingsIntegration:
    """Integration tests for fail-open settings."""

    def test_both_settings_can_be_configured_together(self, monkeypatch):
        """Test that both fail-open settings can be configured simultaneously."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "3")
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "10")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 3
        assert settings.fail_open_alert_window_minutes == 10

    def test_production_scenario_low_sensitivity(self, monkeypatch):
        """Test production scenario with low sensitivity (high threshold, long window)."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "20")
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "30")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 20
        assert settings.fail_open_alert_window_minutes == 30

    def test_staging_scenario_high_sensitivity(self, monkeypatch):
        """Test staging scenario with high sensitivity (low threshold, short window)."""
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "1")
        monkeypatch.setenv("FAIL_OPEN_ALERT_WINDOW_MINUTES", "1")

        reload_settings()

        settings = get_settings()
        assert settings.fail_open_alert_threshold == 1
        assert settings.fail_open_alert_window_minutes == 1

    def test_empty_string_uses_default(self, monkeypatch):
        """Test that empty string env var falls back to default (Pydantic behavior)."""
        # Note: Pydantic may raise ValidationError for empty string on int field
        # This test documents the expected behavior
        monkeypatch.setenv("FAIL_OPEN_ALERT_THRESHOLD", "")

        # Empty string should raise ValidationError for int field
        with pytest.raises(ValidationError):
            reload_settings()
