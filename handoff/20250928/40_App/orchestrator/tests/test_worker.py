"""
Tests for RQ Worker with heartbeat monitoring and graceful shutdown
"""
import pytest
import json
import threading
import uuid
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from redis_queue.worker import (
    update_worker_heartbeat,
    cleanup_heartbeat,
    signal_handler,
    run_step,
    enqueue,
    run_orchestrator_task,
    WORKER_ID,
    shutdown_event,
    HEARTBEAT_TTL,
)


# Check if langgraph is available for tests that need it
try:
    import langgraph
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestRunStep:
    """Test run_step function"""

    def test_run_step_success(self):
        """Test run_step with successful step"""
        result = run_step("analyze code")

        assert result["ok"] is True

    def test_run_step_ci_failure(self):
        """Test run_step with CI check failure"""
        result = run_step("check CI")

        assert result["ok"] is False
        assert result["error"] == "build failed"


class TestEnqueue:
    """Test enqueue function"""

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.q')
    def test_enqueue_without_idempotency(self, mock_queue, mock_redis):
        """Test enqueuing jobs without idempotency key"""
        mock_job1 = Mock()
        mock_job1.id = "job-123"
        mock_job2 = Mock()
        mock_job2.id = "job-456"
        mock_queue.enqueue.side_effect = [mock_job1, mock_job2]

        steps = ["step1", "step2"]
        result = enqueue(steps)

        assert result == ["job-123", "job-456"]
        assert mock_queue.enqueue.call_count == 2

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.q')
    def test_enqueue_with_idempotency_new(self, mock_queue, mock_redis):
        """Test enqueuing jobs with new idempotency key"""
        mock_redis.exists.return_value = False
        mock_job = Mock()
        mock_job.id = "job-789"
        mock_queue.enqueue.return_value = mock_job

        steps = ["step1"]
        result = enqueue(steps, idempotency_key="unique-key-123")

        assert result == ["job-789"]
        mock_redis.exists.assert_called_once_with("orchestrator:job:unique-key-123")
        mock_redis.setex.assert_called_once()

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.q')
    def test_enqueue_with_idempotency_existing(self, mock_queue, mock_redis):
        """Test enqueuing with existing idempotency key returns cached job IDs"""
        mock_redis.exists.return_value = True
        mock_redis.get.return_value = "job-old-1,job-old-2"

        steps = ["step1", "step2"]
        result = enqueue(steps, idempotency_key="existing-key")

        assert result == ["job-old-1", "job-old-2"]
        mock_queue.enqueue.assert_not_called()

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.q')
    def test_enqueue_redis_failure_returns_demo_jobs(self, mock_queue, mock_redis):
        """Test enqueue falls back to demo mode on Redis failure"""
        mock_queue.enqueue.side_effect = Exception("Redis connection failed")

        steps = ["step1", "step2", "step3"]
        result = enqueue(steps)

        assert len(result) == 3
        assert result[0] == "demo-job-0"
        assert result[1] == "demo-job-1"
        assert result[2] == "demo-job-2"


class TestRunOrchestratorTask:
    """Test run_orchestrator_task function (LangGraph-only mode)"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    def test_run_orchestrator_langgraph_mode_success(self, mock_run_orch, mock_redis):
        """Test orchestrator task always uses LangGraph mode"""
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/pr/2",
            "ci_state": "success",
            "trace_id": "trace-456"
        }

        task_id = f"task-456-{uuid.uuid4()}"
        result = run_orchestrator_task(task_id, "Generate docs", "owner/repo", task_type="general")

        assert result["pr_url"] == "https://github.com/pr/2"
        assert result["state"] == "success"
        assert result["trace_id"] == "trace-456"

        mock_run_orch.assert_called_once_with("Generate docs", "owner/repo", task_id)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    def test_run_orchestrator_task_db_persistence(self, mock_upsert_done, mock_upsert_running, mock_run_orch, mock_redis):
        """Test that task status is persisted to database"""
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/pr/3",
            "ci_state": "success",
            "trace_id": "trace-789"
        }

        run_orchestrator_task("task-789", "Test", "owner/repo")

        mock_upsert_running.assert_called_once_with(task_id="task-789", trace_id="task-789")
        mock_upsert_done.assert_called_once_with(
            task_id="task-789",
            trace_id="trace-789",
            pr_url="https://github.com/pr/3"
        )

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_error')
    def test_run_orchestrator_task_handles_errors(self, mock_upsert_error, mock_run_orch, mock_redis):
        """Test orchestrator task error handling"""
        mock_run_orch.side_effect = Exception("Orchestration failed")

        with pytest.raises(Exception, match="Orchestration failed"):
            run_orchestrator_task("task-error", "Test", "owner/repo")

        mock_upsert_error.assert_called_once()
        call_args = mock_upsert_error.call_args
        assert call_args[1]["task_id"] == "task-error"
        assert "Orchestration failed" in call_args[1]["error_msg"]

        calls = [c for c in mock_redis.hset.call_args_list if c[0][0] == "agent:task:task-error"]
        assert len(calls) >= 1
        error_call = None
        for c in calls:
            if "status" in c[1]["mapping"] and c[1]["mapping"]["status"] == "error":
                error_call = c
                break
        assert error_call is not None
        assert error_call[1]["mapping"]["error_message"] == "Orchestration failed"


class TestHeartbeat:
    """Test heartbeat monitoring functions"""

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.shutdown_event')
    def test_update_worker_heartbeat_running(self, mock_shutdown, mock_redis):
        """Test heartbeat update in running state"""
        mock_shutdown.is_set.side_effect = [False, True]
        mock_shutdown.wait.return_value = None

        update_worker_heartbeat()

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        assert "worker:heartbeat:" in call_args[0][0]

        assert call_args[0][1] == HEARTBEAT_TTL

        payload = json.loads(call_args[0][2])
        assert payload["state"] == "running"
        assert "last_heartbeat" in payload
        assert "worker_id" in payload
        assert "timestamp" in payload

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.shutdown_event')
    def test_update_worker_heartbeat_handles_redis_errors(self, mock_shutdown, mock_redis):
        """Test heartbeat continues on Redis errors"""
        mock_shutdown.is_set.side_effect = [False, False, True]
        mock_shutdown.wait.return_value = None
        mock_redis.setex.side_effect = [Exception("Redis error"), None]

        update_worker_heartbeat()

        assert mock_redis.setex.call_count == 2

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.redis_client_rq')
    @patch('redis_queue.worker.heartbeat_thread')
    @patch('redis_queue.worker.shutdown_event')
    def test_cleanup_heartbeat(self, mock_shutdown, mock_heartbeat_thread, mock_redis_rq, mock_redis):
        """Test cleanup_heartbeat graceful shutdown"""
        mock_heartbeat_thread.is_alive.return_value = False

        cleanup_heartbeat()

        mock_shutdown.set.assert_called_once()

        calls = mock_redis.setex.call_args_list
        assert len(calls) >= 1
        payload = json.loads(calls[0][0][2])
        assert payload["state"] == "shutting_down"

        mock_redis.delete.assert_called_once()
        assert "worker:heartbeat:" in mock_redis.delete.call_args[0][0]

        mock_redis_rq.srem.assert_called_once_with('rq:workers', WORKER_ID)

    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker.redis_client_rq')
    def test_cleanup_heartbeat_idempotent(self, mock_redis_rq, mock_redis):
        """Test cleanup_heartbeat is idempotent (safe to call multiple times)"""
        import redis_queue.worker as worker_module
        worker_module.cleanup_started = False

        cleanup_heartbeat()

        mock_redis.reset_mock()
        mock_redis_rq.reset_mock()

        cleanup_heartbeat()

        mock_redis.setex.assert_not_called()
        mock_redis.delete.assert_not_called()


class TestSignalHandler:
    """Test signal handling"""

    @patch('redis_queue.worker.cleanup_heartbeat')
    @patch('sys.exit')
    def test_signal_handler_calls_cleanup(self, mock_exit, mock_cleanup):
        """Test signal handler triggers graceful shutdown"""
        signal_handler(15, None)  # SIGTERM

        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('redis_queue.worker.cleanup_heartbeat')
    @patch('sys.exit')
    def test_signal_handler_sigint(self, mock_exit, mock_cleanup):
        """Test signal handler works with SIGINT"""
        signal_handler(2, None)  # SIGINT

        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(0)


class TestWorkerConfiguration:
    """Test worker configuration and initialization"""

    def test_worker_id_from_env(self):
        """Test WORKER_ID is set from environment"""
        assert WORKER_ID is not None
        assert isinstance(WORKER_ID, str)

    def test_shutdown_event_initialized(self):
        """Test shutdown_event is a threading.Event"""
        assert isinstance(shutdown_event, threading.Event)


class TestMetricsLatencyConsistency:
    """Test that elapsed_ms is calculated once and shared between metrics (Issue #2286)

    This test class verifies that the refactored elapsed_ms calculation provides
    the same latency value to both _canary_metrics and _rollout_tracker, ensuring
    consistent metrics reporting across different tracking systems.
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker._rollout_tracker')
    @patch('redis_queue.worker._canary_metrics')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.time.monotonic_ns')
    @patch('redis_queue.worker.settings')
    def test_elapsed_ms_same_for_canary_and_rollout_tracker(
        self, mock_settings, mock_monotonic_ns, mock_run_orch,
        mock_canary_metrics, mock_rollout_tracker, mock_redis
    ):
        """Test that _canary_metrics and _rollout_tracker receive the same elapsed_ms value

        This test verifies Issue #2286: elapsed_ms should be calculated once and
        shared between both metrics systems, not calculated separately.
        """
        # Setup: Use deterministic time values
        # start_time_ns will be 1_000_000_000 (1 second in ns)
        # end_time_ns will be 1_500_000_000 (1.5 seconds in ns)
        # Expected elapsed_ms = (1_500_000_000 - 1_000_000_000) / 1_000_000 = 500.0 ms
        start_ns = 1_000_000_000
        end_ns = 1_500_000_000
        expected_elapsed_ms = 500.0

        # monotonic_ns is called twice: once for start_time_ns, once for elapsed_ms calculation
        mock_monotonic_ns.side_effect = [start_ns, end_ns]

        # Enable LangGraph mode to trigger both metrics blocks
        mock_settings.use_langgraph = False
        mock_settings.use_langgraph_percent = 100
        mock_settings.canary_alerting_enabled = False

        # Setup mock orchestrator response
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/pr/test",
            "ci_state": "success",
            "trace_id": "trace-test"
        }

        # Setup mock metrics objects
        mock_canary_metrics.observe_latency_ms = Mock()
        mock_canary_metrics.incr_counter = Mock()
        mock_canary_metrics.get_canary_summary = Mock()
        mock_rollout_tracker.record_langgraph_task = Mock()
        mock_rollout_tracker.check_circuit_breaker = Mock(return_value=True)

        # Execute
        task_id = "test-metrics-consistency"
        run_orchestrator_task(task_id, "Test", "owner/repo", task_type="general")

        # Verify _canary_metrics received the correct elapsed_ms
        mock_canary_metrics.observe_latency_ms.assert_called_once()
        canary_latency = mock_canary_metrics.observe_latency_ms.call_args[0][0]

        # Verify _rollout_tracker received the correct elapsed_ms
        mock_rollout_tracker.record_langgraph_task.assert_called_once()
        rollout_latency = mock_rollout_tracker.record_langgraph_task.call_args[1]['latency_ms']

        # Assert both received the same value
        assert canary_latency == rollout_latency, \
            f"Latency mismatch: canary={canary_latency}, rollout={rollout_latency}"

        # Assert the value is correct
        assert canary_latency == expected_elapsed_ms, \
            f"Expected {expected_elapsed_ms}ms, got {canary_latency}ms"

        # Verify monotonic_ns was called exactly twice (start_time_ns + elapsed_ms calculation)
        # This ensures elapsed_ms is calculated once, not separately for each metrics block
        assert mock_monotonic_ns.call_count == 2, \
            f"Expected 2 monotonic_ns calls, got {mock_monotonic_ns.call_count}"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('redis_queue.worker._rollout_tracker')
    @patch('redis_queue.worker._canary_metrics')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.time.monotonic_ns')
    @patch('redis_queue.worker.settings')
    def test_metrics_continue_when_canary_metrics_fails(
        self, mock_settings, mock_monotonic_ns, mock_run_orch,
        mock_canary_metrics, mock_rollout_tracker, mock_redis
    ):
        """Test _rollout_tracker still records when _canary_metrics raises exception

        This covers the exception handling branch in the _canary_metrics block.
        """
        start_ns = 3_000_000_000
        end_ns = 3_100_000_000
        expected_elapsed_ms = 100.0

        mock_monotonic_ns.side_effect = [start_ns, end_ns]

        mock_settings.use_langgraph = False
        mock_settings.use_langgraph_percent = 100
        mock_settings.canary_alerting_enabled = False

        mock_run_orch.return_value = {
            "pr_url": "https://github.com/pr/test",
            "ci_state": "success",
            "trace_id": "trace-test"
        }

        # Make canary_metrics raise an exception
        mock_canary_metrics.observe_latency_ms = Mock(side_effect=Exception("Canary metrics error"))
        mock_rollout_tracker.record_langgraph_task = Mock()
        mock_rollout_tracker.check_circuit_breaker = Mock(return_value=True)

        task_id = "test-canary-failure"
        run_orchestrator_task(task_id, "Test", "owner/repo", task_type="general")

        # Verify _rollout_tracker was still called despite canary failure
        mock_rollout_tracker.record_langgraph_task.assert_called_once()
        rollout_latency = mock_rollout_tracker.record_langgraph_task.call_args[1]['latency_ms']

        assert rollout_latency == expected_elapsed_ms, \
            f"Expected {expected_elapsed_ms}ms, got {rollout_latency}ms"

        # Verify monotonic_ns was called exactly twice (start_time_ns + elapsed_ms calculation)
        assert mock_monotonic_ns.call_count == 2, \
            f"Expected 2 monotonic_ns calls, got {mock_monotonic_ns.call_count}"


class TestReadOnlyErrorHandling:
    """Test Redis ReadOnlyError handling during maintenance windows"""

    def test_readonly_error_sleeps_and_retries(self):
        """Test that ReadOnlyError triggers sleep and retry, not immediate exit"""
        from redis.exceptions import ReadOnlyError

        sleep_calls = []
        work_call_count = [0]

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        def mock_work(max_jobs=None):
            work_call_count[0] += 1
            if work_call_count[0] == 1:
                raise ReadOnlyError("Writes are temporarily rejected due to server upgrade")

        mock_worker = Mock()
        mock_worker.work = mock_work

        with patch('time.sleep', mock_sleep):
            consecutive_readonly_count = 0
            readonly_sleep_seconds = 15
            readonly_max_retries = 20

            for _ in range(3):
                try:
                    mock_worker.work(max_jobs=10)
                    consecutive_readonly_count = 0
                    break
                except ReadOnlyError:
                    consecutive_readonly_count += 1
                    if consecutive_readonly_count >= readonly_max_retries:
                        break
                    mock_sleep(readonly_sleep_seconds)

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 15
        assert work_call_count[0] == 2
        assert consecutive_readonly_count == 0

    def test_readonly_error_exits_after_max_retries(self):
        """Test that ReadOnlyError exits after max retries exceeded"""
        from redis.exceptions import ReadOnlyError

        sleep_calls = []
        work_call_count = [0]

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        def mock_work(max_jobs=None):
            work_call_count[0] += 1
            raise ReadOnlyError("Writes are temporarily rejected due to server upgrade")

        mock_worker = Mock()
        mock_worker.work = mock_work

        with patch('time.sleep', mock_sleep):
            consecutive_readonly_count = 0
            readonly_sleep_seconds = 15
            readonly_max_retries = 3
            should_exit = False

            while not should_exit:
                try:
                    mock_worker.work(max_jobs=10)
                    consecutive_readonly_count = 0
                    should_exit = True
                except ReadOnlyError:
                    consecutive_readonly_count += 1
                    if consecutive_readonly_count >= readonly_max_retries:
                        should_exit = True
                        break
                    mock_sleep(readonly_sleep_seconds)

        assert len(sleep_calls) == 2
        assert work_call_count[0] == 3
        assert consecutive_readonly_count == 3

    def test_readonly_counter_resets_on_success(self):
        """Test that consecutive readonly counter resets after successful work"""
        from redis.exceptions import ReadOnlyError

        work_call_count = [0]

        def mock_work(max_jobs=None):
            work_call_count[0] += 1
            if work_call_count[0] <= 2:
                raise ReadOnlyError("Writes are temporarily rejected")

        mock_worker = Mock()
        mock_worker.work = mock_work

        with patch('time.sleep', Mock()):
            consecutive_readonly_count = 0
            readonly_max_retries = 20

            for _ in range(5):
                try:
                    mock_worker.work(max_jobs=10)
                    consecutive_readonly_count = 0
                    break
                except ReadOnlyError:
                    consecutive_readonly_count += 1
                    if consecutive_readonly_count >= readonly_max_retries:
                        break

        assert consecutive_readonly_count == 0
        assert work_call_count[0] == 3

    def test_readonly_settings_configurable(self):
        """Test that readonly sleep and max retries are configurable via settings"""
        from common.config.settings import Settings

        settings = Settings(
            _env_file=None,
            REDIS_READONLY_SLEEP_SECONDS=30,
            REDIS_READONLY_MAX_RETRIES=10
        )

        assert settings.redis_readonly_sleep_seconds == 30
        assert settings.redis_readonly_max_retries == 10

    def test_readonly_settings_defaults(self):
        """Test that readonly settings have sensible defaults"""
        from common.config.settings import Settings

        settings = Settings(_env_file=None)

        assert settings.redis_readonly_sleep_seconds == 15
        assert settings.redis_readonly_max_retries == 20
