#!/usr/bin/env python3
"""
Safety Metrics Module - EPIC E Phase E-5

Prometheus-style metrics for safety decision tracking and observability.

Design Principles:
- Thread-safe counters and histograms
- Redis-backed persistence for distributed environments
- Configurable alerting thresholds
- Integration with existing governance modules

Blueprint Reference: Section 4.1 Safety Governor v2
EPIC E Roadmap: Phase E-5 Observability & Ops Readiness
"""
import logging
import os
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class SafetyMetricType(Enum):
    """Types of safety metrics"""
    DECISIONS_TOTAL = "safety_decisions_total"
    SCAN_LATENCY = "safety_scan_latency_seconds"
    OVERRIDE_REQUESTS = "safety_override_requests_total"
    BLOCK_RATE = "safety_block_rate"
    FINDINGS_TOTAL = "safety_findings_total"


@dataclass
class SafetyDecisionEvent:
    """Represents a safety decision event for tracking"""
    timestamp: str
    trace_id: str
    scanner_id: str
    action: str  # allow, block, require_approval, log_only
    category: Optional[str] = None  # prompt_injection, jailbreak, harmful_content
    risk_level: str = "none"
    findings_count: int = 0
    scan_duration_ms: float = 0.0
    content_length: int = 0
    policy_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "scanner_id": self.scanner_id,
            "action": self.action,
            "category": self.category,
            "risk_level": self.risk_level,
            "findings_count": self.findings_count,
            "scan_duration_ms": self.scan_duration_ms,
            "content_length": self.content_length,
            "policy_id": self.policy_id,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


@dataclass
class SafetyOverrideRequest:
    """Represents a safety override request"""
    timestamp: str
    trace_id: str
    original_action: str
    requested_action: str
    reason: str
    requester_id: str
    status: str = "pending"  # pending, approved, rejected
    approver_id: Optional[str] = None
    approved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "original_action": self.original_action,
            "requested_action": self.requested_action,
            "reason": self.reason,
            "requester_id": self.requester_id,
            "status": self.status,
            "approver_id": self.approver_id,
            "approved_at": self.approved_at,
            "metadata": self.metadata,
        }


class SafetyMetricsCollector:
    """
    Collects and aggregates safety metrics for observability.

    EPIC E Phase E-5: Metrics & Alerting

    Tracks:
    - safety_decisions_total (by action, category)
    - safety_scan_latency_seconds
    - safety_override_requests_total
    - Alert on high block rate
    """

    # Latency histogram buckets (in seconds)
    LATENCY_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]

    def __init__(
        self,
        enabled: bool = True,
        redis_client: Optional[Any] = None,
        block_rate_threshold: float = 10.0,
        alert_cooldown_minutes: int = 15,
        window_minutes: int = 15,
    ):
        """
        Initialize SafetyMetricsCollector.

        Args:
            enabled: Whether metrics collection is enabled
            redis_client: Optional Redis client for distributed persistence
            block_rate_threshold: Block rate percentage that triggers alerts
            alert_cooldown_minutes: Cooldown between alerts
            window_minutes: Time window for rate calculations
        """
        self.enabled = enabled
        self.redis = redis_client
        self.block_rate_threshold = block_rate_threshold
        self.alert_cooldown_minutes = alert_cooldown_minutes
        self.window_minutes = window_minutes

        # Thread-safe counters
        self._lock = threading.Lock()

        # In-memory counters (fallback when Redis unavailable)
        self._decisions_total: Dict[Tuple[str, str], int] = defaultdict(int)
        self._findings_total: Dict[str, int] = defaultdict(int)
        self._override_requests: Dict[str, int] = defaultdict(int)
        self._latency_histogram: Dict[str, int] = defaultdict(int)
        self._latency_sum: float = 0.0
        self._latency_count: int = 0

        # Event storage (in-memory, limited size)
        self._decision_events: List[SafetyDecisionEvent] = []
        self._override_events: List[SafetyOverrideRequest] = []
        self._max_events = 1000

        # Alert state
        self._last_alert_time: Optional[float] = None

        self._load_settings()

        logger.info(
            "[SafetyMetrics] Initialized - EPIC E Phase E-5: "
            "enabled=%s, block_rate_threshold=%.1f%%",
            self.enabled,
            self.block_rate_threshold,
        )

    def _load_settings(self) -> None:
        """Load settings from environment"""
        self.enabled = os.getenv(
            "SAFETY_METRICS_ENABLED", "true"
        ).lower() == "true"
        self.block_rate_threshold = float(
            os.getenv("SAFETY_BLOCK_RATE_THRESHOLD", "10.0")
        )
        self.alert_cooldown_minutes = int(
            os.getenv("SAFETY_ALERT_COOLDOWN_MINUTES", "15")
        )
        self.window_minutes = int(
            os.getenv("SAFETY_METRICS_WINDOW_MINUTES", "15")
        )

    def record_decision(
        self,
        trace_id: str,
        scanner_id: str,
        action: str,
        category: Optional[str] = None,
        risk_level: str = "none",
        findings_count: int = 0,
        scan_duration_ms: float = 0.0,
        content_length: int = 0,
        policy_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SafetyDecisionEvent:
        """
        Record a safety decision event.

        Args:
            trace_id: Unique trace identifier
            scanner_id: ID of the scanner that made the decision
            action: Decision action (allow, block, require_approval, log_only)
            category: Category of finding (prompt_injection, jailbreak, etc.)
            risk_level: Risk level (none, low, medium, high, critical)
            findings_count: Number of findings
            scan_duration_ms: Scan duration in milliseconds
            content_length: Length of scanned content
            policy_id: Optional policy ID
            agent_id: Optional agent ID
            metadata: Additional metadata

        Returns:
            SafetyDecisionEvent that was recorded
        """
        if not self.enabled:
            return SafetyDecisionEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=trace_id,
                scanner_id=scanner_id,
                action=action,
            )

        timestamp = datetime.now(timezone.utc).isoformat()

        event = SafetyDecisionEvent(
            timestamp=timestamp,
            trace_id=trace_id,
            scanner_id=scanner_id,
            action=action,
            category=category,
            risk_level=risk_level,
            findings_count=findings_count,
            scan_duration_ms=scan_duration_ms,
            content_length=content_length,
            policy_id=policy_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )

        with self._lock:
            # Increment decision counter
            key = (action, category or "none")
            self._decisions_total[key] += 1

            # Increment findings counter
            if category:
                self._findings_total[category] += findings_count

            # Record latency
            latency_seconds = scan_duration_ms / 1000.0
            self._record_latency(latency_seconds)

            # Store event
            self._decision_events.append(event)
            if len(self._decision_events) > self._max_events:
                self._decision_events = self._decision_events[-self._max_events:]

        # Check for high block rate alert
        if action == "block":
            self._check_block_rate_alert()

        # Persist to Redis if available
        self._persist_decision_to_redis(event)

        logger.debug(
            "[SafetyMetrics] Recorded decision: action=%s, category=%s, "
            "risk=%s, duration=%.2fms",
            action,
            category,
            risk_level,
            scan_duration_ms,
        )

        return event

    def _record_latency(self, latency_seconds: float) -> None:
        """Record latency in histogram buckets"""
        self._latency_sum += latency_seconds
        self._latency_count += 1

        # Find bucket
        for bucket in self.LATENCY_BUCKETS:
            if latency_seconds <= bucket:
                bucket_key = f"le_{bucket}"
                self._latency_histogram[bucket_key] += 1
                break
        else:
            self._latency_histogram["le_inf"] += 1

    def record_override_request(
        self,
        trace_id: str,
        original_action: str,
        requested_action: str,
        reason: str,
        requester_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SafetyOverrideRequest:
        """
        Record a safety override request.

        Args:
            trace_id: Unique trace identifier
            original_action: Original safety decision action
            requested_action: Requested override action
            reason: Reason for override request
            requester_id: ID of the requester
            metadata: Additional metadata

        Returns:
            SafetyOverrideRequest that was recorded
        """
        if not self.enabled:
            return SafetyOverrideRequest(
                timestamp=datetime.now(timezone.utc).isoformat(),
                trace_id=trace_id,
                original_action=original_action,
                requested_action=requested_action,
                reason=reason,
                requester_id=requester_id,
            )

        timestamp = datetime.now(timezone.utc).isoformat()

        request = SafetyOverrideRequest(
            timestamp=timestamp,
            trace_id=trace_id,
            original_action=original_action,
            requested_action=requested_action,
            reason=reason,
            requester_id=requester_id,
            metadata=metadata or {},
        )

        with self._lock:
            # Increment override counter
            self._override_requests["pending"] += 1

            # Store event
            self._override_events.append(request)
            if len(self._override_events) > self._max_events:
                self._override_events = self._override_events[-self._max_events:]

        # Persist to Redis if available
        self._persist_override_to_redis(request)

        logger.info(
            "[SafetyMetrics] Override request: trace=%s, from=%s to=%s, "
            "requester=%s",
            trace_id,
            original_action,
            requested_action,
            requester_id,
        )

        return request

    def approve_override(
        self,
        trace_id: str,
        approver_id: str,
    ) -> bool:
        """
        Approve a pending override request.

        Args:
            trace_id: Trace ID of the override request
            approver_id: ID of the approver

        Returns:
            True if approved, False if not found
        """
        with self._lock:
            for request in self._override_events:
                if request.trace_id == trace_id and request.status == "pending":
                    request.status = "approved"
                    request.approver_id = approver_id
                    request.approved_at = datetime.now(timezone.utc).isoformat()

                    self._override_requests["pending"] -= 1
                    self._override_requests["approved"] += 1

                    logger.info(
                        "[SafetyMetrics] Override approved: trace=%s, approver=%s",
                        trace_id,
                        approver_id,
                    )
                    return True

        return False

    def reject_override(
        self,
        trace_id: str,
        approver_id: str,
    ) -> bool:
        """
        Reject a pending override request.

        Args:
            trace_id: Trace ID of the override request
            approver_id: ID of the approver

        Returns:
            True if rejected, False if not found
        """
        with self._lock:
            for request in self._override_events:
                if request.trace_id == trace_id and request.status == "pending":
                    request.status = "rejected"
                    request.approver_id = approver_id
                    request.approved_at = datetime.now(timezone.utc).isoformat()

                    self._override_requests["pending"] -= 1
                    self._override_requests["rejected"] += 1

                    logger.info(
                        "[SafetyMetrics] Override rejected: trace=%s, approver=%s",
                        trace_id,
                        approver_id,
                    )
                    return True

        return False

    def _check_block_rate_alert(self) -> None:
        """Check if block rate exceeds threshold and trigger alert"""
        block_rate = self.get_block_rate()

        if block_rate >= self.block_rate_threshold:
            current_time = time.time()

            # Check cooldown
            if self._last_alert_time is not None:
                elapsed_minutes = (current_time - self._last_alert_time) / 60
                if elapsed_minutes < self.alert_cooldown_minutes:
                    return

            self._last_alert_time = current_time

            logger.warning(
                "[SafetyMetrics] HIGH BLOCK RATE ALERT: %.1f%% (threshold: %.1f%%)",
                block_rate,
                self.block_rate_threshold,
            )

            # TODO: Integrate with HealthAlertService for Slack/webhook notifications

    def get_block_rate(self) -> float:
        """
        Calculate current block rate percentage.

        Returns:
            Block rate as percentage (0-100)
        """
        with self._lock:
            total_decisions = sum(self._decisions_total.values())
            if total_decisions == 0:
                return 0.0

            block_count = sum(
                count for (action, _), count in self._decisions_total.items()
                if action == "block"
            )

            return (block_count / total_decisions) * 100

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics in Prometheus-compatible format.

        Returns:
            Dictionary with all safety metrics
        """
        with self._lock:
            total_decisions = sum(self._decisions_total.values())

            # Calculate action breakdown
            action_counts = defaultdict(int)
            category_counts = defaultdict(int)
            for (action, category), count in self._decisions_total.items():
                action_counts[action] += count
                if category != "none":
                    category_counts[category] += count

            # Calculate latency percentiles
            avg_latency = (
                self._latency_sum / self._latency_count
                if self._latency_count > 0
                else 0.0
            )

            return {
                "safety_decisions_total": {
                    "total": total_decisions,
                    "by_action": dict(action_counts),
                    "by_category": dict(category_counts),
                },
                "safety_scan_latency_seconds": {
                    "sum": self._latency_sum,
                    "count": self._latency_count,
                    "avg": avg_latency,
                    "histogram": dict(self._latency_histogram),
                },
                "safety_override_requests_total": dict(self._override_requests),
                "safety_findings_total": dict(self._findings_total),
                "safety_block_rate": self.get_block_rate(),
                "alert_status": {
                    "block_rate_threshold": self.block_rate_threshold,
                    "last_alert_time": self._last_alert_time,
                    "cooldown_minutes": self.alert_cooldown_minutes,
                },
            }

    def get_decision_events(
        self,
        limit: int = 100,
        action: Optional[str] = None,
        category: Optional[str] = None,
        policy_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent decision events with optional filtering.

        Args:
            limit: Maximum number of events to return
            action: Filter by action (allow, block, etc.)
            category: Filter by category (prompt_injection, etc.)
            policy_id: Filter by policy ID

        Returns:
            List of decision events as dictionaries
        """
        with self._lock:
            events = self._decision_events.copy()

        # Apply filters
        if action:
            events = [e for e in events if e.action == action]
        if category:
            events = [e for e in events if e.category == category]
        if policy_id:
            events = [e for e in events if e.policy_id == policy_id]

        # Sort by timestamp descending and limit
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

        return [e.to_dict() for e in events]

    def get_override_requests(
        self,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get override requests with optional filtering.

        Args:
            limit: Maximum number of requests to return
            status: Filter by status (pending, approved, rejected)

        Returns:
            List of override requests as dictionaries
        """
        with self._lock:
            requests = self._override_events.copy()

        # Apply filters
        if status:
            requests = [r for r in requests if r.status == status]

        # Sort by timestamp descending and limit
        requests = sorted(requests, key=lambda r: r.timestamp, reverse=True)[:limit]

        return [r.to_dict() for r in requests]

    def _persist_decision_to_redis(self, event: SafetyDecisionEvent) -> None:
        """Persist decision event to Redis"""
        if not self.redis:
            return

        try:
            import json
            key = f"safety:decisions:{event.trace_id}"
            self.redis.setex(
                key,
                self.window_minutes * 60 * 4,  # 4x window for history
                json.dumps(event.to_dict()),
            )

            # Increment Redis counters
            action_key = f"safety:counter:action:{event.action}"
            self.redis.incr(action_key)

            if event.category:
                category_key = f"safety:counter:category:{event.category}"
                self.redis.incr(category_key)

        except Exception as e:
            logger.warning("[SafetyMetrics] Failed to persist to Redis: %s", e)

    def _persist_override_to_redis(self, request: SafetyOverrideRequest) -> None:
        """Persist override request to Redis"""
        if not self.redis:
            return

        try:
            import json
            key = f"safety:overrides:{request.trace_id}"
            self.redis.setex(
                key,
                self.window_minutes * 60 * 4,
                json.dumps(request.to_dict()),
            )

            # Increment Redis counter
            status_key = f"safety:counter:override:{request.status}"
            self.redis.incr(status_key)

        except Exception as e:
            logger.warning("[SafetyMetrics] Failed to persist override to Redis: %s", e)

    def reset(self) -> None:
        """Reset all metrics (for testing)"""
        with self._lock:
            self._decisions_total.clear()
            self._findings_total.clear()
            self._override_requests.clear()
            self._latency_histogram.clear()
            self._latency_sum = 0.0
            self._latency_count = 0
            self._decision_events.clear()
            self._override_events.clear()
            self._last_alert_time = None


# Singleton instance
_safety_metrics_collector: Optional[SafetyMetricsCollector] = None


def get_safety_metrics_collector() -> SafetyMetricsCollector:
    """Get or create singleton SafetyMetricsCollector instance"""
    global _safety_metrics_collector
    if _safety_metrics_collector is None:
        _safety_metrics_collector = SafetyMetricsCollector()
    return _safety_metrics_collector


def reset_safety_metrics_collector() -> None:
    """Reset singleton instance (for testing)"""
    global _safety_metrics_collector
    _safety_metrics_collector = None
