"""
Plan Consumer Protocol - Flow Controller v3 Consumption Interface

EPIC F Phase F-0: Planner Output Contract

This module defines the protocol for consuming Planner v3 output.
Flow Controller v3 and other consumers should implement this protocol
to execute plans produced by Planner v3.

Blueprint Reference: Section 3.2 (Flow Controller v3 - Intelligent Dynamic State Machine)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set

from .planner_types import PlannerOutput, TaskNode
from utils.sanitization import sanitize_for_log as _sanitize_for_log


class ExecutionStatus(Enum):
    """Status of task or plan execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class TaskResult:
    """
    Result of executing a single task

    Attributes:
        task_id: ID of the executed task
        status: Execution status
        outputs: Output data from the task
        error_message: Error message if failed
        started_at: When execution started
        completed_at: When execution completed
        actual_duration_minutes: Actual time taken
    """
    task_id: str
    status: ExecutionStatus
    outputs: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_duration_minutes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "outputs": self.outputs,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "actual_duration_minutes": self.actual_duration_minutes,
        }


@dataclass
class ExecutionResult:
    """
    Result of executing a complete plan

    Attributes:
        plan_id: ID of the executed plan
        status: Overall execution status
        task_results: Results for each task
        total_duration_minutes: Total time taken
        error_summary: Summary of errors if any
    """
    plan_id: str
    status: ExecutionStatus
    task_results: List[TaskResult]
    total_duration_minutes: int = 0
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "plan_id": self.plan_id,
            "status": self.status.value,
            "task_results": [r.to_dict() for r in self.task_results],
            "total_duration_minutes": self.total_duration_minutes,
            "error_summary": self.error_summary,
        }

    def get_completed_count(self) -> int:
        """Get count of completed tasks"""
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.COMPLETED)

    def get_failed_count(self) -> int:
        """Get count of failed tasks"""
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.FAILED)

    def get_progress_percent(self) -> float:
        """Get execution progress as percentage"""
        if not self.task_results:
            return 0.0
        completed = self.get_completed_count()
        return (completed / len(self.task_results)) * 100


class PlanConsumer(Protocol):
    """
    Protocol for consuming Planner v3 output

    This protocol defines the interface that Flow Controller v3 and other
    consumers must implement to execute plans produced by Planner v3.

    The protocol supports:
    - Full plan execution with dependency tracking
    - Incremental execution (get next executable tasks)
    - Parallel execution detection
    - Execution state tracking
    """

    def execute_plan(self, plan: PlannerOutput) -> ExecutionResult:
        """
        Execute a complete plan, respecting DAG dependencies

        This method executes all tasks in the plan in the correct order,
        handling dependencies and potential parallelism.

        Args:
            plan: The PlannerOutput to execute

        Returns:
            ExecutionResult with status and task results
        """
        ...

    def get_next_executable_tasks(
        self,
        plan: PlannerOutput,
        completed: Set[str]
    ) -> List[TaskNode]:
        """
        Get tasks ready for execution (all dependencies met)

        This method is useful for incremental execution where the consumer
        wants to control the execution loop.

        Args:
            plan: The PlannerOutput being executed
            completed: Set of completed task_ids

        Returns:
            List of TaskNode objects ready for execution
        """
        ...

    def can_parallelize(self, tasks: List[TaskNode]) -> bool:
        """
        Check if tasks can be executed in parallel

        Args:
            tasks: List of tasks to check

        Returns:
            True if tasks can be executed in parallel
        """
        ...


class BasePlanConsumer(ABC):
    """
    Abstract base class for plan consumers

    This class provides default implementations for common operations
    while requiring subclasses to implement the actual task execution.
    """

    def __init__(self, max_parallel: int = 3):
        """
        Initialize the consumer

        Args:
            max_parallel: Maximum number of tasks to execute in parallel
        """
        self.max_parallel = max_parallel

    def get_next_executable_tasks(
        self,
        plan: PlannerOutput,
        completed: Set[str]
    ) -> List[TaskNode]:
        """
        Get tasks ready for execution (all dependencies met)

        Default implementation uses TaskTree.get_executable_tasks()
        """
        return plan.task_tree.get_executable_tasks(completed)

    def can_parallelize(self, tasks: List[TaskNode]) -> bool:
        """
        Check if tasks can be executed in parallel

        Default implementation checks if task count is within max_parallel
        and none of the tasks require approval.
        """
        if len(tasks) > self.max_parallel:
            return False

        # Don't parallelize if any task requires approval
        if any(task.requires_approval for task in tasks):
            return False

        return True

    def execute_plan(self, plan: PlannerOutput) -> ExecutionResult:
        """
        Execute a complete plan, respecting DAG dependencies

        This implementation executes tasks sequentially by default.
        Subclasses can override for parallel execution.
        """
        # Validate plan first
        errors = plan.validate()
        if errors:
            return ExecutionResult(
                plan_id=plan.plan_id,
                status=ExecutionStatus.FAILED,
                task_results=[],
                error_summary=f"Plan validation failed: {'; '.join(_sanitize_for_log(e) for e in errors)}",
            )

        completed: Set[str] = set()
        task_results: List[TaskResult] = []
        start_time = datetime.now(timezone.utc)

        while True:
            executable = self.get_next_executable_tasks(plan, completed)
            if not executable:
                break

            for task in executable:
                result = self.execute_task(task, plan)
                task_results.append(result)

                if result.status == ExecutionStatus.COMPLETED:
                    completed.add(task.task_id)
                elif result.status == ExecutionStatus.SKIPPED:
                    # SKIPPED tasks are treated as completed for dependency resolution.
                    # This allows dependent tasks to proceed even when a task is skipped
                    # (e.g., due to conditional execution or pre-conditions not met).
                    # See Issue #3834 for the bug this fixes.
                    completed.add(task.task_id)
                elif result.status == ExecutionStatus.FAILED:
                    # Stop on failure (could be configurable)
                    end_time = datetime.now(timezone.utc)
                    duration = int((end_time - start_time).total_seconds() / 60)
                    # Sanitize task_id and error_message to prevent log injection
                    safe_task_id = _sanitize_for_log(task.task_id)
                    safe_error = _sanitize_for_log(result.error_message or "")
                    return ExecutionResult(
                        plan_id=plan.plan_id,
                        status=ExecutionStatus.FAILED,
                        task_results=task_results,
                        total_duration_minutes=duration,
                        error_summary=f"Task {safe_task_id} failed: {safe_error}",
                    )

        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds() / 60)

        # Determine overall status
        all_completed = len(completed) == len(plan.task_tree.nodes)
        status = ExecutionStatus.COMPLETED if all_completed else ExecutionStatus.FAILED

        return ExecutionResult(
            plan_id=plan.plan_id,
            status=status,
            task_results=task_results,
            total_duration_minutes=duration,
        )

    @abstractmethod
    def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
        """
        Execute a single task

        Subclasses must implement this method to perform actual task execution.

        Args:
            task: The TaskNode to execute
            plan: The parent PlannerOutput for context

        Returns:
            TaskResult with execution status and outputs
        """
        ...


class DryRunPlanConsumer(BasePlanConsumer):
    """
    Dry-run plan consumer for testing and validation

    This consumer simulates plan execution without actually performing
    any actions. Useful for testing plan structure and dependencies.
    """

    def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
        """
        Simulate task execution (always succeeds)
        """
        return TaskResult(
            task_id=task.task_id,
            status=ExecutionStatus.COMPLETED,
            outputs={"dry_run": True},
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            actual_duration_minutes=0,
        )
