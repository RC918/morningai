"""
Flow Controller v3 - Intelligent Dynamic State Machine

EPIC F Phase F-2: Flow Controller Integration

This module implements the Flow Controller that consumes PlannerOutput
and orchestrates task execution based on flow templates and DAG dependencies.

Blueprint Reference: Section 3.2 (Flow Controller v3 - Intelligent Dynamic State Machine)

Key Features:
- Flow template-based routing (full_pipeline, review_heavy, test_heavy, etc.)
- DAG-based task execution with dependency tracking
- Parallel execution support for independent tasks
- Integration with existing agent dispatch mechanisms

Usage:
    from core.planner.flow_controller import FlowController
    from core.planner.planner_types import PlannerOutput

    # Create controller with custom executor
    controller = FlowController(task_executor=my_executor)

    # Execute a plan
    result = controller.execute_plan(plan)

    # Or get next executable tasks for manual control
    tasks = controller.get_next_executable_tasks(plan, completed_set)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set

from .consumer import (
    BasePlanConsumer,
    ExecutionResult,
    ExecutionStatus,
    TaskResult,
)
from .planner_types import (
    PlannerOutput,
    TaskNode,
    TaskType,
)

logger = logging.getLogger(__name__)


class ContentSafetyError(Exception):
    """Raised when content safety check fails with BLOCK action."""

    def __init__(self, message: str, violation_type: str, risk_level: str):
        super().__init__(message)
        self.violation_type = violation_type
        self.risk_level = risk_level


class ApprovalRequiredError(Exception):
    """Raised when content safety check requires human approval."""

    def __init__(self, message: str, violation_type: str, risk_level: str):
        super().__init__(message)
        self.violation_type = violation_type
        self.risk_level = risk_level


class FlowTemplate(Enum):
    """
    Supported flow templates for task execution.

    Each template defines a different execution strategy optimized
    for specific task types.
    """
    FULL_PIPELINE = "full_pipeline"
    REVIEW_HEAVY = "review_heavy"
    TEST_HEAVY = "test_heavy"
    DOC_ONLY = "doc_only"
    ANALYSIS_ONLY = "analysis_only"
    CODE_ONLY = "code_only"


@dataclass
class FlowStage:
    """
    Represents a stage in the flow execution.

    Attributes:
        name: Stage identifier
        task_types: Task types that belong to this stage
        required: Whether this stage is required
        max_iterations: Maximum iterations for this stage (for retry loops)
    """
    name: str
    task_types: List[TaskType]
    required: bool = True
    max_iterations: int = 1


@dataclass
class FlowDefinition:
    """
    Defines the execution flow for a template.

    Attributes:
        template: The flow template this definition applies to
        stages: Ordered list of stages in the flow
        allow_parallel: Whether parallel execution is allowed
        require_review: Whether review stage is required
        require_tests: Whether test stage is required
    """
    template: FlowTemplate
    stages: List[FlowStage]
    allow_parallel: bool = True
    require_review: bool = True
    require_tests: bool = True


# Flow template definitions
FLOW_DEFINITIONS: Dict[FlowTemplate, FlowDefinition] = {
    FlowTemplate.FULL_PIPELINE: FlowDefinition(
        template=FlowTemplate.FULL_PIPELINE,
        stages=[
            FlowStage(name="setup", task_types=[TaskType.SETUP]),
            FlowStage(name="analyze", task_types=[TaskType.ANALYZE]),
            FlowStage(name="code", task_types=[TaskType.CODE]),
            FlowStage(name="test", task_types=[TaskType.TEST]),
            FlowStage(name="review", task_types=[TaskType.REVIEW]),
            FlowStage(name="document", task_types=[TaskType.DOCUMENT], required=False),
            FlowStage(name="deploy", task_types=[TaskType.DEPLOY], required=False),
            FlowStage(name="verify", task_types=[TaskType.VERIFY]),
        ],
        allow_parallel=True,
        require_review=True,
        require_tests=True,
    ),
    FlowTemplate.REVIEW_HEAVY: FlowDefinition(
        template=FlowTemplate.REVIEW_HEAVY,
        stages=[
            FlowStage(name="setup", task_types=[TaskType.SETUP]),
            FlowStage(name="analyze", task_types=[TaskType.ANALYZE]),
            FlowStage(name="code", task_types=[TaskType.CODE]),
            FlowStage(name="review", task_types=[TaskType.REVIEW], max_iterations=3),
            FlowStage(name="test", task_types=[TaskType.TEST]),
            FlowStage(name="verify", task_types=[TaskType.VERIFY]),
        ],
        allow_parallel=True,
        require_review=True,
        require_tests=True,
    ),
    FlowTemplate.TEST_HEAVY: FlowDefinition(
        template=FlowTemplate.TEST_HEAVY,
        stages=[
            FlowStage(name="setup", task_types=[TaskType.SETUP]),
            FlowStage(name="analyze", task_types=[TaskType.ANALYZE]),
            FlowStage(name="code", task_types=[TaskType.CODE]),
            FlowStage(name="test", task_types=[TaskType.TEST], max_iterations=3),
            FlowStage(name="review", task_types=[TaskType.REVIEW]),
            FlowStage(name="verify", task_types=[TaskType.VERIFY]),
        ],
        allow_parallel=True,
        require_review=True,
        require_tests=True,
    ),
    FlowTemplate.DOC_ONLY: FlowDefinition(
        template=FlowTemplate.DOC_ONLY,
        stages=[
            FlowStage(name="analyze", task_types=[TaskType.ANALYZE]),
            FlowStage(name="document", task_types=[TaskType.DOCUMENT]),
            FlowStage(name="review", task_types=[TaskType.REVIEW]),
        ],
        allow_parallel=False,
        require_review=True,
        require_tests=False,
    ),
    FlowTemplate.ANALYSIS_ONLY: FlowDefinition(
        template=FlowTemplate.ANALYSIS_ONLY,
        stages=[
            FlowStage(name="analyze", task_types=[TaskType.ANALYZE]),
            FlowStage(name="document", task_types=[TaskType.DOCUMENT], required=False),
        ],
        allow_parallel=False,
        require_review=False,
        require_tests=False,
    ),
    FlowTemplate.CODE_ONLY: FlowDefinition(
        template=FlowTemplate.CODE_ONLY,
        stages=[
            FlowStage(name="setup", task_types=[TaskType.SETUP], required=False),
            FlowStage(name="code", task_types=[TaskType.CODE]),
            FlowStage(name="verify", task_types=[TaskType.VERIFY], required=False),
        ],
        allow_parallel=True,
        require_review=False,
        require_tests=False,
    ),
}


class TaskExecutor(Protocol):
    """
    Protocol for task execution.

    Implementations should handle the actual execution of tasks,
    delegating to appropriate agents based on task type.
    """

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """
        Execute a single task.

        Args:
            task: The TaskNode to execute
            context: Execution context (plan info, previous results, etc.)

        Returns:
            TaskResult with execution status and outputs
        """
        ...


class DefaultTaskExecutor:
    """
    Default task executor that simulates execution.

    This is a placeholder implementation. In production, this would
    delegate to actual agent implementations (DevAgent, ReviewerAgent, etc.)
    """

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """
        Execute a task (placeholder implementation).

        In production, this would:
        1. Route to appropriate agent based on task_type
        2. Pass task inputs and context
        3. Collect and return results
        """
        logger.info(
            f"[FlowController] Executing task: {task.task_id}",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "operation": "execute_task",
            }
        )

        # Placeholder: simulate successful execution
        return TaskResult(
            task_id=task.task_id,
            status=ExecutionStatus.COMPLETED,
            outputs={"executed": True, "task_type": task.task_type.value},
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            actual_duration_minutes=task.estimated_duration_minutes,
        )


@dataclass
class FlowState:
    """
    Tracks the current state of flow execution.

    Attributes:
        plan_id: ID of the plan being executed
        current_stage: Current stage name
        completed_tasks: Set of completed task IDs
        failed_tasks: Set of failed task IDs
        skipped_tasks: Set of skipped task IDs
        stage_iterations: Number of iterations per stage
        task_results: Results for each executed task
    """
    plan_id: str
    current_stage: str = ""
    completed_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)
    skipped_tasks: Set[str] = field(default_factory=set)
    stage_iterations: Dict[str, int] = field(default_factory=dict)
    task_results: List[TaskResult] = field(default_factory=list)

    def mark_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        self.completed_tasks.add(task_id)

    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed."""
        self.failed_tasks.add(task_id)

    def mark_skipped(self, task_id: str) -> None:
        """Mark a task as skipped."""
        self.skipped_tasks.add(task_id)
        # Skipped tasks count as completed for dependency resolution
        self.completed_tasks.add(task_id)

    def increment_stage_iteration(self, stage: str) -> int:
        """Increment and return the iteration count for a stage."""
        self.stage_iterations[stage] = self.stage_iterations.get(stage, 0) + 1
        return self.stage_iterations[stage]

    def get_stage_iteration(self, stage: str) -> int:
        """Get the current iteration count for a stage."""
        return self.stage_iterations.get(stage, 0)


class FlowController(BasePlanConsumer):
    """
    Flow Controller v3 - Intelligent Dynamic State Machine.

    This controller consumes PlannerOutput and orchestrates task execution
    based on flow templates and DAG dependencies.

    Features:
    - Flow template-based routing
    - DAG-based task execution with dependency tracking
    - Parallel execution support
    - Stage-based iteration control
    - Risk-aware execution (respects requires_approval)

    Usage:
        controller = FlowController()
        result = controller.execute_plan(plan)
    """

    def __init__(
        self,
        task_executor: Optional[TaskExecutor] = None,
        max_parallel: int = 3,
        stop_on_failure: bool = True,
    ):
        """
        Initialize the FlowController.

        Args:
            task_executor: Custom task executor (uses DefaultTaskExecutor if None)
            max_parallel: Maximum number of tasks to execute in parallel
            stop_on_failure: Whether to stop execution on task failure
        """
        super().__init__(max_parallel=max_parallel)
        self.task_executor = task_executor or DefaultTaskExecutor()
        self.stop_on_failure = stop_on_failure

    def get_flow_definition(self, template_name: str) -> FlowDefinition:
        """
        Get the flow definition for a template name.

        Args:
            template_name: Name of the flow template

        Returns:
            FlowDefinition for the template (defaults to FULL_PIPELINE)
        """
        try:
            template = FlowTemplate(template_name)
            return FLOW_DEFINITIONS.get(template, FLOW_DEFINITIONS[FlowTemplate.FULL_PIPELINE])
        except ValueError:
            logger.warning(
                f"[FlowController] Unknown flow template: {template_name}, using full_pipeline",
                extra={"template": template_name, "operation": "get_flow_definition"}
            )
            return FLOW_DEFINITIONS[FlowTemplate.FULL_PIPELINE]

    def get_tasks_for_stage(
        self,
        plan: PlannerOutput,
        stage: FlowStage,
        state: FlowState,
    ) -> List[TaskNode]:
        """
        Get tasks that belong to a specific stage and are ready for execution.

        Args:
            plan: The plan being executed
            stage: The current stage
            state: Current flow state

        Returns:
            List of TaskNodes ready for execution in this stage
        """
        executable = plan.task_tree.get_executable_tasks(state.completed_tasks)

        # Filter to tasks that match this stage's task types
        stage_tasks = [
            task for task in executable
            if task.task_type in stage.task_types
        ]

        return stage_tasks

    def should_skip_stage(
        self,
        plan: PlannerOutput,
        stage: FlowStage,
        flow_def: FlowDefinition,
    ) -> bool:
        """
        Determine if a stage should be skipped.

        Args:
            plan: The plan being executed
            stage: The stage to check
            flow_def: The flow definition

        Returns:
            True if the stage should be skipped
        """
        # Check if stage is required
        if not stage.required:
            # Check if there are any tasks for this stage
            has_tasks = any(
                node.task_type in stage.task_types
                for node in plan.task_tree.nodes
            )
            if not has_tasks:
                return True

        # Check flow-level requirements
        if stage.name == "review" and not flow_def.require_review:
            return True
        if stage.name == "test" and not flow_def.require_tests:
            return True

        return False

    def _get_policy_enforcer(self) -> Any:
        """Get the RuntimePolicyEnforcer singleton instance."""
        try:
            from governance.runtime_policy_enforcer import get_runtime_policy_enforcer
            return get_runtime_policy_enforcer()
        except ImportError:
            logger.warning(
                "[FlowController] RuntimePolicyEnforcer not available, "
                "safety checks will be skipped"
            )
            return None

    def _check_input_safety(
        self,
        task: TaskNode,
        context: Dict[str, Any],
    ) -> None:
        """
        Input Guard: Check task input for content safety before execution.

        Scans task description and goal for:
        - Prompt injection attempts
        - Jailbreak attempts
        - Harmful content

        Args:
            task: The TaskNode to check
            context: Execution context with plan metadata

        Raises:
            ContentSafetyError: If content is blocked (critical risk)
            ApprovalRequiredError: If content requires approval (high risk)
                                   and task doesn't have requires_approval=True
        """
        enforcer = self._get_policy_enforcer()
        if enforcer is None:
            return

        input_content = f"{task.description}\n{context.get('goal', '')}"

        logger.debug(
            "[FlowController] Running input safety check",
            extra={
                "task_id": task.task_id,
                "content_length": len(input_content),
                "operation": "input_safety_check",
            }
        )

        try:
            result = enforcer.check_content_safety(
                content=input_content,
                context={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "check_type": "input_guard",
                    **context,
                },
                scan_pii=False,
                scan_content_safety=True,
            )

            if not result.allowed:
                from governance.runtime_policy_enforcer import EnforcementAction

                risk_level = result.context.get("risk_level", "unknown")
                violation_type = result.violation_type or "content_safety"

                if result.action == EnforcementAction.BLOCK:
                    logger.warning(
                        "[FlowController] Input blocked by safety check",
                        extra={
                            "task_id": task.task_id,
                            "violation_type": violation_type,
                            "risk_level": risk_level,
                            "reason": result.reason,
                            "operation": "input_safety_check",
                        }
                    )
                    raise ContentSafetyError(
                        f"Task input blocked: {result.reason}",
                        violation_type=violation_type,
                        risk_level=risk_level,
                    )

                elif result.action == EnforcementAction.REQUIRE_APPROVAL:
                    if not task.requires_approval:
                        logger.warning(
                            "[FlowController] Input requires approval",
                            extra={
                                "task_id": task.task_id,
                                "violation_type": violation_type,
                                "risk_level": risk_level,
                                "reason": result.reason,
                                "operation": "input_safety_check",
                            }
                        )
                        raise ApprovalRequiredError(
                            f"Task input requires approval: {result.reason}",
                            violation_type=violation_type,
                            risk_level=risk_level,
                        )
                    else:
                        logger.info(
                            "[FlowController] Input flagged but task has approval",
                            extra={
                                "task_id": task.task_id,
                                "violation_type": violation_type,
                                "risk_level": risk_level,
                                "operation": "input_safety_check",
                            }
                        )

                else:
                    logger.info(
                        "[FlowController] Input safety check: advisory warning",
                        extra={
                            "task_id": task.task_id,
                            "action": result.action.value if result.action else "none",
                            "reason": result.reason,
                            "operation": "input_safety_check",
                        }
                    )

        except (ContentSafetyError, ApprovalRequiredError):
            raise
        except Exception as e:
            logger.error(
                f"[FlowController] Input safety check failed: {e}",
                extra={
                    "task_id": task.task_id,
                    "error": str(e),
                    "operation": "input_safety_check",
                },
                exc_info=True,
            )

    def _check_output_safety(
        self,
        task: TaskNode,
        result: TaskResult,
        context: Dict[str, Any],
    ) -> TaskResult:
        """
        Output Guard: Check task output for PII and content safety.

        Scans task outputs for:
        - Personally Identifiable Information (PII)
        - Sensitive data leakage

        Args:
            task: The TaskNode that was executed
            result: The TaskResult from execution
            context: Execution context with plan metadata

        Returns:
            TaskResult with potentially redacted outputs

        Raises:
            ContentSafetyError: If output is blocked
        """
        enforcer = self._get_policy_enforcer()
        if enforcer is None:
            return result

        output_content = str(result.outputs) if result.outputs else ""
        if not output_content:
            return result

        logger.debug(
            "[FlowController] Running output safety check",
            extra={
                "task_id": task.task_id,
                "content_length": len(output_content),
                "operation": "output_safety_check",
            }
        )

        try:
            check_result = enforcer.check_content_safety(
                content=output_content,
                context={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "check_type": "output_guard",
                    **context,
                },
                scan_pii=True,
                scan_content_safety=True,
            )

            if not check_result.allowed:
                from governance.runtime_policy_enforcer import EnforcementAction

                risk_level = check_result.context.get("risk_level", "unknown")
                violation_type = check_result.violation_type or "pii_detected"

                if check_result.action == EnforcementAction.BLOCK:
                    logger.warning(
                        "[FlowController] Output blocked by safety check",
                        extra={
                            "task_id": task.task_id,
                            "violation_type": violation_type,
                            "risk_level": risk_level,
                            "reason": check_result.reason,
                            "operation": "output_safety_check",
                        }
                    )
                    raise ContentSafetyError(
                        f"Task output blocked: {check_result.reason}",
                        violation_type=violation_type,
                        risk_level=risk_level,
                    )

                elif check_result.action == EnforcementAction.REDACT:
                    redacted_content = check_result.context.get("redacted_content")
                    if redacted_content:
                        logger.info(
                            "[FlowController] Output redacted by safety check",
                            extra={
                                "task_id": task.task_id,
                                "violation_type": violation_type,
                                "operation": "output_safety_check",
                            }
                        )
                        return TaskResult(
                            task_id=result.task_id,
                            status=result.status,
                            outputs={"redacted_output": redacted_content},
                            error_message=result.error_message,
                            started_at=result.started_at,
                            completed_at=result.completed_at,
                            metadata={
                                **(result.metadata or {}),
                                "safety_redacted": True,
                                "original_pii_findings": check_result.context.get(
                                    "findings", []
                                ),
                            },
                        )

                elif check_result.action == EnforcementAction.REQUIRE_APPROVAL:
                    logger.warning(
                        "[FlowController] Output requires approval review",
                        extra={
                            "task_id": task.task_id,
                            "violation_type": violation_type,
                            "risk_level": risk_level,
                            "reason": check_result.reason,
                            "operation": "output_safety_check",
                        }
                    )
                    return TaskResult(
                        task_id=result.task_id,
                        status=result.status,
                        outputs=result.outputs,
                        error_message=result.error_message,
                        started_at=result.started_at,
                        completed_at=result.completed_at,
                        metadata={
                            **(result.metadata or {}),
                            "safety_review_required": True,
                            "safety_reason": check_result.reason,
                        },
                    )

        except ContentSafetyError:
            raise
        except Exception as e:
            logger.error(
                f"[FlowController] Output safety check failed: {e}",
                extra={
                    "task_id": task.task_id,
                    "error": str(e),
                    "operation": "output_safety_check",
                },
                exc_info=True,
            )

        return result

    def execute_task(self, task: TaskNode, plan: PlannerOutput) -> TaskResult:
        """
        Execute a single task using the configured executor.

        This method implements dual-direction safety interception:
        1. Input Guard (Pre-execution): Scans task input for content safety
        2. Task Execution: Runs the actual task
        3. Output Guard (Post-execution): Scans output for PII and safety

        Args:
            task: The TaskNode to execute
            plan: The parent PlannerOutput for context

        Returns:
            TaskResult with execution status and outputs (potentially redacted)

        Raises:
            ContentSafetyError: If content is blocked by safety checks
            ApprovalRequiredError: If content requires human approval
        """
        context = {
            "plan_id": plan.plan_id,
            "plan_type": plan.plan_type.value,
            "goal": plan.goal,
            "flow_template": plan.flow_template,
            "risk_level": plan.risk_metadata.overall_risk.value,
        }

        logger.info(
            "[FlowController] Starting task execution",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "requires_approval": task.requires_approval,
                "operation": "execute_task",
            }
        )

        try:
            self._check_input_safety(task, context)

            result = self.task_executor.execute(task, context)

            result = self._check_output_safety(task, result, context)

            logger.info(
                "[FlowController] Task completed",
                extra={
                    "task_id": task.task_id,
                    "status": result.status.value,
                    "safety_redacted": result.metadata.get("safety_redacted", False)
                    if result.metadata
                    else False,
                    "operation": "execute_task",
                }
            )
            return result

        except (ContentSafetyError, ApprovalRequiredError) as e:
            logger.warning(
                f"[FlowController] Task blocked by safety check: {e}",
                extra={
                    "task_id": task.task_id,
                    "error_type": type(e).__name__,
                    "violation_type": e.violation_type,
                    "risk_level": e.risk_level,
                    "operation": "execute_task",
                }
            )
            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                outputs={},
                error_message=str(e),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                metadata={
                    "blocked_by_safety": True,
                    "violation_type": e.violation_type,
                    "risk_level": e.risk_level,
                },
            )

        except Exception as e:
            logger.error(
                f"[FlowController] Task execution failed: {e}",
                extra={
                    "task_id": task.task_id,
                    "error": str(e),
                    "operation": "execute_task",
                },
                exc_info=True,
            )
            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                outputs={},
                error_message=str(e),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )

    def execute_plan(self, plan: PlannerOutput) -> ExecutionResult:
        """
        Execute a complete plan using flow template routing.

        This method:
        1. Validates the plan
        2. Gets the appropriate flow definition
        3. Executes tasks stage by stage
        4. Handles parallel execution where allowed
        5. Respects DAG dependencies

        Args:
            plan: The PlannerOutput to execute

        Returns:
            ExecutionResult with status and task results
        """
        # Validate plan first
        errors = plan.validate()
        if errors:
            return ExecutionResult(
                plan_id=plan.plan_id,
                status=ExecutionStatus.FAILED,
                task_results=[],
                error_summary=f"Plan validation failed: {'; '.join(errors[:5])}",
            )

        # Get flow definition
        flow_def = self.get_flow_definition(plan.flow_template)

        logger.info(
            "[FlowController] Starting plan execution",
            extra={
                "plan_id": plan.plan_id,
                "flow_template": plan.flow_template,
                "task_count": len(plan.task_tree.nodes),
                "operation": "execute_plan",
            }
        )

        # Initialize state
        state = FlowState(plan_id=plan.plan_id)
        start_time = datetime.now(timezone.utc)

        # Execute stages in order
        for stage in flow_def.stages:
            # Check if stage should be skipped
            if self.should_skip_stage(plan, stage, flow_def):
                logger.debug(
                    f"[FlowController] Skipping stage: {stage.name}",
                    extra={"stage": stage.name, "operation": "execute_plan"}
                )
                continue

            state.current_stage = stage.name

            # Execute stage with iteration support
            for iteration in range(stage.max_iterations):
                state.increment_stage_iteration(stage.name)

                # Get tasks for this stage
                stage_tasks = self.get_tasks_for_stage(plan, stage, state)

                if not stage_tasks:
                    break

                # Execute tasks (parallel or sequential based on flow definition)
                if flow_def.allow_parallel and self.can_parallelize(stage_tasks):
                    # Execute in parallel (simplified: still sequential for now)
                    # TODO: Implement actual parallel execution in future phase
                    for task in stage_tasks:
                        result = self._execute_and_update_state(task, plan, state)
                        if result.status == ExecutionStatus.FAILED and self.stop_on_failure:
                            return self._build_failure_result(plan, state, start_time, task, result)
                else:
                    # Execute sequentially
                    for task in stage_tasks:
                        result = self._execute_and_update_state(task, plan, state)
                        if result.status == ExecutionStatus.FAILED and self.stop_on_failure:
                            return self._build_failure_result(plan, state, start_time, task, result)

        # Execute any remaining tasks not covered by stages (DAG-based)
        while True:
            remaining = plan.task_tree.get_executable_tasks(state.completed_tasks)
            if not remaining:
                break

            for task in remaining:
                result = self._execute_and_update_state(task, plan, state)
                if result.status == ExecutionStatus.FAILED and self.stop_on_failure:
                    return self._build_failure_result(plan, state, start_time, task, result)

        # Build final result
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds() / 60)

        all_completed = len(state.completed_tasks) == len(plan.task_tree.nodes)
        status = ExecutionStatus.COMPLETED if all_completed else ExecutionStatus.FAILED

        logger.info(
            "[FlowController] Plan execution completed",
            extra={
                "plan_id": plan.plan_id,
                "status": status.value,
                "completed_tasks": len(state.completed_tasks),
                "total_tasks": len(plan.task_tree.nodes),
                "duration_minutes": duration,
                "operation": "execute_plan",
            }
        )

        return ExecutionResult(
            plan_id=plan.plan_id,
            status=status,
            task_results=state.task_results,
            total_duration_minutes=duration,
        )

    def _has_failed_dependency(
        self,
        task: TaskNode,
        plan: PlannerOutput,
        state: FlowState,
    ) -> bool:
        """
        Check if a task has any failed or skipped dependencies.

        A task should be skipped if any of its dependencies:
        - Failed directly
        - Were skipped due to their own failed dependencies

        Args:
            task: The task to check
            plan: The parent plan
            state: Current flow state

        Returns:
            True if any dependency has failed or was skipped due to failure
        """
        deps = plan.task_tree.get_dependencies(task.task_id)
        # Check both failed_tasks and skipped_tasks (skipped due to failed deps)
        blocked_tasks = state.failed_tasks | state.skipped_tasks
        return any(dep in blocked_tasks for dep in deps)

    def _skip_task_due_to_failed_dependency(
        self,
        task: TaskNode,
        state: FlowState,
    ) -> TaskResult:
        """
        Create a SKIPPED result for a task with failed dependencies.

        Args:
            task: The task to skip
            state: Current flow state

        Returns:
            TaskResult with SKIPPED status
        """
        result = TaskResult(
            task_id=task.task_id,
            status=ExecutionStatus.SKIPPED,
            outputs={},
            error_message="Skipped due to failed dependency",
        )
        state.task_results.append(result)
        state.mark_skipped(task.task_id)
        return result

    def _execute_and_update_state(
        self,
        task: TaskNode,
        plan: PlannerOutput,
        state: FlowState,
    ) -> TaskResult:
        """
        Execute a task and update the flow state.

        Args:
            task: The task to execute
            plan: The parent plan
            state: The current flow state

        Returns:
            TaskResult from execution
        """
        # Check for failed dependencies first
        if self._has_failed_dependency(task, plan, state):
            return self._skip_task_due_to_failed_dependency(task, state)

        result = self.execute_task(task, plan)
        state.task_results.append(result)

        if result.status == ExecutionStatus.COMPLETED:
            state.mark_completed(task.task_id)
        elif result.status == ExecutionStatus.SKIPPED:
            state.mark_skipped(task.task_id)
        elif result.status == ExecutionStatus.FAILED:
            state.mark_failed(task.task_id)
            # Also mark as completed to prevent infinite loops when stop_on_failure=False
            # This allows dependent tasks to be skipped/blocked appropriately
            state.completed_tasks.add(task.task_id)

        return result

    def _build_failure_result(
        self,
        plan: PlannerOutput,
        state: FlowState,
        start_time: datetime,
        failed_task: TaskNode,
        failed_result: TaskResult,
    ) -> ExecutionResult:
        """
        Build an ExecutionResult for a failed execution.

        Args:
            plan: The plan that was being executed
            state: The current flow state
            start_time: When execution started
            failed_task: The task that failed
            failed_result: The result of the failed task

        Returns:
            ExecutionResult with failure information
        """
        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds() / 60)

        # Sanitize error message for logging
        safe_task_id = failed_task.task_id[:100] if failed_task.task_id else "unknown"
        safe_error = (failed_result.error_message or "")[:200]

        return ExecutionResult(
            plan_id=plan.plan_id,
            status=ExecutionStatus.FAILED,
            task_results=state.task_results,
            total_duration_minutes=duration,
            error_summary=f"Task {safe_task_id} failed: {safe_error}",
        )


def create_flow_controller(
    task_executor: Optional[TaskExecutor] = None,
    max_parallel: int = 3,
    stop_on_failure: bool = True,
) -> FlowController:
    """
    Factory function to create a FlowController.

    Args:
        task_executor: Custom task executor (uses DefaultTaskExecutor if None)
        max_parallel: Maximum number of tasks to execute in parallel
        stop_on_failure: Whether to stop execution on task failure

    Returns:
        Configured FlowController instance
    """
    return FlowController(
        task_executor=task_executor,
        max_parallel=max_parallel,
        stop_on_failure=stop_on_failure,
    )
