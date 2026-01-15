"""
Router Metrics Alert Evaluator - Scheduled Alert Service for Flow Controller v3

EPIC C: Flow Controller v3 - RouterMetrics Operationalization
Issue #3499: Scheduled Alert Evaluator for RouterMetrics

This module provides scheduled alerting capabilities for RouterMetrics.
It periodically polls the RouterMetrics API and sends alerts via configured
notification channels when thresholds are breached.

Key Features:
- Threshold-based alerting (success rate, latency p99, fallback rate)
- Slow path ratio monitoring
- Cooldown mechanism (prevents alert storms)
- Multi-channel notifications (Slack, PagerDuty webhook)
- Redis-based alert state for cooldown tracking

Alert Conditions (from monitoring_foundation_schema.yaml):
- router_success_rate < 0.95 -> Critical (PagerDuty + Slack)
- router_latency_p99 > 5000ms -> Critical (PagerDuty + Slack)
- router_fallback_rate > 0.20 -> Warning (Slack)
- slow_path_ratio > 0.50 -> Warning (Slack)

Safety Contract:
- This is an observe-only feature - alerts do not affect routing decisions
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


class RouterMetricsAlertEvaluator:
    """
    Service for monitoring RouterMetrics and sending alerts.

    EPIC C: Flow Controller v3 - RouterMetrics Operationalization
    Issue #3499: Scheduled Alert Evaluator for RouterMetrics

    This service periodically checks RouterMetrics and sends alerts
    when thresholds are breached. It integrates with Slack and PagerDuty
    for multi-channel delivery.
    """

    def __init__(
        self,
        enabled: bool = False,
        success_rate_threshold: float = 0.95,
        latency_p99_threshold_ms: float = 5000.0,
        fallback_rate_threshold: float = 0.20,
        slow_path_ratio_threshold: float = 0.50,
        cooldown_minutes: int = 15,
        min_decisions: int = 10,
        window_minutes: int = 15,
        slack_webhook_url: Optional[str] = None,
        pagerduty_webhook_url: Optional[str] = None,
        redis_client: Optional[Any] = None,
    ):
        """
        Initialize Router Metrics Alert Evaluator.

        Args:
            enabled: Whether alerting is enabled
            success_rate_threshold: Success rate below which critical alerts are triggered
            latency_p99_threshold_ms: P99 latency (ms) above which critical alerts are triggered
            fallback_rate_threshold: Fallback rate above which warning alerts are triggered
            slow_path_ratio_threshold: Slow path ratio above which warning alerts are triggered
            cooldown_minutes: Minimum time between alerts for same alert type
            min_decisions: Minimum decisions in window before alerting
            window_minutes: Time window for metrics evaluation
            slack_webhook_url: Slack webhook URL for notifications
            pagerduty_webhook_url: PagerDuty webhook URL for critical alerts
            redis_client: Redis client for cooldown state (optional, uses in-memory if None)
        """
        self.enabled = enabled
        self.success_rate_threshold = success_rate_threshold
        self.latency_p99_threshold_ms = latency_p99_threshold_ms
        self.fallback_rate_threshold = fallback_rate_threshold
        self.slow_path_ratio_threshold = slow_path_ratio_threshold
        self.cooldown_minutes = cooldown_minutes
        self.min_decisions = min_decisions
        self.window_minutes = window_minutes
        self.slack_webhook_url = slack_webhook_url
        self.pagerduty_webhook_url = pagerduty_webhook_url
        self.redis_client = redis_client

        self._last_alert_time: Dict[str, datetime] = {}
        self._lock = threading.Lock()

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval_minutes = 5

        logger.info(
            f"[RouterMetricsAlertEvaluator] Initialized: enabled={enabled}, "
            f"success_rate_threshold={success_rate_threshold}, "
            f"latency_p99_threshold={latency_p99_threshold_ms}ms, "
            f"cooldown={cooldown_minutes}min"
        )

    def evaluate_and_alert(self) -> Dict[str, Any]:
        """
        Evaluate RouterMetrics and send alerts if thresholds are breached.

        EPIC C: Flow Controller v3 - RouterMetrics Operationalization

        Returns:
            Dict with evaluation results and any alerts sent
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            from core.flow.router_metrics import get_router_metrics

            metrics = get_router_metrics()
            summary = metrics.get_summary(window_minutes=self.window_minutes)

            results = {
                "enabled": True,
                "timestamp": _get_utc_timestamp(),
                "window_minutes": self.window_minutes,
                "metrics_evaluated": True,
                "alerts_sent": [],
                "alerts_skipped": [],
            }

            total_decisions = summary.get("total_decisions", 0)
            if total_decisions < self.min_decisions:
                results["metrics_evaluated"] = False
                results["reason"] = (
                    f"Insufficient decisions: {total_decisions} < {self.min_decisions}"
                )
                logger.debug(
                    f"[RouterMetricsAlertEvaluator] Skipping evaluation: {results['reason']}"
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
            logger.warning(f"[RouterMetricsAlertEvaluator] Evaluation failed: {e}")
            return {"enabled": True, "error": str(e)}

    def _check_thresholds(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check all alert thresholds and return list of alerts to send.

        Args:
            summary: RouterMetrics summary dict

        Returns:
            List of alert dicts to send
        """
        alerts = []

        success_rate = summary.get("success_rate", 1.0)
        if success_rate < self.success_rate_threshold:
            alerts.append({
                "alert_type": "router_success_rate_low",
                "severity": "critical",
                "metric_name": "router_success_rate",
                "current_value": success_rate,
                "threshold": self.success_rate_threshold,
                "message": (
                    f"Router success rate ({success_rate:.2%}) is below "
                    f"threshold ({self.success_rate_threshold:.2%})"
                ),
            })

        latency_p99 = summary.get("latency_p99_ms")
        if latency_p99 is not None and latency_p99 > self.latency_p99_threshold_ms:
            alerts.append({
                "alert_type": "router_latency_p99_high",
                "severity": "critical",
                "metric_name": "router_latency_p99",
                "current_value": latency_p99,
                "threshold": self.latency_p99_threshold_ms,
                "message": (
                    f"Router P99 latency ({latency_p99:.0f}ms) exceeds "
                    f"threshold ({self.latency_p99_threshold_ms:.0f}ms)"
                ),
            })

        fallback_rate = summary.get("fallback_rate", 0.0)
        if fallback_rate > self.fallback_rate_threshold:
            alerts.append({
                "alert_type": "router_fallback_rate_high",
                "severity": "warning",
                "metric_name": "router_fallback_rate",
                "current_value": fallback_rate,
                "threshold": self.fallback_rate_threshold,
                "message": (
                    f"Router fallback rate ({fallback_rate:.2%}) exceeds "
                    f"threshold ({self.fallback_rate_threshold:.2%})"
                ),
            })

        mode_dist = summary.get("decision_mode_distribution", {})
        total = summary.get("total_decisions", 0)
        if total > 0:
            slow_path_count = mode_dist.get("slow_path", 0)
            slow_path_ratio = slow_path_count / total
            if slow_path_ratio > self.slow_path_ratio_threshold:
                alerts.append({
                    "alert_type": "router_slow_path_dominant",
                    "severity": "warning",
                    "metric_name": "slow_path_ratio",
                    "current_value": slow_path_ratio,
                    "threshold": self.slow_path_ratio_threshold,
                    "message": (
                        f"Router slow path ratio ({slow_path_ratio:.2%}) exceeds "
                        f"threshold ({self.slow_path_ratio_threshold:.2%})"
                    ),
                })

        return alerts

    def _is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period."""
        cooldown_key = f"router_metrics_alert:{alert_type}"

        if self.redis_client:
            try:
                exists = self.redis_client.exists(cooldown_key)
                return bool(exists)
            except Exception as e:
                logger.warning(
                    f"[RouterMetricsAlertEvaluator] Redis cooldown check failed: {e}, "
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
        cooldown_key = f"router_metrics_alert:{alert_type}"
        cooldown_seconds = self.cooldown_minutes * 60

        if self.redis_client:
            try:
                self.redis_client.setex(cooldown_key, cooldown_seconds, "1")
                return
            except Exception as e:
                logger.warning(
                    f"[RouterMetricsAlertEvaluator] Redis cooldown update failed: {e}, "
                    f"falling back to in-memory"
                )

        with self._lock:
            self._last_alert_time[alert_type] = datetime.now(timezone.utc)

    def _send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert via configured channels.

        EPIC C: Flow Controller v3 - RouterMetrics Operationalization

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
            f"[RouterMetricsAlertEvaluator] ALERT: {alert['alert_type']} - "
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
            "source": "router_metrics_alert_evaluator",
            "epic": "EPIC-C",
            "component": "Flow Controller v3",
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
                    "[RouterMetricsAlertEvaluator] Detected running event loop, "
                    "scheduling Slack alert as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[RouterMetricsAlertEvaluator] Slack alert task failed: {exc}"
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
            logger.warning(f"[RouterMetricsAlertEvaluator] Slack alert failed: {e}")
            return {"success": False, "error": str(e)}

    def _send_pagerduty_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to PagerDuty webhook."""
        try:
            import aiohttp
            import asyncio

            pagerduty_payload = {
                "routing_key": self.pagerduty_webhook_url,
                "event_action": "trigger",
                "dedup_key": f"router_metrics_{payload['alert_type']}",
                "payload": {
                    "summary": payload["message"],
                    "severity": "critical",
                    "source": "morningai-router-metrics",
                    "component": "Flow Controller v3",
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
                    "[RouterMetricsAlertEvaluator] Detected running event loop, "
                    "scheduling PagerDuty alert as background task"
                )

                def handle_task_exception(task):
                    try:
                        exc = task.exception()
                        if exc:
                            logger.warning(
                                f"[RouterMetricsAlertEvaluator] PagerDuty alert task failed: {exc}"
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
            logger.warning(f"[RouterMetricsAlertEvaluator] PagerDuty alert failed: {e}")
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
            f"{severity_emoji} *Router Metrics Alert*\n"
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

        EPIC C: Flow Controller v3 - RouterMetrics Operationalization

        Args:
            interval_minutes: Evaluation interval in minutes (default: 5)
        """
        if not self.enabled:
            logger.info(
                "[RouterMetricsAlertEvaluator] Scheduler not started (disabled)"
            )
            return

        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning(
                "[RouterMetricsAlertEvaluator] Scheduler already running"
            )
            return

        self._interval_minutes = interval_minutes
        self._stop_event.clear()

        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="RouterMetricsAlertScheduler",
            daemon=True
        )
        self._scheduler_thread.start()

        logger.info(
            f"[RouterMetricsAlertEvaluator] Scheduler started "
            f"(interval={interval_minutes}min)"
        )

    def stop_scheduler(self) -> None:
        """Stop the background scheduler thread."""
        self._stop_event.set()

        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=10)
            if self._scheduler_thread.is_alive():
                logger.warning(
                    "[RouterMetricsAlertEvaluator] Scheduler thread did not stop cleanly"
                )
            else:
                logger.info(
                    "[RouterMetricsAlertEvaluator] Scheduler stopped"
                )

        self._scheduler_thread = None

    def _scheduler_loop(self) -> None:
        """Background scheduler loop."""
        logger.info(
            "[RouterMetricsAlertEvaluator] Scheduler thread started"
        )

        while not self._stop_event.is_set():
            try:
                result = self.evaluate_and_alert()
                alerts_sent = len(result.get("alerts_sent", []))
                alerts_skipped = len(result.get("alerts_skipped", []))

                logger.info(
                    f"[RouterMetricsAlertEvaluator] Evaluation complete: "
                    f"alerts_sent={alerts_sent}, alerts_skipped={alerts_skipped}",
                    extra={
                        "operation": "router_metrics_alert",
                        "alerts_sent": alerts_sent,
                        "alerts_skipped": alerts_skipped,
                    }
                )

            except Exception as e:
                logger.warning(
                    f"[RouterMetricsAlertEvaluator] Scheduler iteration failed: {e}"
                )

            self._stop_event.wait(self._interval_minutes * 60)

        logger.info(
            "[RouterMetricsAlertEvaluator] Scheduler thread stopped"
        )

    def get_cooldown_status(self) -> Dict[str, Any]:
        """Get current cooldown status for all alert types."""
        alert_types = [
            "router_success_rate_low",
            "router_latency_p99_high",
            "router_fallback_rate_high",
            "router_slow_path_dominant",
        ]

        status = {}
        for alert_type in alert_types:
            status[alert_type] = {
                "in_cooldown": self._is_in_cooldown(alert_type)
            }

        return status

    def clear_cooldown(self, alert_type: Optional[str] = None) -> None:
        """Clear cooldown for an alert type or all alert types (for testing)."""
        if alert_type:
            cooldown_key = f"router_metrics_alert:{alert_type}"
            if self.redis_client:
                try:
                    self.redis_client.delete(cooldown_key)
                except Exception:
                    pass
            with self._lock:
                self._last_alert_time.pop(alert_type, None)
        else:
            alert_types = [
                "router_success_rate_low",
                "router_latency_p99_high",
                "router_fallback_rate_high",
                "router_slow_path_dominant",
            ]
            for at in alert_types:
                cooldown_key = f"router_metrics_alert:{at}"
                if self.redis_client:
                    try:
                        self.redis_client.delete(cooldown_key)
                    except Exception:
                        pass
            with self._lock:
                self._last_alert_time.clear()


_router_metrics_alert_evaluator: Optional[RouterMetricsAlertEvaluator] = None
_router_metrics_alert_evaluator_lock = threading.Lock()


def get_router_metrics_alert_evaluator() -> Optional[RouterMetricsAlertEvaluator]:
    """
    Get the global RouterMetricsAlertEvaluator singleton instance.

    EPIC C: Flow Controller v3 - RouterMetrics Operationalization
    Issue #3499: Scheduled Alert Evaluator for RouterMetrics

    This function provides thread-safe access to the global alert evaluator.
    Returns None if alerting is disabled or not configured.

    Returns:
        RouterMetricsAlertEvaluator instance or None if not available
    """
    global _router_metrics_alert_evaluator

    if _router_metrics_alert_evaluator is not None:
        return _router_metrics_alert_evaluator

    with _router_metrics_alert_evaluator_lock:
        if _router_metrics_alert_evaluator is not None:
            return _router_metrics_alert_evaluator

        try:
            from common.config.settings import settings

            if not getattr(settings, "router_metrics_alerting_enabled", False):
                logger.debug("[RouterMetricsAlertEvaluator] Alerting disabled")
                return None

            redis_client = None
            try:
                from redis import Redis
                redis_url = getattr(settings, "redis_url", None)
                if redis_url:
                    redis_client = Redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.debug(
                    f"[RouterMetricsAlertEvaluator] Redis not available: {e}"
                )

            _router_metrics_alert_evaluator = RouterMetricsAlertEvaluator(
                enabled=True,
                success_rate_threshold=getattr(
                    settings, "router_alert_success_rate_threshold", 0.95
                ),
                latency_p99_threshold_ms=getattr(
                    settings, "router_alert_latency_p99_threshold_ms", 5000.0
                ),
                fallback_rate_threshold=getattr(
                    settings, "router_alert_fallback_rate_threshold", 0.20
                ),
                slow_path_ratio_threshold=getattr(
                    settings, "router_alert_slow_path_ratio_threshold", 0.50
                ),
                cooldown_minutes=getattr(
                    settings, "router_alert_cooldown_minutes", 15
                ),
                min_decisions=getattr(
                    settings, "router_alert_min_decisions", 10
                ),
                window_minutes=getattr(
                    settings, "router_alert_window_minutes", 15
                ),
                slack_webhook_url=getattr(settings, "slack_webhook_url", None),
                pagerduty_webhook_url=getattr(
                    settings, "pagerduty_routing_key", None
                ),
                redis_client=redis_client,
            )

            logger.info(
                "[RouterMetricsAlertEvaluator] Initialized global alert evaluator"
            )
            return _router_metrics_alert_evaluator

        except Exception as e:
            logger.warning(
                f"[RouterMetricsAlertEvaluator] Failed to initialize: {e}"
            )
            return None


def reset_router_metrics_alert_evaluator() -> None:
    """
    Reset the global RouterMetricsAlertEvaluator singleton (useful for testing).

    EPIC C: Flow Controller v3 - RouterMetrics Operationalization
    """
    global _router_metrics_alert_evaluator
    with _router_metrics_alert_evaluator_lock:
        if _router_metrics_alert_evaluator is not None:
            _router_metrics_alert_evaluator.stop_scheduler()
        _router_metrics_alert_evaluator = None
