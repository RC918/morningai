"""
Unit tests for NotificationChannel abstraction.

Issue #4134: ReviewerMetrics Architecture Improvements
EPIC B: LLM Reviewer Agent - Metrics and Alerting

Tests cover:
- NotificationChannel interface
- SlackChannel implementation
- PagerDutyChannel implementation
- Retry mechanism with exponential backoff
- Factory function create_notification_channels
"""

from unittest.mock import MagicMock, patch
from governance.notification_channels import (
    NotificationResult,
    SlackChannel,
    PagerDutyChannel,
    create_notification_channels,
)


class TestNotificationResult:
    """Tests for NotificationResult dataclass."""

    def test_success_result(self):
        """Test successful notification result."""
        result = NotificationResult(
            success=True,
            channel_type="slack",
            attempts=1,
        )
        assert result.success is True
        assert result.channel_type == "slack"
        assert result.attempts == 1
        assert result.error is None

    def test_failure_result(self):
        """Test failed notification result."""
        result = NotificationResult(
            success=False,
            channel_type="pagerduty",
            attempts=3,
            error="Connection timeout",
            response_code=500,
        )
        assert result.success is False
        assert result.channel_type == "pagerduty"
        assert result.attempts == 3
        assert result.error == "Connection timeout"
        assert result.response_code == 500

    def test_scheduled_result(self):
        """Test scheduled (background task) result."""
        result = NotificationResult(
            success=True,
            channel_type="slack",
            scheduled=True,
        )
        assert result.success is True
        assert result.scheduled is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = NotificationResult(
            success=True,
            channel_type="slack",
            attempts=2,
            response_code=200,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["channel_type"] == "slack"
        assert d["attempts"] == 2
        assert d["response_code"] == 200
        assert "timestamp" in d

    def test_to_dict_with_error(self):
        """Test conversion to dictionary with error."""
        result = NotificationResult(
            success=False,
            channel_type="pagerduty",
            error="Network error",
        )
        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Network error"


class TestSlackChannel:
    """Tests for SlackChannel implementation."""

    def test_channel_type(self):
        """Test channel type property."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        assert channel.channel_type == "slack"

    def test_is_configured_with_url(self):
        """Test is_configured returns True when URL is set."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        assert channel.is_configured() is True

    def test_is_configured_without_url(self):
        """Test is_configured returns False when URL is empty."""
        channel = SlackChannel(webhook_url="")
        assert channel.is_configured() is False

    def test_send_not_configured(self):
        """Test send returns error when not configured."""
        channel = SlackChannel(webhook_url="")
        result = channel.send({"message": "test"})
        assert result.success is False
        assert "not configured" in result.error

    @patch("governance.notification_channels.asyncio")
    def test_send_success(self, mock_asyncio):
        """Test successful send."""
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 1, None, 200)

        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        result = channel.send({
            "alert_type": "test_alert",
            "severity": "warning",
            "message": "Test message",
        })

        assert result.success is True
        assert result.channel_type == "slack"

    @patch("governance.notification_channels.asyncio")
    def test_send_with_retry(self, mock_asyncio):
        """Test send with retry on failure."""
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 2, None, 200)

        channel = SlackChannel(
            webhook_url="https://hooks.slack.com/test",
            max_retries=3,
        )
        result = channel.send({"message": "test"})

        assert result.success is True
        assert result.attempts == 2

    @patch("governance.notification_channels.asyncio")
    def test_send_all_retries_failed(self, mock_asyncio):
        """Test send when all retries fail."""
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (False, 3, "Connection refused", 500)

        channel = SlackChannel(
            webhook_url="https://hooks.slack.com/test",
            max_retries=3,
        )
        result = channel.send({"message": "test"})

        assert result.success is False
        assert result.attempts == 3
        assert result.error == "Connection refused"

    def test_format_message_warning(self):
        """Test message formatting for warning severity."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        message = channel._format_message({
            "alert_type": "json_parse_failure",
            "severity": "warning",
            "metric_name": "json_parse_failure_rate",
            "current_value": 0.15,
            "threshold": 0.10,
            "message": "JSON parse failure rate exceeded",
            "component": "LLM Reviewer Agent",
            "timestamp": "2026-01-18T00:00:00Z",
        })

        assert ":warning:" in message
        assert "json_parse_failure" in message
        assert "15.00%" in message
        assert "10.00%" in message

    def test_format_message_critical(self):
        """Test message formatting for critical severity."""
        channel = SlackChannel(webhook_url="https://hooks.slack.com/test")
        message = channel._format_message({
            "alert_type": "success_rate_low",
            "severity": "critical",
            "metric_name": "success_rate",
            "current_value": 0.85,
            "threshold": 0.90,
            "message": "Success rate below threshold",
            "component": "LLM Reviewer Agent",
            "timestamp": "2026-01-18T00:00:00Z",
        })

        assert ":rotating_light:" in message
        assert "CRITICAL" in message


class TestPagerDutyChannel:
    """Tests for PagerDutyChannel implementation."""

    def test_channel_type(self):
        """Test channel type property."""
        channel = PagerDutyChannel(routing_key="test-routing-key")
        assert channel.channel_type == "pagerduty"

    def test_is_configured_with_key(self):
        """Test is_configured returns True when routing key is set."""
        channel = PagerDutyChannel(routing_key="test-routing-key")
        assert channel.is_configured() is True

    def test_is_configured_without_key(self):
        """Test is_configured returns False when routing key is empty."""
        channel = PagerDutyChannel(routing_key="")
        assert channel.is_configured() is False

    def test_send_not_configured(self):
        """Test send returns error when not configured."""
        channel = PagerDutyChannel(routing_key="")
        result = channel.send({"message": "test"})
        assert result.success is False
        assert "not configured" in result.error

    @patch("governance.notification_channels.asyncio")
    def test_send_success(self, mock_asyncio):
        """Test successful send."""
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 1, None, 202)

        channel = PagerDutyChannel(routing_key="test-routing-key")
        result = channel.send({
            "alert_type": "test_alert",
            "severity": "critical",
            "message": "Test message",
        })

        assert result.success is True
        assert result.channel_type == "pagerduty"

    @patch("governance.notification_channels.asyncio")
    def test_send_with_retry(self, mock_asyncio):
        """Test send with retry on failure."""
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 3, None, 202)

        channel = PagerDutyChannel(
            routing_key="test-routing-key",
            max_retries=3,
        )
        result = channel.send({"message": "test"})

        assert result.success is True
        assert result.attempts == 3

    def test_build_payload(self):
        """Test PagerDuty payload building."""
        channel = PagerDutyChannel(routing_key="test-routing-key")
        payload = channel._build_payload({
            "alert_type": "json_parse_failure_critical",
            "severity": "critical",
            "message": "Critical JSON parse failure rate",
            "source": "reviewer_metrics",
            "component": "LLM Reviewer Agent",
            "metric_name": "json_parse_failure_rate",
            "current_value": 0.30,
            "threshold": 0.25,
            "timestamp": "2026-01-18T00:00:00Z",
            "epic": "EPIC-B",
        })

        assert payload["routing_key"] == "test-routing-key"
        assert payload["event_action"] == "trigger"
        assert "dedup_key" in payload
        assert payload["payload"]["severity"] == "critical"
        assert payload["payload"]["summary"] == "Critical JSON parse failure rate"
        assert payload["payload"]["custom_details"]["metric_name"] == "json_parse_failure_rate"


class TestCreateNotificationChannels:
    """Tests for create_notification_channels factory function."""

    def test_create_no_channels(self):
        """Test creating with no configuration."""
        channels = create_notification_channels()
        assert len(channels) == 0

    def test_create_slack_only(self):
        """Test creating Slack channel only."""
        channels = create_notification_channels(
            slack_webhook_url="https://hooks.slack.com/test"
        )
        assert len(channels) == 1
        assert channels[0].channel_type == "slack"

    def test_create_pagerduty_only(self):
        """Test creating PagerDuty channel only."""
        channels = create_notification_channels(
            pagerduty_routing_key="test-routing-key"
        )
        assert len(channels) == 1
        assert channels[0].channel_type == "pagerduty"

    def test_create_both_channels(self):
        """Test creating both channels."""
        channels = create_notification_channels(
            slack_webhook_url="https://hooks.slack.com/test",
            pagerduty_routing_key="test-routing-key",
        )
        assert len(channels) == 2
        channel_types = {ch.channel_type for ch in channels}
        assert channel_types == {"slack", "pagerduty"}

    def test_create_with_custom_retries(self):
        """Test creating channels with custom retry count."""
        channels = create_notification_channels(
            slack_webhook_url="https://hooks.slack.com/test",
            max_retries=5,
        )
        assert len(channels) == 1
        assert channels[0]._max_retries == 5


class TestReviewerMetricsAlertEvaluatorIntegration:
    """Integration tests for ReviewerMetricsAlertEvaluator with NotificationChannel."""

    def test_evaluator_with_notification_channels(self):
        """Test evaluator initialization with notification channels."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        channels = create_notification_channels(
            slack_webhook_url="https://hooks.slack.com/test",
            pagerduty_routing_key="test-routing-key",
        )

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            notification_channels=channels,
        )

        assert len(evaluator._notification_channels) == 2

    def test_evaluator_creates_channels_from_urls(self):
        """Test evaluator creates channels from URL parameters."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
            pagerduty_routing_key="test-routing-key",
        )

        assert len(evaluator._notification_channels) == 2
        channel_types = {ch.channel_type for ch in evaluator._notification_channels}
        assert channel_types == {"slack", "pagerduty"}

    def test_evaluator_pagerduty_naming_consistency(self):
        """Test evaluator uses pagerduty_routing_key parameter."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            pagerduty_routing_key="test-routing-key",
        )

        assert evaluator.pagerduty_routing_key == "test-routing-key"

    def test_evaluator_max_retries_config(self):
        """Test evaluator passes max_retries to channels."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
            max_retries=5,
        )

        assert evaluator.max_retries == 5
        assert evaluator._notification_channels[0]._max_retries == 5

    @patch("governance.notification_channels.asyncio")
    def test_send_alert_uses_channels(self, mock_asyncio):
        """Test _send_alert uses notification channels."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 1, None, 200)

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
        )

        result = evaluator._send_alert({
            "alert_type": "test_alert",
            "severity": "warning",
            "message": "Test message",
        })

        assert "slack" in result["channels"]
        assert result["channels"]["slack"]["success"] is True

    @patch("governance.notification_channels.asyncio")
    def test_send_alert_pagerduty_only_for_critical(self, mock_asyncio):
        """Test PagerDuty only receives critical alerts."""
        from governance.reviewer_metrics_alerter import ReviewerMetricsAlertEvaluator

        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.side_effect = RuntimeError()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = (True, 1, None, 200)

        evaluator = ReviewerMetricsAlertEvaluator(
            enabled=True,
            slack_webhook_url="https://hooks.slack.com/test",
            pagerduty_routing_key="test-routing-key",
        )

        result = evaluator._send_alert({
            "alert_type": "test_alert",
            "severity": "warning",
            "message": "Test message",
        })

        assert "slack" in result["channels"]
        assert "pagerduty" not in result["channels"]

        result_critical = evaluator._send_alert({
            "alert_type": "test_alert",
            "severity": "critical",
            "message": "Critical message",
        })

        assert "slack" in result_critical["channels"]
        assert "pagerduty" in result_critical["channels"]
