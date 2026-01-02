"""
Tests for Governance Heartbeat Handler (EPIC I-1)

Blueprint Alignment:
- Section 4.3: Model Governance Framework v2
- EPIC I-1: Operationalization (Heartbeat + Distributed Lock)

Test Cases:
1. Lock acquisition - only one worker acquires lock
2. Lock expiry - next cycle can take over after expiry
3. Error isolation - governance errors don't affect worker
4. Health snapshot - correct structure with evaluator_node_id
5. Non-blocking behavior - skip if lock held
"""
import json
import pytest
import time
from unittest.mock import MagicMock, patch

from governance.heartbeat_handler import (
    run_governance_cycle,
    get_health_snapshot,
    _acquire_governance_lock,
    _release_governance_lock,
    GovernanceHeartbeatResult,
    GOVERNANCE_LOCK_KEY,
    GOVERNANCE_LOCK_TTL,
    GOVERNANCE_SNAPSHOT_KEY,
    GOVERNANCE_SNAPSHOT_TTL,
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = MagicMock()
    redis.set.return_value = True
    redis.get.return_value = None
    redis.delete.return_value = 1
    redis.setex.return_value = True
    # Mock register_script for Lua script-based lock release
    # Returns a callable that returns 1 (success) by default
    mock_script = MagicMock(return_value=1)
    redis.register_script.return_value = mock_script
    return redis


class TestLockAcquisition:
    """Test distributed lock acquisition behavior"""

    def test_first_worker_acquires_lock(self, mock_redis):
        """First worker should successfully acquire the lock"""
        mock_redis.set.return_value = True  # SET NX succeeds

        lock_result = _acquire_governance_lock(
            redis_client=mock_redis,
            evaluator_node_id="worker-1",
        )

        assert lock_result is not None
        lock_token, lock_value = lock_result
        assert len(lock_token) == 32  # UUID hex length
        assert lock_value is not None  # JSON string with token and metadata
        mock_redis.set.assert_called_once()

        # Verify SET was called with nx=True and ex=TTL
        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs["nx"] is True
        assert call_kwargs["ex"] == GOVERNANCE_LOCK_TTL

    def test_second_worker_blocked(self, mock_redis):
        """Second worker should be blocked when lock is held"""
        mock_redis.set.return_value = False  # SET NX fails (key exists)

        lock_result = _acquire_governance_lock(
            redis_client=mock_redis,
            evaluator_node_id="worker-2",
        )

        assert lock_result is None

    def test_lock_acquisition_non_blocking(self, mock_redis):
        """Lock acquisition should be non-blocking (no wait/retry)"""
        mock_redis.set.return_value = False

        start_time = time.monotonic()
        lock_result = _acquire_governance_lock(
            redis_client=mock_redis,
            evaluator_node_id="worker-1",
        )
        elapsed = time.monotonic() - start_time

        assert lock_result is None
        assert elapsed < 0.1  # Should return immediately

    def test_lock_acquisition_handles_redis_error(self, mock_redis):
        """Lock acquisition should handle Redis errors gracefully"""
        mock_redis.set.side_effect = Exception("Redis connection error")

        lock_result = _acquire_governance_lock(
            redis_client=mock_redis,
            evaluator_node_id="worker-1",
        )

        assert lock_result is None


class TestLockRelease:
    """Test distributed lock release behavior using atomic Lua script"""

    def test_release_own_lock(self, mock_redis):
        """Should release lock when lock_value matches (Lua script returns 1)"""
        lock_value = json.dumps({
            "token": "abc123",
            "evaluator_node_id": "worker-1",
            "acquired_at": "2025-01-01T00:00:00+00:00",
        })

        # Mock the Lua script execution - returns 1 when lock is released
        mock_script = MagicMock(return_value=1)
        mock_redis.register_script.return_value = mock_script

        result = _release_governance_lock(
            redis_client=mock_redis,
            lock_value=lock_value,
            evaluator_node_id="worker-1",
        )

        assert result is True
        mock_redis.register_script.assert_called_once()
        mock_script.assert_called_once_with(keys=[GOVERNANCE_LOCK_KEY], args=[lock_value])

    def test_release_expired_lock(self, mock_redis):
        """Should return False when lock already expired (Lua script returns 0)"""
        lock_value = json.dumps({
            "token": "abc123",
            "evaluator_node_id": "worker-1",
            "acquired_at": "2025-01-01T00:00:00+00:00",
        })

        # Mock the Lua script execution - returns 0 when lock doesn't exist or doesn't match
        mock_script = MagicMock(return_value=0)
        mock_redis.register_script.return_value = mock_script

        result = _release_governance_lock(
            redis_client=mock_redis,
            lock_value=lock_value,
            evaluator_node_id="worker-1",
        )

        # Returns False because Lua script returns 0 (lock value didn't match)
        assert result is False

    def test_release_different_token(self, mock_redis):
        """Should not release lock when lock_value doesn't match (Lua script returns 0)"""
        lock_value = json.dumps({
            "token": "my-token",
            "evaluator_node_id": "worker-1",
            "acquired_at": "2025-01-01T00:00:00+00:00",
        })

        # Mock the Lua script execution - returns 0 when value doesn't match
        mock_script = MagicMock(return_value=0)
        mock_redis.register_script.return_value = mock_script

        result = _release_governance_lock(
            redis_client=mock_redis,
            lock_value=lock_value,
            evaluator_node_id="worker-1",
        )

        assert result is False

    def test_release_handles_redis_error(self, mock_redis):
        """Should handle Redis errors gracefully during release"""
        lock_value = json.dumps({
            "token": "abc123",
            "evaluator_node_id": "worker-1",
            "acquired_at": "2025-01-01T00:00:00+00:00",
        })

        # Mock the Lua script to raise an exception
        mock_script = MagicMock(side_effect=Exception("Redis error"))
        mock_redis.register_script.return_value = mock_script

        result = _release_governance_lock(
            redis_client=mock_redis,
            lock_value=lock_value,
            evaluator_node_id="worker-1",
        )

        assert result is False


class TestLockExpiry:
    """Test lock expiry and takeover behavior"""

    def test_lock_expiry_allows_new_acquisition(self, mock_redis):
        """After lock expires, next worker should acquire"""
        # First call: lock exists (blocked)
        # Second call: lock expired (acquire succeeds)
        mock_redis.set.side_effect = [False, True]

        # First attempt - blocked
        result1 = _acquire_governance_lock(mock_redis, "worker-1")
        assert result1 is None

        # Second attempt - succeeds (simulating after expiry)
        result2 = _acquire_governance_lock(mock_redis, "worker-2")
        assert result2 is not None
        token2, lock_value2 = result2
        assert len(token2) == 32  # UUID hex length


class TestGovernanceCycle:
    """Test full governance cycle execution"""

    def test_cycle_executes_with_lock(self, mock_redis):
        """Governance cycle should execute when lock is acquired"""
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis.get.return_value = None  # For lock release check

        with patch('governance.health_alerter.get_health_alert_service') as mock_alert:
            with patch('governance.degradation_advisor.get_degradation_advisor') as mock_advisor:
                mock_alert.return_value = None  # Alerting disabled
                mock_advisor.return_value = None  # Advisory disabled

                result = run_governance_cycle(
                    redis_client=mock_redis,
                    evaluator_node_id="worker-1",
                    heartbeat_id="heartbeat-1",
                    worker_id="worker-1",
                )

        assert result.executed is True
        assert result.lock_acquired is True
        assert result.error is None

    def test_cycle_skipped_when_lock_held(self, mock_redis):
        """Governance cycle should skip when lock is held by another worker"""
        mock_redis.set.return_value = False  # Lock not acquired

        result = run_governance_cycle(
            redis_client=mock_redis,
            evaluator_node_id="worker-1",
            heartbeat_id="heartbeat-1",
            worker_id="worker-1",
        )

        assert result.executed is False
        assert result.lock_acquired is False
        assert result.skipped_reason == "lock_held_by_another_worker"

    def test_cycle_skipped_when_redis_unavailable(self):
        """Governance cycle should skip when Redis is unavailable"""
        result = run_governance_cycle(
            redis_client=None,
            evaluator_node_id="worker-1",
            heartbeat_id="heartbeat-1",
            worker_id="worker-1",
        )

        assert result.executed is False
        assert result.lock_acquired is False
        assert result.skipped_reason == "redis_unavailable"


class TestErrorIsolation:
    """Test that governance errors don't affect worker"""

    def test_health_alerter_error_isolated(self, mock_redis):
        """Health alerter errors should not propagate"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None

        with patch('governance.health_alerter.get_health_alert_service') as mock_alert:
            mock_alert.side_effect = Exception("Health alerter crashed")
            with patch('governance.degradation_advisor.get_degradation_advisor') as mock_advisor:
                mock_advisor.return_value = None

                # Should not raise exception
                result = run_governance_cycle(
                    redis_client=mock_redis,
                    evaluator_node_id="worker-1",
                    heartbeat_id="heartbeat-1",
                    worker_id="worker-1",
                )

        # Cycle still completes (with partial results)
        assert result.lock_acquired is True

    def test_degradation_advisor_error_isolated(self, mock_redis):
        """Degradation advisor errors should not propagate"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None

        with patch('governance.health_alerter.get_health_alert_service') as mock_alert:
            mock_alert.return_value = None
            with patch('governance.degradation_advisor.get_degradation_advisor') as mock_advisor:
                mock_advisor.side_effect = Exception("Advisor crashed")

                # Should not raise exception
                result = run_governance_cycle(
                    redis_client=mock_redis,
                    evaluator_node_id="worker-1",
                    heartbeat_id="heartbeat-1",
                    worker_id="worker-1",
                )

        assert result.lock_acquired is True

    def test_snapshot_update_error_isolated(self, mock_redis):
        """Snapshot update errors should not propagate"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = Exception("Snapshot update failed")

        with patch('governance.health_alerter.get_health_alert_service') as mock_alert:
            with patch('governance.degradation_advisor.get_degradation_advisor') as mock_advisor:
                mock_alert.return_value = None
                mock_advisor.return_value = None

                # Should not raise exception
                result = run_governance_cycle(
                    redis_client=mock_redis,
                    evaluator_node_id="worker-1",
                    heartbeat_id="heartbeat-1",
                    worker_id="worker-1",
                )

        assert result.lock_acquired is True


class TestHealthSnapshot:
    """Test health snapshot structure and retrieval"""

    def test_snapshot_includes_required_fields(self, mock_redis):
        """Snapshot should include last_updated_at and evaluator_node_id"""
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None

        with patch('governance.health_alerter.get_health_alert_service') as mock_alert:
            with patch('governance.degradation_advisor.get_degradation_advisor') as mock_advisor:
                mock_alert.return_value = None
                mock_advisor.return_value = None

                run_governance_cycle(
                    redis_client=mock_redis,
                    evaluator_node_id="worker-1",
                    heartbeat_id="heartbeat-1",
                    worker_id="worker-1",
                )

        # Verify setex was called with snapshot
        mock_redis.setex.assert_called()
        call_args = mock_redis.setex.call_args[0]

        assert call_args[0] == GOVERNANCE_SNAPSHOT_KEY
        assert call_args[1] == GOVERNANCE_SNAPSHOT_TTL

        snapshot = json.loads(call_args[2])
        assert "last_updated_at" in snapshot
        assert "evaluator_node_id" in snapshot
        assert snapshot["evaluator_node_id"] == "worker-1"
        assert "version" in snapshot

    def test_get_health_snapshot_returns_data(self, mock_redis):
        """get_health_snapshot should return parsed snapshot"""
        snapshot_data = {
            "version": "1.0.0",
            "last_updated_at": "2025-01-01T00:00:00+00:00",
            "evaluator_node_id": "worker-1",
            "health_check": {"providers_checked": ["openai"]},
            "degradation_advisory": {"advisories_logged": 0},
        }
        mock_redis.get.return_value = json.dumps(snapshot_data)

        result = get_health_snapshot(mock_redis)

        assert result is not None
        assert result["evaluator_node_id"] == "worker-1"
        assert result["version"] == "1.0.0"

    def test_get_health_snapshot_returns_none_when_missing(self, mock_redis):
        """get_health_snapshot should return None when no snapshot exists"""
        mock_redis.get.return_value = None

        result = get_health_snapshot(mock_redis)

        assert result is None

    def test_get_health_snapshot_returns_none_when_redis_unavailable(self):
        """get_health_snapshot should return None when Redis unavailable"""
        result = get_health_snapshot(None)

        assert result is None


class TestGovernanceHeartbeatResult:
    """Test GovernanceHeartbeatResult data class"""

    def test_result_to_dict(self):
        """Result should serialize to dict correctly"""
        result = GovernanceHeartbeatResult(
            executed=True,
            lock_acquired=True,
            duration_seconds=1.5,
            alerts_sent=2,
            advisories_logged=1,
        )

        d = result.to_dict()

        assert d["executed"] is True
        assert d["lock_acquired"] is True
        assert d["duration_seconds"] == 1.5
        assert d["alerts_sent"] == 2
        assert d["advisories_logged"] == 1
        assert d["error"] is None
        assert d["skipped_reason"] is None

    def test_result_with_error(self):
        """Result should include error when present"""
        result = GovernanceHeartbeatResult(
            executed=False,
            lock_acquired=True,
            error="Something went wrong",
        )

        d = result.to_dict()

        assert d["executed"] is False
        assert d["error"] == "Something went wrong"


class TestWorkerIntegration:
    """Test integration with worker heartbeat"""

    def test_run_governance_heartbeat_isolated(self):
        """_run_governance_heartbeat should be fully isolated"""
        # Import the function from worker
        from redis_queue.worker import _run_governance_heartbeat

        # Mock redis to be None (simulating unavailable)
        with patch('redis_queue.worker.redis', None):
            # Should not raise any exception
            _run_governance_heartbeat()

    def test_run_governance_heartbeat_handles_import_error(self):
        """_run_governance_heartbeat should handle import errors"""
        from redis_queue.worker import _run_governance_heartbeat

        with patch('redis_queue.worker.redis', MagicMock()):
            with patch.dict('sys.modules', {'governance.heartbeat_handler': None}):
                # Force ImportError by removing the module
                import sys
                original = sys.modules.get('governance.heartbeat_handler')
                sys.modules['governance.heartbeat_handler'] = None

                try:
                    # Should not raise any exception
                    _run_governance_heartbeat()
                finally:
                    if original:
                        sys.modules['governance.heartbeat_handler'] = original
