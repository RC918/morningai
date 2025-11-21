#!/usr/bin/env python3
"""
Canary Alerting Module - SLO breach detection and alerting

Evaluates canary metrics against defined SLOs and sends alerts via:
- Sentry (capture_message with tags)
- Optional webhook (Slack/email/custom)

Includes per-alert cooldown to prevent alert storms.
"""

import logging
import os
import time
from typing import Dict, Optional
import redis
import requests
from metrics import DEFAULT_BUCKETS_MS

logger = logging.getLogger(__name__)

class CanaryAlerting:
    """Canary SLO monitoring and alerting"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        enabled: bool = True,
        cooldown_seconds: int = 300,
        sentry_dsn: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        """
        Initialize canary alerting
        
        Args:
            redis_client: Redis client instance
            enabled: Whether alerting is enabled
            cooldown_seconds: Cooldown period between alerts (default: 5 minutes)
            sentry_dsn: Sentry DSN for error tracking
            webhook_url: Optional webhook URL for alerts (Slack/email/custom)
        """
        self.redis = redis_client
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self.sentry_dsn = sentry_dsn
        self.webhook_url = webhook_url
        
        if self.sentry_dsn:
            try:
                import sentry_sdk
                self.sentry_sdk = sentry_sdk
            except ImportError:
                logger.warning("Sentry SDK not available, Sentry alerts disabled")
                self.sentry_sdk = None
        else:
            self.sentry_sdk = None
    
    def _get_cooldown_key(self, alert_type: str) -> str:
        """Get Redis key for alert cooldown"""
        return f"metrics:canary:alert:cooldown:{alert_type}"
    
    def _is_in_cooldown(self, alert_type: str) -> bool:
        """Check if alert type is in cooldown period"""
        if not self.enabled:
            return True
        
        try:
            key = self._get_cooldown_key(alert_type)
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Failed to check cooldown for {alert_type}: {e}")
            return False
    
    def _set_cooldown(self, alert_type: str) -> None:
        """Set cooldown for alert type"""
        if not self.enabled:
            return
        
        try:
            key = self._get_cooldown_key(alert_type)
            self.redis.setex(key, self.cooldown_seconds, "1")
        except Exception as e:
            logger.warning(f"Failed to set cooldown for {alert_type}: {e}")
    
    def _send_sentry_alert(self, alert_type: str, message: str, data: Dict) -> None:
        """Send alert to Sentry"""
        if not self.sentry_sdk:
            return
        
        try:
            self.sentry_sdk.capture_message(
                f"[CanaryAlert] {message}",
                level="error",
                tags={
                    "alert_type": alert_type,
                    "component": "canary_deployment",
                    **{k: str(v) for k, v in data.items()}
                }
            )
            logger.info(f"Sent Sentry alert: {alert_type}")
        except Exception as e:
            logger.error(f"Failed to send Sentry alert: {e}")
    
    def _send_webhook_alert(self, alert_type: str, message: str, data: Dict) -> None:
        """Send alert to webhook"""
        if not self.webhook_url:
            return
        
        try:
            payload = {
                "alert_type": alert_type,
                "message": message,
                "timestamp": time.time(),
                "data": data
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Sent webhook alert: {alert_type}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def evaluate_slos(
        self,
        canary_summary: Dict,
        thresholds: Dict
    ) -> None:
        """
        Evaluate canary metrics against SLO thresholds and send alerts
        
        Args:
            canary_summary: Canary metrics summary from CanaryMetrics.get_canary_summary()
            thresholds: Dict with p95_ms, error_5xx_rate, failure_rate thresholds
        """
        if not self.enabled:
            return
        
        if not canary_summary.get('enabled'):
            return
        
        try:
            latency = canary_summary.get('latency', {})
            rates = canary_summary.get('rates', {})
            counts = canary_summary.get('counts', {})
            
            p95_ms = latency.get('p95_ms')
            error_5xx_rate = rates.get('error_5xx_rate', 0)
            failure_rate = rates.get('failure_rate', 0)
            total_planner = counts.get('total_planner', 0)
            
            if total_planner < 5:
                logger.debug(f"Insufficient canary data for SLO evaluation: {total_planner} tasks")
                return
            
            p95_threshold = thresholds.get('p95_ms', 2500)
            
            if p95_ms is None:
                alert_type = "p95_latency_unbounded"
                if not self._is_in_cooldown(alert_type):
                    max_bucket = canary_summary.get('latency', {}).get('max_bucket_ms', max(DEFAULT_BUCKETS_MS))
                    message = f"Canary p95 latency is unbounded (exceeds max bucket {max_bucket}ms)"
                    data = {
                        "p95_ms": None,
                        "threshold_ms": p95_threshold,
                        "window_minutes": canary_summary.get('window_minutes', 15),
                        "total_tasks": total_planner,
                        "severity": "critical"
                    }
                    
                    self._send_sentry_alert(alert_type, message, data)
                    self._send_webhook_alert(alert_type, message, data)
                    self._set_cooldown(alert_type)
                    
                    logger.warning(f"SLO breach: {message}", extra=data)
            elif p95_ms > p95_threshold:
                alert_type = "p95_latency_breach"
                if not self._is_in_cooldown(alert_type):
                    message = f"Canary p95 latency exceeded: {p95_ms}ms > {p95_threshold}ms"
                    data = {
                        "p95_ms": p95_ms,
                        "threshold_ms": p95_threshold,
                        "window_minutes": canary_summary.get('window_minutes', 15),
                        "total_tasks": total_planner
                    }
                    
                    self._send_sentry_alert(alert_type, message, data)
                    self._send_webhook_alert(alert_type, message, data)
                    self._set_cooldown(alert_type)
                    
                    logger.warning(f"SLO breach: {message}", extra=data)
            
            error_5xx_threshold = thresholds.get('error_5xx_rate', 1.0)
            if error_5xx_rate > error_5xx_threshold:
                alert_type = "error_5xx_rate_breach"
                if not self._is_in_cooldown(alert_type):
                    message = f"Canary 5xx error rate exceeded: {error_5xx_rate}% > {error_5xx_threshold}%"
                    data = {
                        "error_5xx_rate": error_5xx_rate,
                        "threshold_rate": error_5xx_threshold,
                        "window_minutes": canary_summary.get('window_minutes', 15),
                        "total_tasks": total_planner,
                        "error_count": counts.get('planner_error_5xx', 0)
                    }
                    
                    self._send_sentry_alert(alert_type, message, data)
                    self._send_webhook_alert(alert_type, message, data)
                    self._set_cooldown(alert_type)
                    
                    logger.warning(f"SLO breach: {message}", extra=data)
            
            failure_threshold = thresholds.get('failure_rate', 5.0)
            if failure_rate > failure_threshold:
                alert_type = "failure_rate_breach"
                if not self._is_in_cooldown(alert_type):
                    message = f"Canary failure rate exceeded: {failure_rate}% > {failure_threshold}%"
                    data = {
                        "failure_rate": failure_rate,
                        "threshold_rate": failure_threshold,
                        "window_minutes": canary_summary.get('window_minutes', 15),
                        "total_tasks": total_planner,
                        "failure_count": counts.get('planner_failure', 0)
                    }
                    
                    self._send_sentry_alert(alert_type, message, data)
                    self._send_webhook_alert(alert_type, message, data)
                    self._set_cooldown(alert_type)
                    
                    logger.warning(f"SLO breach: {message}", extra=data)
            
        except Exception as e:
            logger.error(f"Failed to evaluate SLOs: {e}")


def create_canary_alerting(
    redis_client: redis.Redis,
    enabled: bool = True,
    sentry_dsn: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> CanaryAlerting:
    """
    Factory function to create CanaryAlerting instance
    
    Args:
        redis_client: Redis client instance
        enabled: Whether alerting is enabled
        sentry_dsn: Sentry DSN for error tracking
        webhook_url: Optional webhook URL for alerts
        
    Returns:
        CanaryAlerting instance
    """
    return CanaryAlerting(
        redis_client,
        enabled=enabled,
        sentry_dsn=sentry_dsn,
        webhook_url=webhook_url
    )
