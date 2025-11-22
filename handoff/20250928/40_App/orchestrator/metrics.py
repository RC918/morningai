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
import time
from typing import Dict, List, Optional, Tuple
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
                }
            }
        except Exception as e:
            logger.error(f"Failed to get canary summary: {e}")
            return {
                "enabled": True,
                "window_minutes": window_minutes,
                "error": str(e)
            }


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
