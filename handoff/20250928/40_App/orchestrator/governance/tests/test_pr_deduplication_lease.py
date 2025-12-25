"""
Tests for PR Deduplication Lease Mechanism (Issue #2910)

Blueprint Alignment:
- Memory v2 (Layer 1): Atomic short-term reservation
- Safety Governor v2: Prevents race condition duplicates
- Telemetry v2: Structured logging for lease decisions

Test Cases:
1. Lease acquire - first worker gets lease
2. Lease acquire - second worker blocked
3. Lease release - clears the lease
4. Lease complete - marks as done with PR info
5. Lease acquire after complete - blocked with existing PR URL
6. Redis unavailable - fail-open behavior
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from governance.pr_deduplication import (
    acquire_pr_lease,
    release_pr_lease,
    complete_pr_lease,
    generate_dedup_key,
    generate_deterministic_branch,
    _record_fail_open_event,
    get_fail_open_count,
    check_fail_open_alert_threshold,
    FAIL_OPEN_METRIC_NAME,
    FAIL_OPEN_ALERT_THRESHOLD,
    FAIL_OPEN_ALERT_WINDOW_MINUTES,
)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis = MagicMock()
    redis.set.return_value = True
    redis.get.return_value = None
    redis.delete.return_value = 1
    redis.ttl.return_value = 300
    return redis


class TestLeaseAcquire:
    """Test lease acquisition behavior"""

    def test_first_worker_acquires_lease(self, mock_redis):
        """First worker should successfully acquire the lease"""
        mock_redis.set.return_value = True  # SETNX succeeds

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = acquire_pr_lease(
                dedup_key="test-dedup-key",
                worker_id="worker-1",
                trace_id="trace-123"
            )

        assert result.acquired is True
        assert result.reason == "Lease acquired successfully"
        mock_redis.set.assert_called_once()

    def test_second_worker_blocked(self, mock_redis):
        """Second worker should be blocked when lease is held"""
        mock_redis.set.return_value = False  # SETNX fails (key exists)
        mock_redis.get.return_value = json.dumps({
            "worker_id": "worker-1",
            "trace_id": "trace-111",
            "status": "in_progress"
        })
        mock_redis.ttl.return_value = 250

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = acquire_pr_lease(
                dedup_key="test-dedup-key",
                worker_id="worker-2",
                trace_id="trace-456"
            )

        assert result.acquired is False
        assert result.holder == "worker-1"
        assert "worker-1" in result.reason

    def test_redis_unavailable_fail_open(self):
        """When Redis is unavailable, should fail-open (allow PR creation)"""
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            result = acquire_pr_lease(
                dedup_key="test-dedup-key",
                worker_id="worker-1",
                trace_id="trace-123"
            )

        assert result.acquired is True
        assert "unavailable" in result.reason.lower()


class TestLeaseRelease:
    """Test lease release behavior"""

    def test_release_clears_lease(self, mock_redis):
        """Release should delete the lease key"""
        mock_redis.delete.return_value = 1

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = release_pr_lease(
                dedup_key="test-dedup-key",
                trace_id="trace-123"
            )

        assert result is True
        mock_redis.delete.assert_called_once()

    def test_release_returns_false_when_redis_unavailable(self):
        """Release should return False when Redis is unavailable"""
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            result = release_pr_lease(
                dedup_key="test-dedup-key",
                trace_id="trace-123"
            )

        assert result is False


class TestLeaseComplete:
    """Test lease completion behavior"""

    def test_complete_marks_lease_done(self, mock_redis):
        """Complete should update lease with PR info and extend TTL"""
        mock_redis.get.return_value = json.dumps({
            "worker_id": "worker-1",
            "trace_id": "trace-123",
            "acquired_at": 1234567890.0,
            "status": "in_progress"
        })

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = complete_pr_lease(
                dedup_key="test-dedup-key",
                trace_id="trace-123",
                pr_url="https://github.com/test/repo/pull/123",
                pr_number=123
            )

        assert result is True
        # Verify set was called with the completed value
        call_args = mock_redis.set.call_args
        completed_data = json.loads(call_args[0][1])
        assert completed_data["status"] == "done"
        assert completed_data["pr_url"] == "https://github.com/test/repo/pull/123"
        assert completed_data["pr_number"] == 123

    def test_acquire_after_complete_returns_existing_pr(self, mock_redis):
        """Acquiring lease after completion should return existing PR URL"""
        mock_redis.set.return_value = False  # SETNX fails
        mock_redis.get.return_value = json.dumps({
            "worker_id": "worker-1",
            "trace_id": "trace-111",
            "status": "done",
            "pr_url": "https://github.com/test/repo/pull/123",
            "pr_number": 123
        })
        mock_redis.ttl.return_value = 3500

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            result = acquire_pr_lease(
                dedup_key="test-dedup-key",
                worker_id="worker-2",
                trace_id="trace-456"
            )

        assert result.acquired is False
        assert result.existing_pr_url == "https://github.com/test/repo/pull/123"
        assert result.existing_pr_number == 123


class TestDedupKeyGeneration:
    """Test deterministic key generation"""

    def test_same_input_same_key(self):
        """Same inputs should produce same dedup key"""
        key1 = generate_dedup_key(
            repo="owner/repo",
            doc_file_path="docs/test.md",
            source_pr_number=None,
            event_action=None
        )
        key2 = generate_dedup_key(
            repo="owner/repo",
            doc_file_path="docs/test.md",
            source_pr_number=None,
            event_action=None
        )

        assert key1 == key2

    def test_different_input_different_key(self):
        """Different inputs should produce different dedup keys"""
        key1 = generate_dedup_key(
            repo="owner/repo",
            doc_file_path="docs/test1.md",
            source_pr_number=None,
            event_action=None
        )
        key2 = generate_dedup_key(
            repo="owner/repo",
            doc_file_path="docs/test2.md",
            source_pr_number=None,
            event_action=None
        )

        assert key1 != key2


class TestDeterministicBranch:
    """Test deterministic branch name generation"""

    def test_same_input_same_branch(self):
        """Same inputs should produce same branch name"""
        branch1 = generate_deterministic_branch(
            repo="owner/repo",
            doc_file_path="docs/generated/test-topic.md",
            source_pr_number=None
        )
        branch2 = generate_deterministic_branch(
            repo="owner/repo",
            doc_file_path="docs/generated/test-topic.md",
            source_pr_number=None
        )

        assert branch1 == branch2

    def test_branch_format(self):
        """Branch name should follow expected format"""
        branch = generate_deterministic_branch(
            repo="owner/repo",
            doc_file_path="docs/generated/test-topic.md",
            source_pr_number=None
        )

        assert branch.startswith("orchestrator/docs-")
        assert len(branch) > 20  # Should have hash suffix


class TestFailOpenMonitoring:
    """Test fail-open monitoring functionality (Issue #2919)"""

    def test_record_fail_open_event_adds_sentry_breadcrumb(self):
        """Fail-open event should add Sentry breadcrumb"""
        mock_sentry = MagicMock()

        with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
            _record_fail_open_event(
                trace_id="trace-123",
                dedup_key="test-dedup-key",
                reason="redis_unavailable",
                error=None,
                redis_client=None
            )

        mock_sentry.add_breadcrumb.assert_called_once()
        call_kwargs = mock_sentry.add_breadcrumb.call_args[1]
        assert call_kwargs["category"] == "pr_dedup"
        assert "fail-open" in call_kwargs["message"]
        assert call_kwargs["data"]["trace_id"] == "trace-123"
        assert call_kwargs["data"]["fail_open"] is True

    def test_record_fail_open_event_increments_metric(self, mock_redis):
        """Fail-open event should increment metrics counter with INCR+EXPIRE pattern"""
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="test-dedup-key",
            reason="connection_error",
            error="Connection refused",
            redis_client=mock_redis
        )

        mock_redis.pipeline.assert_called_once()
        mock_pipeline.incr.assert_called_once()
        mock_pipeline.expire.assert_called_once()  # Verify TTL is refreshed

    def test_redis_unavailable_triggers_fail_open_monitoring(self):
        """Redis unavailable should trigger fail-open monitoring"""
        mock_sentry = MagicMock()

        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
                result = acquire_pr_lease(
                    dedup_key="test-dedup-key",
                    worker_id="worker-1",
                    trace_id="trace-123"
                )

        assert result.acquired is True
        assert "unavailable" in result.reason.lower()
        mock_sentry.add_breadcrumb.assert_called()

    def test_connection_error_triggers_fail_open_monitoring(self, mock_redis):
        """Connection error should trigger fail-open monitoring"""
        mock_redis.set.side_effect = Exception("Connection refused")
        mock_sentry = MagicMock()

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
                result = acquire_pr_lease(
                    dedup_key="test-dedup-key",
                    worker_id="worker-1",
                    trace_id="trace-123"
                )

        assert result.acquired is True
        assert "fail-open" in result.reason.lower()

    def test_get_fail_open_count_returns_zero_when_redis_unavailable(self):
        """get_fail_open_count should return 0 when Redis unavailable"""
        with patch('governance.pr_deduplication._get_redis_client', return_value=None):
            count = get_fail_open_count()

        assert count == 0

    def test_get_fail_open_count_sums_minute_buckets(self, mock_redis):
        """get_fail_open_count should sum values from minute buckets"""
        mock_redis.get.side_effect = [b"2", b"3", b"1", None, None]

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            count = get_fail_open_count(window_minutes=5)

        assert count == 6  # 2 + 3 + 1

    def test_check_fail_open_alert_threshold_returns_false_below_threshold(self, mock_redis):
        """Alert threshold check should return False when below threshold"""
        mock_redis.get.return_value = b"1"

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            exceeded = check_fail_open_alert_threshold()

        assert exceeded is False

    def test_check_fail_open_alert_threshold_returns_true_above_threshold(self, mock_redis):
        """Alert threshold check should return True when above threshold"""
        mock_redis.get.return_value = b"10"  # 10 per minute * 5 minutes = 50 > 5

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            exceeded = check_fail_open_alert_threshold()

        assert exceeded is True

    def test_check_fail_open_alert_threshold_sends_sentry_alert(self, mock_redis):
        """Alert threshold exceeded should send Sentry alert"""
        mock_redis.get.return_value = b"10"
        mock_sentry = MagicMock()

        with patch('governance.pr_deduplication._get_redis_client', return_value=mock_redis):
            with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
                check_fail_open_alert_threshold()

        mock_sentry.capture_message.assert_called_once()
        call_args = mock_sentry.capture_message.call_args
        assert "threshold exceeded" in call_args[0][0].lower()
        assert call_args[1]["level"] == "error"

    def test_fail_open_constants_are_configured(self):
        """Fail-open monitoring constants should be properly configured"""
        assert FAIL_OPEN_METRIC_NAME == "pr_lease.fail_open"
        assert FAIL_OPEN_ALERT_THRESHOLD == 5
        assert FAIL_OPEN_ALERT_WINDOW_MINUTES == 5

    def test_record_fail_open_event_graceful_when_sentry_and_redis_unavailable(self):
        """Fail-open monitoring should fail gracefully when both Sentry and Redis unavailable"""
        # Simulate Sentry import failure by not mocking it
        # and Redis unavailable by passing None

        # This should not raise any exception
        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="test-dedup-key",
            reason="redis_unavailable",
            error=None,
            redis_client=None  # Redis unavailable
        )
        # Test passes if no exception is raised

    def test_record_fail_open_event_graceful_when_sentry_raises_exception(self):
        """Fail-open monitoring should continue when Sentry add_breadcrumb raises"""
        mock_sentry = MagicMock()
        mock_sentry.add_breadcrumb.side_effect = Exception("Sentry error")

        with patch.dict('sys.modules', {'sentry_sdk': mock_sentry}):
            # This should not raise any exception
            _record_fail_open_event(
                trace_id="trace-123",
                dedup_key="test-dedup-key",
                reason="connection_error",
                error="Connection refused",
                redis_client=None
            )
        # Test passes if no exception is raised

    def test_record_fail_open_event_graceful_when_redis_pipeline_fails(self, mock_redis):
        """Fail-open monitoring should continue when Redis pipeline fails"""
        mock_redis.pipeline.side_effect = Exception("Redis pipeline error")

        # This should not raise any exception
        _record_fail_open_event(
            trace_id="trace-123",
            dedup_key="test-dedup-key",
            reason="connection_error",
            error="Connection refused",
            redis_client=mock_redis
        )
        # Test passes if no exception is raised
