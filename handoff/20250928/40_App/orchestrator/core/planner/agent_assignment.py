"""
Agent Assignment + Flow Template Selection - F-4 Implementation

EPIC F Phase F-4: Agent Assignment + Flow Template Selection

This module implements intelligent agent assignment and flow template selection
based on task characteristics and risk levels.

Blueprint Reference: Section F-4 (Agent Assignment + Flow Template Selection)

Key Features:
- AgentAssigner: Rule-based agent assignment based on task type and risk level
- FlowTemplateSelector: Flow template selection based on plan characteristics
- EPIC E Integration: Risk metadata consumption for assignment decisions

Usage:
    from core.planner.agent_assignment import AgentAssigner, FlowTemplateSelector
    from core.planner.planner_types import TaskNode, PlannerOutput

    # Assign agent to a task
    assigner = AgentAssigner()
    agent = assigner.assign(task, context)

    # Select flow template for a plan
    selector = FlowTemplateSelector()
    template = selector.select(plan, context)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .planner_types import (
    PlannerOutput,
    RiskLevel,
    TaskNode,
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


def _use_agent_assignment() -> bool:
    """Lazy evaluation for USE_AGENT_ASSIGNMENT setting."""
    settings = _get_settings()
    return settings.use_agent_assignment if settings else False


@dataclass
class AssignmentContext:
    """
    Context for agent assignment decisions.

    Attributes:
        trust_score: Trust score from EPIC I (0.0 to 1.0, None if unavailable)
        available_agents: List of available agent types
        is_retry: Whether this is a retry attempt
        previous_agent: Agent that previously attempted this task (if retry)
    """
    trust_score: Optional[float] = None
    available_agents: List[str] = field(default_factory=lambda: [
        "dev_agent", "senior_coder", "reviewer_agent",
        "tester_agent", "ops_agent", "doc_agent"
    ])
    is_retry: bool = False
    previous_agent: Optional[str] = None


@dataclass
class SelectionContext:
    """
    Context for flow template selection decisions.

    Attributes:
        is_hotfix: Whether this is a hotfix/urgent change
        time_constraint_minutes: Maximum time allowed (None if no constraint)
        user_preference: User-specified template preference (None if no preference)
        trust_score: Trust score from EPIC I (0.0 to 1.0, None if unavailable)
    """
    is_hotfix: bool = False
    time_constraint_minutes: Optional[int] = None
    user_preference: Optional[str] = None
    trust_score: Optional[float] = None


class AgentAssigner:
    """
    Assigns agents to tasks based on type and risk level.

    Blueprint Reference: Section F-4 AgentAssigner

    This class implements rule-based agent assignment that considers:
    - Task type (code, review, test, deploy, etc.)
    - Risk level (low, medium, high, critical)
    - Trust score from EPIC I (when available)
    - Retry context (escalate to senior on retry)

    Usage:
        assigner = AgentAssigner()
        agent = assigner.assign(task, context)
    """

    ASSIGNMENT_RULES: Dict[str, str] = {
        "setup": "dev_agent",
        "analyze": "dev_agent",
        "code": "dev_agent",
        "test": "tester_agent",
        "review": "reviewer_agent",
        "document": "doc_agent",
        "deploy": "ops_agent",
        "verify": "dev_agent",
        "cleanup": "dev_agent",
    }

    SENIOR_UPGRADE_RULES: Dict[str, str] = {
        "dev_agent": "senior_coder",
        "tester_agent": "senior_tester",
        "reviewer_agent": "senior_reviewer",
    }

    HIGH_RISK_TASK_TYPES = {TaskType.DEPLOY, TaskType.CODE}

    def __init__(self):
        """Initialize the AgentAssigner."""
        pass

    def assign(
        self,
        task: TaskNode,
        context: Optional[AssignmentContext] = None,
    ) -> str:
        """
        Assign an agent to a task based on rules.

        Args:
            task: The TaskNode to assign an agent to
            context: Optional assignment context with trust score and availability

        Returns:
            Agent type string (e.g., 'dev_agent', 'senior_coder')
        """
        context = context or AssignmentContext()

        base_agent = self.ASSIGNMENT_RULES.get(
            task.task_type.value, "dev_agent"
        )

        should_upgrade = self._should_upgrade_to_senior(task, context)

        if should_upgrade:
            upgraded_agent = self.SENIOR_UPGRADE_RULES.get(base_agent, base_agent)
            if upgraded_agent in context.available_agents:
                logger.debug(
                    "[AgentAssigner] Upgrading %s to %s for task %s (risk: %s)",
                    base_agent, upgraded_agent, task.task_id, task.risk_level.value
                )
                return upgraded_agent

        if base_agent not in context.available_agents:
            logger.warning(
                "[AgentAssigner] Agent %s not available, falling back to dev_agent",
                base_agent
            )
            return "dev_agent"

        logger.debug(
            "[AgentAssigner] Assigned %s to task %s",
            base_agent, task.task_id
        )
        return base_agent

    def _should_upgrade_to_senior(
        self,
        task: TaskNode,
        context: AssignmentContext,
    ) -> bool:
        """
        Determine if task should be upgraded to senior agent.

        Upgrade conditions:
        - High risk + high-risk task type (code, deploy)
        - Critical risk for any task type
        - Low trust score (< 0.5) from EPIC I
        - Retry attempt with same agent
        """
        if task.risk_level == RiskLevel.CRITICAL:
            return True

        if task.risk_level == RiskLevel.HIGH:
            if task.task_type in self.HIGH_RISK_TASK_TYPES:
                return True

        if context.trust_score is not None and context.trust_score < 0.5:
            return True

        if context.is_retry and context.previous_agent:
            base_agent = self.ASSIGNMENT_RULES.get(
                task.task_type.value, "dev_agent"
            )
            if context.previous_agent == base_agent:
                return True

        return False

    def assign_all(
        self,
        plan: PlannerOutput,
        context: Optional[AssignmentContext] = None,
    ) -> Dict[str, str]:
        """
        Assign agents to all tasks in a plan.

        Args:
            plan: The PlannerOutput containing tasks
            context: Optional assignment context

        Returns:
            Dictionary mapping task_id to agent type
        """
        assignments = {}
        for task in plan.task_tree.nodes:
            assignments[task.task_id] = self.assign(task, context)
        return assignments

    def apply_assignments(
        self,
        plan: PlannerOutput,
        context: Optional[AssignmentContext] = None,
    ) -> PlannerOutput:
        """
        Apply agent assignments to all tasks in a plan (mutates task nodes).

        Args:
            plan: The PlannerOutput to update
            context: Optional assignment context

        Returns:
            The same PlannerOutput with updated agent_assignment fields
        """
        if not _use_agent_assignment():
            logger.debug(
                "[AgentAssigner] Agent assignment disabled, skipping"
            )
            return plan

        for task in plan.task_tree.nodes:
            task.agent_assignment = self.assign(task, context)

        logger.info(
            "[AgentAssigner] Applied assignments to %d tasks in plan %s",
            len(plan.task_tree.nodes), plan.plan_id[:8]
        )
        return plan


class FlowTemplateSelector:
    """
    Selects appropriate flow template based on plan characteristics.

    Blueprint Reference: Section F-4 FlowTemplateSelector

    This class implements rule-based flow template selection that considers:
    - Task types present in the plan
    - Overall risk level
    - Time constraints
    - User preferences
    - Trust score from EPIC I

    Available templates:
    - full_pipeline: Complete flow with all stages
    - review_heavy: Extra review iterations for risky changes
    - test_heavy: Extra test iterations for complex changes
    - doc_only: Documentation-only changes
    - analysis_only: Analysis without code changes
    - code_only: Quick code changes without full review

    Usage:
        selector = FlowTemplateSelector()
        template = selector.select(plan, context)
    """

    TEMPLATES = {
        "full_pipeline": {
            "stages": ["setup", "analyze", "code", "test", "review", "document", "deploy", "verify"],
            "require_review": True,
            "require_tests": True,
        },
        "review_heavy": {
            "stages": ["setup", "analyze", "code", "review", "test", "verify"],
            "require_review": True,
            "require_tests": True,
        },
        "test_heavy": {
            "stages": ["setup", "analyze", "code", "test", "review", "verify"],
            "require_review": True,
            "require_tests": True,
        },
        "doc_only": {
            "stages": ["analyze", "document", "review"],
            "require_review": True,
            "require_tests": False,
        },
        "analysis_only": {
            "stages": ["analyze", "document"],
            "require_review": False,
            "require_tests": False,
        },
        "code_only": {
            "stages": ["setup", "code", "verify"],
            "require_review": False,
            "require_tests": False,
        },
    }

    def __init__(self):
        """Initialize the FlowTemplateSelector."""
        pass

    def select(
        self,
        plan: PlannerOutput,
        context: Optional[SelectionContext] = None,
    ) -> str:
        """
        Select appropriate flow template for a plan.

        Args:
            plan: The PlannerOutput to select template for
            context: Optional selection context

        Returns:
            Flow template name string
        """
        context = context or SelectionContext()

        if context.user_preference and context.user_preference in self.TEMPLATES:
            logger.debug(
                "[FlowTemplateSelector] Using user preference: %s",
                context.user_preference
            )
            return context.user_preference

        if context.is_hotfix:
            logger.debug(
                "[FlowTemplateSelector] Hotfix mode, using code_only"
            )
            return "code_only"

        if plan.risk_metadata.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.debug(
                "[FlowTemplateSelector] High/critical risk, using review_heavy"
            )
            return "review_heavy"

        if context.trust_score is not None and context.trust_score < 0.5:
            logger.debug(
                "[FlowTemplateSelector] Low trust score (%.2f), using review_heavy",
                context.trust_score
            )
            return "review_heavy"

        if context.time_constraint_minutes is not None:
            if context.time_constraint_minutes < 30:
                logger.debug(
                    "[FlowTemplateSelector] Tight time constraint (%d min), using code_only",
                    context.time_constraint_minutes
                )
                return "code_only"

        template = self._infer_from_task_types(plan)
        logger.debug(
            "[FlowTemplateSelector] Inferred template: %s for plan %s",
            template, plan.plan_id[:8]
        )
        return template

    def _infer_from_task_types(self, plan: PlannerOutput) -> str:
        """
        Infer template from task types present in the plan.

        Args:
            plan: The PlannerOutput to analyze

        Returns:
            Inferred flow template name
        """
        task_types = {task.task_type for task in plan.task_tree.nodes}

        if task_types == {TaskType.DOCUMENT}:
            return "doc_only"

        if task_types == {TaskType.ANALYZE}:
            return "analysis_only"

        if TaskType.DOCUMENT not in task_types and TaskType.ANALYZE in task_types:
            if TaskType.CODE not in task_types:
                return "analysis_only"

        has_code = TaskType.CODE in task_types
        has_test = TaskType.TEST in task_types
        has_review = TaskType.REVIEW in task_types

        if has_code and not has_test and not has_review:
            return "code_only"

        if has_test and not has_review:
            return "test_heavy"

        return "full_pipeline"

    def apply_template(
        self,
        plan: PlannerOutput,
        context: Optional[SelectionContext] = None,
    ) -> PlannerOutput:
        """
        Apply selected flow template to a plan (mutates flow_template field).

        Args:
            plan: The PlannerOutput to update
            context: Optional selection context

        Returns:
            The same PlannerOutput with updated flow_template field
        """
        if not _use_agent_assignment():
            logger.debug(
                "[FlowTemplateSelector] Agent assignment disabled, skipping"
            )
            return plan

        plan.flow_template = self.select(plan, context)

        logger.info(
            "[FlowTemplateSelector] Applied template %s to plan %s",
            plan.flow_template, plan.plan_id[:8]
        )
        return plan


def assign_and_select(
    plan: PlannerOutput,
    assignment_context: Optional[AssignmentContext] = None,
    selection_context: Optional[SelectionContext] = None,
) -> PlannerOutput:
    """
    Convenience function to apply both agent assignment and flow template selection.

    Args:
        plan: The PlannerOutput to process
        assignment_context: Optional context for agent assignment
        selection_context: Optional context for flow template selection

    Returns:
        The processed PlannerOutput with assignments and template applied
    """
    assigner = AgentAssigner()
    selector = FlowTemplateSelector()

    plan = assigner.apply_assignments(plan, assignment_context)
    plan = selector.apply_template(plan, selection_context)

    return plan
