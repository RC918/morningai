"""
Fault Injection Tests for RolloutTracker and Redis Queue Components.

This module implements fault injection tests to verify system resilience under
adverse conditions. These tests cover:

1. Concurrency: Multi-worker race conditions, circuit breaker state consistency
2. Redis Failures: Connection timeout, network partition recovery, pipeline failures
3. Edge Cases: Long-running job timeout, clock skew scenarios

Issue: #2650 (Add redis_queue integration tests to CI and implement fault injection tests)

Test Markers:
- @pytest.mark.concurrency: Tests involving multi-threading (potential flakiness)
- @pytest.mark.integration: Tests requiring real Redis connection
"""

import pytest
import threading
import logging
from unittest.mock import MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis


class TestConcurrencyFaultInjection:
    """Tests for multi-worker race conditions and concurrent access patterns.

    Note: These tests use threading and may be sensitive to CI environment
    resource constraints. Marked with @pytest.mark.concurrency for monitoring.
    """

    @pytest.mark.concurrency
    def test_concurrent_record_langgraph_task_calls(self):
        """Test that concurrent record_langgraph_task calls don't corrupt state.

        Simulates multiple workers recording tasks simultaneously.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        errors = []
        call_count = [0]
        lock = threading.Lock()

        def record_task(trace_id: str):
            try:
                tracker.record_langgraph_task(
                    trace_id=trace_id,
                    success=True,
                    latency_ms=100.0
                )
                with lock:
                    call_count[0] += 1
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(record_task, f"trace-{i}")
                for i in range(50)
            ]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors during concurrent execution: {errors}"
        assert call_count[0] == 50, f"Expected 50 calls, got {call_count[0]}"
        # Verify pipeline was called for each task
        assert mock_redis.pipeline.call_count >= 50

    @pytest.mark.concurrency
    def test_concurrent_circuit_breaker_state_transitions(self):
        """Test circuit breaker state consistency under concurrent access.

        Verifies that circuit breaker state transitions are atomic and consistent
        when multiple threads attempt to modify state simultaneously.
        """
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN
        tracker._circuit_breaker.success_count_since_half_open = 0

        errors = []

        def record_success():
            try:
                tracker.record_langgraph_task(
                    trace_id=f"trace-{threading.current_thread().name}",
                    success=True,
                    latency_ms=50.0
                )
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=record_success) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent state transitions: {errors}"
        # Circuit breaker should be in a valid state (HALF_OPEN or transitioned to CLOSED)
        assert tracker._circuit_breaker.state in [
            CircuitState.HALF_OPEN, CircuitState.CLOSED
        ], f"Invalid circuit breaker state: {tracker._circuit_breaker.state}"

    @pytest.mark.concurrency
    def test_concurrent_check_circuit_breaker_reads(self):
        """Test that concurrent check_circuit_breaker reads are thread-safe."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.CLOSED

        results = []
        lock = threading.Lock()

        def check_breaker():
            result = tracker.check_circuit_breaker()
            with lock:
                results.append(result)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(check_breaker) for _ in range(100)]
            for future in as_completed(futures):
                future.result()

        assert len(results) == 100
        assert all(r is True for r in results), "All reads should return True for CLOSED state"


class TestRedisFailureFaultInjection:
    """Tests for Redis failure scenarios and recovery behavior.

    RolloutTracker handles Redis errors internally (logs warning, continues).
    These tests verify graceful degradation without crashing.
    """

    def test_redis_connection_timeout_handling(self, caplog):
        """Test behavior when Redis connection times out during record_langgraph_task.

        Verifies: Tracker logs warning, doesn't crash, state remains valid.
        """
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = redis.ConnectionError("Connection timed out")

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        with caplog.at_level(logging.WARNING):
            # Should not raise - RolloutTracker handles Redis errors internally
            tracker.record_langgraph_task(
                trace_id="test-timeout",
                success=True,
                latency_ms=100.0
            )

        # Verify warning was logged
        assert any("Failed to" in record.message for record in caplog.records), \
            "Expected warning log for Redis failure"
        # State should remain valid
        assert tracker._circuit_breaker.state in [
            CircuitState.CLOSED, CircuitState.HALF_OPEN, CircuitState.OPEN
        ]
        # Tracker should still be enabled
        assert tracker.enabled is True

    def test_redis_pipeline_partial_failure(self, caplog):
        """Test behavior when pipeline execution fails.

        Simulates a scenario where Redis pipeline execution fails.
        Verifies: Tracker logs warning, remains functional.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_pipeline.execute.side_effect = redis.RedisError("Pipeline execution failed")
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        with caplog.at_level(logging.WARNING):
            tracker.record_langgraph_task(
                trace_id="test-partial-failure",
                success=True,
                latency_ms=100.0
            )

        # Tracker should remain enabled and functional
        assert tracker.enabled is True
        # Pipeline should have been called
        mock_redis.pipeline.assert_called()

    def test_redis_reconnection_after_temporary_outage(self, caplog):
        """Test that tracker recovers after temporary Redis outage.

        Simulates Redis becoming unavailable and then recovering.
        Verifies: First calls fail gracefully, later calls succeed.
        """
        from rollout_tracker import RolloutTracker

        call_count = [0]
        success_count = [0]

        def pipeline_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise redis.ConnectionError("Redis unavailable")
            mock_pipeline = MagicMock()
            mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
            mock_pipeline.__exit__ = MagicMock(return_value=False)
            success_count[0] += 1
            return mock_pipeline

        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = pipeline_side_effect

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        with caplog.at_level(logging.WARNING):
            for i in range(3):
                tracker.record_langgraph_task(
                    trace_id=f"test-reconnect-{i}",
                    success=True,
                    latency_ms=100.0
                )

        # Verify pipeline was called multiple times
        assert call_count[0] >= 3, f"Expected at least 3 pipeline calls, got {call_count[0]}"
        # Verify at least one success after recovery
        assert success_count[0] >= 1, "Expected at least one successful pipeline after recovery"

    def test_redis_memory_pressure_handling(self, caplog):
        """Test behavior when Redis reports memory pressure (OOM).

        Simulates Redis returning OOM error during write operations.
        Verifies: Tracker logs warning, remains functional.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_pipeline.execute.side_effect = redis.ResponseError(
            "OOM command not allowed when used memory > 'maxmemory'"
        )
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        with caplog.at_level(logging.WARNING):
            tracker.record_langgraph_task(
                trace_id="test-oom",
                success=True,
                latency_ms=100.0
            )

        # Tracker should remain enabled
        assert tracker.enabled is True
        # Pipeline should have been called
        mock_redis.pipeline.assert_called()


class TestEdgeCaseFaultInjection:
    """Tests for edge cases and unusual conditions."""

    def test_long_running_task_timeout_behavior(self):
        """Test behavior with extremely long latency values.

        Verifies that the tracker handles edge case latency values correctly.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-long-running",
            success=True,
            latency_ms=3600000.0
        )

        mock_pipeline.execute.assert_called()

    def test_zero_latency_handling(self):
        """Test behavior with zero latency value."""
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-zero-latency",
            success=True,
            latency_ms=0.0
        )

        mock_pipeline.execute.assert_called()

    def test_negative_latency_handling(self):
        """Test behavior with negative latency value (clock skew scenario)."""
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="test-negative-latency",
            success=True,
            latency_ms=-100.0
        )

        mock_pipeline.execute.assert_called()

    def test_empty_trace_id_handling(self):
        """Test behavior with empty trace_id."""
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="",
            success=True,
            latency_ms=100.0
        )

        mock_pipeline.execute.assert_called()

    def test_very_long_trace_id_handling(self):
        """Test behavior with extremely long trace_id."""
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        long_trace_id = "trace-" + "x" * 10000
        tracker.record_langgraph_task(
            trace_id=long_trace_id,
            success=True,
            latency_ms=100.0
        )

        mock_pipeline.execute.assert_called()

    def test_unicode_trace_id_handling(self):
        """Test behavior with unicode characters in trace_id."""
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        tracker.record_langgraph_task(
            trace_id="trace-測試-🚀-émoji",
            success=True,
            latency_ms=100.0
        )

        mock_pipeline.execute.assert_called()


class TestCircuitBreakerFaultInjection:
    """Tests for circuit breaker behavior under fault conditions."""

    def test_circuit_breaker_opens_after_consecutive_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        tracker._circuit_breaker.state = CircuitState.CLOSED
        tracker._circuit_breaker.failure_count = 0
        tracker._circuit_breaker.failure_threshold = 5

        for i in range(10):
            tracker.record_langgraph_task(
                trace_id=f"test-failure-{i}",
                success=False,
                latency_ms=500.0,
                is_5xx_error=True
            )

        assert tracker._circuit_breaker.failure_count >= 5 or \
               tracker._circuit_breaker.state == CircuitState.OPEN

    def test_circuit_breaker_half_open_allows_probe_request(self):
        """Test that HALF_OPEN state allows probe requests."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN

        result = tracker.check_circuit_breaker()

        assert result is True, "HALF_OPEN should allow probe requests"

    def test_circuit_breaker_cooldown_expiry(self):
        """Test circuit breaker behavior when cooldown expires."""
        from rollout_tracker import RolloutTracker, CircuitState
        from datetime import datetime, timezone, timedelta

        tracker = RolloutTracker(redis_client=None, enabled=False)
        tracker._circuit_breaker.state = CircuitState.OPEN

        past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        tracker._circuit_breaker.cooldown_until = past_time

        result = tracker.check_circuit_breaker()

        assert result is True or tracker._circuit_breaker.state == CircuitState.HALF_OPEN


class TestRealRedisIntegration:
    """Integration tests that require a real Redis connection.

    These tests are skipped if Redis is not available.
    Marked with @pytest.mark.integration for selective execution.
    """

    @pytest.fixture
    def redis_client(self):
        """Create a real Redis client for integration tests."""
        import os
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            client = redis.from_url(redis_url)
            client.ping()
            yield client
            # Clean up test keys only (safer than flushdb)
            for key in client.keys("metrics:rollout:*"):
                client.delete(key)
        except redis.ConnectionError:
            pytest.skip("Redis not available for integration tests")

    @pytest.mark.integration
    def test_real_redis_record_and_retrieve(self, redis_client):
        """Test recording and retrieving metrics with real Redis."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=redis_client, enabled=True)

        tracker.record_langgraph_task(
            trace_id="integration-test-001",
            success=True,
            latency_ms=150.0
        )

        keys = redis_client.keys("metrics:rollout:*")
        assert len(keys) > 0, "Should have created Redis keys"

    @pytest.mark.integration
    @pytest.mark.concurrency
    def test_real_redis_concurrent_writes(self, redis_client):
        """Test concurrent writes to real Redis."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=redis_client, enabled=True)
        errors = []
        success_count = [0]
        lock = threading.Lock()

        def write_task(i):
            try:
                tracker.record_langgraph_task(
                    trace_id=f"concurrent-test-{i}",
                    success=True,
                    latency_ms=100.0 + i
                )
                with lock:
                    success_count[0] += 1
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_task, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
        assert success_count[0] == 50, f"Expected 50 successful writes, got {success_count[0]}"

    @pytest.mark.integration
    def test_real_redis_circuit_breaker_persistence(self, redis_client):
        """Test circuit breaker state persistence with real Redis."""
        from rollout_tracker import RolloutTracker, CircuitState

        tracker = RolloutTracker(redis_client=redis_client, enabled=True)

        for i in range(3):
            tracker.record_langgraph_task(
                trace_id=f"persistence-test-{i}",
                success=True,
                latency_ms=100.0
            )

        state = tracker.get_circuit_breaker_state()
        # get_circuit_breaker_state returns a CircuitBreakerState object
        assert hasattr(state, "state"), "Should have state attribute"
        assert state.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN, CircuitState.OPEN]
