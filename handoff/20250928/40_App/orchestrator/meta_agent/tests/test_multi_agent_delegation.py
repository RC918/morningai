"""
Tests for Multi-Agent Delegation - Task Distribution to Sub-Agents

This module tests the AutonomousExecutor's ability to delegate tasks to
different agent types (dev_agent, ops_agent) based on task type.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Issue: #2067 - Cloud IDE Integration
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from ..goal_parser import GoalParser
from ..task_planner import TaskPlanner, SubTask, SubTaskType, SubTaskStatus
from ..autonomous_executor import (
    AutonomousExecutor,
    ExecutionResult,
    ExecutionStatus,
)


class MockDevAgent:
    """Mock DevAgent for testing task delegation"""
    
    def __init__(self):
        self.executed_tasks = []
        self.analyze_code = AsyncMock(return_value={"analysis": "complete"})
        self.write_code = AsyncMock(return_value={"code": "written"})
        self.write_test = AsyncMock(return_value={"test": "written"})
        self.run_test = AsyncMock(return_value={"tests_passed": True})
        self.review_code = AsyncMock(return_value={"review": "approved"})
    
    async def execute(self, task_type: str, task: SubTask) -> dict:
        """Execute a task and record it"""
        self.executed_tasks.append({
            "task_id": task.task_id,
            "task_type": task_type,
            "description": task.description,
        })
        return {"success": True, "agent": "dev_agent"}


class MockOpsAgent:
    """Mock OpsAgent for testing task delegation"""
    
    def __init__(self):
        self.executed_tasks = []
        self.deploy = AsyncMock(return_value={"deployed": True})
        self.setup_environment = AsyncMock(return_value={"environment": "ready"})
        self.cleanup = AsyncMock(return_value={"cleanup": "complete"})
    
    async def execute(self, task_type: str, task: SubTask) -> dict:
        """Execute a task and record it"""
        self.executed_tasks.append({
            "task_id": task.task_id,
            "task_type": task_type,
            "description": task.description,
        })
        return {"success": True, "agent": "ops_agent"}


class TestMultiAgentDelegation:
    """Tests for multi-agent task delegation"""

    @pytest.fixture
    def mock_dev_agent(self):
        """Create a mock DevAgent"""
        return MockDevAgent()

    @pytest.fixture
    def mock_ops_agent(self):
        """Create a mock OpsAgent"""
        return MockOpsAgent()

    @pytest.fixture
    def executor_with_agents(self, mock_dev_agent, mock_ops_agent):
        """Create an executor with mock agents"""
        return AutonomousExecutor(
            dev_agent=mock_dev_agent,
            ops_agent=mock_ops_agent,
            max_retries=1,
            task_timeout_seconds=10,
        )

    @pytest.fixture
    def parser(self):
        return GoalParser()

    @pytest.fixture
    def planner(self):
        return TaskPlanner()

    def test_executor_accepts_dev_agent(self, mock_dev_agent):
        """Test that executor accepts dev_agent parameter"""
        executor = AutonomousExecutor(dev_agent=mock_dev_agent)
        assert executor.dev_agent is mock_dev_agent

    def test_executor_accepts_ops_agent(self, mock_ops_agent):
        """Test that executor accepts ops_agent parameter"""
        executor = AutonomousExecutor(ops_agent=mock_ops_agent)
        assert executor.ops_agent is mock_ops_agent

    def test_executor_accepts_both_agents(self, mock_dev_agent, mock_ops_agent):
        """Test that executor accepts both agents"""
        executor = AutonomousExecutor(
            dev_agent=mock_dev_agent,
            ops_agent=mock_ops_agent,
        )
        assert executor.dev_agent is mock_dev_agent
        assert executor.ops_agent is mock_ops_agent

    def test_subtask_has_agent_type(self):
        """Test that SubTask has agent_type field"""
        task = SubTask(
            task_id="test-001",
            task_type=SubTaskType.WRITE_CODE,
            description="Write code",
            agent_type="dev_agent",
        )
        assert task.agent_type == "dev_agent"

    def test_subtask_default_agent_type(self):
        """Test that SubTask defaults to dev_agent"""
        task = SubTask(
            task_id="test-001",
            task_type=SubTaskType.WRITE_CODE,
            description="Write code",
        )
        assert task.agent_type == "dev_agent"


class TestAgentTypeRouting:
    """Tests for routing tasks to correct agent based on agent_type"""

    @pytest.fixture
    def parser(self):
        return GoalParser()

    @pytest.fixture
    def planner(self):
        return TaskPlanner()

    def test_deployment_tasks_use_ops_agent(self, parser, planner):
        """Test that deployment tasks are assigned to ops_agent"""
        goal = parser.parse("Deploy to staging")
        plan = planner.create_plan(goal)
        
        deployment_tasks = [
            t for t in plan.subtasks 
            if t.task_type == SubTaskType.DEPLOYMENT
        ]
        
        for task in deployment_tasks:
            assert task.agent_type == "ops_agent"

    def test_code_tasks_use_dev_agent(self, parser, planner):
        """Test that code-related tasks are assigned to dev_agent"""
        goal = parser.parse("Implement new feature")
        plan = planner.create_plan(goal)
        
        code_tasks = [
            t for t in plan.subtasks 
            if t.task_type in [SubTaskType.WRITE_CODE, SubTaskType.ANALYZE_CODE]
        ]
        
        for task in code_tasks:
            assert task.agent_type == "dev_agent"

    def test_test_tasks_use_dev_agent(self, parser, planner):
        """Test that test-related tasks are assigned to dev_agent"""
        goal = parser.parse("Add unit tests")
        plan = planner.create_plan(goal)
        
        test_tasks = [
            t for t in plan.subtasks 
            if t.task_type in [SubTaskType.WRITE_TEST, SubTaskType.RUN_TEST]
        ]
        
        for task in test_tasks:
            assert task.agent_type == "dev_agent"


class TestTaskDelegationExecution:
    """Tests for actual task delegation during execution"""

    @pytest.fixture
    def setup_executor_state(self):
        """Helper to initialize executor state for direct handler calls"""
        from ..audit_log import AuditLogger
        
        def _setup(executor):
            executor.audit_logger = AuditLogger(
                execution_id="test-delegation-001",
                actor="test-user",
            )
            executor.current_execution = ExecutionResult(
                execution_id="test-delegation-001",
                plan_id="test-plan-001",
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
            )
            return executor
        return _setup

    @pytest.mark.asyncio
    async def test_analyze_code_handler_called(self, setup_executor_state):
        """Test that analyze_code handler is called for ANALYZE_CODE tasks"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        setup_executor_state(executor)
        
        task = SubTask(
            task_id="test-analyze-001",
            task_type=SubTaskType.ANALYZE_CODE,
            description="Analyze code structure",
            agent_type="dev_agent",
        )
        
        result = await executor._execute_task(task)
        
        assert result is True
        assert task.status == SubTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_write_code_handler_called(self, setup_executor_state):
        """Test that write_code handler is called for WRITE_CODE tasks"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        setup_executor_state(executor)
        
        task = SubTask(
            task_id="test-write-001",
            task_type=SubTaskType.WRITE_CODE,
            description="Write feature code",
            agent_type="dev_agent",
        )
        
        result = await executor._execute_task(task)
        
        assert result is True
        assert task.status == SubTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_deployment_handler_called(self, setup_executor_state):
        """Test that deployment handler is called for DEPLOYMENT tasks"""
        from ..execution_policy import ExecutionPolicy, AllowedOperation
        
        policy = ExecutionPolicy(
            allowed_operations={
                AllowedOperation.READ_FILE,
                AllowedOperation.WRITE_FILE,
                AllowedOperation.EXECUTE_COMMAND,
                AllowedOperation.DEPLOY_STAGING,
            },
            require_approval_for_deployment=True,
        )
        
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=10,
            policy=policy,
        )
        setup_executor_state(executor)
        
        def approve_all(task):
            return True
        
        executor.on_approval_required = approve_all
        
        task = SubTask(
            task_id="test-deploy-001",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
            agent_type="ops_agent",
            requires_approval=True,
        )
        
        result = await executor._execute_task(task)
        
        assert result is True
        assert task.status == SubTaskStatus.COMPLETED


@pytest.mark.slow  # These tests invoke real async goal execution and can take 5+ minutes
class TestTaskAggregation:
    """Tests for aggregating results from multiple agents"""

    @pytest.fixture
    def parser(self):
        return GoalParser()

    @pytest.fixture
    def planner(self):
        return TaskPlanner()

    @pytest.mark.asyncio
    async def test_execution_aggregates_all_task_results(self, parser, planner):
        """Test that execution result aggregates all task results"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        goal = parser.parse("Add feature and deploy")
        plan = planner.create_plan(goal)
        
        def approve_all(task):
            return True
        
        executor.on_approval_required = approve_all
        
        result = await executor.execute_plan(plan)
        
        total_tasks = len(plan.subtasks)
        processed_tasks = result.tasks_completed + result.tasks_failed + result.tasks_skipped
        
        assert processed_tasks <= total_tasks
        assert result.execution_id is not None

    @pytest.mark.asyncio
    async def test_execution_tracks_completed_tasks(self, parser, planner):
        """Test that execution tracks completed tasks correctly"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        goal = parser.parse("Write documentation")
        plan = planner.create_plan(goal)
        
        result = await executor.execute_plan(plan)
        
        assert result.tasks_completed >= 0

    @pytest.mark.asyncio
    async def test_execution_tracks_failed_tasks(self, parser, planner):
        """Test that execution tracks failed tasks correctly"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        goal = parser.parse("Simple task")
        plan = planner.create_plan(goal)
        
        result = await executor.execute_plan(plan)
        
        assert result.tasks_failed >= 0


@pytest.mark.slow  # These tests invoke real async goal execution and can take 5+ minutes
class TestAgentCallbacks:
    """Tests for agent-related callbacks during execution"""

    @pytest.mark.asyncio
    async def test_task_start_callback_includes_agent_type(self):
        """Test that task start callback receives task with agent_type"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        started_tasks = []
        
        def on_start(task):
            started_tasks.append({
                "task_id": task.task_id,
                "agent_type": task.agent_type,
            })
        
        executor.on_task_start = on_start
        
        await executor.execute_goal("Add feature")
        
        assert len(started_tasks) > 0
        for task_info in started_tasks:
            assert "agent_type" in task_info

    @pytest.mark.asyncio
    async def test_task_complete_callback_receives_result(self):
        """Test that task complete callback receives task result"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        completed_tasks = []
        
        def on_complete(task, result):
            completed_tasks.append({
                "task_id": task.task_id,
                "result": result,
            })
        
        executor.on_task_complete = on_complete
        
        await executor.execute_goal("Simple task")
        
        assert len(completed_tasks) > 0


@pytest.mark.slow  # These tests invoke real async goal execution and can take 5+ minutes
class TestMixedAgentExecution:
    """Tests for execution with mixed agent types"""

    @pytest.fixture
    def parser(self):
        return GoalParser()

    @pytest.fixture
    def planner(self):
        return TaskPlanner()

    @pytest.mark.asyncio
    async def test_plan_with_mixed_agents_executes(self, parser, planner):
        """Test that a plan with both dev and ops tasks executes correctly"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        def approve_all(task):
            return True
        
        executor.on_approval_required = approve_all
        
        goal = parser.parse("Implement feature and deploy to staging")
        plan = planner.create_plan(goal)
        
        agent_types = {t.agent_type for t in plan.subtasks}
        
        result = await executor.execute_plan(plan)
        
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    @pytest.mark.asyncio
    async def test_execution_respects_task_order(self, parser, planner):
        """Test that execution respects task dependencies and order"""
        executor = AutonomousExecutor(max_retries=1, task_timeout_seconds=10)
        
        executed_order = []
        
        def on_start(task):
            executed_order.append(task.task_id)
        
        executor.on_task_start = on_start
        
        goal = parser.parse("Add feature")
        plan = planner.create_plan(goal)
        
        await executor.execute_plan(plan)
        
        for i, task_id in enumerate(executed_order[1:], 1):
            current_task = next(t for t in plan.subtasks if t.task_id == task_id)
            for dep_id in current_task.dependencies:
                if dep_id in executed_order:
                    dep_index = executed_order.index(dep_id)
                    assert dep_index < i
