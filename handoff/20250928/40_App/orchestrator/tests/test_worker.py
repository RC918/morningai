"""
Tests for RQ Worker with heartbeat monitoring and graceful shutdown
"""
import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone

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
    shutting_down
)


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
    """Test run_orchestrator_task function"""
    
    @patch('redis_queue.worker.redis')
    @patch('graph.execute')
    @patch.dict(os.environ, {"USE_LANGGRAPH": "false"})
    def test_run_orchestrator_simple_mode_success(self, mock_execute, mock_redis):
        """Test orchestrator task in simple mode (non-LangGraph)"""
        mock_execute.return_value = ("https://github.com/pr/1", "success", "trace-123")
        
        result = run_orchestrator_task("task-123", "Create FAQ", "owner/repo")
        
        assert result["pr_url"] == "https://github.com/pr/1"
        assert result["trace_id"] == "trace-123"
        assert result["state"] == "success"
        
        assert mock_redis.hset.call_count >= 2  # running + done
        assert mock_redis.expire.call_count >= 2
    
    @patch('redis_queue.worker.redis')
    @patch('langgraph_orchestrator.run_orchestrator')
    @patch.dict(os.environ, {"USE_LANGGRAPH": "true"})
    def test_run_orchestrator_langgraph_mode_success(self, mock_run_orch, mock_redis):
        """Test orchestrator task in LangGraph mode"""
        mock_run_orch.return_value = {
            "pr_url": "https://github.com/pr/2",
            "ci_state": "success",
            "trace_id": "trace-456"
        }
        
        result = run_orchestrator_task("task-456", "Generate docs", "owner/repo")
        
        assert result["pr_url"] == "https://github.com/pr/2"
        assert result["state"] == "success"
        assert result["trace_id"] == "trace-456"
        
        mock_run_orch.assert_called_once_with("Generate docs", "owner/repo", "task-456")
    
    @patch('redis_queue.worker.redis')
    @patch('graph.execute')
    @patch('redis_queue.worker.upsert_task_running')
    @patch('redis_queue.worker.upsert_task_done')
    @patch.dict(os.environ, {"USE_LANGGRAPH": "false"})
    def test_run_orchestrator_task_db_persistence(self, mock_upsert_done, mock_upsert_running, mock_execute, mock_redis):
        """Test that task status is persisted to database"""
        mock_execute.return_value = ("https://github.com/pr/3", "success", "trace-789")
        
        run_orchestrator_task("task-789", "Test", "owner/repo")
        
        mock_upsert_running.assert_called_once_with(task_id="task-789", trace_id="task-789")
        mock_upsert_done.assert_called_once_with(
            task_id="task-789",
            trace_id="trace-789",
            pr_url="https://github.com/pr/3"
        )
    
    @patch('redis_queue.worker.redis')
    @patch('graph.execute')
    @patch('redis_queue.worker.upsert_task_error')
    @patch.dict(os.environ, {"USE_LANGGRAPH": "false"})
    def test_run_orchestrator_task_handles_errors(self, mock_upsert_error, mock_execute, mock_redis):
        """Test orchestrator task error handling"""
        mock_execute.side_effect = Exception("Orchestration failed")
        
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
        
        assert call_args[0][1] == 120
        
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
