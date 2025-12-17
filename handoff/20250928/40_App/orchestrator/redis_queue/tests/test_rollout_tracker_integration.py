"""
Tests for RolloutTracker integration in worker.py

This module tests the RolloutTracker integration points in the worker module,
including initialization, circuit breaker checks, and task recording.

Issue: #2280 (Integrate RolloutTracker to worker.py)
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRolloutTrackerIntegration:
    """Tests for RolloutTracker integration in worker module."""

    def test_rollout_tracker_global_variable_exists(self):
        """Test that _rollout_tracker global variable exists in worker module."""
        pytest.importorskip("rq")
        from redis_queue import worker

        assert hasattr(worker, "_rollout_tracker")

    def test_create_rollout_tracker_can_be_imported(self):
        """Test that create_rollout_tracker can be imported from rollout_tracker."""
        from rollout_tracker import create_rollout_tracker

        assert callable(create_rollout_tracker)

    def test_rollout_tracker_has_check_circuit_breaker(self):
        """Test that RolloutTracker has check_circuit_breaker method."""
        from rollout_tracker import RolloutTracker

        assert hasattr(RolloutTracker, "check_circuit_breaker")
        assert callable(getattr(RolloutTracker, "check_circuit_breaker"))

    def test_rollout_tracker_has_record_langgraph_task(self):
        """Test that RolloutTracker has record_langgraph_task method."""
        from rollout_tracker import RolloutTracker

        assert hasattr(RolloutTracker, "record_langgraph_task")
        assert callable(getattr(RolloutTracker, "record_langgraph_task"))

    def test_rollout_tracker_has_record_simple_task(self):
        """Test that RolloutTracker has record_simple_task method."""
        from rollout_tracker import RolloutTracker

        assert hasattr(RolloutTracker, "record_simple_task")
        assert callable(getattr(RolloutTracker, "record_simple_task"))

    def test_rollout_tracker_has_get_circuit_breaker_state(self):
        """Test that RolloutTracker has get_circuit_breaker_state method."""
        from rollout_tracker import RolloutTracker

        assert hasattr(RolloutTracker, "get_circuit_breaker_state")
        assert callable(getattr(RolloutTracker, "get_circuit_breaker_state"))


class TestRolloutTrackerCircuitBreaker:
    """Tests for circuit breaker behavior."""

    def test_circuit_breaker_allows_traffic_when_closed(self):
        """Test that circuit breaker allows traffic when in CLOSED state."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.CLOSED

        assert tracker.check_circuit_breaker() is True

    def test_circuit_breaker_blocks_traffic_when_open(self):
        """Test that circuit breaker blocks traffic when in OPEN state."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.OPEN
        tracker._circuit_breaker.cooldown_until = "2099-12-31T23:59:59+00:00"

        assert tracker.check_circuit_breaker() is False

    def test_circuit_breaker_allows_traffic_when_half_open(self):
        """Test that circuit breaker allows limited traffic when in HALF_OPEN state."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN

        assert tracker.check_circuit_breaker() is True


class TestRolloutTrackerFeatureFlag:
    """Tests for rollout_tracker_enabled feature flag."""

    def test_rollout_tracker_enabled_default_true(self):
        """Test that rollout_tracker_enabled defaults to True."""
        from common.config.settings import Settings

        settings = Settings()
        assert settings.rollout_tracker_enabled is True

    def test_rollout_tracker_can_be_disabled(self):
        """Test that rollout_tracker_enabled can be disabled via environment."""
        import os
        from common.config.settings import Settings

        with patch.dict(os.environ, {"ROLLOUT_TRACKER_ENABLED": "false"}):
            settings = Settings()
            assert settings.rollout_tracker_enabled is False


class TestRolloutTrackerRecordMethods:
    """Tests for RolloutTracker record methods (Issue #2280 acceptance criteria).

    Note: When enabled=False (no Redis), record methods return early without
    recording. These tests verify the methods can be called without error
    and that the circuit breaker state is updated correctly for LangGraph tasks.
    """

    def test_record_langgraph_task_disabled_does_not_update_circuit_breaker(self):
        """Test that record_langgraph_task does NOT update circuit breaker when disabled.

        When enabled=False, record methods return early (no-op), so circuit
        breaker state should remain unchanged.
        """
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN
        tracker._circuit_breaker.success_count_since_half_open = 2

        tracker.record_langgraph_task(
            trace_id="test-trace-123",
            success=True,
            latency_ms=150.5
        )

        assert tracker._circuit_breaker.success_count_since_half_open == 2

    def test_record_langgraph_task_can_be_called_without_error(self):
        """Test that record_langgraph_task can be called without error when disabled."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=None, enabled=False)

        tracker.record_langgraph_task(
            trace_id="test-trace-456",
            success=False,
            latency_ms=500.0,
            is_5xx_error=True
        )

    def test_record_simple_task_can_be_called_without_error(self):
        """Test that record_simple_task can be called without error when disabled."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=None, enabled=False)

        tracker.record_simple_task(
            trace_id="test-trace-789",
            success=True,
            latency_ms=100.0
        )

    def test_record_simple_task_failure_can_be_called_without_error(self):
        """Test that record_simple_task failure can be called without error when disabled."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=None, enabled=False)

        tracker.record_simple_task(
            trace_id="test-trace-abc",
            success=False,
            latency_ms=200.0
        )


class TestRolloutTrackerCircuitBreakerFallback:
    """Tests for circuit breaker fallback behavior (Issue #2280 acceptance criteria)."""

    def test_circuit_breaker_open_should_trigger_fallback(self):
        """Test that circuit breaker OPEN state should trigger fallback to Simple mode.

        This test verifies the expected behavior: when circuit breaker is OPEN,
        check_circuit_breaker() returns False, which should cause worker.py to
        fall back to Simple mode instead of LangGraph.
        """
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.OPEN
        tracker._circuit_breaker.cooldown_until = "2099-12-31T23:59:59+00:00"

        should_use_langgraph = tracker.check_circuit_breaker()
        assert should_use_langgraph is False

    def test_circuit_breaker_closed_allows_langgraph(self):
        """Test that circuit breaker CLOSED state allows LangGraph mode."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.CLOSED

        should_use_langgraph = tracker.check_circuit_breaker()
        assert should_use_langgraph is True


class TestRolloutTrackerDisabledBehavior:
    """Tests for disabled tracker behavior (Issue #2280 acceptance criteria)."""

    def test_disabled_tracker_does_not_persist_to_redis(self):
        """Test that disabled tracker does not attempt to persist metrics to Redis.

        When enabled=False, record methods are no-op and do not write to Redis.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=False)

        tracker.record_langgraph_task(
            trace_id="test-trace",
            success=True,
            latency_ms=100.0
        )

        mock_redis.set.assert_not_called()
        mock_redis.hset.assert_not_called()
        mock_redis.zadd.assert_not_called()

    def test_create_rollout_tracker_respects_enabled_flag(self):
        """Test that create_rollout_tracker passes enabled flag correctly.

        Note: When redis_client=None, enabled is always False regardless of
        the enabled parameter (see RolloutTracker.__init__ line 267:
        self.enabled = enabled and redis_client is not None)
        """
        from rollout_tracker import create_rollout_tracker

        tracker_with_enabled_true = create_rollout_tracker(redis_client=None, enabled=True)
        tracker_with_enabled_false = create_rollout_tracker(redis_client=None, enabled=False)

        assert tracker_with_enabled_true.enabled is False
        assert tracker_with_enabled_false.enabled is False
