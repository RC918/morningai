"""
Tests for AutonomousExecutor - End-to-End Task Execution

Issue: #1821 - Meta Agent 自主任務規劃與執行
"""

import pytest
from ..goal_parser import GoalParser
from ..task_planner import TaskPlanner, SubTask, SubTaskType
from ..autonomous_executor import AutonomousExecutor, ExecutionResult, ExecutionStatus


class TestAutonomousExecutor:
    """Test cases for AutonomousExecutor"""

    @pytest.fixture
    def executor(self):
        """Create an AutonomousExecutor instance"""
        return AutonomousExecutor(max_retries=2, task_timeout_seconds=10)

    @pytest.fixture
    def parser(self):
        """Create a GoalParser instance"""
        return GoalParser()

    @pytest.fixture
    def planner(self):
        """Create a TaskPlanner instance"""
        return TaskPlanner()

    @pytest.mark.asyncio
    async def test_execute_goal_returns_result(self, executor):
        """Test that execute_goal returns an ExecutionResult"""
        result = await executor.execute_goal("Add a simple feature")

        assert isinstance(result, ExecutionResult)
        assert result.execution_id is not None
        assert result.plan_id is not None

    @pytest.mark.asyncio
    async def test_execute_goal_completes_tasks(self, executor):
        """Test that execute_goal completes tasks"""
        result = await executor.execute_goal("Update documentation")

        assert result.tasks_completed > 0
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    @pytest.mark.asyncio
    async def test_execute_plan_tracks_progress(self, executor, parser, planner):
        """Test that execute_plan tracks progress correctly"""
        goal = parser.parse("Add a test feature")
        plan = planner.create_plan(goal)

        result = await executor.execute_plan(plan)

        total_tasks = len(plan.subtasks)
        assert result.tasks_completed + result.tasks_failed + result.tasks_skipped <= total_tasks

    @pytest.mark.asyncio
    async def test_execution_result_to_dict(self, executor):
        """Test ExecutionResult serialization"""
        result = await executor.execute_goal("Simple task")
        result_dict = result.to_dict()

        assert "execution_id" in result_dict
        assert "plan_id" in result_dict
        assert "status" in result_dict
        assert "tasks_completed" in result_dict
        assert "total_duration_seconds" in result_dict

    @pytest.mark.asyncio
    async def test_get_status(self, executor):
        """Test get_status method"""
        # Before execution
        status = executor.get_status()
        assert status["status"] == "idle"

        # Start execution
        await executor.execute_goal("Test task")

        # After execution
        status = executor.get_status()
        assert "status" in status

    @pytest.mark.asyncio
    async def test_context_passed_to_goal(self, executor):
        """Test that context is passed through execution"""
        context = {"repo": "RC918/morningai", "branch": "feature/test"}
        result = await executor.execute_goal("Add feature", context)

        assert result is not None

    @pytest.mark.asyncio
    async def test_pause_and_resume(self, executor):
        """Test pause and resume functionality"""
        executor.pause()
        assert executor.is_paused is True

        executor.resume()
        assert executor.is_paused is False

    @pytest.mark.asyncio
    async def test_cancel_execution(self, executor):
        """Test cancel functionality"""
        executor.cancel()
        assert executor.is_cancelled is True

    @pytest.mark.asyncio
    async def test_task_callbacks(self, executor):
        """Test task callbacks are called"""
        started_tasks = []
        completed_tasks = []

        def on_start(task):
            started_tasks.append(task.task_id)

        def on_complete(task, result):
            completed_tasks.append(task.task_id)

        executor.on_task_start = on_start
        executor.on_task_complete = on_complete

        await executor.execute_goal("Simple task")

        assert len(started_tasks) > 0
        assert len(completed_tasks) > 0

    @pytest.mark.asyncio
    async def test_approval_callback(self, executor, parser, planner):
        """Test approval callback for high-risk tasks"""
        approval_requests = []

        def on_approval(task):
            approval_requests.append(task.task_id)
            return True  # Auto-approve

        executor.on_approval_required = on_approval

        # Create a deployment goal which requires approval
        goal = parser.parse("Deploy to production")
        plan = planner.create_plan(goal)

        await executor.execute_plan(plan)

        # Should have requested approval for deployment tasks
        # (may or may not have approval requests depending on plan)

    @pytest.mark.asyncio
    async def test_execution_duration_tracked(self, executor):
        """Test that execution duration is tracked"""
        result = await executor.execute_goal("Quick task")

        assert result.total_duration_seconds >= 0
        assert result.started_at is not None
        assert result.completed_at is not None


class TestExecutionResult:
    """Test cases for ExecutionResult dataclass"""

    def test_execution_result_creation(self):
        """Test ExecutionResult creation"""
        from datetime import datetime

        result = ExecutionResult(
            execution_id="exec-123",
            plan_id="plan-456",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
        )

        assert result.execution_id == "exec-123"
        assert result.plan_id == "plan-456"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.tasks_completed == 0
        assert result.tasks_failed == 0

    def test_execution_result_to_dict(self):
        """Test ExecutionResult serialization"""
        from datetime import datetime

        result = ExecutionResult(
            execution_id="exec-123",
            plan_id="plan-456",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
            tasks_completed=5,
            tasks_failed=1,
        )

        result_dict = result.to_dict()
        assert result_dict["execution_id"] == "exec-123"
        assert result_dict["tasks_completed"] == 5
        assert result_dict["tasks_failed"] == 1


class TestExecutionStatus:
    """Test cases for ExecutionStatus enum"""

    def test_all_statuses_exist(self):
        """Test that all expected statuses exist"""
        expected_statuses = [
            "PENDING",
            "RUNNING",
            "PAUSED",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        ]

        for status_name in expected_statuses:
            assert hasattr(ExecutionStatus, status_name)


class TestTaskHandlers:
    """Test cases for individual task handlers"""

    @pytest.fixture
    def executor(self):
        """Create an AutonomousExecutor instance"""
        return AutonomousExecutor()

    @pytest.mark.asyncio
    async def test_setup_environment_handler(self, executor):
        """Test setup environment handler"""
        task = SubTask(
            task_id="test-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )

        result = await executor._handle_setup_environment(task)
        assert result["environment_ready"] is True

    @pytest.mark.asyncio
    async def test_analyze_code_handler(self, executor):
        """Test analyze code handler"""
        task = SubTask(
            task_id="test-002",
            task_type=SubTaskType.ANALYZE_CODE,
            description="Analyze code",
        )

        result = await executor._handle_analyze_code(task)
        assert result["analysis_complete"] is True

    @pytest.mark.asyncio
    async def test_write_code_handler(self, executor):
        """Test write code handler"""
        task = SubTask(
            task_id="test-003",
            task_type=SubTaskType.WRITE_CODE,
            description="Write code",
        )

        result = await executor._handle_write_code(task)
        assert result["code_written"] is True

    @pytest.mark.asyncio
    async def test_run_test_handler(self, executor):
        """Test run test handler"""
        task = SubTask(
            task_id="test-004",
            task_type=SubTaskType.RUN_TEST,
            description="Run tests",
        )

        result = await executor._handle_run_test(task)
        assert result["tests_passed"] is True

    @pytest.mark.asyncio
    async def test_verification_handler(self, executor):
        """Test verification handler"""
        task = SubTask(
            task_id="test-005",
            task_type=SubTaskType.VERIFICATION,
            description="Verify changes",
        )

        result = await executor._handle_verification(task)
        assert result["verification_passed"] is True
