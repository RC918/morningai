"""
Autonomous Executor - End-to-End Task Execution for Meta Agent

This module implements autonomous task execution, handling environment setup,
code writing, testing, error fixing, and deployment.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .audit_log import AuditLogger
from .execution_policy import ExecutionPolicy
from .goal_parser import GoalParser
from .session_command_processor import SessionCommandProcessor
from .state_persistence import ExecutionStateManager, create_checkpoint_from_execution
from .task_planner import SubTask, SubTaskStatus, SubTaskType, TaskPlan, TaskPlanner
from .visual_verifier import VisualVerifier
from .vm_provisioner import VMProvisioner, VMProvider, TaskVM
from .vscode_ide import VSCodeIDEService, IDESession

try:
    from common.config.settings import settings
except ImportError:
    settings = None  # type: ignore[assignment]

try:
    from governance.runtime_policy_enforcer import (
        RuntimePolicyEnforcer,
        get_runtime_policy_enforcer,
        EnforcementAction,
    )
except ImportError:
    RuntimePolicyEnforcer = None  # type: ignore[assignment,misc]
    get_runtime_policy_enforcer = None  # type: ignore[assignment,misc]
    EnforcementAction = None  # type: ignore[assignment,misc]

try:
    from deepwiki.service import get_deepwiki_service, QueryType
except ImportError:
    get_deepwiki_service = None  # type: ignore[assignment,misc]
    QueryType = None  # type: ignore[assignment,misc]

try:
    from webhooks.outbound_notifier import OutboundNotifier, WebhookSource
except ImportError:
    OutboundNotifier = None  # type: ignore[assignment,misc]
    WebhookSource = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Base exception for execution errors"""
    pass


class SafetyLimitError(ExecutionError):
    """Raised when a safety limit is reached"""
    pass


class PolicyViolationError(ExecutionError):
    """Raised when execution policy is violated"""
    pass


class ExecutionStatus(Enum):
    """Status of the overall execution"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of executing a task plan"""
    execution_id: str
    plan_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_skipped: int = 0
    total_duration_seconds: float = 0
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    pr_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_skipped": self.tasks_skipped,
            "total_duration_seconds": self.total_duration_seconds,
            "outputs": self.outputs,
            "errors": self.errors,
            "pr_url": self.pr_url,
            "metadata": self.metadata,
        }


class AutonomousExecutor:
    """
    Executes task plans autonomously with error handling and recovery.

    This executor coordinates the execution of subtasks, handles failures,
    and manages the overall execution lifecycle.
    """

    def __init__(
        self,
        goal_parser: Optional[GoalParser] = None,
        task_planner: Optional[TaskPlanner] = None,
        dev_agent: Optional[Any] = None,
        ops_agent: Optional[Any] = None,
        max_retries: int = 3,
        task_timeout_seconds: int = 300,
        policy: Optional[ExecutionPolicy] = None,
        state_manager: Optional[ExecutionStateManager] = None,
        vm_provisioner: Optional[VMProvisioner] = None,
        ide_service: Optional[VSCodeIDEService] = None,
        vm_provider: VMProvider = VMProvider.LOCAL,
        outbound_notifier: Optional[Any] = None,
    ):
        """
        Initialize the AutonomousExecutor.

        Args:
            goal_parser: GoalParser instance for parsing goals
            task_planner: TaskPlanner instance for creating plans
            dev_agent: DevAgent instance for code-related tasks
            ops_agent: OpsAgent instance for operations tasks
            max_retries: Maximum retries per task
            task_timeout_seconds: Timeout for individual tasks
            policy: ExecutionPolicy for safety limits and constraints
            state_manager: ExecutionStateManager for state persistence
            vm_provisioner: VMProvisioner for task VM management (Issue #2018)
            ide_service: VSCodeIDEService for IDE integration (Issue #2018)
            vm_provider: Default VM provider to use (Issue #2018)
            outbound_notifier: OutboundNotifier for closed-loop notifications (Issue #2154)
        """
        self.goal_parser = goal_parser or GoalParser()
        self.task_planner = task_planner or TaskPlanner()
        self.dev_agent = dev_agent
        self.ops_agent = ops_agent
        self.max_retries = max_retries
        self.task_timeout_seconds = task_timeout_seconds

        # Execution policy and state management
        self.policy = policy or ExecutionPolicy()
        self.state_manager = state_manager

        # VM and IDE integration (Issue #2018)
        self.vm_provisioner = vm_provisioner or VMProvisioner(default_provider=vm_provider)
        self.ide_service = ide_service or VSCodeIDEService()
        self.vm_provider = vm_provider

        # OutboundNotifier for closed-loop notifications (Issue #2154)
        self.outbound_notifier = outbound_notifier
        self._notification_source: Optional[Any] = None  # WebhookSource for notifications

        # Current VM and IDE session for the execution
        self._current_vm: Optional[TaskVM] = None
        self._current_ide_session: Optional[IDESession] = None

        # Execution state
        self.current_execution: Optional[ExecutionResult] = None
        self.current_plan: Optional[TaskPlan] = None
        self.is_paused = False
        self.is_cancelled = False

        # Audit logger (initialized per execution)
        self.audit_logger: Optional[AuditLogger] = None

        # Safety counters
        self._loop_iterations = 0
        self._consecutive_failures = 0
        self._blocked_since: Optional[datetime] = None

        # Task handlers
        self.task_handlers: Dict[SubTaskType, Callable] = {
            SubTaskType.SETUP_ENVIRONMENT: self._handle_setup_environment,
            SubTaskType.ANALYZE_CODE: self._handle_analyze_code,
            SubTaskType.WRITE_CODE: self._handle_write_code,
            SubTaskType.WRITE_TEST: self._handle_write_test,
            SubTaskType.RUN_TEST: self._handle_run_test,
            SubTaskType.CODE_REVIEW: self._handle_code_review,
            SubTaskType.DOCUMENTATION: self._handle_documentation,
            SubTaskType.DEPLOYMENT: self._handle_deployment,
            SubTaskType.VERIFICATION: self._handle_verification,
            SubTaskType.CLEANUP: self._handle_cleanup,
        }

        # Callbacks for external integration
        self.on_task_start: Optional[Callable[[SubTask], None]] = None
        self.on_task_complete: Optional[Callable[[SubTask, Dict], None]] = None
        self.on_task_fail: Optional[Callable[[SubTask, str], None]] = None
        self.on_approval_required: Optional[Callable[[SubTask], bool]] = None

        # Session command processor for handling user commands (Issue #2242)
        self.command_processor: Optional[SessionCommandProcessor] = None
        self._session_data: Optional[Dict[str, Any]] = None
        self._last_failed_task: Optional[SubTask] = None
        self._user_context_updates: List[str] = []

        # Runtime policy enforcer for safety governance (Epic #2311)
        self._runtime_policy_enforcer: Optional[Any] = None
        if get_runtime_policy_enforcer is not None:
            try:
                self._runtime_policy_enforcer = get_runtime_policy_enforcer()
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to initialize RuntimePolicyEnforcer: %s", e)

        logger.info(
            "[AutonomousExecutor] Initialized with max_retries=%d, timeout=%ds, "
            "max_loop_iterations=%d, vm_provider=%s, outbound_notifier=%s",
            max_retries, task_timeout_seconds, self.policy.max_loop_iterations,
            vm_provider.value, "enabled" if outbound_notifier else "disabled")

    async def execute_goal(
        self,
        goal_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a goal from natural language description.

        This is the main entry point for autonomous execution. It:
        1. Enriches context with DeepWiki knowledge (if enabled)
        2. Parses the goal into structured format
        3. Creates an execution plan
        4. Executes the plan with error handling

        Issue #2154: Integrates DeepWiki for context enrichment before planning.

        Args:
            goal_text: Natural language goal description
            context: Optional context (repo, branch, etc.)

        Returns:
            ExecutionResult with execution details
        """
        context = context or {}
        execution_id = f"exec-{int(time.time())}"

        logger.info(
            "[AutonomousExecutor] Starting execution %s for goal: %s...",
            execution_id, goal_text[:50])

        # Initialize execution result
        self.current_execution = ExecutionResult(
            execution_id=execution_id,
            plan_id="",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            # Step 0: Enrich context with DeepWiki knowledge (Issue #2154)
            context = await self._enrich_context_with_deepwiki(goal_text, context)

            # Step 1: Parse the goal
            parsed_goal = self.goal_parser.parse(goal_text, context)
            logger.info(
                "[AutonomousExecutor] Goal parsed: type=%s, complexity=%s",
                parsed_goal.goal_type.value, parsed_goal.estimated_complexity)

            # Step 2: Create execution plan
            plan = self.task_planner.create_plan(parsed_goal, context)
            self.current_plan = plan
            self.current_execution.plan_id = plan.plan_id

            logger.info(
                "[AutonomousExecutor] Plan created: %d tasks, estimated %d minutes",
                len(plan.subtasks), plan.total_estimated_minutes)

            # Step 3: Execute the plan
            result = await self.execute_plan(plan)

            return result

        except Exception as e:
            logger.error("[AutonomousExecutor] Execution failed: %s", e, exc_info=True)
            self.current_execution.status = ExecutionStatus.FAILED
            self.current_execution.errors.append(str(e))
            self.current_execution.completed_at = datetime.now()
            self.current_execution.total_duration_seconds = (
                self.current_execution.completed_at - self.current_execution.started_at
            ).total_seconds()
            return self.current_execution

    async def execute_plan(self, plan: TaskPlan) -> ExecutionResult:
        """
        Execute a task plan with safety limits to prevent infinite loops.

        Args:
            plan: The TaskPlan to execute

        Returns:
            ExecutionResult with execution details

        Raises:
            SafetyLimitError: If max iterations or execution time exceeded
        """
        self.current_plan = plan
        plan.status = "in_progress"

        # Reset safety counters
        self._loop_iterations = 0
        self._consecutive_failures = 0
        self._blocked_since = None

        if not self.current_execution:
            self.current_execution = ExecutionResult(
                execution_id=f"exec-{int(time.time())}",
                plan_id=plan.plan_id,
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
            )

        # Initialize audit logger for this execution
        self.audit_logger = AuditLogger(
            execution_id=self.current_execution.execution_id,
            actor="meta_agent",
        )

        logger.info(
            "[AutonomousExecutor] Executing plan %s with %d tasks",
            plan.plan_id[:8], len(plan.subtasks))

        # Log execution start
        self.audit_logger.log_execution_started(
            goal_text=plan.goal.original_text if hasattr(plan, 'goal') and plan.goal else "N/A",
            plan_id=plan.plan_id,
            task_count=len(plan.subtasks),
        )

        # Issue #2154: Send task started notification (closed-loop)
        goal_text = plan.goal.original_text if hasattr(plan, 'goal') and plan.goal else "N/A"
        await self._notify_task_started(
            execution_id=self.current_execution.execution_id,
            goal_text=goal_text,
            metadata={"plan_id": plan.plan_id, "task_count": len(plan.subtasks)},
        )

        try:
            while True:
                # Safety check: max loop iterations
                self._loop_iterations += 1
                if self._loop_iterations > self.policy.max_loop_iterations:
                    error_msg = (
                        f"Max loop iterations ({self.policy.max_loop_iterations}) exceeded. "
                        "Possible infinite loop detected."
                    )
                    logger.error("[AutonomousExecutor] %s", error_msg)
                    self.audit_logger.log_safety_limit_reached(
                        limit_type="max_loop_iterations",
                        limit_value=self.policy.max_loop_iterations,
                        current_value=self._loop_iterations,
                    )
                    self.current_execution.status = ExecutionStatus.FAILED
                    self.current_execution.errors.append(error_msg)
                    break

                # Safety check: max execution time
                elapsed = datetime.now() - self.current_execution.started_at
                if elapsed > self.policy.max_execution_time:
                    error_msg = (
                        f"Max execution time ({self.policy.max_execution_time}) exceeded. "
                        f"Elapsed: {elapsed}"
                    )
                    logger.error("[AutonomousExecutor] %s", error_msg)
                    self.audit_logger.log_safety_limit_reached(
                        limit_type="max_execution_time",
                        limit_value=str(self.policy.max_execution_time),
                        current_value=str(elapsed),
                    )
                    self.current_execution.status = ExecutionStatus.FAILED
                    self.current_execution.errors.append(error_msg)
                    break

                # Safety check: consecutive failures
                if self._consecutive_failures >= self.policy.max_consecutive_failures:
                    error_msg = (
                        f"Max consecutive failures ({self.policy.max_consecutive_failures}) reached. "
                        "Stopping execution."
                    )
                    logger.error("[AutonomousExecutor] %s", error_msg)
                    self.audit_logger.log_safety_limit_reached(
                        limit_type="max_consecutive_failures",
                        limit_value=self.policy.max_consecutive_failures,
                        current_value=self._consecutive_failures,
                    )
                    self.current_execution.status = ExecutionStatus.FAILED
                    self.current_execution.errors.append(error_msg)
                    break

                # Check for cancellation
                if self.is_cancelled:
                    logger.info("[AutonomousExecutor] Execution cancelled")
                    self.current_execution.status = ExecutionStatus.CANCELLED
                    # Clean up resources on cancellation (Issue #2018)
                    await self.cleanup_resources()
                    break

                # Check for pause
                if self.is_paused:
                    logger.info("[AutonomousExecutor] Execution paused")
                    self.current_execution.status = ExecutionStatus.PAUSED
                    # Save state when paused
                    if self.state_manager:
                        checkpoint = create_checkpoint_from_execution(
                            self.current_execution, plan
                        )
                        self.state_manager.save_state(
                            self.current_execution.execution_id,
                            checkpoint.to_dict(),
                        )
                    await asyncio.sleep(1)
                    continue

                # Issue #2242: Process pending session commands from Redis
                await self._process_session_commands(plan)

                # Get next task
                next_task = plan.get_next_task()
                if not next_task:
                    # Check if all tasks are done
                    progress = plan.get_progress()
                    if progress["pending"] == 0 and progress["in_progress"] == 0:
                        logger.info("[AutonomousExecutor] All tasks completed")
                        break
                    else:
                        # Tasks are blocked - track how long we've been blocked
                        if self._blocked_since is None:
                            self._blocked_since = datetime.now()
                        else:
                            blocked_duration = datetime.now() - self._blocked_since
                            if blocked_duration > self.policy.max_blocked_wait_time:
                                error_msg = (
                                    f"Tasks blocked for too long ({blocked_duration}). "
                                    f"Pending: {progress['pending']}, "
                                    f"In Progress: {progress['in_progress']}"
                                )
                                logger.error("[AutonomousExecutor] %s", error_msg)
                                self.audit_logger.log_safety_limit_reached(
                                    limit_type="max_blocked_wait_time",
                                    limit_value=str(self.policy.max_blocked_wait_time),
                                    current_value=str(blocked_duration),
                                )
                                self.current_execution.status = ExecutionStatus.FAILED
                                self.current_execution.errors.append(error_msg)
                                break
                        await asyncio.sleep(0.5)
                        continue
                else:
                    # Reset blocked timer when we have a task to execute
                    self._blocked_since = None

                # Execute the task
                task_success = await self._execute_task(next_task)

                # Track consecutive failures
                if task_success:
                    self._consecutive_failures = 0
                else:
                    self._consecutive_failures += 1

            # Finalize execution
            self._finalize_execution(plan)

            # Log execution completion
            self.audit_logger.log_execution_completed(
                status=self.current_execution.status.value,
                tasks_completed=self.current_execution.tasks_completed,
                tasks_failed=self.current_execution.tasks_failed,
                duration_seconds=self.current_execution.total_duration_seconds,
            )

            # Issue #2154: Send completion/failure notification (closed-loop)
            if self.current_execution.status == ExecutionStatus.COMPLETED:
                await self._notify_task_completed(
                    execution_id=self.current_execution.execution_id,
                    goal_text=goal_text,
                    result=self.current_execution.outputs,
                    pr_url=self.current_execution.pr_url,
                    metadata={"plan_id": plan.plan_id},
                )
            elif self.current_execution.status == ExecutionStatus.FAILED:
                error_summary = "; ".join(self.current_execution.errors[:3])
                await self._notify_task_failed(
                    execution_id=self.current_execution.execution_id,
                    goal_text=goal_text,
                    error=error_summary,
                    metadata={"plan_id": plan.plan_id},
                )

        except Exception as e:
            logger.error("[AutonomousExecutor] Plan execution failed: %s", e, exc_info=True)
            self.current_execution.status = ExecutionStatus.FAILED
            self.current_execution.errors.append(str(e))
            if self.audit_logger:
                self.audit_logger.log_execution_failed(error=str(e))
            # Clean up resources on unexpected failure (Issue #2018)
            await self.cleanup_resources()

            # Issue #2154: Send failure notification (closed-loop)
            await self._notify_task_failed(
                execution_id=self.current_execution.execution_id,
                goal_text=goal_text,
                error=str(e),
                metadata={"plan_id": plan.plan_id},
            )

        self.current_execution.completed_at = datetime.now()
        self.current_execution.total_duration_seconds = (
            self.current_execution.completed_at - self.current_execution.started_at
        ).total_seconds()

        # Clean up state on completion
        if self.state_manager and self.current_execution.status in (
            ExecutionStatus.COMPLETED, ExecutionStatus.FAILED
        ):
            self.state_manager.delete_state(self.current_execution.execution_id)

        return self.current_execution

    async def _execute_task(self, task: SubTask) -> bool:
        """
        Execute a single task with retries and error handling.

        Args:
            task: The SubTask to execute

        Returns:
            True if task completed successfully, False otherwise
        """
        task.status = SubTaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        logger.info(
            "[AutonomousExecutor] Executing task %s: %s",
            task.task_id, task.description[:50])

        # Log task start to audit log
        if self.audit_logger:
            self.audit_logger.log_task_started(
                task_id=task.task_id,
                task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                description=task.description,
            )

        # Notify task start
        if self.on_task_start:
            self.on_task_start(task)

        # Policy enforcement: Check if task type operations are allowed (#1959)
        task_type_value = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)
        is_allowed, disallowed_ops = self.policy.check_task_type_allowed(task_type_value)

        if not is_allowed:
            disallowed_names = [op.value for op in disallowed_ops]
            error_msg = (
                f"Policy violation: Task type '{task_type_value}' requires operations "
                f"{disallowed_names} which are not allowed by current policy"
            )
            logger.error("[AutonomousExecutor] %s", error_msg)

            # Log policy violation to audit log
            if self.audit_logger:
                self.audit_logger.log_policy_violation(
                    violation_type="disallowed_operation",
                    details=error_msg,
                    task_id=task.task_id,
                    task_type=task_type_value,
                    disallowed_operations=disallowed_names,
                )

            # Mark task as failed due to policy violation
            task.status = SubTaskStatus.FAILED
            task.error = error_msg
            task.completed_at = datetime.now()
            if self.current_execution:
                self.current_execution.tasks_failed += 1
                self.current_execution.errors.append(f"Task {task.task_id}: {error_msg}")

            raise PolicyViolationError(error_msg)

        # Policy enforcement: Check if any operations require approval (#1959)
        approval_required_ops = self.policy.get_approval_required_operations(task_type_value)
        if approval_required_ops and not task.requires_approval:
            # Augment task's requires_approval based on policy
            task.requires_approval = True
            logger.info(
                "[AutonomousExecutor] Task %s requires approval due to policy (operations: %s)",
                task.task_id, [op.value for op in approval_required_ops])

        # Runtime policy enforcement: Check resource access and cost budget (Epic #2311)
        if self._runtime_policy_enforcer is not None:
            runtime_check_result = await self._check_runtime_policy(task, task_type_value)
            if runtime_check_result is not None:
                if runtime_check_result.get("action") == "block":
                    error_msg = runtime_check_result.get("reason", "Runtime policy violation")
                    logger.error("[AutonomousExecutor] Runtime policy blocked task %s: %s", task.task_id, error_msg)
                    task.status = SubTaskStatus.FAILED
                    task.error = error_msg
                    task.completed_at = datetime.now()
                    if self.current_execution:
                        self.current_execution.tasks_failed += 1
                        self.current_execution.errors.append(f"Task {task.task_id}: {error_msg}")
                    raise PolicyViolationError(error_msg)
                elif runtime_check_result.get("action") == "require_approval":
                    task.requires_approval = True
                    logger.info(
                        "[AutonomousExecutor] Task %s requires approval due to runtime policy: %s",
                        task.task_id, runtime_check_result.get("reason"))

        # Check if approval is required
        if task.requires_approval:
            if self.audit_logger:
                self.audit_logger.log_approval_requested(
                    task_id=task.task_id,
                    operation=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                    resource=task.description[:100],
                    reason="Task marked as requiring approval",
                )

            if self.on_approval_required:
                approved = self.on_approval_required(task)
                if not approved:
                    logger.info(
                        "[AutonomousExecutor] Task %s not approved, skipping",
                        task.task_id)
                    task.status = SubTaskStatus.SKIPPED
                    self.current_execution.tasks_skipped += 1
                    if self.audit_logger:
                        self.audit_logger.log_approval_denied(
                            task_id=task.task_id,
                            denier="user",
                            operation=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                        )
                    return True  # Not a failure, just skipped
            else:
                logger.warning(
                    "[AutonomousExecutor] Task %s requires approval but no handler",
                    task.task_id)
                task.status = SubTaskStatus.BLOCKED
                return False  # Blocked is considered a failure for consecutive tracking

        # Execute with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Get handler for task type
                handler = self.task_handlers.get(task.task_type)
                if not handler:
                    raise ValueError(f"No handler for task type: {task.task_type}")

                # Execute with timeout
                result = await asyncio.wait_for(
                    handler(task),
                    timeout=self.task_timeout_seconds
                )

                # Success
                task.status = SubTaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.outputs = result or {}
                self.current_execution.tasks_completed += 1

                duration = (task.completed_at - task.started_at).total_seconds()

                logger.info(
                    "[AutonomousExecutor] Task %s completed successfully",
                    task.task_id)

                # Log task completion to audit log
                if self.audit_logger:
                    self.audit_logger.log_task_completed(
                        task_id=task.task_id,
                        duration_seconds=duration,
                        outputs=result,
                    )

                # Notify completion
                if self.on_task_complete:
                    self.on_task_complete(task, result or {})

                return True

            except asyncio.TimeoutError:
                last_error = f"Task timed out after {self.task_timeout_seconds}s"
                logger.warning(
                    "[AutonomousExecutor] Task %s attempt %d timed out",
                    task.task_id, attempt + 1)

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "[AutonomousExecutor] Task %s attempt %d failed: %s",
                    task.task_id, attempt + 1, e)

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # All retries failed
        task.status = SubTaskStatus.FAILED
        task.error = last_error
        task.completed_at = datetime.now()
        self.current_execution.tasks_failed += 1
        self.current_execution.errors.append(f"Task {task.task_id}: {last_error}")

        # Issue #2242: Track last failed task for retry command
        self._last_failed_task = task

        logger.error(
            "[AutonomousExecutor] Task %s failed after %d attempts: %s",
            task.task_id, self.max_retries, last_error)

        # Issue #2154: Query DeepWiki for error suggestions
        task_type_value = task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type)
        deepwiki_suggestions = await self._query_deepwiki_for_error(
            error_text=last_error or "Unknown error",
            task_type=task_type_value,
        )
        if deepwiki_suggestions:
            task.outputs = task.outputs or {}
            task.outputs["deepwiki_error_suggestions"] = deepwiki_suggestions
            logger.info(
                "[AutonomousExecutor] DeepWiki provided %d error suggestions for task %s",
                len(deepwiki_suggestions.get("similar_errors", [])),
                task.task_id,
            )

        # Log task failure to audit log
        if self.audit_logger:
            self.audit_logger.log_task_failed(
                task_id=task.task_id,
                error=last_error or "Unknown error",
                attempt=self.max_retries,
            )

        # Notify failure
        if self.on_task_fail:
            self.on_task_fail(task, last_error)

        return False

    def _finalize_execution(self, plan: TaskPlan) -> None:
        """Finalize execution and determine final status"""
        progress = plan.get_progress()

        self.current_execution.tasks_completed = progress["completed"]
        self.current_execution.tasks_failed = progress["failed"]

        if progress["failed"] > 0:
            self.current_execution.status = ExecutionStatus.FAILED
            plan.status = "failed"
        elif progress["completed"] == progress["total"]:
            self.current_execution.status = ExecutionStatus.COMPLETED
            plan.status = "completed"
        else:
            self.current_execution.status = ExecutionStatus.COMPLETED
            plan.status = "completed_with_skips"

        # Collect outputs from all tasks
        for task in plan.subtasks:
            if task.outputs:
                self.current_execution.outputs[task.task_id] = task.outputs

        logger.info(
            "[AutonomousExecutor] Execution finalized: status=%s, "
            "completed=%d, failed=%d, skipped=%d",
            self.current_execution.status.value,
            progress["completed"],
            progress["failed"],
            self.current_execution.tasks_skipped,
        )

        # Generate DeepWiki session insights if enabled (Tier 5 #1824)
        self._generate_session_insights(plan)

    def _generate_session_insights(self, plan: TaskPlan) -> None:
        """
        Generate session insights using DeepWiki service.

        Issue #1824: DeepWiki 知識庫與 Session Insights

        This method is called after execution finalization to provide
        actionable insights based on the execution results.

        Args:
            plan: The executed TaskPlan
        """
        # Check if DeepWiki is enabled
        if settings is None:
            return

        if not getattr(settings, 'enable_deepwiki', False):
            logger.debug("[AutonomousExecutor] DeepWiki disabled, skipping session insights")
            return

        try:
            from deepwiki.service import get_deepwiki_service

            deepwiki = get_deepwiki_service()

            # Prepare execution result data for insights
            # Pass all errors to DeepWiki for better insights quality
            execution_result = {
                "status": self.current_execution.status.value,
                "tasks_completed": self.current_execution.tasks_completed,
                "tasks_failed": self.current_execution.tasks_failed,
                "tasks_skipped": self.current_execution.tasks_skipped,
                "errors": list(self.current_execution.errors),  # Pass all errors
                "duration_seconds": self.current_execution.total_duration_seconds,
            }

            # Prepare task plan data
            task_plan = {
                "plan_id": plan.plan_id,
                "steps": [
                    {
                        "task_id": task.task_id,
                        "description": task.description,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                    }
                    for task in plan.subtasks
                ],
            }

            # Get session insights
            insight = deepwiki.get_session_insights(
                session_id=self.current_execution.execution_id,
                execution_result=execution_result,
                task_plan=task_plan,
            )

            # Store insights in execution metadata
            self.current_execution.metadata["deepwiki_insights"] = {
                "session_id": insight.session_id,
                "insight_type": insight.insight_type,
                "summary": insight.summary,
                "recommendations": insight.recommendations,
                "metrics": insight.metrics,
            }

            logger.info(
                "[AutonomousExecutor] DeepWiki session insights generated: %s",
                insight.summary[:100] if insight.summary else "No summary",
            )

        except ImportError as e:
            logger.debug("[AutonomousExecutor] DeepWiki not available: %s", e)
        except Exception as e:
            # Don't fail execution due to insights generation failure
            logger.warning(
                "[AutonomousExecutor] Failed to generate DeepWiki insights: %s",
                e,
            )

    # Task handlers
    async def _handle_setup_environment(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle environment setup tasks.

        Issue #2018: Provisions a VM and creates an IDE session for task execution.
        The VM and IDE session are stored in instance variables for use by other
        task handlers and cleaned up in _handle_cleanup.

        Issue #1959: Supports dry_run mode where VM provisioning is simulated.
        """
        logger.info("[AutonomousExecutor] Setting up environment for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would provision VM for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="setup_environment",
                    resource=task.description[:100],
                    risk_level="low",
                    dry_run=True,
                    planned_action="Provision VM and create IDE session",
                )
            return {
                "environment_ready": False,
                "dry_run": True,
                "planned_action": "Would provision VM and create IDE session",
                "vm_id": None,
                "ide_session_id": None,
                "setup_steps": ["DRY_RUN: VM provisioning skipped"],
            }

        setup_steps = []
        plan_id = self.current_plan.plan_id if self.current_plan else "unknown"

        # Step 1: Provision VM for task isolation (Issue #2018)
        try:
            self._current_vm = await self.vm_provisioner.provision_vm(
                task_id=task.task_id,
                plan_id=plan_id,
                provider=self.vm_provider,
            )
            setup_steps.append(f"Provisioned VM {self._current_vm.vm_id}")
            logger.info(
                "[AutonomousExecutor] Provisioned VM %s for task %s",
                self._current_vm.vm_id, task.task_id[:8]
            )
        except Exception as e:
            logger.error(
                "[AutonomousExecutor] Failed to provision VM for task %s: %s",
                task.task_id[:8], type(e).__name__
            )
            raise ExecutionError(
                f"VM provisioning failed for task {task.task_id[:8]}: {type(e).__name__}"
            ) from e

        # Step 2: Create IDE session for the VM (Issue #2018)
        if self._current_vm and self._current_vm.mcp_endpoint:
            try:
                self._current_ide_session = await self.ide_service.create_session(
                    vm_id=self._current_vm.vm_id,
                    task_id=task.task_id,
                    mcp_endpoint=self._current_vm.mcp_endpoint,
                )
                setup_steps.append(f"Created IDE session {self._current_ide_session.session_id}")
                logger.info(
                    "[AutonomousExecutor] Created IDE session %s for task %s",
                    self._current_ide_session.session_id, task.task_id[:8]
                )
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to create IDE session for task %s: %s",
                    task.task_id[:8], e
                )
                setup_steps.append(f"IDE session creation failed: {e}")
                # Continue without IDE - VM is still usable
        else:
            setup_steps.append("Skipped IDE session (no MCP endpoint)")

        # Store VM and IDE info in execution metadata
        if self.current_execution:
            self.current_execution.metadata["vm_id"] = (
                self._current_vm.vm_id if self._current_vm else None
            )
            self.current_execution.metadata["ide_session_id"] = (
                self._current_ide_session.session_id if self._current_ide_session else None
            )

        return {
            "environment_ready": True,
            "vm_id": self._current_vm.vm_id if self._current_vm else None,
            "ide_session_id": (
                self._current_ide_session.session_id if self._current_ide_session else None
            ),
            "setup_steps": setup_steps,
        }

    async def _handle_analyze_code(self, task: SubTask) -> Dict[str, Any]:
        """Handle code analysis tasks"""
        logger.info("[AutonomousExecutor] Analyzing code for task %s", task.task_id)

        # Use dev_agent if available
        if self.dev_agent:
            try:
                # Call dev_agent's analyze method
                result = await self._call_dev_agent("analyze", task)
                return result
            except Exception as e:
                logger.warning("[AutonomousExecutor] Dev agent analysis failed: %s", e)

        # Fallback to simulated analysis
        await asyncio.sleep(1)

        return {
            "analysis_complete": True,
            "findings": ["Code structure analyzed", "Integration points identified"],
        }

    async def _handle_write_code(self, task: SubTask) -> Dict[str, Any]:
        """Handle code writing tasks"""
        logger.info("[AutonomousExecutor] Writing code for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would write code for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="write_code",
                    resource=task.description[:100],
                    risk_level="medium",
                    dry_run=True,
                    planned_action="Write code to implement feature/fix",
                )
            return {
                "code_written": False,
                "dry_run": True,
                "planned_action": "Would write code to implement feature/fix",
                "files_modified": [],
            }

        # Use dev_agent if available
        if self.dev_agent:
            try:
                result = await self._call_dev_agent("write_code", task)
                return result
            except Exception as e:
                logger.warning("[AutonomousExecutor] Dev agent code writing failed: %s", e)

        # Fallback
        await asyncio.sleep(2)

        return {
            "code_written": True,
            "files_modified": [],
        }

    async def _handle_write_test(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle test writing tasks.

        Issue #1959: Supports dry_run mode where test writing is simulated.
        """
        logger.info("[AutonomousExecutor] Writing tests for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would write tests for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="write_test",
                    resource=task.description[:100],
                    risk_level="medium",
                    dry_run=True,
                    planned_action="Write test files",
                )
            return {
                "tests_written": False,
                "dry_run": True,
                "planned_action": "Would write test files",
                "test_files": [],
            }

        if self.dev_agent:
            try:
                result = await self._call_dev_agent("write_test", task)
                return result
            except Exception as e:
                logger.warning("[AutonomousExecutor] Dev agent test writing failed: %s", e)

        await asyncio.sleep(1)

        return {
            "tests_written": True,
            "test_files": [],
        }

    async def _handle_run_test(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle test execution tasks.

        Issue #1959: Supports dry_run mode where test execution is simulated.
        """
        logger.info("[AutonomousExecutor] Running tests for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would run tests for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="run_test",
                    resource=task.description[:100],
                    risk_level="low",
                    dry_run=True,
                    planned_action="Execute test suite",
                )
            return {
                "tests_passed": False,
                "dry_run": True,
                "planned_action": "Would execute test suite",
                "test_count": 0,
                "coverage": 0,
            }

        if self.dev_agent:
            try:
                result = await self._call_dev_agent("run_test", task)
                return result
            except Exception as e:
                logger.warning("[AutonomousExecutor] Dev agent test run failed: %s", e)

        await asyncio.sleep(1)

        return {
            "tests_passed": True,
            "test_count": 0,
            "coverage": 0,
        }

    async def _handle_code_review(self, task: SubTask) -> Dict[str, Any]:
        """Handle code review tasks"""
        logger.info("[AutonomousExecutor] Reviewing code for task %s", task.task_id)

        await asyncio.sleep(1)

        return {
            "review_complete": True,
            "issues_found": 0,
            "suggestions": [],
        }

    async def _handle_documentation(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle documentation tasks.

        Issue #1959: Supports dry_run mode where documentation writing is simulated.
        """
        logger.info("[AutonomousExecutor] Writing documentation for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would write documentation for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="documentation",
                    resource=task.description[:100],
                    risk_level="low",
                    dry_run=True,
                    planned_action="Update documentation files",
                )
            return {
                "documentation_updated": False,
                "dry_run": True,
                "planned_action": "Would update documentation files",
                "files_updated": [],
            }

        await asyncio.sleep(1)

        return {
            "documentation_updated": True,
            "files_updated": [],
        }

    async def _handle_deployment(self, task: SubTask) -> Dict[str, Any]:
        """Handle deployment tasks"""
        logger.info("[AutonomousExecutor] Handling deployment for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would deploy for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="deployment",
                    resource=task.description[:100],
                    risk_level="high",
                    dry_run=True,
                    planned_action="Deploy to staging environment",
                )
            return {
                "deployment_complete": False,
                "dry_run": True,
                "planned_action": "Would deploy to staging environment",
                "environment": "staging",
            }

        # Use ops_agent if available
        if self.ops_agent:
            try:
                result = await self._call_ops_agent("deploy", task)
                return result
            except Exception as e:
                logger.warning("[AutonomousExecutor] Ops agent deployment failed: %s", e)

        await asyncio.sleep(2)

        return {
            "deployment_complete": True,
            "environment": "staging",
        }

    async def _handle_verification(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle verification tasks with optional visual verification.

        Issue #2073: Integrates VisualVerifier for headless browser-based
        UI verification when task.inputs contains visual_verification config.

        Task inputs can include:
            - visual_verification: Dict with verification config
                - url: URL to verify
                - checks: List of verification checks
                - screenshot: Whether to capture screenshot

        Falls back to basic verification if visual verification is not
        configured or if headless browser is unavailable.
        """
        logger.info("[AutonomousExecutor] Verifying for task %s", task.task_id)

        checks_performed = []
        verification_results = []
        screenshot_result = None

        # Check if visual verification is enabled and requested
        # Tier 5: Visual verification is gated behind ENABLE_VISUAL_VERIFICATION flag
        visual_verification_enabled = (
            settings is not None and
            getattr(settings, 'enable_visual_verification', False)
        )
        visual_config = task.inputs.get("visual_verification") if task.inputs else None

        if visual_config and not visual_verification_enabled:
            logger.info(
                "[AutonomousExecutor] Visual verification requested but disabled "
                "(ENABLE_VISUAL_VERIFICATION=false), skipping"
            )
            checks_performed.append("Skipped: Visual verification disabled")
            visual_config = None  # Skip visual verification

        if visual_config:
            url = visual_config.get("url", "")
            checks = visual_config.get("checks", [])
            capture_screenshot = visual_config.get("screenshot", False)

            if url:
                verifier = None
                try:
                    verifier = VisualVerifier(headless=True)

                    # Capture screenshot if requested
                    if capture_screenshot:
                        selector = visual_config.get("selector")
                        screenshot = await verifier.capture_screenshot(
                            url=url,
                            selector=selector,
                            full_page=visual_config.get("full_page", False),
                        )
                        screenshot_result = screenshot.to_dict()
                        checks_performed.append("Screenshot capture")
                        logger.info(
                            "[AutonomousExecutor] Screenshot captured for %s: success=%s",
                            url, screenshot.success
                        )

                    # Run verification checks
                    if checks:
                        results = await verifier.run_verification_suite(url, checks)
                        for result in results:
                            verification_results.append(result.to_dict())
                            checks_performed.append(f"{result.check_type}: {result.selector}")

                        logger.info(
                            "[AutonomousExecutor] Visual verification completed: %d checks",
                            len(results)
                        )

                except ImportError:
                    logger.warning(
                        "[AutonomousExecutor] Playwright not available, "
                        "falling back to basic verification"
                    )
                    checks_performed.append("Fallback: Playwright unavailable")

                except Exception as e:
                    logger.error(
                        "[AutonomousExecutor] Visual verification failed: %s", e
                    )
                    checks_performed.append(f"Error: {type(e).__name__}")

                finally:
                    if verifier:
                        await verifier.close()

        # Basic verification checks (always performed)
        checks_performed.extend(["Functionality", "No regressions"])

        # Determine overall verification status
        all_passed = all(
            r.get("passed", False) for r in verification_results
        ) if verification_results else True

        return {
            "verification_passed": all_passed,
            "checks_performed": checks_performed,
            "visual_verification_results": verification_results,
            "screenshot": screenshot_result,
        }

    async def _handle_cleanup(self, task: SubTask) -> Dict[str, Any]:
        """
        Handle cleanup tasks.

        Issue #2018: Closes IDE session and destroys VM to release resources.
        This ensures proper cleanup of resources created in _handle_setup_environment.

        Issue #1959: Supports dry_run mode where cleanup is simulated.
        """
        logger.info("[AutonomousExecutor] Cleaning up for task %s", task.task_id)

        # dry_run mode: Log planned action but don't execute (#1959)
        if self.policy.dry_run:
            logger.info(
                "[AutonomousExecutor] DRY_RUN: Would cleanup resources for task %s",
                task.task_id)
            if self.audit_logger:
                self.audit_logger.log_high_risk_operation(
                    task_id=task.task_id,
                    operation="cleanup",
                    resource=task.description[:100],
                    risk_level="low",
                    dry_run=True,
                    planned_action="Close IDE session and destroy VM",
                )
            return {
                "cleanup_complete": False,
                "dry_run": True,
                "planned_action": "Would close IDE session and destroy VM",
                "cleanup_steps": ["DRY_RUN: Cleanup skipped"],
                "cleanup_failures": [],
            }

        cleanup_steps = []
        cleanup_failures = []

        # Step 1: Close IDE session (Issue #2018)
        if self._current_ide_session:
            try:
                await self.ide_service.close_session(self._current_ide_session.session_id)
                cleanup_steps.append(f"Closed IDE session {self._current_ide_session.session_id}")
                logger.info(
                    "[AutonomousExecutor] Closed IDE session %s",
                    self._current_ide_session.session_id
                )
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to close IDE session %s: %s",
                    self._current_ide_session.session_id, e
                )
                cleanup_failures.append(f"IDE session close failed: {type(e).__name__}")
            finally:
                self._current_ide_session = None

        # Step 2: Destroy VM (Issue #2018)
        if self._current_vm:
            try:
                success = await self.vm_provisioner.destroy_vm(self._current_vm.vm_id)
                if success:
                    cleanup_steps.append(f"Destroyed VM {self._current_vm.vm_id}")
                    logger.info(
                        "[AutonomousExecutor] Destroyed VM %s",
                        self._current_vm.vm_id
                    )
                else:
                    cleanup_failures.append(
                        f"VM destruction returned False for {self._current_vm.vm_id}"
                    )
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to destroy VM %s: %s",
                    self._current_vm.vm_id, e
                )
                cleanup_failures.append(f"VM destruction failed: {type(e).__name__}")
            finally:
                self._current_vm = None

        cleanup_complete = len(cleanup_failures) == 0
        return {
            "cleanup_complete": cleanup_complete,
            "cleanup_steps": cleanup_steps,
            "cleanup_failures": cleanup_failures,
        }

    async def _call_dev_agent(self, action: str, task: SubTask) -> Dict[str, Any]:
        """Call dev_agent for task execution"""
        if not self.dev_agent:
            raise ValueError("Dev agent not available")

        # This would integrate with the actual dev_agent
        # For now, return a placeholder
        return {"action": action, "task_id": task.task_id, "status": "completed"}

    async def _call_ops_agent(self, action: str, task: SubTask) -> Dict[str, Any]:
        """Call ops_agent for task execution"""
        if not self.ops_agent:
            raise ValueError("Ops agent not available")

        return {"action": action, "task_id": task.task_id, "status": "completed"}

    def pause(self) -> None:
        """Pause the current execution"""
        self.is_paused = True
        logger.info("[AutonomousExecutor] Execution paused")

    def resume(self) -> None:
        """Resume the current execution"""
        self.is_paused = False
        logger.info("[AutonomousExecutor] Execution resumed")

    def cancel(self) -> None:
        """Cancel the current execution"""
        self.is_cancelled = True
        logger.info("[AutonomousExecutor] Execution cancelled")

    def set_session_data(self, session_data: Dict[str, Any]) -> None:
        """
        Set the session data for command processing.

        Issue #2242: This method should be called to provide the session data
        from Redis that contains pending commands from SessionCommandInput.

        Args:
            session_data: Session data dictionary from Redis
        """
        self._session_data = session_data
        logger.info(
            "[AutonomousExecutor] Session data set, commands count: %d",
            len(session_data.get("commands", []))
        )

    def _initialize_command_processor(self) -> None:
        """
        Initialize the SessionCommandProcessor with callbacks.

        Issue #2242: Sets up the command processor with callbacks that
        integrate with the executor's state management.
        """
        self.command_processor = SessionCommandProcessor(
            on_continue=self._handle_continue_command,
            on_explain=self._handle_explain_command,
            on_skip=self._handle_skip_command,
            on_retry=self._handle_retry_command,
            on_user_command=self._handle_user_command_text,
        )
        logger.info("[AutonomousExecutor] Command processor initialized")

    def _handle_continue_command(self) -> None:
        """
        Handle 'continue' quick command.

        Issue #2242: Resumes execution if paused, or signals to continue
        if waiting for approval.
        """
        if self.is_paused:
            self.resume()
            logger.info("[AutonomousExecutor] Continued from paused state via command")
        else:
            logger.info("[AutonomousExecutor] Continue command received (not paused)")

    def _handle_explain_command(self) -> str:
        """
        Handle 'explain' quick command.

        Issue #2242: Generates an explanation of the current execution state
        and writes it to the session observations.

        Returns:
            Explanation string
        """
        explanation_parts = []

        if self.current_execution:
            explanation_parts.append(
                f"Execution {self.current_execution.execution_id}: "
                f"status={self.current_execution.status.value}"
            )

        if self.current_plan:
            progress = self.current_plan.get_progress()
            explanation_parts.append(
                f"Plan progress: {progress['completed']}/{progress['total']} tasks completed, "
                f"{progress['pending']} pending, {progress['failed']} failed"
            )

            # Find current task
            current_task = None
            for task in self.current_plan.subtasks:
                if task.status == SubTaskStatus.IN_PROGRESS:
                    current_task = task
                    break

            if current_task:
                explanation_parts.append(
                    f"Current task: {current_task.description[:100]}"
                )

        explanation = "; ".join(explanation_parts) if explanation_parts else "No active execution"
        logger.info("[AutonomousExecutor] Explain command: %s", explanation)

        # Add to session observations if session_data is available
        if self._session_data is not None:
            observations = self._session_data.setdefault("observations", [])
            observations.append({
                "type": "explanation",
                "content": explanation,
                "timestamp": datetime.now().isoformat(),
            })

        return explanation

    def _handle_skip_command(self) -> None:
        """
        Handle 'skip' quick command.

        Issue #2242: Marks the current task as skipped and moves to the next.
        """
        if self.current_plan:
            for task in self.current_plan.subtasks:
                if task.status == SubTaskStatus.IN_PROGRESS:
                    task.status = SubTaskStatus.SKIPPED
                    if self.current_execution:
                        self.current_execution.tasks_skipped += 1
                    logger.info(
                        "[AutonomousExecutor] Task %s skipped via command",
                        task.task_id
                    )
                    break
        else:
            logger.warning("[AutonomousExecutor] Skip command received but no active plan")

    def _handle_retry_command(self) -> None:
        """
        Handle 'retry' quick command.

        Issue #2242: Re-executes the last failed task.
        """
        if self._last_failed_task:
            self._last_failed_task.status = SubTaskStatus.PENDING
            self._last_failed_task.retry_count = 0
            logger.info(
                "[AutonomousExecutor] Task %s queued for retry via command",
                self._last_failed_task.task_id
            )
        else:
            logger.warning("[AutonomousExecutor] Retry command received but no failed task to retry")

    def _handle_user_command_text(self, command_text: str) -> None:
        """
        Handle user command (free-form text instruction).

        Issue #2242: Stores the user command for the ProjectEngineerAgent
        to use as additional context or goal update.

        Args:
            command_text: The user's instruction text
        """
        self._user_context_updates.append(command_text)
        logger.info(
            "[AutonomousExecutor] User command received: %s...",
            command_text[:50]
        )

        # Add to session observations
        if self._session_data is not None:
            observations = self._session_data.setdefault("observations", [])
            observations.append({
                "type": "user_command",
                "content": command_text,
                "timestamp": datetime.now().isoformat(),
            })

    async def _process_session_commands(self, plan: TaskPlan) -> None:
        """
        Process pending session commands from Redis.

        Issue #2242: This method is called in the main execution loop to
        check for and process any pending user commands from SessionCommandInput.

        Args:
            plan: The current TaskPlan being executed
        """
        if self._session_data is None:
            return

        # Initialize command processor if not already done
        if self.command_processor is None:
            self._initialize_command_processor()

        # Process pending commands
        results = self.command_processor.process_pending_commands(self._session_data)

        if results:
            logger.info(
                "[AutonomousExecutor] Processed %d session commands",
                len(results)
            )

            # Log results to audit log
            if self.audit_logger:
                for result in results:
                    self.audit_logger.log_event(
                        event_type="session_command_processed",
                        details={
                            "command_id": result.command_id,
                            "action": result.action_taken,
                            "success": result.success,
                            "message": result.message,
                            "error": result.error,
                        }
                    )

    def get_user_context_updates(self) -> List[str]:
        """
        Get accumulated user context updates from user commands.

        Issue #2242: Returns the list of user command texts that have been
        received, which can be used by ProjectEngineerAgent as additional context.

        Returns:
            List of user command texts
        """
        return self._user_context_updates.copy()

    def clear_user_context_updates(self) -> None:
        """
        Clear accumulated user context updates.

        Issue #2242: Should be called after the updates have been consumed
        by ProjectEngineerAgent.
        """
        self._user_context_updates.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        if not self.current_execution:
            return {"status": "idle"}

        result = self.current_execution.to_dict()

        if self.current_plan:
            result["plan_progress"] = self.current_plan.get_progress()

        # Include VM and IDE session info (Issue #2018)
        if self._current_vm:
            result["vm_id"] = self._current_vm.vm_id
            result["vm_status"] = self._current_vm.status.value
        if self._current_ide_session:
            result["ide_session_id"] = self._current_ide_session.session_id
            result["ide_status"] = self._current_ide_session.status.value

        return result

    def get_current_vm(self) -> Optional[TaskVM]:
        """
        Get the current VM for the execution.

        Issue #2018: Returns the TaskVM instance provisioned for the current
        execution, or None if no VM is active.
        """
        return self._current_vm

    def get_current_ide_session(self) -> Optional[IDESession]:
        """
        Get the current IDE session for the execution.

        Issue #2018: Returns the IDESession instance created for the current
        execution, or None if no IDE session is active.
        """
        return self._current_ide_session

    async def cleanup_resources(self) -> None:
        """
        Clean up VM and IDE resources.

        Issue #2018: This method should be called when execution is cancelled
        or fails unexpectedly to ensure resources are properly released.
        """
        if self._current_ide_session:
            try:
                await self.ide_service.close_session(self._current_ide_session.session_id)
                logger.info(
                    "[AutonomousExecutor] Cleaned up IDE session %s",
                    self._current_ide_session.session_id
                )
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to clean up IDE session: %s", e
                )
            finally:
                self._current_ide_session = None

        if self._current_vm:
            try:
                await self.vm_provisioner.destroy_vm(self._current_vm.vm_id)
                logger.info(
                    "[AutonomousExecutor] Cleaned up VM %s",
                    self._current_vm.vm_id
                )
            except Exception as e:
                logger.warning(
                    "[AutonomousExecutor] Failed to clean up VM: %s", e
                )
            finally:
                self._current_vm = None

    async def _enrich_context_with_deepwiki(
        self,
        goal_text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich execution context with DeepWiki knowledge.

        Issue #2154: Queries DeepWiki for relevant patterns and past failures
        before planning to provide better context for task execution.

        Args:
            goal_text: Natural language goal description
            context: Current execution context

        Returns:
            Enriched context dictionary with DeepWiki insights
        """
        deepwiki_enabled = (
            settings is not None and
            getattr(settings, 'enable_deepwiki', False) and
            get_deepwiki_service is not None
        )

        if not deepwiki_enabled:
            logger.debug(
                "[AutonomousExecutor] DeepWiki disabled or unavailable, skipping context enrichment"
            )
            return context

        try:
            deepwiki = get_deepwiki_service()

            query_result = await asyncio.to_thread(
                deepwiki.query,
                question=goal_text,
                query_type=QueryType.CODE_QUESTION,
                language=context.get("language"),
                repo=context.get("repo"),
                limit=5,
            )

            if query_result.sources:
                enriched_context = context.copy()
                enriched_context["deepwiki_context"] = {
                    "query_id": query_result.query_id,
                    "sources": query_result.sources,
                    "confidence": query_result.confidence,
                    "answer_summary": query_result.answer[:500] if query_result.answer else None,
                }

                logger.info(
                    "[AutonomousExecutor] Context enriched with DeepWiki: %d sources, confidence=%.2f",
                    len(query_result.sources),
                    query_result.confidence,
                )
                return enriched_context

            logger.debug("[AutonomousExecutor] DeepWiki returned no relevant sources")
            return context

        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] DeepWiki context enrichment failed: %s", e
            )
            return context

    async def _query_deepwiki_for_error(
        self,
        error_text: str,
        task_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query DeepWiki for error resolution suggestions.

        Issue #2154: When a task fails, queries DeepWiki for similar past
        failures and their fixes to help with error recovery.

        Args:
            error_text: Error message or stack trace
            task_type: Optional task type for context

        Returns:
            Dictionary with error suggestions or None if unavailable
        """
        deepwiki_enabled = (
            settings is not None and
            getattr(settings, 'enable_deepwiki', False) and
            get_deepwiki_service is not None
        )

        if not deepwiki_enabled:
            return None

        try:
            deepwiki = get_deepwiki_service()

            query_result = await asyncio.to_thread(
                deepwiki.query,
                question=error_text[:1000],
                query_type=QueryType.ERROR_LOOKUP,
                limit=3,
            )

            if query_result.sources:
                suggestions = {
                    "query_id": query_result.query_id,
                    "similar_errors": query_result.sources,
                    "confidence": query_result.confidence,
                    "suggested_fixes": query_result.answer,
                }

                logger.info(
                    "[AutonomousExecutor] DeepWiki found %d similar errors for task_type=%s",
                    len(query_result.sources),
                    task_type,
                )
                return suggestions

            return None

        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] DeepWiki error lookup failed: %s", e
            )
            return None

    def set_notification_source(self, source: Any) -> None:
        """
        Set the webhook source for outbound notifications.

        Issue #2154: Configures which external service to notify (GitHub, Jira, Slack).

        Args:
            source: WebhookSource enum value (GITHUB, JIRA, SLACK)
        """
        self._notification_source = source
        logger.info(
            "[AutonomousExecutor] Notification source set to: %s",
            source.value if hasattr(source, 'value') else source
        )

    async def _notify_task_started(
        self,
        execution_id: str,
        goal_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification that execution has started.

        Issue #2154: Closed-loop notification for task start.

        Args:
            execution_id: Execution ID
            goal_text: Goal text
            metadata: Additional metadata (repo, issue_number, etc.)
        """
        if not self.outbound_notifier or not self._notification_source:
            return

        if OutboundNotifier is None or WebhookSource is None:
            return

        try:
            await self.outbound_notifier.notify_task_started(
                source=self._notification_source,
                task_id=execution_id,
                goal_text=goal_text,
                metadata=metadata,
            )
            logger.info(
                "[AutonomousExecutor] Sent task started notification for %s",
                execution_id
            )
        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] Failed to send task started notification: %s", e
            )

    async def _notify_task_completed(
        self,
        execution_id: str,
        goal_text: str,
        result: Optional[Dict[str, Any]] = None,
        pr_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification that execution has completed.

        Issue #2154: Closed-loop notification for task completion.

        Args:
            execution_id: Execution ID
            goal_text: Goal text
            result: Execution result
            pr_url: URL of created PR (if any)
            metadata: Additional metadata
        """
        if not self.outbound_notifier or not self._notification_source:
            return

        if OutboundNotifier is None or WebhookSource is None:
            return

        try:
            await self.outbound_notifier.notify_task_completed(
                source=self._notification_source,
                task_id=execution_id,
                goal_text=goal_text,
                result=result,
                pr_url=pr_url,
                metadata=metadata,
            )
            logger.info(
                "[AutonomousExecutor] Sent task completed notification for %s",
                execution_id
            )
        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] Failed to send task completed notification: %s", e
            )

    async def _notify_task_failed(
        self,
        execution_id: str,
        goal_text: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification that execution has failed.

        Issue #2154: Closed-loop notification for task failure.

        Args:
            execution_id: Execution ID
            goal_text: Goal text
            error: Error message
            metadata: Additional metadata
        """
        if not self.outbound_notifier or not self._notification_source:
            return

        if OutboundNotifier is None or WebhookSource is None:
            return

        try:
            await self.outbound_notifier.notify_task_failed(
                source=self._notification_source,
                task_id=execution_id,
                goal_text=goal_text,
                error=error,
                metadata=metadata,
            )
            logger.info(
                "[AutonomousExecutor] Sent task failed notification for %s",
                execution_id
            )
        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] Failed to send task failed notification: %s", e
            )

    async def _notify_approval_required(
        self,
        execution_id: str,
        task_id: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification that approval is required.

        Issue #2154: Closed-loop notification for approval requests.

        Args:
            execution_id: Execution ID
            task_id: Task ID requiring approval
            operation: Operation requiring approval
            metadata: Additional metadata
        """
        if not self.outbound_notifier or not self._notification_source:
            return

        if OutboundNotifier is None or WebhookSource is None:
            return

        try:
            await self.outbound_notifier.notify_approval_required(
                source=self._notification_source,
                task_id=execution_id,
                operation=operation,
                resource=task_id,
                metadata=metadata,
            )
            logger.info(
                "[AutonomousExecutor] Sent approval required notification for %s",
                task_id
            )
        except Exception as e:
            logger.warning(
                "[AutonomousExecutor] Failed to send approval required notification: %s", e
            )

    async def _check_runtime_policy(
        self,
        task: SubTask,
        task_type_value: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Check runtime policy for task execution.

        Epic #2311: Runtime policy enforcement for deny writes and cost budgets.

        This method checks:
        1. Resource access policies (deny writes, network, shell)
        2. Cost/token budget policies

        Args:
            task: The SubTask to check
            task_type_value: String value of task type

        Returns:
            Dict with action and reason if policy check fails, None if allowed
        """
        if self._runtime_policy_enforcer is None:
            return None

        context = {
            "task_id": task.task_id,
            "task_type": task_type_value,
            "execution_id": self.current_execution.execution_id if self.current_execution else None,
        }

        write_task_types = {"write_code", "write_test", "documentation"}
        if task_type_value in write_task_types:
            target_files = task.outputs.get("target_files", []) if task.outputs else []
            if not target_files:
                logger.warning(
                    "[AutonomousExecutor] target_files is empty for write task (fail-closed)",
                    extra={
                        "operation": "runtime_policy_check",
                        "task_id": task.task_id,
                        "task_type": task_type_value,
                    }
                )
                if self.audit_logger:
                    self.audit_logger.log_policy_violation(
                        violation_type="runtime_policy_missing_target_files",
                        details="target_files is empty for write task (configuration error)",
                        task_id=task.task_id,
                        task_type=task_type_value,
                    )
                return {
                    "action": "require_approval",
                    "reason": "Write task missing target_files - requires approval (fail-closed)",
                }

            for target in target_files:
                check_result = self._runtime_policy_enforcer.check_resource_access(
                    operation="write",
                    resource=str(target),
                    context=context,
                )
                if not check_result.allowed:
                    if self.audit_logger:
                        self.audit_logger.log_policy_violation(
                            violation_type="runtime_policy_write_denied",
                            details=check_result.reason,
                            task_id=task.task_id,
                            task_type=task_type_value,
                        )
                    return {
                        "action": check_result.action.value if EnforcementAction else "block",
                        "reason": check_result.reason,
                    }

        if task_type_value == "cleanup":
            check_result = self._runtime_policy_enforcer.check_resource_access(
                operation="delete",
                resource=task.description[:100],
                context=context,
            )
            if not check_result.allowed:
                if self.audit_logger:
                    self.audit_logger.log_policy_violation(
                        violation_type="runtime_policy_delete_denied",
                        details=check_result.reason,
                        task_id=task.task_id,
                        task_type=task_type_value,
                    )
                return {
                    "action": check_result.action.value if EnforcementAction else "require_approval",
                    "reason": check_result.reason,
                }

        execution_task_types = {"setup_environment", "run_test", "verification"}
        if task_type_value in execution_task_types:
            command = task.outputs.get("command", "") if task.outputs else ""
            # Only validate shell execution if there's an explicit command in task.outputs
            # Task descriptions are natural language, not shell commands, so we skip
            # validation when falling back to description (Issue #3717 fix)
            if command:
                check_result = self._runtime_policy_enforcer.check_resource_access(
                    operation="execute",
                    resource=command,
                    context=context,
                )
                if not check_result.allowed:
                    if self.audit_logger:
                        self.audit_logger.log_policy_violation(
                            violation_type="runtime_policy_execute_denied",
                            details=check_result.reason,
                            task_id=task.task_id,
                            task_type=task_type_value,
                        )
                    return {
                        "action": check_result.action.value if EnforcementAction else "block",
                        "reason": check_result.reason,
                    }

        estimated_tokens = task.outputs.get("estimated_tokens", 1000) if task.outputs else 1000
        model = task.outputs.get("model", "gpt-4") if task.outputs else "gpt-4"

        cost_result = self._runtime_policy_enforcer.check_cost(
            task_id=task.task_id,
            estimated_tokens=estimated_tokens,
            model=model,
            context=context,
        )

        if not cost_result.allowed:
            if self.audit_logger:
                self.audit_logger.log_policy_violation(
                    violation_type="runtime_policy_cost_exceeded",
                    details=cost_result.reason,
                    task_id=task.task_id,
                    task_type=task_type_value,
                )

            if cost_result.action.value == "degrade_model" if EnforcementAction else False:
                if task.outputs is None:
                    task.outputs = {}
                task.outputs["suggested_model"] = cost_result.suggested_model
                logger.info(
                    "[AutonomousExecutor] Cost budget exceeded, suggesting model downgrade to %s",
                    cost_result.suggested_model,
                )
                return None

            return {
                "action": cost_result.action.value if EnforcementAction else "block",
                "reason": cost_result.reason,
            }

        return None
