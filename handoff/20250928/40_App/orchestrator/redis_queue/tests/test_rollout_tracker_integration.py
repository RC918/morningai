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

    # NOTE: test_rollout_tracker_has_record_simple_task was removed in Issue #2651 after LangGraph 100% rollout (2025-12-15)
    # TODO: Remove this comment after 2026-01-15 (one release cycle)

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

    # NOTE: test_record_simple_task_can_be_called_without_error was removed in Issue #2651 after LangGraph 100% rollout
    # NOTE: test_record_simple_task_failure_can_be_called_without_error was removed in Issue #2651 after LangGraph 100% rollout


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


class TestRolloutTrackerEnabledWithRedis:
    """Tests for RolloutTracker with enabled=True and mock Redis (Issue #2641).

    These tests verify that when enabled=True and a Redis client is provided,
    the tracker correctly writes metrics to Redis.
    """

    def _create_mock_redis(self):
        """Create a mock Redis client with pipeline support."""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline
        return mock_redis, mock_pipeline

    def test_record_langgraph_task_success_writes_to_redis(self):
        """Test that record_langgraph_task writes to Redis when enabled."""
        from rollout_tracker import RolloutTracker

        mock_redis, mock_pipeline = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-trace-001",
            success=True,
            latency_ms=150.0
        )

        mock_redis.pipeline.assert_called()
        mock_pipeline.set.assert_called()
        mock_pipeline.incrby.assert_called()
        mock_pipeline.execute.assert_called()

    def test_record_langgraph_task_failure_writes_to_redis(self):
        """Test that record_langgraph_task failure writes to Redis when enabled."""
        from rollout_tracker import RolloutTracker

        mock_redis, mock_pipeline = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-trace-002",
            success=False,
            latency_ms=500.0,
            is_5xx_error=True
        )

        mock_redis.pipeline.assert_called()
        mock_pipeline.execute.assert_called()

    # NOTE: test_record_simple_task_success_writes_to_redis was removed in Issue #2651 after LangGraph 100% rollout
    # NOTE: test_record_simple_task_failure_writes_to_redis was removed in Issue #2651 after LangGraph 100% rollout

    def test_enabled_tracker_with_redis_client_is_enabled(self):
        """Test that tracker is enabled when redis_client is provided and enabled=True."""
        from rollout_tracker import RolloutTracker

        mock_redis, _ = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        assert tracker.enabled is True

    def test_record_langgraph_task_success_updates_circuit_breaker(self):
        """Test that record_langgraph_task updates circuit breaker on success when enabled."""
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis, _ = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN
        tracker._circuit_breaker.success_count_since_half_open = 2

        tracker.record_langgraph_task(
            trace_id="test-trace-005",
            success=True,
            latency_ms=150.0
        )

        assert tracker._circuit_breaker.success_count_since_half_open == 3

    def test_record_langgraph_task_failure_updates_circuit_breaker(self):
        """Test that record_langgraph_task updates circuit breaker on failure when enabled."""
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis, _ = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._circuit_breaker.state = CircuitState.CLOSED
        tracker._circuit_breaker.failure_count = 0

        tracker.record_langgraph_task(
            trace_id="test-trace-006",
            success=False,
            latency_ms=500.0
        )

        assert tracker._circuit_breaker.failure_count == 1

    def test_redis_key_format_contains_metric_name(self):
        """Test that Redis keys are generated with correct format."""
        from rollout_tracker import RolloutTracker

        mock_redis, mock_pipeline = self._create_mock_redis()
        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-trace-007",
            success=True,
            latency_ms=100.0
        )

        set_calls = mock_pipeline.set.call_args_list
        assert len(set_calls) > 0
        first_key = set_calls[0][0][0]
        assert "metrics:rollout" in first_key
        assert "langgraph" in first_key
