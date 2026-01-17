"""
LLM Reviewer Metrics - Observability for LLM Reviewer Agent

Issue #4130: P1 - Add JSON parsing failure metrics and alerting
EPIC B: LLM Reviewer Agent - Metrics and Alerting

This module provides observability for the LLM Reviewer:
- reviewer_json_parse_success: Successful JSON parse count
- reviewer_json_parse_failure: JSON parse failure count
- reviewer_json_repair_attempts: JSON repair attempt count
- reviewer_cross_provider_fallback: Cross-provider fallback count
- reviewer_total_reviews: Total review count
- reviewer_latency_ms: Review latency

Usage:
    from core.flow.reviewer_metrics import get_reviewer_metrics

    metrics = get_reviewer_metrics()

    # Record a successful review
    metrics.record_review(
        trace_id="abc123",
        latency_ms=1500.5,
        success=True,
        provider="gemini",
        json_parse_success=True,
    )

    # Record a JSON parse failure
    metrics.record_json_parse_failure(
        trace_id="abc123",
        error_type="json_decode_error",
        repair_attempted=True,
        repair_success=False,
    )

    # Get JSON parse failure rate
    rate = metrics.get_json_parse_failure_rate(window_minutes=60)
"""
import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Deque, Dict, Optional

logger = logging.getLogger(__name__)


# Metrics schema version for safe evolution
REVIEWER_METRICS_VERSION = "v1"


@dataclass
class ReviewerRecord:
    """Record of a single LLM review operation.

    Note:
        All timestamps are in UTC (using datetime.now(timezone.utc)).
    """

    trace_id: str
    timestamp: datetime  # UTC timestamp
    latency_ms: float
    success: bool
    provider: str
    json_parse_success: bool
    json_repair_attempted: bool = False
    json_repair_success: bool = False
    cross_provider_fallback: bool = False
    fallback_provider: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class JsonParseFailureRecord:
    """Record of a JSON parse failure event."""

    trace_id: str
    timestamp: datetime
    error_type: str  # json_decode_error, llm_repair_failed, all_repairs_failed
    repair_attempted: bool
    repair_success: bool
    original_provider: str
    input_length: int = 0


class ReviewerMetrics:
    """LLM Reviewer observability and metrics collection.

    This class collects and aggregates metrics for LLM Reviewer operations.
    It provides methods to record reviews and query aggregated metrics.

    Thread-safe: All operations are protected by a lock.
    """

    def __init__(self, max_records: int = 10000):
        """Initialize ReviewerMetrics.

        Args:
            max_records: Maximum number of records to keep in memory.
                         Uses deque with maxlen for O(1) FIFO eviction.
        """
        self._review_records: Deque[ReviewerRecord] = deque(maxlen=max_records)
        self._json_failure_records: Deque[JsonParseFailureRecord] = deque(maxlen=max_records)
        self._max_records = max_records
        self._lock = Lock()

        # Aggregated counters
        self._total_reviews = 0
        self._total_successes = 0
        self._total_failures = 0
        self._total_json_parse_successes = 0
        self._total_json_parse_failures = 0
        self._total_json_repair_attempts = 0
        self._total_json_repair_successes = 0
        self._total_cross_provider_fallbacks = 0
        self._provider_counts: Dict[str, int] = defaultdict(int)
        self._error_type_counts: Dict[str, int] = defaultdict(int)
        self._total_latency_ms = 0.0

    def record_review(
        self,
        trace_id: str,
        latency_ms: float,
        success: bool,
        provider: str,
        json_parse_success: bool,
        json_repair_attempted: bool = False,
        json_repair_success: bool = False,
        cross_provider_fallback: bool = False,
        fallback_provider: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Record a single LLM review operation.

        Args:
            trace_id: Unique identifier for the trace
            latency_ms: Review latency in milliseconds
            success: Whether the review completed successfully
            provider: LLM provider used (gemini, openai, etc.)
            json_parse_success: Whether JSON parsing succeeded
            json_repair_attempted: Whether JSON repair was attempted
            json_repair_success: Whether JSON repair succeeded
            cross_provider_fallback: Whether cross-provider fallback was used
            fallback_provider: Provider used for fallback (if any)
            error_type: Type of error (if success=False)
        """
        record = ReviewerRecord(
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            success=success,
            provider=provider,
            json_parse_success=json_parse_success,
            json_repair_attempted=json_repair_attempted,
            json_repair_success=json_repair_success,
            cross_provider_fallback=cross_provider_fallback,
            fallback_provider=fallback_provider,
            error_type=error_type,
        )

        with self._lock:
            self._review_records.append(record)

            # Update aggregates
            self._total_reviews += 1
            self._total_latency_ms += latency_ms
            self._provider_counts[provider] += 1

            if success:
                self._total_successes += 1
            else:
                self._total_failures += 1
                if error_type:
                    self._error_type_counts[error_type] += 1

            if json_parse_success:
                self._total_json_parse_successes += 1
            else:
                self._total_json_parse_failures += 1

            if json_repair_attempted:
                self._total_json_repair_attempts += 1
                if json_repair_success:
                    self._total_json_repair_successes += 1

            if cross_provider_fallback:
                self._total_cross_provider_fallbacks += 1

        # Log the review
        log_extra = {
            "trace_id": trace_id,
            "latency_ms": latency_ms,
            "success": success,
            "provider": provider,
            "json_parse_success": json_parse_success,
        }
        if error_type:
            log_extra["error_type"] = error_type
        if cross_provider_fallback:
            log_extra["cross_provider_fallback"] = True
            log_extra["fallback_provider"] = fallback_provider

        logger.info(
            "[ReviewerMetrics] Review recorded: provider=%s, success=%s, "
            "json_parse=%s, latency=%sms",
            provider, success, json_parse_success, latency_ms,
            extra=log_extra
        )

    def record_json_parse_failure(
        self,
        trace_id: str,
        error_type: str,
        repair_attempted: bool,
        repair_success: bool,
        original_provider: str,
        input_length: int = 0,
    ) -> None:
        """Record a JSON parse failure event.

        Args:
            trace_id: Unique identifier for the trace
            error_type: Type of error (json_decode_error, llm_repair_failed, etc.)
            repair_attempted: Whether repair was attempted
            repair_success: Whether repair succeeded
            original_provider: LLM provider that returned malformed JSON
            input_length: Length of the malformed JSON input
        """
        record = JsonParseFailureRecord(
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc),
            error_type=error_type,
            repair_attempted=repair_attempted,
            repair_success=repair_success,
            original_provider=original_provider,
            input_length=input_length,
        )

        with self._lock:
            self._json_failure_records.append(record)

        logger.warning(
            "[ReviewerMetrics] JSON parse failure: provider=%s, error_type=%s, "
            "repair_attempted=%s, repair_success=%s",
            original_provider, error_type, repair_attempted, repair_success,
            extra={
                "trace_id": trace_id,
                "error_type": error_type,
                "repair_attempted": repair_attempted,
                "repair_success": repair_success,
                "original_provider": original_provider,
                "input_length": input_length,
            }
        )

    def get_json_parse_failure_rate(self, window_minutes: int = 60) -> float:
        """Get the JSON parse failure rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Failure rate as a float (0.0 to 1.0)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 0.0

            failures = sum(1 for r in recent_records if not r.json_parse_success)
            return failures / len(recent_records)

    def get_json_repair_success_rate(self, window_minutes: int = 60) -> float:
        """Get the JSON repair success rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Success rate as a float (0.0 to 1.0), or 0.0 if no repairs attempted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff and r.json_repair_attempted
            ]

            if not recent_records:
                return 0.0

            successes = sum(1 for r in recent_records if r.json_repair_success)
            return successes / len(recent_records)

    def get_cross_provider_fallback_rate(self, window_minutes: int = 60) -> float:
        """Get the cross-provider fallback rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Fallback rate as a float (0.0 to 1.0)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 0.0

            fallbacks = sum(1 for r in recent_records if r.cross_provider_fallback)
            return fallbacks / len(recent_records)

    def get_success_rate(self, window_minutes: int = 60) -> float:
        """Get the overall review success rate within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Success rate as a float (0.0 to 1.0)
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 1.0  # No data = assume success

            successes = sum(1 for r in recent_records if r.success)
            return successes / len(recent_records)

    def get_average_latency(self, window_minutes: int = 60) -> float:
        """Get the average latency within a time window.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Average latency in milliseconds
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff
            ]

            if not recent_records:
                return 0.0

            return sum(r.latency_ms for r in recent_records) / len(recent_records)

    def get_provider_distribution(
        self,
        window_minutes: int = 60
    ) -> Dict[str, int]:
        """Get the distribution of providers used.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict mapping provider name to count
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            distribution: Dict[str, int] = defaultdict(int)
            for r in self._review_records:
                if r.timestamp >= cutoff:
                    distribution[r.provider] += 1
            return dict(distribution)

    def get_error_distribution(
        self,
        window_minutes: int = 60
    ) -> Dict[str, int]:
        """Get the distribution of error types.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict mapping error type to count
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            distribution: Dict[str, int] = defaultdict(int)
            for r in self._review_records:
                if r.timestamp >= cutoff and r.error_type:
                    distribution[r.error_type] += 1
            return dict(distribution)

    def get_summary(self, window_minutes: int = 60) -> dict:
        """Get a summary of reviewer metrics.

        Args:
            window_minutes: Time window in minutes (default: 60)

        Returns:
            Dict with summary metrics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        with self._lock:
            recent_records = [
                r for r in self._review_records
                if r.timestamp >= cutoff
            ]

            total = len(recent_records)
            successes = sum(1 for r in recent_records if r.success)
            failures = total - successes

            json_parse_successes = sum(1 for r in recent_records if r.json_parse_success)
            json_parse_failures = total - json_parse_successes

            json_repair_attempts = sum(1 for r in recent_records if r.json_repair_attempted)
            json_repair_successes = sum(
                1 for r in recent_records
                if r.json_repair_attempted and r.json_repair_success
            )

            cross_provider_fallbacks = sum(
                1 for r in recent_records if r.cross_provider_fallback
            )

            avg_latency = (
                sum(r.latency_ms for r in recent_records) / total
                if total > 0 else 0.0
            )

            # Compute distributions inline
            provider_dist: Dict[str, int] = defaultdict(int)
            error_dist: Dict[str, int] = defaultdict(int)
            for r in recent_records:
                provider_dist[r.provider] += 1
                if r.error_type:
                    error_dist[r.error_type] += 1

            return {
                "metrics_version": REVIEWER_METRICS_VERSION,
                "window_minutes": window_minutes,
                "total_reviews": total,
                "successes": successes,
                "failures": failures,
                "success_rate": successes / total if total > 0 else 1.0,
                "failure_rate": failures / total if total > 0 else 0.0,
                "json_parse_successes": json_parse_successes,
                "json_parse_failures": json_parse_failures,
                "json_parse_failure_rate": json_parse_failures / total if total > 0 else 0.0,
                "json_repair_attempts": json_repair_attempts,
                "json_repair_successes": json_repair_successes,
                "json_repair_success_rate": (
                    json_repair_successes / json_repair_attempts
                    if json_repair_attempts > 0 else 0.0
                ),
                "cross_provider_fallbacks": cross_provider_fallbacks,
                "cross_provider_fallback_rate": (
                    cross_provider_fallbacks / total if total > 0 else 0.0
                ),
                "average_latency_ms": avg_latency,
                "provider_distribution": dict(provider_dist),
                "error_distribution": dict(error_dist),
            }

    def get_all_time_summary(self) -> dict:
        """Get all-time summary metrics.

        Returns:
            Dict with all-time summary metrics
        """
        with self._lock:
            avg_latency = (
                self._total_latency_ms / self._total_reviews
                if self._total_reviews > 0 else 0.0
            )

            return {
                "metrics_version": REVIEWER_METRICS_VERSION,
                "total_reviews": self._total_reviews,
                "total_successes": self._total_successes,
                "total_failures": self._total_failures,
                "success_rate": (
                    self._total_successes / self._total_reviews
                    if self._total_reviews > 0 else 1.0
                ),
                "json_parse_successes": self._total_json_parse_successes,
                "json_parse_failures": self._total_json_parse_failures,
                "json_parse_failure_rate": (
                    self._total_json_parse_failures / self._total_reviews
                    if self._total_reviews > 0 else 0.0
                ),
                "json_repair_attempts": self._total_json_repair_attempts,
                "json_repair_successes": self._total_json_repair_successes,
                "json_repair_success_rate": (
                    self._total_json_repair_successes / self._total_json_repair_attempts
                    if self._total_json_repair_attempts > 0 else 0.0
                ),
                "cross_provider_fallbacks": self._total_cross_provider_fallbacks,
                "average_latency_ms": avg_latency,
                "provider_counts": dict(self._provider_counts),
                "error_type_counts": dict(self._error_type_counts),
            }

    def reset(self) -> None:
        """Reset all metrics.

        Use with caution - this clears all collected data.
        """
        with self._lock:
            self._review_records.clear()
            self._json_failure_records.clear()
            self._total_reviews = 0
            self._total_successes = 0
            self._total_failures = 0
            self._total_json_parse_successes = 0
            self._total_json_parse_failures = 0
            self._total_json_repair_attempts = 0
            self._total_json_repair_successes = 0
            self._total_cross_provider_fallbacks = 0
            self._provider_counts.clear()
            self._error_type_counts.clear()
            self._total_latency_ms = 0.0

        logger.info("[ReviewerMetrics] Metrics reset")


# Global metrics instance (singleton pattern)
_global_reviewer_metrics: Optional[ReviewerMetrics] = None
_global_reviewer_metrics_lock = Lock()


def get_reviewer_metrics() -> ReviewerMetrics:
    """Get the global ReviewerMetrics instance.

    Thread-safe singleton using double-checked locking pattern.

    Returns:
        The global ReviewerMetrics singleton
    """
    global _global_reviewer_metrics
    if _global_reviewer_metrics is None:
        with _global_reviewer_metrics_lock:
            # Double-check after acquiring lock to prevent race condition
            if _global_reviewer_metrics is None:
                _global_reviewer_metrics = ReviewerMetrics()
    return _global_reviewer_metrics
