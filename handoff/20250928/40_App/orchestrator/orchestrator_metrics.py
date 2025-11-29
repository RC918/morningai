#!/usr/bin/env python3
"""
Orchestrator Metrics Module - Multi-Agent Flow Observability

Phase 3 Enhancement: Provides comprehensive metrics for the LangGraph orchestrator
multi-agent workflow including:
- Node-level execution metrics (count, success/failure, latency)
- Graph transition tracking
- Decision outcome distribution
- Review quality score tracking
- Fixer retry metrics
- End-to-end workflow metrics
- A/B experiment metrics (Phase 5 PR-5)

All metrics operations are wrapped in try/except to never break the job path.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

# Node names in the orchestrator graph
ORCHESTRATOR_NODES = [
    "planner",
    "executor",
    "ci_monitor",
    "reviewer",
    "decision",
    "fixer",
    "finalizer"
]

# Decision outcomes
DECISION_OUTCOMES = ["approve", "needs_fix", "request_changes", "pending"]

# Review severity levels
SEVERITY_LEVELS = ["none", "low", "medium", "high", "critical", "unknown"]

# Latency buckets in milliseconds
LATENCY_BUCKETS_MS = [100, 250, 500, 1000, 2500, 5000, 10000, 30000]


class OrchestratorMetrics:
    """
    Metrics collector for LangGraph orchestrator multi-agent flow

    Tracks:
    - Node execution counts and latencies
    - Graph transitions between nodes
    - Decision outcomes (approve, needs_fix, request_changes, pending)
    - Code quality score distribution
    - Fixer retry counts
    - End-to-end workflow metrics
    """

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        enabled: bool = True,
        ttl_seconds: int = 7200,
        key_prefix: str = "metrics:orchestrator"
    ):
        """
        Initialize orchestrator metrics

        Args:
            redis_client: Redis client instance (optional, metrics disabled if None)
            enabled: Whether metrics collection is enabled
            ttl_seconds: TTL for minute-bucket keys (default: 2 hours)
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis_client
        self.enabled = enabled and redis_client is not None
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.buckets_ms = LATENCY_BUCKETS_MS

    def _get_minute_key(self, metric_name: str, timestamp: Optional[datetime] = None) -> str:
        """Generate minute-bucket key for a metric"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        minute_str = timestamp.strftime("%Y%m%d%H%M")
        return f"{self.key_prefix}:{metric_name}:{minute_str}"

    def _safe_incr(self, key: str, value: int = 1) -> None:
        """Safely increment a Redis key with TTL"""
        if not self.enabled:
            return

        try:
            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incrby(key, value)
                pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to increment metric {key}: {e}")

    def _safe_get(self, key: str) -> int:
        """Safely get a Redis key value"""
        if not self.enabled:
            return 0

        try:
            value = self.redis.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.warning(f"Failed to get metric {key}: {e}")
            return 0

    # ==================== Node Metrics ====================

    def record_node_start(self, node_name: str, trace_id: str) -> None:
        """Record node execution start"""
        if not self.enabled:
            return

        key = self._get_minute_key(f"node.{node_name}.started")
        self._safe_incr(key)

        logger.debug(f"[Metrics] Node started: {node_name}", extra={
            "operation": "metrics_node_start",
            "node": node_name,
            "trace_id": trace_id
        })

    def record_node_complete(
        self,
        node_name: str,
        trace_id: str,
        success: bool = True,
        latency_ms: Optional[float] = None
    ) -> None:
        """Record node execution completion"""
        if not self.enabled:
            return

        # Record success/failure
        status = "success" if success else "failure"
        key = self._get_minute_key(f"node.{node_name}.{status}")
        self._safe_incr(key)

        # Record latency if provided
        if latency_ms is not None:
            self._record_latency(f"node.{node_name}", latency_ms)

        logger.debug(f"[Metrics] Node completed: {node_name}", extra={
            "operation": "metrics_node_complete",
            "node": node_name,
            "trace_id": trace_id,
            "success": success,
            "latency_ms": latency_ms
        })

    @contextmanager
    def track_node_execution(self, node_name: str, trace_id: str):
        """
        Context manager to track node execution time

        Usage:
            with metrics.track_node_execution("planner", trace_id):
                # node logic here
        """
        start_time = time.time()
        self.record_node_start(node_name, trace_id)
        success = True

        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            self.record_node_complete(node_name, trace_id, success, latency_ms)

    # ==================== Transition Metrics ====================

    def record_transition(self, from_node: str, to_node: str, trace_id: str) -> None:
        """Record graph transition between nodes"""
        if not self.enabled:
            return

        key = self._get_minute_key(f"transition.{from_node}_to_{to_node}")
        self._safe_incr(key)

        logger.debug(f"[Metrics] Transition: {from_node} -> {to_node}", extra={
            "operation": "metrics_transition",
            "from_node": from_node,
            "to_node": to_node,
            "trace_id": trace_id
        })

    # ==================== Decision Metrics ====================

    def record_decision(
        self,
        decision: str,
        trace_id: str,
        quality_score: Optional[int] = None,
        review_severity: Optional[str] = None
    ) -> None:
        """Record merge decision outcome"""
        if not self.enabled:
            return

        # Record decision outcome
        key = self._get_minute_key(f"decision.{decision}")
        self._safe_incr(key)

        # Record quality score bucket if provided
        if quality_score is not None:
            score_bucket = self._get_quality_score_bucket(quality_score)
            score_key = self._get_minute_key(f"quality_score.{score_bucket}")
            self._safe_incr(score_key)

        # Record severity if provided
        if review_severity is not None:
            severity_key = self._get_minute_key(f"severity.{review_severity}")
            self._safe_incr(severity_key)

        logger.debug(f"[Metrics] Decision recorded: {decision}", extra={
            "operation": "metrics_decision",
            "decision": decision,
            "trace_id": trace_id,
            "quality_score": quality_score,
            "review_severity": review_severity
        })

    def _get_quality_score_bucket(self, score: int) -> str:
        """Get quality score bucket label"""
        if score >= 90:
            return "excellent_90_100"
        elif score >= 70:
            return "good_70_89"
        elif score >= 50:
            return "fair_50_69"
        elif score >= 30:
            return "poor_30_49"
        else:
            return "critical_0_29"

    # ==================== Fixer Metrics ====================

    def record_fixer_attempt(
        self,
        trace_id: str,
        retry_count: int,
        success: bool = False
    ) -> None:
        """Record fixer attempt"""
        if not self.enabled:
            return

        # Record attempt
        key = self._get_minute_key("fixer.attempts")
        self._safe_incr(key)

        # Record retry count bucket
        retry_bucket = f"retry_{min(retry_count, 3)}"
        retry_key = self._get_minute_key(f"fixer.{retry_bucket}")
        self._safe_incr(retry_key)

        # Record success/failure
        status = "success" if success else "failure"
        status_key = self._get_minute_key(f"fixer.{status}")
        self._safe_incr(status_key)

        logger.debug("[Metrics] Fixer attempt recorded", extra={
            "operation": "metrics_fixer",
            "trace_id": trace_id,
            "retry_count": retry_count,
            "success": success
        })

    # ==================== Workflow Metrics ====================

    def record_workflow_start(self, trace_id: str, goal: str) -> None:
        """Record workflow start"""
        if not self.enabled:
            return

        key = self._get_minute_key("workflow.started")
        self._safe_incr(key)

        logger.debug("[Metrics] Workflow started", extra={
            "operation": "metrics_workflow_start",
            "trace_id": trace_id,
            "goal_length": len(goal)
        })

    def record_workflow_complete(
        self,
        trace_id: str,
        status: str,
        latency_ms: Optional[float] = None
    ) -> None:
        """Record workflow completion"""
        if not self.enabled:
            return

        # Record completion status
        key = self._get_minute_key(f"workflow.{status}")
        self._safe_incr(key)

        # Record total latency
        if latency_ms is not None:
            self._record_latency("workflow.total", latency_ms)

        logger.debug("[Metrics] Workflow completed", extra={
            "operation": "metrics_workflow_complete",
            "trace_id": trace_id,
            "status": status,
            "latency_ms": latency_ms
        })

    # ==================== Experiment Metrics (Phase 5 PR-5) ====================

    def record_experiment_assignment(
        self,
        experiment_name: str,
        variant: str,
        trace_id: str,
        component: str
    ) -> None:
        """
        Record experiment variant assignment

        Args:
            experiment_name: Name of the experiment
            variant: Assigned variant (control/treatment)
            trace_id: Unique trace identifier
            component: Component being experimented on (planner, reviewer, etc.)
        """
        if not self.enabled:
            return

        key = self._get_minute_key(f"experiment.{experiment_name}.{variant}")
        self._safe_incr(key)

        component_key = self._get_minute_key(
            f"experiment.{experiment_name}.component.{component}"
        )
        self._safe_incr(component_key)

        logger.debug("[Metrics] Experiment assignment recorded", extra={
            "operation": "metrics_experiment_assignment",
            "experiment_name": experiment_name,
            "variant": variant,
            "trace_id": trace_id,
            "component": component
        })

    def record_experiment_outcome(
        self,
        experiment_name: str,
        variant: str,
        trace_id: str,
        success: bool,
        latency_ms: Optional[float] = None
    ) -> None:
        """
        Record experiment outcome for A/B analysis

        Args:
            experiment_name: Name of the experiment
            variant: Variant that was used (control/treatment)
            trace_id: Unique trace identifier
            success: Whether the operation succeeded
            latency_ms: Optional latency in milliseconds
        """
        if not self.enabled:
            return

        status = "success" if success else "failure"
        key = self._get_minute_key(f"experiment.{experiment_name}.{variant}.{status}")
        self._safe_incr(key)

        if latency_ms is not None:
            self._record_latency(
                f"experiment.{experiment_name}.{variant}",
                latency_ms
            )

        logger.debug("[Metrics] Experiment outcome recorded", extra={
            "operation": "metrics_experiment_outcome",
            "experiment_name": experiment_name,
            "variant": variant,
            "trace_id": trace_id,
            "success": success,
            "latency_ms": latency_ms
        })

    def get_experiment_summary(
        self,
        experiment_name: str,
        window_minutes: int = 15
    ) -> Dict:
        """
        Get summary of experiment metrics for A/B analysis

        Args:
            experiment_name: Name of the experiment
            window_minutes: Time window in minutes

        Returns:
            Dict with control/treatment metrics for comparison
        """
        if not self.enabled:
            return {"enabled": False}

        def _get_variant_summary(variant: str) -> Dict:
            """Helper to get metrics summary for a variant"""
            total = self.get_window_count(
                f"experiment.{experiment_name}.{variant}", window_minutes
            )
            success = self.get_window_count(
                f"experiment.{experiment_name}.{variant}.success", window_minutes
            )
            failure = self.get_window_count(
                f"experiment.{experiment_name}.{variant}.failure", window_minutes
            )
            return {
                "total": total,
                "success": success,
                "failure": failure,
                "success_rate": round(success / total * 100, 2) if total > 0 else 0
            }

        return {
            "experiment_name": experiment_name,
            "window_minutes": window_minutes,
            "control": _get_variant_summary("control"),
            "treatment": _get_variant_summary("treatment")
        }

    # ==================== Latency Metrics ====================

    def _record_latency(self, metric_name: str, latency_ms: float) -> None:
        """Record latency in histogram buckets"""
        if not self.enabled:
            return

        try:
            target_bucket = None
            for bucket in self.buckets_ms:
                if latency_ms <= bucket:
                    target_bucket = bucket
                    break

            bucket_label = str(target_bucket) if target_bucket else "inf"
            key = self._get_minute_key(f"{metric_name}.latency_bucket_{bucket_label}")
            self._safe_incr(key)
        except Exception as e:
            logger.warning(f"Failed to record latency {latency_ms}ms: {e}")

    # ==================== Summary Methods ====================

    def get_window_count(self, metric_name: str, window_minutes: int = 15) -> int:
        """Get total count for a metric over a time window"""
        if not self.enabled:
            return 0

        try:
            now = datetime.utcnow()
            total = 0

            for i in range(window_minutes):
                timestamp = now - timedelta(minutes=i)
                key = self._get_minute_key(metric_name, timestamp)
                value = self._safe_get(key)
                total += value

            return total
        except Exception as e:
            logger.warning(f"Failed to get window count for {metric_name}: {e}")
            return 0

    def get_node_summary(self, window_minutes: int = 15) -> Dict:
        """Get summary of node-level metrics"""
        if not self.enabled:
            return {"enabled": False}

        summary = {}
        for node in ORCHESTRATOR_NODES:
            started = self.get_window_count(f"node.{node}.started", window_minutes)
            success = self.get_window_count(f"node.{node}.success", window_minutes)
            failure = self.get_window_count(f"node.{node}.failure", window_minutes)

            summary[node] = {
                "started": started,
                "success": success,
                "failure": failure,
                "success_rate": round(success / started * 100, 2) if started > 0 else 0
            }

        return summary

    def get_decision_summary(self, window_minutes: int = 15) -> Dict:
        """Get summary of decision outcomes"""
        if not self.enabled:
            return {"enabled": False}

        summary = {}
        total = 0

        for outcome in DECISION_OUTCOMES:
            count = self.get_window_count(f"decision.{outcome}", window_minutes)
            summary[outcome] = count
            total += count

        summary["total"] = total

        # Calculate rates
        if total > 0:
            summary["approve_rate"] = round(summary.get("approve", 0) / total * 100, 2)
            summary["needs_fix_rate"] = round(summary.get("needs_fix", 0) / total * 100, 2)

        return summary

    def get_fixer_summary(self, window_minutes: int = 15) -> Dict:
        """Get summary of fixer metrics"""
        if not self.enabled:
            return {"enabled": False}

        attempts = self.get_window_count("fixer.attempts", window_minutes)
        success = self.get_window_count("fixer.success", window_minutes)
        failure = self.get_window_count("fixer.failure", window_minutes)

        return {
            "attempts": attempts,
            "success": success,
            "failure": failure,
            "success_rate": round(success / attempts * 100, 2) if attempts > 0 else 0,
            "retry_0": self.get_window_count("fixer.retry_0", window_minutes),
            "retry_1": self.get_window_count("fixer.retry_1", window_minutes),
            "retry_2": self.get_window_count("fixer.retry_2", window_minutes),
            "retry_3": self.get_window_count("fixer.retry_3", window_minutes)
        }

    def get_workflow_summary(self, window_minutes: int = 15) -> Dict:
        """Get summary of workflow metrics"""
        if not self.enabled:
            return {"enabled": False}

        started = self.get_window_count("workflow.started", window_minutes)
        success = self.get_window_count("workflow.success", window_minutes)
        error = self.get_window_count("workflow.error", window_minutes)

        return {
            "started": started,
            "success": success,
            "error": error,
            "success_rate": round(success / started * 100, 2) if started > 0 else 0
        }

    def get_quality_score_summary(self, window_minutes: int = 15) -> Dict:
        """Get summary of quality score distribution"""
        if not self.enabled:
            return {"enabled": False}

        buckets = [
            "excellent_90_100",
            "good_70_89",
            "fair_50_69",
            "poor_30_49",
            "critical_0_29"
        ]

        summary = {}
        total = 0

        for bucket in buckets:
            count = self.get_window_count(f"quality_score.{bucket}", window_minutes)
            summary[bucket] = count
            total += count

        summary["total"] = total
        return summary

    def get_comprehensive_summary(self, window_minutes: int = 15) -> Dict:
        """Get comprehensive metrics summary for the orchestrator"""
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Orchestrator metrics disabled"
            }

        return {
            "enabled": True,
            "window_minutes": window_minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "workflow": self.get_workflow_summary(window_minutes),
            "nodes": self.get_node_summary(window_minutes),
            "decisions": self.get_decision_summary(window_minutes),
            "fixer": self.get_fixer_summary(window_minutes),
            "quality_scores": self.get_quality_score_summary(window_minutes)
        }


# Global metrics instance (lazy initialization)
_metrics_instance: Optional[OrchestratorMetrics] = None


def get_orchestrator_metrics(
    redis_client: Optional["redis.Redis"] = None,
    enabled: bool = True
) -> OrchestratorMetrics:
    """
    Get or create the global orchestrator metrics instance

    Args:
        redis_client: Redis client instance (optional)
        enabled: Whether metrics collection is enabled

    Returns:
        OrchestratorMetrics instance
    """
    global _metrics_instance

    if _metrics_instance is None:
        _metrics_instance = OrchestratorMetrics(
            redis_client=redis_client,
            enabled=enabled
        )

    return _metrics_instance


def create_orchestrator_metrics(
    redis_client: Optional["redis.Redis"] = None,
    enabled: bool = True
) -> OrchestratorMetrics:
    """
    Factory function to create a new OrchestratorMetrics instance

    Args:
        redis_client: Redis client instance (optional)
        enabled: Whether metrics collection is enabled

    Returns:
        New OrchestratorMetrics instance
    """
    return OrchestratorMetrics(
        redis_client=redis_client,
        enabled=enabled
    )
