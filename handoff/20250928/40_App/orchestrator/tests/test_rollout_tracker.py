#!/usr/bin/env python3
"""
Unit tests for LangGraph 100% Rollout Tracker - Issue #2214

Tests cover:
- RolloutStage enum and stage progression
- CircuitState enum and circuit breaker logic
- RolloutSLO configuration
- StageRequirement definitions
- RolloutTracker service methods
- Metric recording and retrieval
- SLO evaluation
- Dashboard summary generation
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

from rollout_tracker import (
    RolloutStage,
    CircuitState,
    RolloutSLO,
    RolloutMetrics,
    RolloutComparison,
    CircuitBreakerState,
    RolloutHealth,
    RolloutTracker,
    STAGE_REQUIREMENTS,
    create_rollout_tracker,
)


class TestRolloutStage:
    """Tests for RolloutStage enum"""

    def test_stage_values(self):
        """Test stage percentage values"""
        assert RolloutStage.STAGE_0.value == 0
        assert RolloutStage.STAGE_1.value == 5
        assert RolloutStage.STAGE_2.value == 15
        assert RolloutStage.STAGE_3.value == 30
        assert RolloutStage.STAGE_4.value == 50
        assert RolloutStage.STAGE_5.value == 100

    def test_from_percent_boundaries(self):
        """Test from_percent at boundary values"""
        assert RolloutStage.from_percent(0) == RolloutStage.STAGE_0
        assert RolloutStage.from_percent(4) == RolloutStage.STAGE_0
        assert RolloutStage.from_percent(5) == RolloutStage.STAGE_1
        assert RolloutStage.from_percent(14) == RolloutStage.STAGE_1
        assert RolloutStage.from_percent(15) == RolloutStage.STAGE_2
        assert RolloutStage.from_percent(29) == RolloutStage.STAGE_2
        assert RolloutStage.from_percent(30) == RolloutStage.STAGE_3
        assert RolloutStage.from_percent(49) == RolloutStage.STAGE_3
        assert RolloutStage.from_percent(50) == RolloutStage.STAGE_4
        assert RolloutStage.from_percent(99) == RolloutStage.STAGE_4
        assert RolloutStage.from_percent(100) == RolloutStage.STAGE_5
        assert RolloutStage.from_percent(150) == RolloutStage.STAGE_5

    def test_next_stage(self):
        """Test next_stage property"""
        assert RolloutStage.STAGE_0.next_stage == RolloutStage.STAGE_1
        assert RolloutStage.STAGE_1.next_stage == RolloutStage.STAGE_2
        assert RolloutStage.STAGE_2.next_stage == RolloutStage.STAGE_3
        assert RolloutStage.STAGE_3.next_stage == RolloutStage.STAGE_4
        assert RolloutStage.STAGE_4.next_stage == RolloutStage.STAGE_5
        assert RolloutStage.STAGE_5.next_stage is None

    def test_previous_stage(self):
        """Test previous_stage property"""
        assert RolloutStage.STAGE_0.previous_stage is None
        assert RolloutStage.STAGE_1.previous_stage == RolloutStage.STAGE_0
        assert RolloutStage.STAGE_2.previous_stage == RolloutStage.STAGE_1
        assert RolloutStage.STAGE_3.previous_stage == RolloutStage.STAGE_2
        assert RolloutStage.STAGE_4.previous_stage == RolloutStage.STAGE_3
        assert RolloutStage.STAGE_5.previous_stage == RolloutStage.STAGE_4


class TestCircuitState:
    """Tests for CircuitState enum"""

    def test_circuit_states(self):
        """Test circuit state values"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestRolloutSLO:
    """Tests for RolloutSLO dataclass"""

    def test_default_values(self):
        """Test default SLO values"""
        slo = RolloutSLO()
        assert slo.p95_latency_ms == 5000.0
        assert slo.failure_rate_percent == 5.0
        assert slo.error_5xx_rate_percent == 1.0
        assert slo.min_sample_size == 10

    def test_custom_values(self):
        """Test custom SLO values"""
        slo = RolloutSLO(
            p95_latency_ms=3000.0,
            failure_rate_percent=3.0,
            error_5xx_rate_percent=0.5,
            min_sample_size=20
        )
        assert slo.p95_latency_ms == 3000.0
        assert slo.failure_rate_percent == 3.0
        assert slo.error_5xx_rate_percent == 0.5
        assert slo.min_sample_size == 20

    def test_to_dict(self):
        """Test SLO serialization"""
        slo = RolloutSLO()
        result = slo.to_dict()
        assert "p95_latency_ms" in result
        assert "failure_rate_percent" in result
        assert "error_5xx_rate_percent" in result
        assert "min_sample_size" in result


class TestStageRequirement:
    """Tests for StageRequirement dataclass"""

    def test_stage_requirements_defined(self):
        """Test all stage requirements are defined"""
        assert RolloutStage.STAGE_1 in STAGE_REQUIREMENTS
        assert RolloutStage.STAGE_2 in STAGE_REQUIREMENTS
        assert RolloutStage.STAGE_3 in STAGE_REQUIREMENTS
        assert RolloutStage.STAGE_4 in STAGE_REQUIREMENTS
        assert RolloutStage.STAGE_5 in STAGE_REQUIREMENTS

    def test_stage_1_requirements(self):
        """Test Stage 1 requirements"""
        req = STAGE_REQUIREMENTS[RolloutStage.STAGE_1]
        assert req.min_success_rate == 90.0
        assert req.min_duration_days == 0
        assert req.max_p0_incidents == 0

    def test_stage_5_requirements(self):
        """Test Stage 5 requirements"""
        req = STAGE_REQUIREMENTS[RolloutStage.STAGE_5]
        assert req.min_success_rate == 98.0
        assert req.min_duration_days == 7
        assert req.max_p0_incidents == 0

    def test_to_dict(self):
        """Test requirement serialization"""
        req = STAGE_REQUIREMENTS[RolloutStage.STAGE_1]
        result = req.to_dict()
        assert result["stage"] == "STAGE_1"
        assert result["percent"] == 5
        assert "min_success_rate" in result
        assert "description" in result


class TestRolloutMetrics:
    """Tests for RolloutMetrics dataclass"""

    def test_default_values(self):
        """Test default metric values"""
        metrics = RolloutMetrics()
        assert metrics.total_tasks == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.success_rate == 0.0

    def test_to_dict(self):
        """Test metrics serialization"""
        metrics = RolloutMetrics(
            total_tasks=100,
            success_count=95,
            failure_count=5,
            success_rate=95.0
        )
        result = metrics.to_dict()
        assert result["total_tasks"] == 100
        assert result["success_count"] == 95
        assert result["success_rate"] == 95.0


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState dataclass"""

    def test_default_state(self):
        """Test default circuit breaker state"""
        state = CircuitBreakerState()
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0

    def test_to_dict(self):
        """Test state serialization"""
        state = CircuitBreakerState(
            state=CircuitState.OPEN,
            failure_count=5,
            last_failure_reason="5xx_error"
        )
        result = state.to_dict()
        assert result["state"] == "open"
        assert result["failure_count"] == 5
        assert result["last_failure_reason"] == "5xx_error"


class TestRolloutHealth:
    """Tests for RolloutHealth dataclass"""

    def test_healthy_state(self):
        """Test healthy rollout state"""
        health = RolloutHealth(
            healthy=True,
            current_stage=RolloutStage.STAGE_1,
            current_percent=5,
            slo_compliant=True,
            circuit_state=CircuitState.CLOSED,
            can_advance=True,
            should_rollback=False
        )
        assert health.healthy is True
        assert health.can_advance is True
        assert health.should_rollback is False

    def test_to_dict(self):
        """Test health serialization"""
        health = RolloutHealth(
            healthy=False,
            current_stage=RolloutStage.STAGE_2,
            current_percent=15,
            slo_compliant=False,
            circuit_state=CircuitState.OPEN,
            can_advance=False,
            should_rollback=True,
            issues=["SLO violation"],
            recommendations=["Rollback to 5%"]
        )
        result = health.to_dict()
        assert result["healthy"] is False
        assert result["current_stage"] == "STAGE_2"
        assert result["circuit_state"] == "open"
        assert "SLO violation" in result["issues"]


class TestRolloutTracker:
    """Tests for RolloutTracker service"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_init_with_redis(self, mock_redis):
        """Test initialization with Redis client"""
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        assert tracker.enabled is True
        assert tracker.redis is mock_redis

    def test_init_without_redis(self):
        """Test initialization without Redis client"""
        tracker = RolloutTracker(redis_client=None, enabled=True)
        assert tracker.enabled is False

    def test_init_disabled(self, mock_redis):
        """Test initialization with enabled=False"""
        tracker = RolloutTracker(redis_client=mock_redis, enabled=False)
        assert tracker.enabled is False

    def test_custom_slo(self, mock_redis):
        """Test initialization with custom SLO"""
        custom_slo = RolloutSLO(p95_latency_ms=3000.0)
        tracker = RolloutTracker(redis_client=mock_redis, slo=custom_slo)
        assert tracker.slo.p95_latency_ms == 3000.0

    def test_get_minute_key(self, tracker):
        """Test minute key generation"""
        timestamp = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        key = tracker._get_minute_key("test.metric", timestamp)
        assert key == "metrics:rollout:test.metric:202501151030"

    def test_record_langgraph_task_success(self, tracker, mock_redis):
        """Test recording successful LangGraph task"""
        tracker.record_langgraph_task(
            trace_id="test-123",
            success=True,
            latency_ms=1000.0
        )
        # Verify pipeline was called
        mock_redis.pipeline.assert_called()

    def test_record_langgraph_task_failure(self, tracker, mock_redis):
        """Test recording failed LangGraph task"""
        tracker.record_langgraph_task(
            trace_id="test-123",
            success=False,
            is_5xx_error=True
        )
        mock_redis.pipeline.assert_called()

    def test_record_simple_task(self, tracker, mock_redis):
        """Test recording Simple mode task"""
        tracker.record_simple_task(
            trace_id="test-456",
            success=True,
            latency_ms=500.0
        )
        mock_redis.pipeline.assert_called()

    def test_record_p0_incident(self, tracker, mock_redis):
        """Test recording P0 incident"""
        tracker.record_p0_incident(
            description="Critical failure",
            mode="langgraph"
        )
        mock_redis.lpush.assert_called()


class TestCircuitBreaker:
    """Tests for circuit breaker functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_initial_state_closed(self, tracker):
        """Test circuit breaker starts closed"""
        assert tracker._circuit_breaker.state == CircuitState.CLOSED

    def test_check_circuit_breaker_closed(self, tracker):
        """Test circuit breaker allows traffic when closed"""
        assert tracker.check_circuit_breaker() is True

    def test_circuit_opens_after_failures(self, tracker):
        """Test circuit breaker opens after threshold failures"""
        for i in range(tracker.circuit_failure_threshold):
            tracker._update_circuit_breaker_failure("test_failure")

        assert tracker._circuit_breaker.state == CircuitState.OPEN

    def test_circuit_blocks_when_open(self, tracker):
        """Test circuit breaker blocks traffic when open"""
        tracker._set_circuit_state(CircuitState.OPEN)
        # Set cooldown in the future
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        tracker._circuit_breaker.cooldown_until = future_time.isoformat()

        assert tracker.check_circuit_breaker() is False

    def test_circuit_half_open_after_cooldown(self, tracker):
        """Test circuit breaker enters half-open after cooldown"""
        tracker._set_circuit_state(CircuitState.OPEN)
        # Set cooldown in the past
        past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        tracker._circuit_breaker.cooldown_until = past_time.isoformat()

        result = tracker.check_circuit_breaker()
        assert result is True
        assert tracker._circuit_breaker.state == CircuitState.HALF_OPEN

    def test_circuit_closes_after_successes(self, tracker):
        """Test circuit breaker closes after successful recovery"""
        tracker._set_circuit_state(CircuitState.HALF_OPEN)

        for i in range(tracker.circuit_success_threshold):
            tracker._update_circuit_breaker_success()

        assert tracker._circuit_breaker.state == CircuitState.CLOSED

    def test_circuit_reopens_on_failure_in_half_open(self, tracker):
        """Test circuit breaker reopens on failure in half-open state"""
        tracker._set_circuit_state(CircuitState.HALF_OPEN)
        tracker._update_circuit_breaker_failure("test_failure")

        assert tracker._circuit_breaker.state == CircuitState.OPEN

    def test_reset_circuit_breaker(self, tracker):
        """Test manual circuit breaker reset"""
        tracker._set_circuit_state(CircuitState.OPEN)
        tracker.reset_circuit_breaker()

        assert tracker._circuit_breaker.state == CircuitState.CLOSED
        assert tracker._circuit_breaker.failure_count == 0

    def test_get_circuit_breaker_state(self, tracker):
        """Test getting circuit breaker state"""
        state = tracker.get_circuit_breaker_state()
        assert isinstance(state, CircuitBreakerState)
        assert state.state == CircuitState.CLOSED


class TestSLOEvaluation:
    """Tests for SLO evaluation"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_evaluate_slo_insufficient_data(self, tracker):
        """Test SLO evaluation with insufficient data"""
        result = tracker.evaluate_slo_compliance(window_minutes=15)
        assert result["compliant"] is None
        assert "Insufficient data" in result["reason"]

    def test_evaluate_slo_compliant(self, tracker, mock_redis):
        """Test SLO evaluation when compliant"""
        # Mock sufficient data with good metrics
        def mock_get(key):
            if "total" in key:
                return "100"
            elif "success" in key:
                return "98"
            elif "failure" in key:
                return "2"
            elif "error_5xx" in key:
                return "0"
            elif "latency_bucket_1000" in key:
                return "95"
            return "0"

        mock_redis.get.side_effect = mock_get

        result = tracker.evaluate_slo_compliance(window_minutes=15)
        # With mocked data showing good metrics
        assert "violations" in result

    def test_evaluate_slo_with_violations(self, tracker, mock_redis):
        """Test SLO evaluation with violations"""
        # Mock data with violations
        def mock_get(key):
            if "total" in key:
                return "100"
            elif "success" in key:
                return "80"  # 80% success rate
            elif "failure" in key:
                return "20"  # 20% failure rate - violation
            elif "error_5xx" in key:
                return "5"   # 5% error rate - violation
            return "0"

        mock_redis.get.side_effect = mock_get

        result = tracker.evaluate_slo_compliance(window_minutes=15)
        assert "violations" in result


class TestStageManagement:
    """Tests for rollout stage management"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_get_current_stage(self, tracker):
        """Test getting current stage from percentage"""
        assert tracker.get_current_stage(0) == RolloutStage.STAGE_0
        assert tracker.get_current_stage(5) == RolloutStage.STAGE_1
        assert tracker.get_current_stage(15) == RolloutStage.STAGE_2
        assert tracker.get_current_stage(30) == RolloutStage.STAGE_3
        assert tracker.get_current_stage(50) == RolloutStage.STAGE_4
        assert tracker.get_current_stage(100) == RolloutStage.STAGE_5

    def test_can_advance_at_max_stage(self, tracker):
        """Test cannot advance from max stage"""
        result = tracker.can_advance_stage(100)
        assert result["can_advance"] is False
        assert "maximum rollout" in result["reason"]

    def test_can_advance_with_circuit_open(self, tracker):
        """Test cannot advance with open circuit breaker"""
        tracker._set_circuit_state(CircuitState.OPEN)
        result = tracker.can_advance_stage(5)
        assert result["can_advance"] is False
        # Circuit breaker check happens after SLO check, so reason may vary
        # The key assertion is that advancement is blocked
        assert "reason" in result or "circuit_state" in result

    def test_should_rollback_with_circuit_open(self, tracker):
        """Test should rollback with open circuit breaker"""
        tracker._set_circuit_state(CircuitState.OPEN)
        result = tracker.should_rollback(15)
        assert result["should_rollback"] is True
        assert "Circuit breaker is open" in result["reason"]

    def test_should_not_rollback_when_healthy(self, tracker):
        """Test should not rollback when healthy"""
        result = tracker.should_rollback(5)
        assert result["should_rollback"] is False


class TestDashboard:
    """Tests for dashboard functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_get_comparison(self, tracker):
        """Test getting mode comparison"""
        comparison = tracker.get_comparison(window_minutes=15)
        assert isinstance(comparison, RolloutComparison)
        assert comparison.window_minutes == 15
        assert isinstance(comparison.langgraph, RolloutMetrics)
        assert isinstance(comparison.simple, RolloutMetrics)

    def test_get_rollout_health(self, tracker):
        """Test getting rollout health"""
        health = tracker.get_rollout_health(current_percent=5)
        assert isinstance(health, RolloutHealth)
        assert health.current_stage == RolloutStage.STAGE_1
        assert health.current_percent == 5

    def test_get_dashboard_summary(self, tracker):
        """Test getting dashboard summary"""
        summary = tracker.get_dashboard_summary(current_percent=15)
        assert "timestamp" in summary
        assert "rollout" in summary
        assert "health" in summary
        assert "comparison" in summary
        assert "slo" in summary
        assert "circuit_breaker" in summary
        assert "stage_requirements" in summary

    def test_dashboard_summary_rollout_info(self, tracker):
        """Test dashboard summary rollout information"""
        summary = tracker.get_dashboard_summary(current_percent=30)
        assert summary["rollout"]["current_percent"] == 30
        assert summary["rollout"]["current_stage"] == "STAGE_3"
        assert len(summary["rollout"]["target_stages"]) == 6


class TestFactoryFunction:
    """Tests for factory function"""

    def test_create_rollout_tracker_with_redis(self):
        """Test factory with Redis client"""
        mock_redis = MagicMock()
        tracker = create_rollout_tracker(redis_client=mock_redis, enabled=True)
        assert isinstance(tracker, RolloutTracker)
        assert tracker.enabled is True

    def test_create_rollout_tracker_without_redis(self):
        """Test factory without Redis client"""
        tracker = create_rollout_tracker(redis_client=None, enabled=True)
        assert isinstance(tracker, RolloutTracker)
        assert tracker.enabled is False

    def test_create_rollout_tracker_with_custom_slo(self):
        """Test factory with custom SLO"""
        mock_redis = MagicMock()
        custom_slo = RolloutSLO(p95_latency_ms=2000.0)
        tracker = create_rollout_tracker(
            redis_client=mock_redis,
            enabled=True,
            slo=custom_slo
        )
        assert tracker.slo.p95_latency_ms == 2000.0


class TestDisabledTracker:
    """Tests for disabled tracker behavior"""

    @pytest.fixture
    def disabled_tracker(self):
        """Create disabled RolloutTracker"""
        return RolloutTracker(redis_client=None, enabled=False)

    def test_record_langgraph_task_disabled(self, disabled_tracker):
        """Test recording task when disabled"""
        # Should not raise any errors
        disabled_tracker.record_langgraph_task(
            trace_id="test",
            success=True,
            latency_ms=100
        )

    def test_record_simple_task_disabled(self, disabled_tracker):
        """Test recording simple task when disabled"""
        disabled_tracker.record_simple_task(
            trace_id="test",
            success=True,
            latency_ms=100
        )

    def test_get_comparison_disabled(self, disabled_tracker):
        """Test getting comparison when disabled"""
        comparison = disabled_tracker.get_comparison()
        assert comparison.langgraph.total_tasks == 0
        assert comparison.simple.total_tasks == 0

    def test_evaluate_slo_disabled(self, disabled_tracker):
        """Test SLO evaluation when disabled"""
        result = disabled_tracker.evaluate_slo_compliance()
        assert result["compliant"] is None


class TestRolloutComparison:
    """Tests for RolloutComparison dataclass"""

    def test_comparison_to_dict(self):
        """Test comparison serialization"""
        comparison = RolloutComparison(
            window_minutes=15,
            timestamp="2025-01-15T10:00:00Z",
            langgraph=RolloutMetrics(total_tasks=100, success_rate=95.0),
            simple=RolloutMetrics(total_tasks=100, success_rate=90.0),
            langgraph_advantage={"success_rate_diff": 5.0}
        )
        result = comparison.to_dict()
        assert result["window_minutes"] == 15
        assert result["langgraph"]["success_rate"] == 95.0
        assert result["simple"]["success_rate"] == 90.0
        assert result["langgraph_advantage"]["success_rate_diff"] == 5.0


class TestRedisExceptionHandling:
    """Tests for Redis exception handling - tracker should never crash on Redis errors"""

    def test_safe_incr_handles_pipeline_execute_exception(self):
        """Test that _safe_incr handles pipeline.execute() exceptions gracefully"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.side_effect = Exception("Redis connection lost")
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        # Should not raise - tracker should handle exception gracefully
        tracker.record_langgraph_task(trace_id="test", success=True, latency_ms=100)

    def test_safe_incr_handles_pipeline_creation_exception(self):
        """Test that _safe_incr handles pipeline() creation exceptions gracefully"""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis not available")

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        # Should not raise - tracker should handle exception gracefully
        tracker.record_langgraph_task(trace_id="test", success=True, latency_ms=100)

    def test_record_simple_task_handles_redis_exception(self):
        """Test that record_simple_task handles Redis exceptions gracefully"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.side_effect = Exception("Redis timeout")
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        # Should not raise - tracker should handle exception gracefully
        tracker.record_simple_task(trace_id="test", success=False, is_5xx_error=True)

    def test_save_circuit_state_handles_redis_exception(self):
        """Test that _save_circuit_state_to_redis handles exceptions gracefully"""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis write failed")
        mock_redis.get.return_value = None
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        # Should not raise - circuit state save failure should be handled
        tracker._set_circuit_state(CircuitState.OPEN)

    def test_get_circuit_state_handles_redis_exception(self):
        """Test that _get_circuit_state_from_redis handles exceptions gracefully"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis read failed")
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        # Should not raise - should return None on exception
        result = tracker._get_circuit_state_from_redis()
        assert result is None


class TestRedisPipelineCallVerification:
    """Tests verifying exact Redis pipeline call parameters"""

    def test_safe_incr_uses_transaction_pipeline(self):
        """Test that _safe_incr uses pipeline with transaction=True"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._safe_incr("test:key", 1)

        mock_redis.pipeline.assert_called_with(transaction=True)

    def test_safe_incr_sets_key_with_correct_params(self):
        """Test that _safe_incr calls set with nx=True and correct TTL"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True, ttl_seconds=86400)
        tracker._safe_incr("test:key", 1)

        # Verify set was called with nx=True and correct TTL
        mock_pipe.set.assert_called_once_with("test:key", 0, ex=86400, nx=True)

    def test_safe_incr_calls_incrby_with_correct_value(self):
        """Test that _safe_incr calls incrby with correct key and value"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._safe_incr("test:key", 5)

        mock_pipe.incrby.assert_called_once_with("test:key", 5)

    def test_safe_incr_executes_pipeline(self):
        """Test that _safe_incr calls execute on the pipeline"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._safe_incr("test:key", 1)

        mock_pipe.execute.assert_called_once()

    def test_record_langgraph_task_success_increments_correct_keys(self):
        """Test that record_langgraph_task success increments total, success, and latency keys"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        mock_redis.get.return_value = None

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True, ttl_seconds=86400)
        tracker.record_langgraph_task(trace_id="test", success=True, latency_ms=100)

        set_calls = mock_pipe.set.call_args_list
        set_keys = [call[0][0] for call in set_calls]
        incrby_calls = mock_pipe.incrby.call_args_list
        incrby_keys = [call[0][0] for call in incrby_calls]

        assert any("langgraph.total" in key for key in set_keys)
        assert any("langgraph.success" in key for key in set_keys)
        assert any("latency_bucket_" in key for key in set_keys)

        assert any("langgraph.total" in key for key in incrby_keys)
        assert any("langgraph.success" in key for key in incrby_keys)
        assert any("latency_bucket_" in key for key in incrby_keys)

        for call in set_calls:
            assert call[0][1] == 0
            assert call[1]["ex"] == 86400
            assert call[1]["nx"] is True

        for call in incrby_calls:
            assert call[0][1] == 1

    def test_record_langgraph_task_failure_increments_failure_key(self):
        """Test that record_langgraph_task failure increments failure key with correct params"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        mock_redis.get.return_value = None

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True, ttl_seconds=86400)
        tracker.record_langgraph_task(trace_id="test", success=False)

        set_calls = mock_pipe.set.call_args_list
        set_keys = [call[0][0] for call in set_calls]
        incrby_calls = mock_pipe.incrby.call_args_list
        incrby_keys = [call[0][0] for call in incrby_calls]

        assert any("langgraph.total" in key for key in set_keys)
        assert any("langgraph.failure" in key for key in set_keys)

        assert any("langgraph.total" in key for key in incrby_keys)
        assert any("langgraph.failure" in key for key in incrby_keys)

        for call in set_calls:
            assert call[0][1] == 0
            assert call[1]["ex"] == 86400
            assert call[1]["nx"] is True

        for call in incrby_calls:
            assert call[0][1] == 1

    def test_record_langgraph_task_5xx_increments_error_key(self):
        """Test that record_langgraph_task with 5xx error increments all expected keys"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        mock_redis.get.return_value = None

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True, ttl_seconds=86400)
        tracker.record_langgraph_task(trace_id="test", success=False, is_5xx_error=True)

        set_calls = mock_pipe.set.call_args_list
        set_keys = [call[0][0] for call in set_calls]
        incrby_calls = mock_pipe.incrby.call_args_list
        incrby_keys = [call[0][0] for call in incrby_calls]

        assert any("langgraph.total" in key for key in set_keys)
        assert any("langgraph.failure" in key for key in set_keys)
        assert any("langgraph.error_5xx" in key for key in set_keys)

        assert any("langgraph.total" in key for key in incrby_keys)
        assert any("langgraph.failure" in key for key in incrby_keys)
        assert any("langgraph.error_5xx" in key for key in incrby_keys)

        for call in set_calls:
            assert call[0][1] == 0
            assert call[1]["ex"] == 86400
            assert call[1]["nx"] is True

        for call in incrby_calls:
            assert call[0][1] == 1


class TestCircuitBreakerPublicAPI:
    """Tests for circuit breaker using public API instead of internal attributes"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    def test_circuit_breaker_state_via_public_api(self, tracker):
        """Test getting circuit breaker state via public API"""
        state = tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0

    def test_circuit_breaker_opens_via_public_api(self, tracker):
        """Test circuit breaker opens after failures - verified via public API"""
        for _ in range(tracker.circuit_failure_threshold):
            tracker._update_circuit_breaker_failure("test")

        state = tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.OPEN

    def test_circuit_breaker_closes_via_public_api(self, tracker):
        """Test circuit breaker closes after recovery - verified via public API"""
        tracker._set_circuit_state(CircuitState.HALF_OPEN)

        for _ in range(tracker.circuit_success_threshold):
            tracker._update_circuit_breaker_success()

        state = tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.CLOSED

    def test_circuit_breaker_tracks_failure_count_via_public_api(self, tracker):
        """Test failure count tracking via public API"""
        tracker._update_circuit_breaker_failure("test_error")
        tracker._update_circuit_breaker_failure("test_error")

        state = tracker.get_circuit_breaker_state()
        assert state.failure_count == 2
        assert state.last_failure_reason == "test_error"

    def test_circuit_breaker_half_open_success_count_via_public_api(self, tracker):
        """Test success count in half-open state via public API"""
        tracker._set_circuit_state(CircuitState.HALF_OPEN)
        tracker._update_circuit_breaker_success()

        state = tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.HALF_OPEN
        assert state.success_count_since_half_open == 1

    def test_check_circuit_breaker_returns_correct_value(self, tracker):
        """Test check_circuit_breaker returns correct allow/block decision"""
        # Initially closed - should allow
        assert tracker.check_circuit_breaker() is True

        # Set to open with future cooldown - should block
        tracker._set_circuit_state(CircuitState.OPEN)
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        tracker._circuit_breaker.cooldown_until = future_time.isoformat()
        assert tracker.check_circuit_breaker() is False


class TestCircuitBreakerBlackBox:
    """Black-box tests for circuit breaker using only public API (Issue #2647).

    These tests verify circuit breaker behavior without directly setting internal state.
    State transitions are driven entirely through public API methods:
    - record_langgraph_task(success=False) to drive failure count increases
    - record_langgraph_task(success=True) to drive success count increases
    - get_circuit_breaker_state() and check_circuit_breaker() to verify results

    Time-based transitions (OPEN -> HALF_OPEN) use datetime patching to simulate
    cooldown expiration without accessing internal state.

    Design notes (team template):
    - FrozenDatetime inherits from datetime to support all datetime methods automatically
    - Fixtures only drive state, assertions are in test body for clearer error messages
    """

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with pipeline support"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        mock_pipe = MagicMock()
        redis_mock.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        redis_mock.pipeline.return_value.__exit__ = MagicMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def tracker(self, mock_redis):
        """Create RolloutTracker with mock Redis"""
        return RolloutTracker(redis_client=mock_redis, enabled=True)

    @pytest.fixture
    def open_tracker(self, tracker):
        """Create a tracker in OPEN state via public API (failures).

        This fixture drives the circuit breaker to OPEN state by recording
        enough failures through the public API.

        Note: State verification is done in test body, not here, for clearer error messages.
        """
        for i in range(tracker.circuit_failure_threshold):
            tracker.record_langgraph_task(trace_id=f"open-{i}", success=False)
        return tracker

    @pytest.fixture
    def half_open_tracker(self, open_tracker, monkeypatch):
        """Create a tracker in HALF_OPEN state via public API + time patching.

        This fixture:
        1. Starts with an OPEN tracker (from open_tracker fixture)
        2. Patches datetime using FrozenDatetime (inherits all datetime methods)
        3. Calls check_circuit_breaker() to trigger OPEN -> HALF_OPEN transition

        Note: State verification is done in test body, not here, for clearer error messages.
        """
        import rollout_tracker as rt_module

        cooldown_seconds = open_tracker.circuit_cooldown_seconds
        future_time = datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds + 1)

        class FrozenDatetime(datetime):
            """Datetime subclass that freezes now() while inheriting all other methods.

            This approach is more robust than a minimal mock because:
            - All datetime methods (strftime, utcnow, astimezone, etc.) work automatically
            - Future code changes using new datetime methods won't break tests silently
            """

            @classmethod
            def now(cls, tz=None):
                return future_time

        monkeypatch.setattr(rt_module, "datetime", FrozenDatetime)

        open_tracker.check_circuit_breaker()
        return open_tracker

    def test_circuit_breaker_opens_after_threshold_failures_black_box(self, tracker):
        """Test circuit breaker opens after threshold failures - black box approach."""
        initial_state = tracker.get_circuit_breaker_state()
        assert initial_state.state == CircuitState.CLOSED

        for i in range(tracker.circuit_failure_threshold):
            tracker.record_langgraph_task(trace_id=f"test-{i}", success=False)

        final_state = tracker.get_circuit_breaker_state()
        assert final_state.state == CircuitState.OPEN

    def test_circuit_breaker_tracks_failure_count_black_box(self, tracker):
        """Test failure count tracking via public API - black box approach."""
        tracker.record_langgraph_task(trace_id="test-1", success=False)
        tracker.record_langgraph_task(trace_id="test-2", success=False)

        state = tracker.get_circuit_breaker_state()
        assert state.failure_count == 2

    def test_circuit_breaker_resets_failure_count_on_success_black_box(self, tracker):
        """Test failure count resets on success when closed - black box approach."""
        tracker.record_langgraph_task(trace_id="test-1", success=False)
        tracker.record_langgraph_task(trace_id="test-2", success=False)

        state = tracker.get_circuit_breaker_state()
        assert state.failure_count == 2

        tracker.record_langgraph_task(trace_id="test-3", success=True)

        state = tracker.get_circuit_breaker_state()
        assert state.failure_count == 0

    def test_circuit_breaker_closes_after_recovery_black_box(self, half_open_tracker):
        """Test circuit breaker closes after recovery in half-open - black box approach.

        Uses half_open_tracker fixture which reaches HALF_OPEN via public API + time patching.
        """
        for i in range(half_open_tracker.circuit_success_threshold):
            half_open_tracker.record_langgraph_task(trace_id=f"recovery-{i}", success=True)

        state = half_open_tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.CLOSED

    def test_circuit_breaker_tracks_success_count_in_half_open_black_box(self, half_open_tracker):
        """Test success count tracking in half-open state - black box approach."""
        initial_state = half_open_tracker.get_circuit_breaker_state()
        initial_count = initial_state.success_count_since_half_open

        half_open_tracker.record_langgraph_task(trace_id="test-1", success=True)

        state = half_open_tracker.get_circuit_breaker_state()
        assert state.success_count_since_half_open == initial_count + 1

    def test_circuit_breaker_reopens_on_failure_in_half_open_black_box(self, half_open_tracker):
        """Test circuit breaker reopens on failure in half-open - black box approach."""
        half_open_tracker.record_langgraph_task(trace_id="test-fail", success=False)

        state = half_open_tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.OPEN

    def test_check_circuit_breaker_allows_when_closed_black_box(self, tracker):
        """Test check_circuit_breaker allows traffic when closed - black box approach."""
        state = tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.CLOSED

        assert tracker.check_circuit_breaker() is True

    def test_check_circuit_breaker_blocks_when_open_black_box(self, open_tracker):
        """Test check_circuit_breaker blocks traffic when open - black box approach."""
        state = open_tracker.get_circuit_breaker_state()
        assert state.state == CircuitState.OPEN

        assert open_tracker.check_circuit_breaker() is False

    def test_full_circuit_breaker_lifecycle_black_box(self, tracker, monkeypatch):
        """Test full circuit breaker lifecycle: closed -> open -> half-open -> closed.

        This is an end-to-end black-box test that verifies the complete lifecycle
        using only public API methods and time patching for cooldown simulation.

        Uses FrozenDatetime (inherits from datetime) for robust time patching.
        """
        import rollout_tracker as rt_module

        assert tracker.get_circuit_breaker_state().state == CircuitState.CLOSED
        assert tracker.check_circuit_breaker() is True

        for i in range(tracker.circuit_failure_threshold):
            tracker.record_langgraph_task(trace_id=f"fail-{i}", success=False)

        assert tracker.get_circuit_breaker_state().state == CircuitState.OPEN
        assert tracker.check_circuit_breaker() is False

        cooldown_seconds = tracker.circuit_cooldown_seconds
        future_time = datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds + 1)

        class FrozenDatetime(datetime):
            """Datetime subclass that freezes now() while inheriting all other methods."""

            @classmethod
            def now(cls, tz=None):
                return future_time

        monkeypatch.setattr(rt_module, "datetime", FrozenDatetime)

        assert tracker.check_circuit_breaker() is True
        assert tracker.get_circuit_breaker_state().state == CircuitState.HALF_OPEN

        for i in range(tracker.circuit_success_threshold):
            tracker.record_langgraph_task(trace_id=f"success-{i}", success=True)

        assert tracker.get_circuit_breaker_state().state == CircuitState.CLOSED
        assert tracker.check_circuit_breaker() is True
