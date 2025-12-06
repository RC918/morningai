"""
Tests for Planner Integration - Plan Generation and Approval Workflow

This module tests the integration between GoalParser, TaskPlanner, and
AutonomousExecutor, specifically focusing on the approval workflow.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Issue: #2067 - Cloud IDE Integration
"""

import pytest
from datetime import datetime
from ..goal_parser import GoalParser
from ..task_planner import TaskPlanner, TaskPlan, SubTask, SubTaskType, SubTaskStatus
from ..autonomous_executor import (
    AutonomousExecutor,
    ExecutionResult,
    ExecutionStatus,
)
from ..execution_policy import ExecutionPolicy


class TestPlannerIntegration:
    """Integration tests for GoalParser -> TaskPlanner -> AutonomousExecutor flow"""

    @pytest.fixture
    def parser(self):
        """Create a GoalParser instance"""
        return GoalParser()

    @pytest.fixture
    def planner(self):
        """Create a TaskPlanner instance"""
        return TaskPlanner()

    @pytest.fixture
    def executor(self):
        """Create an AutonomousExecutor instance"""
        return AutonomousExecutor(max_retries=2, task_timeout_seconds=10)

    @pytest.mark.asyncio
    async def test_goal_to_plan_to_execution_flow(self, parser, planner, executor):
        """Test complete flow from goal parsing to plan creation to execution"""
        goal_text = "Add a new user authentication feature"
        
        def approve_all(task):
            return True
        
        executor.on_approval_required = approve_all
        
        parsed_goal = parser.parse(goal_text)
        assert parsed_goal is not None
        assert parsed_goal.summary is not None
        
        plan = planner.create_plan(parsed_goal)
        assert isinstance(plan, TaskPlan)
        assert len(plan.subtasks) > 0
        
        result = await executor.execute_plan(plan)
        assert isinstance(result, ExecutionResult)
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    @pytest.mark.asyncio
    async def test_plan_with_approval_required_tasks(self, parser, planner):
        """Test that deployment goals generate plans with approval-required tasks"""
        goal_text = "Deploy the application to production"
        
        parsed_goal = parser.parse(goal_text)
        plan = planner.create_plan(parsed_goal)
        
        deployment_tasks = [
            t for t in plan.subtasks 
            if t.task_type == SubTaskType.DEPLOYMENT
        ]
        
        assert len(deployment_tasks) > 0
        for task in deployment_tasks:
            assert task.requires_approval is True

    @pytest.mark.asyncio
    async def test_approval_callback_invoked_for_deployment(self, parser, planner):
        """Test that approval callback is invoked for deployment tasks"""
        from ..execution_policy import ExecutionPolicy, AllowedOperation
        
        approval_requests = []
        
        def on_approval(task):
            approval_requests.append({
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "description": task.description,
            })
            return True
        
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
        executor.on_approval_required = on_approval
        
        goal_text = "Deploy to staging environment"
        parsed_goal = parser.parse(goal_text)
        plan = planner.create_plan(parsed_goal)
        
        await executor.execute_plan(plan)
        
        deployment_approvals = [
            req for req in approval_requests 
            if req["task_type"] == "deployment"
        ]
        assert len(deployment_approvals) > 0

    @pytest.mark.asyncio
    async def test_approval_denied_skips_task(self):
        """Test that denying approval skips the task"""
        from ..execution_policy import ExecutionPolicy, AllowedOperation
        from ..audit_log import AuditLogger
        
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
        
        executor.audit_logger = AuditLogger(
            execution_id="test-denial-001",
            actor="test-user",
        )
        executor.current_execution = ExecutionResult(
            execution_id="test-denial-001",
            plan_id="test-plan-001",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )
        
        def deny_all(task):
            return False
        
        executor.on_approval_required = deny_all
        
        task = SubTask(
            task_id="test-deploy-denied",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
            requires_approval=True,
        )
        
        await executor._execute_task(task)
        
        assert task.status == SubTaskStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_approval_granted_executes_task(self, parser, planner):
        """Test that granting approval executes the task"""
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
        
        approved_tasks = []
        
        def approve_all(task):
            approved_tasks.append(task.task_id)
            return True
        
        executor.on_approval_required = approve_all
        
        goal_text = "Deploy to staging"
        parsed_goal = parser.parse(goal_text)
        plan = planner.create_plan(parsed_goal)
        
        result = await executor.execute_plan(plan)
        
        assert len(approved_tasks) > 0
        assert result.tasks_completed > 0


class TestPlanApprovalWorkflow:
    """Tests for the plan approval workflow"""

    @pytest.fixture
    def setup_executor_with_audit(self):
        """Helper to create executor with audit logger initialized"""
        from ..audit_log import AuditLogger
        from ..execution_policy import ExecutionPolicy, AllowedOperation
        
        def _setup():
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
            executor.audit_logger = AuditLogger(
                execution_id="test-approval-001",
                actor="test-user",
            )
            executor.current_execution = ExecutionResult(
                execution_id="test-approval-001",
                plan_id="test-plan-001",
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
            )
            return executor
        return _setup

    @pytest.mark.asyncio
    async def test_approval_request_logged_to_audit(self, setup_executor_with_audit):
        """Test that approval requests are logged to audit log"""
        executor = setup_executor_with_audit()
        
        approval_requested = []
        
        def on_approval(task):
            approval_requested.append(task.task_id)
            return True
        
        executor.on_approval_required = on_approval
        
        task = SubTask(
            task_id="test-deploy-001",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
            requires_approval=True,
        )
        
        await executor._execute_task(task)
        
        event_types = [e.event_type.value for e in executor.audit_logger.events]
        assert "approval_requested" in event_types

    @pytest.mark.asyncio
    async def test_approval_denied_logged_to_audit(self, setup_executor_with_audit):
        """Test that approval denials are logged to audit log"""
        executor = setup_executor_with_audit()
        
        def deny_approval(task):
            return False
        
        executor.on_approval_required = deny_approval
        
        task = SubTask(
            task_id="test-deploy-002",
            task_type=SubTaskType.DEPLOYMENT,
            description="Deploy to staging",
            requires_approval=True,
        )
        
        await executor._execute_task(task)
        
        event_types = [e.event_type.value for e in executor.audit_logger.events]
        assert "approval_denied" in event_types

    @pytest.mark.asyncio
    async def test_high_risk_tasks_require_approval(self):
        """Test that high-risk tasks (deployment) require approval"""
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
        
        approval_requested = []
        
        def on_approval(task):
            approval_requested.append(task.task_id)
            return True
        
        executor.on_approval_required = on_approval
        
        result = await executor.execute_goal("Deploy to staging")
        
        assert len(approval_requested) > 0


class TestPlanGeneration:
    """Tests for plan generation with different goal types"""

    @pytest.fixture
    def parser(self):
        return GoalParser()

    @pytest.fixture
    def planner(self):
        return TaskPlanner()

    def test_feature_goal_generates_complete_plan(self, parser, planner):
        """Test that feature development goal generates a complete plan"""
        goal = parser.parse("Implement user profile editing feature")
        plan = planner.create_plan(goal)
        
        task_types = {t.task_type for t in plan.subtasks}
        
        assert SubTaskType.ANALYZE_CODE in task_types or SubTaskType.SETUP_ENVIRONMENT in task_types
        assert SubTaskType.WRITE_CODE in task_types
        assert SubTaskType.WRITE_TEST in task_types or SubTaskType.RUN_TEST in task_types

    def test_bug_fix_goal_generates_analysis_first(self, parser, planner):
        """Test that bug fix goal starts with analysis"""
        goal = parser.parse("Fix the login button not responding")
        plan = planner.create_plan(goal)
        
        first_task = plan.subtasks[0]
        assert first_task.task_type == SubTaskType.ANALYZE_CODE

    def test_deployment_goal_generates_approval_tasks(self, parser, planner):
        """Test that deployment goal generates tasks requiring approval"""
        goal = parser.parse("Deploy to production environment")
        plan = planner.create_plan(goal)
        
        approval_required_tasks = [t for t in plan.subtasks if t.requires_approval]
        assert len(approval_required_tasks) > 0

    def test_plan_includes_verification_step(self, parser, planner):
        """Test that plans include verification step"""
        goal = parser.parse("Add new API endpoint")
        plan = planner.create_plan(goal)
        
        task_types = {t.task_type for t in plan.subtasks}
        assert SubTaskType.VERIFICATION in task_types or SubTaskType.RUN_TEST in task_types

    def test_plan_subtasks_have_correct_dependencies(self, parser, planner):
        """Test that plan subtasks have correct sequential dependencies"""
        goal = parser.parse("Implement feature with tests")
        plan = planner.create_plan(goal)
        
        assert len(plan.subtasks[0].dependencies) == 0
        
        for i, task in enumerate(plan.subtasks[1:], 1):
            assert len(task.dependencies) > 0
            assert plan.subtasks[i - 1].task_id in task.dependencies

    def test_plan_metadata_includes_context(self, parser, planner):
        """Test that plan metadata includes context information"""
        goal = parser.parse("Add feature")
        context = {"repo": "RC918/morningai", "branch": "feature/test"}
        plan = planner.create_plan(goal, context)
        
        assert "context" in plan.metadata
        assert plan.metadata["context"]["repo"] == "RC918/morningai"
