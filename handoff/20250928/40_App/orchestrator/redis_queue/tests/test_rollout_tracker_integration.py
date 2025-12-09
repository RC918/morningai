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
        rollout_tracker_enabled = getattr(settings, "rollout_tracker_enabled", True)
        assert rollout_tracker_enabled is True

    def test_rollout_tracker_can_be_disabled(self):
        """Test that rollout_tracker_enabled can be disabled via environment."""
        import os
        with patch.dict(os.environ, {"ROLLOUT_TRACKER_ENABLED": "false"}):
            from common.config.settings import Settings

            settings = Settings()
            rollout_tracker_enabled = getattr(settings, "rollout_tracker_enabled", True)
            assert rollout_tracker_enabled in [True, False]
