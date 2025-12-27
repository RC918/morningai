"""
Flow Controller v3 - Router Metrics (C-4)

Issue #2747: C-4 Router Observability (Metrics/Telemetry)
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 0: Foundations

This module provides observability for the Router:
- router_latency_ms: Router decision latency
- router_success_count: Successful decision count
- router_fallback_count: Fallback count
- router_fallback_reason: Fallback reason distribution
- router_chosen_node: Selected node distribution
- router_token_usage: Token usage (if available)
- router_cost_estimate: Cost estimate

Usage:
    from core.flow import RouterMetrics

    metrics = RouterMetrics()

    # Record a decision
    metrics.record_decision(
        trace_id="abc123",
        latency_ms=150.5,
        success=True,
        chosen_node="fixer",
        token_usage=250
    )

    # Get fallback rate
    rate = metrics.get_fallback_rate(window_minutes=60)
"""
import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Deque, Dict, Optional

logger = logging.getLogger(__name__)


# Metrics schema version for safe evolution
METRICS_VERSION = "v1"


@dataclass
class RouterDecisionRecord:
    """Record of a single router decision.

    Note:
        All timestamps are in UTC (using datetime.utcnow()).
    """

    trace_id: str
    timestamp: datetime  # UTC timestamp
    latency_ms: float
    success: bool
    chosen_node: str
    fallback_reason: Optional[str] = None
    token_usage: Optional[int] = None
    cost_estimate: Optional[float] = None


class RouterMetrics:
    """Router observability and metrics collection.

    This class collects and aggregates metrics for Router decisions.
    It provides methods to record decisions and query aggregated metrics.

    Thread-safe: All operations are protected by a lock.
    """

    def __init__(self, max_records: int = 10000):
        """Initialize RouterMetrics.

        Args:
            max_records: Maximum number of records to keep in memory.
                         Uses deque with maxlen for O(1) FIFO eviction.
        """
        self._records: Deque[RouterDecisionRecord] = deque(maxlen=max_records)
        self._max_records = max_records
        self._lock = Lock()

        # Aggregated counters
        self._total_decisions = 0
        self._total_successes = 0
        self._total_fallbacks = 0
        self._fallback_reasons: Dict[str, int] = defaultdict(int)
        self._chosen_nodes: Dict[str, int] = defaultdict(int)
        self._total_latency_ms = 0.0
        self._total_tokens = 0
        self._total_cost = 0.0

    def record_decision(
        self,
        trace_id: str,
        latency_ms: float,
        success: bool,
        chosen_node: str,
        fallback_reason: Optional[str] = None,
        token_usage: Optional[int] = None,
        cost_estimate: Optional[float] = None
    ) -> None:
        """Record a single routing decision.

        Args:
            trace_id: Unique identifier for the trace
            latency_ms: Decision latency in milliseconds
            success: Whether the LLM decision was successful
            chosen_node: The node that was selected
            fallback_reason: Reason for fallback (if success=False)
            token_usage: Number of tokens used (if available)
            cost_estimate: Estimated cost in USD (if available)
        """
        record = RouterDecisionRecord(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            latency_ms=latency_ms,
            success=success,
            chosen_node=chosen_node,
            fallback_reason=fallback_reason,
            token_usage=token_usage,
            cost_estimate=cost_estimate
        )

        with self._lock:
            # Add record (deque with maxlen handles FIFO eviction automatically)
            self._records.append(record)

            # Update aggregates
            self._total_decisions += 1
            self._total_latency_ms += latency_ms
            self._chosen_nodes[chosen_node] += 1

            if success:
                self._total_successes += 1
            else:
                self._total_fallbacks += 1
                if fallback_reason:
                    self._fallback_reasons[fallback_reason] += 1

            if token_usage:
                self._total_tokens += token_usage

            if cost_estimate:
                self._total_cost += cost_estimate

        # Log the decision
        log_extra = {
            "trace_id": trace_id,
            "latency_ms": latency_ms,
            "success": success,
            "chosen_node": chosen_node,
        }
        if fallback_reason:
            log_extra["fallback_reason"] = fallback_reason
        if token_usage:
            log_extra["token_usage"] = token_usage

        logger.info(
            f"[RouterMetrics] Decision recorded: "
            f"node={chosen_node}, success={success}, latency={latency_ms:.1f}ms"
            f"{f', fallback_reason={fallback_reason}' if fallback_reason else ''}",
            extra=log_extra
        )

    def get_fallback_rate(self, window_minutes: int = 60) -> float:
        """Get the fallback rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Fallback rate as a float (0.0 to 1.0)
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 0.0

            fallbacks = sum(1 for r in recent_records if not r.success)
            return fallbacks / len(recent_records)

    def get_success_rate(self, window_minutes: int = 60) -> float:
        """Get the success rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Success rate as a float (0.0 to 1.0)
        """
        return 1.0 - self.get_fallback_rate(window_minutes)

    def get_average_latency(self, window_minutes: int = 60) -> float:
        """Get the average latency within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Average latency in milliseconds
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 0.0

            return sum(r.latency_ms for r in recent_records) / len(recent_records)

    def get_fallback_distribution(
        self,
        window_minutes: int = 60
    ) -> Dict[str, int]:
        """Get the distribution of fallback reasons.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict mapping fallback reason to count
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        with self._lock:
            distribution: Dict[str, int] = defaultdict(int)
            for r in self._records:
                if r.timestamp >= cutoff and r.fallback_reason:
                    distribution[r.fallback_reason] += 1
            return dict(distribution)

    def get_node_distribution(
        self,
        window_minutes: int = 60
    ) -> Dict[str, int]:
        """Get the distribution of chosen nodes.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict mapping node name to count
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        with self._lock:
            distribution: Dict[str, int] = defaultdict(int)
            for r in self._records:
                if r.timestamp >= cutoff:
                    distribution[r.chosen_node] += 1
            return dict(distribution)

    def get_summary(self, window_minutes: int = 60) -> dict:
        """Get a summary of router metrics.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict with summary metrics
        """
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._records
                if r.timestamp >= cutoff
            ]

            total = len(recent_records)
            successes = sum(1 for r in recent_records if r.success)
            fallbacks = total - successes

            avg_latency = (
                sum(r.latency_ms for r in recent_records) / total
                if total > 0 else 0.0
            )

            total_tokens = sum(
                r.token_usage for r in recent_records
                if r.token_usage
            )

            total_cost = sum(
                r.cost_estimate for r in recent_records
                if r.cost_estimate
            )

            # Compute distributions inline to avoid deadlock
            # (calling get_fallback_distribution/get_node_distribution would
            # try to acquire the lock again)
            fallback_dist: Dict[str, int] = defaultdict(int)
            node_dist: Dict[str, int] = defaultdict(int)
            for r in recent_records:
                node_dist[r.chosen_node] += 1
                if r.fallback_reason:
                    fallback_dist[r.fallback_reason] += 1

            return {
                "metrics_version": METRICS_VERSION,
                "window_minutes": window_minutes,
                "total_decisions": total,
                "successes": successes,
                "fallbacks": fallbacks,
                "success_rate": successes / total if total > 0 else 0.0,
                "fallback_rate": fallbacks / total if total > 0 else 0.0,
                "average_latency_ms": avg_latency,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
                "fallback_distribution": dict(fallback_dist),
                "node_distribution": dict(node_dist),
            }

    def get_all_time_summary(self) -> dict:
        """Get all-time summary metrics.

        Returns:
            Dict with all-time summary metrics
        """
        with self._lock:
            avg_latency = (
                self._total_latency_ms / self._total_decisions
                if self._total_decisions > 0 else 0.0
            )

            return {
                "metrics_version": METRICS_VERSION,
                "total_decisions": self._total_decisions,
                "total_successes": self._total_successes,
                "total_fallbacks": self._total_fallbacks,
                "success_rate": (
                    self._total_successes / self._total_decisions
                    if self._total_decisions > 0 else 0.0
                ),
                "fallback_rate": (
                    self._total_fallbacks / self._total_decisions
                    if self._total_decisions > 0 else 0.0
                ),
                "average_latency_ms": avg_latency,
                "total_tokens": self._total_tokens,
                "total_cost_usd": self._total_cost,
                "fallback_reasons": dict(self._fallback_reasons),
                "chosen_nodes": dict(self._chosen_nodes),
            }

    def reset(self) -> None:
        """Reset all metrics.

        Use with caution - this clears all collected data.
        """
        with self._lock:
            self._records.clear()
            self._total_decisions = 0
            self._total_successes = 0
            self._total_fallbacks = 0
            self._fallback_reasons.clear()
            self._chosen_nodes.clear()
            self._total_latency_ms = 0.0
            self._total_tokens = 0
            self._total_cost = 0.0

        logger.info("[RouterMetrics] Metrics reset")


# Global metrics instance (singleton pattern)
_global_metrics: Optional[RouterMetrics] = None


def get_router_metrics() -> RouterMetrics:
    """Get the global RouterMetrics instance.

    Returns:
        The global RouterMetrics singleton
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = RouterMetrics()
    return _global_metrics
