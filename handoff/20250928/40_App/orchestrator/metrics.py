#!/usr/bin/env python3
"""
Canary Metrics Module - Lightweight Redis-based metrics for canary deployment monitoring

Provides minute-bucket counters and latency histograms with TTL to track:
- Routing decisions (simple vs langgraph)
- Planner success/failure/error rates
- Latency distribution (p50, p90, p95, p99)

All metrics operations are wrapped in try/except to never break the job path.
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)

DEFAULT_BUCKETS_MS = [50, 100, 200, 400, 800, 1600, 3200]


class CanaryMetrics:
    """Lightweight canary metrics using Redis minute-bucket keys"""

    def __init__(self, redis_client: redis.Redis, enabled: bool = True, ttl_seconds: int = 7200):
        """
        Initialize canary metrics

        Args:
            redis_client: Redis client instance
            enabled: Whether metrics collection is enabled
            ttl_seconds: TTL for minute-bucket keys (default: 2 hours)
        """
        self.redis = redis_client
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.buckets_ms = DEFAULT_BUCKETS_MS

    def _get_minute_key(self, metric_name: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate minute-bucket key for a metric

        Args:
            metric_name: Name of the metric (e.g., 'decisions.simple')
            timestamp: Timestamp for the bucket (default: now)

        Returns:
            Redis key in format: metrics:canary:{metric}:{YYYYMMDDHHMM}
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        minute_str = timestamp.strftime("%Y%m%d%H%M")
        return f"metrics:canary:{metric_name}:{minute_str}"

    def incr_counter(self, metric_name: str, value: int = 1) -> None:
        """
        Increment a counter metric

        Args:
            metric_name: Name of the counter (e.g., 'decisions.simple', 'planner.success')
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
            logger.warning(f"Failed to increment counter {metric_name}: {e}")

    def observe_latency_ms(self, latency_ms: float) -> None:
        """
        Record a latency observation in histogram buckets

        Increments exactly one bucket: the first bucket where latency_ms <= bucket,
        or the 'inf' bucket if latency exceeds all finite buckets.

        Args:
            latency_ms: Latency in milliseconds
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

            key = self._get_minute_key(f"latency.bucket_{bucket_label}")

            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(key)
                pipe.execute()
        except Exception as e:
            logger.warning(f"Failed to observe latency {latency_ms}ms: {e}")

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
            total = 0

            for i in range(window_minutes):
                timestamp = now - timedelta(minutes=i)
                key = self._get_minute_key(metric_name, timestamp)
                value = self.redis.get(key)
                if value:
                    total += int(value)

            return total
        except Exception as e:
            logger.warning(f"Failed to get window counts for {metric_name}: {e}")
            return 0

    def get_latency_percentiles(self, window_minutes: int = 15) -> Dict[str, Optional[float]]:
        """
        Calculate approximate latency percentiles from histogram buckets

        Uses cumulative distribution: walks buckets from smallest to largest,
        accumulating counts until reaching the target percentile threshold.

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with p50, p90, p95, p99 in milliseconds (None if no data or unbounded tail)
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
                        key = self._get_minute_key(f"latency.bucket_{bucket}", mk)
                        pipe.get(key)

                for mk in minute_keys:
                    key = self._get_minute_key("latency.bucket_inf", mk)
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

            # Calculate total observations
            total = sum(bucket_counts.values()) + inf_count
            if total == 0:
                return {"p50": None, "p90": None, "p95": None, "p99": None}

            # Calculate percentiles by walking cumulative distribution
            percentiles = {"p50": None, "p90": None, "p95": None, "p99": None}
            targets = [50, 90, 95, 99]
            target_idx = 0
            cumulative = 0

            for bucket in sorted(self.buckets_ms):
                cumulative += bucket_counts[bucket]
                cumulative_pct = (cumulative / total) * 100.0

                # Check if we've reached any target percentiles
                while target_idx < len(targets) and cumulative_pct >= targets[target_idx]:
                    percentiles[f"p{targets[target_idx]}"] = float(bucket)
                    target_idx += 1

                if target_idx >= len(targets):
                    break

            return percentiles
        except Exception as e:
            logger.warning(f"Failed to calculate latency percentiles: {e}")
            return {"p50": None, "p90": None, "p95": None, "p99": None}

    def get_canary_summary(self, window_minutes: int = 15) -> Dict:
        """
        Get comprehensive canary metrics summary

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with counts, rates, latency percentiles, and SLO compliance
        """
        if not self.enabled:
            return {
                "enabled": False,
                "window_minutes": window_minutes,
                "message": "Canary metrics disabled"
            }

        try:
            decisions_simple = self.get_window_counts("decisions.simple", window_minutes)
            decisions_langgraph = self.get_window_counts("decisions.langgraph", window_minutes)
            total_decisions = decisions_simple + decisions_langgraph

            planner_success = self.get_window_counts("planner.success", window_minutes)
            planner_failure = self.get_window_counts("planner.failure", window_minutes)
            planner_error_5xx = self.get_window_counts("planner.error_5xx", window_minutes)
            total_planner = planner_success + planner_failure + planner_error_5xx

            failure_rate = (planner_failure / total_planner * 100) if total_planner > 0 else 0
            error_5xx_rate = (planner_error_5xx / total_planner * 100) if total_planner > 0 else 0

            latency = self.get_latency_percentiles(window_minutes)

            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "counts": {
                    "decisions_simple": decisions_simple,
                    "decisions_langgraph": decisions_langgraph,
                    "total_decisions": total_decisions,
                    "planner_success": planner_success,
                    "planner_failure": planner_failure,
                    "planner_error_5xx": planner_error_5xx,
                    "total_planner": total_planner
                },
                "rates": {
                    "failure_rate": round(failure_rate, 2),
                    "error_5xx_rate": round(error_5xx_rate, 2)
                },
                "latency": {
                    "p50_ms": latency["p50"],
                    "p90_ms": latency["p90"],
                    "p95_ms": latency["p95"],
                    "p99_ms": latency["p99"],
                    "max_bucket_ms": float(max(self.buckets_ms))
                },
                "drift": self.get_drift_summary(window_minutes)
            }
        except Exception as e:
            logger.error(f"Failed to get canary summary: {e}")
            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "error": str(e)
            }

    # EPIC I-1: Drift Detection Metrics
    def incr_drift_event(self, drift_type: str, provider: str = "unknown") -> None:
        """
        Increment drift event counter

        EPIC I-1: Runtime Drift Detection metrics

        Args:
            drift_type: Type of drift (json_parse_error, schema_violation, etc.)
            provider: LLM provider name
        """
        if not self.enabled:
            return

        try:
            # Global drift counter
            self.incr_counter("drift.total")
            # Per-type counter
            self.incr_counter(f"drift.type.{drift_type}")
            # Per-provider counter
            self.incr_counter(f"drift.provider.{provider}")
        except Exception as e:
            logger.warning(f"Failed to increment drift event: {e}")

    def incr_drift_check(self) -> None:
        """
        Increment drift check counter (total validations performed)

        EPIC I-1: Runtime Drift Detection metrics
        """
        if not self.enabled:
            return

        try:
            self.incr_counter("drift.checks")
        except Exception as e:
            logger.warning(f"Failed to increment drift check: {e}")

    def get_drift_summary(self, window_minutes: int = 15) -> dict:
        """
        Get drift detection metrics summary

        EPIC I-1: Runtime Drift Detection metrics

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with drift counts and rates
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            total_checks = self.get_window_counts("drift.checks", window_minutes)
            total_drift = self.get_window_counts("drift.total", window_minutes)

            # Per-type breakdown
            drift_types = [
                "json_parse_error",
                "schema_violation",
                "empty_response",
                "unexpected_format",
                "missing_required_field"
            ]
            type_counts = {}
            for dt in drift_types:
                count = self.get_window_counts(f"drift.type.{dt}", window_minutes)
                if count > 0:
                    type_counts[dt] = count

            drift_rate = (total_drift / total_checks * 100) if total_checks > 0 else 0

            return {
                "enabled": True,
                "total_checks": total_checks,
                "total_drift": total_drift,
                "drift_rate": round(drift_rate, 2),
                "by_type": type_counts
            }
        except Exception as e:
            logger.warning(f"Failed to get drift summary: {e}")
            return {"enabled": True, "error": str(e)}

    # EPIC I-2: Provider Health Scoring
    def record_provider_request(
        self,
        provider: str,
        latency_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record a provider request for health scoring

        EPIC I-2: Provider Health Scoring metrics

        Args:
            provider: LLM provider name (openai, gemini, alicloud, siliconflow)
            latency_ms: Request latency in milliseconds
            success: Whether the request succeeded
            error_type: Type of error if failed (e.g., "timeout", "rate_limit", "api_error")
        """
        if not self.enabled:
            return

        try:
            # Total requests counter
            self.incr_counter(f"provider.{provider}.requests")

            # Success/error counters
            if success:
                self.incr_counter(f"provider.{provider}.success")
            else:
                self.incr_counter(f"provider.{provider}.errors")
                if error_type:
                    self.incr_counter(f"provider.{provider}.error.{error_type}")

            # Latency recording (using histogram buckets)
            self._record_provider_latency(provider, latency_ms)

        except Exception as e:
            logger.warning(f"Failed to record provider request for {provider}: {e}")

    def _record_provider_latency(self, provider: str, latency_ms: float) -> None:
        """
        Record provider latency in histogram buckets

        EPIC I-2: Provider Health Scoring metrics

        Performance optimization: Uses a single Redis pipeline for both bucket
        and sum recording to reduce round-trips (gemini-code-assist suggestion).
        """
        try:
            # Find the appropriate bucket
            target_bucket = None
            for bucket in self.buckets_ms:
                if latency_ms <= bucket:
                    target_bucket = bucket
                    break

            bucket_label = str(target_bucket) if target_bucket else "inf"
            bucket_key = self._get_minute_key(
                f"provider.{provider}.latency.bucket_{bucket_label}"
            )
            sum_key = self._get_minute_key(f"provider.{provider}.latency.sum")

            # Single pipeline for both bucket and sum recording (reduces Redis round-trips)
            with self.redis.pipeline(transaction=True) as pipe:
                # Bucket key: initialize if not exists, then increment
                pipe.set(bucket_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(bucket_key)
                # Sum key: initialize if not exists, then add latency
                pipe.set(sum_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incrbyfloat(sum_key, latency_ms)
                pipe.execute()

        except Exception as e:
            logger.warning(f"Failed to record provider latency for {provider}: {e}")

    def get_provider_health(
        self,
        provider: str,
        window_minutes: Optional[int] = None,
        latency_weight: Optional[float] = None,
        error_weight: Optional[float] = None,
        drift_weight: Optional[float] = None
    ) -> dict:
        """
        Calculate provider health score

        EPIC I-2: Provider Health Scoring

        Health score formula:
        health = 100 - (latency_penalty * latency_weight +
                        error_rate * error_weight +
                        drift_rate * drift_weight)

        Where:
        - latency_penalty: Normalized latency score (0-100, based on p95 vs target)
        - error_rate: Percentage of failed requests (0-100)
        - drift_rate: Percentage of drift events (0-100)

        Args:
            provider: LLM provider name
            window_minutes: Time window in minutes (default: from settings or 15)
            latency_weight: Weight for latency (default: from settings or 0.3)
            error_weight: Weight for error rate (default: from settings or 0.4)
            drift_weight: Weight for drift rate (default: from settings or 0.3)

        Returns:
            Dict with health score and component metrics
        """
        if not self.enabled:
            return {"enabled": False, "provider": provider}

        try:
            # Fallback to settings if parameters not provided
            try:
                from common.config.settings import settings
                if window_minutes is None:
                    window_minutes = getattr(
                        settings, "provider_health_window_minutes", 15
                    )
                if latency_weight is None:
                    latency_weight = getattr(
                        settings, "provider_health_latency_weight", 0.3
                    )
                if error_weight is None:
                    error_weight = getattr(
                        settings, "provider_health_error_weight", 0.4
                    )
                if drift_weight is None:
                    drift_weight = getattr(
                        settings, "provider_health_drift_weight", 0.3
                    )
            except ImportError:
                # Fallback to defaults if settings not available
                window_minutes = window_minutes or 15
                latency_weight = latency_weight if latency_weight is not None else 0.3
                error_weight = error_weight if error_weight is not None else 0.4
                drift_weight = drift_weight if drift_weight is not None else 0.3
            # Get request counts
            total_requests = self.get_window_counts(
                f"provider.{provider}.requests", window_minutes
            )
            success_count = self.get_window_counts(
                f"provider.{provider}.success", window_minutes
            )
            error_count = self.get_window_counts(
                f"provider.{provider}.errors", window_minutes
            )

            # Calculate error rate
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0

            # Get latency metrics
            latency_stats = self._get_provider_latency_stats(provider, window_minutes)

            # Get drift rate for this provider
            # Use per-provider drift events divided by total requests for accurate per-provider drift rate
            # (EPIC I-1 records drift.provider.{provider} for each drift event)
            drift_events = self.get_window_counts(
                f"drift.provider.{provider}", window_minutes
            )
            drift_rate = (drift_events / total_requests * 100) if total_requests > 0 else 0

            # Calculate latency penalty (0-100)
            # Target: p95 < 2000ms = 0 penalty, p95 > 10000ms = 100 penalty
            p95 = latency_stats.get("p95_ms") or 0
            latency_penalty = min(100, max(0, (p95 - 2000) / 80))  # Linear scale

            # Calculate health score
            health_score = max(0, min(100, 100 - (
                latency_penalty * latency_weight +
                error_rate * error_weight +
                drift_rate * drift_weight
            )))

            return {
                "enabled": True,
                "provider": provider,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "health_score": round(health_score, 2),
                "metrics": {
                    "total_requests": total_requests,
                    "success_count": success_count,
                    "error_count": error_count,
                    "error_rate": round(error_rate, 2),
                    "drift_rate": round(drift_rate, 2),
                    "latency": latency_stats
                },
                "weights": {
                    "latency": latency_weight,
                    "error": error_weight,
                    "drift": drift_weight
                }
            }

        except Exception as e:
            logger.warning(f"Failed to get provider health for {provider}: {e}")
            return {"enabled": True, "provider": provider, "error": str(e)}

    def _get_provider_latency_stats(
        self,
        provider: str,
        window_minutes: int = 15
    ) -> dict:
        """
        Get provider latency statistics

        EPIC I-2: Provider Health Scoring metrics
        """
        try:
            now = datetime.utcnow()
            minute_keys = [now - timedelta(minutes=i) for i in range(window_minutes)]

            # Get bucket counts
            bucket_counts = {}
            with self.redis.pipeline(transaction=False) as pipe:
                for bucket in self.buckets_ms:
                    for mk in minute_keys:
                        key = self._get_minute_key(
                            f"provider.{provider}.latency.bucket_{bucket}", mk
                        )
                        pipe.get(key)

                for mk in minute_keys:
                    key = self._get_minute_key(
                        f"provider.{provider}.latency.bucket_inf", mk
                    )
                    pipe.get(key)

                # Get sum for average
                for mk in minute_keys:
                    key = self._get_minute_key(
                        f"provider.{provider}.latency.sum", mk
                    )
                    pipe.get(key)

                results = pipe.execute()

            # Parse bucket counts
            idx = 0
            for bucket in self.buckets_ms:
                count = 0
                for _ in minute_keys:
                    val = results[idx]
                    idx += 1
                    count += int(val) if val is not None else 0
                bucket_counts[bucket] = count

            # Parse inf bucket
            inf_count = 0
            for _ in minute_keys:
                val = results[idx]
                idx += 1
                inf_count += int(val) if val is not None else 0

            # Parse sum
            total_sum = 0.0
            for _ in minute_keys:
                val = results[idx]
                idx += 1
                total_sum += float(val) if val is not None else 0.0

            # Calculate total and percentiles
            total = sum(bucket_counts.values()) + inf_count
            if total == 0:
                return {
                    "p50_ms": None,
                    "p90_ms": None,
                    "p95_ms": None,
                    "p99_ms": None,
                    "avg_ms": None,
                    "total_observations": 0
                }

            avg_ms = total_sum / total if total > 0 else None

            # Calculate percentiles
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

            return {
                "p50_ms": percentiles["p50"],
                "p90_ms": percentiles["p90"],
                "p95_ms": percentiles["p95"],
                "p99_ms": percentiles["p99"],
                "avg_ms": round(avg_ms, 2) if avg_ms else None,
                "total_observations": total
            }

        except Exception as e:
            logger.warning(f"Failed to get provider latency stats for {provider}: {e}")
            return {"error": str(e)}

    def get_all_providers_health(
        self,
        providers: Optional[List[str]] = None,
        window_minutes: int = 15
    ) -> dict:
        """
        Get health scores for all providers

        EPIC I-2: Provider Health Scoring

        Args:
            providers: List of provider names (default: all known providers)
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with health scores for all providers
        """
        if not self.enabled:
            return {"enabled": False}

        if providers is None:
            providers = ["openai", "gemini", "alicloud", "siliconflow"]

        try:
            results = {}
            for provider in providers:
                results[provider] = self.get_provider_health(provider, window_minutes)

            # Sort by health score (descending)
            sorted_providers = sorted(
                results.items(),
                key=lambda x: x[1].get("health_score", 0) if isinstance(x[1], dict) else 0,
                reverse=True
            )

            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "providers": dict(sorted_providers),
                "ranking": [p[0] for p in sorted_providers]
            }

        except Exception as e:
            logger.warning(f"Failed to get all providers health: {e}")
            return {"enabled": True, "error": str(e)}

    # Issue #3486: Router Metrics for Flow Controller v3
    def record_router_decision(
        self,
        next_node: str,
        success: bool,
        latency_ms: float,
        decision_mode: str,
        fallback_reason: Optional[str] = None
    ) -> None:
        """
        Record a router decision for cross-process metrics

        Issue #3486: RouterMetrics Operationalization Gap
        EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing

        Args:
            next_node: The node selected by the router (fixer, publisher, executor, decision)
            success: Whether the routing decision was successful
            latency_ms: Decision latency in milliseconds
            decision_mode: How the decision was made (fast_path, slow_path, ci_failure_fast_path, outer_fallback)
            fallback_reason: Reason for fallback if success=False
        """
        if not self.enabled:
            return

        try:
            # Total decisions counter
            self.incr_counter("router.decisions")

            # Per-node counter
            self.incr_counter(f"router.node.{next_node}")

            # Per-mode counter
            self.incr_counter(f"router.mode.{decision_mode}")

            # Success/fallback counters
            if success:
                self.incr_counter("router.success")
            else:
                self.incr_counter("router.fallbacks")
                if fallback_reason:
                    self.incr_counter(f"router.fallback.{fallback_reason}")

            # Latency recording (using histogram buckets)
            self._record_router_latency(latency_ms)

        except Exception as e:
            logger.warning(f"Failed to record router decision: {e}")

    def _record_router_latency(self, latency_ms: float) -> None:
        """
        Record router latency in histogram buckets

        Issue #3486: RouterMetrics Operationalization Gap
        """
        try:
            # Find the appropriate bucket
            target_bucket = None
            for bucket in self.buckets_ms:
                if latency_ms <= bucket:
                    target_bucket = bucket
                    break

            bucket_label = str(target_bucket) if target_bucket else "inf"
            bucket_key = self._get_minute_key(f"router.latency.bucket_{bucket_label}")
            sum_key = self._get_minute_key("router.latency.sum")
            count_key = self._get_minute_key("router.latency.count")

            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(bucket_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(bucket_key)
                pipe.set(sum_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incrbyfloat(sum_key, latency_ms)
                pipe.set(count_key, 0, ex=self.ttl_seconds, nx=True)
                pipe.incr(count_key)
                pipe.execute()

        except Exception as e:
            logger.warning(f"Failed to record router latency: {e}")

    def get_router_metrics_summary(self, window_minutes: int = 15) -> dict:
        """
        Get router metrics summary for API endpoint

        Issue #3486: RouterMetrics Operationalization Gap
        EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing

        Args:
            window_minutes: Time window in minutes (default: 15)

        Returns:
            Dict with router metrics summary
        """
        if not self.enabled:
            return {"enabled": False, "message": "Canary metrics disabled"}

        try:
            total_decisions = self.get_window_counts("router.decisions", window_minutes)
            total_success = self.get_window_counts("router.success", window_minutes)
            total_fallbacks = self.get_window_counts("router.fallbacks", window_minutes)

            # Per-node breakdown
            nodes = ["fixer", "publisher", "executor", "decision"]
            node_counts = {}
            for node in nodes:
                count = self.get_window_counts(f"router.node.{node}", window_minutes)
                if count > 0:
                    node_counts[node] = count

            # Per-mode breakdown
            modes = ["fast_path", "slow_path", "ci_failure_fast_path", "outer_fallback"]
            mode_counts = {}
            for mode in modes:
                count = self.get_window_counts(f"router.mode.{mode}", window_minutes)
                if count > 0:
                    mode_counts[mode] = count

            # Per-fallback-reason breakdown
            fallback_reasons = ["llm_fallback", "router_exception", "llm_error", "timeout"]
            fallback_counts = {}
            for reason in fallback_reasons:
                count = self.get_window_counts(f"router.fallback.{reason}", window_minutes)
                if count > 0:
                    fallback_counts[reason] = count

            # Calculate rates
            success_rate = (total_success / total_decisions * 100) if total_decisions > 0 else 0
            fallback_rate = (total_fallbacks / total_decisions * 100) if total_decisions > 0 else 0

            # Calculate latency percentiles
            latency_percentiles = self._get_router_latency_percentiles(window_minutes)

            # Calculate average latency
            avg_latency = self._get_router_average_latency(window_minutes)

            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "total_decisions": total_decisions,
                "successes": total_success,
                "fallbacks": total_fallbacks,
                "success_rate": round(success_rate, 2),
                "fallback_rate": round(fallback_rate, 2),
                "average_latency_ms": round(avg_latency, 2) if avg_latency else None,
                "latency_p50_ms": latency_percentiles.get("p50"),
                "latency_p90_ms": latency_percentiles.get("p90"),
                "latency_p95_ms": latency_percentiles.get("p95"),
                "latency_p99_ms": latency_percentiles.get("p99"),
                "node_distribution": node_counts,
                "decision_mode_distribution": mode_counts,
                "fallback_distribution": fallback_counts,
            }

        except Exception as e:
            logger.error(f"Failed to get router metrics summary: {e}")
            return {"enabled": True, "error": str(e)}

    def _get_router_latency_percentiles(self, window_minutes: int = 15) -> dict:
        """
        Calculate router latency percentiles from histogram buckets

        Issue #3486: RouterMetrics Operationalization Gap

        Uses Redis pipeline to batch all GET operations in a single round trip
        to reduce network overhead (reviewer feedback).
        """
        try:
            now = datetime.utcnow()
            minute_keys = [now - timedelta(minutes=i) for i in range(window_minutes)]

            # Use pipeline to batch all bucket key fetches
            bucket_counts = {}
            with self.redis.pipeline(transaction=False) as pipe:
                # Queue all bucket keys for all minutes
                for bucket in self.buckets_ms:
                    for mk in minute_keys:
                        key = self._get_minute_key(f"router.latency.bucket_{bucket}", mk)
                        pipe.get(key)

                # Queue inf bucket keys
                for mk in minute_keys:
                    key = self._get_minute_key("router.latency.bucket_inf", mk)
                    pipe.get(key)

                results = pipe.execute()

            # Parse results: first (len(buckets_ms) * window_minutes) are bucket results
            idx = 0
            total = 0
            for bucket in self.buckets_ms:
                bucket_total = 0
                for _ in minute_keys:
                    val = results[idx]
                    if val:
                        bucket_total += int(val)
                    idx += 1
                bucket_counts[bucket] = bucket_total
                total += bucket_total

            # Parse inf bucket results
            inf_total = 0
            for _ in minute_keys:
                val = results[idx]
                if val:
                    inf_total += int(val)
                idx += 1
            bucket_counts["inf"] = inf_total
            total += inf_total

            if total == 0:
                return {"p50": None, "p90": None, "p95": None, "p99": None}

            # Calculate percentiles using cumulative distribution
            targets = [50, 90, 95, 99]
            percentiles = {"p50": None, "p90": None, "p95": None, "p99": None}
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
            logger.warning(f"Failed to calculate router latency percentiles: {e}")
            return {"p50": None, "p90": None, "p95": None, "p99": None}

    def _get_router_average_latency(self, window_minutes: int = 15) -> Optional[float]:
        """
        Calculate router average latency from sum and count

        Issue #3486: RouterMetrics Operationalization Gap

        Uses Redis pipeline to batch all GET operations in a single round trip
        to reduce network overhead (reviewer feedback).
        """
        try:
            now = datetime.utcnow()

            # Use pipeline to batch all sum/count key fetches
            with self.redis.pipeline(transaction=False) as pipe:
                for i in range(window_minutes):
                    ts = now - timedelta(minutes=i)
                    sum_key = self._get_minute_key("router.latency.sum", ts)
                    count_key = self._get_minute_key("router.latency.count", ts)
                    pipe.get(sum_key)
                    pipe.get(count_key)

                results = pipe.execute()

            # Parse results: alternating sum, count values
            total_sum = 0.0
            total_count = 0
            for i in range(window_minutes):
                sum_val = results[i * 2]
                count_val = results[i * 2 + 1]

                if sum_val:
                    total_sum += float(sum_val)
                if count_val:
                    total_count += int(count_val)

            if total_count == 0:
                return None

            return total_sum / total_count

        except Exception as e:
            logger.warning(f"Failed to calculate router average latency: {e}")
            return None


def create_canary_metrics(redis_client: redis.Redis, enabled: bool = True) -> CanaryMetrics:
    """
    Factory function to create CanaryMetrics instance

    Args:
        redis_client: Redis client instance
        enabled: Whether metrics collection is enabled

    Returns:
        CanaryMetrics instance
    """
    return CanaryMetrics(redis_client, enabled=enabled)


# Global singleton for canary metrics (EPIC I-2)
_canary_metrics: Optional[CanaryMetrics] = None
_canary_metrics_lock = threading.Lock()


def get_canary_metrics() -> Optional[CanaryMetrics]:
    """
    Get the global CanaryMetrics singleton instance

    EPIC I-2: Provider Health Scoring

    This function provides thread-safe access to the global metrics instance.
    Returns None if Redis is not configured or metrics are disabled.

    Returns:
        CanaryMetrics instance or None if not available
    """
    global _canary_metrics

    if _canary_metrics is not None:
        return _canary_metrics

    with _canary_metrics_lock:
        if _canary_metrics is not None:
            return _canary_metrics

        try:
            import os
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                logger.debug("[CanaryMetrics] REDIS_URL not configured, metrics disabled")
                return None

            redis_client = redis.from_url(redis_url)
            _canary_metrics = CanaryMetrics(redis_client, enabled=True)
            logger.info("[CanaryMetrics] Initialized global metrics instance")
            return _canary_metrics

        except Exception as e:
            logger.warning(f"[CanaryMetrics] Failed to initialize: {e}")
            return None


def reset_canary_metrics() -> None:
    """
    Reset the global CanaryMetrics singleton (useful for testing)

    EPIC I-2: Provider Health Scoring
    """
    global _canary_metrics
    with _canary_metrics_lock:
        _canary_metrics = None
