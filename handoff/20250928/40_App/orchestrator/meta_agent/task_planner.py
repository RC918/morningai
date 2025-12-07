"""
Task Planner - Automatic Subtask Decomposition for Meta Agent

This module implements automatic task decomposition, breaking down high-level
goals into executable subtasks with dependencies and execution order.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Issue: #2072 - Failure Learning Context Integration
Milestone: M5 - Meta Agent 優化

Features:
- Template-based task decomposition by goal type
- LLM-enhanced planning (optional)
- Failure learning context integration (Phase 2 Brain Layer)
- Automatic recovery planning from failures
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .goal_parser import GoalType, ParsedGoal

logger = logging.getLogger(__name__)


def _get_failure_learning_enabled() -> bool:
    """
    Check if failure learning context is enabled.

    Returns:
        True if ENABLE_FAILURE_LEARNING_CONTEXT is enabled, False otherwise
    """
    try:
        from common.config.settings import settings
        return getattr(settings, 'enable_failure_learning_context', True)
    except ImportError:
        logger.debug("[TaskPlanner] Settings not available, defaulting to enabled")
        return True


def _get_learning_context(goal_summary: str, task_type: Optional[str] = None) -> str:
    """
    Get learning context from past failures for planning.

    This function queries the Observer Node for similar past failures
    and returns formatted context for the planner.

    Args:
        goal_summary: Summary of the current goal
        task_type: Optional task type for filtering

    Returns:
        Formatted learning context string, empty if not available
    """
    if not _get_failure_learning_enabled():
        logger.debug("[TaskPlanner] Failure learning context disabled")
        return ""

    try:
        from orchestrator.observer_node import get_learning_context
        context = get_learning_context(goal_summary, task_type)
        if context:
            logger.info(
                "[TaskPlanner] Retrieved failure learning context (%d chars)",
                len(context)
            )
        return context
    except ImportError as e:
        logger.debug("[TaskPlanner] Observer node not available: %s", e)
        return ""
    except Exception as e:
        logger.warning("[TaskPlanner] Failed to get learning context: %s", e)
        return ""


class SubTaskType(Enum):
    """Types of subtasks"""
    SETUP_ENVIRONMENT = "setup_environment"
    ANALYZE_CODE = "analyze_code"
    WRITE_CODE = "write_code"
    WRITE_TEST = "write_test"
    RUN_TEST = "run_test"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    VERIFICATION = "verification"
    CLEANUP = "cleanup"


class SubTaskStatus(Enum):
    """Status of a subtask"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class SubTask:
    """Represents a single subtask in the execution plan"""
    task_id: str
    task_type: SubTaskType
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: SubTaskStatus = SubTaskStatus.PENDING
    priority: int = 0  # Lower number = higher priority
    estimated_duration_minutes: int = 5
    requires_approval: bool = False
    agent_type: str = "dev_agent"  # Which agent should execute this
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "priority": self.priority,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "requires_approval": self.requires_approval,
            "agent_type": self.agent_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if this task is ready to execute (all dependencies met)"""
        return all(dep in completed_tasks for dep in self.dependencies)


@dataclass
class TaskPlan:
    """Complete execution plan for a goal"""
    plan_id: str
    goal: ParsedGoal
    subtasks: List[SubTask]
    total_estimated_minutes: int
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed
    current_task_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal.to_dict(),
            "subtasks": [t.to_dict() for t in self.subtasks],
            "total_estimated_minutes": self.total_estimated_minutes,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "current_task_index": self.current_task_index,
            "metadata": self.metadata,
        }

    def get_next_task(self) -> Optional[SubTask]:
        """Get the next task to execute"""
        completed_ids = {
            t.task_id for t in self.subtasks
            if t.status == SubTaskStatus.COMPLETED
        }

        for task in self.subtasks:
            if task.status == SubTaskStatus.PENDING and task.is_ready(completed_ids):
                return task
        return None

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress of the plan"""
        total = len(self.subtasks)
        completed = sum(1 for t in self.subtasks if t.status == SubTaskStatus.COMPLETED)
        failed = sum(1 for t in self.subtasks if t.status == SubTaskStatus.FAILED)
        in_progress = sum(1 for t in self.subtasks if t.status == SubTaskStatus.IN_PROGRESS)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }


class TaskPlanner:
    """
    Plans and decomposes goals into executable subtasks.

    This planner uses goal type and objectives to generate a structured
    execution plan with proper task ordering and dependencies.
    """

    # Task templates for different goal types
    TASK_TEMPLATES = {
        GoalType.FEATURE_DEVELOPMENT: [
            (SubTaskType.SETUP_ENVIRONMENT, "Set up development environment", "dev_agent", 5),
            (SubTaskType.ANALYZE_CODE, "Analyze existing codebase and identify integration points", "dev_agent", 10),
            (SubTaskType.WRITE_CODE, "Implement the feature", "dev_agent", 30),
            (SubTaskType.WRITE_TEST, "Write unit tests for the feature", "dev_agent", 15),
            (SubTaskType.RUN_TEST, "Run tests and fix any failures", "dev_agent", 10),
            (SubTaskType.CODE_REVIEW, "Self-review code for quality", "dev_agent", 10),
            (SubTaskType.DOCUMENTATION, "Update documentation", "dev_agent", 10),
            (SubTaskType.VERIFICATION, "Final verification and cleanup", "dev_agent", 5),
        ],
        GoalType.BUG_FIX: [
            (SubTaskType.ANALYZE_CODE, "Reproduce and analyze the bug", "dev_agent", 15),
            (SubTaskType.ANALYZE_CODE, "Identify root cause", "dev_agent", 10),
            (SubTaskType.WRITE_CODE, "Implement the fix", "dev_agent", 20),
            (SubTaskType.WRITE_TEST, "Add regression test", "dev_agent", 10),
            (SubTaskType.RUN_TEST, "Run all tests to verify fix", "dev_agent", 10),
            (SubTaskType.VERIFICATION, "Verify fix doesn't introduce new issues", "dev_agent", 5),
        ],
        GoalType.REFACTORING: [
            (SubTaskType.ANALYZE_CODE, "Analyze code to be refactored", "dev_agent", 15),
            (SubTaskType.RUN_TEST, "Run existing tests as baseline", "dev_agent", 5),
            (SubTaskType.WRITE_CODE, "Perform refactoring", "dev_agent", 30),
            (SubTaskType.RUN_TEST, "Run tests to ensure no regressions", "dev_agent", 10),
            (SubTaskType.CODE_REVIEW, "Review refactored code", "dev_agent", 10),
            (SubTaskType.VERIFICATION, "Final verification", "dev_agent", 5),
        ],
        GoalType.TESTING: [
            (SubTaskType.ANALYZE_CODE, "Analyze code coverage gaps", "dev_agent", 10),
            (SubTaskType.WRITE_TEST, "Write test cases", "dev_agent", 30),
            (SubTaskType.RUN_TEST, "Run tests and verify coverage", "dev_agent", 10),
            (SubTaskType.VERIFICATION, "Review test quality", "dev_agent", 5),
        ],
        GoalType.DOCUMENTATION: [
            (SubTaskType.ANALYZE_CODE, "Analyze code to document", "dev_agent", 10),
            (SubTaskType.DOCUMENTATION, "Write documentation", "dev_agent", 30),
            (SubTaskType.VERIFICATION, "Review documentation for accuracy", "dev_agent", 10),
        ],
        GoalType.DEPLOYMENT: [
            (SubTaskType.RUN_TEST, "Run pre-deployment tests", "ops_agent", 10),
            (SubTaskType.VERIFICATION, "Verify deployment readiness", "ops_agent", 5),
            (SubTaskType.DEPLOYMENT, "Execute deployment", "ops_agent", 15),
            (SubTaskType.VERIFICATION, "Post-deployment verification", "ops_agent", 10),
        ],
        GoalType.OPTIMIZATION: [
            (SubTaskType.ANALYZE_CODE, "Profile and identify bottlenecks", "dev_agent", 15),
            (SubTaskType.WRITE_CODE, "Implement optimizations", "dev_agent", 25),
            (SubTaskType.RUN_TEST, "Benchmark and verify improvements", "dev_agent", 10),
            (SubTaskType.VERIFICATION, "Verify no regressions", "dev_agent", 5),
        ],
        GoalType.INVESTIGATION: [
            (SubTaskType.ANALYZE_CODE, "Gather information and context", "dev_agent", 15),
            (SubTaskType.ANALYZE_CODE, "Analyze findings", "dev_agent", 20),
            (SubTaskType.DOCUMENTATION, "Document findings and recommendations", "dev_agent", 15),
        ],
        GoalType.MAINTENANCE: [
            (SubTaskType.ANALYZE_CODE, "Review current state", "dev_agent", 10),
            (SubTaskType.WRITE_CODE, "Perform maintenance tasks", "dev_agent", 20),
            (SubTaskType.RUN_TEST, "Verify changes", "dev_agent", 10),
            (SubTaskType.CLEANUP, "Clean up and finalize", "dev_agent", 5),
        ],
    }

    def __init__(self, llm_planner: Optional[Any] = None):
        """
        Initialize the TaskPlanner.

        Args:
            llm_planner: Optional LLM planner for advanced decomposition.
                        If not provided, uses template-based planning.
        """
        self.llm_planner = llm_planner
        logger.info("[TaskPlanner] Initialized (LLM: %s)", "enabled" if llm_planner else "disabled")

    def create_plan(self, goal: ParsedGoal, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        Create an execution plan for a parsed goal.

        This method integrates failure learning context from the Observer Node
        (Phase 2 Brain Layer) to help avoid repeating past mistakes.

        Args:
            goal: The parsed goal to plan for
            context: Optional context information

        Returns:
            TaskPlan with ordered subtasks
        """
        plan_id = str(uuid.uuid4())
        context = context or {}

        logger.info(
            "[TaskPlanner] Creating plan for goal %s (type: %s)",
            goal.goal_id[:8], goal.goal_type.value)

        # Get failure learning context from Observer Node (#2072)
        learning_context = _get_learning_context(
            goal_summary=goal.summary,
            task_type=goal.goal_type.value if goal.goal_type else None
        )

        # Add learning context to the planning context
        if learning_context:
            context["failure_learning_context"] = learning_context
            logger.info(
                "[TaskPlanner] Added failure learning context to plan %s",
                plan_id[:8]
            )

        # Get base template for goal type
        template = self.TASK_TEMPLATES.get(goal.goal_type, self.TASK_TEMPLATES[GoalType.FEATURE_DEVELOPMENT])

        # Generate subtasks from template (includes learning context in inputs)
        subtasks = self._generate_subtasks(goal, template, context)

        # Adjust based on complexity
        subtasks = self._adjust_for_complexity(subtasks, goal.estimated_complexity)

        # Set up dependencies
        subtasks = self._setup_dependencies(subtasks)

        # Mark high-risk tasks
        subtasks = self._mark_approval_required(subtasks, goal)

        # Calculate total estimated time
        total_minutes = sum(t.estimated_duration_minutes for t in subtasks)

        plan = TaskPlan(
            plan_id=plan_id,
            goal=goal,
            subtasks=subtasks,
            total_estimated_minutes=total_minutes,
            metadata={
                "context": context,
                "planner_version": "1.1.0",  # Version bump for learning context
                "template_used": goal.goal_type.value,
                "has_learning_context": bool(learning_context),
            },
        )

        logger.info(
            "[TaskPlanner] Created plan %s: %d subtasks, estimated %d minutes, learning_context=%s",
            plan_id[:8], len(subtasks), total_minutes, bool(learning_context)
        )

        return plan

    def _generate_subtasks(
        self,
        goal: ParsedGoal,
        template: List[tuple],
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """
        Generate subtasks from template and goal objectives.

        Includes failure learning context from Observer Node (#2072) in subtask
        inputs to help agents avoid repeating past mistakes.
        """
        subtasks = []

        # Extract failure learning context if available
        learning_context = context.get("failure_learning_context", "")

        for i, (task_type, description, agent_type, duration) in enumerate(template):
            # Customize description based on goal
            customized_desc = self._customize_description(description, goal)

            # Build subtask inputs with learning context
            task_inputs: Dict[str, Any] = {
                "goal_summary": goal.summary,
                "objectives": goal.objectives,
                "constraints": goal.constraints,
                "repo": context.get("repo", "RC918/morningai"),
            }

            # Add learning context to relevant task types (#2072)
            # Include learning context for analysis and code tasks where
            # past failure knowledge is most valuable
            if learning_context and task_type in [
                SubTaskType.ANALYZE_CODE,
                SubTaskType.WRITE_CODE,
                SubTaskType.WRITE_TEST,
                SubTaskType.RUN_TEST,
            ]:
                task_inputs["failure_learning_context"] = learning_context

            task = SubTask(
                task_id=f"{goal.goal_id[:8]}-{i:02d}",
                task_type=task_type,
                description=customized_desc,
                priority=i,
                estimated_duration_minutes=duration,
                agent_type=agent_type,
                inputs=task_inputs,
            )
            subtasks.append(task)

        return subtasks

    def _customize_description(self, base_description: str, goal: ParsedGoal) -> str:
        """Customize task description based on goal context"""
        # Add goal-specific context to description
        if goal.summary and len(goal.summary) < 50:
            return f"{base_description} for: {goal.summary}"
        return base_description

    def _adjust_for_complexity(self, subtasks: List[SubTask], complexity: str) -> List[SubTask]:
        """Adjust task estimates based on complexity"""
        multipliers = {
            "simple": 0.7,
            "moderate": 1.0,
            "complex": 1.5,
        }

        multiplier = multipliers.get(complexity, 1.0)

        for task in subtasks:
            task.estimated_duration_minutes = int(task.estimated_duration_minutes * multiplier)

        return subtasks

    def _setup_dependencies(self, subtasks: List[SubTask]) -> List[SubTask]:
        """Set up task dependencies (sequential by default)"""
        for i, task in enumerate(subtasks):
            if i > 0:
                # Each task depends on the previous one
                task.dependencies = [subtasks[i - 1].task_id]

        return subtasks

    def _mark_approval_required(self, subtasks: List[SubTask], goal: ParsedGoal) -> List[SubTask]:
        """Mark tasks that require human approval"""
        # If goal requires approval, mark deployment and high-risk tasks
        if goal.requires_approval:
            for task in subtasks:
                if task.task_type in [SubTaskType.DEPLOYMENT, SubTaskType.WRITE_CODE]:
                    task.requires_approval = True

        # Always require approval for deployment tasks
        for task in subtasks:
            if task.task_type == SubTaskType.DEPLOYMENT:
                task.requires_approval = True

        return subtasks

    async def create_plan_with_llm(
        self, goal: ParsedGoal, context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """
        Create a plan using LLM for more intelligent decomposition.

        Args:
            goal: The parsed goal to plan for
            context: Optional context information

        Returns:
            TaskPlan with LLM-enhanced subtasks
        """
        if not self.llm_planner:
            logger.warning("[TaskPlanner] LLM planner not available, using template planning")
            return self.create_plan(goal, context)

        # First create base plan
        base_plan = self.create_plan(goal, context)

        try:
            # Enhance with LLM
            enhanced_subtasks = await self._enhance_with_llm(goal, base_plan.subtasks, context)
            base_plan.subtasks = enhanced_subtasks
            base_plan.metadata["llm_enhanced"] = True

            # Recalculate total time
            base_plan.total_estimated_minutes = sum(
                t.estimated_duration_minutes for t in enhanced_subtasks
            )

            return base_plan

        except Exception as e:
            logger.error("[TaskPlanner] LLM planning failed: %s, using base plan", e)
            return base_plan

    async def _enhance_with_llm(
        self,
        goal: ParsedGoal,
        subtasks: List[SubTask],
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """Enhance subtasks using LLM"""
        # For now, return base subtasks - LLM integration to be implemented
        return subtasks

    def replan_from_failure(
        self, plan: TaskPlan, failed_task: SubTask, error: str
    ) -> TaskPlan:
        """
        Create a recovery plan after a task failure.

        Args:
            plan: The original plan
            failed_task: The task that failed
            error: Error message from the failure

        Returns:
            Updated TaskPlan with recovery steps
        """
        logger.info("[TaskPlanner] Replanning after failure of task %s", failed_task.task_id)

        # Mark failed task
        failed_task.status = SubTaskStatus.FAILED
        failed_task.error = error

        # Add recovery task
        recovery_task = SubTask(
            task_id=f"{failed_task.task_id}-recovery",
            task_type=SubTaskType.ANALYZE_CODE,
            description=f"Analyze and recover from failure: {error[:100]}",
            dependencies=[],  # No dependencies - can start immediately
            priority=-1,  # High priority
            estimated_duration_minutes=10,
            agent_type=failed_task.agent_type,
            inputs={
                "failed_task": failed_task.to_dict(),
                "error": error,
            },
        )

        # Insert recovery task
        failed_index = plan.subtasks.index(failed_task)
        plan.subtasks.insert(failed_index + 1, recovery_task)

        # Update dependencies for subsequent tasks
        for task in plan.subtasks[failed_index + 2:]:
            if failed_task.task_id in task.dependencies:
                task.dependencies.remove(failed_task.task_id)
                task.dependencies.append(recovery_task.task_id)

        plan.metadata["replanned"] = True
        plan.metadata["failure_recovery"] = {
            "failed_task_id": failed_task.task_id,
            "error": error,
            "recovery_task_id": recovery_task.task_id,
        }

        return plan
