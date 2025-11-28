#!/usr/bin/env python3
"""
Phase 3 Metrics Module - Monitoring for ProjectEngineerAgent and multi-agent orchestration

Provides Redis-based metrics for tracking:
- ProjectEngineerAgent task execution (success/failure/timeout)
- Task type distribution
- Execution latency by task type
- Code generation vs analysis-only mode usage
- Semantic rule violations

All metrics operations are wrapped in try/except to never break the job path.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)

# Default latency buckets for Phase 3 (longer tasks than Phase 1)
DEFAULT_PHASE3_BUCKETS_MS = [1000, 5000, 10000, 30000, 60000, 120000, 300000]


class Phase3Metrics:
    """Phase 3 metrics for ProjectEngineerAgent and multi-agent orchestration"""

    def __init__(self, redis_client: redis.Redis, enabled: bool = True, ttl_seconds: int = 7200):
        """
        Initialize Phase 3 metrics

        Args:
            redis_client: Redis client instance
            enabled: Whether metrics collection is enabled
            ttl_seconds: TTL for minute-bucket keys (default: 2 hours)
        """
        self.redis = redis_client
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.buckets_ms = DEFAULT_PHASE3_BUCKETS_MS

    def _get_minute_key(self, metric_name: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate minute-bucket key for a metric

        Args:
            metric_name: Name of the metric (e.g., 'pe.task.success')
            timestamp: Timestamp for the bucket (default: now)

        Returns:
            Redis key in format: metrics:phase3:{metric}:{YYYYMMDDHHMM}
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        minute_str = timestamp.strftime("%Y%m%d%H%M")
        return f"metrics:phase3:{metric_name}:{minute_str}"

    def incr_counter(self, metric_name: str, value: int = 1) -> None:
        """
        Increment a counter metric

        Args:
            metric_name: Name of the counter (e.g., 'pe.task.success', 'pe.task.timeout')
            value: Increment value (default: 1)
        """
        if not self.enabled:
            return

        try:
            key = self._get_minute_key(metric_name)
            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incrby(key, value)
                pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to increment Phase 3 counter {metric_name}: {e}")

    def observe_latency_ms(self, latency_ms: float, task_type: str = "general") -> None:
        """
        Record a latency observation in histogram buckets

        Args:
            latency_ms: Latency in milliseconds
            task_type: Task type for categorization (default: "general")
        """
        if not self.enabled:
            return

        try:
            target_bucket = None
            for bucket in self.buckets_ms:
                if latency_ms <= bucket:
                    target_bucket = bucket
                    break

            if target_bucket is not None:
                bucket_label = str(target_bucket)
            else:
                bucket_label = "inf"

            # Record overall and per-task-type latency in a single pipeline
            key = self._get_minute_key(f"pe.latency.bucket_{bucket_label}")
            task_key = self._get_minute_key(f"pe.latency.{task_type}.bucket_{bucket_label}")
            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(key)
                pipe.set(task_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(task_key)
                pipe.execute()

        except Exception as e:
            logger.warning(f"Failed to observe Phase 3 latency {latency_ms}ms: {e}")

    def record_task_execution(
        self,
        task_id: str,
        status: str,
        task_type: str,
        elapsed_ms: float,
        mode: str = "analysis_only",
        tenant_id: Optional[str] = None
    ) -> None:
        """
        Record a ProjectEngineerAgent task execution

        Args:
            task_id: Unique task identifier
            status: Task status (success, failed, timeout, skipped)
            task_type: Task type (documentation_update, test_generation, etc.)
            elapsed_ms: Execution time in milliseconds
            mode: Execution mode (analysis_only, execution)
            tenant_id: Optional tenant ID for multi-tenant tracking
        """
        if not self.enabled:
            return

        try:
            # Record status counter
            self.incr_counter(f"pe.task.{status}")

            # Record task type counter
            self.incr_counter(f"pe.task_type.{task_type}")

            # Record mode counter
            self.incr_counter(f"pe.mode.{mode}")

            # Record latency
            self.observe_latency_ms(elapsed_ms, task_type)

            # Log structured metric
            logger.info(
                "[Phase3Metrics] Task execution recorded",
                extra={
                    "operation": "phase3_metrics",
                    "task_id": task_id,
                    "status": status,
                    "task_type": task_type,
                    "elapsed_ms": elapsed_ms,
                    "mode": mode,
                    "tenant_id": tenant_id
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record Phase 3 task execution: {e}")

    def record_semantic_rule_violation(
        self,
        task_id: str,
        rule_type: str,
        details: str
    ) -> None:
        """
        Record a semantic rule violation

        Args:
            task_id: Task identifier
            rule_type: Type of rule violated (repo_whitelist, directory_whitelist, task_type_whitelist)
            details: Details about the violation
        """
        if not self.enabled:
            return

        try:
            self.incr_counter(f"pe.rule_violation.{rule_type}")

            logger.warning(
                "[Phase3Metrics] Semantic rule violation",
                extra={
                    "operation": "phase3_metrics",
                    "task_id": task_id,
                    "rule_type": rule_type,
                    "details": details
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record semantic rule violation: {e}")

    def record_timeout(self, task_id: str, timeout_seconds: int, elapsed_ms: float) -> None:
        """
        Record a task timeout event

        Args:
            task_id: Task identifier
            timeout_seconds: Configured timeout in seconds
            elapsed_ms: Actual elapsed time in milliseconds
        """
        if not self.enabled:
            return

        try:
            self.incr_counter("pe.task.timeout")

            logger.warning(
                "[Phase3Metrics] Task timeout",
                extra={
                    "operation": "phase3_metrics",
                    "task_id": task_id,
                    "timeout_seconds": timeout_seconds,
                    "elapsed_ms": elapsed_ms
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record timeout: {e}")

    def get_window_counts(self, metric_name: str, window_minutes: int = 15) -> int:
        """
        Get total count for a metric over a time window

        Args:
            metric_name: Name of the metric
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Total count across all minute buckets in the window
        """
        if not self.enabled:
            return 0

        try:
            now = datetime.utcnow()
            # Use MGET to retrieve all values in one network round-trip
            keys = [self._get_minute_key(metric_name, now - timedelta(minutes=i)) for i in range(window_minutes)]
            values = self.redis.mget(keys)
            total = sum(int(v) for v in values if v is not None)
            return total
        except Exception as e:
            logger.warning(f"Failed to get window counts for {metric_name}: {e}")
            return 0

    def get_latency_percentiles(self, window_minutes: int = 15) -> Dict[str, Optional[float]]:
        """
        Calculate approximate latency percentiles from histogram buckets

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with p50, p90, p95, p99 in milliseconds (None if no data)
        """
        if not self.enabled:
            return {"p50": None, "p90": None, "p95": None, "p99": None}

        try:
            now = datetime.utcnow()
            minute_keys = [now - timedelta(minutes=i) for i in range(window_minutes)]

            bucket_counts = {}
            with self.redis.pipeline(transaction=False) as pipe:
                for bucket in self.buckets_ms:
                    for mk in minute_keys:
                        key = self._get_minute_key(f"pe.latency.bucket_{bucket}", mk)
                        pipe.get(key)

                for mk in minute_keys:
                    key = self._get_minute_key("pe.latency.bucket_inf", mk)
                    pipe.get(key)

                results = pipe.execute()

            idx = 0
            for bucket in self.buckets_ms:
                count = 0
                for _ in minute_keys:
                    val = results[idx]
                    idx += 1
                    count += int(val) if val is not None else 0
                bucket_counts[bucket] = count

            inf_count = 0
            for _ in minute_keys:
                val = results[idx]
                idx += 1
                inf_count += int(val) if val is not None else 0

            total = sum(bucket_counts.values()) + inf_count
            if total == 0:
                return {"p50": None, "p90": None, "p95": None, "p99": None}

            percentiles = {"p50": None, "p90": None, "p95": None, "p99": None}
            targets = [50, 90, 95, 99]
            target_idx = 0
            cumulative = 0

            for bucket in sorted(self.buckets_ms):
                cumulative += bucket_counts[bucket]
                cumulative_pct = (cumulative / total) * 100.0

                while target_idx < len(targets) and cumulative_pct >= targets[target_idx]:
                    percentiles[f"p{targets[target_idx]}"] = float(bucket)
                    target_idx += 1

                if target_idx >= len(targets):
                    break

            return percentiles
        except Exception as e:
            logger.warning(f"Failed to calculate Phase 3 latency percentiles: {e}")
            return {"p50": None, "p90": None, "p95": None, "p99": None}

    def get_phase3_summary(self, window_minutes: int = 15) -> Dict:
        """
        Get comprehensive Phase 3 metrics summary

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with counts, rates, latency percentiles, and task type distribution
        """
        if not self.enabled:
            return {
                "enabled": False,
                "window_minutes": window_minutes,
                "message": "Phase 3 metrics disabled"
            }

        try:
            # Task status counts
            task_success = self.get_window_counts("pe.task.success", window_minutes)
            task_failed = self.get_window_counts("pe.task.failed", window_minutes)
            task_timeout = self.get_window_counts("pe.task.timeout", window_minutes)
            task_skipped = self.get_window_counts("pe.task.skipped", window_minutes)
            total_tasks = task_success + task_failed + task_timeout + task_skipped

            # Mode counts
            mode_analysis = self.get_window_counts("pe.mode.analysis_only", window_minutes)
            mode_execution = self.get_window_counts("pe.mode.execution", window_minutes)

            # Rule violation counts
            rule_repo = self.get_window_counts("pe.rule_violation.repo_whitelist", window_minutes)
            rule_directory = self.get_window_counts("pe.rule_violation.directory_whitelist", window_minutes)
            rule_task_type = self.get_window_counts("pe.rule_violation.task_type_whitelist", window_minutes)
            total_violations = rule_repo + rule_directory + rule_task_type

            # Calculate rates
            success_rate = (task_success / total_tasks * 100) if total_tasks > 0 else 0
            failure_rate = (task_failed / total_tasks * 100) if total_tasks > 0 else 0
            timeout_rate = (task_timeout / total_tasks * 100) if total_tasks > 0 else 0

            # Get latency percentiles
            latency = self.get_latency_percentiles(window_minutes)

            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "counts": {
                    "task_success": task_success,
                    "task_failed": task_failed,
                    "task_timeout": task_timeout,
                    "task_skipped": task_skipped,
                    "total_tasks": total_tasks,
                    "mode_analysis": mode_analysis,
                    "mode_execution": mode_execution,
                    "rule_violations": total_violations
                },
                "rates": {
                    "success_rate": round(success_rate, 2),
                    "failure_rate": round(failure_rate, 2),
                    "timeout_rate": round(timeout_rate, 2)
                },
                "latency": {
                    "p50_ms": latency["p50"],
                    "p90_ms": latency["p90"],
                    "p95_ms": latency["p95"],
                    "p99_ms": latency["p99"],
                    "max_bucket_ms": float(max(self.buckets_ms))
                },
                "rule_violations": {
                    "repo_whitelist": rule_repo,
                    "directory_whitelist": rule_directory,
                    "task_type_whitelist": rule_task_type
                }
            }
        except Exception as e:
            logger.error(f"Failed to get Phase 3 summary: {e}")
            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "error": str(e)
            }


def create_phase3_metrics(redis_client: redis.Redis, enabled: bool = True) -> Phase3Metrics:
    """
    Factory function to create Phase3Metrics instance

    Args:
        redis_client: Redis client instance
        enabled: Whether metrics collection is enabled

    Returns:
        Phase3Metrics instance
    """
    return Phase3Metrics(redis_client, enabled=enabled)
