"""
Health Alerter - Provider Health Alerting Service

EPIC I-3a: Health Alerting (Blueprint 4.3 - Model Governance Framework v2)

This module provides alerting capabilities for provider health degradation.
It monitors health scores from CanaryMetrics and sends alerts via configured
notification channels when thresholds are breached.

Key Features:
- Threshold-based alerting (health score below threshold)
- Error rate spike detection (immediate alerts)
- Cooldown mechanism (prevents alert storms)
- Minimum sample size (prevents noise during low traffic)
- Multi-channel notifications (Slack, webhook, email)

Safety Contract:
- This is an observe-only feature - alerts do not affect routing decisions
- Notification failures are logged but never block the main service
- All operations are wrapped in try/except
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class HealthAlertService:
    """
    Service for monitoring provider health and sending alerts

    EPIC I-3a: Health Alerting

    This service periodically checks provider health scores and sends
    alerts when thresholds are breached. It integrates with the existing
    NotificationService for multi-channel delivery.
    """

    def __init__(
        self,
        enabled: bool = False,
        health_threshold: float = 70.0,
        cooldown_minutes: int = 15,
        min_requests: int = 10,
        error_rate_threshold: float = 10.0,
        slack_webhook_url: Optional[str] = None,
        ops_webhook_url: Optional[str] = None,
    ):
        """
        Initialize Health Alert Service

        Args:
            enabled: Whether alerting is enabled
            health_threshold: Health score below which alerts are triggered
            cooldown_minutes: Minimum time between alerts for same provider
            min_requests: Minimum requests in window before alerting
            error_rate_threshold: Error rate (%) that triggers immediate alert
            slack_webhook_url: Slack webhook URL for notifications
            ops_webhook_url: Ops webhook URL for notifications
        """
        self.enabled = enabled
        self.health_threshold = health_threshold
        self.cooldown_minutes = cooldown_minutes
        self.min_requests = min_requests
        self.error_rate_threshold = error_rate_threshold
        self.slack_webhook_url = slack_webhook_url
        self.ops_webhook_url = ops_webhook_url

        # Track last alert time per provider (for cooldown)
        self._last_alert_time: Dict[str, datetime] = {}
        self._lock = threading.Lock()

        logger.info(
            f"[HealthAlertService] Initialized: enabled={enabled}, "
            f"threshold={health_threshold}, cooldown={cooldown_minutes}min"
        )

    def check_and_alert(
        self,
        provider: str,
        health_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check provider health and send alert if needed

        EPIC I-3a: Health Alerting

        Args:
            provider: Provider name
            health_data: Health data from get_provider_health()

        Returns:
            Alert result dict if alert was sent, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Extract metrics from health data
            health_score = health_data.get("health_score")
            error_rate = health_data.get("error_rate", 0)
            total_requests = health_data.get("total_requests", 0)

            # Skip if not enough data
            if health_score is None:
                logger.debug(f"[HealthAlertService] No health score for {provider}")
                return None

            if total_requests < self.min_requests:
                logger.debug(
                    f"[HealthAlertService] Insufficient requests for {provider}: "
                    f"{total_requests} < {self.min_requests}"
                )
                return None

            # Check if alert is needed
            alert_reason = self._should_alert(provider, health_score, error_rate)
            if not alert_reason:
                return None

            # Check cooldown
            if self._is_in_cooldown(provider):
                logger.debug(
                    f"[HealthAlertService] Provider {provider} in cooldown, skipping alert"
                )
                return None

            # Send alert
            result = self._send_alert(provider, health_data, alert_reason)

            # Update cooldown
            self._update_cooldown(provider)

            return result

        except Exception as e:
            logger.warning(f"[HealthAlertService] Error checking {provider}: {e}")
            return None

    def _should_alert(
        self,
        provider: str,
        health_score: float,
        error_rate: float
    ) -> Optional[str]:
        """
        Determine if an alert should be sent

        Returns:
            Alert reason string if alert needed, None otherwise
        """
        # Check error rate threshold (immediate alert)
        if error_rate >= self.error_rate_threshold:
            return f"error_rate_spike ({error_rate:.1f}% >= {self.error_rate_threshold}%)"

        # Check health score threshold
        if health_score < self.health_threshold:
            return f"low_health_score ({health_score:.1f} < {self.health_threshold})"

        return None

    def _is_in_cooldown(self, provider: str) -> bool:
        """Check if provider is in cooldown period"""
        with self._lock:
            last_alert = self._last_alert_time.get(provider)
            if last_alert is None:
                return False

            cooldown_end = last_alert + timedelta(minutes=self.cooldown_minutes)
            return datetime.utcnow() < cooldown_end

    def _update_cooldown(self, provider: str) -> None:
        """Update last alert time for provider"""
        with self._lock:
            self._last_alert_time[provider] = datetime.utcnow()

    def _send_alert(
        self,
        provider: str,
        health_data: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """
        Send alert via configured channels

        EPIC I-3a: Health Alerting

        This method sends alerts via Slack and/or webhook. Failures are
        logged but never propagated (observe-only contract).
        """
        alert_payload = self._build_alert_payload(provider, health_data, reason)

        results = {
            "provider": provider,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "channels": {}
        }

        # Send to Slack
        if self.slack_webhook_url:
            slack_result = self._send_slack_alert(alert_payload)
            results["channels"]["slack"] = slack_result

        # Send to Ops webhook
        if self.ops_webhook_url:
            webhook_result = self._send_webhook_alert(alert_payload)
            results["channels"]["webhook"] = webhook_result

        # Log the alert
        logger.warning(
            f"[HealthAlertService] ALERT: Provider {provider} - {reason}. "
            f"Health: {health_data.get('health_score', 'N/A'):.1f}, "
            f"Error Rate: {health_data.get('error_rate', 0):.1f}%"
        )

        return results

    def _build_alert_payload(
        self,
        provider: str,
        health_data: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Build alert payload for notifications"""
        return {
            "alert_type": "provider_health_degradation",
            "provider": provider,
            "reason": reason,
            "health_score": health_data.get("health_score"),
            "error_rate": health_data.get("error_rate", 0),
            "latency_p95_ms": health_data.get("latency", {}).get("p95_ms"),
            "drift_rate": health_data.get("drift_rate", 0),
            "total_requests": health_data.get("total_requests", 0),
            "window_minutes": health_data.get("window_minutes", 15),
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "critical" if "error_rate_spike" in reason else "warning",
        }

    def _send_slack_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Slack webhook"""
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

            # Run async in sync context
            loop = asyncio.new_event_loop()
            try:
                success = loop.run_until_complete(send())
            finally:
                loop.close()

            return {"success": success}

        except Exception as e:
            logger.warning(f"[HealthAlertService] Slack alert failed: {e}")
            return {"success": False, "error": str(e)}

    def _send_webhook_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to ops webhook"""
        try:
            import aiohttp
            import asyncio

            async def send():
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.ops_webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        return response.status < 400

            # Run async in sync context
            loop = asyncio.new_event_loop()
            try:
                success = loop.run_until_complete(send())
            finally:
                loop.close()

            return {"success": success}

        except Exception as e:
            logger.warning(f"[HealthAlertService] Webhook alert failed: {e}")
            return {"success": False, "error": str(e)}

    def _format_slack_message(self, payload: Dict[str, Any]) -> str:
        """Format alert payload as Slack message"""
        severity_emoji = ":rotating_light:" if payload["severity"] == "critical" else ":warning:"
        provider = payload["provider"]
        reason = payload["reason"]
        health = payload.get("health_score", "N/A")
        error_rate = payload.get("error_rate", 0)
        latency = payload.get("latency_p95_ms", "N/A")

        # Format health score with proper handling
        if isinstance(health, (int, float)):
            health_str = f"{health:.1f}"
        else:
            health_str = str(health)

        return (
            f"{severity_emoji} *Provider Health Alert*\n"
            f"*Provider:* `{provider}`\n"
            f"*Reason:* {reason}\n"
            f"*Health Score:* {health_str}\n"
            f"*Error Rate:* {error_rate:.1f}%\n"
            f"*Latency (p95):* {latency}ms\n"
            f"*Time:* {payload['timestamp']}"
        )

    def check_all_providers(
        self,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check health for all providers and send alerts as needed

        EPIC I-3a: Health Alerting

        This method is designed to be called periodically (e.g., by a background task)
        to check all provider health scores and send alerts.

        Args:
            providers: List of provider names (default: all known providers)

        Returns:
            Dict with check results and any alerts sent
        """
        if not self.enabled:
            return {"enabled": False}

        if providers is None:
            providers = ["openai", "gemini", "alicloud", "siliconflow"]

        try:
            from metrics import get_canary_metrics

            metrics = get_canary_metrics()
            if metrics is None:
                logger.debug("[HealthAlertService] CanaryMetrics not available")
                return {"enabled": True, "error": "metrics_unavailable"}

            results = {
                "enabled": True,
                "timestamp": datetime.utcnow().isoformat(),
                "providers_checked": [],
                "alerts_sent": []
            }

            for provider in providers:
                health_data = metrics.get_provider_health(provider)
                alert_result = self.check_and_alert(provider, health_data)

                results["providers_checked"].append(provider)
                if alert_result:
                    results["alerts_sent"].append(alert_result)

            return results

        except Exception as e:
            logger.warning(f"[HealthAlertService] Error checking all providers: {e}")
            return {"enabled": True, "error": str(e)}

    def get_cooldown_status(self) -> Dict[str, Any]:
        """Get current cooldown status for all providers"""
        with self._lock:
            now = datetime.utcnow()
            status = {}
            for provider, last_alert in self._last_alert_time.items():
                cooldown_end = last_alert + timedelta(minutes=self.cooldown_minutes)
                remaining = (cooldown_end - now).total_seconds()
                status[provider] = {
                    "last_alert": last_alert.isoformat(),
                    "cooldown_remaining_seconds": max(0, remaining),
                    "in_cooldown": remaining > 0
                }
            return status

    def clear_cooldown(self, provider: Optional[str] = None) -> None:
        """Clear cooldown for a provider or all providers (for testing)"""
        with self._lock:
            if provider:
                self._last_alert_time.pop(provider, None)
            else:
                self._last_alert_time.clear()


# Global singleton for health alert service (EPIC I-3a)
_health_alert_service: Optional[HealthAlertService] = None
_health_alert_service_lock = threading.Lock()


def get_health_alert_service() -> Optional[HealthAlertService]:
    """
    Get the global HealthAlertService singleton instance

    EPIC I-3a: Health Alerting

    This function provides thread-safe access to the global alert service.
    Returns None if alerting is disabled or not configured.

    Returns:
        HealthAlertService instance or None if not available
    """
    global _health_alert_service

    if _health_alert_service is not None:
        return _health_alert_service

    with _health_alert_service_lock:
        if _health_alert_service is not None:
            return _health_alert_service

        try:
            from common.config.settings import settings

            if not getattr(settings, "health_alerting_enabled", False):
                logger.debug("[HealthAlertService] Alerting disabled")
                return None

            _health_alert_service = HealthAlertService(
                enabled=True,
                health_threshold=getattr(settings, "health_alert_threshold", 70.0),
                cooldown_minutes=getattr(settings, "health_alert_cooldown_minutes", 15),
                min_requests=getattr(settings, "health_alert_min_requests", 10),
                error_rate_threshold=getattr(
                    settings, "health_alert_error_rate_threshold", 10.0
                ),
                slack_webhook_url=getattr(settings, "slack_webhook_url", None),
                ops_webhook_url=getattr(settings, "ops_alert_webhook_url", None),
            )

            logger.info("[HealthAlertService] Initialized global alert service")
            return _health_alert_service

        except Exception as e:
            logger.warning(f"[HealthAlertService] Failed to initialize: {e}")
            return None


def reset_health_alert_service() -> None:
    """
    Reset the global HealthAlertService singleton (useful for testing)

    EPIC I-3a: Health Alerting
    """
    global _health_alert_service
    with _health_alert_service_lock:
        _health_alert_service = None
