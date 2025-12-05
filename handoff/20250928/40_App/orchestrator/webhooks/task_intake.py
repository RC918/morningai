"""
Task Intake Service - Webhook to Meta Agent Task Bridge

This module provides the TaskIntakeService that bridges webhook events
to the Meta Agent autonomous execution system.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Flow:
    Webhook → Handler → EventNormalizer → NormalizedTask → TaskIntakeService → AutonomousExecutor
"""

import asyncio
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .bot_protocol import WebhookSource
from .normalizer import EventNormalizer, NormalizedTask

logger = logging.getLogger(__name__)


class IntakeTaskStatus(Enum):
    """Status of a task in the intake queue"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class IntakeTask:
    """
    A task in the intake queue, wrapping NormalizedTask with queue metadata.
    """
    intake_id: str
    normalized_task: NormalizedTask
    status: IntakeTaskStatus
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "intake_id": self.intake_id,
            "task_id": self.normalized_task.task_id,
            "source": self.normalized_task.source_event.source.value,
            "event_type": self.normalized_task.source_event.event_type.value,
            "goal_text": self.normalized_task.goal_text,
            "priority": self.normalized_task.priority,
            "requires_approval": self.normalized_task.requires_approval,
            "status": self.status.value,
            "queued_at": self.queued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_id": self.execution_id,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


class TaskIntakeService:
    """
    Service for receiving and queueing tasks from webhooks for Meta Agent processing.

    This service:
    1. Receives NormalizedTask from EventNormalizer
    2. Queues tasks with priority ordering
    3. Manages task lifecycle (queued, processing, completed, failed)
    4. Provides callbacks for task execution
    5. Supports task approval workflow
    """

    # Priority order (lower number = higher priority)
    PRIORITY_ORDER = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    def __init__(
        self,
        event_normalizer: Optional[EventNormalizer] = None,
        max_queue_size: int = 1000,
        max_concurrent_tasks: int = 5,
    ):
        """
        Initialize the TaskIntakeService.

        Args:
            event_normalizer: EventNormalizer instance for processing webhooks
            max_queue_size: Maximum number of tasks in queue
            max_concurrent_tasks: Maximum concurrent task executions
        """
        self.event_normalizer = event_normalizer or EventNormalizer()
        self.max_queue_size = max_queue_size
        self.max_concurrent_tasks = max_concurrent_tasks

        # Task queues by priority
        self._queues: Dict[str, deque] = {
            "critical": deque(),
            "high": deque(),
            "medium": deque(),
            "low": deque(),
        }

        # Task registry for lookup
        self._tasks: Dict[str, IntakeTask] = {}

        # Processing state
        self._processing_count = 0
        self._is_running = False
        self._process_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_task_received: Optional[Callable[[IntakeTask], None]] = None
        self.on_task_started: Optional[Callable[[IntakeTask], None]] = None
        self.on_task_completed: Optional[Callable[[IntakeTask], None]] = None
        self.on_task_failed: Optional[Callable[[IntakeTask, str], None]] = None
        self.on_approval_required: Optional[Callable[[IntakeTask], bool]] = None

        # Task executor callback (set by AutonomousExecutor integration)
        self._task_executor: Optional[Callable[[NormalizedTask], Any]] = None

        logger.info(
            "[TaskIntakeService] Initialized with max_queue=%d, max_concurrent=%d",
            max_queue_size,
            max_concurrent_tasks,
        )

    @property
    def queue_size(self) -> int:
        """Get total number of queued tasks"""
        return sum(len(q) for q in self._queues.values())

    @property
    def is_full(self) -> bool:
        """Check if queue is at capacity"""
        return self.queue_size >= self.max_queue_size

    def set_task_executor(self, executor: Callable[[NormalizedTask], Any]) -> None:
        """
        Set the task executor callback.

        This is typically the AutonomousExecutor.execute_goal method.

        Args:
            executor: Async callable that executes a task
        """
        self._task_executor = executor
        logger.info("[TaskIntakeService] Task executor set")

    def receive_webhook(
        self,
        source: WebhookSource,
        headers: Dict[str, str],
        payload: Dict[str, Any],
    ) -> Optional[IntakeTask]:
        """
        Receive and process a webhook event.

        Args:
            source: Webhook source (github, jira, slack, linear)
            headers: Request headers
            payload: Parsed JSON payload

        Returns:
            IntakeTask if task was queued, None otherwise
        """
        # Parse the event
        event = self.event_normalizer.parse_event(source, headers, payload)
        if not event:
            logger.warning(
                "[TaskIntakeService] Failed to parse event from %s",
                source.value,
            )
            return None

        # Extract task from event
        normalized_task = self.event_normalizer.extract_task(event)
        if not normalized_task:
            logger.debug(
                "[TaskIntakeService] Event %s is not actionable",
                event.event_id,
            )
            return None

        # Queue the task
        return self.queue_task(normalized_task)

    def queue_task(self, normalized_task: NormalizedTask) -> Optional[IntakeTask]:
        """
        Queue a normalized task for processing.

        Args:
            normalized_task: Task to queue

        Returns:
            IntakeTask if queued successfully, None if queue is full
        """
        if self.is_full:
            logger.warning(
                "[TaskIntakeService] Queue is full, rejecting task %s",
                normalized_task.task_id,
            )
            return None

        # Create intake task
        intake_id = f"intake-{uuid.uuid4().hex[:8]}"
        intake_task = IntakeTask(
            intake_id=intake_id,
            normalized_task=normalized_task,
            status=IntakeTaskStatus.QUEUED,
            queued_at=datetime.now(),
        )

        # Check if approval is required
        if normalized_task.requires_approval:
            intake_task.status = IntakeTaskStatus.AWAITING_APPROVAL

        # Add to appropriate priority queue
        priority = normalized_task.priority
        if priority not in self._queues:
            priority = "medium"

        self._queues[priority].append(intake_task)
        self._tasks[intake_id] = intake_task

        logger.info(
            "[TaskIntakeService] Task queued: id=%s, priority=%s, approval=%s",
            intake_id,
            priority,
            intake_task.status == IntakeTaskStatus.AWAITING_APPROVAL,
        )

        # Notify callback
        if self.on_task_received:
            self.on_task_received(intake_task)

        return intake_task

    def get_task(self, intake_id: str) -> Optional[IntakeTask]:
        """Get a task by intake ID"""
        return self._tasks.get(intake_id)

    def get_tasks_by_status(self, status: IntakeTaskStatus) -> List[IntakeTask]:
        """Get all tasks with a specific status"""
        return [t for t in self._tasks.values() if t.status == status]

    def get_pending_tasks(self) -> List[IntakeTask]:
        """Get all pending (queued or awaiting approval) tasks"""
        return [
            t for t in self._tasks.values()
            if t.status in (IntakeTaskStatus.QUEUED, IntakeTaskStatus.AWAITING_APPROVAL)
        ]

    def approve_task(self, intake_id: str) -> bool:
        """
        Approve a task that is awaiting approval.

        Args:
            intake_id: Task intake ID

        Returns:
            True if task was approved, False otherwise
        """
        task = self._tasks.get(intake_id)
        if not task:
            logger.warning("[TaskIntakeService] Task %s not found", intake_id)
            return False

        if task.status != IntakeTaskStatus.AWAITING_APPROVAL:
            logger.warning(
                "[TaskIntakeService] Task %s is not awaiting approval (status=%s)",
                intake_id,
                task.status.value,
            )
            return False

        task.status = IntakeTaskStatus.QUEUED
        logger.info("[TaskIntakeService] Task %s approved", intake_id)
        return True

    def reject_task(self, intake_id: str, reason: str = "Rejected by user") -> bool:
        """
        Reject a task that is awaiting approval.

        Args:
            intake_id: Task intake ID
            reason: Rejection reason

        Returns:
            True if task was rejected, False otherwise
        """
        task = self._tasks.get(intake_id)
        if not task:
            logger.warning("[TaskIntakeService] Task %s not found", intake_id)
            return False

        if task.status != IntakeTaskStatus.AWAITING_APPROVAL:
            logger.warning(
                "[TaskIntakeService] Task %s is not awaiting approval (status=%s)",
                intake_id,
                task.status.value,
            )
            return False

        task.status = IntakeTaskStatus.CANCELLED
        task.error = reason
        task.completed_at = datetime.now()

        # Remove from queue
        priority = task.normalized_task.priority
        if priority in self._queues and task in self._queues[priority]:
            self._queues[priority].remove(task)

        logger.info("[TaskIntakeService] Task %s rejected: %s", intake_id, reason)
        return True

    def cancel_task(self, intake_id: str) -> bool:
        """
        Cancel a queued task.

        Args:
            intake_id: Task intake ID

        Returns:
            True if task was cancelled, False otherwise
        """
        task = self._tasks.get(intake_id)
        if not task:
            logger.warning("[TaskIntakeService] Task %s not found", intake_id)
            return False

        if task.status not in (IntakeTaskStatus.QUEUED, IntakeTaskStatus.AWAITING_APPROVAL):
            logger.warning(
                "[TaskIntakeService] Cannot cancel task %s (status=%s)",
                intake_id,
                task.status.value,
            )
            return False

        task.status = IntakeTaskStatus.CANCELLED
        task.completed_at = datetime.now()

        # Remove from queue
        priority = task.normalized_task.priority
        if priority in self._queues and task in self._queues[priority]:
            self._queues[priority].remove(task)

        logger.info("[TaskIntakeService] Task %s cancelled", intake_id)
        return True

    def _get_next_task(self) -> Optional[IntakeTask]:
        """
        Get the next task to process based on priority.

        Returns:
            Next IntakeTask or None if no tasks available
        """
        # Check queues in priority order
        for priority in ["critical", "high", "medium", "low"]:
            queue = self._queues[priority]
            for task in queue:
                if task.status == IntakeTaskStatus.QUEUED:
                    return task
        return None

    async def start(self) -> None:
        """Start the task processing loop"""
        if self._is_running:
            logger.warning("[TaskIntakeService] Already running")
            return

        self._is_running = True
        self._process_task = asyncio.create_task(self._process_loop())
        logger.info("[TaskIntakeService] Started processing loop")

    async def stop(self) -> None:
        """Stop the task processing loop"""
        self._is_running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        logger.info("[TaskIntakeService] Stopped processing loop")

    async def _process_loop(self) -> None:
        """Main processing loop"""
        while self._is_running:
            try:
                # Check if we can process more tasks
                if self._processing_count >= self.max_concurrent_tasks:
                    await asyncio.sleep(0.5)
                    continue

                # Get next task
                task = self._get_next_task()
                if not task:
                    await asyncio.sleep(0.5)
                    continue

                # Process the task
                asyncio.create_task(self._process_task_async(task))

            except Exception as e:
                logger.error(
                    "[TaskIntakeService] Error in process loop: %s",
                    e,
                    exc_info=True,
                )
                await asyncio.sleep(1)

    async def _process_task_async(self, task: IntakeTask) -> None:
        """
        Process a single task asynchronously.

        Args:
            task: IntakeTask to process
        """
        self._processing_count += 1
        task.status = IntakeTaskStatus.PROCESSING
        task.started_at = datetime.now()

        logger.info(
            "[TaskIntakeService] Processing task %s: %s",
            task.intake_id,
            task.normalized_task.goal_text[:50],
        )

        # Notify callback
        if self.on_task_started:
            self.on_task_started(task)

        try:
            # Execute the task
            if self._task_executor:
                result = await self._task_executor(task.normalized_task)
                task.result = result if isinstance(result, dict) else {"result": str(result)}
                task.status = IntakeTaskStatus.COMPLETED
                task.completed_at = datetime.now()

                logger.info(
                    "[TaskIntakeService] Task %s completed",
                    task.intake_id,
                )

                # Notify callback
                if self.on_task_completed:
                    self.on_task_completed(task)
            else:
                # No executor configured - mark as completed (stub mode)
                logger.warning(
                    "[TaskIntakeService] No task executor configured, task %s marked as completed (stub)",
                    task.intake_id,
                )
                task.status = IntakeTaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = {"stub": True, "message": "No executor configured"}

        except Exception as e:
            error_msg = str(e)
            logger.error(
                "[TaskIntakeService] Task %s failed: %s",
                task.intake_id,
                error_msg,
                exc_info=True,
            )

            task.retry_count += 1
            if task.retry_count < task.max_retries:
                # Retry the task
                task.status = IntakeTaskStatus.QUEUED
                logger.info(
                    "[TaskIntakeService] Task %s will be retried (%d/%d)",
                    task.intake_id,
                    task.retry_count,
                    task.max_retries,
                )
            else:
                # Max retries exceeded
                task.status = IntakeTaskStatus.FAILED
                task.error = error_msg
                task.completed_at = datetime.now()

                # Notify callback
                if self.on_task_failed:
                    self.on_task_failed(task, error_msg)

        finally:
            self._processing_count -= 1

            # Remove from queue
            priority = task.normalized_task.priority
            if priority in self._queues and task in self._queues[priority]:
                self._queues[priority].remove(task)

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        status_counts = {}
        for status in IntakeTaskStatus:
            status_counts[status.value] = len(self.get_tasks_by_status(status))

        source_counts: Dict[str, int] = {}
        for task in self._tasks.values():
            source = task.normalized_task.source_event.source.value
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "queue_size": self.queue_size,
            "max_queue_size": self.max_queue_size,
            "processing_count": self._processing_count,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "is_running": self._is_running,
            "total_tasks": len(self._tasks),
            "status_counts": status_counts,
            "source_counts": source_counts,
        }

    def clear_completed(self) -> int:
        """
        Clear completed and failed tasks from registry.

        Returns:
            Number of tasks cleared
        """
        to_remove = [
            intake_id
            for intake_id, task in self._tasks.items()
            if task.status in (
                IntakeTaskStatus.COMPLETED,
                IntakeTaskStatus.FAILED,
                IntakeTaskStatus.CANCELLED,
            )
        ]

        for intake_id in to_remove:
            del self._tasks[intake_id]

        logger.info("[TaskIntakeService] Cleared %d completed tasks", len(to_remove))
        return len(to_remove)
