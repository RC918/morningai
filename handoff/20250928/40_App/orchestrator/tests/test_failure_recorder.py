"""Tests for failure_recorder module (Phase 5 PR-1)"""
import sys
import os
import json
from unittest.mock import MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from failure_recorder import (  # noqa: E402
    FailureRecord,
    FailureRecorder,
    ReplayResult,
    get_failure_recorder,
    create_failure_recorder,
    FAILURE_KEY_PREFIX,
    FAILURE_LIST_KEY,
    FAILURE_TTL_SECONDS,
)


class TestFailureRecord:
    """Tests for FailureRecord dataclass"""

    def test_create_failure_record_minimal(self):
        """Test creating a failure record with minimal required fields"""
        record = FailureRecord(
            trace_id="test-trace-123",
            goal="Test goal",
            error_type="test_error"
        )

        assert record.trace_id == "test-trace-123"
        assert record.goal == "Test goal"
        assert record.error_type == "test_error"
        assert record.id is not None
        assert record.status == "error"
        assert record.fixer_retries == 0
        assert record.env == "production"
        assert record.pipeline == "5-agent-advisory"

    def test_create_failure_record_full(self):
        """Test creating a failure record with all fields"""
        record = FailureRecord(
            trace_id="test-trace-456",
            goal="Full test goal",
            error_type="ci_failure",
            id="custom-id-789",
            task_type="code_generation",
            error_message="CI check failed",
            fixer_retries=3,
            merge_decision="rejected",
            pr_url="https://github.com/test/repo/pull/123",
            status="error",
            created_at="2025-01-01T00:00:00",
            env="staging",
            pipeline="test-pipeline",
            metadata={"key": "value"}
        )

        assert record.trace_id == "test-trace-456"
        assert record.goal == "Full test goal"
        assert record.error_type == "ci_failure"
        assert record.id == "custom-id-789"
        assert record.task_type == "code_generation"
        assert record.error_message == "CI check failed"
        assert record.fixer_retries == 3
        assert record.merge_decision == "rejected"
        assert record.pr_url == "https://github.com/test/repo/pull/123"
        assert record.status == "error"
        assert record.created_at == "2025-01-01T00:00:00"
        assert record.env == "staging"
        assert record.pipeline == "test-pipeline"
        assert record.metadata == {"key": "value"}

    def test_failure_record_auto_generated_id(self):
        """Test that failure records get auto-generated UUIDs"""
        record1 = FailureRecord(trace_id="t1", goal="g1", error_type="e1")
        record2 = FailureRecord(trace_id="t2", goal="g2", error_type="e2")

        assert record1.id != record2.id
        assert len(record1.id) == 36

    def test_failure_record_auto_generated_timestamp(self):
        """Test that failure records get auto-generated timestamps"""
        record = FailureRecord(trace_id="t1", goal="g1", error_type="e1")

        assert record.created_at is not None
        datetime.fromisoformat(record.created_at)


class TestFailureRecorder:
    """Tests for FailureRecorder class"""

    def test_recorder_disabled_without_redis(self):
        """Test that recorder is disabled when no Redis client is provided"""
        recorder = FailureRecorder(redis_client=None, enabled=True)

        assert recorder.enabled is False

    def test_recorder_disabled_explicitly(self):
        """Test that recorder can be explicitly disabled"""
        mock_redis = MagicMock()
        recorder = FailureRecorder(redis_client=mock_redis, enabled=False)

        assert recorder.enabled is False

    def test_recorder_enabled_with_redis(self):
        """Test that recorder is enabled with Redis client"""
        mock_redis = MagicMock()
        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        assert recorder.enabled is True
        assert recorder.redis == mock_redis

    def test_record_failure_when_disabled(self):
        """Test that record_failure returns None when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)
        record = FailureRecord(trace_id="t1", goal="g1", error_type="e1")

        result = recorder.record_failure(record)

        assert result is None

    def test_record_failure_success(self):
        """Test successful failure recording"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)
        record = FailureRecord(
            trace_id="test-trace",
            goal="Test goal",
            error_type="test_error",
            id="test-id"
        )

        result = recorder.record_failure(record)

        assert result == "test-id"
        mock_redis.pipeline.assert_called_once()
        mock_pipeline.set.assert_called_once()
        mock_pipeline.lpush.assert_called_once()
        mock_pipeline.execute.assert_called_once()

    def test_record_failure_from_state(self):
        """Test recording failure from orchestrator state"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        state = {
            "trace_id": "state-trace-123",
            "goal": "State goal",
            "task_type": "code_review",
            "retry_count": 2,
            "merge_decision": "pending",
            "pr_url": "https://github.com/test/pr/1"
        }

        result = recorder.record_failure_from_state(
            state=state,
            error_type="workflow_error",
            error_message="Test error message"
        )

        assert result is not None
        mock_pipeline.set.assert_called_once()

    def test_record_failure_from_state_when_disabled(self):
        """Test that record_failure_from_state returns None when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.record_failure_from_state(
            state={"trace_id": "t1", "goal": "g1"},
            error_type="test_error"
        )

        assert result is None

    def test_get_failure_success(self):
        """Test getting a failure record by ID"""
        mock_redis = MagicMock()
        test_record = FailureRecord(
            id="test-id", trace_id="t1", goal="g1", error_type="e1",
            created_at="2025-01-01T00:00:00", env="production", pipeline="test"
        )
        mock_redis.get.return_value = json.dumps(test_record.to_dict()).encode('utf-8')

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.get_failure("test-id")

        assert result is not None
        assert result.id == "test-id"
        assert result.trace_id == "t1"
        mock_redis.get.assert_called_once()

    def test_get_failure_not_found(self):
        """Test getting a non-existent failure record"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.get_failure("non-existent-id")

        assert result is None

    def test_get_failure_when_disabled(self):
        """Test that get_failure returns None when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.get_failure("test-id")

        assert result is None

    def test_list_failures_success(self):
        """Test listing failure records"""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = [b"id1", b"id2"]
        record1 = FailureRecord(
            id="id1", trace_id="t1", goal="g1", error_type="e1",
            created_at="2025-01-01T00:00:00", env="production", pipeline="test"
        )
        record2 = FailureRecord(
            id="id2", trace_id="t2", goal="g2", error_type="e2",
            created_at="2025-01-01T00:00:00", env="production", pipeline="test"
        )
        mock_redis.get.side_effect = [
            json.dumps(record1.to_dict()).encode('utf-8'),
            json.dumps(record2.to_dict()).encode('utf-8')
        ]

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.list_failures(limit=10, offset=0)

        assert len(result) == 2
        assert result[0].id == "id1"
        assert result[1].id == "id2"

    def test_list_failures_with_filter(self):
        """Test listing failures with trace_id filter"""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = [b"id1", b"id2"]
        record1 = FailureRecord(
            id="id1", trace_id="target-trace", goal="g1", error_type="e1",
            created_at="2025-01-01T00:00:00", env="production", pipeline="test"
        )
        record2 = FailureRecord(
            id="id2", trace_id="other-trace", goal="g2", error_type="e2",
            created_at="2025-01-01T00:00:00", env="production", pipeline="test"
        )
        mock_redis.get.side_effect = [
            json.dumps(record1.to_dict()).encode('utf-8'),
            json.dumps(record2.to_dict()).encode('utf-8')
        ]

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.list_failures(trace_id="target-trace")

        assert len(result) == 1
        assert result[0].trace_id == "target-trace"

    def test_list_failures_when_disabled(self):
        """Test that list_failures returns empty list when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.list_failures()

        assert result == []

    def test_get_failure_count_success(self):
        """Test getting failure count"""
        mock_redis = MagicMock()
        mock_redis.llen.return_value = 42

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.get_failure_count()

        assert result == 42
        mock_redis.llen.assert_called_once()

    def test_get_failure_count_when_disabled(self):
        """Test that get_failure_count returns 0 when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.get_failure_count()

        assert result == 0

    def test_get_failure_summary_success(self):
        """Test getting failure summary"""
        mock_redis = MagicMock()
        mock_redis.llen.return_value = 5
        mock_redis.lrange.return_value = [b"id1", b"id2"]
        record1 = FailureRecord(
            id="id1", trace_id="t1", goal="g1", error_type="ci_failure",
            task_type="code_gen", created_at="2025-01-01T00:00:00",
            env="production", pipeline="test"
        )
        record2 = FailureRecord(
            id="id2", trace_id="t2", goal="g2", error_type="workflow_error",
            task_type="code_review", created_at="2025-01-01T00:00:00",
            env="production", pipeline="test"
        )
        mock_redis.get.side_effect = [
            json.dumps(record1.to_dict()).encode('utf-8'),
            json.dumps(record2.to_dict()).encode('utf-8')
        ]

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.get_failure_summary()

        assert result["total"] == 5
        assert "error_types" in result
        assert "task_types" in result
        assert "ci_failure" in result["error_types"]
        assert "workflow_error" in result["error_types"]

    def test_get_failure_summary_when_disabled(self):
        """Test that get_failure_summary returns empty summary when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.get_failure_summary()

        assert result["total"] == 0
        assert result["enabled"] is False

    def test_record_failure_handles_redis_error(self):
        """Test that record_failure handles Redis errors gracefully"""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis connection error")

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)
        record = FailureRecord(trace_id="t1", goal="g1", error_type="e1")

        result = recorder.record_failure(record)

        assert result is None


class TestHelperFunctions:
    """Tests for module-level helper functions"""

    def test_get_failure_recorder_without_redis(self):
        """Test get_failure_recorder without Redis client"""
        recorder = get_failure_recorder(redis_client=None, enabled=True)

        assert recorder is not None
        assert recorder.enabled is False

    def test_get_failure_recorder_with_redis(self):
        """Test get_failure_recorder with Redis client"""
        mock_redis = MagicMock()
        recorder = create_failure_recorder(redis_client=mock_redis, enabled=True)

        assert recorder is not None
        assert recorder.enabled is True

    def test_create_failure_recorder(self):
        """Test create_failure_recorder factory function"""
        mock_redis = MagicMock()
        recorder = create_failure_recorder(
            redis_client=mock_redis,
            enabled=True
        )

        assert recorder is not None
        assert recorder.enabled is True
        assert recorder.ttl_seconds == FAILURE_TTL_SECONDS
        assert recorder.key_prefix == FAILURE_KEY_PREFIX


class TestConstants:
    """Tests for module constants"""

    def test_failure_key_prefix(self):
        """Test failure key prefix constant"""
        assert FAILURE_KEY_PREFIX == "orchestrator:failures"

    def test_failure_list_key(self):
        """Test failure list key constant"""
        assert FAILURE_LIST_KEY == "orchestrator:failures:list"

    def test_failure_ttl_seconds(self):
        """Test failure TTL constant (30 days)"""
        assert FAILURE_TTL_SECONDS == 86400 * 30


class TestReplayResult:
    """Tests for ReplayResult class (Phase 5 PR-2)"""

    def test_replay_result_success(self):
        """Test creating a successful replay result"""
        result = ReplayResult(
            success=True,
            failure_id="test-failure-id",
            new_trace_id="replay-test-12345678",
            job_id="job-123"
        )

        assert result.success is True
        assert result.failure_id == "test-failure-id"
        assert result.new_trace_id == "replay-test-12345678"
        assert result.job_id == "job-123"
        assert result.error is None

    def test_replay_result_failure(self):
        """Test creating a failed replay result"""
        result = ReplayResult(
            success=False,
            failure_id="test-failure-id",
            error="Failure record not found"
        )

        assert result.success is False
        assert result.failure_id == "test-failure-id"
        assert result.new_trace_id is None
        assert result.job_id is None
        assert result.error == "Failure record not found"

    def test_replay_result_to_dict(self):
        """Test ReplayResult to_dict serialization"""
        result = ReplayResult(
            success=True,
            failure_id="test-id",
            new_trace_id="new-trace",
            job_id="job-456"
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["failure_id"] == "test-id"
        assert result_dict["new_trace_id"] == "new-trace"
        assert result_dict["job_id"] == "job-456"
        assert result_dict["error"] is None


class TestReplayFailure:
    """Tests for replay_failure method (Phase 5 PR-2)"""

    def test_replay_failure_when_disabled(self):
        """Test that replay_failure returns error when disabled"""
        recorder = FailureRecorder(redis_client=None, enabled=False)

        result = recorder.replay_failure("test-id")

        assert result.success is False
        assert result.error == "Failure recorder is disabled"

    def test_replay_failure_not_found(self):
        """Test replay_failure when failure record not found"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.replay_failure("non-existent-id")

        assert result.success is False
        assert "not found" in result.error

    def test_replay_failure_success_with_mock_queue(self):
        """Test successful replay with mocked RQ queue"""
        mock_redis = MagicMock()
        test_record = FailureRecord(
            id="test-failure-id",
            trace_id="original-trace",
            goal="Test goal for replay",
            error_type="ci_failure",
            metadata={"repo": "RC918/morningai"}
        )
        mock_redis.get.return_value = json.dumps(test_record.to_dict()).encode('utf-8')

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.replay_failure("test-failure-id")

        assert result.failure_id == "test-failure-id"
        assert result.new_trace_id is not None or result.error is not None

    def test_replay_failure_with_repo_override(self):
        """Test replay_failure with repository override"""
        mock_redis = MagicMock()
        test_record = FailureRecord(
            id="test-failure-id",
            trace_id="original-trace",
            goal="Test goal",
            error_type="workflow_error"
        )
        mock_redis.get.return_value = json.dumps(test_record.to_dict()).encode('utf-8')

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.replay_failure("test-failure-id", repo="custom/repo")

        assert result.failure_id == "test-failure-id"

    def test_replay_failure_generates_new_trace_id(self):
        """Test that replay generates a new trace_id with replay prefix"""
        mock_redis = MagicMock()
        test_record = FailureRecord(
            id="abcd1234-5678-90ab-cdef-1234567890ab",
            trace_id="original-trace",
            goal="Test goal",
            error_type="test_error"
        )
        mock_redis.get.return_value = json.dumps(test_record.to_dict()).encode('utf-8')

        recorder = FailureRecorder(redis_client=mock_redis, enabled=True)

        result = recorder.replay_failure("abcd1234-5678-90ab-cdef-1234567890ab")

        if result.new_trace_id:
            assert result.new_trace_id.startswith("replay-")
            assert "abcd1234" in result.new_trace_id
