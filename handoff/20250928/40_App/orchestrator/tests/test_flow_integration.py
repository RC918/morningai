"""
Tests for Flow Integration Module

EPIC F Phase F-3b: Flow Integration Layer Tests

This module tests the integration layer between FlowController and AgentState.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from core.planner.flow_integration import (
    FlowIntegrationConfig,
    AgentStateUpdate,
    execute_with_flow_controller,
    create_flow_executor_node,
    validate_flow_integration_ready,
    _extract_plan_from_state,
    _map_execution_result_to_state_update,
    _convert_string_plan_to_planner_output,
    _convert_dict_plan_to_planner_output,
)
from core.planner.consumer import ExecutionResult, ExecutionStatus, TaskResult
from core.planner.planner_types import (
    CostEstimate,
    PlannerMetadata,
    PlannerOutput,
    PlanType,
    RiskLevel,
    RiskMetadata,
    TaskNode,
    TaskTree,
    TaskType,
)


class TestFlowIntegrationConfig:
    """Tests for FlowIntegrationConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = FlowIntegrationConfig()
        assert config.dry_run is False
        assert config.max_parallel == 3
        assert config.stop_on_failure is True
        assert config.timeout_seconds == 300
        assert config.max_retries == 2

    def test_custom_config(self):
        """Test custom configuration values"""
        config = FlowIntegrationConfig(
            dry_run=True,
            max_parallel=5,
            stop_on_failure=False,
            timeout_seconds=600,
            max_retries=3,
        )
        assert config.dry_run is True
        assert config.max_parallel == 5
        assert config.stop_on_failure is False
        assert config.timeout_seconds == 600
        assert config.max_retries == 3


class TestValidateFlowIntegrationReady:
    """Tests for validate_flow_integration_ready function"""

    def test_valid_state_with_string_plan(self):
        """Test validation passes with valid state containing string plan"""
        state = {
            "plan": ["Step 1: Analyze code", "Step 2: Make changes"],
            "goal": "Fix the bug",
        }
        assert validate_flow_integration_ready(state) is True

    def test_valid_state_with_dict_plan(self):
        """Test validation passes with valid state containing dict plan"""
        state = {
            "plan": [{"task": "analyze", "description": "Analyze code"}],
            "goal": "Fix the bug",
        }
        assert validate_flow_integration_ready(state) is True

    def test_missing_plan(self):
        """Test validation fails when plan is missing"""
        state = {"goal": "Fix the bug"}
        assert validate_flow_integration_ready(state) is False

    def test_empty_plan(self):
        """Test validation fails when plan is empty"""
        state = {"plan": [], "goal": "Fix the bug"}
        assert validate_flow_integration_ready(state) is False

    def test_missing_goal(self):
        """Test validation fails when goal is missing"""
        state = {"plan": ["Step 1"]}
        assert validate_flow_integration_ready(state) is False

    def test_empty_goal(self):
        """Test validation fails when goal is empty"""
        state = {"plan": ["Step 1"], "goal": ""}
        assert validate_flow_integration_ready(state) is False

    def test_plan_not_list(self):
        """Test validation fails when plan is not a list"""
        state = {"plan": "Step 1", "goal": "Fix the bug"}
        assert validate_flow_integration_ready(state) is False


class TestExtractPlanFromState:
    """Tests for _extract_plan_from_state function"""

    def test_extract_llm_planner_output(self):
        """Test extraction of LLM planner output (list of strings)"""
        state = {
            "plan": ["Step 1: Analyze code", "Step 2: Make changes"],
            "goal": "Fix the bug",
            "repo": "owner/repo",
        }
        result = _extract_plan_from_state(state)
        assert result is not None
        assert isinstance(result, PlannerOutput)
        assert len(result.task_tree.nodes) == 2

    def test_extract_task_planner_output(self):
        """Test extraction of task planner output (list of dicts)"""
        state = {
            "plan": [
                {"task": "analyze", "description": "Analyze code"},
                {"task": "code", "description": "Make changes"},
            ],
            "goal": "Fix the bug",
            "repo": "owner/repo",
        }
        result = _extract_plan_from_state(state)
        assert result is not None
        assert isinstance(result, PlannerOutput)

    def test_extract_empty_plan(self):
        """Test extraction returns None for empty plan"""
        state = {"plan": [], "goal": "Fix the bug"}
        result = _extract_plan_from_state(state)
        assert result is None

    def test_extract_no_plan(self):
        """Test extraction returns None when no plan in state"""
        state = {"goal": "Fix the bug"}
        result = _extract_plan_from_state(state)
        assert result is None


class TestMapExecutionResultToStateUpdate:
    """Tests for _map_execution_result_to_state_update function"""

    def _create_test_plan(self) -> PlannerOutput:
        """Create a test PlannerOutput for testing"""
        nodes = [
            TaskNode(
                task_id="task-1",
                task_type=TaskType.ANALYZE,
                description="Analyze code",
                estimated_duration_minutes=5,
            ),
            TaskNode(
                task_id="task-2",
                task_type=TaskType.CODE,
                description="Make changes",
                estimated_duration_minutes=10,
            ),
        ]
        task_tree = TaskTree(nodes=nodes, edges=[])
        return PlannerOutput(
            plan_id="test-plan",
            goal="Fix the bug",
            plan_type=PlanType.DETAILED,
            task_tree=task_tree,
            risk_metadata=RiskMetadata(overall_risk=RiskLevel.LOW),
            cost_estimate=CostEstimate(),
            planner_metadata=PlannerMetadata(planner_type="test"),
        )

    def test_map_completed_result(self):
        """Test mapping a completed execution result"""
        plan = self._create_test_plan()
        result = ExecutionResult(
            plan_id="test-plan",
            status=ExecutionStatus.COMPLETED,
            task_results=[
                TaskResult(
                    task_id="task-1",
                    status=ExecutionStatus.COMPLETED,
                    outputs={"result": "analyzed"},
                ),
                TaskResult(
                    task_id="task-2",
                    status=ExecutionStatus.COMPLETED,
                    outputs={"result": "coded"},
                ),
            ],
            total_duration_minutes=15,
        )

        update = _map_execution_result_to_state_update(result, plan)

        assert update["flow_execution_status"] == "completed"
        assert update["current_step"] == 2
        assert update["flow_completed_tasks"] == ["task-1", "task-2"]
        assert update["flow_failed_tasks"] == []
        assert update["error"] == ""
        assert update["final_result"]["status"] == "success"
        assert update["final_result"]["completed_tasks"] == 2

    def test_map_failed_result(self):
        """Test mapping a failed execution result"""
        plan = self._create_test_plan()
        result = ExecutionResult(
            plan_id="test-plan",
            status=ExecutionStatus.FAILED,
            task_results=[
                TaskResult(
                    task_id="task-1",
                    status=ExecutionStatus.COMPLETED,
                    outputs={"result": "analyzed"},
                ),
                TaskResult(
                    task_id="task-2",
                    status=ExecutionStatus.FAILED,
                    outputs={},
                    error_message="Task failed",
                ),
            ],
            total_duration_minutes=10,
            error_summary="Task task-2 failed: Task failed",
        )

        update = _map_execution_result_to_state_update(result, plan)

        assert update["flow_execution_status"] == "failed"
        assert update["current_step"] == 1
        assert update["flow_completed_tasks"] == ["task-1"]
        assert update["flow_failed_tasks"] == ["task-2"]
        assert "failed" in update["error"].lower()
        assert update["final_result"]["status"] == "failed"
        assert update["final_result"]["failed_tasks"] == 1

    def test_map_result_with_skipped_tasks(self):
        """Test mapping a result with skipped tasks"""
        plan = self._create_test_plan()
        result = ExecutionResult(
            plan_id="test-plan",
            status=ExecutionStatus.FAILED,
            task_results=[
                TaskResult(
                    task_id="task-1",
                    status=ExecutionStatus.FAILED,
                    outputs={},
                    error_message="Task failed",
                ),
                TaskResult(
                    task_id="task-2",
                    status=ExecutionStatus.SKIPPED,
                    outputs={},
                    error_message="Skipped due to failed dependency",
                ),
            ],
            total_duration_minutes=5,
            error_summary="Task task-1 failed",
        )

        update = _map_execution_result_to_state_update(result, plan)

        assert update["flow_execution_status"] == "failed"
        assert update["flow_completed_tasks"] == []
        assert update["flow_failed_tasks"] == ["task-1"]
        assert update["final_result"]["skipped_tasks"] == 1


class TestExecuteWithFlowController:
    """Tests for execute_with_flow_controller function"""

    def test_execute_with_valid_state(self):
        """Test execution with valid state"""
        state = {
            "plan": ["Step 1: Analyze code", "Step 2: Make changes"],
            "goal": "Fix the bug",
            "repo": "owner/repo",
            "trace_id": "test-trace",
        }

        with patch("core.planner.flow_integration.create_flow_controller") as mock_controller:
            mock_result = ExecutionResult(
                plan_id="test-plan",
                status=ExecutionStatus.COMPLETED,
                task_results=[
                    TaskResult(
                        task_id="task-1",
                        status=ExecutionStatus.COMPLETED,
                        outputs={},
                    ),
                ],
                total_duration_minutes=5,
            )
            mock_controller.return_value.execute_plan.return_value = mock_result

            update = execute_with_flow_controller(state)

            assert update["flow_execution_status"] == "completed"
            mock_controller.return_value.execute_plan.assert_called_once()

    def test_execute_with_no_plan(self):
        """Test execution returns error when no plan in state"""
        state = {"goal": "Fix the bug", "trace_id": "test-trace"}

        update = execute_with_flow_controller(state)

        assert update["flow_execution_status"] == "failed"
        assert "No valid plan" in update.get("error", "")

    def test_execute_with_custom_config(self):
        """Test execution with custom configuration"""
        state = {
            "plan": ["Step 1: Analyze code"],
            "goal": "Fix the bug",
            "repo": "owner/repo",
            "trace_id": "test-trace",
        }
        config = FlowIntegrationConfig(dry_run=True, max_parallel=5)

        with patch("core.planner.flow_integration.create_flow_controller") as mock_controller:
            mock_result = ExecutionResult(
                plan_id="test-plan",
                status=ExecutionStatus.COMPLETED,
                task_results=[],
                total_duration_minutes=0,
            )
            mock_controller.return_value.execute_plan.return_value = mock_result

            execute_with_flow_controller(state, config)

            mock_controller.assert_called_once()
            call_kwargs = mock_controller.call_args[1]
            assert call_kwargs["max_parallel"] == 5

    def test_execute_handles_exception(self):
        """Test execution handles exceptions gracefully"""
        state = {
            "plan": ["Step 1: Analyze code"],
            "goal": "Fix the bug",
            "repo": "owner/repo",
            "trace_id": "test-trace",
        }

        with patch("core.planner.flow_integration.create_flow_controller") as mock_controller:
            mock_controller.return_value.execute_plan.side_effect = RuntimeError("Test error")

            update = execute_with_flow_controller(state)

            assert update["flow_execution_status"] == "failed"
            assert "internal error" in update.get("error", "").lower()


class TestCreateFlowExecutorNode:
    """Tests for create_flow_executor_node function"""

    def test_create_node_returns_callable(self):
        """Test that create_flow_executor_node returns a callable"""
        node = create_flow_executor_node()
        assert callable(node)

    def test_node_executes_flow(self):
        """Test that the created node executes flow correctly"""
        node = create_flow_executor_node()
        state = {
            "plan": ["Step 1: Analyze code"],
            "goal": "Fix the bug",
            "repo": "owner/repo",
            "trace_id": "test-trace",
        }

        with patch("core.planner.flow_integration.create_flow_controller") as mock_controller:
            mock_result = ExecutionResult(
                plan_id="test-plan",
                status=ExecutionStatus.COMPLETED,
                task_results=[],
                total_duration_minutes=0,
            )
            mock_controller.return_value.execute_plan.return_value = mock_result

            result = node(state)

            assert isinstance(result, dict)
            assert result.get("flow_execution_status") == "completed"

    def test_node_with_custom_config(self):
        """Test node creation with custom config"""
        config = FlowIntegrationConfig(dry_run=True)
        node = create_flow_executor_node(config)

        state = {
            "plan": ["Step 1"],
            "goal": "Test",
            "repo": "owner/repo",
            "trace_id": "test",
        }

        with patch("core.planner.flow_integration.create_flow_controller") as mock_controller:
            with patch("core.planner.flow_integration.AgentTaskExecutor") as mock_executor:
                mock_result = ExecutionResult(
                    plan_id="test",
                    status=ExecutionStatus.COMPLETED,
                    task_results=[],
                    total_duration_minutes=0,
                )
                mock_controller.return_value.execute_plan.return_value = mock_result

                node(state)

                mock_executor.assert_called_once()
                call_kwargs = mock_executor.call_args[1]
                assert call_kwargs["config"].dry_run is True


class TestIntegrationWithRealComponents:
    """Integration tests with real FlowController and AgentTaskExecutor"""

    def test_end_to_end_dry_run(self):
        """Test end-to-end execution in dry_run mode"""
        state = {
            "plan": [
                "Step 1: Analyze the codebase",
                "Step 2: Implement the fix",
                "Step 3: Write tests",
            ],
            "goal": "Fix the authentication bug",
            "repo": "owner/repo",
            "trace_id": "integration-test",
        }
        config = FlowIntegrationConfig(dry_run=True)

        update = execute_with_flow_controller(state, config)

        assert update["flow_execution_status"] == "completed"
        assert len(update["flow_completed_tasks"]) == 3
        assert len(update["flow_failed_tasks"]) == 0
        assert update["final_result"]["status"] == "success"

    def test_end_to_end_with_dict_plan(self):
        """Test end-to-end execution with dict plan format"""
        state = {
            "plan": [
                {"task": "analyze", "description": "Analyze code"},
                {"task": "code", "description": "Make changes"},
            ],
            "goal": "Implement feature",
            "repo": "owner/repo",
            "trace_id": "integration-test-dict",
        }
        config = FlowIntegrationConfig(dry_run=True)

        update = execute_with_flow_controller(state, config)

        assert update["flow_execution_status"] == "completed"
        assert update["final_result"]["status"] == "success"
