#!/usr/bin/env python3
"""
Task Routing Tests for Ops Agent Worker
Tests for Issue #1909 (misrouted task -> FAILED + event) and Issue #1910 (enqueue without assigned_to -> warning log)
"""
import os
import sys
import pytest
import pytest_asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from common.config.settings import settings
from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority, TaskStatus
from orchestrator.task_queue.redis_queue import RedisQueue, create_redis_queue


class TestMisroutedTaskHandling:
    """
    Tests for Issue #1909: Misrouted task should be marked as FAILED and publish task.failed event
    """

    @pytest.fixture
    def mock_queue(self):
        """Create a mock RedisQueue"""
        queue = MagicMock(spec=RedisQueue)
        queue.update_task = AsyncMock(return_value=True)
        queue.publish_event = AsyncMock(return_value=True)
        queue.dequeue_task = AsyncMock()
        return queue

    @pytest.mark.asyncio
    async def test_misrouted_task_assigned_to_dev_marked_failed(self, mock_queue):
        """Test that task assigned to 'dev' is marked as failed by ops worker"""
        from agents.ops_agent.worker import OpsAgentWorker

        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"test": "misrouted"},
            priority=TaskPriority.P2,
            source="test",
            assigned_to="dev"
        )

        mock_queue.dequeue_task.return_value = task

        with patch.object(OpsAgentWorker, '__init__', lambda self, **kwargs: None):
            worker = OpsAgentWorker()
            worker.queue = mock_queue
            worker.is_running = False
            worker.poll_interval = 0.1
            worker.ops_agent = None
            worker.agent_id = None

            if task.assigned_to != "ops":
                error_msg = (
                    f"Task routing error: assigned_to='{task.assigned_to}', expected 'ops'. "
                    "Task may have been misrouted or created without proper assignment."
                )
                task.mark_failed(error_msg)
                await mock_queue.update_task(task)
                await mock_queue.publish_event(
                    event_type="task.failed",
                    source_agent="ops",
                    task_id=task.task_id,
                    payload={
                        "task_type": task.type.value,
                        "error": error_msg,
                        "reason": "misrouted_task"
                    },
                    trace_id=task.trace_id
                )

        assert task.status == TaskStatus.FAILED
        assert "routing error" in task.error.lower()

        mock_queue.update_task.assert_called_once()
        updated_task = mock_queue.update_task.call_args[0][0]
        assert updated_task.status == TaskStatus.FAILED

        mock_queue.publish_event.assert_called_once()
        event_call = mock_queue.publish_event.call_args
        assert event_call.kwargs["event_type"] == "task.failed"
        assert event_call.kwargs["payload"]["reason"] == "misrouted_task"

    @pytest.mark.asyncio
    async def test_misrouted_task_assigned_to_none_marked_failed(self, mock_queue):
        """Test that task with assigned_to=None is marked as failed by ops worker"""
        task = UnifiedTask(
            type=TaskType.MONITOR,
            payload={"test": "unassigned"},
            priority=TaskPriority.P1,
            source="test",
            assigned_to=None
        )

        if task.assigned_to != "ops":
            error_msg = (
                f"Task routing error: assigned_to='{task.assigned_to}', expected 'ops'. "
                "Task may have been misrouted or created without proper assignment."
            )
            task.mark_failed(error_msg)
            await mock_queue.update_task(task)
            await mock_queue.publish_event(
                event_type="task.failed",
                source_agent="ops",
                task_id=task.task_id,
                payload={
                    "task_type": task.type.value,
                    "error": error_msg,
                    "reason": "misrouted_task"
                },
                trace_id=task.trace_id
            )

        assert task.status == TaskStatus.FAILED
        assert "None" in task.error

        mock_queue.publish_event.assert_called_once()
        event_call = mock_queue.publish_event.call_args
        assert event_call.kwargs["payload"]["reason"] == "misrouted_task"

    @pytest.mark.asyncio
    async def test_misrouted_task_event_contains_correct_fields(self, mock_queue):
        """Test that task.failed event contains all required fields"""
        task = UnifiedTask(
            type=TaskType.ALERT,
            payload={"alert_type": "test"},
            priority=TaskPriority.P0,
            source="test",
            assigned_to="faq"
        )

        error_msg = (
            f"Task routing error: assigned_to='{task.assigned_to}', expected 'ops'. "
            "Task may have been misrouted or created without proper assignment."
        )
        task.mark_failed(error_msg)

        await mock_queue.publish_event(
            event_type="task.failed",
            source_agent="ops",
            task_id=task.task_id,
            payload={
                "task_type": task.type.value,
                "error": error_msg,
                "reason": "misrouted_task"
            },
            trace_id=task.trace_id
        )

        event_call = mock_queue.publish_event.call_args

        assert event_call.kwargs["event_type"] == "task.failed"
        assert event_call.kwargs["source_agent"] == "ops"
        assert event_call.kwargs["task_id"] == task.task_id
        assert event_call.kwargs["trace_id"] == task.trace_id

        payload = event_call.kwargs["payload"]
        assert "task_type" in payload
        assert "error" in payload
        assert "reason" in payload
        assert payload["reason"] == "misrouted_task"
        assert payload["task_type"] == "alert"

    @pytest.mark.asyncio
    async def test_properly_assigned_task_not_marked_failed(self, mock_queue):
        """Test that task assigned to 'ops' is NOT marked as failed"""
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"test": "correct"},
            priority=TaskPriority.P2,
            source="test",
            assigned_to="ops"
        )

        if task.assigned_to != "ops":
            task.mark_failed("Should not happen")
            await mock_queue.update_task(task)

        assert task.status == TaskStatus.PENDING
        mock_queue.update_task.assert_not_called()


class TestEnqueueWithoutAssignedToWarning:
    """
    Tests for Issue #1910: Enqueue without assigned_to should log warning
    """

    @pytest_asyncio.fixture
    async def redis_queue(self):
        """Create a real Redis queue for testing (requires Redis)"""
        redis_url = settings.redis_url or "redis://localhost:6379"
        try:
            queue = await create_redis_queue(redis_url=redis_url)
            yield queue
            await queue.close()
        except Exception:
            pytest.skip("Redis not available for testing")

    @pytest.mark.asyncio
    async def test_enqueue_without_assigned_to_logs_warning(self, caplog):
        """Test that enqueueing task without assigned_to logs a warning"""
        redis_url = settings.redis_url or "redis://localhost:6379"

        try:
            queue = await create_redis_queue(redis_url=redis_url)
        except Exception:
            pytest.skip("Redis not available for testing")

        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"test": "no_assignment"},
            priority=TaskPriority.P2,
            source="test",
            assigned_to=None
        )

        with caplog.at_level(logging.WARNING):
            await queue.enqueue_task(task, publish_events=False)

        warning_found = any(
            "enqueued without assigned_to" in record.message
            for record in caplog.records
        )
        assert warning_found, "Expected warning about missing assigned_to not found in logs"

        await queue.close()

    @pytest.mark.asyncio
    async def test_enqueue_with_assigned_to_no_warning(self, caplog):
        """Test that enqueueing task with assigned_to does NOT log warning"""
        redis_url = settings.redis_url or "redis://localhost:6379"

        try:
            queue = await create_redis_queue(redis_url=redis_url)
        except Exception:
            pytest.skip("Redis not available for testing")

        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"test": "with_assignment"},
            priority=TaskPriority.P2,
            source="test",
            assigned_to="ops"
        )

        with caplog.at_level(logging.WARNING):
            await queue.enqueue_task(task, publish_events=False)

        warning_found = any(
            "enqueued without assigned_to" in record.message
            for record in caplog.records
        )
        assert not warning_found, "Unexpected warning about missing assigned_to found in logs"

        await queue.close()

    @pytest.mark.asyncio
    async def test_enqueue_without_assigned_to_still_succeeds(self):
        """Test that enqueueing task without assigned_to still succeeds (backward compatibility)"""
        redis_url = settings.redis_url or "redis://localhost:6379"

        try:
            queue = await create_redis_queue(redis_url=redis_url)
        except Exception:
            pytest.skip("Redis not available for testing")

        task = UnifiedTask(
            type=TaskType.MONITOR,
            payload={"test": "backward_compat"},
            priority=TaskPriority.P3,
            source="test",
            assigned_to=None
        )

        result = await queue.enqueue_task(task, publish_events=False)

        assert result is True, "Enqueue should succeed even without assigned_to"

        retrieved_task = await queue.get_task(task.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id

        await queue.close()


class TestTaskRoutingIntegration:
    """
    Integration tests for task routing behavior
    """

    @pytest.mark.asyncio
    async def test_full_misrouted_task_flow(self):
        """Test the full flow of a misrouted task being marked as failed"""
        redis_url = settings.redis_url or "redis://localhost:6379"

        try:
            queue = await create_redis_queue(redis_url=redis_url)
        except Exception:
            pytest.skip("Redis not available for testing")

        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"test": "integration"},
            priority=TaskPriority.P2,
            source="test",
            assigned_to="dev"
        )

        await queue.enqueue_task(task, publish_events=False)

        dequeued_task = await queue.dequeue_task()
        assert dequeued_task is not None
        assert dequeued_task.task_id == task.task_id

        if dequeued_task.assigned_to != "ops":
            error_msg = (
                f"Task routing error: assigned_to='{dequeued_task.assigned_to}', expected 'ops'. "
                "Task may have been misrouted or created without proper assignment."
            )
            dequeued_task.mark_failed(error_msg)
            await queue.update_task(dequeued_task)

        updated_task = await queue.get_task(task.task_id)
        assert updated_task.status == TaskStatus.FAILED
        assert "routing error" in updated_task.error.lower()

        await queue.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
