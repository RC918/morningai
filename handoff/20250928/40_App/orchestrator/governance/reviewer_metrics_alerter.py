"""
Reviewer Metrics Alert Evaluator - Scheduled Alert Service for LLM Reviewer

Issue #4130: P1 - Add JSON parsing failure metrics and alerting
EPIC B: LLM Reviewer Agent - Metrics and Alerting

This module provides scheduled alerting capabilities for ReviewerMetrics.
It periodically polls the ReviewerMetrics API and sends alerts via configured
notification channels when thresholds are breached.

Key Features:
- Threshold-based alerting (JSON parse failure rate, success rate, latency)
- Cross-provider fallback rate monitoring
- Cooldown mechanism (prevents alert storms)
- Multi-channel notifications (Slack, PagerDuty webhook)
- Redis-based alert state for cooldown tracking

Alert Conditions:
- reviewer_json_parse_failure_rate > 0.10 -> Warning (Slack)
- reviewer_json_parse_failure_rate > 0.25 -> Critical (PagerDuty + Slack)
- reviewer_success_rate < 0.90 -> Critical (PagerDuty + Slack)
- reviewer_cross_provider_fallback_rate > 0.30 -> Warning (Slack)

Safety Contract:
- This is an observe-only feature - alerts do not affect review decisions
- Notification failures are logged but never block the main service
- All operations are wrapped in try/except
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def _get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in RFC3339 format.

    Returns ISO 8601 format with timezone designator (+00:00) for UTC.
    This is RFC3339 compliant and preferred over deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc).isoformat()


class ReviewerMetricsAlertEvaluator:
    """
    Service for monitoring ReviewerMetrics and sending alerts.

    Issue #4130: P1 - Add JSON parsing failure metrics and alerting

    This service periodically checks ReviewerMetrics and sends alerts
    when thresholds are breached. It integrates with Slack and PagerDuty
    for multi-channel delivery.
    """

    def __init__(
        self,
        enabled: bool = False,
        json_parse_failure_warning_threshold: float = 0.10,
        json_parse_failure_critical_threshold: float = 0.25,
        success_rate_threshold: float = 0.90,
        cross_provider_fallback_threshold: float = 0.30,
        cooldown_minutes: int = 15,
        min_reviews: int = 5,
        window_minutes: int = 15,
        slack_webhook_url: Optional[str] = None,
        pagerduty_webhook_url: Optional[str] = None,
        redis_client: Optional[Any] = None,
    ):
        """
        Initialize Reviewer Metrics Alert Evaluator.

        Args:
            enabled: Whether alerting is enabled
            json_parse_failure_warning_threshold: JSON parse failure rate for warning alerts
            json_parse_failure_critical_threshold: JSON parse failure rate for critical alerts
            success_rate_threshold: Success rate below which critical alerts are triggered
            cross_provider_fallback_threshold: Fallback rate above which warning alerts are triggered
            cooldown_minutes: Minimum time between alerts for same alert type
            min_reviews: Minimum reviews in window before alerting
            window_minutes: Time window for metrics evaluation
            slack_webhook_url: Slack webhook URL for notifications
            pagerduty_webhook_url: PagerDuty webhook URL for critical alerts
            redis_client: Redis client for cooldown state (optional, uses in-memory if None)
        """
        self.enabled = enabled
        self.json_parse_failure_warning_threshold = json_parse_failure_warning_threshold
        self.json_parse_failure_critical_threshold = json_parse_failure_critical_threshold
        self.success_rate_threshold = success_rate_threshold
        self.cross_provider_fallback_threshold = cross_provider_fallback_threshold
        self.cooldown_minutes = cooldown_minutes
        self.min_reviews = min_reviews
        self.window_minutes = window_minutes
        self.slack_webhook_url = slack_webhook_url
        self.pagerduty_webhook_url = pagerduty_webhook_url
        self.redis_client = redis_client

        self._last_alert_time: Dict[str, datetime] = {}
        self._lock = threading.Lock()

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval_minutes = 5

        # Public read-only properties for logging/monitoring
        self.interval_minutes = 5  # Will be updated by start_scheduler()

        logger.info(
            f"[ReviewerMetricsAlertEvaluator] Initialized: enabled={enabled}, "
            f"json_parse_failure_warning={json_parse_failure_warning_threshold}, "
            f"json_parse_failure_critical={json_parse_failure_critical_threshold}, "
            f"success_rate_threshold={success_rate_threshold}, "
            f"cooldown={cooldown_minutes}min"
        )

    def evaluate_and_alert(self) -> Dict[str, Any]:
        """
        Evaluate ReviewerMetrics and send alerts if thresholds are breached.

        Returns:
            Dict with evaluation results and any alerts sent
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            from core.flow.reviewer_metrics import get_reviewer_metrics

            metrics = get_reviewer_metrics()
            summary = metrics.get_summary(window_minutes=self.window_minutes)

            results = {
                "enabled": True,
                "timestamp": _get_utc_timestamp(),
                "window_minutes": self.window_minutes,
                "metrics_evaluated": True,
                "alerts_sent": [],
                "alerts_skipped": [],
            }

            total_reviews = summary.get("total_reviews", 0)
            if total_reviews < self.min_reviews:
                results["metrics_evaluated"] = False
                results["reason"] = (
                    f"Insufficient reviews: {total_reviews} < {self.min_reviews}"
                )
                logger.debug(
                    f"[ReviewerMetricsAlertEvaluator] Skipping evaluation: {results['reason']}"
                )
                return results

            alerts_to_send = self._check_thresholds(summary)

            for alert in alerts_to_send:
                alert_type = alert["alert_type"]
                if self._is_in_cooldown(alert_type):
                    results["alerts_skipped"].append({
                        "alert_type": alert_type,
                        "reason": "in_cooldown"
                    })
                    continue

                send_result = self._send_alert(alert)
                results["alerts_sent"].append(send_result)
                self._update_cooldown(alert_type)

            return results

        except Exception as e:
            logger.warning(f"[ReviewerMetricsAlertEvaluator] Evaluation failed: {e}")
            return {"enabled": True, "error": str(e)}

    def _check_thresholds(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check all alert thresholds and return list of alerts to send.

        Args:
            summary: ReviewerMetrics summary dict

        Returns:
            List of alert dicts to send
        """
        alerts = []

        # JSON parse failure rate - critical threshold
        json_parse_failure_rate = summary.get("json_parse_failure_rate", 0.0)
        if json_parse_failure_rate > self.json_parse_failure_critical_threshold:
            alerts.append({
                "alert_type": "reviewer_json_parse_failure_critical",
                "severity": "critical",
                "metric_name": "json_parse_failure_rate",
                "current_value": json_parse_failure_rate,
                "threshold": self.json_parse_failure_critical_threshold,
                "message": (
                    f"Reviewer JSON parse failure rate ({json_parse_failure_rate:.2%}) "
                    f"exceeds critical threshold ({self.json_parse_failure_critical_threshold:.2%}). "
                    f"LLM responses are frequently malformed."
                ),
            })
        elif json_parse_failure_rate > self.json_parse_failure_warning_threshold:
            # Only send warning if not already sending critical
            alerts.append({
                "alert_type": "reviewer_json_parse_failure_warning",
                "severity": "warning",
                "metric_name": "json_parse_failure_rate",
                "current_value": json_parse_failure_rate,
                "threshold": self.json_parse_failure_warning_threshold,
                "message": (
                    f"Reviewer JSON parse failure rate ({json_parse_failure_rate:.2%}) "
                    f"exceeds warning threshold ({self.json_parse_failure_warning_threshold:.2%}). "
                    f"Monitor for potential LLM response issues."
                ),
            })

        # Overall success rate
        success_rate = summary.get("success_rate", 1.0)
        if success_rate < self.success_rate_threshold:
            alerts.append({
                "alert_type": "reviewer_success_rate_low",
                "severity": "critical",
                "metric_name": "reviewer_success_rate",
                "current_value": success_rate,
                "threshold": self.success_rate_threshold,
                "message": (
                    f"Reviewer success rate ({success_rate:.2%}) is below "
                    f"threshold ({self.success_rate_threshold:.2%}). "
                    f"Reviews may be failing silently."
                ),
            })

        # Cross-provider fallback rate
        fallback_rate = summary.get("cross_provider_fallback_rate", 0.0)
        if fallback_rate > self.cross_provider_fallback_threshold:
            alerts.append({
                "alert_type": "reviewer_cross_provider_fallback_high",
                "severity": "warning",
                "metric_name": "cross_provider_fallback_rate",
                "current_value": fallback_rate,
                "threshold": self.cross_provider_fallback_threshold,
                "message": (
                    f"Reviewer cross-provider fallback rate ({fallback_rate:.2%}) "
                    f"exceeds threshold ({self.cross_provider_fallback_threshold:.2%}). "
                    f"Primary LLM provider may be experiencing issues."
                ),
            })

        return alerts

    def _is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period."""
        cooldown_key = f"reviewer_metrics_alert:{alert_type}"

        if self.redis_client:
            try:
                exists = self.redis_client.exists(cooldown_key)
                return bool(exists)
            except Exception as e:
                logger.warning(
                    f"[ReviewerMetricsAlertEvaluator] Redis cooldown check failed: {e}, "
                    f"falling back to in-memory"
                )

        with self._lock:
            last_alert = self._last_alert_time.get(alert_type)
            if last_alert is None:
                return False

            cooldown_end = last_alert + timedelta(minutes=self.cooldown_minutes)
            return datetime.now(timezone.utc) < cooldown_end

    def _update_cooldown(self, alert_type: str) -> None:
        """Update cooldown state for alert type."""
        cooldown_key = f"reviewer_metrics_alert:{alert_type}"
        cooldown_seconds = self.cooldown_minutes * 60

        if self.redis_client:
            try:
                self.redis_client.setex(cooldown_key, cooldown_seconds, "1")
                return
            except Exception as e:
                logger.warning(
                    f"[ReviewerMetricsAlertEvaluator] Redis cooldown update failed: {e}, "
                    f"falling back to in-memory"
                )

        with self._lock:
            self._last_alert_time[alert_type] = datetime.now(timezone.utc)

    def _send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert via configured channels.

        Args:
            alert: Alert dict with type, severity, message, etc.

        Returns:
            Dict with send results
        """
        alert_payload = self._build_alert_payload(alert)

        results = {
            "alert_type": alert["alert_type"],
            "severity": alert["severity"],
            "timestamp": _get_utc_timestamp(),
            "channels": {}
        }

        if self.slack_webhook_url:
            slack_result = self._send_slack_alert(alert_payload)
            results["channels"]["slack"] = slack_result

        if alert["severity"] == "critical" and self.pagerduty_webhook_url:
            pagerduty_result = self._send_pagerduty_alert(alert_payload)
            results["channels"]["pagerduty"] = pagerduty_result

        logger.warning(
            f"[ReviewerMetricsAlertEvaluator] ALERT: {alert['alert_type']} - "
            f"{alert['message']} (severity={alert['severity']})"
        )

        return results

    def _build_alert_payload(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Build alert payload for notifications."""
        return {
            "alert_type": alert["alert_type"],
            "severity": alert["severity"],
            "metric_name": alert.get("metric_name"),
            "current_value": alert.get("current_value"),
            "threshold": alert.get("threshold"),
            "message": alert["message"],
            "timestamp": _get_utc_timestamp(),
            "source": "reviewer_metrics_alert_evaluator",
            "epic": "EPIC-B",
            "component": "LLM Reviewer Agent",
        }

    def _send_slack_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Slack webhook."""
        try:
            import aiohttp
            import asyncio

            message = self._format_slack_message(payload)

            async def send():
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.slack_webhook_url,
                        json={"text": message}
                    ) as response:
                        return response.status == 200

            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop is not None:
                logger.debug(
                    "[ReviewerMetricsAlertEvaluator] Detected running event loop, "
                    "scheduling Slack alert as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[ReviewerMetricsAlertEvaluator] Slack alert task failed: {exc}"
                            )
                    except asyncio.CancelledError:
                        pass

                task = running_loop.create_task(send())
                task.add_done_callback(handle_task_exception)
                return {"success": True, "scheduled": True}

            loop = asyncio.new_event_loop()
            try:
                success = loop.run_until_complete(send())
            finally:
                loop.close()

            return {"success": success}

        except Exception as e:
            logger.warning(f"[ReviewerMetricsAlertEvaluator] Slack alert failed: {e}")
            return {"success": False, "error": str(e)}

    def _send_pagerduty_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to PagerDuty webhook."""
        try:
            import aiohttp
            import asyncio

            pagerduty_payload = {
                "routing_key": self.pagerduty_webhook_url,
                "event_action": "trigger",
                "dedup_key": f"reviewer_metrics_{payload['alert_type']}",
                "payload": {
                    "summary": payload["message"],
                    "severity": "critical",
                    "source": "morningai-reviewer-metrics",
                    "component": "LLM Reviewer Agent",
                    "custom_details": {
                        "metric_name": payload.get("metric_name"),
                        "current_value": payload.get("current_value"),
                        "threshold": payload.get("threshold"),
                        "timestamp": payload["timestamp"],
                    }
                }
            }

            async def send():
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://events.pagerduty.com/v2/enqueue",
                        json=pagerduty_payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        return response.status < 300

            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop is not None:
                logger.debug(
                    "[ReviewerMetricsAlertEvaluator] Detected running event loop, "
                    "scheduling PagerDuty alert as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[ReviewerMetricsAlertEvaluator] PagerDuty alert task failed: {exc}"
                            )
                    except asyncio.CancelledError:
                        pass

                task = running_loop.create_task(send())
                task.add_done_callback(handle_task_exception)
                return {"success": True, "scheduled": True}

            loop = asyncio.new_event_loop()
            try:
                success = loop.run_until_complete(send())
            finally:
                loop.close()

            return {"success": success}

        except Exception as e:
            logger.warning(f"[ReviewerMetricsAlertEvaluator] PagerDuty alert failed: {e}")
            return {"success": False, "error": str(e)}

    def _format_slack_message(self, payload: Dict[str, Any]) -> str:
        """Format alert payload as Slack message."""
        severity = payload["severity"]
        severity_emoji = ":rotating_light:" if severity == "critical" else ":warning:"

        current_value = payload.get("current_value")
        threshold = payload.get("threshold")

        if isinstance(current_value, float) and current_value < 1:
            current_str = f"{current_value:.2%}"
        elif isinstance(current_value, float):
            current_str = f"{current_value:.0f}"
        else:
            current_str = str(current_value)

        if isinstance(threshold, float) and threshold < 1:
            threshold_str = f"{threshold:.2%}"
        elif isinstance(threshold, float):
            threshold_str = f"{threshold:.0f}"
        else:
            threshold_str = str(threshold)

        return (
            f"{severity_emoji} *LLM Reviewer Metrics Alert*\n"
            f"*Alert Type:* `{payload['alert_type']}`\n"
            f"*Severity:* {severity.upper()}\n"
            f"*Metric:* {payload.get('metric_name', 'N/A')}\n"
            f"*Current Value:* {current_str}\n"
            f"*Threshold:* {threshold_str}\n"
            f"*Message:* {payload['message']}\n"
            f"*Time:* {payload['timestamp']}"
        )

    def start_scheduler(self, interval_minutes: int = 5) -> None:
        """
        Start the background scheduler thread.

        Args:
            interval_minutes: Evaluation interval in minutes (default: 5)
        """
        if not self.enabled:
            logger.info(
                "[ReviewerMetricsAlertEvaluator] Scheduler not started (disabled)"
            )
            return

        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning(
                "[ReviewerMetricsAlertEvaluator] Scheduler already running"
            )
            return

        self._interval_minutes = interval_minutes
        self.interval_minutes = interval_minutes  # Sync public property
        self._stop_event.clear()

        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="ReviewerMetricsAlertScheduler",
            daemon=True
        )
        self._scheduler_thread.start()

        logger.info(
            f"[ReviewerMetricsAlertEvaluator] Scheduler started "
            f"(interval={interval_minutes}min)"
        )

    def stop_scheduler(self) -> None:
        """Stop the background scheduler thread."""
        self._stop_event.set()

        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=10)
            if self._scheduler_thread.is_alive():
                logger.warning(
                    "[ReviewerMetricsAlertEvaluator] Scheduler thread did not stop cleanly"
                )
            self._scheduler_thread = None

        logger.info("[ReviewerMetricsAlertEvaluator] Scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Background scheduler loop."""
        logger.info("[ReviewerMetricsAlertEvaluator] Scheduler loop started")

        while not self._stop_event.is_set():
            try:
                self.evaluate_and_alert()
            except Exception as e:
                logger.warning(
                    f"[ReviewerMetricsAlertEvaluator] Scheduler evaluation error: {e}"
                )

            # Wait for interval or stop event
            self._stop_event.wait(timeout=self._interval_minutes * 60)

        logger.info("[ReviewerMetricsAlertEvaluator] Scheduler loop exited")

    def get_cooldown_status(self) -> Dict[str, Any]:
        """Get current cooldown status for all alert types."""
        alert_types = [
            "reviewer_json_parse_failure_warning",
            "reviewer_json_parse_failure_critical",
            "reviewer_success_rate_low",
            "reviewer_cross_provider_fallback_high",
        ]

        status = {}
        for alert_type in alert_types:
            status[alert_type] = {
                "in_cooldown": self._is_in_cooldown(alert_type),
            }

        return status

    def clear_cooldown(self, alert_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear cooldown for specified alert type or all types.

        Args:
            alert_type: Specific alert type to clear, or None for all

        Returns:
            Dict with cleared alert types
        """
        alert_types = [alert_type] if alert_type else [
            "reviewer_json_parse_failure_warning",
            "reviewer_json_parse_failure_critical",
            "reviewer_success_rate_low",
            "reviewer_cross_provider_fallback_high",
        ]

        cleared = []
        for at in alert_types:
            cooldown_key = f"reviewer_metrics_alert:{at}"

            if self.redis_client:
                try:
                    self.redis_client.delete(cooldown_key)
                except Exception as e:
                    logger.warning(
                        f"[ReviewerMetricsAlertEvaluator] Redis cooldown clear failed: {e}"
                    )

            with self._lock:
                if at in self._last_alert_time:
                    del self._last_alert_time[at]

            cleared.append(at)

        logger.info(f"[ReviewerMetricsAlertEvaluator] Cleared cooldown for: {cleared}")
        return {"cleared": cleared}


# Global evaluator instance (singleton pattern)
_global_reviewer_alert_evaluator: Optional[ReviewerMetricsAlertEvaluator] = None
_global_reviewer_alert_evaluator_lock = threading.Lock()


def get_reviewer_metrics_alert_evaluator(
    enabled: Optional[bool] = None,
    json_parse_failure_warning_threshold: Optional[float] = None,
    json_parse_failure_critical_threshold: Optional[float] = None,
    success_rate_threshold: Optional[float] = None,
    cross_provider_fallback_threshold: Optional[float] = None,
    cooldown_minutes: Optional[int] = None,
    min_reviews: Optional[int] = None,
    window_minutes: Optional[int] = None,
    slack_webhook_url: Optional[str] = None,
    pagerduty_webhook_url: Optional[str] = None,
    redis_client: Optional[Any] = None,
) -> ReviewerMetricsAlertEvaluator:
    """
    Get the global ReviewerMetricsAlertEvaluator instance.

    Thread-safe singleton. On first call, creates instance with provided or default config.
    Subsequent calls return existing instance (config params ignored).

    Args:
        enabled: Whether alerting is enabled (default: from settings or False)
        json_parse_failure_warning_threshold: Warning threshold (default: 0.10)
        json_parse_failure_critical_threshold: Critical threshold (default: 0.25)
        success_rate_threshold: Success rate threshold (default: 0.90)
        cross_provider_fallback_threshold: Fallback rate threshold (default: 0.30)
        cooldown_minutes: Cooldown period (default: 15)
        min_reviews: Minimum reviews before alerting (default: 5)
        window_minutes: Metrics window (default: 15)
        slack_webhook_url: Slack webhook URL
        pagerduty_webhook_url: PagerDuty webhook URL
        redis_client: Redis client for cooldown state

    Returns:
        The global ReviewerMetricsAlertEvaluator singleton
    """
    global _global_reviewer_alert_evaluator

    if _global_reviewer_alert_evaluator is None:
        with _global_reviewer_alert_evaluator_lock:
            if _global_reviewer_alert_evaluator is None:
                # Try to load from settings
                try:
                    from common.config.settings import settings
                    _enabled = enabled if enabled is not None else getattr(
                        settings, 'reviewer_metrics_alerting_enabled', False
                    )
                    _slack_url = slack_webhook_url or getattr(
                        settings, 'slack_webhook_url', None
                    )
                    _pagerduty_url = pagerduty_webhook_url or getattr(
                        settings, 'pagerduty_webhook_url', None
                    )
                except Exception:
                    _enabled = enabled if enabled is not None else False
                    _slack_url = slack_webhook_url
                    _pagerduty_url = pagerduty_webhook_url

                _global_reviewer_alert_evaluator = ReviewerMetricsAlertEvaluator(
                    enabled=_enabled,
                    json_parse_failure_warning_threshold=(
                        json_parse_failure_warning_threshold or 0.10
                    ),
                    json_parse_failure_critical_threshold=(
                        json_parse_failure_critical_threshold or 0.25
                    ),
                    success_rate_threshold=success_rate_threshold or 0.90,
                    cross_provider_fallback_threshold=cross_provider_fallback_threshold or 0.30,
                    cooldown_minutes=cooldown_minutes or 15,
                    min_reviews=min_reviews or 5,
                    window_minutes=window_minutes or 15,
                    slack_webhook_url=_slack_url,
                    pagerduty_webhook_url=_pagerduty_url,
                    redis_client=redis_client,
                )

    return _global_reviewer_alert_evaluator


def reset_reviewer_metrics_alert_evaluator() -> None:
    """Reset the global evaluator instance. Use with caution."""
    global _global_reviewer_alert_evaluator
    with _global_reviewer_alert_evaluator_lock:
        if _global_reviewer_alert_evaluator is not None:
            _global_reviewer_alert_evaluator.stop_scheduler()
        _global_reviewer_alert_evaluator = None
    logger.info("[ReviewerMetricsAlertEvaluator] Global instance reset")
