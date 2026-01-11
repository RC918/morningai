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
