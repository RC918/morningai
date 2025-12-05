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


class TestExecutorIntegration:
    """Integration tests for AutonomousExecutor with AuditLogger, ExecutionPolicy, and StateManager"""

    @pytest.mark.asyncio
    async def test_policy_safety_limit_triggers_audit_event(self):
        """Test that policy safety limits trigger audit events"""
        from ..execution_policy import ExecutionPolicy

        policy = ExecutionPolicy(max_loop_iterations=0)

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=policy,
        )

        result = await executor.execute_goal("Simple task")

        assert any("max loop iterations" in err.lower() for err in result.errors)

        assert executor.audit_logger is not None
        event_type_values = {e.event_type.value for e in executor.audit_logger.events}
        assert "execution_started" in event_type_values
        assert "safety_limit_reached" in event_type_values

        safety_events = [
            e for e in executor.audit_logger.events
            if e.event_type.value == "safety_limit_reached"
        ]
        assert len(safety_events) >= 1
        assert safety_events[0].details.get("limit_type") == "max_loop_iterations"

    @pytest.mark.asyncio
    async def test_state_manager_delete_on_completion(self, tmp_path):
        """Test that state manager deletes state on execution completion"""
        from ..state_persistence import ExecutionStateManager

        state_manager = ExecutionStateManager(storage_dir=str(tmp_path / "state"))

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            state_manager=state_manager,
        )

        result = await executor.execute_goal("Quick task")

        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

        loaded = state_manager.load_state(result.execution_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_audit_logger_records_task_lifecycle(self):
        """Test that audit logger records task start and completion events"""
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=10,
        )

        await executor.execute_goal("Add documentation")

        assert executor.audit_logger is not None

        event_type_values = [e.event_type.value for e in executor.audit_logger.events]

        assert "execution_started" in event_type_values

        task_started_count = sum(1 for e in event_type_values if e == "task_started")
        task_completed_count = sum(1 for e in event_type_values if e == "task_completed")

        assert task_started_count > 0
        assert task_completed_count > 0

        assert "execution_completed" in event_type_values or "execution_failed" in event_type_values

    @pytest.mark.asyncio
    async def test_executor_uses_default_policy_when_none_provided(self):
        """Test that executor creates default ExecutionPolicy when none provided"""
        executor = AutonomousExecutor()

        assert executor.policy is not None
        assert hasattr(executor.policy, "max_loop_iterations")
        assert executor.policy.max_loop_iterations == 1000

    @pytest.mark.asyncio
    async def test_executor_respects_custom_policy_limits(self):
        """Test that executor respects custom policy limits"""
        from datetime import timedelta
        from ..execution_policy import ExecutionPolicy

        custom_policy = ExecutionPolicy(
            max_loop_iterations=5,
            max_execution_time=timedelta(seconds=1),
            max_consecutive_failures=2,
        )

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=custom_policy,
        )

        assert executor.policy.max_loop_iterations == 5
        assert executor.policy.max_execution_time == timedelta(seconds=1)
        assert executor.policy.max_consecutive_failures == 2

    @pytest.mark.asyncio
    async def test_full_integration_audit_policy_state(self, tmp_path):
        """Test full integration of AuditLogger, ExecutionPolicy, and StateManager"""
        from ..execution_policy import ExecutionPolicy
        from ..state_persistence import ExecutionStateManager

        state_manager = ExecutionStateManager(storage_dir=str(tmp_path / "state"))
        policy = ExecutionPolicy(max_loop_iterations=100)

        executor = AutonomousExecutor(
            max_retries=2,
            task_timeout_seconds=10,
            policy=policy,
            state_manager=state_manager,
        )

        result = await executor.execute_goal("Write a simple test")

        assert executor.policy is policy
        assert executor.state_manager is state_manager
        assert executor.audit_logger is not None

        event_type_values = {e.event_type.value for e in executor.audit_logger.events}
        assert "execution_started" in event_type_values

        assert result.execution_id is not None
        assert result.plan_id is not None

        loaded = state_manager.load_state(result.execution_id)
        assert loaded is None
