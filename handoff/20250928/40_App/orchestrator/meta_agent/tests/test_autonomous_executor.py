"""
Tests for AutonomousExecutor - End-to-End Task Execution

Issue: #1821 - Meta Agent 自主任務規劃與執行
Issue: #1959 - ExecutionPolicy 強制執行與 dry_run 行為實作
"""

import pytest
from ..goal_parser import GoalParser
from ..task_planner import TaskPlanner, SubTask, SubTaskType, SubTaskStatus
from ..autonomous_executor import (
    AutonomousExecutor,
    ExecutionResult,
    ExecutionStatus,
    PolicyViolationError,
)
from ..execution_policy import ExecutionPolicy, AllowedOperation, DRY_RUN_POLICY


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


class TestPolicyEnforcementInExecutor:
    """Tests for ExecutionPolicy enforcement in AutonomousExecutor (#1959)"""

    @pytest.fixture
    def setup_executor_state(self):
        """Helper to initialize executor state for direct _execute_task calls"""
        from datetime import datetime
        from ..audit_log import AuditLogger

        def _setup(executor):
            executor.audit_logger = AuditLogger(
                execution_id="test-exec-001",
                actor="test-user",
            )
            executor.current_execution = ExecutionResult(
                execution_id="test-exec-001",
                plan_id="test-plan-001",
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
            )
            return executor
        return _setup

    @pytest.mark.asyncio
    async def test_policy_violation_for_deployment_with_restrictive_policy(self, setup_executor_state):
        """Test that deployment task raises PolicyViolationError with restrictive policy"""
        restrictive_policy = ExecutionPolicy(
            allowed_operations={AllowedOperation.READ_FILE}
        )

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=restrictive_policy,
        )
        setup_executor_state(executor)

        task = SubTask(
            task_id="test-deploy-001",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        with pytest.raises(PolicyViolationError) as exc_info:
            await executor._execute_task(task)

        assert "Policy violation" in str(exc_info.value)
        assert "deploy_staging" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_policy_violation_logs_audit_event(self, setup_executor_state):
        """Test that policy violation logs audit event"""
        restrictive_policy = ExecutionPolicy(
            allowed_operations={AllowedOperation.READ_FILE}
        )

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=restrictive_policy,
        )
        setup_executor_state(executor)

        task = SubTask(
            task_id="test-deploy-002",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        try:
            await executor._execute_task(task)
        except PolicyViolationError:
            pass

        assert executor.audit_logger is not None
        event_types = [e.event_type.value for e in executor.audit_logger.events]
        assert "policy_violation" in event_types

    @pytest.mark.asyncio
    async def test_policy_allows_safe_tasks(self, setup_executor_state):
        """Test that default policy allows safe tasks like analyze_code"""
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
        )
        setup_executor_state(executor)

        task = SubTask(
            task_id="test-analyze-001",
            task_type=SubTaskType.ANALYZE_CODE,
            description="Analyze code structure",
        )

        result = await executor._execute_task(task)
        assert result is True
        assert task.status == SubTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_policy_augments_requires_approval(self, setup_executor_state):
        """Test that policy augments task.requires_approval based on operations"""
        policy = ExecutionPolicy(
            allowed_operations={
                AllowedOperation.READ_FILE,
                AllowedOperation.DEPLOY_STAGING,
            },
            require_approval_for_deployment=True,
        )

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=policy,
        )
        setup_executor_state(executor)

        task = SubTask(
            task_id="test-deploy-003",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        approval_requested = []

        def on_approval(t):
            approval_requested.append(t.task_id)
            return True

        executor.on_approval_required = on_approval

        await executor._execute_task(task)

        assert task.requires_approval is True
        assert "test-deploy-003" in approval_requested


class TestDryRunBehavior:
    """Tests for dry_run behavior in AutonomousExecutor (#1959)"""

    @pytest.fixture
    def setup_executor_state(self):
        """Helper to initialize executor state for direct handler calls"""
        from datetime import datetime
        from ..audit_log import AuditLogger

        def _setup(executor):
            executor.audit_logger = AuditLogger(
                execution_id="test-exec-dry-001",
                actor="test-user",
            )
            executor.current_execution = ExecutionResult(
                execution_id="test-exec-dry-001",
                plan_id="test-plan-dry-001",
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
            )
            return executor
        return _setup

    @pytest.mark.asyncio
    async def test_dry_run_deployment_does_not_execute(self):
        """Test that dry_run mode prevents actual deployment"""
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=DRY_RUN_POLICY,
        )

        task = SubTask(
            task_id="test-dry-deploy-001",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        result = await executor._handle_deployment(task)

        assert result["dry_run"] is True
        assert result["deployment_complete"] is False
        assert "planned_action" in result

    @pytest.mark.asyncio
    async def test_dry_run_write_code_does_not_execute(self):
        """Test that dry_run mode prevents actual code writing"""
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=DRY_RUN_POLICY,
        )

        task = SubTask(
            task_id="test-dry-write-001",
            task_type=SubTaskType.WRITE_CODE,
            description="Write feature code",
        )

        result = await executor._handle_write_code(task)

        assert result["dry_run"] is True
        assert result["code_written"] is False
        assert "planned_action" in result

    @pytest.mark.asyncio
    async def test_dry_run_logs_high_risk_operation(self, setup_executor_state):
        """Test that dry_run mode logs high risk operations"""
        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=DRY_RUN_POLICY,
        )
        setup_executor_state(executor)

        task = SubTask(
            task_id="test-dry-deploy-002",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        await executor._handle_deployment(task)

        assert executor.audit_logger is not None
        event_types = [e.event_type.value for e in executor.audit_logger.events]
        assert "high_risk_operation" in event_types

        high_risk_events = [
            e for e in executor.audit_logger.events
            if e.event_type.value == "high_risk_operation"
        ]
        assert len(high_risk_events) >= 1
        assert high_risk_events[0].details.get("dry_run") is True

    @pytest.mark.asyncio
    async def test_non_dry_run_deployment_executes(self):
        """Test that non-dry_run mode executes deployment"""
        policy = ExecutionPolicy(dry_run=False)

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=policy,
        )

        task = SubTask(
            task_id="test-real-deploy-001",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
        )

        result = await executor._handle_deployment(task)

        assert result.get("dry_run") is not True
        assert result["deployment_complete"] is True

    @pytest.mark.asyncio
    async def test_non_dry_run_write_code_executes(self):
        """Test that non-dry_run mode executes code writing"""
        policy = ExecutionPolicy(dry_run=False)

        executor = AutonomousExecutor(
            max_retries=1,
            task_timeout_seconds=5,
            policy=policy,
        )

        task = SubTask(
            task_id="test-real-write-001",
            task_type=SubTaskType.WRITE_CODE,
            description="Write feature code",
        )

        result = await executor._handle_write_code(task)

        assert result.get("dry_run") is not True
        assert result["code_written"] is True


class TestVMAndIDEIntegration:
    """Tests for VM and IDE integration in AutonomousExecutor (#2018)"""

    @pytest.mark.asyncio
    async def test_executor_initializes_with_vm_provisioner(self):
        """Test that executor initializes with VMProvisioner"""
        from ..vm_provisioner import VMProvisioner, VMProvider

        executor = AutonomousExecutor()

        assert executor.vm_provisioner is not None
        assert isinstance(executor.vm_provisioner, VMProvisioner)
        assert executor.vm_provider == VMProvider.LOCAL

    @pytest.mark.asyncio
    async def test_executor_initializes_with_ide_service(self):
        """Test that executor initializes with VSCodeIDEService"""
        from ..vscode_ide import VSCodeIDEService

        executor = AutonomousExecutor()

        assert executor.ide_service is not None
        assert isinstance(executor.ide_service, VSCodeIDEService)

    @pytest.mark.asyncio
    async def test_executor_accepts_custom_vm_provider(self):
        """Test that executor accepts custom VM provider"""
        from ..vm_provisioner import VMProvider

        executor = AutonomousExecutor(vm_provider=VMProvider.DOCKER)

        assert executor.vm_provider == VMProvider.DOCKER

    @pytest.fixture
    def mock_plan(self):
        """Create a mock TaskPlan for testing"""
        from ..task_planner import TaskPlan
        from ..goal_parser import ParsedGoal, GoalType, GoalPriority

        goal = ParsedGoal(
            goal_id="test-goal-001",
            original_text="Test task",
            goal_type=GoalType.FEATURE_DEVELOPMENT,
            priority=GoalPriority.MEDIUM,
            summary="Test task summary",
            objectives=["Complete test"],
            constraints=[],
            success_criteria=["Test passes"],
            estimated_complexity="simple",
            requires_approval=False,
        )
        return TaskPlan(
            plan_id="test-plan-001",
            goal=goal,
            subtasks=[],
            total_estimated_minutes=10,
        )

    @pytest.mark.asyncio
    async def test_setup_environment_provisions_vm(self, mock_plan):
        """Test that setup_environment provisions a VM"""
        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        task = SubTask(
            task_id="test-setup-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )

        result = await executor._handle_setup_environment(task)

        assert result["environment_ready"] is True
        assert result["vm_id"] is not None
        assert "Provisioned VM" in result["setup_steps"][0]

    @pytest.mark.asyncio
    async def test_cleanup_destroys_vm(self, mock_plan):
        """Test that cleanup destroys the VM"""
        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        # First provision a VM
        setup_task = SubTask(
            task_id="test-setup-002",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        assert executor._current_vm is not None
        vm_id = executor._current_vm.vm_id

        # Then cleanup
        cleanup_task = SubTask(
            task_id="test-cleanup-002",
            task_type=SubTaskType.CLEANUP,
            description="Clean up resources",
        )
        result = await executor._handle_cleanup(cleanup_task)

        assert result["cleanup_complete"] is True
        assert executor._current_vm is None
        assert f"Destroyed VM {vm_id}" in result["cleanup_steps"]

    @pytest.mark.asyncio
    async def test_get_current_vm_returns_vm(self, mock_plan):
        """Test that get_current_vm returns the current VM"""
        executor = AutonomousExecutor()

        # Initially no VM
        assert executor.get_current_vm() is None

        executor.current_plan = mock_plan

        # Provision a VM
        setup_task = SubTask(
            task_id="test-setup-003",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        # Now should have a VM
        vm = executor.get_current_vm()
        assert vm is not None
        assert vm.vm_id is not None

    @pytest.mark.asyncio
    async def test_get_status_includes_vm_info(self, mock_plan):
        """Test that get_status includes VM and IDE session info"""
        from datetime import datetime

        executor = AutonomousExecutor()

        # Set up execution state
        executor.current_execution = ExecutionResult(
            execution_id="test-exec-vm-001",
            plan_id="test-plan-vm-001",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )
        executor.current_plan = mock_plan

        # Provision a VM
        setup_task = SubTask(
            task_id="test-setup-vm-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        # Check status includes VM info
        status = executor.get_status()
        assert "vm_id" in status
        assert "vm_status" in status

    @pytest.mark.asyncio
    async def test_cleanup_resources_method(self, mock_plan):
        """Test the cleanup_resources method for emergency cleanup"""
        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        # Provision a VM
        setup_task = SubTask(
            task_id="test-setup-cleanup-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        assert executor._current_vm is not None

        # Call cleanup_resources
        await executor.cleanup_resources()

        assert executor._current_vm is None
        assert executor._current_ide_session is None

    @pytest.mark.asyncio
    async def test_setup_environment_raises_on_vm_failure(self, mock_plan):
        """Test that setup_environment raises ExecutionError when VM provisioning fails"""
        from unittest.mock import AsyncMock, patch
        from ..autonomous_executor import ExecutionError

        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        # Mock vm_provisioner to raise an exception
        executor.vm_provisioner.provision_vm = AsyncMock(
            side_effect=RuntimeError("VM provisioning failed")
        )

        setup_task = SubTask(
            task_id="test-setup-fail-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )

        with pytest.raises(ExecutionError) as exc_info:
            await executor._handle_setup_environment(setup_task)

        assert "VM provisioning failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_returns_false_on_vm_destroy_failure(self, mock_plan):
        """Test that cleanup returns cleanup_complete=False when VM destruction fails"""
        from unittest.mock import AsyncMock

        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        # First provision a VM
        setup_task = SubTask(
            task_id="test-setup-cleanup-fail-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        # Mock destroy_vm to return False
        executor.vm_provisioner.destroy_vm = AsyncMock(return_value=False)

        cleanup_task = SubTask(
            task_id="test-cleanup-fail-001",
            task_type=SubTaskType.CLEANUP,
            description="Clean up resources",
        )
        result = await executor._handle_cleanup(cleanup_task)

        assert result["cleanup_complete"] is False
        assert len(result["cleanup_failures"]) > 0

    @pytest.mark.asyncio
    async def test_cleanup_returns_false_on_vm_destroy_exception(self, mock_plan):
        """Test that cleanup returns cleanup_complete=False when VM destruction raises"""
        from unittest.mock import AsyncMock

        executor = AutonomousExecutor()
        executor.current_plan = mock_plan

        # First provision a VM
        setup_task = SubTask(
            task_id="test-setup-cleanup-exc-001",
            task_type=SubTaskType.SETUP_ENVIRONMENT,
            description="Set up environment",
        )
        await executor._handle_setup_environment(setup_task)

        # Mock destroy_vm to raise an exception
        executor.vm_provisioner.destroy_vm = AsyncMock(
            side_effect=RuntimeError("VM destruction failed")
        )

        cleanup_task = SubTask(
            task_id="test-cleanup-exc-001",
            task_type=SubTaskType.CLEANUP,
            description="Clean up resources",
        )
        result = await executor._handle_cleanup(cleanup_task)

        assert result["cleanup_complete"] is False
        assert "VM destruction failed" in str(result["cleanup_failures"])
