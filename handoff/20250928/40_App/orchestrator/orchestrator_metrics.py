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
            "quality_scores": self.get_quality_score_summary(window_minutes),
            "failure_learning": self.get_failure_learning_summary(window_minutes),
            "review": self.get_review_summary(window_minutes)
        }

    # ==================== Failure Learning Metrics (Issue #2124) ====================

    def record_failure_observation(
        self,
        trace_id: str,
        error_type: str,
        saved_to_pgvector: bool,
        latency_ms: float
    ) -> None:
        """
        Record failure observation metrics.

        Issue #2124: Latency metrics for failure learning observability.

        Args:
            trace_id: Unique trace identifier
            error_type: Categorized error type
            saved_to_pgvector: Whether the failure was saved to pgvector
            latency_ms: Observation latency in milliseconds
        """
        if not self.enabled:
            return

        # Record observation count
        key = self._get_minute_key("failure_learning.observe")
        self._safe_incr(key)

        # Record error type distribution
        error_key = self._get_minute_key(f"failure_learning.error_type.{error_type}")
        self._safe_incr(error_key)

        # Record pgvector save status
        save_status = "saved" if saved_to_pgvector else "skipped"
        save_key = self._get_minute_key(f"failure_learning.pgvector.{save_status}")
        self._safe_incr(save_key)

        # Record latency
        self._record_latency("failure_learning.observe", latency_ms)

        logger.debug("[Metrics] Failure observation recorded", extra={
            "operation": "metrics_failure_observation",
            "trace_id": trace_id,
            "error_type": error_type,
            "saved_to_pgvector": saved_to_pgvector,
            "latency_ms": latency_ms
        })

    def record_failure_query(
        self,
        trace_id: str,
        results_count: int,
        latency_ms: float,
        query_type: str = "similar_errors"
    ) -> None:
        """
        Record failure query metrics.

        Issue #2124: Latency metrics for failure learning observability.

        Args:
            trace_id: Unique trace identifier
            results_count: Number of results returned
            latency_ms: Query latency in milliseconds
            query_type: Type of query (similar_errors, learning_context, etc.)
        """
        if not self.enabled:
            return

        # Record query count
        key = self._get_minute_key(f"failure_learning.query.{query_type}")
        self._safe_incr(key)

        # Record results count bucket
        if results_count == 0:
            results_bucket = "empty"
        elif results_count <= 3:
            results_bucket = "few"
        else:
            results_bucket = "many"
        results_key = self._get_minute_key(
            f"failure_learning.query.results.{results_bucket}"
        )
        self._safe_incr(results_key)

        # Record latency
        self._record_latency(f"failure_learning.query.{query_type}", latency_ms)

        logger.debug("[Metrics] Failure query recorded", extra={
            "operation": "metrics_failure_query",
            "trace_id": trace_id,
            "query_type": query_type,
            "results_count": results_count,
            "latency_ms": latency_ms
        })

    def record_learning_context_generation(
        self,
        trace_id: str,
        has_past_failures: bool,
        has_kg_patterns: bool,
        latency_ms: float
    ) -> None:
        """
        Record learning context generation metrics.

        Issue #2124: Latency metrics for failure learning observability.

        Args:
            trace_id: Unique trace identifier
            has_past_failures: Whether past failures were included
            has_kg_patterns: Whether Knowledge Graph patterns were included
            latency_ms: Generation latency in milliseconds
        """
        if not self.enabled:
            return

        # Record generation count
        key = self._get_minute_key("failure_learning.context_generation")
        self._safe_incr(key)

        # Record context composition
        if has_past_failures:
            pf_key = self._get_minute_key("failure_learning.context.has_past_failures")
            self._safe_incr(pf_key)

        if has_kg_patterns:
            kg_key = self._get_minute_key("failure_learning.context.has_kg_patterns")
            self._safe_incr(kg_key)

        # Record latency
        self._record_latency("failure_learning.context_generation", latency_ms)

        logger.debug("[Metrics] Learning context generation recorded", extra={
            "operation": "metrics_learning_context",
            "trace_id": trace_id,
            "has_past_failures": has_past_failures,
            "has_kg_patterns": has_kg_patterns,
            "latency_ms": latency_ms
        })

    def record_fix_update(
        self,
        trace_id: str,
        was_successful: bool,
        latency_ms: float
    ) -> None:
        """
        Record fix update metrics.

        Issue #2124: Latency metrics for failure learning observability.

        Args:
            trace_id: Unique trace identifier
            was_successful: Whether the fix was successful
            latency_ms: Update latency in milliseconds
        """
        if not self.enabled:
            return

        # Record update count
        key = self._get_minute_key("failure_learning.fix_update")
        self._safe_incr(key)

        # Record success/failure
        status = "success" if was_successful else "failure"
        status_key = self._get_minute_key(f"failure_learning.fix_update.{status}")
        self._safe_incr(status_key)

        # Record latency
        self._record_latency("failure_learning.fix_update", latency_ms)

        logger.debug("[Metrics] Fix update recorded", extra={
            "operation": "metrics_fix_update",
            "trace_id": trace_id,
            "was_successful": was_successful,
            "latency_ms": latency_ms
        })

    @contextmanager
    def track_failure_learning_operation(
        self,
        operation_name: str,
        trace_id: str
    ):
        """
        Context manager to track failure learning operation latency.

        Issue #2124: Latency metrics for failure learning observability.

        Usage:
            with metrics.track_failure_learning_operation("query", trace_id):
                # operation logic here

        Args:
            operation_name: Name of the operation (observe, query, context, fix_update)
            trace_id: Unique trace identifier
        """
        start_time = time.time()

        try:
            yield
        finally:
            latency_ms = (time.time() - start_time) * 1000
            key = self._get_minute_key(f"failure_learning.{operation_name}")
            self._safe_incr(key)
            self._record_latency(f"failure_learning.{operation_name}", latency_ms)

            logger.debug(f"[Metrics] Failure learning operation: {operation_name}", extra={
                "operation": f"metrics_failure_learning_{operation_name}",
                "trace_id": trace_id,
                "latency_ms": latency_ms
            })

    def get_failure_learning_summary(self, window_minutes: int = 15) -> Dict:
        """
        Get summary of failure learning metrics.

        Issue #2124: Latency metrics for failure learning observability.

        Args:
            window_minutes: Time window in minutes

        Returns:
            Dict with failure learning metrics summary
        """
        if not self.enabled:
            return {"enabled": False}

        observations = self.get_window_count(
            "failure_learning.observe", window_minutes
        )
        pgvector_saved = self.get_window_count(
            "failure_learning.pgvector.saved", window_minutes
        )
        pgvector_skipped = self.get_window_count(
            "failure_learning.pgvector.skipped", window_minutes
        )

        queries = self.get_window_count(
            "failure_learning.query.similar_errors", window_minutes
        )
        context_generations = self.get_window_count(
            "failure_learning.context_generation", window_minutes
        )
        fix_updates = self.get_window_count(
            "failure_learning.fix_update", window_minutes
        )
        fix_successes = self.get_window_count(
            "failure_learning.fix_update.success", window_minutes
        )

        return {
            "observations": observations,
            "pgvector_saved": pgvector_saved,
            "pgvector_skipped": pgvector_skipped,
            "save_rate": round(
                pgvector_saved / observations * 100, 2
            ) if observations > 0 else 0,
            "queries": queries,
            "context_generations": context_generations,
            "fix_updates": fix_updates,
            "fix_success_rate": round(
                fix_successes / fix_updates * 100, 2
            ) if fix_updates > 0 else 0,
            "context_with_past_failures": self.get_window_count(
                "failure_learning.context.has_past_failures", window_minutes
            ),
            "context_with_kg_patterns": self.get_window_count(
                "failure_learning.context.has_kg_patterns", window_minutes
            )
        }

    # ==================== Review Metrics (EPIC B Phase B-B C-lite) ====================

    def record_diff_fetch(
        self,
        trace_id: str,
        success: bool,
        truncated: bool = False,
        original_files: int = 0,
        included_files: int = 0,
        original_lines: int = 0,
        included_lines: int = 0,
        lockfile_only: bool = False
    ) -> None:
        """
        Record diff fetch metrics for EPIC B Phase B-B.

        Issue #2595: Diff-Aware Review Plumbing - C-lite Telemetry

        KPI: Diff Coverage > 90% (未截斷 PR 比例)
        - Denominator excludes lockfile-only PRs

        Args:
            trace_id: Unique trace identifier
            success: Whether diff fetch succeeded
            truncated: Whether diff was truncated
            original_files: Total files in PR (from GitHub)
            included_files: Files included after truncation
            original_lines: Total lines in PR
            included_lines: Lines included after truncation
            lockfile_only: Whether PR only contains lockfiles (excluded from KPI)
        """
        if not self.enabled:
            return

        if lockfile_only:
            key = self._get_minute_key("review.diff.lockfile_only")
            self._safe_incr(key)
            logger.debug("[Metrics] Diff fetch skipped (lockfile-only)", extra={
                "operation": "metrics_diff_fetch",
                "trace_id": trace_id,
                "lockfile_only": True
            })
            return

        if success:
            key = self._get_minute_key("review.diff.fetch_success")
            self._safe_incr(key)

            if truncated:
                truncated_key = self._get_minute_key("review.diff.truncated")
                self._safe_incr(truncated_key)
            else:
                not_truncated_key = self._get_minute_key("review.diff.not_truncated")
                self._safe_incr(not_truncated_key)

            if original_files > 0:
                files_key = self._get_minute_key("review.diff.original_files")
                self._safe_incr(files_key, original_files)
                included_files_key = self._get_minute_key("review.diff.included_files")
                self._safe_incr(included_files_key, included_files)

            if original_lines > 0:
                lines_key = self._get_minute_key("review.diff.original_lines")
                self._safe_incr(lines_key, original_lines)
                included_lines_key = self._get_minute_key("review.diff.included_lines")
                self._safe_incr(included_lines_key, included_lines)
        else:
            key = self._get_minute_key("review.diff.fetch_failure")
            self._safe_incr(key)

        logger.debug("[Metrics] Diff fetch recorded", extra={
            "operation": "metrics_diff_fetch",
            "trace_id": trace_id,
            "success": success,
            "truncated": truncated,
            "original_files": original_files,
            "included_files": included_files
        })

    def record_schema_validation(
        self,
        trace_id: str,
        raw_count: int,
        normalized_count: int,
        llm_api_failed: bool = False
    ) -> None:
        """
        Record schema validation metrics for EPIC B Phase B-B.

        Issue #2595: Diff-Aware Review Plumbing - C-lite Telemetry

        KPI: Schema Pass Rate > 95%
        - Formula: normalized_count / raw_count
        - Excludes LLM API failures (infrastructure issue, not schema issue)

        Args:
            trace_id: Unique trace identifier
            raw_count: Number of raw comments from LLM
            normalized_count: Number of comments after schema normalization
            llm_api_failed: Whether LLM API call failed (excluded from KPI)
        """
        if not self.enabled:
            return

        if llm_api_failed:
            key = self._get_minute_key("review.schema.llm_api_failed")
            self._safe_incr(key)
            logger.debug("[Metrics] Schema validation skipped (LLM API failed)", extra={
                "operation": "metrics_schema_validation",
                "trace_id": trace_id,
                "llm_api_failed": True
            })
            return

        if raw_count == 0:
            key = self._get_minute_key("review.schema.empty_output")
            self._safe_incr(key)
            logger.debug("[Metrics] Schema validation skipped (empty LLM output)", extra={
                "operation": "metrics_schema_validation",
                "trace_id": trace_id,
                "raw_count": 0
            })
            return

        raw_key = self._get_minute_key("review.schema.raw_total")
        self._safe_incr(raw_key, raw_count)

        normalized_key = self._get_minute_key("review.schema.normalized_total")
        self._safe_incr(normalized_key, normalized_count)

        filtered_count = raw_count - normalized_count
        if filtered_count > 0:
            filtered_key = self._get_minute_key("review.schema.filtered_total")
            self._safe_incr(filtered_key, filtered_count)

        logger.debug("[Metrics] Schema validation recorded", extra={
            "operation": "metrics_schema_validation",
            "trace_id": trace_id,
            "raw_count": raw_count,
            "normalized_count": normalized_count,
            "filtered_count": filtered_count
        })

    def record_inline_comment_result(
        self,
        trace_id: str,
        eligible_count: int,
        validated_count: int,
        downgraded_count: int,
        posted_count: int,
        post_failed: bool = False,
        fallback_used: bool = False,
        dry_run: bool = False,
        feature_disabled: bool = False
    ) -> None:
        """
        Record inline comment posting metrics for EPIC B Phase B-B.

        Issue #2595: Diff-Aware Review Plumbing - C-lite Telemetry

        KPIs:
        - Inline Success Rate > 90%: posted_count / eligible_count (strict)
        - Review Delivery Rate: (posted_count + fallback_count) / eligible_count

        Args:
            trace_id: Unique trace identifier
            eligible_count: Comments with file+line info (inline-eligible)
            validated_count: Comments that passed diff line validation
            downgraded_count: Comments downgraded to file-level due to validation
            posted_count: Comments successfully posted as inline
            post_failed: Whether GitHub API posting failed entirely
            fallback_used: Whether fallback to review body was used
            dry_run: Whether this was a dry-run (excluded from KPI)
            feature_disabled: Whether feature was disabled (excluded from KPI)
        """
        if not self.enabled:
            return

        if feature_disabled:
            key = self._get_minute_key("review.inline.feature_disabled")
            self._safe_incr(key)
            return

        if dry_run:
            key = self._get_minute_key("review.inline.dry_run")
            self._safe_incr(key)
            return

        eligible_key = self._get_minute_key("review.inline.eligible_total")
        self._safe_incr(eligible_key, eligible_count)

        validated_key = self._get_minute_key("review.inline.validated_total")
        self._safe_incr(validated_key, validated_count)

        downgraded_key = self._get_minute_key("review.inline.downgraded_total")
        self._safe_incr(downgraded_key, downgraded_count)

        if post_failed:
            failed_key = self._get_minute_key("review.inline.post_failed")
            self._safe_incr(failed_key)
        else:
            posted_key = self._get_minute_key("review.inline.posted_total")
            self._safe_incr(posted_key, posted_count)

            if fallback_used:
                fallback_key = self._get_minute_key("review.inline.fallback_total")
                self._safe_incr(fallback_key)

        logger.debug("[Metrics] Inline comment result recorded", extra={
            "operation": "metrics_inline_comment",
            "trace_id": trace_id,
            "eligible_count": eligible_count,
            "validated_count": validated_count,
            "downgraded_count": downgraded_count,
            "posted_count": posted_count,
            "post_failed": post_failed,
            "fallback_used": fallback_used
        })

    def get_review_summary(self, window_minutes: int = 15) -> Dict:
        """
        Get summary of review metrics for EPIC B Phase B-B KPIs.

        Issue #2595: Diff-Aware Review Plumbing - C-lite Telemetry

        Returns:
            Dict with review KPI metrics:
            - diff_coverage_rate: % of PRs not truncated (target > 90%)
            - schema_pass_rate: % of comments passing schema (target > 95%)
            - inline_success_rate: % of inline comments posted (target > 90%)
            - delivery_rate: % of comments delivered (inline + fallback)
        """
        if not self.enabled:
            return {"enabled": False}

        fetch_success = self.get_window_count(
            "review.diff.fetch_success", window_minutes
        )
        fetch_failure = self.get_window_count(
            "review.diff.fetch_failure", window_minutes
        )
        truncated = self.get_window_count(
            "review.diff.truncated", window_minutes
        )
        not_truncated = self.get_window_count(
            "review.diff.not_truncated", window_minutes
        )
        lockfile_only = self.get_window_count(
            "review.diff.lockfile_only", window_minutes
        )

        schema_raw = self.get_window_count(
            "review.schema.raw_total", window_minutes
        )
        schema_normalized = self.get_window_count(
            "review.schema.normalized_total", window_minutes
        )
        schema_filtered = self.get_window_count(
            "review.schema.filtered_total", window_minutes
        )
        schema_empty = self.get_window_count(
            "review.schema.empty_output", window_minutes
        )
        llm_api_failed = self.get_window_count(
            "review.schema.llm_api_failed", window_minutes
        )

        inline_eligible = self.get_window_count(
            "review.inline.eligible_total", window_minutes
        )
        inline_validated = self.get_window_count(
            "review.inline.validated_total", window_minutes
        )
        inline_downgraded = self.get_window_count(
            "review.inline.downgraded_total", window_minutes
        )
        inline_posted = self.get_window_count(
            "review.inline.posted_total", window_minutes
        )
        inline_fallback = self.get_window_count(
            "review.inline.fallback_total", window_minutes
        )
        inline_post_failed = self.get_window_count(
            "review.inline.post_failed", window_minutes
        )
        inline_dry_run = self.get_window_count(
            "review.inline.dry_run", window_minutes
        )
        inline_feature_disabled = self.get_window_count(
            "review.inline.feature_disabled", window_minutes
        )

        diff_coverage_rate = round(
            not_truncated / fetch_success * 100, 2
        ) if fetch_success > 0 else 0

        schema_pass_rate = round(
            schema_normalized / schema_raw * 100, 2
        ) if schema_raw > 0 else 0

        inline_success_rate = round(
            inline_posted / inline_eligible * 100, 2
        ) if inline_eligible > 0 else 0

        delivery_rate = round(
            (inline_posted + inline_fallback) / inline_eligible * 100, 2
        ) if inline_eligible > 0 else 0

        return {
            "diff": {
                "fetch_success": fetch_success,
                "fetch_failure": fetch_failure,
                "truncated": truncated,
                "not_truncated": not_truncated,
                "lockfile_only_excluded": lockfile_only,
                "coverage_rate": diff_coverage_rate
            },
            "schema": {
                "raw_total": schema_raw,
                "normalized_total": schema_normalized,
                "filtered_total": schema_filtered,
                "empty_output_runs": schema_empty,
                "llm_api_failed_excluded": llm_api_failed,
                "pass_rate": schema_pass_rate
            },
            "inline": {
                "eligible_total": inline_eligible,
                "validated_total": inline_validated,
                "downgraded_total": inline_downgraded,
                "posted_total": inline_posted,
                "fallback_total": inline_fallback,
                "post_failed": inline_post_failed,
                "dry_run_excluded": inline_dry_run,
                "feature_disabled_excluded": inline_feature_disabled,
                "success_rate": inline_success_rate,
                "delivery_rate": delivery_rate
            },
            "kpis": {
                "diff_coverage_rate": diff_coverage_rate,
                "schema_pass_rate": schema_pass_rate,
                "inline_success_rate": inline_success_rate,
                "delivery_rate": delivery_rate
            }
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
