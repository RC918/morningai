"""
Unit tests for Planner Flow Controller v3 (Phase F-2)

Tests the FlowController that consumes PlannerOutput and orchestrates
task execution based on flow templates and DAG dependencies.

EPIC F Phase F-2: Flow Controller Integration
"""

from unittest.mock import MagicMock

from core.planner.flow_controller import (
    FlowTemplate,
    FlowStage,
    FlowState,
    FlowController,
    DefaultTaskExecutor,
    create_flow_controller,
    FLOW_DEFINITIONS,
)
from core.planner.planner_types import (
    PlannerOutput,
    PlanType,
    TaskNode,
    TaskEdge,
    TaskTree,
    TaskType,
    EdgeType,
)
from core.planner.consumer import (
    ExecutionStatus,
    TaskResult,
)


class TestFlowTemplate:
    """Tests for FlowTemplate enum"""

    def test_flow_template_values(self):
        """Test that all expected flow templates exist"""
        assert FlowTemplate.FULL_PIPELINE.value == "full_pipeline"
        assert FlowTemplate.REVIEW_HEAVY.value == "review_heavy"
        assert FlowTemplate.TEST_HEAVY.value == "test_heavy"
        assert FlowTemplate.DOC_ONLY.value == "doc_only"
        assert FlowTemplate.ANALYSIS_ONLY.value == "analysis_only"
        assert FlowTemplate.CODE_ONLY.value == "code_only"


class TestFlowDefinitions:
    """Tests for flow template definitions"""

    def test_all_templates_have_definitions(self):
        """Test that all flow templates have definitions"""
        for template in FlowTemplate:
            assert template in FLOW_DEFINITIONS

    def test_full_pipeline_definition(self):
        """Test full_pipeline flow definition"""
        flow_def = FLOW_DEFINITIONS[FlowTemplate.FULL_PIPELINE]
        assert flow_def.template == FlowTemplate.FULL_PIPELINE
        assert flow_def.allow_parallel is True
        assert flow_def.require_review is True
        assert flow_def.require_tests is True
        assert len(flow_def.stages) > 0

    def test_doc_only_definition(self):
        """Test doc_only flow definition"""
        flow_def = FLOW_DEFINITIONS[FlowTemplate.DOC_ONLY]
        assert flow_def.template == FlowTemplate.DOC_ONLY
        assert flow_def.allow_parallel is False
        assert flow_def.require_review is True
        assert flow_def.require_tests is False

    def test_analysis_only_definition(self):
        """Test analysis_only flow definition"""
        flow_def = FLOW_DEFINITIONS[FlowTemplate.ANALYSIS_ONLY]
        assert flow_def.template == FlowTemplate.ANALYSIS_ONLY
        assert flow_def.require_review is False
        assert flow_def.require_tests is False


class TestFlowState:
    """Tests for FlowState dataclass"""

    def test_initial_state(self):
        """Test initial flow state"""
        state = FlowState(plan_id="test-plan")
        assert state.plan_id == "test-plan"
        assert state.current_stage == ""
        assert len(state.completed_tasks) == 0
        assert len(state.failed_tasks) == 0
        assert len(state.skipped_tasks) == 0

    def test_mark_completed(self):
        """Test marking task as completed"""
        state = FlowState(plan_id="test-plan")
        state.mark_completed("task-1")
        assert "task-1" in state.completed_tasks

    def test_mark_failed(self):
        """Test marking task as failed"""
        state = FlowState(plan_id="test-plan")
        state.mark_failed("task-1")
        assert "task-1" in state.failed_tasks

    def test_mark_skipped(self):
        """Test marking task as skipped"""
        state = FlowState(plan_id="test-plan")
        state.mark_skipped("task-1")
        assert "task-1" in state.skipped_tasks
        # Skipped tasks should also be in completed for dependency resolution
        assert "task-1" in state.completed_tasks

    def test_stage_iterations(self):
        """Test stage iteration tracking"""
        state = FlowState(plan_id="test-plan")
        assert state.get_stage_iteration("review") == 0
        assert state.increment_stage_iteration("review") == 1
        assert state.get_stage_iteration("review") == 1
        assert state.increment_stage_iteration("review") == 2


class TestDefaultTaskExecutor:
    """Tests for DefaultTaskExecutor"""

    def test_execute_returns_completed(self):
        """Test that default executor returns completed status"""
        executor = DefaultTaskExecutor()
        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Test task",
        )
        result = executor.execute(task, {})
        assert result.status == ExecutionStatus.COMPLETED
        assert result.task_id == "task-1"
        assert result.outputs["executed"] is True


class TestFlowController:
    """Tests for FlowController"""

    def _create_simple_plan(
        self,
        flow_template: str = "full_pipeline",
        task_count: int = 3,
    ) -> PlannerOutput:
        """Helper to create a simple test plan"""
        nodes = [
            TaskNode(
                task_id=f"task-{i}",
                task_type=TaskType.CODE,
                description=f"Task {i}",
            )
            for i in range(task_count)
        ]
        # Create linear dependencies
        edges = [
            TaskEdge(
                from_task=f"task-{i}",
                to_task=f"task-{i + 1}",
                edge_type=EdgeType.DEPENDS_ON,
            )
            for i in range(task_count - 1)
        ]
        return PlannerOutput(
            plan_id="test-plan",
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            flow_template=flow_template,
        )

    def _create_multi_type_plan(self) -> PlannerOutput:
        """Helper to create a plan with multiple task types"""
        nodes = [
            TaskNode(task_id="setup-1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="analyze-1", task_type=TaskType.ANALYZE, description="Analyze"),
            TaskNode(task_id="code-1", task_type=TaskType.CODE, description="Code"),
            TaskNode(task_id="test-1", task_type=TaskType.TEST, description="Test"),
            TaskNode(task_id="review-1", task_type=TaskType.REVIEW, description="Review"),
        ]
        edges = [
            TaskEdge(from_task="setup-1", to_task="analyze-1", edge_type=EdgeType.DEPENDS_ON),
            TaskEdge(from_task="analyze-1", to_task="code-1", edge_type=EdgeType.DEPENDS_ON),
            TaskEdge(from_task="code-1", to_task="test-1", edge_type=EdgeType.DEPENDS_ON),
            TaskEdge(from_task="test-1", to_task="review-1", edge_type=EdgeType.DEPENDS_ON),
        ]
        return PlannerOutput(
            plan_id="multi-type-plan",
            plan_type=PlanType.DETAILED,
            goal="Multi-type test",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            flow_template="full_pipeline",
        )

    def test_create_flow_controller(self):
        """Test FlowController creation"""
        controller = FlowController()
        assert controller is not None
        assert controller.max_parallel == 3
        assert controller.stop_on_failure is True

    def test_create_flow_controller_with_params(self):
        """Test FlowController creation with custom parameters"""
        controller = FlowController(max_parallel=5, stop_on_failure=False)
        assert controller.max_parallel == 5
        assert controller.stop_on_failure is False

    def test_factory_function(self):
        """Test create_flow_controller factory function"""
        controller = create_flow_controller(max_parallel=2)
        assert isinstance(controller, FlowController)
        assert controller.max_parallel == 2

    def test_get_flow_definition_valid(self):
        """Test getting flow definition for valid template"""
        controller = FlowController()
        flow_def = controller.get_flow_definition("full_pipeline")
        assert flow_def.template == FlowTemplate.FULL_PIPELINE

    def test_get_flow_definition_invalid(self):
        """Test getting flow definition for invalid template defaults to full_pipeline"""
        controller = FlowController()
        flow_def = controller.get_flow_definition("invalid_template")
        assert flow_def.template == FlowTemplate.FULL_PIPELINE

    def test_execute_plan_simple(self):
        """Test executing a simple plan"""
        controller = FlowController()
        plan = self._create_simple_plan(task_count=3)
        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert result.plan_id == "test-plan"
        assert len(result.task_results) == 3

    def test_execute_plan_with_dependencies(self):
        """Test executing a plan with dependencies"""
        controller = FlowController()
        plan = self._create_multi_type_plan()
        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 5

    def test_execute_plan_invalid_plan(self):
        """Test executing an invalid plan"""
        controller = FlowController()
        # Create plan with cycle
        nodes = [
            TaskNode(task_id="task-1", task_type=TaskType.CODE, description="Task 1"),
            TaskNode(task_id="task-2", task_type=TaskType.CODE, description="Task 2"),
        ]
        edges = [
            TaskEdge(from_task="task-1", to_task="task-2", edge_type=EdgeType.DEPENDS_ON),
            TaskEdge(from_task="task-2", to_task="task-1", edge_type=EdgeType.DEPENDS_ON),
        ]
        plan = PlannerOutput(
            plan_id="invalid-plan",
            goal="Invalid",
            task_tree=TaskTree(nodes=nodes, edges=edges),
        )
        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.FAILED
        assert "Cycle detected" in result.error_summary

    def test_execute_plan_empty_goal(self):
        """Test executing a plan with empty goal"""
        controller = FlowController()
        plan = PlannerOutput(
            plan_id="no-goal-plan",
            goal="",
            task_tree=TaskTree(nodes=[
                TaskNode(task_id="task-1", task_type=TaskType.CODE, description="Task")
            ]),
        )
        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.FAILED
        assert "goal" in result.error_summary.lower()

    def test_execute_plan_with_custom_executor(self):
        """Test executing a plan with custom task executor"""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = TaskResult(
            task_id="task-0",
            status=ExecutionStatus.COMPLETED,
            outputs={"custom": True},
        )

        controller = FlowController(task_executor=mock_executor)
        plan = self._create_simple_plan(task_count=1)
        result = controller.execute_plan(plan)

        assert result.status == ExecutionStatus.COMPLETED
        mock_executor.execute.assert_called()

    def test_execute_plan_with_failure(self):
        """Test executing a plan where a task fails"""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = TaskResult(
            task_id="task-0",
            status=ExecutionStatus.FAILED,
            outputs={},
            error_message="Task failed",
        )

        controller = FlowController(task_executor=mock_executor, stop_on_failure=True)
        plan = self._create_simple_plan(task_count=3)
        result = controller.execute_plan(plan)

        assert result.status == ExecutionStatus.FAILED
        assert "failed" in result.error_summary.lower()

    def test_execute_plan_continue_on_failure(self):
        """Test executing a plan that continues on failure"""
        executed_tasks = []

        def mock_execute(task, context):
            executed_tasks.append(task.task_id)
            if task.task_id == "task-0":
                return TaskResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.FAILED,
                    outputs={},
                    error_message="First task failed",
                )
            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                outputs={},
            )

        mock_executor = MagicMock()
        mock_executor.execute.side_effect = mock_execute

        controller = FlowController(task_executor=mock_executor, stop_on_failure=False)
        # Create plan without dependencies so all tasks can execute
        nodes = [
            TaskNode(task_id=f"task-{i}", task_type=TaskType.CODE, description=f"Task {i}")
            for i in range(3)
        ]
        plan = PlannerOutput(
            plan_id="test-plan",
            goal="Test",
            task_tree=TaskTree(nodes=nodes, edges=[]),
        )
        controller.execute_plan(plan)

        # Should have attempted all 3 unique tasks (may be called multiple times due to stage iteration)
        unique_tasks = set(executed_tasks)
        assert len(unique_tasks) == 3
        assert "task-0" in unique_tasks
        assert "task-1" in unique_tasks
        assert "task-2" in unique_tasks

    def test_execute_plan_skip_dependent_on_failed(self):
        """Test that tasks dependent on failed tasks are skipped (not executed)"""
        executed_tasks = []

        def mock_execute(task, context):
            executed_tasks.append(task.task_id)
            if task.task_id == "task-A":
                return TaskResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.FAILED,
                    outputs={},
                    error_message="Task A failed",
                )
            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                outputs={},
            )

        mock_executor = MagicMock()
        mock_executor.execute.side_effect = mock_execute

        controller = FlowController(task_executor=mock_executor, stop_on_failure=False)

        # Create plan with dependencies: A -> B -> C
        # If A fails, B and C should be skipped (not executed)
        nodes = [
            TaskNode(task_id="task-A", task_type=TaskType.CODE, description="Task A"),
            TaskNode(task_id="task-B", task_type=TaskType.CODE, description="Task B"),
            TaskNode(task_id="task-C", task_type=TaskType.CODE, description="Task C"),
        ]
        edges = [
            TaskEdge(from_task="task-A", to_task="task-B"),
            TaskEdge(from_task="task-B", to_task="task-C"),
        ]
        plan = PlannerOutput(
            plan_id="test-plan",
            goal="Test failed dependency skipping",
            task_tree=TaskTree(nodes=nodes, edges=edges),
        )
        result = controller.execute_plan(plan)

        # Only task-A should have been executed (B and C should be skipped)
        assert "task-A" in executed_tasks
        assert "task-B" not in executed_tasks
        assert "task-C" not in executed_tasks

        # Verify B and C were marked as SKIPPED
        task_b_result = next((r for r in result.task_results if r.task_id == "task-B"), None)
        task_c_result = next((r for r in result.task_results if r.task_id == "task-C"), None)
        assert task_b_result is not None
        assert task_b_result.status == ExecutionStatus.SKIPPED
        assert "failed dependency" in task_b_result.error_message.lower()
        assert task_c_result is not None
        assert task_c_result.status == ExecutionStatus.SKIPPED

    def test_flow_template_routing(self):
        """Test that different flow templates are handled correctly"""
        controller = FlowController()

        for template in ["full_pipeline", "review_heavy", "test_heavy", "doc_only"]:
            plan = self._create_simple_plan(flow_template=template, task_count=2)
            result = controller.execute_plan(plan)
            assert result.status == ExecutionStatus.COMPLETED

    def test_should_skip_stage_optional(self):
        """Test stage skipping for optional stages"""
        controller = FlowController()
        plan = self._create_simple_plan()  # No DOCUMENT tasks
        flow_def = FLOW_DEFINITIONS[FlowTemplate.FULL_PIPELINE]

        # Find the document stage (optional)
        doc_stage = next(
            (s for s in flow_def.stages if s.name == "document"),
            None
        )
        if doc_stage:
            assert controller.should_skip_stage(plan, doc_stage, flow_def) is True

    def test_get_tasks_for_stage(self):
        """Test getting tasks for a specific stage"""
        controller = FlowController()
        plan = self._create_multi_type_plan()
        state = FlowState(plan_id=plan.plan_id)

        # Get setup stage
        setup_stage = FlowStage(name="setup", task_types=[TaskType.SETUP])
        tasks = controller.get_tasks_for_stage(plan, setup_stage, state)

        assert len(tasks) == 1
        assert tasks[0].task_id == "setup-1"


class TestFlowControllerIntegration:
    """Integration tests for FlowController"""

    def test_full_pipeline_execution(self):
        """Test full pipeline execution with all task types"""
        controller = FlowController()

        nodes = [
            TaskNode(task_id="setup", task_type=TaskType.SETUP, description="Setup env"),
            TaskNode(task_id="analyze", task_type=TaskType.ANALYZE, description="Analyze code"),
            TaskNode(task_id="code", task_type=TaskType.CODE, description="Write code"),
            TaskNode(task_id="test", task_type=TaskType.TEST, description="Run tests"),
            TaskNode(task_id="review", task_type=TaskType.REVIEW, description="Code review"),
            TaskNode(task_id="verify", task_type=TaskType.VERIFY, description="Verify"),
        ]
        edges = [
            TaskEdge(from_task="setup", to_task="analyze"),
            TaskEdge(from_task="analyze", to_task="code"),
            TaskEdge(from_task="code", to_task="test"),
            TaskEdge(from_task="test", to_task="review"),
            TaskEdge(from_task="review", to_task="verify"),
        ]

        plan = PlannerOutput(
            plan_id="full-pipeline-test",
            goal="Full pipeline test",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            flow_template="full_pipeline",
        )

        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 6
        assert result.get_completed_count() == 6

    def test_parallel_tasks_execution(self):
        """Test execution of parallel tasks (no dependencies)"""
        controller = FlowController()

        # Create tasks with no dependencies (can run in parallel)
        nodes = [
            TaskNode(task_id=f"task-{i}", task_type=TaskType.CODE, description=f"Task {i}")
            for i in range(5)
        ]

        plan = PlannerOutput(
            plan_id="parallel-test",
            goal="Parallel execution test",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            flow_template="code_only",
        )

        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 5

    def test_diamond_dependency_execution(self):
        """Test execution with diamond dependency pattern"""
        controller = FlowController()

        # Diamond pattern: A -> B, A -> C, B -> D, C -> D
        nodes = [
            TaskNode(task_id="A", task_type=TaskType.SETUP, description="Start"),
            TaskNode(task_id="B", task_type=TaskType.CODE, description="Branch 1"),
            TaskNode(task_id="C", task_type=TaskType.CODE, description="Branch 2"),
            TaskNode(task_id="D", task_type=TaskType.VERIFY, description="Merge"),
        ]
        edges = [
            TaskEdge(from_task="A", to_task="B"),
            TaskEdge(from_task="A", to_task="C"),
            TaskEdge(from_task="B", to_task="D"),
            TaskEdge(from_task="C", to_task="D"),
        ]

        plan = PlannerOutput(
            plan_id="diamond-test",
            goal="Diamond dependency test",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            flow_template="full_pipeline",
        )

        result = controller.execute_plan(plan)
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 4

        # Verify execution order: A must be first, D must be last
        task_order = [r.task_id for r in result.task_results]
        assert task_order[0] == "A"
        assert task_order[-1] == "D"
