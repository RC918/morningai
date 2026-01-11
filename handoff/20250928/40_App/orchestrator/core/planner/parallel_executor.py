"""
Parallel Executor - Phase F-2: DAG + Parallelization

EPIC F Phase F-2: Executes DAG tasks with parallelism support.

This module provides the ParallelExecutor class for executing tasks from a TaskTree
with support for parallel execution of independent tasks.

Blueprint Reference: Section 3.1 (Planner v3 - Intelligent Planner)
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .planner_types import (
    TaskNode,
    TaskTree,
)

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of task execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskExecutionResult:
    """
    Result of executing a single task

    Attributes:
        task_id: ID of the executed task
        status: Execution status
        result: Result data from the task (if successful)
        error: Error message (if failed)
        duration_ms: Execution duration in milliseconds
        started_at: Start timestamp
        completed_at: Completion timestamp
    """
    task_id: str
    status: ExecutionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class BatchExecutionResult:
    """
    Result of executing a batch of tasks

    Attributes:
        results: List of individual task results
        total_duration_ms: Total batch execution time
        successful_count: Number of successful tasks
        failed_count: Number of failed tasks
    """
    results: List[TaskExecutionResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    successful_count: int = 0
    failed_count: int = 0

    def add_result(self, result: TaskExecutionResult) -> None:
        """Add a task result to the batch"""
        self.results.append(result)
        if result.status == ExecutionStatus.COMPLETED:
            self.successful_count += 1
        elif result.status == ExecutionStatus.FAILED:
            self.failed_count += 1

    @property
    def all_successful(self) -> bool:
        """Check if all tasks completed successfully"""
        return self.failed_count == 0 and self.successful_count == len(self.results)


class TaskExecutor(ABC):
    """
    Abstract base class for task execution

    Implementations should define how individual tasks are executed.
    This allows for different execution strategies (sync, async, remote, etc.)
    """

    @abstractmethod
    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskExecutionResult:
        """
        Execute a single task

        Args:
            task: TaskNode to execute
            context: Execution context (inputs, state, etc.)

        Returns:
            TaskExecutionResult with execution outcome
        """
        pass


class SimpleTaskExecutor(TaskExecutor):
    """
    Simple task executor that calls a provided function

    Useful for testing and simple use cases.
    """

    def __init__(self, execute_fn: Callable[[TaskNode, Dict[str, Any]], Any]):
        """
        Initialize with an execution function

        Args:
            execute_fn: Function that takes (TaskNode, context) and returns result
        """
        self.execute_fn = execute_fn

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskExecutionResult:
        """Execute the task using the provided function"""
        started_at = time.time()
        try:
            result = self.execute_fn(task, context)
            completed_at = time.time()
            return TaskExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                result=result,
                duration_ms=(completed_at - started_at) * 1000,
                started_at=started_at,
                completed_at=completed_at,
            )
        except Exception as e:
            completed_at = time.time()
            return TaskExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                duration_ms=(completed_at - started_at) * 1000,
                started_at=started_at,
                completed_at=completed_at,
            )


class ParallelExecutor:
    """
    Executes DAG tasks with parallelism

    Phase F-2 deliverable: Provides methods to execute tasks from a TaskTree
    with support for parallel execution of independent tasks.

    Features:
    - Respects task dependencies (DEPENDS_ON edges)
    - Executes parallel-safe tasks concurrently (PARALLEL_WITH edges)
    - Limits concurrent execution (max_parallel)
    - Tracks execution state and results

    Example usage:
        executor = ParallelExecutor(max_parallel=3)

        # Get batch of executable tasks
        batch = executor.get_executable_batch(tree, completed, in_progress)

        # Execute batch
        results = executor.execute_batch(batch, task_executor, context)

        # Or execute entire tree
        all_results = executor.execute_tree(tree, task_executor, context)
    """

    def __init__(self, max_parallel: int = 3):
        """
        Initialize the parallel executor

        Args:
            max_parallel: Maximum number of tasks to execute concurrently (default: 3)
        """
        if max_parallel < 1:
            raise ValueError("max_parallel must be at least 1")
        self.max_parallel = max_parallel
        self._thread_pool: Optional[ThreadPoolExecutor] = None

    def get_executable_batch(
        self,
        tree: TaskTree,
        completed: Set[str],
        in_progress: Set[str],
    ) -> List[TaskNode]:
        """
        Get batch of tasks that can run in parallel

        Returns tasks that:
        1. Are not completed or in progress
        2. Have all dependencies satisfied (completed)
        3. Are limited to max_parallel count

        Args:
            tree: TaskTree containing all tasks
            completed: Set of completed task_ids
            in_progress: Set of task_ids currently being executed

        Returns:
            List of TaskNode objects ready for execution (up to max_parallel)
        """
        executable: List[TaskNode] = []

        for node in tree.nodes:
            # Skip completed or in-progress tasks
            if node.task_id in completed or node.task_id in in_progress:
                continue

            # Check all dependencies are completed
            deps = tree.get_dependencies(node.task_id)
            if all(dep in completed for dep in deps):
                executable.append(node)

        # Sort by priority (lower = higher priority)
        executable.sort(key=lambda n: n.priority)

        # Limit to max_parallel
        return executable[:self.max_parallel]

    def execute_batch(
        self,
        tasks: List[TaskNode],
        executor: TaskExecutor,
        context: Optional[Dict[str, Any]] = None,
    ) -> BatchExecutionResult:
        """
        Execute tasks in parallel (up to max_parallel)

        Args:
            tasks: List of TaskNode objects to execute
            executor: TaskExecutor implementation for running tasks
            context: Optional execution context

        Returns:
            BatchExecutionResult with all task results
        """
        if not tasks:
            return BatchExecutionResult()

        context = context or {}
        batch_start = time.time()
        batch_result = BatchExecutionResult()

        # Use thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(tasks), self.max_parallel)) as pool:
            futures = {
                pool.submit(executor.execute, task, context): task
                for task in tasks
            }

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    batch_result.add_result(result)
                except Exception as e:
                    # Handle unexpected errors
                    batch_result.add_result(TaskExecutionResult(
                        task_id=task.task_id,
                        status=ExecutionStatus.FAILED,
                        error=f"Unexpected error: {str(e)}",
                    ))

        batch_result.total_duration_ms = (time.time() - batch_start) * 1000
        return batch_result

    async def execute_batch_async(
        self,
        tasks: List[TaskNode],
        executor: TaskExecutor,
        context: Optional[Dict[str, Any]] = None,
    ) -> BatchExecutionResult:
        """
        Execute tasks in parallel using asyncio

        Args:
            tasks: List of TaskNode objects to execute
            executor: TaskExecutor implementation for running tasks
            context: Optional execution context

        Returns:
            BatchExecutionResult with all task results
        """
        if not tasks:
            return BatchExecutionResult()

        context = context or {}
        batch_start = time.time()
        batch_result = BatchExecutionResult()

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(task: TaskNode) -> TaskExecutionResult:
            async with semaphore:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    executor.execute,
                    task,
                    context,
                )

        # Execute all tasks concurrently (limited by semaphore)
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True,
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_result.add_result(TaskExecutionResult(
                    task_id=tasks[i].task_id,
                    status=ExecutionStatus.FAILED,
                    error=f"Unexpected error: {str(result)}",
                ))
            else:
                batch_result.add_result(result)

        batch_result.total_duration_ms = (time.time() - batch_start) * 1000
        return batch_result

    def execute_tree(
        self,
        tree: TaskTree,
        executor: TaskExecutor,
        context: Optional[Dict[str, Any]] = None,
        on_batch_complete: Optional[Callable[[BatchExecutionResult], None]] = None,
    ) -> List[TaskExecutionResult]:
        """
        Execute entire task tree respecting dependencies

        Executes tasks in batches, where each batch contains tasks
        whose dependencies have been satisfied.

        Args:
            tree: TaskTree to execute
            executor: TaskExecutor implementation for running tasks
            context: Optional execution context
            on_batch_complete: Optional callback after each batch completes

        Returns:
            List of all TaskExecutionResult objects
        """
        if not tree.nodes:
            return []

        context = context or {}
        completed: Set[str] = set()
        in_progress: Set[str] = set()
        all_results: List[TaskExecutionResult] = []
        failed_tasks: Set[str] = set()

        while len(completed) + len(failed_tasks) < len(tree.nodes):
            # Get next batch of executable tasks
            batch = self.get_executable_batch(tree, completed, in_progress)

            if not batch:
                # No more tasks can be executed
                # This could mean remaining tasks have failed dependencies
                remaining = [
                    node.task_id for node in tree.nodes
                    if node.task_id not in completed and node.task_id not in failed_tasks
                ]
                if remaining:
                    logger.warning(
                        f"Cannot execute remaining tasks due to failed dependencies: {remaining}"
                    )
                    # Mark remaining as skipped
                    for task_id in remaining:
                        all_results.append(TaskExecutionResult(
                            task_id=task_id,
                            status=ExecutionStatus.SKIPPED,
                            error="Skipped due to failed dependencies",
                        ))
                        failed_tasks.add(task_id)
                break

            # Mark batch as in progress
            for task in batch:
                in_progress.add(task.task_id)

            # Execute batch
            batch_result = self.execute_batch(batch, executor, context)

            # Process results
            for result in batch_result.results:
                all_results.append(result)
                in_progress.discard(result.task_id)

                if result.status == ExecutionStatus.COMPLETED:
                    completed.add(result.task_id)
                else:
                    failed_tasks.add(result.task_id)

            # Callback if provided
            if on_batch_complete:
                on_batch_complete(batch_result)

        return all_results

    async def execute_tree_async(
        self,
        tree: TaskTree,
        executor: TaskExecutor,
        context: Optional[Dict[str, Any]] = None,
        on_batch_complete: Optional[Callable[[BatchExecutionResult], None]] = None,
    ) -> List[TaskExecutionResult]:
        """
        Execute entire task tree asynchronously

        Args:
            tree: TaskTree to execute
            executor: TaskExecutor implementation for running tasks
            context: Optional execution context
            on_batch_complete: Optional callback after each batch completes

        Returns:
            List of all TaskExecutionResult objects
        """
        if not tree.nodes:
            return []

        context = context or {}
        completed: Set[str] = set()
        in_progress: Set[str] = set()
        all_results: List[TaskExecutionResult] = []
        failed_tasks: Set[str] = set()

        while len(completed) + len(failed_tasks) < len(tree.nodes):
            batch = self.get_executable_batch(tree, completed, in_progress)

            if not batch:
                remaining = [
                    node.task_id for node in tree.nodes
                    if node.task_id not in completed and node.task_id not in failed_tasks
                ]
                if remaining:
                    logger.warning(
                        f"Cannot execute remaining tasks due to failed dependencies: {remaining}"
                    )
                    for task_id in remaining:
                        all_results.append(TaskExecutionResult(
                            task_id=task_id,
                            status=ExecutionStatus.SKIPPED,
                            error="Skipped due to failed dependencies",
                        ))
                        failed_tasks.add(task_id)
                break

            for task in batch:
                in_progress.add(task.task_id)

            batch_result = await self.execute_batch_async(batch, executor, context)

            for result in batch_result.results:
                all_results.append(result)
                in_progress.discard(result.task_id)

                if result.status == ExecutionStatus.COMPLETED:
                    completed.add(result.task_id)
                else:
                    failed_tasks.add(result.task_id)

            if on_batch_complete:
                on_batch_complete(batch_result)

        return all_results
