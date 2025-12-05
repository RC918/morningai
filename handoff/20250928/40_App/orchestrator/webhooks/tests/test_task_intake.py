"""
Tests for TaskIntakeService

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..normalizer import NormalizedTask
from ..task_intake import IntakeTask, IntakeTaskStatus, TaskIntakeService


@pytest.fixture
def mock_webhook_event():
    """Create a mock WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.JIRA,
        event_type=WebhookEventType.ISSUE_CREATED,
        timestamp=datetime.now(),
        raw_payload={"test": "payload"},
        title="Test Issue",
        description="This is a test issue for implementing a feature",
        url="https://jira.example.com/browse/TEST-123",
        actor_id="user-123",
        actor_name="Test User",
        resource_id="TEST-123",
        resource_type="issue",
        project_key="TEST",
        labels=["feature", "high"],
        priority="high",
    )


@pytest.fixture
def mock_normalized_task(mock_webhook_event):
    """Create a mock NormalizedTask for testing"""
    return NormalizedTask(
        task_id="webhook-jira-abc12345",
        source_event=mock_webhook_event,
        goal_text="[Jira] Issue Created: Test Issue",
        priority="high",
        requires_approval=False,
        context={"source": "jira", "project": "TEST"},
    )


@pytest.fixture
def task_intake_service():
    """Create a TaskIntakeService instance for testing"""
    return TaskIntakeService(max_queue_size=100, max_concurrent_tasks=3)


class TestTaskIntakeService:
    """Tests for TaskIntakeService"""

    def test_init(self, task_intake_service):
        """Test TaskIntakeService initialization"""
        assert task_intake_service.max_queue_size == 100
        assert task_intake_service.max_concurrent_tasks == 3
        assert task_intake_service.queue_size == 0
        assert not task_intake_service.is_full
        assert not task_intake_service._is_running

    def test_queue_task(self, task_intake_service, mock_normalized_task):
        """Test queueing a task"""
        intake_task = task_intake_service.queue_task(mock_normalized_task)

        assert intake_task is not None
        assert intake_task.intake_id.startswith("intake-")
        assert intake_task.normalized_task == mock_normalized_task
        assert intake_task.status == IntakeTaskStatus.QUEUED
        assert task_intake_service.queue_size == 1

    def test_queue_task_with_approval(self, task_intake_service, mock_webhook_event):
        """Test queueing a task that requires approval"""
        task = NormalizedTask(
            task_id="webhook-jira-xyz789",
            source_event=mock_webhook_event,
            goal_text="Deploy to production",
            priority="high",
            requires_approval=True,
            context={},
        )

        intake_task = task_intake_service.queue_task(task)

        assert intake_task is not None
        assert intake_task.status == IntakeTaskStatus.AWAITING_APPROVAL

    def test_queue_full(self, mock_normalized_task):
        """Test queue full behavior"""
        service = TaskIntakeService(max_queue_size=2)

        # Queue 2 tasks
        service.queue_task(mock_normalized_task)
        service.queue_task(mock_normalized_task)

        assert service.is_full

        # Try to queue another task
        result = service.queue_task(mock_normalized_task)
        assert result is None

    def test_get_task(self, task_intake_service, mock_normalized_task):
        """Test getting a task by ID"""
        intake_task = task_intake_service.queue_task(mock_normalized_task)

        retrieved = task_intake_service.get_task(intake_task.intake_id)
        assert retrieved == intake_task

        # Test non-existent task
        assert task_intake_service.get_task("non-existent") is None

    def test_get_tasks_by_status(self, task_intake_service, mock_normalized_task):
        """Test getting tasks by status"""
        task_intake_service.queue_task(mock_normalized_task)
        task_intake_service.queue_task(mock_normalized_task)

        queued_tasks = task_intake_service.get_tasks_by_status(IntakeTaskStatus.QUEUED)
        assert len(queued_tasks) == 2

        processing_tasks = task_intake_service.get_tasks_by_status(IntakeTaskStatus.PROCESSING)
        assert len(processing_tasks) == 0

    def test_approve_task(self, task_intake_service, mock_webhook_event):
        """Test approving a task"""
        task = NormalizedTask(
            task_id="webhook-jira-xyz789",
            source_event=mock_webhook_event,
            goal_text="Deploy to production",
            priority="high",
            requires_approval=True,
            context={},
        )

        intake_task = task_intake_service.queue_task(task)
        assert intake_task.status == IntakeTaskStatus.AWAITING_APPROVAL

        result = task_intake_service.approve_task(intake_task.intake_id)
        assert result is True
        assert intake_task.status == IntakeTaskStatus.QUEUED

    def test_reject_task(self, task_intake_service, mock_webhook_event):
        """Test rejecting a task"""
        task = NormalizedTask(
            task_id="webhook-jira-xyz789",
            source_event=mock_webhook_event,
            goal_text="Deploy to production",
            priority="high",
            requires_approval=True,
            context={},
        )

        intake_task = task_intake_service.queue_task(task)
        result = task_intake_service.reject_task(intake_task.intake_id, "Not approved")

        assert result is True
        assert intake_task.status == IntakeTaskStatus.CANCELLED
        assert intake_task.error == "Not approved"

    def test_cancel_task(self, task_intake_service, mock_normalized_task):
        """Test cancelling a task"""
        intake_task = task_intake_service.queue_task(mock_normalized_task)

        result = task_intake_service.cancel_task(intake_task.intake_id)
        assert result is True
        assert intake_task.status == IntakeTaskStatus.CANCELLED

    def test_priority_ordering(self, task_intake_service, mock_webhook_event):
        """Test that tasks are processed in priority order"""
        # Create tasks with different priorities
        low_task = NormalizedTask(
            task_id="low-task",
            source_event=mock_webhook_event,
            goal_text="Low priority task",
            priority="low",
            requires_approval=False,
            context={},
        )
        high_task = NormalizedTask(
            task_id="high-task",
            source_event=mock_webhook_event,
            goal_text="High priority task",
            priority="high",
            requires_approval=False,
            context={},
        )
        critical_task = NormalizedTask(
            task_id="critical-task",
            source_event=mock_webhook_event,
            goal_text="Critical priority task",
            priority="critical",
            requires_approval=False,
            context={},
        )

        # Queue in reverse priority order
        task_intake_service.queue_task(low_task)
        task_intake_service.queue_task(high_task)
        task_intake_service.queue_task(critical_task)

        # Get next task should return critical first
        next_task = task_intake_service._get_next_task()
        assert next_task.normalized_task.priority == "critical"

    def test_get_stats(self, task_intake_service, mock_normalized_task):
        """Test getting service statistics"""
        task_intake_service.queue_task(mock_normalized_task)

        stats = task_intake_service.get_stats()

        assert stats["queue_size"] == 1
        assert stats["max_queue_size"] == 100
        assert stats["processing_count"] == 0
        assert stats["total_tasks"] == 1
        assert stats["status_counts"]["queued"] == 1

    def test_clear_completed(self, task_intake_service, mock_normalized_task):
        """Test clearing completed tasks"""
        intake_task = task_intake_service.queue_task(mock_normalized_task)
        intake_task.status = IntakeTaskStatus.COMPLETED

        cleared = task_intake_service.clear_completed()
        assert cleared == 1
        assert task_intake_service.get_task(intake_task.intake_id) is None

    def test_set_task_executor(self, task_intake_service):
        """Test setting task executor"""
        mock_executor = AsyncMock()
        task_intake_service.set_task_executor(mock_executor)

        assert task_intake_service._task_executor == mock_executor

    def test_intake_task_to_dict(self, mock_normalized_task):
        """Test IntakeTask serialization"""
        intake_task = IntakeTask(
            intake_id="intake-test123",
            normalized_task=mock_normalized_task,
            status=IntakeTaskStatus.QUEUED,
            queued_at=datetime.now(),
        )

        data = intake_task.to_dict()

        assert data["intake_id"] == "intake-test123"
        assert data["task_id"] == mock_normalized_task.task_id
        assert data["status"] == "queued"
        assert data["source"] == "jira"
        assert data["priority"] == "high"


class TestTaskIntakeServiceAsync:
    """Async tests for TaskIntakeService"""

    @pytest.mark.asyncio
    async def test_start_stop(self, task_intake_service):
        """Test starting and stopping the service"""
        await task_intake_service.start()
        assert task_intake_service._is_running

        await task_intake_service.stop()
        assert not task_intake_service._is_running

    @pytest.mark.asyncio
    async def test_process_task_with_executor(self, task_intake_service, mock_normalized_task):
        """Test processing a task with an executor"""
        mock_executor = AsyncMock(return_value={"success": True})
        task_intake_service.set_task_executor(mock_executor)

        intake_task = task_intake_service.queue_task(mock_normalized_task)

        await task_intake_service._process_task_async(intake_task)

        assert intake_task.status == IntakeTaskStatus.COMPLETED
        assert intake_task.result == {"success": True}
        mock_executor.assert_called_once_with(mock_normalized_task)

    @pytest.mark.asyncio
    async def test_process_task_without_executor(self, task_intake_service, mock_normalized_task):
        """Test processing a task without an executor (stub mode)"""
        intake_task = task_intake_service.queue_task(mock_normalized_task)

        await task_intake_service._process_task_async(intake_task)

        assert intake_task.status == IntakeTaskStatus.COMPLETED
        assert intake_task.result["stub"] is True

    @pytest.mark.asyncio
    async def test_process_task_with_failure(self, task_intake_service, mock_normalized_task):
        """Test processing a task that fails"""
        mock_executor = AsyncMock(side_effect=Exception("Task failed"))
        task_intake_service.set_task_executor(mock_executor)

        intake_task = task_intake_service.queue_task(mock_normalized_task)
        intake_task.max_retries = 2  # Allow one retry before failing

        await task_intake_service._process_task_async(intake_task)

        # First failure should retry (retry_count=1, max_retries=2)
        assert intake_task.retry_count == 1
        assert intake_task.status == IntakeTaskStatus.QUEUED

        # Second failure should mark as failed (retry_count=2, max_retries=2)
        await task_intake_service._process_task_async(intake_task)
        assert intake_task.status == IntakeTaskStatus.FAILED
        assert "Task failed" in intake_task.error

    @pytest.mark.asyncio
    async def test_callbacks(self, task_intake_service, mock_normalized_task):
        """Test that callbacks are called"""
        received_callback = MagicMock()
        started_callback = MagicMock()
        completed_callback = MagicMock()

        # Set up an executor so on_task_completed is called
        mock_executor = AsyncMock(return_value={"success": True})
        task_intake_service.set_task_executor(mock_executor)

        task_intake_service.on_task_received = received_callback
        task_intake_service.on_task_started = started_callback
        task_intake_service.on_task_completed = completed_callback

        intake_task = task_intake_service.queue_task(mock_normalized_task)
        received_callback.assert_called_once_with(intake_task)

        await task_intake_service._process_task_async(intake_task)
        started_callback.assert_called_once_with(intake_task)
        completed_callback.assert_called_once_with(intake_task)
