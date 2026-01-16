"""
Tests for Planner v3 Types

EPIC F Phase F-0: Planner Output Contract

Tests for:
- TaskNode, TaskEdge, TaskTree data structures
- PlannerOutput schema validation
- DAG validation and cycle detection
- Serialization/deserialization
"""

import pytest
from datetime import datetime, timezone

pytestmark = pytest.mark.usefixtures()

from core.planner import (
    TaskType,
    EdgeType,
    RiskLevel,
    PlanType,
    TaskNode,
    TaskEdge,
    TaskTree,
    RiskMetadata,
    CostEstimate,
    PlannerMetadata,
    PlannerOutput,
    ExecutionStatus,
    TaskResult,
    ExecutionResult,
    DryRunPlanConsumer,
)


class TestTaskNode:
    """Tests for TaskNode dataclass"""

    def test_create_task_node(self):
        """Test creating a TaskNode with required fields"""
        node = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Implement feature X",
        )
        assert node.task_id == "task-1"
        assert node.task_type == TaskType.CODE
        assert node.description == "Implement feature X"
        assert node.agent_assignment == "dev_agent"
        assert node.risk_level == RiskLevel.LOW

    def test_task_node_to_dict(self):
        """Test TaskNode serialization"""
        node = TaskNode(
            task_id="task-1",
            task_type=TaskType.ANALYZE,
            description="Analyze codebase",
            priority=1,
            risk_level=RiskLevel.MEDIUM,
        )
        data = node.to_dict()
        assert data["task_id"] == "task-1"
        assert data["task_type"] == "analyze"
        assert data["risk_level"] == "medium"
        assert data["priority"] == 1

    def test_task_node_from_dict(self):
        """Test TaskNode deserialization"""
        data = {
            "task_id": "task-2",
            "task_type": "test",
            "description": "Run tests",
            "requires_approval": True,
        }
        node = TaskNode.from_dict(data)
        assert node.task_id == "task-2"
        assert node.task_type == TaskType.TEST
        assert node.requires_approval is True


class TestTaskEdge:
    """Tests for TaskEdge dataclass"""

    def test_create_task_edge(self):
        """Test creating a TaskEdge"""
        edge = TaskEdge(
            from_task="task-1",
            to_task="task-2",
            edge_type=EdgeType.DEPENDS_ON,
        )
        assert edge.from_task == "task-1"
        assert edge.to_task == "task-2"
        assert edge.edge_type == EdgeType.DEPENDS_ON

    def test_task_edge_to_dict(self):
        """Test TaskEdge serialization"""
        edge = TaskEdge(
            from_task="task-1",
            to_task="task-2",
            edge_type=EdgeType.PARALLEL_WITH,
        )
        data = edge.to_dict()
        assert data["from"] == "task-1"
        assert data["to"] == "task-2"
        assert data["type"] == "parallel_with"

    def test_task_edge_from_dict(self):
        """Test TaskEdge deserialization"""
        data = {"from": "a", "to": "b", "type": "optional_after"}
        edge = TaskEdge.from_dict(data)
        assert edge.from_task == "a"
        assert edge.to_task == "b"
        assert edge.edge_type == EdgeType.OPTIONAL_AFTER


class TestTaskTree:
    """Tests for TaskTree DAG structure"""

    def test_create_empty_task_tree(self):
        """Test creating an empty TaskTree"""
        tree = TaskTree()
        assert len(tree.nodes) == 0
        assert len(tree.edges) == 0

    def test_task_tree_get_dependencies(self):
        """Test getting dependencies for a task"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="Code"),
                TaskNode(task_id="c", task_type=TaskType.TEST, description="Test"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
                TaskEdge(from_task="b", to_task="c"),
            ],
        )
        assert tree.get_dependencies("a") == []
        assert tree.get_dependencies("b") == ["a"]
        assert tree.get_dependencies("c") == ["b"]

    def test_task_tree_get_dependents(self):
        """Test getting dependents for a task"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="Code"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
            ],
        )
        assert tree.get_dependents("a") == ["b"]
        assert tree.get_dependents("b") == []

    def test_task_tree_get_executable_tasks(self):
        """Test getting executable tasks based on completed set"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="Code"),
                TaskNode(task_id="c", task_type=TaskType.TEST, description="Test"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
                TaskEdge(from_task="b", to_task="c"),
            ],
        )
        # Initially only 'a' is executable
        executable = tree.get_executable_tasks(set())
        assert len(executable) == 1
        assert executable[0].task_id == "a"

        # After 'a' completes, 'b' is executable
        executable = tree.get_executable_tasks({"a"})
        assert len(executable) == 1
        assert executable[0].task_id == "b"

        # After 'a' and 'b' complete, 'c' is executable
        executable = tree.get_executable_tasks({"a", "b"})
        assert len(executable) == 1
        assert executable[0].task_id == "c"

    def test_task_tree_validate_valid_dag(self):
        """Test validation of a valid DAG"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="Code"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
            ],
        )
        errors = tree.validate()
        assert len(errors) == 0

    def test_task_tree_validate_missing_node(self):
        """Test validation catches missing node references"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),  # 'b' doesn't exist
            ],
        )
        errors = tree.validate()
        assert len(errors) == 1
        assert "unknown target task" in errors[0]

    def test_task_tree_validate_cycle_detection(self):
        """Test validation detects cycles"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="A"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="B"),
                TaskNode(task_id="c", task_type=TaskType.TEST, description="C"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
                TaskEdge(from_task="b", to_task="c"),
                TaskEdge(from_task="c", to_task="a"),  # Creates cycle
            ],
        )
        errors = tree.validate()
        assert len(errors) == 1
        assert "Cycle detected" in errors[0]

    def test_task_tree_serialization(self):
        """Test TaskTree serialization and deserialization"""
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="a", task_type=TaskType.SETUP, description="Setup"),
                TaskNode(task_id="b", task_type=TaskType.CODE, description="Code"),
            ],
            edges=[
                TaskEdge(from_task="a", to_task="b"),
            ],
        )
        data = tree.to_dict()
        restored = TaskTree.from_dict(data)
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1
        assert restored.nodes[0].task_id == "a"


class TestPlannerOutput:
    """Tests for PlannerOutput schema"""

    def test_create_planner_output(self):
        """Test creating a PlannerOutput"""
        output = PlannerOutput(
            goal="Implement feature X",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="t1", task_type=TaskType.CODE, description="Code"),
                ],
            ),
        )
        assert output.goal == "Implement feature X"
        assert output.plan_type == PlanType.DETAILED
        assert len(output.task_tree.nodes) == 1

    def test_planner_output_validation_valid(self):
        """Test validation of a valid PlannerOutput"""
        output = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="t1", task_type=TaskType.CODE, description="Code"),
                ],
            ),
        )
        errors = output.validate()
        assert len(errors) == 0
        assert output.is_valid()

    def test_planner_output_validation_no_goal(self):
        """Test validation catches missing goal"""
        output = PlannerOutput(
            goal="",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="t1", task_type=TaskType.CODE, description="Code"),
                ],
            ),
        )
        errors = output.validate()
        assert "Plan must have a goal" in errors

    def test_planner_output_validation_no_tasks(self):
        """Test validation catches empty task tree"""
        output = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(),
        )
        errors = output.validate()
        assert "Plan must have at least one task" in errors

    def test_planner_output_get_total_estimated_minutes(self):
        """Test calculating total estimated duration"""
        output = PlannerOutput(
            goal="Test",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(
                        task_id="t1",
                        task_type=TaskType.CODE,
                        description="Code",
                        estimated_duration_minutes=30,
                    ),
                    TaskNode(
                        task_id="t2",
                        task_type=TaskType.TEST,
                        description="Test",
                        estimated_duration_minutes=15,
                    ),
                ],
            ),
        )
        assert output.get_total_estimated_minutes() == 45

    def test_planner_output_serialization(self):
        """Test PlannerOutput serialization and deserialization"""
        output = PlannerOutput(
            goal="Test goal",
            flow_template="review_heavy",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="t1", task_type=TaskType.CODE, description="Code"),
                ],
            ),
            risk_metadata=RiskMetadata(
                overall_risk=RiskLevel.MEDIUM,
                requires_approval=True,
            ),
            planner_metadata=PlannerMetadata(
                planner_type="llm",
                confidence_score=0.85,
            ),
        )
        data = output.to_dict()
        restored = PlannerOutput.from_dict(data)

        assert restored.goal == "Test goal"
        assert restored.flow_template == "review_heavy"
        assert restored.risk_metadata.overall_risk == RiskLevel.MEDIUM
        assert restored.planner_metadata.confidence_score == 0.85


class TestDryRunPlanConsumer:
    """Tests for DryRunPlanConsumer"""

    def test_dry_run_execute_plan(self):
        """Test dry-run execution of a plan"""
        consumer = DryRunPlanConsumer()
        plan = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="t1", task_type=TaskType.SETUP, description="Setup"),
                    TaskNode(task_id="t2", task_type=TaskType.CODE, description="Code"),
                ],
                edges=[
                    TaskEdge(from_task="t1", to_task="t2"),
                ],
            ),
        )
        result = consumer.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 2
        assert result.get_completed_count() == 2

    def test_dry_run_invalid_plan(self):
        """Test dry-run with invalid plan"""
        consumer = DryRunPlanConsumer()
        plan = PlannerOutput(
            goal="",  # Invalid: empty goal
            task_tree=TaskTree(),  # Invalid: no tasks
        )
        result = consumer.execute_plan(plan)
        assert result.status == ExecutionStatus.FAILED
        assert "validation failed" in result.error_summary


class TestExecutionResult:
    """Tests for ExecutionResult"""

    def test_execution_result_progress(self):
        """Test progress calculation"""
        result = ExecutionResult(
            plan_id="test",
            status=ExecutionStatus.IN_PROGRESS,
            task_results=[
                TaskResult(task_id="t1", status=ExecutionStatus.COMPLETED, outputs={}),
                TaskResult(task_id="t2", status=ExecutionStatus.COMPLETED, outputs={}),
                TaskResult(task_id="t3", status=ExecutionStatus.PENDING, outputs={}),
                TaskResult(task_id="t4", status=ExecutionStatus.PENDING, outputs={}),
            ],
        )
        assert result.get_completed_count() == 2
        assert result.get_progress_percent() == 50.0


class TestSanitizeForLog:
    """
    Tests for _sanitize_for_log() function in consumer.py

    Issue #3840: Unit tests for sanitization functions
    Source: Gemini Code Assist (PR #3837, Comment r2679560564)
    """

    def test_empty_string(self):
        """Test sanitization of empty string"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("") == ""

    def test_newline_replacement(self):
        """Test that newlines are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("line1\nline2") == "line1 line2"

    def test_carriage_return_replacement(self):
        """Test that carriage returns are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("line1\rline2") == "line1 line2"

    def test_crlf_replacement(self):
        """Test that CRLF sequences are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("line1\r\nline2") == "line1  line2"

    def test_string_shorter_than_max_length(self):
        """Test that short strings are not truncated"""
        from core.planner.consumer import _sanitize_for_log
        short_string = "short"
        assert _sanitize_for_log(short_string, max_length=200) == "short"

    def test_string_equal_to_max_length(self):
        """Test that strings exactly at max_length are not truncated"""
        from core.planner.consumer import _sanitize_for_log
        exact_string = "a" * 200
        assert _sanitize_for_log(exact_string, max_length=200) == exact_string

    def test_string_longer_than_max_length(self):
        """Test that long strings are truncated with ellipsis"""
        from core.planner.consumer import _sanitize_for_log
        long_string = "a" * 250
        result = _sanitize_for_log(long_string, max_length=200)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_only_control_characters(self):
        """Test string with only control characters (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("\n\r\n\r") == "    "

    def test_multiple_newlines(self):
        """Test string with multiple newlines (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        assert _sanitize_for_log("a\nb\nc\nd") == "a b c d"

    def test_custom_max_length(self):
        """Test with custom max_length parameter"""
        from core.planner.consumer import _sanitize_for_log
        result = _sanitize_for_log("abcdefghij", max_length=5)
        assert result == "abcde..."

    def test_truncation_after_escape(self):
        """Test that truncation happens after control char replacement (Issue #4016, #3992)"""
        from core.planner.consumer import _sanitize_for_log
        # "\n" becomes " " (1 char), so 100 newlines become 100 spaces
        result = _sanitize_for_log("\n" * 100, max_length=10)
        assert result == "          ..."  # 10 spaces + "..."


class TestSanitizeTaskId:
    """
    Tests for _sanitize_task_id() function in planner_types.py

    Issue #3840: Unit tests for sanitization functions
    Source: Gemini Code Assist (PR #3837, Comment r2679560564)
    """

    def test_empty_string(self):
        """Test sanitization of empty string"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("") == ""

    def test_normal_task_id(self):
        """Test normal task_id passes through unchanged"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("task-123") == "task-123"

    def test_newline_replacement(self):
        """Test that newlines are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("task\n123") == "task 123"

    def test_carriage_return_replacement(self):
        """Test that carriage returns are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("task\r123") == "task 123"

    def test_crlf_replacement(self):
        """Test that CRLF sequences are replaced with spaces (Issue #4016, #3992)"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("task\r\n123") == "task  123"

    def test_string_shorter_than_max_length(self):
        """Test that short strings are not truncated"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("short", max_length=100) == "short"

    def test_string_equal_to_max_length(self):
        """Test that strings exactly at max_length are not truncated"""
        from core.planner.planner_types import _sanitize_task_id
        exact_string = "a" * 100
        assert _sanitize_task_id(exact_string, max_length=100) == exact_string

    def test_string_longer_than_max_length(self):
        """Test that long strings are truncated with ellipsis"""
        from core.planner.planner_types import _sanitize_task_id
        long_string = "a" * 150
        result = _sanitize_task_id(long_string, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")

    def test_default_max_length_is_100(self):
        """Test that default max_length is 100"""
        from core.planner.planner_types import _sanitize_task_id
        long_string = "a" * 150
        result = _sanitize_task_id(long_string)
        assert len(result) == 103  # 100 + "..."

    def test_only_control_characters(self):
        """Test string with only control characters (Issue #4016, #3992)"""
        from core.planner.planner_types import _sanitize_task_id
        assert _sanitize_task_id("\n\r") == "  "

    def test_uuid_style_task_id(self):
        """Test UUID-style task_id passes through unchanged"""
        from core.planner.planner_types import _sanitize_task_id
        uuid_id = "550e8400-e29b-41d4-a716-446655440000"
        assert _sanitize_task_id(uuid_id) == uuid_id


class TestSkippedTaskDependencyResolution:
    """
    Tests for SKIPPED task handling in BasePlanConsumer.execute_plan()

    Issue #3842: Unit test for SKIPPED task dependency resolution
    Source: Gemini Code Assist (PR #3838 Review)

    Verifies that when a task returns SKIPPED status, dependent tasks
    can still proceed (SKIPPED is treated as completed for dependency resolution).
    """

    def test_skipped_task_allows_dependent_to_execute(self):
        """
        Test that a SKIPPED task allows its dependent task to execute.

        Scenario:
        1. Create a plan with task A → task B dependency
        2. Task A returns SKIPPED status
        3. Verify task B becomes executable (not blocked)
        """
        from core.planner.consumer import (
            BasePlanConsumer,
            TaskResult,
            ExecutionStatus,
        )
        from core.planner.planner_types import (
            PlannerOutput,
            TaskTree,
            TaskNode,
            TaskEdge,
            TaskType,
        )

        class SkipFirstTaskConsumer(BasePlanConsumer):
            """Consumer that SKIPs the first task and COMPLETEs others"""
            def __init__(self):
                super().__init__()
                self.executed_tasks = []

            def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
                self.executed_tasks.append(task.task_id)
                # First task (task_a) returns SKIPPED
                if task.task_id == "task_a":
                    return TaskResult(
                        task_id=task.task_id,
                        status=ExecutionStatus.SKIPPED,
                        outputs={"reason": "pre-condition not met"},
                    )
                # All other tasks complete normally
                return TaskResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.COMPLETED,
                    outputs={},
                )

        # Create plan: task_a → task_b
        plan = PlannerOutput(
            goal="Test SKIPPED dependency resolution",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="task_a", task_type=TaskType.SETUP, description="Setup task"),
                    TaskNode(task_id="task_b", task_type=TaskType.CODE, description="Code task"),
                ],
                edges=[
                    TaskEdge(from_task="task_a", to_task="task_b"),
                ],
            ),
        )

        consumer = SkipFirstTaskConsumer()
        result = consumer.execute_plan(plan)

        # Both tasks should have been executed
        assert "task_a" in consumer.executed_tasks
        assert "task_b" in consumer.executed_tasks

        # Plan should complete successfully (SKIPPED + COMPLETED = all done)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 2

        # Verify task statuses
        task_a_result = next(r for r in result.task_results if r.task_id == "task_a")
        task_b_result = next(r for r in result.task_results if r.task_id == "task_b")
        assert task_a_result.status == ExecutionStatus.SKIPPED
        assert task_b_result.status == ExecutionStatus.COMPLETED

    def test_skipped_task_in_chain_allows_all_dependents(self):
        """
        Test that SKIPPED task in a chain allows all downstream tasks.

        Scenario: A → B → C, where B is SKIPPED
        Expected: C should still execute
        """
        from core.planner.consumer import (
            BasePlanConsumer,
            TaskResult,
            ExecutionStatus,
        )
        from core.planner.planner_types import (
            PlannerOutput,
            TaskTree,
            TaskNode,
            TaskEdge,
            TaskType,
        )

        class SkipMiddleTaskConsumer(BasePlanConsumer):
            """Consumer that SKIPs the middle task"""
            def __init__(self):
                super().__init__()
                self.executed_tasks = []

            def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
                self.executed_tasks.append(task.task_id)
                if task.task_id == "task_b":
                    return TaskResult(
                        task_id=task.task_id,
                        status=ExecutionStatus.SKIPPED,
                        outputs={},
                    )
                return TaskResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.COMPLETED,
                    outputs={},
                )

        # Create plan: task_a → task_b → task_c
        plan = PlannerOutput(
            goal="Test SKIPPED in chain",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="task_a", task_type=TaskType.SETUP, description="A"),
                    TaskNode(task_id="task_b", task_type=TaskType.ANALYZE, description="B"),
                    TaskNode(task_id="task_c", task_type=TaskType.CODE, description="C"),
                ],
                edges=[
                    TaskEdge(from_task="task_a", to_task="task_b"),
                    TaskEdge(from_task="task_b", to_task="task_c"),
                ],
            ),
        )

        consumer = SkipMiddleTaskConsumer()
        result = consumer.execute_plan(plan)

        # All three tasks should have been executed
        assert consumer.executed_tasks == ["task_a", "task_b", "task_c"]
        assert result.status == ExecutionStatus.COMPLETED

    def test_multiple_skipped_tasks(self):
        """
        Test that multiple SKIPPED tasks are handled correctly.

        Scenario: A and B are parallel, both SKIPPED, C depends on both
        Expected: C should still execute
        """
        from core.planner.consumer import (
            BasePlanConsumer,
            TaskResult,
            ExecutionStatus,
        )
        from core.planner.planner_types import (
            PlannerOutput,
            TaskTree,
            TaskNode,
            TaskEdge,
            TaskType,
        )

        class SkipParallelTasksConsumer(BasePlanConsumer):
            """Consumer that SKIPs parallel tasks A and B"""
            def __init__(self):
                super().__init__()
                self.executed_tasks = []

            def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
                self.executed_tasks.append(task.task_id)
                if task.task_id in ("task_a", "task_b"):
                    return TaskResult(
                        task_id=task.task_id,
                        status=ExecutionStatus.SKIPPED,
                        outputs={},
                    )
                return TaskResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.COMPLETED,
                    outputs={},
                )

        # Create plan: task_a and task_b (parallel) → task_c
        plan = PlannerOutput(
            goal="Test multiple SKIPPED",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(task_id="task_a", task_type=TaskType.SETUP, description="A"),
                    TaskNode(task_id="task_b", task_type=TaskType.SETUP, description="B"),
                    TaskNode(task_id="task_c", task_type=TaskType.CODE, description="C"),
                ],
                edges=[
                    TaskEdge(from_task="task_a", to_task="task_c"),
                    TaskEdge(from_task="task_b", to_task="task_c"),
                ],
            ),
        )

        consumer = SkipParallelTasksConsumer()
        result = consumer.execute_plan(plan)

        # All tasks should have been executed
        assert "task_a" in consumer.executed_tasks
        assert "task_b" in consumer.executed_tasks
        assert "task_c" in consumer.executed_tasks
        assert result.status == ExecutionStatus.COMPLETED
