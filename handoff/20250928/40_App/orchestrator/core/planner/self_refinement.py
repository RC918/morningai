"""
Self-refinement Loop - Plan Execute Feedback Replan Closed Loop

EPIC F Phase F-5: Self-refinement Loop

This module implements the plan -> execute -> feedback -> replan closed loop
for automatic recovery from task failures with failure learning context.

Blueprint Reference: Section F-5 (Self-refinement Loop)

Key Features:
- FeedbackCollector: Collects and aggregates execution feedback
- Replanner: Replans based on execution feedback (partial or full)
- SelfRefinementLoop: Orchestrates the closed loop execution
- Replan limits with HITL escalation

Usage:
    from core.planner.self_refinement import SelfRefinementLoop
    from core.planner.planner_types import PlannerOutput

    loop = SelfRefinementLoop(planner=my_planner, executor=my_executor)
    result = loop.execute_with_refinement(plan)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set

from .consumer import ExecutionResult, ExecutionStatus, TaskResult
from .planner_types import (
    EdgeType,
    PlannerMetadata,
    PlannerOutput,
    RiskLevel,
    RiskMetadata,
    TaskEdge,
    TaskNode,
    TaskTree,
    TaskType,
)

logger = logging.getLogger(__name__)


def _get_settings():
    """Get settings with fallback for testing."""
    try:
        from common.config.settings import settings
        return settings
    except ImportError:
        return None


USE_SELF_REFINEMENT = _get_settings().use_self_refinement if _get_settings() else False
MAX_TASK_REPLANS = _get_settings().self_refinement_max_task_replans if _get_settings() else 3
MAX_FULL_REPLANS = _get_settings().self_refinement_max_full_replans if _get_settings() else 2


class FeedbackStatus(Enum):
    """Status of execution feedback"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ExecutionFeedback:
    """
    Feedback from task execution.

    Blueprint Reference: Section F-5 FeedbackCollector

    Attributes:
        task_id: ID of the executed task
        status: Execution status (success, failed, partial)
        error_message: Error message if failed
        actual_duration_minutes: Actual time taken
        outputs: Output data from the task
        failure_context: Context from failure learning
    """
    task_id: str
    status: FeedbackStatus
    error_message: Optional[str] = None
    actual_duration_minutes: int = 0
    outputs: Dict[str, Any] = field(default_factory=dict)
    failure_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "error_message": self.error_message,
            "actual_duration_minutes": self.actual_duration_minutes,
            "outputs": self.outputs,
            "failure_context": self.failure_context,
        }

    @classmethod
    def from_task_result(cls, result: TaskResult) -> "ExecutionFeedback":
        """Create ExecutionFeedback from TaskResult"""
        if result.status == ExecutionStatus.COMPLETED:
            status = FeedbackStatus.SUCCESS
        elif result.status == ExecutionStatus.FAILED:
            status = FeedbackStatus.FAILED
        else:
            status = FeedbackStatus.PARTIAL

        return cls(
            task_id=result.task_id,
            status=status,
            error_message=result.error_message,
            actual_duration_minutes=result.actual_duration_minutes,
            outputs=result.outputs,
        )


@dataclass
class PlanFeedback:
    """
    Aggregated feedback for a plan execution.

    Blueprint Reference: Section F-5 FeedbackCollector.aggregate()

    Attributes:
        plan_id: ID of the plan
        feedbacks: List of task feedbacks
        has_failures: Whether any tasks failed
        recoverable: Whether failures are recoverable
        failed_task_ids: IDs of failed tasks
        success_rate: Percentage of successful tasks
    """
    plan_id: str
    feedbacks: List[ExecutionFeedback] = field(default_factory=list)
    has_failures: bool = False
    recoverable: bool = True
    failed_task_ids: List[str] = field(default_factory=list)
    success_rate: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "plan_id": self.plan_id,
            "feedbacks": [f.to_dict() for f in self.feedbacks],
            "has_failures": self.has_failures,
            "recoverable": self.recoverable,
            "failed_task_ids": self.failed_task_ids,
            "success_rate": self.success_rate,
        }


class FeedbackCollector:
    """
    Collects and aggregates execution feedback.

    Blueprint Reference: Section F-5 FeedbackCollector

    This class is responsible for:
    - Converting TaskResult to ExecutionFeedback
    - Aggregating feedbacks into PlanFeedback
    - Determining recoverability of failures
    """

    def collect(self, task_id: str, result: TaskResult) -> ExecutionFeedback:
        """
        Collect feedback from a task execution.

        Args:
            task_id: ID of the task
            result: TaskResult from execution

        Returns:
            ExecutionFeedback with status and context
        """
        feedback = ExecutionFeedback.from_task_result(result)

        if feedback.status == FeedbackStatus.FAILED:
            feedback.failure_context = self._get_failure_context(
                task_id, result.error_message
            )

        logger.debug(
            "[FeedbackCollector] Collected feedback for task %s: %s",
            task_id, feedback.status.value
        )

        return feedback

    def aggregate(self, feedbacks: List[ExecutionFeedback], plan_id: str) -> PlanFeedback:
        """
        Aggregate feedbacks into plan-level feedback.

        Args:
            feedbacks: List of task feedbacks
            plan_id: ID of the plan

        Returns:
            PlanFeedback with aggregated status
        """
        failed_ids = [
            f.task_id for f in feedbacks
            if f.status == FeedbackStatus.FAILED
        ]

        success_count = sum(
            1 for f in feedbacks
            if f.status == FeedbackStatus.SUCCESS
        )

        success_rate = success_count / len(feedbacks) if feedbacks else 1.0

        recoverable = self._is_recoverable(feedbacks)

        plan_feedback = PlanFeedback(
            plan_id=plan_id,
            feedbacks=feedbacks,
            has_failures=len(failed_ids) > 0,
            recoverable=recoverable,
            failed_task_ids=failed_ids,
            success_rate=success_rate,
        )

        logger.info(
            "[FeedbackCollector] Aggregated feedback for plan %s: "
            "success_rate=%.2f, has_failures=%s, recoverable=%s",
            plan_id[:8], success_rate, plan_feedback.has_failures, recoverable
        )

        return plan_feedback

    def _get_failure_context(
        self, task_id: str, error_message: Optional[str]
    ) -> Optional[str]:
        """Get failure learning context from Observer Node."""
        try:
            try:
                from observer_node import get_learning_context
            except ImportError:
                from orchestrator.observer_node import get_learning_context

            context = get_learning_context(
                goal_summary=f"Task {task_id} failed: {error_message or 'unknown error'}",
                task_type=None
            )
            return context
        except Exception as e:
            logger.debug(
                "[FeedbackCollector] Failed to get failure context: %s", e
            )
            return None

    def _is_recoverable(self, feedbacks: List[ExecutionFeedback]) -> bool:
        """
        Determine if failures are recoverable.

        Failures are considered non-recoverable if:
        - More than 50% of tasks failed
        - Critical infrastructure failures detected
        """
        if not feedbacks:
            return True

        failed_count = sum(
            1 for f in feedbacks
            if f.status == FeedbackStatus.FAILED
        )

        failure_rate = failed_count / len(feedbacks)

        if failure_rate > 0.5:
            return False

        for feedback in feedbacks:
            if feedback.error_message and any(
                keyword in feedback.error_message.lower()
                for keyword in ["authentication", "permission", "quota", "rate limit"]
            ):
                return False

        return True


class Replanner:
    """
    Replans based on execution feedback.

    Blueprint Reference: Section F-5 Replanner

    This class is responsible for:
    - Determining if replanning is needed
    - Partial replan (single task and dependents)
    - Full replan with failure context
    """

    def __init__(self, max_task_replans: int = 3, max_full_replans: int = 2):
        """
        Initialize the Replanner.

        Args:
            max_task_replans: Maximum replans per task
            max_full_replans: Maximum full replans per plan
        """
        self.max_task_replans = max_task_replans
        self.max_full_replans = max_full_replans
        self._task_replan_counts: Dict[str, int] = {}
        self._full_replan_count: int = 0

    def should_replan(self, plan: PlannerOutput, feedback: PlanFeedback) -> bool:
        """
        Determine if replanning is needed.

        Args:
            plan: The current plan
            feedback: Aggregated feedback

        Returns:
            True if replanning should be attempted
        """
        if not feedback.has_failures:
            return False

        if not feedback.recoverable:
            logger.info(
                "[Replanner] Failures not recoverable for plan %s",
                plan.plan_id[:8]
            )
            return False

        if self._full_replan_count >= self.max_full_replans:
            logger.warning(
                "[Replanner] Max full replans (%d) reached for plan %s",
                self.max_full_replans, plan.plan_id[:8]
            )
            return False

        for task_id in feedback.failed_task_ids:
            if self._task_replan_counts.get(task_id, 0) >= self.max_task_replans:
                logger.warning(
                    "[Replanner] Max task replans (%d) reached for task %s",
                    self.max_task_replans, task_id
                )
                return False

        return True

    def replan_partial(
        self,
        plan: PlannerOutput,
        failed_task_id: str,
        feedback: ExecutionFeedback,
    ) -> PlannerOutput:
        """
        Replan only the failed subtask and its dependents.

        Args:
            plan: The current plan
            failed_task_id: ID of the failed task
            feedback: Feedback for the failed task

        Returns:
            Updated PlannerOutput with recovery tasks
        """
        self._task_replan_counts[failed_task_id] = (
            self._task_replan_counts.get(failed_task_id, 0) + 1
        )

        logger.info(
            "[Replanner] Partial replan for task %s (attempt %d/%d)",
            failed_task_id,
            self._task_replan_counts[failed_task_id],
            self.max_task_replans
        )

        failed_node = plan.task_tree.get_node(failed_task_id)
        if not failed_node:
            logger.error(
                "[Replanner] Failed task %s not found in plan", failed_task_id
            )
            return plan

        recovery_task = TaskNode(
            task_id=f"{failed_task_id}-recovery-{self._task_replan_counts[failed_task_id]}",
            task_type=TaskType.ANALYZE,
            description=f"Analyze and recover from failure: {feedback.error_message or 'unknown error'}"[:200],
            agent_assignment=failed_node.agent_assignment,
            estimated_duration_minutes=10,
            priority=-1,
            risk_level=RiskLevel.MEDIUM,
            inputs={
                "failed_task_id": failed_task_id,
                "error_message": feedback.error_message,
                "failure_context": feedback.failure_context,
                "original_description": failed_node.description,
            },
        )

        retry_task = TaskNode(
            task_id=f"{failed_task_id}-retry-{self._task_replan_counts[failed_task_id]}",
            task_type=failed_node.task_type,
            description=f"Retry: {failed_node.description}",
            agent_assignment=failed_node.agent_assignment,
            estimated_duration_minutes=failed_node.estimated_duration_minutes,
            priority=failed_node.priority,
            risk_level=failed_node.risk_level,
            inputs={
                **failed_node.inputs,
                "retry_attempt": self._task_replan_counts[failed_task_id],
                "failure_context": feedback.failure_context,
            },
        )

        new_nodes = list(plan.task_tree.nodes)
        new_nodes.append(recovery_task)
        new_nodes.append(retry_task)

        new_edges = list(plan.task_tree.edges)
        new_edges.append(TaskEdge(
            from_task=recovery_task.task_id,
            to_task=retry_task.task_id,
            edge_type=EdgeType.DEPENDS_ON,
        ))

        dependents = plan.task_tree.get_dependents(failed_task_id)
        for dep_id in dependents:
            for i, edge in enumerate(new_edges):
                if edge.from_task == failed_task_id and edge.to_task == dep_id:
                    new_edges[i] = TaskEdge(
                        from_task=retry_task.task_id,
                        to_task=dep_id,
                        edge_type=edge.edge_type,
                    )

        new_tree = TaskTree(nodes=new_nodes, edges=new_edges)

        new_metadata = PlannerMetadata(
            planner_type=plan.planner_metadata.planner_type,
            planning_time_ms=plan.planner_metadata.planning_time_ms,
            confidence_score=plan.planner_metadata.confidence_score * 0.9,
            trace_id=plan.planner_metadata.trace_id,
            provider=plan.planner_metadata.provider,
        )

        return PlannerOutput(
            plan_id=plan.plan_id,
            plan_type=plan.plan_type,
            goal=plan.goal,
            task_tree=new_tree,
            flow_template=plan.flow_template,
            model_tier_hints=plan.model_tier_hints,
            risk_metadata=RiskMetadata(
                overall_risk=RiskLevel.MEDIUM,
                requires_approval=plan.risk_metadata.requires_approval,
                trust_score_input=plan.risk_metadata.trust_score_input,
                risk_factors=plan.risk_metadata.risk_factors + [
                    f"Partial replan after task {failed_task_id} failure"
                ],
            ),
            cost_estimate=plan.cost_estimate,
            planner_metadata=new_metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def replan_full(
        self,
        plan: PlannerOutput,
        feedback: PlanFeedback,
    ) -> PlannerOutput:
        """
        Full replan with failure context.

        Args:
            plan: The current plan
            feedback: Aggregated feedback

        Returns:
            New PlannerOutput with full replan
        """
        self._full_replan_count += 1

        logger.info(
            "[Replanner] Full replan for plan %s (attempt %d/%d)",
            plan.plan_id[:8],
            self._full_replan_count,
            self.max_full_replans
        )

        failure_summary = "; ".join(
            f"{f.task_id}: {f.error_message or 'unknown'}"
            for f in feedback.feedbacks
            if f.status == FeedbackStatus.FAILED
        )[:500]

        new_goal = f"{plan.goal}\n\n[Replan Context] Previous attempt failed: {failure_summary}"

        new_metadata = PlannerMetadata(
            planner_type=plan.planner_metadata.planner_type,
            planning_time_ms=plan.planner_metadata.planning_time_ms,
            confidence_score=plan.planner_metadata.confidence_score * 0.8,
            trace_id=plan.planner_metadata.trace_id,
            provider=plan.planner_metadata.provider,
        )

        return PlannerOutput(
            plan_id=f"{plan.plan_id}-replan-{self._full_replan_count}",
            plan_type=plan.plan_type,
            goal=new_goal,
            task_tree=plan.task_tree,
            flow_template=plan.flow_template,
            model_tier_hints=plan.model_tier_hints,
            risk_metadata=RiskMetadata(
                overall_risk=RiskLevel.HIGH,
                requires_approval=True,
                trust_score_input=plan.risk_metadata.trust_score_input,
                risk_factors=plan.risk_metadata.risk_factors + [
                    f"Full replan attempt {self._full_replan_count}"
                ],
            ),
            cost_estimate=plan.cost_estimate,
            planner_metadata=new_metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_replan_counts(self) -> Dict[str, Any]:
        """Get current replan counts for monitoring."""
        return {
            "task_replans": dict(self._task_replan_counts),
            "full_replans": self._full_replan_count,
            "max_task_replans": self.max_task_replans,
            "max_full_replans": self.max_full_replans,
        }

    def reset(self) -> None:
        """Reset replan counts for a new plan execution."""
        self._task_replan_counts.clear()
        self._full_replan_count = 0


class TaskExecutorProtocol(Protocol):
    """Protocol for task execution."""

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """Execute a single task."""
        ...


class RefinementResult:
    """
    Result of self-refinement loop execution.

    Attributes:
        execution_result: Final execution result
        replan_history: History of replans performed
        escalated_to_hitl: Whether HITL escalation was triggered
        total_replans: Total number of replans performed
    """

    def __init__(
        self,
        execution_result: ExecutionResult,
        replan_history: List[Dict[str, Any]] = None,
        escalated_to_hitl: bool = False,
    ):
        self.execution_result = execution_result
        self.replan_history = replan_history or []
        self.escalated_to_hitl = escalated_to_hitl
        self.total_replans = len(self.replan_history)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "execution_result": self.execution_result.to_dict(),
            "replan_history": self.replan_history,
            "escalated_to_hitl": self.escalated_to_hitl,
            "total_replans": self.total_replans,
        }


class SelfRefinementLoop:
    """
    Orchestrates the plan -> execute -> feedback -> replan closed loop.

    Blueprint Reference: Section F-5 Self-refinement Loop

    This class coordinates:
    - Plan execution with feedback collection
    - Automatic replanning on failures
    - HITL escalation when limits exceeded
    - Failure learning context integration

    Usage:
        loop = SelfRefinementLoop(executor=my_executor)
        result = loop.execute_with_refinement(plan)
    """

    def __init__(
        self,
        executor: TaskExecutorProtocol,
        max_task_replans: int = None,
        max_full_replans: int = None,
    ):
        """
        Initialize the SelfRefinementLoop.

        Args:
            executor: Task executor for running tasks
            max_task_replans: Maximum replans per task (default from settings)
            max_full_replans: Maximum full replans (default from settings)
        """
        self.executor = executor
        self.feedback_collector = FeedbackCollector()
        self.replanner = Replanner(
            max_task_replans=max_task_replans or MAX_TASK_REPLANS,
            max_full_replans=max_full_replans or MAX_FULL_REPLANS,
        )
        self._replan_history: List[Dict[str, Any]] = []

    def execute_with_refinement(self, plan: PlannerOutput) -> RefinementResult:
        """
        Execute a plan with automatic refinement on failures.

        This method implements the closed loop:
        1. Execute plan
        2. Collect feedback
        3. If failures and recoverable, replan
        4. Repeat until success or limits exceeded

        Args:
            plan: The PlannerOutput to execute

        Returns:
            RefinementResult with execution result and replan history
        """
        if not USE_SELF_REFINEMENT:
            logger.debug(
                "[SelfRefinementLoop] Self-refinement disabled, executing without refinement"
            )
            result = self._execute_plan(plan)
            return RefinementResult(execution_result=result)

        logger.info(
            "[SelfRefinementLoop] Starting execution with refinement for plan %s",
            plan.plan_id[:8]
        )

        current_plan = plan
        self.replanner.reset()
        self._replan_history.clear()

        while True:
            result = self._execute_plan(current_plan)
            feedbacks = [
                self.feedback_collector.collect(r.task_id, r)
                for r in result.task_results
            ]
            plan_feedback = self.feedback_collector.aggregate(
                feedbacks, current_plan.plan_id
            )

            if result.status == ExecutionStatus.COMPLETED:
                logger.info(
                    "[SelfRefinementLoop] Plan %s completed successfully",
                    current_plan.plan_id[:8]
                )
                return RefinementResult(
                    execution_result=result,
                    replan_history=self._replan_history,
                )

            if not self.replanner.should_replan(current_plan, plan_feedback):
                logger.warning(
                    "[SelfRefinementLoop] Cannot replan for plan %s, escalating to HITL",
                    current_plan.plan_id[:8]
                )
                return RefinementResult(
                    execution_result=result,
                    replan_history=self._replan_history,
                    escalated_to_hitl=True,
                )

            if len(plan_feedback.failed_task_ids) == 1:
                failed_task_id = plan_feedback.failed_task_ids[0]
                failed_feedback = next(
                    f for f in feedbacks if f.task_id == failed_task_id
                )
                current_plan = self.replanner.replan_partial(
                    current_plan, failed_task_id, failed_feedback
                )
                self._replan_history.append({
                    "type": "partial",
                    "failed_task_id": failed_task_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            else:
                current_plan = self.replanner.replan_full(
                    current_plan, plan_feedback
                )
                self._replan_history.append({
                    "type": "full",
                    "failed_task_ids": plan_feedback.failed_task_ids,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            logger.info(
                "[SelfRefinementLoop] Replanned, continuing execution (replan count: %d)",
                len(self._replan_history)
            )

    def _execute_plan(self, plan: PlannerOutput) -> ExecutionResult:
        """
        Execute a plan using the configured executor.

        Args:
            plan: The plan to execute

        Returns:
            ExecutionResult with task results
        """
        errors = plan.validate()
        if errors:
            return ExecutionResult(
                plan_id=plan.plan_id,
                status=ExecutionStatus.FAILED,
                task_results=[],
                error_summary=f"Plan validation failed: {'; '.join(errors[:5])}",
            )

        completed: Set[str] = set()
        task_results: List[TaskResult] = []
        start_time = datetime.now(timezone.utc)

        while True:
            executable = plan.task_tree.get_executable_tasks(completed)
            if not executable:
                break

            for task in executable:
                context = {
                    "plan_id": plan.plan_id,
                    "goal": plan.goal,
                    "flow_template": plan.flow_template,
                }

                result = self.executor.execute(task, context)
                task_results.append(result)

                if result.status == ExecutionStatus.COMPLETED:
                    completed.add(task.task_id)
                elif result.status == ExecutionStatus.SKIPPED:
                    completed.add(task.task_id)
                elif result.status == ExecutionStatus.FAILED:
                    end_time = datetime.now(timezone.utc)
                    duration = int((end_time - start_time).total_seconds() / 60)
                    return ExecutionResult(
                        plan_id=plan.plan_id,
                        status=ExecutionStatus.FAILED,
                        task_results=task_results,
                        total_duration_minutes=duration,
                        error_summary=f"Task {task.task_id} failed: {result.error_message}",
                    )

        end_time = datetime.now(timezone.utc)
        duration = int((end_time - start_time).total_seconds() / 60)

        all_completed = len(completed) == len(plan.task_tree.nodes)
        status = ExecutionStatus.COMPLETED if all_completed else ExecutionStatus.FAILED

        return ExecutionResult(
            plan_id=plan.plan_id,
            status=status,
            task_results=task_results,
            total_duration_minutes=duration,
        )

    def get_replan_history(self) -> List[Dict[str, Any]]:
        """Get the history of replans performed."""
        return list(self._replan_history)

    def get_replan_counts(self) -> Dict[str, Any]:
        """Get current replan counts from the replanner."""
        return self.replanner.get_replan_counts()
