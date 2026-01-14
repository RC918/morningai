"""
Model Tier Selection + Decision Hooks - F-6 Implementation

EPIC F Phase F-6: Model Tier Selection + Decision Hooks

This module implements rule-based model tier selection and provides hooks
for advanced features like Debate Engine integration and Memory v2.

Blueprint Reference: Section F-6 (Model Tier Selection + Decision Hooks)

Key Features:
- ModelTierSelector: Rule-based model tier selection based on task characteristics
- PlannerHook Protocol: Pluggable hooks for plan modification
- DebateHook: Integration with Debate Engine v2 for high-risk decisions
- MemoryHook: Placeholder for Memory v2 integration
- PlanOracle: Interface for pre-execution simulation (future)

Usage:
    from core.planner.model_tier_selection import (
        ModelTierSelector,
        TierContext,
        DebateHook,
    )

    # Select model tier for a task
    selector = ModelTierSelector()
    tier = selector.select_tier(task, context)

    # Get tier assignments for all tasks in a plan
    tiers = selector.get_plan_tiers(plan)

    # Apply hooks to a plan
    hook = DebateHook(trace_id="abc123")
    modified_plan = hook.on_plan_created(plan)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple

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


def _use_model_tier_selection() -> bool:
    """Lazy evaluation for USE_MODEL_TIER_SELECTION setting."""
    settings = _get_settings()
    return settings.use_model_tier_selection if settings else False


def _use_debate_hook() -> bool:
    """Lazy evaluation for USE_DEBATE_HOOK setting."""
    settings = _get_settings()
    return settings.use_debate_hook if settings else False


@dataclass
class TierContext:
    """
    Context for model tier selection decisions.

    Attributes:
        complexity: Task complexity level (simple, low, medium, high)
        provider_preference: Preferred provider (None for auto-selection)
        cost_sensitive: Whether to prefer lower-cost tiers
        latency_sensitive: Whether to prefer lower-latency tiers
    """
    complexity: str = "medium"
    provider_preference: Optional[str] = None
    cost_sensitive: bool = False
    latency_sensitive: bool = False


@dataclass
class ProviderStatus:
    """
    Status of a provider for resource-aware planning.

    Attributes:
        health_score: Provider health score (0.0 to 1.0)
        rate_limit_remaining: Remaining rate limit
        latency_p99_ms: P99 latency in milliseconds
        recommended_tier: Recommended tier based on current status
    """
    health_score: float = 1.0
    rate_limit_remaining: int = 1000
    latency_p99_ms: float = 100.0
    recommended_tier: Optional[str] = None


@dataclass
class ProviderHealthSnapshot:
    """
    Snapshot of provider health for resource-aware planning.

    Attributes:
        timestamp: Snapshot timestamp (ISO format)
        providers: Dictionary mapping provider name to status
    """
    timestamp: str = ""
    providers: Dict[str, ProviderStatus] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """
    Result of plan simulation (Plan Oracle).

    Attributes:
        estimated_cost_usd: Estimated cost in USD
        estimated_duration_minutes: Estimated duration in minutes
        risk_assessment: Risk assessment string
        requires_approval: Whether approval is required
        warnings: List of warnings
    """
    estimated_cost_usd: float = 0.0
    estimated_duration_minutes: int = 0
    risk_assessment: str = "low"
    requires_approval: bool = False
    warnings: List[str] = field(default_factory=list)


class ModelTierSelector:
    """
    Selects model tier based on task characteristics.

    Blueprint Reference: Section F-6 ModelTierSelector

    This class implements rule-based model tier selection that considers:
    - Task risk level (critical, high, medium, low)
    - Task type (deploy, security_review, code, review, etc.)
    - Task complexity
    - Cost and latency constraints

    Model Tiers:
    - tier_0: Most capable, highest cost (critical tasks, security)
    - tier_1: High capability (high-risk code, review)
    - tier_2: Standard (medium/low risk, analyze, test, document)
    - tier_3: Fast, low cost (cleanup, format, simple tasks)

    Usage:
        selector = ModelTierSelector()
        tier = selector.select_tier(task, context)
    """

    TIER_RULES: Dict[str, Dict[str, Any]] = {
        "tier_0": {
            "risk_levels": [RiskLevel.CRITICAL],
            "task_types": [TaskType.DEPLOY],
            "complexity": "high",
            "description": "Most capable, highest cost",
        },
        "tier_1": {
            "risk_levels": [RiskLevel.HIGH],
            "task_types": [TaskType.CODE, TaskType.REVIEW],
            "complexity": "medium",
            "description": "High capability",
        },
        "tier_2": {
            "risk_levels": [RiskLevel.MEDIUM, RiskLevel.LOW],
            "task_types": [TaskType.ANALYZE, TaskType.TEST, TaskType.DOCUMENT],
            "complexity": "low",
            "description": "Standard",
        },
        "tier_3": {
            "risk_levels": [RiskLevel.LOW],
            "task_types": [TaskType.CLEANUP, TaskType.SETUP, TaskType.VERIFY],
            "complexity": "simple",
            "description": "Fast, low cost",
        },
    }

    DEFAULT_TIER = "tier_2"

    def __init__(self):
        """Initialize the ModelTierSelector."""
        pass

    def select_tier(
        self,
        task: TaskNode,
        context: Optional[TierContext] = None,
    ) -> str:
        """
        Select model tier for a task based on rules.

        Args:
            task: The TaskNode to select tier for
            context: Optional tier context with complexity and preferences

        Returns:
            Model tier string (e.g., 'tier_0', 'tier_1', 'tier_2', 'tier_3')
        """
        context = context or TierContext()

        if task.risk_level == RiskLevel.CRITICAL:
            logger.debug(
                "[ModelTierSelector] Critical risk task %s, using tier_0",
                task.task_id
            )
            return "tier_0"

        if task.risk_level == RiskLevel.HIGH:
            if task.task_type in [TaskType.CODE, TaskType.DEPLOY]:
                logger.debug(
                    "[ModelTierSelector] High risk %s task %s, using tier_0",
                    task.task_type.value, task.task_id
                )
                return "tier_0"
            logger.debug(
                "[ModelTierSelector] High risk task %s, using tier_1",
                task.task_id
            )
            return "tier_1"

        if task.task_type == TaskType.DEPLOY:
            logger.debug(
                "[ModelTierSelector] Deploy task %s, using tier_1",
                task.task_id
            )
            return "tier_1"

        if task.task_type in [TaskType.CODE, TaskType.REVIEW]:
            if context.complexity == "high":
                logger.debug(
                    "[ModelTierSelector] High complexity %s task %s, using tier_1",
                    task.task_type.value, task.task_id
                )
                return "tier_1"
            logger.debug(
                "[ModelTierSelector] Standard %s task %s, using tier_2",
                task.task_type.value, task.task_id
            )
            return "tier_2"

        if task.task_type in [TaskType.CLEANUP, TaskType.SETUP, TaskType.VERIFY]:
            if context.latency_sensitive or context.cost_sensitive:
                logger.debug(
                    "[ModelTierSelector] Cost/latency sensitive %s task %s, using tier_3",
                    task.task_type.value, task.task_id
                )
                return "tier_3"

        logger.debug(
            "[ModelTierSelector] Default tier for task %s: %s",
            task.task_id, self.DEFAULT_TIER
        )
        return self.DEFAULT_TIER

    def get_plan_tiers(
        self,
        plan: PlannerOutput,
        context: Optional[TierContext] = None,
    ) -> Dict[str, str]:
        """
        Get tier assignments for all tasks in a plan.

        Args:
            plan: The PlannerOutput containing tasks
            context: Optional tier context

        Returns:
            Dictionary mapping task_id to tier string
        """
        tiers = {}
        for task in plan.task_tree.nodes:
            tiers[task.task_id] = self.select_tier(task, context)
        return tiers

    def apply_tiers(
        self,
        plan: PlannerOutput,
        context: Optional[TierContext] = None,
    ) -> PlannerOutput:
        """
        Apply tier assignments to a plan (updates model_tier_hints).

        Args:
            plan: The PlannerOutput to update
            context: Optional tier context

        Returns:
            The same PlannerOutput with updated model_tier_hints
        """
        if not _use_model_tier_selection():
            logger.debug(
                "[ModelTierSelector] Model tier selection disabled, skipping"
            )
            return plan

        tiers = self.get_plan_tiers(plan, context)

        default_tier = self._determine_default_tier(tiers)
        per_task_overrides = {
            task_id: tier
            for task_id, tier in tiers.items()
            if tier != default_tier
        }

        plan.model_tier_hints = {
            "default_tier": default_tier,
            "per_task_overrides": per_task_overrides,
        }

        logger.info(
            "[ModelTierSelector] Applied tiers to plan %s: default=%s, overrides=%d",
            plan.plan_id[:8], default_tier, len(per_task_overrides)
        )
        return plan

    def _determine_default_tier(self, tiers: Dict[str, str]) -> str:
        """Determine the most common tier to use as default."""
        if not tiers:
            return self.DEFAULT_TIER

        tier_counts: Dict[str, int] = {}
        for tier in tiers.values():
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return max(tier_counts, key=tier_counts.get)  # type: ignore


class PlannerHook(Protocol):
    """
    Protocol for pluggable planner hooks.

    Blueprint Reference: Section F-6 Decision Hooks Interface

    Hooks can modify plans at various points in the planning lifecycle:
    - on_plan_created: Called after plan creation, can modify plan
    - on_task_assigned: Called after agent assignment, can override

    Usage:
        class MyHook(PlannerHook):
            def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
                # Modify plan
                return plan

            def on_task_assigned(
                self, task: TaskNode, agent: str
            ) -> Tuple[TaskNode, str]:
                # Override assignment
                return task, agent
    """

    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        """Called after plan creation, can modify plan."""
        ...

    def on_task_assigned(
        self, task: TaskNode, agent: str
    ) -> Tuple[TaskNode, str]:
        """Called after agent assignment, can override."""
        ...


class BasePlannerHook(ABC):
    """
    Abstract base class for planner hooks.

    Provides default implementations that pass through unchanged.
    Subclasses can override specific methods as needed.
    """

    @abstractmethod
    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        """Called after plan creation, can modify plan."""
        return plan

    @abstractmethod
    def on_task_assigned(
        self, task: TaskNode, agent: str
    ) -> Tuple[TaskNode, str]:
        """Called after agent assignment, can override."""
        return task, agent


class DebateHook(BasePlannerHook):
    """
    Hook for Debate Engine v2 integration.

    Blueprint Reference: Section F-6 DebateHook

    This hook triggers the Debate Engine for high-risk plans,
    allowing adversarial collaboration to improve decision quality.

    Usage:
        hook = DebateHook(trace_id="abc123")
        modified_plan = hook.on_plan_created(plan)
    """

    def __init__(self, trace_id: str = ""):
        """
        Initialize the DebateHook.

        Args:
            trace_id: Trace ID for telemetry
        """
        self.trace_id = trace_id

    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        """
        Invoke debate for high-risk plans.

        Args:
            plan: The PlannerOutput to potentially debate

        Returns:
            The plan, potentially modified by debate outcome
        """
        if not _use_debate_hook():
            logger.debug(
                "[DebateHook] Debate hook disabled, skipping"
            )
            return plan

        if not self._should_trigger_debate(plan):
            logger.debug(
                "[DebateHook] Plan %s does not require debate",
                plan.plan_id[:8]
            )
            return plan

        logger.info(
            "[DebateHook] Triggering debate for high-risk plan %s",
            plan.plan_id[:8]
        )

        try:
            from .debate_engine import (
                DebateEngine,
                create_debate_topic_from_plan,
                should_trigger_debate,
            )

            if not should_trigger_debate(plan):
                return plan

            topic = create_debate_topic_from_plan(plan)
            engine = DebateEngine(trace_id=self.trace_id)
            result = engine.debate(topic)

            if result.decision.requires_human_review:
                plan.risk_metadata.requires_approval = True
                logger.info(
                    "[DebateHook] Debate result requires human review for plan %s",
                    plan.plan_id[:8]
                )

            return plan

        except ImportError as e:
            logger.warning(
                "[DebateHook] Debate engine not available: %s", e
            )
            return plan
        except Exception as e:
            logger.error(
                "[DebateHook] Debate failed for plan %s: %s",
                plan.plan_id[:8], e
            )
            return plan

    def on_task_assigned(
        self, task: TaskNode, agent: str
    ) -> Tuple[TaskNode, str]:
        """Pass through - DebateHook does not modify task assignments."""
        return task, agent

    def _should_trigger_debate(self, plan: PlannerOutput) -> bool:
        """Determine if debate should be triggered for this plan."""
        if plan.risk_metadata.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True

        high_risk_tasks = [
            task for task in plan.task_tree.nodes
            if task.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        if len(high_risk_tasks) >= 2:
            return True

        return False


class MemoryHook(BasePlannerHook):
    """
    Hook for Memory v2 integration (placeholder).

    Blueprint Reference: Section F-6 MemoryHook

    This hook will enrich plans with historical context from Memory v2
    when EPIC G reaches maturity.

    Currently a stub implementation that passes through unchanged.
    """

    def __init__(self, trace_id: str = ""):
        """
        Initialize the MemoryHook.

        Args:
            trace_id: Trace ID for telemetry
        """
        self.trace_id = trace_id

    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        """
        Enrich plan with historical context (placeholder).

        Args:
            plan: The PlannerOutput to enrich

        Returns:
            The plan (unchanged in stub implementation)
        """
        logger.debug(
            "[MemoryHook] Memory v2 integration not yet implemented, "
            "passing through plan %s",
            plan.plan_id[:8]
        )
        return plan

    def on_task_assigned(
        self, task: TaskNode, agent: str
    ) -> Tuple[TaskNode, str]:
        """Pass through - MemoryHook does not modify task assignments."""
        return task, agent


class PlanOracle(Protocol):
    """
    Protocol for pre-execution simulation (future).

    Blueprint Reference: Section F-6 Plan Oracle Interface

    The Plan Oracle will simulate plan execution and estimate outcomes
    before actual execution, enabling:
    - Cost estimation
    - Duration prediction
    - Risk assessment
    - Approval requirements

    This is a stub interface for future implementation.
    """

    def simulate(self, plan: PlannerOutput) -> SimulationResult:
        """Simulate plan execution and estimate outcomes."""
        ...


class ProviderHealthProvider(Protocol):
    """
    Protocol for provider health data (from EPIC I).

    Blueprint Reference: Section F-6 Resource-Aware Input Interface

    This protocol defines how provider health data is consumed
    for resource-aware planning decisions.

    This is a stub interface for future implementation.
    """

    def get_health_snapshot(self) -> ProviderHealthSnapshot:
        """Get current provider health status."""
        ...


class HookChain:
    """
    Chain of planner hooks to apply in sequence.

    Usage:
        chain = HookChain([DebateHook(), MemoryHook()])
        modified_plan = chain.apply_to_plan(plan)
    """

    def __init__(self, hooks: Optional[List[BasePlannerHook]] = None):
        """
        Initialize the hook chain.

        Args:
            hooks: List of hooks to apply in order
        """
        self.hooks = hooks or []

    def add_hook(self, hook: BasePlannerHook) -> None:
        """Add a hook to the chain."""
        self.hooks.append(hook)

    def apply_to_plan(self, plan: PlannerOutput) -> PlannerOutput:
        """
        Apply all hooks to a plan in sequence.

        Args:
            plan: The PlannerOutput to process

        Returns:
            The processed PlannerOutput
        """
        for hook in self.hooks:
            plan = hook.on_plan_created(plan)
        return plan

    def apply_to_assignment(
        self, task: TaskNode, agent: str
    ) -> Tuple[TaskNode, str]:
        """
        Apply all hooks to a task assignment in sequence.

        Args:
            task: The TaskNode being assigned
            agent: The assigned agent

        Returns:
            Tuple of (potentially modified task, potentially modified agent)
        """
        for hook in self.hooks:
            task, agent = hook.on_task_assigned(task, agent)
        return task, agent


def apply_model_tiers_and_hooks(
    plan: PlannerOutput,
    tier_context: Optional[TierContext] = None,
    hooks: Optional[List[BasePlannerHook]] = None,
    trace_id: str = "",
) -> PlannerOutput:
    """
    Convenience function to apply model tier selection and hooks to a plan.

    Args:
        plan: The PlannerOutput to process
        tier_context: Optional context for tier selection
        hooks: Optional list of hooks to apply
        trace_id: Trace ID for telemetry

    Returns:
        The processed PlannerOutput with tiers and hook modifications applied
    """
    selector = ModelTierSelector()
    plan = selector.apply_tiers(plan, tier_context)

    if hooks is None:
        hooks = [
            DebateHook(trace_id=trace_id),
            MemoryHook(trace_id=trace_id),
        ]

    chain = HookChain(hooks)
    plan = chain.apply_to_plan(plan)

    return plan
