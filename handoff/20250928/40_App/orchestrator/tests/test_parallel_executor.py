"""
Tests for ParallelExecutor - Phase F-2: DAG + Parallelization

EPIC F Phase F-2: Tests for parallel task execution.
"""

import time
from typing import Any, Dict

import pytest

from core.planner.dag_builder import DAGBuilder
from core.planner.parallel_executor import (
    BatchExecutionResult,
    ExecutionStatus,
    ParallelExecutor,
    SimpleTaskExecutor,
    TaskExecutionResult,
)
from core.planner.planner_types import (
    TaskNode,
    TaskTree,
    TaskType,
)


class TestTaskExecutionResult:
    """Tests for TaskExecutionResult"""

    def test_to_dict_serialization(self):
        """TaskExecutionResult should serialize to dict"""
        result = TaskExecutionResult(
            task_id="task1",
            status=ExecutionStatus.COMPLETED,
            result={"output": "test"},
            duration_ms=100.0,
        )
        data = result.to_dict()

        assert data["task_id"] == "task1"
        assert data["status"] == "completed"
        assert data["result"] == {"output": "test"}
        assert data["duration_ms"] == 100.0


class TestBatchExecutionResult:
    """Tests for BatchExecutionResult"""

    def test_add_result_tracks_success(self):
        """add_result should track successful tasks"""
        batch = BatchExecutionResult()
        batch.add_result(TaskExecutionResult(
            task_id="task1",
            status=ExecutionStatus.COMPLETED,
        ))

        assert batch.successful_count == 1
        assert batch.failed_count == 0
        assert batch.all_successful

    def test_add_result_tracks_failure(self):
        """add_result should track failed tasks"""
        batch = BatchExecutionResult()
        batch.add_result(TaskExecutionResult(
            task_id="task1",
            status=ExecutionStatus.FAILED,
            error="Test error",
        ))

        assert batch.successful_count == 0
        assert batch.failed_count == 1
        assert not batch.all_successful

    def test_all_successful_with_mixed_results(self):
        """all_successful should be False with mixed results"""
        batch = BatchExecutionResult()
        batch.add_result(TaskExecutionResult(
            task_id="task1",
            status=ExecutionStatus.COMPLETED,
        ))
        batch.add_result(TaskExecutionResult(
            task_id="task2",
            status=ExecutionStatus.FAILED,
        ))

        assert not batch.all_successful


class TestSimpleTaskExecutor:
    """Tests for SimpleTaskExecutor"""

    def test_execute_success(self):
        """SimpleTaskExecutor should return success result"""
        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            return f"Executed {task.task_id}"

        executor = SimpleTaskExecutor(execute_fn)
        task = TaskNode(task_id="task1", task_type=TaskType.CODE, description="Test")
        result = executor.execute(task, {})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.result == "Executed task1"
        assert result.duration_ms > 0

    def test_execute_failure(self):
        """SimpleTaskExecutor should return failure result on exception"""
        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            raise ValueError("Test error")

        executor = SimpleTaskExecutor(execute_fn)
        task = TaskNode(task_id="task1", task_type=TaskType.CODE, description="Test")
        result = executor.execute(task, {})

        assert result.status == ExecutionStatus.FAILED
        assert "Test error" in result.error


class TestParallelExecutorInit:
    """Tests for ParallelExecutor initialization"""

    def test_default_max_parallel(self):
        """Default max_parallel should be 3"""
        executor = ParallelExecutor()
        assert executor.max_parallel == 3

    def test_custom_max_parallel(self):
        """Custom max_parallel should be set"""
        executor = ParallelExecutor(max_parallel=5)
        assert executor.max_parallel == 5

    def test_invalid_max_parallel_raises_error(self):
        """max_parallel < 1 should raise ValueError"""
        with pytest.raises(ValueError, match="at least 1"):
            ParallelExecutor(max_parallel=0)


class TestParallelExecutorGetExecutableBatch:
    """Tests for ParallelExecutor.get_executable_batch()"""

    def test_empty_tree_returns_empty_batch(self):
        """Empty tree should return empty batch"""
        executor = ParallelExecutor()
        tree = TaskTree(nodes=[], edges=[])
        batch = executor.get_executable_batch(tree, set(), set())

        assert len(batch) == 0

    def test_all_completed_returns_empty_batch(self):
        """All completed tasks should return empty batch"""
        executor = ParallelExecutor()
        tasks = [TaskNode(task_id="task1", task_type=TaskType.CODE, description="Test")]
        tree = TaskTree(nodes=tasks, edges=[])
        batch = executor.get_executable_batch(tree, {"task1"}, set())

        assert len(batch) == 0

    def test_in_progress_excluded_from_batch(self):
        """In-progress tasks should be excluded from batch"""
        executor = ParallelExecutor()
        tasks = [TaskNode(task_id="task1", task_type=TaskType.CODE, description="Test")]
        tree = TaskTree(nodes=tasks, edges=[])
        batch = executor.get_executable_batch(tree, set(), {"task1"})

        assert len(batch) == 0

    def test_respects_dependencies(self):
        """Tasks with unmet dependencies should not be in batch"""
        executor = ParallelExecutor()
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        tree = builder.from_linear(tasks)

        # task2 depends on task1, so only task1 should be executable
        batch = executor.get_executable_batch(tree, set(), set())
        assert len(batch) == 1
        assert batch[0].task_id == "task1"

        # After task1 completes, task2 should be executable
        batch = executor.get_executable_batch(tree, {"task1"}, set())
        assert len(batch) == 1
        assert batch[0].task_id == "task2"

    def test_limits_to_max_parallel(self):
        """Batch should be limited to max_parallel"""
        executor = ParallelExecutor(max_parallel=2)
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task 1"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Task 2"),
            TaskNode(task_id="task3", task_type=TaskType.CODE, description="Task 3"),
        ]
        tree = TaskTree(nodes=tasks, edges=[])

        batch = executor.get_executable_batch(tree, set(), set())
        assert len(batch) == 2

    def test_sorts_by_priority(self):
        """Batch should be sorted by priority (lower = higher priority)"""
        executor = ParallelExecutor(max_parallel=3)
        tasks = [
            TaskNode(task_id="low", task_type=TaskType.CODE, description="Low", priority=10),
            TaskNode(task_id="high", task_type=TaskType.CODE, description="High", priority=1),
            TaskNode(task_id="medium", task_type=TaskType.CODE, description="Medium", priority=5),
        ]
        tree = TaskTree(nodes=tasks, edges=[])

        batch = executor.get_executable_batch(tree, set(), set())
        assert batch[0].task_id == "high"
        assert batch[1].task_id == "medium"
        assert batch[2].task_id == "low"


class TestParallelExecutorExecuteBatch:
    """Tests for ParallelExecutor.execute_batch()"""

    def test_empty_batch_returns_empty_result(self):
        """Empty batch should return empty result"""
        executor = ParallelExecutor()
        task_executor = SimpleTaskExecutor(lambda t, c: None)
        result = executor.execute_batch([], task_executor)

        assert len(result.results) == 0

    def test_executes_all_tasks(self):
        """All tasks in batch should be executed"""
        executor = ParallelExecutor()
        executed = []

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            executed.append(task.task_id)
            return f"Done {task.task_id}"

        task_executor = SimpleTaskExecutor(execute_fn)
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task 1"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Task 2"),
        ]
        result = executor.execute_batch(tasks, task_executor)

        assert len(result.results) == 2
        assert "task1" in executed
        assert "task2" in executed

    def test_tracks_duration(self):
        """Batch result should track total duration"""
        executor = ParallelExecutor()

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            time.sleep(0.01)  # Small delay
            return "Done"

        task_executor = SimpleTaskExecutor(execute_fn)
        tasks = [TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task")]
        result = executor.execute_batch(tasks, task_executor)

        assert result.total_duration_ms > 0


class TestParallelExecutorExecuteTree:
    """Tests for ParallelExecutor.execute_tree()"""

    def test_empty_tree_returns_empty_results(self):
        """Empty tree should return empty results"""
        executor = ParallelExecutor()
        task_executor = SimpleTaskExecutor(lambda t, c: None)
        tree = TaskTree(nodes=[], edges=[])
        results = executor.execute_tree(tree, task_executor)

        assert len(results) == 0

    def test_executes_all_tasks_in_order(self):
        """All tasks should be executed respecting dependencies"""
        executor = ParallelExecutor()
        execution_order = []

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            execution_order.append(task.task_id)
            return f"Done {task.task_id}"

        task_executor = SimpleTaskExecutor(execute_fn)
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
            TaskNode(task_id="task3", task_type=TaskType.TEST, description="Test"),
        ]
        tree = builder.from_linear(tasks)
        results = executor.execute_tree(tree, task_executor)

        assert len(results) == 3
        # task1 must come before task2, task2 before task3
        assert execution_order.index("task1") < execution_order.index("task2")
        assert execution_order.index("task2") < execution_order.index("task3")

    def test_handles_failed_tasks(self):
        """Failed tasks should be tracked and dependents skipped"""
        executor = ParallelExecutor()

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            if task.task_id == "task1":
                raise ValueError("Task 1 failed")
            return f"Done {task.task_id}"

        task_executor = SimpleTaskExecutor(execute_fn)
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        tree = builder.from_linear(tasks)
        results = executor.execute_tree(tree, task_executor)

        assert len(results) == 2
        task1_result = next(r for r in results if r.task_id == "task1")
        task2_result = next(r for r in results if r.task_id == "task2")

        assert task1_result.status == ExecutionStatus.FAILED
        assert task2_result.status == ExecutionStatus.SKIPPED

    def test_calls_on_batch_complete_callback(self):
        """on_batch_complete callback should be called after each batch"""
        executor = ParallelExecutor()
        batches_completed = []

        def on_batch_complete(batch_result: BatchExecutionResult):
            batches_completed.append(batch_result)

        task_executor = SimpleTaskExecutor(lambda t, c: "Done")
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        tree = builder.from_linear(tasks)
        executor.execute_tree(tree, task_executor, on_batch_complete=on_batch_complete)

        # Two batches: one for task1, one for task2
        assert len(batches_completed) == 2

    def test_parallel_execution_of_independent_tasks(self):
        """Independent tasks should be executed in parallel"""
        executor = ParallelExecutor(max_parallel=3)
        execution_times = {}

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            start = time.time()
            time.sleep(0.05)  # 50ms delay
            execution_times[task.task_id] = (start, time.time())
            return f"Done {task.task_id}"

        task_executor = SimpleTaskExecutor(execute_fn)
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="setup", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="analyze1", task_type=TaskType.ANALYZE, description="Analyze 1"),
            TaskNode(task_id="analyze2", task_type=TaskType.ANALYZE, description="Analyze 2"),
        ]
        deps = {
            "analyze1": ["setup"],
            "analyze2": ["setup"],
        }
        tree = builder.from_dependencies(tasks, deps)
        results = executor.execute_tree(tree, task_executor)

        assert len(results) == 3

        # analyze1 and analyze2 should have overlapping execution times
        # (they run in parallel after setup completes)
        a1_start, a1_end = execution_times["analyze1"]
        a2_start, a2_end = execution_times["analyze2"]

        # Check for overlap: one starts before the other ends
        has_overlap = (a1_start < a2_end and a2_start < a1_end)
        assert has_overlap, "analyze1 and analyze2 should run in parallel"


class TestParallelExecutorAsync:
    """Tests for async methods of ParallelExecutor"""

    @pytest.mark.asyncio
    async def test_execute_batch_async_empty(self):
        """Empty batch should return empty result"""
        executor = ParallelExecutor()
        task_executor = SimpleTaskExecutor(lambda t, c: None)
        result = await executor.execute_batch_async([], task_executor)

        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_execute_batch_async_executes_all(self):
        """All tasks should be executed asynchronously"""
        executor = ParallelExecutor()
        executed = []

        def execute_fn(task: TaskNode, context: Dict[str, Any]) -> str:
            executed.append(task.task_id)
            return f"Done {task.task_id}"

        task_executor = SimpleTaskExecutor(execute_fn)
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task 1"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Task 2"),
        ]
        result = await executor.execute_batch_async(tasks, task_executor)

        assert len(result.results) == 2
        assert "task1" in executed
        assert "task2" in executed

    @pytest.mark.asyncio
    async def test_execute_tree_async(self):
        """execute_tree_async should execute all tasks"""
        executor = ParallelExecutor()
        task_executor = SimpleTaskExecutor(lambda t, c: f"Done {t.task_id}")
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        tree = builder.from_linear(tasks)
        results = await executor.execute_tree_async(tree, task_executor)

        assert len(results) == 2
        assert all(r.status == ExecutionStatus.COMPLETED for r in results)
