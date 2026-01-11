"""
Tests for AgentTaskExecutor - Phase F-3: Orchestrator Integration

Tests the AgentTaskExecutor class that bridges FlowController with agent dispatch.
"""

from unittest.mock import MagicMock

from core.planner.agent_task_executor import (
    AgentTaskExecutor,
    AgentTaskExecutorConfig,
    DefaultAgentDispatcher,
    create_agent_task_executor,
)
from core.planner.consumer import ExecutionStatus
from core.planner.planner_types import TaskNode, TaskType


class TestAgentTaskExecutorConfig:
    """Tests for AgentTaskExecutorConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AgentTaskExecutorConfig()
        assert config.dry_run is False
        assert config.timeout_seconds == 300
        assert config.retry_count == 0
        assert config.enable_metrics is True

    def test_custom_config(self):
        """Test custom configuration values"""
        config = AgentTaskExecutorConfig(
            dry_run=True,
            timeout_seconds=600,
            retry_count=3,
            enable_metrics=False,
        )
        assert config.dry_run is True
        assert config.timeout_seconds == 600
        assert config.retry_count == 3
        assert config.enable_metrics is False


class TestDefaultAgentDispatcher:
    """Tests for DefaultAgentDispatcher"""

    def test_dispatch_code_task(self):
        """Test dispatching CODE task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="code-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        result = dispatcher.dispatch(TaskType.CODE, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "DevAgent"

    def test_dispatch_review_task(self):
        """Test dispatching REVIEW task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="review-1",
            task_type=TaskType.REVIEW,
            description="Review code",
        )
        result = dispatcher.dispatch(TaskType.REVIEW, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "ReviewerAgent"

    def test_dispatch_test_task(self):
        """Test dispatching TEST task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="test-1",
            task_type=TaskType.TEST,
            description="Run tests",
        )
        result = dispatcher.dispatch(TaskType.TEST, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "CIMonitor"

    def test_dispatch_analyze_task(self):
        """Test dispatching ANALYZE task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="analyze-1",
            task_type=TaskType.ANALYZE,
            description="Analyze code",
        )
        result = dispatcher.dispatch(TaskType.ANALYZE, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "AnalysisAgent"

    def test_dispatch_document_task(self):
        """Test dispatching DOCUMENT task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="doc-1",
            task_type=TaskType.DOCUMENT,
            description="Write docs",
        )
        result = dispatcher.dispatch(TaskType.DOCUMENT, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "DocAgent"

    def test_dispatch_deploy_task(self):
        """Test dispatching DEPLOY task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="deploy-1",
            task_type=TaskType.DEPLOY,
            description="Deploy app",
        )
        result = dispatcher.dispatch(TaskType.DEPLOY, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "DeployAgent"

    def test_dispatch_verify_task(self):
        """Test dispatching VERIFY task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="verify-1",
            task_type=TaskType.VERIFY,
            description="Verify deployment",
        )
        result = dispatcher.dispatch(TaskType.VERIFY, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "VerifyAgent"

    def test_dispatch_setup_task(self):
        """Test dispatching SETUP task"""
        dispatcher = DefaultAgentDispatcher()
        task = TaskNode(
            task_id="setup-1",
            task_type=TaskType.SETUP,
            description="Setup environment",
        )
        result = dispatcher.dispatch(TaskType.SETUP, task, {})
        assert result["status"] == "completed"
        assert result["agent"] == "SetupAgent"

    def test_dispatch_with_custom_handler(self):
        """Test dispatching with custom handler"""
        custom_result = {"custom": True, "status": "custom_completed"}

        def custom_handler(task, context):
            return custom_result

        dispatcher = DefaultAgentDispatcher(
            custom_handlers={TaskType.CODE: custom_handler}
        )
        task = TaskNode(
            task_id="code-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        result = dispatcher.dispatch(TaskType.CODE, task, {})
        assert result == custom_result

    def test_dispatch_with_agent_state(self):
        """Test dispatcher with agent state"""
        agent_state = {"trace_id": "test-123", "repo": "test/repo"}
        dispatcher = DefaultAgentDispatcher(agent_state=agent_state)
        assert dispatcher.agent_state == agent_state


class TestAgentTaskExecutor:
    """Tests for AgentTaskExecutor"""

    def test_create_executor(self):
        """Test creating executor with defaults"""
        executor = AgentTaskExecutor()
        assert executor.agent_state == {}
        assert executor.config.dry_run is False
        assert executor.execution_count == 0

    def test_create_executor_with_state(self):
        """Test creating executor with agent state"""
        state = {"trace_id": "test-123"}
        executor = AgentTaskExecutor(agent_state=state)
        assert executor.agent_state == state

    def test_create_executor_with_config(self):
        """Test creating executor with custom config"""
        config = AgentTaskExecutorConfig(dry_run=True)
        executor = AgentTaskExecutor(config=config)
        assert executor.config.dry_run is True

    def test_execute_task_success(self):
        """Test successful task execution"""
        executor = AgentTaskExecutor()
        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        context = {"plan_id": "plan-1"}

        result = executor.execute(task, context)

        assert result.task_id == "task-1"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs is not None
        assert result.started_at is not None
        assert result.completed_at is not None
        assert executor.execution_count == 1

    def test_execute_task_dry_run(self):
        """Test dry-run execution"""
        config = AgentTaskExecutorConfig(dry_run=True)
        executor = AgentTaskExecutor(config=config)
        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        context = {"plan_id": "plan-1"}

        result = executor.execute(task, context)

        assert result.task_id == "task-1"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["dry_run"] is True
        assert result.outputs["task_type"] == "code"

    def test_execute_task_failure(self):
        """Test task execution failure"""
        # Create a dispatcher that raises an exception
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.side_effect = Exception("Test error")

        executor = AgentTaskExecutor(dispatcher=mock_dispatcher)
        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        context = {"plan_id": "plan-1"}

        result = executor.execute(task, context)

        assert result.task_id == "task-1"
        assert result.status == ExecutionStatus.FAILED
        # Security: error message should not expose raw exception details
        assert "internal error" in result.error_message
        assert "Test error" not in result.error_message

    def test_execute_multiple_tasks(self):
        """Test executing multiple tasks"""
        executor = AgentTaskExecutor()

        for i in range(3):
            task = TaskNode(
                task_id=f"task-{i}",
                task_type=TaskType.CODE,
                description=f"Task {i}",
            )
            executor.execute(task, {})

        assert executor.execution_count == 3

    def test_execute_with_task_inputs_outputs(self):
        """Test execution with task inputs and outputs"""
        executor = AgentTaskExecutor()
        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Write code",
            inputs={"file": "test.py"},
            outputs=["code_changes"],
        )
        context = {"plan_id": "plan-1"}

        result = executor.execute(task, context)

        assert result.status == ExecutionStatus.COMPLETED


class TestCreateAgentTaskExecutor:
    """Tests for create_agent_task_executor factory function"""

    def test_create_with_defaults(self):
        """Test factory with default parameters"""
        executor = create_agent_task_executor()
        assert executor.config.dry_run is False
        assert executor.agent_state == {}

    def test_create_with_dry_run(self):
        """Test factory with dry_run enabled"""
        executor = create_agent_task_executor(dry_run=True)
        assert executor.config.dry_run is True

    def test_create_with_agent_state(self):
        """Test factory with agent state"""
        state = {"trace_id": "test-123"}
        executor = create_agent_task_executor(agent_state=state)
        assert executor.agent_state == state

    def test_create_with_custom_handlers(self):
        """Test factory with custom handlers"""
        custom_result = {"custom": True}

        def custom_handler(task, context):
            return custom_result

        executor = create_agent_task_executor(
            custom_handlers={TaskType.CODE: custom_handler}
        )

        task = TaskNode(
            task_id="task-1",
            task_type=TaskType.CODE,
            description="Write code",
        )
        result = executor.execute(task, {})

        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs == custom_result


class TestAgentTaskExecutorIntegration:
    """Integration tests for AgentTaskExecutor with FlowController"""

    def test_executor_with_flow_controller(self):
        """Test using AgentTaskExecutor with FlowController"""
        from core.planner.flow_controller import FlowController
        from core.planner.planner_types import (
            PlannerOutput,
            TaskTree,
            TaskEdge,
        )

        # Create executor
        executor = create_agent_task_executor(dry_run=True)

        # Create FlowController with our executor
        controller = FlowController(task_executor=executor)

        # Create a simple plan
        nodes = [
            TaskNode(task_id="setup", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="code", task_type=TaskType.CODE, description="Code"),
            TaskNode(task_id="verify", task_type=TaskType.VERIFY, description="Verify"),
        ]
        edges = [
            TaskEdge(from_task="setup", to_task="code"),
            TaskEdge(from_task="code", to_task="verify"),
        ]
        plan = PlannerOutput(
            plan_id="test-plan",
            goal="Test integration",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            flow_template="code_only",
        )

        # Execute plan
        result = controller.execute_plan(plan)

        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 3
        assert executor.execution_count == 3

    def test_executor_with_parallel_tasks(self):
        """Test executor with parallel tasks (no dependencies)"""
        from core.planner.flow_controller import FlowController
        from core.planner.planner_types import PlannerOutput, TaskTree

        executor = create_agent_task_executor(dry_run=True)
        controller = FlowController(task_executor=executor)

        # Create parallel tasks (no edges = no dependencies)
        nodes = [
            TaskNode(task_id=f"task-{i}", task_type=TaskType.CODE, description=f"Task {i}")
            for i in range(5)
        ]
        plan = PlannerOutput(
            plan_id="parallel-test",
            goal="Test parallel execution",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            flow_template="code_only",
        )

        result = controller.execute_plan(plan)

        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.task_results) == 5
        assert executor.execution_count == 5
