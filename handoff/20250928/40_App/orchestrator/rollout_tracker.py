#!/usr/bin/env python3
"""
LangGraph 100% Rollout Tracker - Issue #2214

Provides comprehensive tracking for LangGraph rollout progress including:
- Rollout stage management (0% -> 5% -> 15% -> 30% -> 50% -> 100%)
- SLO monitoring (p95 latency, failure rate, 5xx error rate)
- Auto circuit breaker for automatic rollback on SLO breach
- LangGraph vs Simple Mode comparison dashboard
- Rollout health assessment

All metrics operations are wrapped in try/except to never break the job path.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class RolloutStage(Enum):
    """Rollout stages for LangGraph deployment"""
    STAGE_0 = 0      # 0% - Simple Mode only
    STAGE_1 = 5      # 5% - Basic stability verification
    STAGE_2 = 15     # 15% - 1 week no P0 incident
    STAGE_3 = 30     # 30% - 2 weeks no P0 incident
    STAGE_4 = 50     # 50% - Success rate > 95%
    STAGE_5 = 100    # 100% - Success rate > 98%, full rollout

    @classmethod
    def from_percent(cls, percent: int) -> "RolloutStage":
        """Get rollout stage from percentage"""
        if percent >= 100:
            return cls.STAGE_5
        elif percent >= 50:
            return cls.STAGE_4
        elif percent >= 30:
            return cls.STAGE_3
        elif percent >= 15:
            return cls.STAGE_2
        elif percent >= 5:
            return cls.STAGE_1
        else:
            return cls.STAGE_0

    @property
    def next_stage(self) -> Optional["RolloutStage"]:
        """Get next rollout stage"""
        stages = list(RolloutStage)
        current_idx = stages.index(self)
        if current_idx < len(stages) - 1:
            return stages[current_idx + 1]
        return None

    @property
    def previous_stage(self) -> Optional["RolloutStage"]:
        """Get previous rollout stage for rollback"""
        stages = list(RolloutStage)
        current_idx = stages.index(self)
        if current_idx > 0:
            return stages[current_idx - 1]
        return None


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Tripped, blocking LangGraph
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RolloutSLO:
    """SLO thresholds for rollout progression"""
    p95_latency_ms: float = 5000.0      # p95 < 5s
    failure_rate_percent: float = 5.0    # failure rate < 5%
    error_5xx_rate_percent: float = 1.0  # 5xx error rate < 1%
    min_sample_size: int = 10            # Minimum samples for evaluation

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StageRequirement:
    """Requirements for advancing to next stage"""
    stage: RolloutStage
    min_success_rate: float
    min_duration_days: int
    max_p0_incidents: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.name,
            "percent": self.stage.value,
            "min_success_rate": self.min_success_rate,
            "min_duration_days": self.min_duration_days,
            "max_p0_incidents": self.max_p0_incidents,
            "description": self.description
        }


# Stage advancement requirements
STAGE_REQUIREMENTS: Dict[RolloutStage, StageRequirement] = {
    RolloutStage.STAGE_1: StageRequirement(
        stage=RolloutStage.STAGE_1,
        min_success_rate=90.0,
        min_duration_days=0,
        max_p0_incidents=0,
        description="Basic stability verification"
    ),
    RolloutStage.STAGE_2: StageRequirement(
        stage=RolloutStage.STAGE_2,
        min_success_rate=93.0,
        min_duration_days=7,
        max_p0_incidents=0,
        description="1 week no P0 incident"
    ),
    RolloutStage.STAGE_3: StageRequirement(
        stage=RolloutStage.STAGE_3,
        min_success_rate=95.0,
        min_duration_days=14,
        max_p0_incidents=0,
        description="2 weeks no P0 incident"
    ),
    RolloutStage.STAGE_4: StageRequirement(
        stage=RolloutStage.STAGE_4,
        min_success_rate=95.0,
        min_duration_days=7,
        max_p0_incidents=0,
        description="Success rate > 95%"
    ),
    RolloutStage.STAGE_5: StageRequirement(
        stage=RolloutStage.STAGE_5,
        min_success_rate=98.0,
        min_duration_days=7,
        max_p0_incidents=0,
        description="Success rate > 98%, full rollout"
    ),
}


@dataclass
class RolloutMetrics:
    """Metrics for rollout comparison"""
    total_tasks: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_5xx_count: int = 0
    p50_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    success_rate: float = 0.0
    failure_rate: float = 0.0
    error_5xx_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RolloutComparison:
    """Comparison between LangGraph and Simple Mode"""
    window_minutes: int
    timestamp: str
    langgraph: RolloutMetrics
    simple: RolloutMetrics
    langgraph_advantage: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_minutes": self.window_minutes,
            "timestamp": self.timestamp,
            "langgraph": self.langgraph.to_dict(),
            "simple": self.simple.to_dict(),
            "langgraph_advantage": self.langgraph_advantage
        }


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    state: CircuitState = CircuitState.CLOSED
    last_state_change: str = ""
    failure_count: int = 0
    success_count_since_half_open: int = 0
    last_failure_reason: str = ""
    cooldown_until: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "last_state_change": self.last_state_change,
            "failure_count": self.failure_count,
            "success_count_since_half_open": self.success_count_since_half_open,
            "last_failure_reason": self.last_failure_reason,
            "cooldown_until": self.cooldown_until
        }


@dataclass
class RolloutHealth:
    """Overall rollout health assessment"""
    healthy: bool
    current_stage: RolloutStage
    current_percent: int
    slo_compliant: bool
    circuit_state: CircuitState
    can_advance: bool
    should_rollback: bool
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "current_stage": self.current_stage.name,
            "current_percent": self.current_percent,
            "slo_compliant": self.slo_compliant,
            "circuit_state": self.circuit_state.value,
            "can_advance": self.can_advance,
            "should_rollback": self.should_rollback,
            "issues": self.issues,
            "recommendations": self.recommendations
        }


class RolloutTracker:
    """
    LangGraph 100% Rollout Tracker

    Tracks rollout progress, monitors SLOs, and provides auto circuit breaker
    functionality for safe LangGraph deployment.
    """

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        enabled: bool = True,
        slo: Optional[RolloutSLO] = None,
        ttl_seconds: int = 86400,  # 24 hours
        key_prefix: str = "metrics:rollout"
    ):
        """
        Initialize rollout tracker

        Args:
            redis_client: Redis client instance (optional, tracking disabled if None)
            enabled: Whether tracking is enabled
            slo: SLO thresholds (uses defaults if None)
            ttl_seconds: TTL for metric keys (default: 24 hours)
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis_client
        self.enabled = enabled and redis_client is not None
        self.slo = slo or RolloutSLO()
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._circuit_breaker = CircuitBreakerState()

        # Circuit breaker configuration
        self.circuit_failure_threshold = 5  # Open after 5 consecutive failures
        self.circuit_success_threshold = 3  # Close after 3 successes in half-open
        self.circuit_cooldown_seconds = 300  # 5 minutes cooldown

    def _get_minute_key(self, metric_name: str, timestamp: Optional[datetime] = None) -> str:
        """Generate minute-bucket key for a metric"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
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
            logger.warning(f"[RolloutTracker] Failed to increment {key}: {e}")

    def _safe_get(self, key: str) -> int:
        """Safely get a Redis key value"""
        if not self.enabled:
            return 0

        try:
            value = self.redis.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to get {key}: {e}")
            return 0

    def _get_window_count(self, metric_name: str, window_minutes: int = 15) -> int:
        """Get total count for a metric over a time window using mget for efficiency"""
        if not self.enabled:
            return 0

        try:
            now = datetime.now(timezone.utc)
            keys = [
                self._get_minute_key(metric_name, now - timedelta(minutes=i))
                for i in range(window_minutes)
            ]

            # Use mget for batch retrieval (single round-trip)
            values = self.redis.mget(keys)
            total = sum(int(v) for v in values if v is not None)

            return total
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to get window count for {metric_name}: {e}")
            return 0

    # ==================== Metric Recording ====================

    def record_langgraph_task(
        self,
        trace_id: str,
        success: bool,
        latency_ms: Optional[float] = None,
        is_5xx_error: bool = False
    ) -> None:
        """
        Record a LangGraph task execution

        Args:
            trace_id: Unique trace identifier
            success: Whether the task succeeded
            latency_ms: Task latency in milliseconds
            is_5xx_error: Whether this was a 5xx error
        """
        if not self.enabled:
            return

        try:
            # Record task count
            self._safe_incr(self._get_minute_key("langgraph.total"))

            if success:
                self._safe_incr(self._get_minute_key("langgraph.success"))
                self._update_circuit_breaker_success()
            else:
                self._safe_incr(self._get_minute_key("langgraph.failure"))
                reason = "5xx_error" if is_5xx_error else "task_failure"
                self._update_circuit_breaker_failure(reason)

            if is_5xx_error:
                self._safe_incr(self._get_minute_key("langgraph.error_5xx"))

            # Record latency bucket
            if latency_ms is not None:
                self._record_latency("langgraph", latency_ms)

            logger.debug(
                "[RolloutTracker] Recorded LangGraph task",
                extra={
                    "trace_id": trace_id,
                    "success": success,
                    "latency_ms": latency_ms,
                    "is_5xx_error": is_5xx_error
                }
            )
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to record LangGraph task: {e}")

    def record_simple_task(
        self,
        trace_id: str,
        success: bool,
        latency_ms: Optional[float] = None,
        is_5xx_error: bool = False
    ) -> None:
        """
        Record a Simple Mode task execution

        Args:
            trace_id: Unique trace identifier
            success: Whether the task succeeded
            latency_ms: Task latency in milliseconds
            is_5xx_error: Whether this was a 5xx error
        """
        if not self.enabled:
            return

        try:
            # Record task count
            self._safe_incr(self._get_minute_key("simple.total"))

            if success:
                self._safe_incr(self._get_minute_key("simple.success"))
            else:
                self._safe_incr(self._get_minute_key("simple.failure"))

            if is_5xx_error:
                self._safe_incr(self._get_minute_key("simple.error_5xx"))

            # Record latency bucket
            if latency_ms is not None:
                self._record_latency("simple", latency_ms)

            logger.debug(
                "[RolloutTracker] Recorded Simple task",
                extra={
                    "trace_id": trace_id,
                    "success": success,
                    "latency_ms": latency_ms,
                    "is_5xx_error": is_5xx_error
                }
            )
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to record Simple task: {e}")

    def _record_latency(self, mode: str, latency_ms: float) -> None:
        """Record latency in histogram buckets"""
        buckets = [100, 500, 1000, 2000, 5000, 10000, 30000]

        try:
            target_bucket = None
            for bucket in buckets:
                if latency_ms <= bucket:
                    target_bucket = bucket
                    break

            bucket_label = str(target_bucket) if target_bucket else "inf"
            key = self._get_minute_key(f"{mode}.latency_bucket_{bucket_label}")
            self._safe_incr(key)
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to record latency: {e}")

    def record_p0_incident(self, description: str, mode: str = "langgraph") -> None:
        """
        Record a P0 incident

        Args:
            description: Incident description
            mode: Which mode caused the incident (langgraph or simple)
        """
        if not self.enabled:
            return

        try:
            key = f"{self.key_prefix}:p0_incidents:{mode}"
            incident_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": description
            }
            self.redis.lpush(key, json.dumps(incident_data))
            self.redis.ltrim(key, 0, 99)  # Keep last 100 incidents
            self.redis.expire(key, 86400 * 30)  # 30 days

            logger.warning(
                "[RolloutTracker] P0 incident recorded",
                extra={"mode": mode, "description": description}
            )
        except Exception as e:
            logger.error(f"[RolloutTracker] Failed to record P0 incident: {e}")

    # ==================== Circuit Breaker ====================

    def _update_circuit_breaker_success(self) -> None:
        """Update circuit breaker on successful task"""
        if self._circuit_breaker.state == CircuitState.HALF_OPEN:
            self._circuit_breaker.success_count_since_half_open += 1
            if self._circuit_breaker.success_count_since_half_open >= self.circuit_success_threshold:
                self._set_circuit_state(CircuitState.CLOSED)
                logger.info("[RolloutTracker] Circuit breaker closed after recovery")
        elif self._circuit_breaker.state == CircuitState.CLOSED:
            # Reset failure count on success
            self._circuit_breaker.failure_count = 0

    def _update_circuit_breaker_failure(self, reason: str) -> None:
        """Update circuit breaker on failed task"""
        self._circuit_breaker.failure_count += 1
        self._circuit_breaker.last_failure_reason = reason

        if self._circuit_breaker.state == CircuitState.HALF_OPEN:
            # Any failure in half-open trips back to open
            self._set_circuit_state(CircuitState.OPEN)
            logger.warning("[RolloutTracker] Circuit breaker re-opened after failure in half-open")
        elif self._circuit_breaker.state == CircuitState.CLOSED:
            if self._circuit_breaker.failure_count >= self.circuit_failure_threshold:
                self._set_circuit_state(CircuitState.OPEN)
                logger.warning(
                    f"[RolloutTracker] Circuit breaker opened after {self.circuit_failure_threshold} failures"
                )

    def _set_circuit_state(self, state: CircuitState) -> None:
        """Set circuit breaker state"""
        self._circuit_breaker.state = state
        self._circuit_breaker.last_state_change = datetime.now(timezone.utc).isoformat()

        if state == CircuitState.OPEN:
            cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=self.circuit_cooldown_seconds)
            self._circuit_breaker.cooldown_until = cooldown_until.isoformat()
        elif state == CircuitState.HALF_OPEN:
            self._circuit_breaker.success_count_since_half_open = 0
        elif state == CircuitState.CLOSED:
            self._circuit_breaker.failure_count = 0
            self._circuit_breaker.cooldown_until = None

    def check_circuit_breaker(self) -> bool:
        """
        Check if LangGraph should be allowed

        Returns:
            True if LangGraph is allowed, False if circuit is open
        """
        if self._circuit_breaker.state == CircuitState.CLOSED:
            return True

        if self._circuit_breaker.state == CircuitState.OPEN:
            # Check if cooldown has passed
            if self._circuit_breaker.cooldown_until:
                cooldown_time = datetime.fromisoformat(self._circuit_breaker.cooldown_until.replace('Z', '+00:00'))
                if datetime.now(timezone.utc) >= cooldown_time:
                    self._set_circuit_state(CircuitState.HALF_OPEN)
                    logger.info("[RolloutTracker] Circuit breaker entering half-open state")
                    return True
            return False

        # Half-open: allow limited traffic
        return True

    def get_circuit_breaker_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        return self._circuit_breaker

    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker to closed state"""
        self._set_circuit_state(CircuitState.CLOSED)
        logger.info("[RolloutTracker] Circuit breaker manually reset")

    # ==================== Metrics Retrieval ====================

    def _get_mode_metrics(self, mode: str, window_minutes: int = 15) -> RolloutMetrics:
        """Get metrics for a specific mode"""
        total = self._get_window_count(f"{mode}.total", window_minutes)
        success = self._get_window_count(f"{mode}.success", window_minutes)
        failure = self._get_window_count(f"{mode}.failure", window_minutes)
        error_5xx = self._get_window_count(f"{mode}.error_5xx", window_minutes)

        success_rate = (success / total * 100) if total > 0 else 0.0
        failure_rate = (failure / total * 100) if total > 0 else 0.0
        error_5xx_rate = (error_5xx / total * 100) if total > 0 else 0.0

        # Get latency percentiles
        latency = self._get_latency_percentiles(mode, window_minutes)

        return RolloutMetrics(
            total_tasks=total,
            success_count=success,
            failure_count=failure,
            error_5xx_count=error_5xx,
            p50_latency_ms=latency.get("p50"),
            p95_latency_ms=latency.get("p95"),
            p99_latency_ms=latency.get("p99"),
            success_rate=round(success_rate, 2),
            failure_rate=round(failure_rate, 2),
            error_5xx_rate=round(error_5xx_rate, 2)
        )

    def _get_latency_percentiles(self, mode: str, window_minutes: int = 15) -> Dict[str, Optional[float]]:
        """Calculate latency percentiles from histogram buckets"""
        if not self.enabled:
            return {"p50": None, "p95": None, "p99": None}

        buckets = [100, 500, 1000, 2000, 5000, 10000, 30000]

        try:
            bucket_counts = {}
            for bucket in buckets:
                count = self._get_window_count(f"{mode}.latency_bucket_{bucket}", window_minutes)
                bucket_counts[bucket] = count

            inf_count = self._get_window_count(f"{mode}.latency_bucket_inf", window_minutes)

            total = sum(bucket_counts.values()) + inf_count
            if total == 0:
                return {"p50": None, "p95": None, "p99": None}

            percentiles = {"p50": None, "p95": None, "p99": None}
            targets = [50, 95, 99]
            target_idx = 0
            cumulative = 0

            for bucket in sorted(buckets):
                cumulative += bucket_counts[bucket]
                cumulative_pct = (cumulative / total) * 100.0

                while target_idx < len(targets) and cumulative_pct >= targets[target_idx]:
                    percentiles[f"p{targets[target_idx]}"] = float(bucket)
                    target_idx += 1

                if target_idx >= len(targets):
                    break

            return percentiles
        except Exception as e:
            logger.warning(f"[RolloutTracker] Failed to calculate latency percentiles: {e}")
            return {"p50": None, "p95": None, "p99": None}

    def get_comparison(self, window_minutes: int = 15) -> RolloutComparison:
        """
        Get comparison between LangGraph and Simple Mode

        Args:
            window_minutes: Time window in minutes

        Returns:
            RolloutComparison with metrics for both modes
        """
        langgraph_metrics = self._get_mode_metrics("langgraph", window_minutes)
        simple_metrics = self._get_mode_metrics("simple", window_minutes)

        # Calculate advantage metrics
        advantage = {}
        if langgraph_metrics.success_rate > 0 and simple_metrics.success_rate > 0:
            advantage["success_rate_diff"] = round(
                langgraph_metrics.success_rate - simple_metrics.success_rate, 2
            )

        if langgraph_metrics.p95_latency_ms and simple_metrics.p95_latency_ms:
            advantage["p95_latency_diff_ms"] = round(
                simple_metrics.p95_latency_ms - langgraph_metrics.p95_latency_ms, 2
            )

        return RolloutComparison(
            window_minutes=window_minutes,
            timestamp=datetime.now(timezone.utc).isoformat(),
            langgraph=langgraph_metrics,
            simple=simple_metrics,
            langgraph_advantage=advantage
        )

    # ==================== SLO Evaluation ====================

    def evaluate_slo_compliance(self, window_minutes: int = 15) -> Dict[str, Any]:
        """
        Evaluate SLO compliance for LangGraph

        Args:
            window_minutes: Time window in minutes

        Returns:
            Dict with SLO compliance status and details
        """
        metrics = self._get_mode_metrics("langgraph", window_minutes)

        violations = []
        compliant = True

        # Check minimum sample size
        if metrics.total_tasks < self.slo.min_sample_size:
            return {
                "compliant": None,
                "reason": f"Insufficient data: {metrics.total_tasks} < {self.slo.min_sample_size} samples",
                "metrics": metrics.to_dict(),
                "slo": self.slo.to_dict(),
                "violations": []
            }

        # Check p95 latency
        if metrics.p95_latency_ms is not None and metrics.p95_latency_ms > self.slo.p95_latency_ms:
            violations.append({
                "metric": "p95_latency_ms",
                "value": metrics.p95_latency_ms,
                "threshold": self.slo.p95_latency_ms,
                "severity": "high"
            })
            compliant = False

        # Check failure rate
        if metrics.failure_rate > self.slo.failure_rate_percent:
            violations.append({
                "metric": "failure_rate",
                "value": metrics.failure_rate,
                "threshold": self.slo.failure_rate_percent,
                "severity": "critical"
            })
            compliant = False

        # Check 5xx error rate
        if metrics.error_5xx_rate > self.slo.error_5xx_rate_percent:
            violations.append({
                "metric": "error_5xx_rate",
                "value": metrics.error_5xx_rate,
                "threshold": self.slo.error_5xx_rate_percent,
                "severity": "critical"
            })
            compliant = False

        return {
            "compliant": compliant,
            "metrics": metrics.to_dict(),
            "slo": self.slo.to_dict(),
            "violations": violations,
            "window_minutes": window_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ==================== Rollout Stage Management ====================

    def get_current_stage(self, current_percent: int) -> RolloutStage:
        """Get current rollout stage based on percentage"""
        return RolloutStage.from_percent(current_percent)

    def can_advance_stage(self, current_percent: int, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Check if rollout can advance to next stage

        Args:
            current_percent: Current rollout percentage
            window_minutes: Time window for evaluation

        Returns:
            Dict with advancement eligibility and details
        """
        current_stage = self.get_current_stage(current_percent)
        next_stage = current_stage.next_stage

        if next_stage is None:
            return {
                "can_advance": False,
                "reason": "Already at maximum rollout (100%)",
                "current_stage": current_stage.name,
                "current_percent": current_percent
            }

        requirement = STAGE_REQUIREMENTS.get(next_stage)
        if requirement is None:
            return {
                "can_advance": False,
                "reason": f"No requirements defined for {next_stage.name}",
                "current_stage": current_stage.name,
                "next_stage": next_stage.name
            }

        # Check SLO compliance
        slo_result = self.evaluate_slo_compliance(window_minutes)
        if not slo_result.get("compliant"):
            return {
                "can_advance": False,
                "reason": "SLO violations detected",
                "current_stage": current_stage.name,
                "next_stage": next_stage.name,
                "slo_result": slo_result,
                "requirement": requirement.to_dict()
            }

        # Check success rate requirement
        metrics = self._get_mode_metrics("langgraph", window_minutes)
        if metrics.success_rate < requirement.min_success_rate:
            return {
                "can_advance": False,
                "reason": f"Success rate {metrics.success_rate}% < {requirement.min_success_rate}% required",
                "current_stage": current_stage.name,
                "next_stage": next_stage.name,
                "metrics": metrics.to_dict(),
                "requirement": requirement.to_dict()
            }

        # Check circuit breaker
        if self._circuit_breaker.state != CircuitState.CLOSED:
            return {
                "can_advance": False,
                "reason": f"Circuit breaker is {self._circuit_breaker.state.value}",
                "current_stage": current_stage.name,
                "next_stage": next_stage.name,
                "circuit_state": self._circuit_breaker.to_dict()
            }

        return {
            "can_advance": True,
            "current_stage": current_stage.name,
            "next_stage": next_stage.name,
            "next_percent": next_stage.value,
            "metrics": metrics.to_dict(),
            "requirement": requirement.to_dict()
        }

    def should_rollback(self, current_percent: int, window_minutes: int = 15) -> Dict[str, Any]:
        """
        Check if rollout should rollback to previous stage

        Args:
            current_percent: Current rollout percentage
            window_minutes: Time window for evaluation

        Returns:
            Dict with rollback recommendation and details
        """
        current_stage = self.get_current_stage(current_percent)
        previous_stage = current_stage.previous_stage

        # Check circuit breaker
        if self._circuit_breaker.state == CircuitState.OPEN:
            return {
                "should_rollback": True,
                "reason": "Circuit breaker is open",
                "current_stage": current_stage.name,
                "target_stage": previous_stage.name if previous_stage else "STAGE_0",
                "target_percent": previous_stage.value if previous_stage else 0,
                "circuit_state": self._circuit_breaker.to_dict()
            }

        # Check SLO compliance
        slo_result = self.evaluate_slo_compliance(window_minutes)
        if slo_result.get("compliant") is False:
            critical_violations = [
                v for v in slo_result.get("violations", [])
                if v.get("severity") == "critical"
            ]
            if critical_violations:
                return {
                    "should_rollback": True,
                    "reason": "Critical SLO violations detected",
                    "current_stage": current_stage.name,
                    "target_stage": previous_stage.name if previous_stage else "STAGE_0",
                    "target_percent": previous_stage.value if previous_stage else 0,
                    "slo_result": slo_result
                }

        return {
            "should_rollback": False,
            "current_stage": current_stage.name,
            "current_percent": current_percent,
            "slo_result": slo_result
        }

    # ==================== Health Assessment ====================

    def get_rollout_health(self, current_percent: int, window_minutes: int = 15) -> RolloutHealth:
        """
        Get comprehensive rollout health assessment

        Args:
            current_percent: Current rollout percentage
            window_minutes: Time window for evaluation

        Returns:
            RolloutHealth with overall assessment
        """
        current_stage = self.get_current_stage(current_percent)
        slo_result = self.evaluate_slo_compliance(window_minutes)
        advance_result = self.can_advance_stage(current_percent, window_minutes)
        rollback_result = self.should_rollback(current_percent, window_minutes)

        issues = []
        recommendations = []

        # Check SLO compliance
        slo_compliant = slo_result.get("compliant", True)
        if slo_compliant is False:
            for violation in slo_result.get("violations", []):
                issues.append(
                    f"{violation['metric']}: {violation['value']} exceeds threshold {violation['threshold']}"
                )

        # Check circuit breaker
        circuit_state = self._circuit_breaker.state
        if circuit_state != CircuitState.CLOSED:
            issues.append(f"Circuit breaker is {circuit_state.value}")

        # Generate recommendations
        if rollback_result.get("should_rollback"):
            recommendations.append(
                f"Consider rolling back to {rollback_result.get('target_percent', 0)}%"
            )
        elif advance_result.get("can_advance"):
            recommendations.append(
                f"Ready to advance to {advance_result.get('next_percent', current_percent)}%"
            )

        if not slo_compliant:
            recommendations.append("Investigate SLO violations before proceeding")

        healthy = (
            slo_compliant is not False and
            circuit_state == CircuitState.CLOSED and
            not rollback_result.get("should_rollback", False)
        )

        return RolloutHealth(
            healthy=healthy,
            current_stage=current_stage,
            current_percent=current_percent,
            slo_compliant=slo_compliant if slo_compliant is not None else True,
            circuit_state=circuit_state,
            can_advance=advance_result.get("can_advance", False),
            should_rollback=rollback_result.get("should_rollback", False),
            issues=issues,
            recommendations=recommendations
        )

    # ==================== Dashboard Summary ====================

    def get_dashboard_summary(self, current_percent: int, window_minutes: int = 15) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary for monitoring

        Args:
            current_percent: Current rollout percentage
            window_minutes: Time window for evaluation

        Returns:
            Dict with all dashboard data
        """
        comparison = self.get_comparison(window_minutes)
        health = self.get_rollout_health(current_percent, window_minutes)
        slo_result = self.evaluate_slo_compliance(window_minutes)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "window_minutes": window_minutes,
            "rollout": {
                "current_percent": current_percent,
                "current_stage": health.current_stage.name,
                "target_stages": [
                    {"stage": s.name, "percent": s.value}
                    for s in RolloutStage
                ]
            },
            "health": health.to_dict(),
            "comparison": comparison.to_dict(),
            "slo": slo_result,
            "circuit_breaker": self._circuit_breaker.to_dict(),
            "stage_requirements": {
                stage.name: req.to_dict()
                for stage, req in STAGE_REQUIREMENTS.items()
            }
        }


def create_rollout_tracker(
    redis_client: Optional["redis.Redis"] = None,
    enabled: bool = True,
    slo: Optional[RolloutSLO] = None
) -> RolloutTracker:
    """
    Factory function to create RolloutTracker instance

    Args:
        redis_client: Redis client instance
        enabled: Whether tracking is enabled
        slo: SLO thresholds (uses defaults if None)

    Returns:
        RolloutTracker instance
    """
    return RolloutTracker(redis_client, enabled=enabled, slo=slo)
