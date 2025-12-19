"""
E2E and Circuit Breaker Tests for LangGraph-only Mode - Issue #2736
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from rollout_tracker import RolloutTracker, CircuitState, CircuitBreakerState

try:
    import langgraph  # noqa: F401
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


@pytest.fixture
def mock_redis():
    """Shared mock Redis client fixture for circuit breaker tests."""
    redis = MagicMock()
    redis.get.return_value = None
    return redis


@pytest.fixture
def tracker(mock_redis):
    """RolloutTracker fixture with mock Redis."""
    return RolloutTracker(redis_client=mock_redis, enabled=True)


class TestCircuitBreakerBehavior:
    """Circuit Breaker Behavior Tests for LangGraph-only Mode"""

    def test_circuit_breaker_returns_false_when_open(self, tracker):
        tracker._circuit_breaker.state = CircuitState.OPEN
        tracker._circuit_breaker.cooldown_until = "2099-12-31T23:59:59+00:00"
        result = tracker.check_circuit_breaker()
        assert result is False

    def test_circuit_breaker_closed_to_open(self, tracker):
        assert tracker._circuit_breaker.state == CircuitState.CLOSED
        for i in range(tracker.circuit_failure_threshold):
            tracker._update_circuit_breaker_failure(f"failure_{i}")
        assert tracker._circuit_breaker.state == CircuitState.OPEN

    def test_circuit_breaker_open_to_half_open(self, tracker):
        tracker._circuit_breaker.state = CircuitState.OPEN
        tracker._circuit_breaker.cooldown_until = "2020-01-01T00:00:00+00:00"
        result = tracker.check_circuit_breaker()
        assert result is True
        assert tracker._circuit_breaker.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_half_open_to_closed(self, tracker):
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN
        for i in range(tracker.circuit_success_threshold):
            tracker._update_circuit_breaker_success()
        assert tracker._circuit_breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_half_open_to_open_on_failure(self, tracker):
        tracker._circuit_breaker.state = CircuitState.HALF_OPEN
        tracker._update_circuit_breaker_failure("test_failure")
        assert tracker._circuit_breaker.state == CircuitState.OPEN

    def test_no_simple_mode_fallback_exists(self):
        assert hasattr(CircuitState, 'CLOSED')
        assert hasattr(CircuitState, 'OPEN')
        assert hasattr(CircuitState, 'HALF_OPEN')
        assert not hasattr(CircuitState, 'FALLBACK')
        assert not hasattr(CircuitState, 'SIMPLE_MODE')

    def test_circuit_breaker_state_persisted_to_redis(self, tracker, mock_redis):
        for i in range(tracker.circuit_failure_threshold):
            tracker._update_circuit_breaker_failure(f"failure_{i}")
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        assert "circuit_breaker" in call_args[0][0]


class TestLangGraphOnlyRouting:
    """E2E Tests for LangGraph-only Mode"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    def test_general_task_routes_to_langgraph(
        self, mock_upsert_done, mock_upsert_running, mock_run_orch, mock_redis
    ):
        """Test that general tasks are routed to LangGraph"""
        from redis_queue.worker import run_orchestrator_task
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/owner/repo/pull/1",
            "ci_state": "success",
            "trace_id": "trace-general-123"
        }
        task_id = f"task-general-{uuid.uuid4()}"
        result = run_orchestrator_task(
            task_id, "Implement feature X", "owner/repo", task_type="general"
        )
        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"
        assert result["state"] == "success"
        mock_run_orch.assert_called_once()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    def test_faq_task_routes_to_langgraph(
        self, mock_upsert_done, mock_upsert_running, mock_run_orch, mock_redis
    ):
        """Test FAQ tasks use LangGraph (not Simple Mode after #2720)"""
        from redis_queue.worker import run_orchestrator_task
        mock_run_orch.return_value = {
            "pr_url": "",
            "ci_state": "success",
            "trace_id": "trace-faq-456"
        }
        task_id = f"task-faq-{uuid.uuid4()}"
        result = run_orchestrator_task(
            task_id, "What is the purpose of this function?",
            "owner/repo", task_type="faq"
        )
        assert result["trace_id"] == "trace-faq-456"
        mock_run_orch.assert_called_once()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    def test_webhook_task_receives_pr_context(
        self, mock_upsert_done, mock_upsert_running, mock_run_orch, mock_redis
    ):
        """Test webhook tasks receive PR context (Phase B-B)"""
        from redis_queue.worker import run_orchestrator_task
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/owner/repo/pull/42",
            "ci_state": "success",
            "trace_id": "trace-webhook-789"
        }
        webhook_context = {
            "resource_id": 42,
            "resource_type": "pull_request",
            "url": "https://github.com/owner/repo/pull/42"
        }
        task_id = f"task-webhook-{uuid.uuid4()}"
        result = run_orchestrator_task(
            task_id, "Review this PR", "owner/repo",
            task_type="review", context=webhook_context
        )
        assert result["pr_url"] == "https://github.com/owner/repo/pull/42"
        mock_run_orch.assert_called_once()
        call_args = mock_run_orch.call_args
        passed_context = call_args[1].get("context") if call_args[1] else None
        if passed_context is None and len(call_args[0]) > 3:
            passed_context = call_args[0][3]
        assert passed_context == webhook_context

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    def test_task_completion_stores_result(
        self, mock_upsert_done, mock_upsert_running, mock_run_orch, mock_redis
    ):
        """Test task completion and result storage"""
        from redis_queue.worker import run_orchestrator_task
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/owner/repo/pull/99",
            "ci_state": "success",
            "trace_id": "trace-complete-999"
        }
        task_id = f"task-complete-{uuid.uuid4()}"
        result = run_orchestrator_task(task_id, "Complete task", "owner/repo")
        assert mock_redis.hset.called
        mock_upsert_running.assert_called_once()
        mock_upsert_done.assert_called_once()
        assert "pr_url" in result
        assert "trace_id" in result
        assert "state" in result


class TestWorkerCircuitBreakerIntegration:
    """Integration tests for circuit breaker in worker.py"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    @patch('redis_queue.worker._rollout_tracker')
    def test_worker_proceeds_when_circuit_breaker_open(
        self, mock_tracker, mock_upsert_done, mock_upsert_running,
        mock_run_orch, mock_redis
    ):
        """Test worker proceeds with LangGraph even when circuit breaker is OPEN"""
        from redis_queue.worker import run_orchestrator_task
        mock_tracker.check_circuit_breaker.return_value = False
        mock_tracker.get_circuit_breaker_state.return_value = CircuitBreakerState(
            state=CircuitState.OPEN,
            last_state_change=datetime.now(timezone.utc).isoformat(),
            failure_count=5,
            last_failure_reason="test_failure"
        )
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/owner/repo/pull/1",
            "ci_state": "success",
            "trace_id": "trace-open-circuit"
        }
        task_id = f"task-open-circuit-{uuid.uuid4()}"
        result = run_orchestrator_task(task_id, "Test task", "owner/repo")
        assert result["pr_url"] == "https://github.com/owner/repo/pull/1"
        mock_run_orch.assert_called_once()
