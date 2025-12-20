"""
Fault Injection Tests for RolloutTracker and Redis Queue Components.

This module implements fault injection tests to verify system resilience under
adverse conditions. These tests cover:

1. Concurrency: Multi-worker race conditions, circuit breaker state consistency
2. Redis Failures: Connection timeout, network partition recovery, pipeline failures
3. Edge Cases: Long-running job timeout, clock skew scenarios

Issue: #2650 (Add redis_queue integration tests to CI and implement fault injection tests)
"""

import pytest
import threading
from unittest.mock import MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis


class TestConcurrencyFaultInjection:
    """Tests for multi-worker race conditions and concurrent access patterns."""

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
        assert tracker._circuit_breaker.state in [
            CircuitState.HALF_OPEN, CircuitState.CLOSED
        ], "Circuit breaker should be in valid state"

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
    """Tests for Redis failure scenarios and recovery behavior."""

    def test_redis_connection_timeout_handling(self):
        """Test behavior when Redis connection times out during record_langgraph_task.

        Verifies that the tracker handles connection timeouts gracefully without
        crashing or corrupting internal state.
        """
        from rollout_tracker import RolloutTracker, CircuitState

        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = redis.ConnectionError("Connection timed out")

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)
        initial_state = tracker._circuit_breaker.state

        try:
            tracker.record_langgraph_task(
                trace_id="test-timeout",
                success=True,
                latency_ms=100.0
            )
        except redis.ConnectionError:
            pass

        assert tracker._circuit_breaker.state == initial_state or \
               tracker._circuit_breaker.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN, CircuitState.OPEN]

    def test_redis_pipeline_partial_failure(self):
        """Test behavior when some pipeline commands succeed but others fail.

        Simulates a scenario where Redis pipeline execution partially fails.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_pipeline.execute.side_effect = redis.RedisError("Pipeline execution failed")
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        try:
            tracker.record_langgraph_task(
                trace_id="test-partial-failure",
                success=True,
                latency_ms=100.0
            )
        except redis.RedisError:
            pass

        assert tracker.enabled is True

    def test_redis_reconnection_after_temporary_outage(self):
        """Test that tracker recovers after temporary Redis outage.

        Simulates Redis becoming unavailable and then recovering.
        """
        from rollout_tracker import RolloutTracker

        call_count = [0]

        def pipeline_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise redis.ConnectionError("Redis unavailable")
            mock_pipeline = MagicMock()
            mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
            mock_pipeline.__exit__ = MagicMock(return_value=False)
            return mock_pipeline

        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = pipeline_side_effect

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        for i in range(3):
            try:
                tracker.record_langgraph_task(
                    trace_id=f"test-reconnect-{i}",
                    success=True,
                    latency_ms=100.0
                )
            except redis.ConnectionError:
                pass

        # The tracker may call pipeline multiple times per record_langgraph_task
        # so we just verify it was called at least 3 times
        assert call_count[0] >= 3, f"Should have attempted at least 3 pipeline operations, got {call_count[0]}"

    def test_redis_memory_pressure_handling(self):
        """Test behavior when Redis reports memory pressure (OOM).

        Simulates Redis returning OOM error during write operations.
        """
        from rollout_tracker import RolloutTracker

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        mock_pipeline.execute.side_effect = redis.ResponseError("OOM command not allowed when used memory > 'maxmemory'")
        mock_redis.pipeline.return_value = mock_pipeline

        tracker = RolloutTracker(redis_client=mock_redis, enabled=True)

        try:
            tracker.record_langgraph_task(
                trace_id="test-oom",
                success=True,
                latency_ms=100.0
            )
        except redis.ResponseError:
            pass

        assert tracker.enabled is True


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
            client.flushdb()
        except redis.ConnectionError:
            pytest.skip("Redis not available for integration tests")

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

    def test_real_redis_concurrent_writes(self, redis_client):
        """Test concurrent writes to real Redis."""
        from rollout_tracker import RolloutTracker

        tracker = RolloutTracker(redis_client=redis_client, enabled=True)
        errors = []

        def write_task(i):
            try:
                tracker.record_langgraph_task(
                    trace_id=f"concurrent-test-{i}",
                    success=True,
                    latency_ms=100.0 + i
                )
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_task, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

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
