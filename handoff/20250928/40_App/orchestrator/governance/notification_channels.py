"""
Notification Channel Abstraction - Extensible Alert Delivery

Issue #4134: ReviewerMetrics Architecture Improvements
EPIC B: LLM Reviewer Agent - Metrics and Alerting

This module provides a NotificationChannel interface for extensible alert delivery.
It follows the Dependency Inversion Principle (DIP) to decouple alert evaluators
from specific notification implementations.

Key Features:
- Abstract NotificationChannel interface
- Concrete implementations: SlackChannel, PagerDutyChannel
- Retry mechanism with exponential backoff
- Async-aware delivery (handles both sync and async contexts)

Usage:
    from governance.notification_channels import (
        SlackChannel, PagerDutyChannel, NotificationResult
    )

    slack = SlackChannel(webhook_url="https://hooks.slack.com/...")
    result = slack.send(payload)

    pagerduty = PagerDutyChannel(routing_key="your-routing-key")
    result = pagerduty.send(payload)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of a notification delivery attempt."""

    success: bool
    channel_type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scheduled: bool = False
    attempts: int = 1
    error: Optional[str] = None
    response_code: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        result = {
            "success": self.success,
            "channel_type": self.channel_type,
            "timestamp": self.timestamp,
            "attempts": self.attempts,
        }
        if self.scheduled:
            result["scheduled"] = True
        if self.error:
            result["error"] = self.error
        if self.response_code is not None:
            result["response_code"] = self.response_code
        return result


class NotificationChannel(ABC):
    """
    Abstract base class for notification channels.

    Implementations must provide:
    - send(): Deliver a notification payload
    - channel_type: String identifier for the channel type

    This follows the Dependency Inversion Principle - high-level alert
    evaluators depend on this abstraction, not concrete implementations.
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Return the channel type identifier (e.g., 'slack', 'pagerduty')."""
        pass

    @abstractmethod
    def send(self, payload: Dict[str, Any]) -> NotificationResult:
        """
        Send a notification.

        Args:
            payload: Alert payload with message, severity, etc.

        Returns:
            NotificationResult with success status and metadata
        """
        pass

    def is_configured(self) -> bool:
        """Check if the channel is properly configured."""
        return True


class SlackChannel(NotificationChannel):
    """
    Slack notification channel using incoming webhooks.

    Features:
    - Async-aware: Uses background task if event loop is running
    - Retry mechanism with exponential backoff
    - Formatted messages with severity indicators
    """

    def __init__(
        self,
        webhook_url: str,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
    ):
        """
        Initialize Slack channel.

        Args:
            webhook_url: Slack incoming webhook URL
            max_retries: Maximum retry attempts (default: 3)
            base_delay_seconds: Base delay for exponential backoff (default: 1.0)
        """
        self._webhook_url = webhook_url
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds

    @property
    def channel_type(self) -> str:
        return "slack"

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    def send(self, payload: Dict[str, Any]) -> NotificationResult:
        """Send notification to Slack with retry support."""
        if not self.is_configured():
            return NotificationResult(
                success=False,
                channel_type=self.channel_type,
                error="Slack webhook URL not configured",
            )

        message = self._format_message(payload)

        try:
            import aiohttp

            async def send_with_retry() -> tuple[bool, int, Optional[str], Optional[int]]:
                """Send with retry, returns (success, attempts, error, status_code)."""
                last_error = None
                last_status = None

                for attempt in range(1, self._max_retries + 1):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                self._webhook_url,
                                json={"text": message},
                                timeout=aiohttp.ClientTimeout(total=10),
                            ) as response:
                                last_status = response.status
                                if response.status == 200:
                                    return True, attempt, None, response.status
                                last_error = f"HTTP {response.status}"
                    except asyncio.TimeoutError:
                        last_error = "Request timeout"
                    except Exception as e:
                        last_error = str(e)

                    if attempt < self._max_retries:
                        delay = self._base_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)

                return False, self._max_retries, last_error, last_status

            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop is not None:
                logger.debug(
                    f"[{self.channel_type}] Detected running event loop, "
                    "scheduling as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[{self.channel_type}] Background task failed: {exc}"
                            )
                    except asyncio.CancelledError:
                        pass

                task = running_loop.create_task(send_with_retry())
                task.add_done_callback(handle_task_exception)
                return NotificationResult(
                    success=True,
                    channel_type=self.channel_type,
                    scheduled=True,
                )

            loop = asyncio.new_event_loop()
            try:
                success, attempts, error, status = loop.run_until_complete(
                    send_with_retry()
                )
            finally:
                loop.close()

            return NotificationResult(
                success=success,
                channel_type=self.channel_type,
                attempts=attempts,
                error=error,
                response_code=status,
            )

        except Exception as e:
            logger.warning(f"[{self.channel_type}] Send failed: {e}")
            return NotificationResult(
                success=False,
                channel_type=self.channel_type,
                error=str(e),
            )

    def _format_message(self, payload: Dict[str, Any]) -> str:
        """Format alert payload as Slack message."""
        severity = payload.get("severity", "info")
        severity_emoji = ":rotating_light:" if severity == "critical" else ":warning:"

        current_value = payload.get("current_value")
        threshold = payload.get("threshold")

        if isinstance(current_value, float) and current_value < 1:
            current_str = f"{current_value:.2%}"
        elif isinstance(current_value, float):
            current_str = f"{current_value:.0f}"
        else:
            current_str = str(current_value) if current_value is not None else "N/A"

        if isinstance(threshold, float) and threshold < 1:
            threshold_str = f"{threshold:.2%}"
        elif isinstance(threshold, float):
            threshold_str = f"{threshold:.0f}"
        else:
            threshold_str = str(threshold) if threshold is not None else "N/A"

        return (
            f"{severity_emoji} *{payload.get('component', 'Alert')}*\n"
            f"*Alert Type:* `{payload.get('alert_type', 'unknown')}`\n"
            f"*Severity:* {severity.upper()}\n"
            f"*Metric:* {payload.get('metric_name', 'N/A')}\n"
            f"*Current Value:* {current_str}\n"
            f"*Threshold:* {threshold_str}\n"
            f"*Message:* {payload.get('message', 'No message')}\n"
            f"*Time:* {payload.get('timestamp', 'N/A')}"
        )


class PagerDutyChannel(NotificationChannel):
    """
    PagerDuty notification channel using Events API v2.

    Features:
    - Async-aware: Uses background task if event loop is running
    - Retry mechanism with exponential backoff
    - Deduplication key support
    """

    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"

    def __init__(
        self,
        routing_key: str,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
    ):
        """
        Initialize PagerDuty channel.

        Args:
            routing_key: PagerDuty Events API v2 integration/routing key
            max_retries: Maximum retry attempts (default: 3)
            base_delay_seconds: Base delay for exponential backoff (default: 1.0)
        """
        self._routing_key = routing_key
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds

    @property
    def channel_type(self) -> str:
        return "pagerduty"

    def is_configured(self) -> bool:
        return bool(self._routing_key)

    def send(self, payload: Dict[str, Any]) -> NotificationResult:
        """Send notification to PagerDuty with retry support."""
        if not self.is_configured():
            return NotificationResult(
                success=False,
                channel_type=self.channel_type,
                error="PagerDuty routing key not configured",
            )

        pagerduty_payload = self._build_payload(payload)

        try:
            import aiohttp

            async def send_with_retry() -> tuple[bool, int, Optional[str], Optional[int]]:
                """Send with retry, returns (success, attempts, error, status_code)."""
                last_error = None
                last_status = None

                for attempt in range(1, self._max_retries + 1):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                self.EVENTS_API_URL,
                                json=pagerduty_payload,
                                headers={"Content-Type": "application/json"},
                                timeout=aiohttp.ClientTimeout(total=10),
                            ) as response:
                                last_status = response.status
                                if response.status < 300:
                                    return True, attempt, None, response.status
                                last_error = f"HTTP {response.status}"
                    except asyncio.TimeoutError:
                        last_error = "Request timeout"
                    except Exception as e:
                        last_error = str(e)

                    if attempt < self._max_retries:
                        delay = self._base_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)

                return False, self._max_retries, last_error, last_status

            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop is not None:
                logger.debug(
                    f"[{self.channel_type}] Detected running event loop, "
                    "scheduling as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[{self.channel_type}] Background task failed: {exc}"
                            )
                    except asyncio.CancelledError:
                        pass

                task = running_loop.create_task(send_with_retry())
                task.add_done_callback(handle_task_exception)
                return NotificationResult(
                    success=True,
                    channel_type=self.channel_type,
                    scheduled=True,
                )

            loop = asyncio.new_event_loop()
            try:
                success, attempts, error, status = loop.run_until_complete(
                    send_with_retry()
                )
            finally:
                loop.close()

            return NotificationResult(
                success=success,
                channel_type=self.channel_type,
                attempts=attempts,
                error=error,
                response_code=status,
            )

        except Exception as e:
            logger.warning(f"[{self.channel_type}] Send failed: {e}")
            return NotificationResult(
                success=False,
                channel_type=self.channel_type,
                error=str(e),
            )

    def _build_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build PagerDuty Events API v2 payload."""
        return {
            "routing_key": self._routing_key,
            "event_action": "trigger",
            "dedup_key": f"{payload.get('source', 'morningai')}_{payload.get('alert_type', 'unknown')}",
            "payload": {
                "summary": payload.get("message", "Alert triggered"),
                "severity": "critical" if payload.get("severity") == "critical" else "warning",
                "source": payload.get("source", "morningai"),
                "component": payload.get("component", "Unknown"),
                "custom_details": {
                    "metric_name": payload.get("metric_name"),
                    "current_value": payload.get("current_value"),
                    "threshold": payload.get("threshold"),
                    "timestamp": payload.get("timestamp"),
                    "epic": payload.get("epic"),
                }
            }
        }


def create_notification_channels(
    slack_webhook_url: Optional[str] = None,
    pagerduty_routing_key: Optional[str] = None,
    max_retries: int = 3,
) -> List[NotificationChannel]:
    """
    Factory function to create configured notification channels.

    Args:
        slack_webhook_url: Slack incoming webhook URL
        pagerduty_routing_key: PagerDuty Events API v2 routing key
        max_retries: Maximum retry attempts for each channel

    Returns:
        List of configured NotificationChannel instances
    """
    channels: List[NotificationChannel] = []

    if slack_webhook_url:
        channels.append(SlackChannel(
            webhook_url=slack_webhook_url,
            max_retries=max_retries,
        ))

    if pagerduty_routing_key:
        channels.append(PagerDutyChannel(
            routing_key=pagerduty_routing_key,
            max_retries=max_retries,
        ))

    return channels
