"""
Tests for Health Alerter Service

EPIC I-3a: Health Alerting (Blueprint 4.3 - Model Governance Framework v2)

These tests verify the health alerting functionality including:
- Alert triggering based on health score threshold
- Alert triggering based on error rate spike
- Cooldown mechanism to prevent alert storms
- Minimum sample size to prevent noise
- Notification channel integration
- Observe-only safety contract (failures don't propagate)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from governance.health_alerter import (
    HealthAlertService,
    get_health_alert_service,
    reset_health_alert_service,
)


class TestHealthAlertService:
    """Test suite for HealthAlertService"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_health_alert_service()

    def test_init_default_values(self):
        """Test service initialization with default values"""
        service = HealthAlertService()

        assert service.enabled is False
        assert service.health_threshold == 70.0
        assert service.cooldown_minutes == 15
        assert service.min_requests == 10
        assert service.error_rate_threshold == 10.0

    def test_init_custom_values(self):
        """Test service initialization with custom values"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=80.0,
            cooldown_minutes=30,
            min_requests=20,
            error_rate_threshold=5.0,
            slack_webhook_url="https://hooks.slack.com/test",
            ops_webhook_url="https://ops.example.com/webhook",
        )

        assert service.enabled is True
        assert service.health_threshold == 80.0
        assert service.cooldown_minutes == 30
        assert service.min_requests == 20
        assert service.error_rate_threshold == 5.0
        assert service.slack_webhook_url == "https://hooks.slack.com/test"
        assert service.ops_webhook_url == "https://ops.example.com/webhook"

    def test_check_and_alert_disabled(self):
        """Test that no alerts are sent when service is disabled"""
        service = HealthAlertService(enabled=False)

        health_data = {
            "health_score": 50.0,
            "error_rate": 20.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)
        assert result is None

    def test_check_and_alert_no_health_score(self):
        """Test that no alerts are sent when health score is missing"""
        service = HealthAlertService(enabled=True)

        health_data = {
            "error_rate": 5.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)
        assert result is None

    def test_check_and_alert_insufficient_requests(self):
        """Test that no alerts are sent when request count is below minimum"""
        service = HealthAlertService(enabled=True, min_requests=10)

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 5,
        }

        result = service.check_and_alert("openai", health_data)
        assert result is None

    def test_check_and_alert_healthy_provider(self):
        """Test that no alerts are sent for healthy providers"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            error_rate_threshold=10.0,
        )

        health_data = {
            "health_score": 85.0,
            "error_rate": 2.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)
        assert result is None

    def test_check_and_alert_low_health_score(self):
        """Test alert triggered when health score is below threshold"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            min_requests=10,
        )

        health_data = {
            "health_score": 60.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)

        assert result is not None
        assert result["provider"] == "openai"
        assert "low_health_score" in result["reason"]

    def test_check_and_alert_error_rate_spike(self):
        """Test alert triggered when error rate exceeds threshold"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            error_rate_threshold=10.0,
            min_requests=10,
        )

        health_data = {
            "health_score": 75.0,
            "error_rate": 15.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)

        assert result is not None
        assert result["provider"] == "openai"
        assert "error_rate_spike" in result["reason"]

    def test_cooldown_prevents_duplicate_alerts(self):
        """Test that cooldown prevents duplicate alerts for same provider"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # First alert should be sent
        result1 = service.check_and_alert("openai", health_data)
        assert result1 is not None

        # Second alert should be blocked by cooldown
        result2 = service.check_and_alert("openai", health_data)
        assert result2 is None

    def test_cooldown_expires(self):
        """Test that alerts can be sent after cooldown expires"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # First alert
        result1 = service.check_and_alert("openai", health_data)
        assert result1 is not None

        # Manually expire cooldown
        service._last_alert_time["openai"] = datetime.now(timezone.utc) - timedelta(minutes=20)

        # Second alert should now be sent
        result2 = service.check_and_alert("openai", health_data)
        assert result2 is not None

    def test_different_providers_independent_cooldown(self):
        """Test that different providers have independent cooldowns"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # Alert for openai
        result1 = service.check_and_alert("openai", health_data)
        assert result1 is not None

        # Alert for gemini should still work
        result2 = service.check_and_alert("gemini", health_data)
        assert result2 is not None

    def test_clear_cooldown_single_provider(self):
        """Test clearing cooldown for a single provider"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # Trigger alert
        service.check_and_alert("openai", health_data)
        service.check_and_alert("gemini", health_data)

        # Clear cooldown for openai only
        service.clear_cooldown("openai")

        # openai should be able to alert again
        result1 = service.check_and_alert("openai", health_data)
        assert result1 is not None

        # gemini should still be in cooldown
        result2 = service.check_and_alert("gemini", health_data)
        assert result2 is None

    def test_clear_cooldown_all_providers(self):
        """Test clearing cooldown for all providers"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # Trigger alerts
        service.check_and_alert("openai", health_data)
        service.check_and_alert("gemini", health_data)

        # Clear all cooldowns
        service.clear_cooldown()

        # Both should be able to alert again
        result1 = service.check_and_alert("openai", health_data)
        assert result1 is not None

        service.clear_cooldown()  # Clear again for gemini test

        result2 = service.check_and_alert("gemini", health_data)
        assert result2 is not None

    def test_get_cooldown_status(self):
        """Test getting cooldown status for all providers"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            cooldown_minutes=15,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # Trigger alert
        service.check_and_alert("openai", health_data)

        status = service.get_cooldown_status()

        assert "openai" in status
        assert status["openai"]["in_cooldown"] is True
        assert status["openai"]["cooldown_remaining_seconds"] > 0

    def test_should_alert_error_rate_takes_priority(self):
        """Test that error rate spike takes priority over low health score"""
        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            error_rate_threshold=10.0,
        )

        # Both conditions met - error rate should take priority
        reason = service._should_alert("openai", 50.0, 15.0)
        assert "error_rate_spike" in reason

    def test_build_alert_payload(self):
        """Test alert payload structure"""
        service = HealthAlertService(enabled=True)

        health_data = {
            "health_score": 50.0,
            "error_rate": 15.0,
            "latency": {"p95_ms": 500},
            "drift_rate": 5.0,
            "total_requests": 100,
            "window_minutes": 15,
        }

        payload = service._build_alert_payload("openai", health_data, "test_reason")

        assert payload["alert_type"] == "provider_health_degradation"
        assert payload["provider"] == "openai"
        assert payload["reason"] == "test_reason"
        assert payload["health_score"] == 50.0
        assert payload["error_rate"] == 15.0
        assert payload["latency_p95_ms"] == 500
        assert payload["drift_rate"] == 5.0
        assert payload["total_requests"] == 100

    def test_format_slack_message(self):
        """Test Slack message formatting"""
        service = HealthAlertService(enabled=True)

        payload = {
            "severity": "critical",
            "provider": "openai",
            "reason": "error_rate_spike",
            "health_score": 50.0,
            "error_rate": 15.0,
            "latency_p95_ms": 500,
            "timestamp": "2025-01-01T00:00:00",
        }

        message = service._format_slack_message(payload)

        assert ":rotating_light:" in message
        assert "openai" in message
        assert "error_rate_spike" in message
        assert "50.0" in message
        assert "15.0%" in message

    def test_format_slack_message_warning_severity(self):
        """Test Slack message formatting for warning severity"""
        service = HealthAlertService(enabled=True)

        payload = {
            "severity": "warning",
            "provider": "gemini",
            "reason": "low_health_score",
            "health_score": 65.0,
            "error_rate": 5.0,
            "latency_p95_ms": 300,
            "timestamp": "2025-01-01T00:00:00",
        }

        message = service._format_slack_message(payload)

        assert ":warning:" in message
        assert "gemini" in message

    def test_exception_handling_in_check_and_alert(self):
        """Test that exceptions in check_and_alert don't propagate"""
        service = HealthAlertService(enabled=True, min_requests=10)

        # Pass invalid data that might cause issues
        health_data = {
            "health_score": "invalid",
            "error_rate": None,
            "total_requests": 100,
        }

        # Should not raise, should return None
        result = service.check_and_alert("openai", health_data)
        assert result is None


class TestHealthAlertServiceSingleton:
    """Test suite for global singleton functions"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_health_alert_service()

    def test_get_health_alert_service_disabled(self):
        """Test that get_health_alert_service returns None when disabled"""
        mock_settings = MagicMock()
        mock_settings.health_alerting_enabled = False

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            reset_health_alert_service()
            service = get_health_alert_service()
            assert service is None

    def test_get_health_alert_service_enabled(self):
        """Test that get_health_alert_service returns service when enabled"""
        mock_settings = MagicMock()
        mock_settings.health_alerting_enabled = True
        mock_settings.health_alert_threshold = 75.0
        mock_settings.health_alert_cooldown_minutes = 20
        mock_settings.health_alert_min_requests = 15
        mock_settings.health_alert_error_rate_threshold = 8.0
        mock_settings.slack_webhook_url = "https://hooks.slack.com/test"
        mock_settings.ops_alert_webhook_url = "https://ops.example.com/webhook"

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            reset_health_alert_service()
            service = get_health_alert_service()

            assert service is not None
            assert service.enabled is True
            assert service.health_threshold == 75.0
            assert service.cooldown_minutes == 20

    def test_get_health_alert_service_singleton(self):
        """Test that get_health_alert_service returns same instance"""
        mock_settings = MagicMock()
        mock_settings.health_alerting_enabled = True
        mock_settings.health_alert_threshold = 70.0
        mock_settings.health_alert_cooldown_minutes = 15
        mock_settings.health_alert_min_requests = 10
        mock_settings.health_alert_error_rate_threshold = 10.0
        mock_settings.slack_webhook_url = None
        mock_settings.ops_alert_webhook_url = None

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            reset_health_alert_service()
            service1 = get_health_alert_service()
            service2 = get_health_alert_service()

            assert service1 is service2

    def test_reset_health_alert_service(self):
        """Test that reset_health_alert_service clears the singleton"""
        mock_settings = MagicMock()
        mock_settings.health_alerting_enabled = True
        mock_settings.health_alert_threshold = 70.0
        mock_settings.health_alert_cooldown_minutes = 15
        mock_settings.health_alert_min_requests = 10
        mock_settings.health_alert_error_rate_threshold = 10.0
        mock_settings.slack_webhook_url = None
        mock_settings.ops_alert_webhook_url = None

        with patch.dict("sys.modules", {"common.config.settings": MagicMock(settings=mock_settings)}):
            reset_health_alert_service()
            service1 = get_health_alert_service()
            reset_health_alert_service()
            service2 = get_health_alert_service()

            assert service1 is not service2


class TestHealthAlertServiceNotifications:
    """Test suite for notification sending"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_health_alert_service()

    def test_send_slack_alert_returns_result(self):
        """Test that Slack alert returns a result dict (even on failure)"""
        service = HealthAlertService(
            enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
        )

        payload = {
            "severity": "warning",
            "provider": "openai",
            "reason": "test",
            "health_score": 50.0,
            "error_rate": 5.0,
            "latency_p95_ms": 100,
            "timestamp": "2025-01-01T00:00:00",
        }

        # This will fail to connect but should not raise
        result = service._send_slack_alert(payload)

        # Should return result dict with success=False (connection will fail)
        assert isinstance(result, dict)
        assert "success" in result

    def test_send_slack_alert_no_url(self):
        """Test that Slack alert is skipped when no URL configured"""
        service = HealthAlertService(
            enabled=True,
            slack_webhook_url=None,
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        result = service.check_and_alert("openai", health_data)

        # Alert should still be logged even without Slack
        assert result is not None
        assert "slack" not in result.get("channels", {})

    def test_send_alert_failure_does_not_propagate(self):
        """Test that notification failures don't propagate (observe-only contract)"""
        service = HealthAlertService(
            enabled=True,
            slack_webhook_url="https://invalid-url",
            min_requests=10,
        )

        health_data = {
            "health_score": 50.0,
            "error_rate": 5.0,
            "total_requests": 100,
        }

        # Should not raise even if notification fails
        result = service.check_and_alert("openai", health_data)

        # Alert should still be recorded
        assert result is not None


class TestHealthAlertServiceCheckAllProviders:
    """Test suite for check_all_providers method"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_health_alert_service()

    def test_check_all_providers_disabled(self):
        """Test check_all_providers when service is disabled"""
        service = HealthAlertService(enabled=False)

        result = service.check_all_providers()

        assert result["enabled"] is False

    def test_check_all_providers_metrics_unavailable(self):
        """Test check_all_providers when metrics are unavailable"""
        mock_get_canary_metrics = MagicMock(return_value=None)
        mock_metrics_module = MagicMock(get_canary_metrics=mock_get_canary_metrics)

        service = HealthAlertService(enabled=True)

        with patch.dict("sys.modules", {"metrics": mock_metrics_module}):
            result = service.check_all_providers()

        assert result["enabled"] is True
        assert result.get("error") == "metrics_unavailable"

    def test_check_all_providers_success(self):
        """Test check_all_providers with healthy providers"""
        mock_metrics = MagicMock()
        mock_metrics.get_provider_health.return_value = {
            "health_score": 90.0,
            "error_rate": 1.0,
            "total_requests": 100,
        }
        mock_get_canary_metrics = MagicMock(return_value=mock_metrics)
        mock_metrics_module = MagicMock(get_canary_metrics=mock_get_canary_metrics)

        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            min_requests=10,
        )

        with patch.dict("sys.modules", {"metrics": mock_metrics_module}):
            result = service.check_all_providers(["openai", "gemini"])

        assert result["enabled"] is True
        assert "openai" in result["providers_checked"]
        assert "gemini" in result["providers_checked"]
        assert len(result["alerts_sent"]) == 0

    def test_check_all_providers_with_alerts(self):
        """Test check_all_providers with unhealthy providers"""
        mock_metrics = MagicMock()
        mock_metrics.get_provider_health.return_value = {
            "health_score": 50.0,
            "error_rate": 15.0,
            "total_requests": 100,
        }
        mock_get_canary_metrics = MagicMock(return_value=mock_metrics)
        mock_metrics_module = MagicMock(get_canary_metrics=mock_get_canary_metrics)

        service = HealthAlertService(
            enabled=True,
            health_threshold=70.0,
            error_rate_threshold=10.0,
            min_requests=10,
        )

        with patch.dict("sys.modules", {"metrics": mock_metrics_module}):
            result = service.check_all_providers(["openai"])

        assert result["enabled"] is True
        assert len(result["alerts_sent"]) == 1
        assert result["alerts_sent"][0]["provider"] == "openai"
