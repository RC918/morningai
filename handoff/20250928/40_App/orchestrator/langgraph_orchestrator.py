"""
LangGraph-based Orchestrator for MorningAI

Phase 3: Multi-Agent Coordination

Implements a stateful agent workflow using LangGraph for:
- Planning and task decomposition (Planner Agent)
- Code generation execution (Dev Codegen Agent)
- Code review and analysis (Reviewer Agent)
- Merge decision logic (Decision Agent)
- CI monitoring and auto-fixing (Fixer Agent)
- State management and persistence

Multi-Agent Flow:
  planner → executor → reviewer → decision → (fixer if needed) → finalizer
"""

import functools
import logging
import time
from typing import TypedDict, Annotated, Sequence, Optional, Callable
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from orchestrator_metrics import get_orchestrator_metrics, OrchestratorMetrics
from failure_recorder import init_failure_recorder_from_env, FailureRecorder
from agent_eval_integration import (
    init_agent_eval_from_env,
    AgentEvalIntegration
)
from common.config.settings import settings
from llm_reviewer_adapter import generate_llm_review

logger = logging.getLogger(__name__)

# Global metrics instance (lazy initialization)
_metrics: Optional[OrchestratorMetrics] = None
_failure_recorder: Optional[FailureRecorder] = None
_agent_eval: Optional[AgentEvalIntegration] = None


def _get_metrics() -> OrchestratorMetrics:
    """Get or initialize the global metrics instance"""
    global _metrics
    if _metrics is None:
        try:
            import os
            import redis
            redis_url = os.environ.get("REDIS_URL")
            if redis_url:
                redis_client = redis.from_url(redis_url)
                _metrics = get_orchestrator_metrics(redis_client=redis_client, enabled=True)
            else:
                _metrics = get_orchestrator_metrics(redis_client=None, enabled=False)
        except Exception as e:
            logger.warning(f"Failed to initialize metrics: {e}")
            _metrics = get_orchestrator_metrics(redis_client=None, enabled=False)
    return _metrics


def _get_failure_recorder() -> FailureRecorder:
    """Get or initialize the global failure recorder instance"""
    global _failure_recorder
    if _failure_recorder is None:
        _failure_recorder = init_failure_recorder_from_env()
    return _failure_recorder


def _get_agent_eval() -> AgentEvalIntegration:
    """Get or initialize the global agent eval integration instance"""
    global _agent_eval
    if _agent_eval is None:
        _agent_eval = init_agent_eval_from_env()
    return _agent_eval


def node_metrics(node_name: str) -> Callable:
    """
    Decorator to extract common node boilerplate for metrics recording.

    Phase 3 Follow-up (#1858): Reduces duplication in advisor nodes by
    automatically handling:
    - start_time tracking
    - metrics.record_node_start()
    - latency_ms calculation
    - metrics.record_node_complete()

    Usage:
        @node_metrics("pm_advisor")
        def pm_advisor_node(state: AgentState) -> AgentState:
            # Node logic here - set success[0] = True on success
            return state

    The decorated function receives an additional 'success' parameter
    (a mutable list [False]) that should be set to [True] on success.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state: "AgentState") -> "AgentState":
            start_time = time.time()
            metrics = _get_metrics()
            trace_id = state.get("trace_id", "unknown")

            metrics.record_node_start(node_name, trace_id)

            success = [False]
            try:
                result = func(state, success)
            finally:
                latency_ms = (time.time() - start_time) * 1000
                metrics.record_node_complete(
                    node_name, trace_id, success=success[0], latency_ms=latency_ms
                )

            return result
        return wrapper
    return decorator


def get_checkpointer():
    """
    Factory function to create the appropriate checkpointer based on configuration.

    Returns:
        - RedisSaver if USE_REDIS_CHECKPOINTER=true and REDIS_URL is configured
        - MemorySaver as fallback (default)

    Configuration:
        - USE_REDIS_CHECKPOINTER: Enable Redis-based checkpointer (default: false)
        - REDIS_CHECKPOINTER_TTL: TTL in seconds for checkpoint entries (default: 86400)
        - REDIS_URL: Redis connection URL (required for Redis checkpointer)
    """
    import os

    use_redis = settings.use_redis_checkpointer
    redis_url = settings.redis_url or os.environ.get("REDIS_URL")

    if use_redis and redis_url:
        try:
            from langgraph.checkpoint.redis import RedisSaver

            ttl_seconds = settings.redis_checkpointer_ttl

            # Build TTL configuration dict for RedisSaver
            # RedisSaver expects TTL in minutes, so convert from seconds
            ttl_config = None
            if ttl_seconds and ttl_seconds > 0:
                ttl_minutes = ttl_seconds / 60
                ttl_config = {
                    "default_ttl": ttl_minutes,
                    "refresh_on_read": True
                }

            # Create RedisSaver with TTL configuration
            checkpointer = RedisSaver(redis_url=redis_url, ttl=ttl_config)
            checkpointer.setup()

            logger.info(
                "Using Redis checkpointer for LangGraph state persistence",
                extra={
                    "operation": "get_checkpointer",
                    "checkpointer_type": "redis",
                    "ttl_seconds": ttl_seconds,
                    "ttl_minutes": ttl_config.get("default_ttl") if ttl_config else None,
                    "redis_url_masked": redis_url[:20] + "..." if len(redis_url) > 20 else redis_url
                }
            )

            return checkpointer

        except ImportError as e:
            logger.warning(
                f"langgraph-checkpoint-redis not installed, falling back to MemorySaver: {e}",
                extra={
                    "operation": "get_checkpointer",
                    "error": str(e)
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize Redis checkpointer, falling back to MemorySaver: {e}",
                extra={
                    "operation": "get_checkpointer",
                    "error": str(e)
                }
            )

    # Fallback to in-memory checkpointer
    logger.info(
        "Using in-memory MemorySaver for LangGraph state persistence",
        extra={
            "operation": "get_checkpointer",
            "checkpointer_type": "memory",
            "use_redis_configured": use_redis,
            "redis_url_available": bool(redis_url)
        }
    )

    return MemorySaver()


# Maximum number of fix retries before giving up
MAX_FIXER_RETRIES = 3

# Token estimation multipliers for cost analysis
GOAL_TOKEN_MULTIPLIER = 2
PLAN_STEP_TOKEN_MULTIPLIER = 100


def _planner_success(
    state: "AgentState",
    metrics: OrchestratorMetrics,
    start_time: float,
    trace_id: str
) -> "AgentState":
    """Helper to record planner success metrics and transition"""
    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("planner", trace_id, success=True, latency_ms=latency_ms)
    metrics.record_transition("planner", "security_advisor", trace_id)
    return state


class AgentState(TypedDict):
    """
    State of the agent workflow

    Phase 3 Multi-Agent State Fields:
        messages: Conversation history
        goal: Original user goal/question
        trace_id: Unique identifier for this task
        repo: GitHub repository (owner/repo format)
        branch: Git branch name
        plan: List of planned steps
        current_step: Current step being executed
        pr_url: Pull request URL
        pr_number: Pull request number
        ci_state: CI check state (pending, success, failure)
        ci_checks: CI check details
        error: Error message if any
        retry_count: Number of retries attempted
        final_result: Final result of the workflow

    Phase 3 New Fields:
        review_result: Result from ReviewerAgent analysis
        review_comments: List of review comments/issues found
        review_severity: Highest severity level (critical, high, medium, low)
        merge_decision: Decision from decision node (approve, request_changes, needs_fix)
        code_quality_score: Code quality score from reviewer (0-100)

    Phase 4 New Fields (PR-2 SecurityAgent):
        security_advisory: SecurityAdvisory result from SecurityAgent
        security_risk: Overall security risk level (critical, high, medium, low, info)
        security_findings: List of security findings
        security_is_safe: Boolean indicating if task is safe to proceed

    Phase 4 New Fields (PR-3 GovernanceAgent):
        governance_advisory: GovernanceAdvisory result from GovernanceAgent
        governance_risk: Overall governance risk level (critical, high, medium, low, info)
        governance_findings: List of governance findings
        governance_is_compliant: Boolean indicating if task is compliant with policies

    Phase 4 New Fields (PR-4 5-Agent Advisory Pipeline):
        cost_advisory: Cost budget analysis result
        cost_risk: Cost risk level (critical, high, medium, low, info)
        cost_within_budget: Boolean indicating if task is within budget
        permission_advisory: Permission analysis result
        permission_risk: Permission risk level (critical, high, medium, low, info)
        permission_granted: Boolean indicating if all permissions are granted
        reputation_advisory: Reputation analysis result
        reputation_score: Agent reputation score (0-100)
        reputation_level: Reputation level (trusted, standard, restricted, new)

    Policy Enforcement Fields (PR-2 Policy Enforcement):
        policy_blocked: Boolean indicating if task was blocked by policy enforcement
        policy_block_reason: Human-readable reason for blocking (empty if not blocked)

    Phase 2 New Fields (PR-1813 Agent Evaluation):
        evaluation_result: Result from evaluation node (capability regression detection)
        evaluation_health_status: Health status (healthy, degraded, critical)
        evaluation_has_regression: Boolean indicating if capability regression detected

    Phase 3 New Fields (PR-3 PM Agent + Ops Agent #1815):
        pm_advisory: PMAdvisory result from PMAgent goal decomposition
        pm_sub_tasks: List of decomposed sub-tasks
        pm_confidence_score: Confidence score for the plan (0.0 to 1.0)
        pm_risk: PM planning risk level (high, medium, low, info)
        ops_advisory: OpsAdvisory result from OpsAgent health check
        ops_health_status: System health status (healthy, degraded, unhealthy, unknown)
        ops_risk: Operations risk level (critical, high, medium, low, info)
        ops_recommended_actions: List of recommended operational actions
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    goal: str
    trace_id: str
    repo: str
    branch: str
    plan: list[str]
    current_step: int
    pr_url: str
    pr_number: int
    ci_state: str
    ci_checks: dict
    error: str
    retry_count: int
    final_result: dict
    review_result: dict
    review_comments: list
    review_severity: str
    merge_decision: str
    code_quality_score: int
    security_advisory: dict
    security_risk: str
    security_findings: list
    security_is_safe: bool
    governance_advisory: dict
    governance_risk: str
    governance_findings: list
    governance_is_compliant: bool
    cost_advisory: dict
    cost_risk: str
    cost_within_budget: bool
    permission_advisory: dict
    permission_risk: str
    permission_granted: bool
    reputation_advisory: dict
    reputation_score: int
    reputation_level: str
    policy_blocked: bool
    policy_block_reason: str
    evaluation_result: dict
    evaluation_health_status: str
    evaluation_has_regression: bool
    # Phase 3 PR-3 PM Agent + Ops Agent (#1815)
    pm_advisory: dict
    pm_sub_tasks: list
    pm_confidence_score: float
    pm_risk: str
    ops_advisory: dict
    ops_health_status: str
    ops_risk: str
    ops_recommended_actions: list


def _get_learning_context_for_planner(goal: str, task_type: Optional[str] = None) -> str:
    """
    Phase 2 PR-1811: Query past failures for learning context

    This function queries pgvector for similar past failures and formats
    them as context for the Planner.

    Args:
        goal: The current task goal
        task_type: Optional task type for filtering

    Returns:
        Formatted context string, empty if no relevant past failures or if disabled
    """
    try:
        from common.config.settings import settings

        if not settings.enable_failure_learning_context:
            logger.debug("[Planner] Failure learning context disabled via feature flag")
            return ""

        from observer_node import get_learning_context

        context = get_learning_context(goal, task_type=task_type, limit=3)

        if context:
            logger.debug("[Planner] Found learning context from past failures", extra={
                "operation": "get_learning_context",
                "context_length": len(context)
            })

        return context

    except ImportError:
        logger.debug("[Planner] observer_node module not available for learning context")
        return ""
    except Exception as e:
        logger.debug(f"[Planner] Failed to get learning context: {e}")
        return ""


def planner_node(state: AgentState) -> AgentState:
    """
    Planning node: Analyzes the goal and creates a plan

    Phase 1: Integrates LLM-powered dynamic planning when USE_LLM_PLANNER=true
    Phase 2 PR-1811: Queries past failures for learning context before planning
    """
    from common.config.settings import settings

    start_time = time.time()
    metrics = _get_metrics()

    goal = state["goal"]
    repo = state.get("repo", "RC918/morningai")
    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("planner", trace_id)

    # Phase 2 PR-1811: Query past failures for learning context
    learning_context = _get_learning_context_for_planner(goal)
    if learning_context:
        state["learning_context"] = learning_context
        logger.info("[Planner] Using learning context from past failures", extra={
            "operation": "planner",
            "trace_id": trace_id,
            "has_learning_context": True
        })

    logger.info("[Planner] Analyzing goal", extra={
        "operation": "planner",
        "trace_id": trace_id,
        "goal": goal[:50],
        "use_llm_planner": settings.use_llm_planner,
        "has_learning_context": bool(learning_context)
    })

    if settings.use_llm_planner:
        try:
            from llm_planner_adapter import generate_llm_plan

            logger.info("[Planner] Using LLM planner", extra={
                "operation": "planner",
                "trace_id": trace_id
            })

            plan_data = generate_llm_plan(goal, repo, trace_id)

            state["plan"] = plan_data["plan"]
            state["planner_type"] = plan_data["planner_type"]
            state["task_type"] = plan_data.get("task_type")
            state["planning_time_ms"] = plan_data.get("planning_time_ms", 0)
            state["current_step"] = 0
            state["messages"] = state.get("messages", []) + [
                SystemMessage(content=f"Planned {len(plan_data['plan'])} steps using {plan_data['planner_type']} planner for goal: {goal}")
            ]

            logger.info(f"[Planner] Created plan with {len(plan_data['plan'])} steps using {plan_data['planner_type']} planner", extra={
                "operation": "planner",
                "trace_id": trace_id,
                "steps": plan_data["plan"],
                "planner_type": plan_data["planner_type"],
                "planning_time_ms": plan_data.get("planning_time_ms", 0)
            })

            return _planner_success(state, metrics, start_time, trace_id)

        except Exception as e:
            logger.error(f"[Planner] LLM planner failed, falling back to static: {e}", extra={
                "operation": "planner",
                "trace_id": trace_id,
                "error": str(e)
            })
            metrics.record_node_complete("planner", trace_id, success=False)

    plan = [
        "Analyze codebase and requirements",
        "Generate FAQ content with GPT-4",
        "Create git branch",
        "Commit changes to FAQ.md",
        "Open pull request",
        "Monitor CI checks",
        "Auto-merge if CI passes"
    ]

    state["plan"] = plan
    state["planner_type"] = "static"
    state["current_step"] = 0
    state["messages"] = state.get("messages", []) + [
        SystemMessage(content=f"Planned {len(plan)} steps for goal: {goal}")
    ]

    logger.info(f"[Planner] Created plan with {len(plan)} steps", extra={
        "operation": "planner",
        "trace_id": trace_id,
        "steps": plan,
        "planner_type": "static"
    })

    return _planner_success(state, metrics, start_time, trace_id)


def security_advisor_node(state: AgentState) -> AgentState:
    """
    Security Advisor node: Analyzes task for security concerns

    Phase 4 PR-2 Enhancement:
    - Provides security advisory for planned tasks
    - Analyzes file paths, code patterns, and task types
    - Integrates with PolicyGuard and ViolationDetector
    - Advisory role: provides recommendations but does not block execution

    Returns:
        Updated state with security_advisory, security_risk, security_findings, security_is_safe
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    goal = state.get("goal", "")
    repo = state.get("repo", "")
    plan = state.get("plan", [])
    task_type = state.get("task_type", "unknown")

    metrics.record_node_start("security_advisor", trace_id)

    logger.info("[SecurityAdvisor] Starting security analysis", extra={
        "operation": "security_advisor",
        "trace_id": trace_id,
        "repo": repo,
        "task_type": task_type,
        "plan_steps": len(plan)
    })

    state["security_advisory"] = {}
    state["security_risk"] = "info"
    state["security_findings"] = []
    state["security_is_safe"] = True

    success = True
    try:
        from security_agent import get_security_agent

        agent = get_security_agent()

        advisory = agent.analyze_task(
            task_type=task_type,
            repo=repo,
            code_changes=goal
        )

        # Use advisory.to_dict() to populate state fields (preserves all finding details)
        advisory_dict = advisory.to_dict()
        state["security_advisory"] = advisory_dict
        state["security_risk"] = advisory_dict["overall_risk"]
        state["security_findings"] = advisory_dict["findings"]
        state["security_is_safe"] = advisory_dict["is_safe"]

        logger.info("[SecurityAdvisor] Analysis complete", extra={
            "operation": "security_advisor",
            "trace_id": trace_id,
            "is_safe": advisory.is_safe,
            "risk_level": advisory.overall_risk.value,
            "findings_count": len(advisory.findings)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Security analysis: risk={advisory.overall_risk.value}, findings={len(advisory.findings)}, safe={advisory.is_safe}")
        ]

    except ImportError as e:
        logger.warning(f"[SecurityAdvisor] SecurityAgent not available: {e}", extra={
            "operation": "security_advisor",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Security analysis skipped (SecurityAgent not available)")
        ]

    except Exception as e:
        success = False
        logger.error(f"[SecurityAdvisor] Analysis failed: {e}", extra={
            "operation": "security_advisor",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)
        state["security_advisory"] = {"error": str(e)}
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Security analysis failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("security_advisor", trace_id, success=success, latency_ms=latency_ms)

    agent_eval = _get_agent_eval()
    agent_eval.record_node_latency(trace_id, "security_advisor", latency_ms)
    agent_eval.record_security_advisory(
        trace_id,
        state.get("security_risk", "info"),
        len(state.get("security_findings", []))
    )

    if success:
        metrics.record_transition("security_advisor", "governance_advisor", trace_id)
    return state


def governance_advisor_node(state: AgentState) -> AgentState:
    """
    Governance Advisor node: Analyzes task for governance compliance

    Phase 4 PR-3 Enhancement:
    - Provides governance advisory for planned tasks
    - Integrates with PolicyGuard, ViolationDetector, CostTracker, PermissionChecker
    - Analyzes policy compliance, cost budget, and permissions
    - Advisory role: provides recommendations but does not block execution

    Returns:
        Updated state with governance_advisory, governance_risk, governance_findings, governance_is_compliant
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    goal = state.get("goal", "")
    repo = state.get("repo", "")
    plan = state.get("plan", [])
    task_type = state.get("task_type", "unknown")

    metrics.record_node_start("governance_advisor", trace_id)

    logger.info("[GovernanceAdvisor] Starting governance analysis", extra={
        "operation": "governance_advisor",
        "trace_id": trace_id,
        "repo": repo,
        "task_type": task_type,
        "plan_steps": len(plan)
    })

    state["governance_advisory"] = {}
    state["governance_risk"] = "info"
    state["governance_findings"] = []
    state["governance_is_compliant"] = True

    success = True
    try:
        from governance_agent import get_governance_agent

        agent = get_governance_agent()

        advisory = agent.analyze_task(
            task_type=task_type,
            trace_id=trace_id,
            agent_id="orchestrator",
            file_paths=[],
            operations=plan,
            content=goal,
            labels=[],
            environment="sandbox"
        )

        advisory_dict = advisory.to_dict()
        state["governance_advisory"] = advisory_dict
        state["governance_risk"] = advisory_dict["overall_risk"]
        state["governance_findings"] = advisory_dict["findings"]
        state["governance_is_compliant"] = advisory_dict["is_compliant"]

        logger.info("[GovernanceAdvisor] Analysis complete", extra={
            "operation": "governance_advisor",
            "trace_id": trace_id,
            "is_compliant": advisory.is_compliant,
            "risk_level": advisory.overall_risk.value,
            "findings_count": len(advisory.findings)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Governance analysis: risk={advisory.overall_risk.value}, findings={len(advisory.findings)}, compliant={advisory.is_compliant}")
        ]

    except ImportError as e:
        logger.warning(f"[GovernanceAdvisor] GovernanceAgent not available: {e}", extra={
            "operation": "governance_advisor",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Governance analysis skipped (GovernanceAgent not available)")
        ]

    except Exception as e:
        success = False
        logger.error(f"[GovernanceAdvisor] Analysis failed: {e}", extra={
            "operation": "governance_advisor",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)
        state["governance_advisory"] = {"error": str(e)}
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Governance analysis failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("governance_advisor", trace_id, success=success, latency_ms=latency_ms)

    agent_eval = _get_agent_eval()
    agent_eval.record_node_latency(trace_id, "governance_advisor", latency_ms)
    agent_eval.record_governance_advisory(
        trace_id,
        state.get("governance_risk", "info"),
        len(state.get("governance_findings", []))
    )

    if success:
        metrics.record_transition("governance_advisor", "cost_advisor", trace_id)
    return state


def cost_advisor_node(state: AgentState) -> AgentState:
    """
    Cost Advisor node: Analyzes task for cost budget compliance

    Phase 4 PR-4 Enhancement (5-Agent Advisory Pipeline):
    - Provides cost budget advisory for planned tasks
    - Integrates with CostTracker via GovernanceAgent
    - Analyzes estimated token usage and budget status
    - Advisory role: provides recommendations but does not block execution

    Returns:
        Updated state with cost_advisory, cost_risk, cost_within_budget
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    goal = state.get("goal", "")
    plan = state.get("plan", [])
    task_type = state.get("task_type", "unknown")

    metrics.record_node_start("cost_advisor", trace_id)

    logger.info("[CostAdvisor] Starting cost analysis", extra={
        "operation": "cost_advisor",
        "trace_id": trace_id,
        "task_type": task_type,
        "plan_steps": len(plan)
    })

    state["cost_advisory"] = {}
    state["cost_risk"] = "info"
    state["cost_within_budget"] = True

    success = True
    try:
        from governance_agent import get_governance_agent

        agent = get_governance_agent()

        estimated_tokens = len(goal) * GOAL_TOKEN_MULTIPLIER + len(plan) * PLAN_STEP_TOKEN_MULTIPLIER

        advisory = agent.analyze_cost_budget(
            trace_id=trace_id,
            estimated_tokens=estimated_tokens,
            model="gpt-4"
        )

        advisory_dict = advisory.to_dict()
        state["cost_advisory"] = advisory_dict
        state["cost_risk"] = advisory_dict["overall_risk"]
        state["cost_within_budget"] = advisory_dict["is_compliant"]

        logger.info("[CostAdvisor] Analysis complete", extra={
            "operation": "cost_advisor",
            "trace_id": trace_id,
            "within_budget": advisory.is_compliant,
            "risk_level": advisory.overall_risk.value,
            "findings_count": len(advisory.findings)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Cost analysis: risk={advisory.overall_risk.value}, within_budget={advisory.is_compliant}")
        ]

    except ImportError as e:
        logger.warning(f"[CostAdvisor] GovernanceAgent not available: {e}", extra={
            "operation": "cost_advisor",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Cost analysis skipped (GovernanceAgent not available)")
        ]

    except Exception as e:
        success = False
        logger.error(f"[CostAdvisor] Analysis failed: {e}", extra={
            "operation": "cost_advisor",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)
        state["cost_advisory"] = {"error": str(e)}
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Cost analysis failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("cost_advisor", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("cost_advisor", "permission_advisor", trace_id)
    return state


def permission_advisor_node(state: AgentState) -> AgentState:
    """
    Permission Advisor node: Analyzes task for permission compliance

    Phase 4 PR-4 Enhancement (5-Agent Advisory Pipeline):
    - Provides permission advisory for planned tasks
    - Integrates with PermissionChecker via GovernanceAgent
    - Analyzes agent permissions for operations and environment access
    - Advisory role: provides recommendations but does not block execution

    Returns:
        Updated state with permission_advisory, permission_risk, permission_granted
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    plan = state.get("plan", [])
    task_type = state.get("task_type", "unknown")

    metrics.record_node_start("permission_advisor", trace_id)

    logger.info("[PermissionAdvisor] Starting permission analysis", extra={
        "operation": "permission_advisor",
        "trace_id": trace_id,
        "task_type": task_type,
        "plan_steps": len(plan)
    })

    state["permission_advisory"] = {}
    state["permission_risk"] = "info"
    state["permission_granted"] = True

    success = True
    try:
        from governance_agent import get_governance_agent

        agent = get_governance_agent()

        advisory = agent.analyze_permissions(
            agent_id=state.get("agent_id", "orchestrator"),
            operations=plan,
            environment=state.get("environment", "sandbox")
        )

        advisory_dict = advisory.to_dict()
        state["permission_advisory"] = advisory_dict
        state["permission_risk"] = advisory_dict["overall_risk"]
        state["permission_granted"] = advisory_dict["is_compliant"]

        logger.info("[PermissionAdvisor] Analysis complete", extra={
            "operation": "permission_advisor",
            "trace_id": trace_id,
            "permission_granted": advisory.is_compliant,
            "risk_level": advisory.overall_risk.value,
            "findings_count": len(advisory.findings)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Permission analysis: risk={advisory.overall_risk.value}, granted={advisory.is_compliant}")
        ]

    except ImportError as e:
        logger.warning(f"[PermissionAdvisor] GovernanceAgent not available: {e}", extra={
            "operation": "permission_advisor",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Permission analysis skipped (GovernanceAgent not available)")
        ]

    except Exception as e:
        success = False
        logger.error(f"[PermissionAdvisor] Analysis failed: {e}", extra={
            "operation": "permission_advisor",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)
        state["permission_advisory"] = {"error": str(e)}
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Permission analysis failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("permission_advisor", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("permission_advisor", "reputation_advisor", trace_id)
    return state


def reputation_advisor_node(state: AgentState) -> AgentState:
    """
    Reputation Advisor node: Analyzes agent reputation for task execution

    Phase 4 PR-4 Enhancement (5-Agent Advisory Pipeline):
    - Provides reputation advisory for agent trustworthiness
    - Integrates with ReputationEngine via GovernanceAgent
    - Analyzes agent reputation score and level
    - Advisory role: provides recommendations but does not block execution

    Returns:
        Updated state with reputation_advisory, reputation_score, reputation_level
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    task_type = state.get("task_type", "unknown")

    metrics.record_node_start("reputation_advisor", trace_id)

    logger.info("[ReputationAdvisor] Starting reputation analysis", extra={
        "operation": "reputation_advisor",
        "trace_id": trace_id,
        "task_type": task_type
    })

    state["reputation_advisory"] = {}
    state["reputation_score"] = 100
    state["reputation_level"] = "trusted"

    success = True
    try:
        from governance_agent import get_governance_agent

        agent = get_governance_agent()

        reputation_data = {
            "agent_id": "orchestrator",
            "score": 100,
            "level": "trusted",
            "history": []
        }

        if agent.reputation_engine:
            try:
                reputation_data = agent.reputation_engine.get_reputation("orchestrator") or reputation_data
            except Exception as e:
                logger.warning(f"[ReputationAdvisor] ReputationEngine query failed: {e}")

        score = reputation_data.get("score", 100)
        level = reputation_data.get("level", "trusted")

        state["reputation_advisory"] = {
            "agent_id": reputation_data.get("agent_id", "orchestrator"),
            "score": score,
            "level": level,
            "history": reputation_data.get("history", []),
            "recommendations": []
        }
        state["reputation_score"] = score
        state["reputation_level"] = level

        logger.info("[ReputationAdvisor] Analysis complete", extra={
            "operation": "reputation_advisor",
            "trace_id": trace_id,
            "reputation_score": state["reputation_score"],
            "reputation_level": state["reputation_level"]
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Reputation analysis: score={state['reputation_score']}, level={state['reputation_level']}")
        ]

    except ImportError as e:
        logger.warning(f"[ReputationAdvisor] GovernanceAgent not available: {e}", extra={
            "operation": "reputation_advisor",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Reputation analysis skipped (GovernanceAgent not available)")
        ]

    except Exception as e:
        success = False
        logger.error(f"[ReputationAdvisor] Analysis failed: {e}", extra={
            "operation": "reputation_advisor",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)
        state["reputation_advisory"] = {"error": str(e)}
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Reputation analysis failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("reputation_advisor", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("reputation_advisor", "policy_enforcement", trace_id)
    return state


def pm_advisor_node(state: AgentState) -> AgentState:
    """
    PM Advisor node: Task decomposition and planning analysis

    Phase 3 PR-3 (#1815) PM Agent Integration:
    - Decomposes high-level goals into actionable sub-tasks
    - Provides confidence scores for generated plans
    - Identifies planning risks and dependencies
    - Generates implementation recommendations

    This is an advisory node that enhances the planner with structured
    task decomposition. It runs after the planner to provide additional
    planning insights.

    Returns:
        Updated state with pm_advisory, pm_sub_tasks, pm_confidence_score, pm_risk
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    goal = state.get("goal", "")
    repo = state.get("repo", "RC918/morningai")

    metrics.record_node_start("pm_advisor", trace_id)

    logger.info("[PMAdvisor] Starting goal decomposition", extra={
        "operation": "pm_advisor_node",
        "trace_id": trace_id,
        "goal": goal[:50]
    })

    state["pm_advisory"] = {}
    state["pm_sub_tasks"] = []
    state["pm_confidence_score"] = 0.0
    state["pm_risk"] = "info"

    success = False

    try:
        from pm_agent import get_pm_agent

        pm_agent = get_pm_agent()
        advisory = pm_agent.decompose_goal(goal, repo)

        state["pm_advisory"] = advisory.to_dict()
        state["pm_sub_tasks"] = [
            {
                "task_id": t.task_id,
                "title": t.title,
                "description": t.description,
                "estimated_effort": t.estimated_effort,
                "task_type": t.task_type,
                "priority": t.priority,
            }
            for t in advisory.sub_tasks
        ]
        state["pm_confidence_score"] = advisory.confidence_score
        state["pm_risk"] = advisory.overall_risk.value

        logger.info("[PMAdvisor] Goal decomposition complete", extra={
            "operation": "pm_advisor_node",
            "trace_id": trace_id,
            "sub_task_count": len(advisory.sub_tasks),
            "confidence_score": advisory.confidence_score,
            "risk": advisory.overall_risk.value
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"PM Advisory: {len(advisory.sub_tasks)} sub-tasks, confidence={advisory.confidence_score:.2f}, risk={advisory.overall_risk.value}")
        ]

        success = True

    except ImportError as e:
        logger.warning("[PMAdvisor] PM Agent not available: %s", e)
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="PM Advisory: PM Agent not available, skipping decomposition")
        ]
        success = True

    except Exception as e:
        logger.error("[PMAdvisor] Goal decomposition failed: %s", e, extra={
            "operation": "pm_advisor_node",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"PM Advisory failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("pm_advisor", trace_id, success=success, latency_ms=latency_ms)
    return state


def ops_advisor_node(state: AgentState) -> AgentState:
    """
    Ops Advisor node: System health monitoring and operational recommendations

    Phase 3 PR-3 (#1815) Ops Agent Integration:
    - Monitors system health metrics
    - Analyzes structured logs for issues
    - Recommends operational actions (restart, rollback, scaling)
    - Integrates with HITL for high-risk operation approval

    This is an advisory node that provides operational insights.
    It can be triggered on-demand or as part of the workflow.

    Returns:
        Updated state with ops_advisory, ops_health_status, ops_risk, ops_recommended_actions
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("ops_advisor", trace_id)

    logger.info("[OpsAdvisor] Starting health check", extra={
        "operation": "ops_advisor_node",
        "trace_id": trace_id
    })

    state["ops_advisory"] = {}
    state["ops_health_status"] = "unknown"
    state["ops_risk"] = "info"
    state["ops_recommended_actions"] = []

    success = False

    try:
        from ops_agent import get_ops_agent

        ops_agent = get_ops_agent()
        advisory = ops_agent.check_system_health()

        state["ops_advisory"] = advisory.to_dict()
        state["ops_health_status"] = advisory.health_status.value
        state["ops_risk"] = advisory.overall_risk.value
        state["ops_recommended_actions"] = [
            {
                "action_type": a.action_type.value,
                "target": a.target,
                "reason": a.reason,
                "urgency": a.urgency.value,
                "requires_approval": a.requires_approval,
            }
            for a in advisory.recommended_actions
        ]

        logger.info("[OpsAdvisor] Health check complete", extra={
            "operation": "ops_advisor_node",
            "trace_id": trace_id,
            "health_status": advisory.health_status.value,
            "risk": advisory.overall_risk.value,
            "actions_count": len(advisory.recommended_actions)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Ops Advisory: health={advisory.health_status.value}, risk={advisory.overall_risk.value}, {len(advisory.recommended_actions)} recommended actions")
        ]

        success = True

    except ImportError as e:
        logger.warning("[OpsAdvisor] Ops Agent not available: %s", e)
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Ops Advisory: Ops Agent not available, skipping health check")
        ]
        success = True

    except Exception as e:
        logger.error("[OpsAdvisor] Health check failed: %s", e, extra={
            "operation": "ops_advisor_node",
            "trace_id": trace_id,
            "error": str(e)
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Ops Advisory failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("ops_advisor", trace_id, success=success, latency_ms=latency_ms)
    return state


RISK_SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def policy_enforcement_node(state: AgentState) -> AgentState:
    """
    Policy Enforcement node: Evaluates advisory results and enforces security policy

    PR-2 Policy Enforcement Integration:
    - Reads SECURITY_ENFORCEMENT_MODE from settings
    - Evaluates risk levels from all advisory nodes
    - Blocks execution if risk exceeds threshold for the configured mode
    - Modes:
        - advisory: Never block, only log (default)
        - block_critical: Block if any advisor returns critical risk
        - block_high: Block if any advisor returns high or critical risk
        - block_all: Block if any advisor returns non-info risk

    Returns:
        Updated state with policy_blocked and policy_block_reason
    """
    from common.config.settings import get_settings

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("policy_enforcement", trace_id)

    state["policy_blocked"] = False
    state["policy_block_reason"] = ""

    settings = get_settings()
    mode = settings.security_enforcement_mode

    logger.info("[PolicyEnforcement] Evaluating policy", extra={
        "operation": "policy_enforcement",
        "trace_id": trace_id,
        "enforcement_mode": mode
    })

    if mode == "advisory":
        logger.info("[PolicyEnforcement] Advisory mode - no blocking", extra={
            "operation": "policy_enforcement",
            "trace_id": trace_id,
            "enforcement_mode": mode
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Policy enforcement: mode={mode}, no blocking")
        ]
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("policy_enforcement", trace_id, success=True, latency_ms=latency_ms)
        metrics.record_transition("policy_enforcement", "executor", trace_id)
        return state

    advisor_risks = {
        "security": state.get("security_risk", "info"),
        "governance": state.get("governance_risk", "info"),
        "cost": state.get("cost_risk", "info"),
        "permission": state.get("permission_risk", "info"),
    }

    mode_thresholds = {
        "block_critical": 4,
        "block_high": 3,
        "block_all": 1,
    }

    threshold = mode_thresholds.get(mode, 5)

    worst_risk = "info"
    worst_severity = 0
    worst_advisor = "none"

    for advisor, risk in advisor_risks.items():
        severity = RISK_SEVERITY.get(risk, 0)
        if severity > worst_severity:
            worst_severity = severity
            worst_risk = risk
            worst_advisor = advisor

    should_block = worst_severity >= threshold

    severity_to_risk = {v: k for k, v in RISK_SEVERITY.items()}
    threshold_name = severity_to_risk.get(threshold, "none")

    if should_block:
        block_reason = f"{worst_advisor}_risk={worst_risk} (mode={mode}, threshold={threshold_name})"
        state["policy_blocked"] = True
        state["policy_block_reason"] = block_reason

        logger.warning("[PolicyEnforcement] Blocking execution", extra={
            "operation": "policy_enforcement",
            "trace_id": trace_id,
            "enforcement_mode": mode,
            "worst_advisor": worst_advisor,
            "worst_risk": worst_risk,
            "block_reason": block_reason
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Policy enforcement: BLOCKED - {block_reason}")
        ]
    else:
        logger.info("[PolicyEnforcement] Allowing execution", extra={
            "operation": "policy_enforcement",
            "trace_id": trace_id,
            "enforcement_mode": mode,
            "worst_advisor": worst_advisor,
            "worst_risk": worst_risk
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Policy enforcement: mode={mode}, worst_risk={worst_risk} from {worst_advisor}, allowing execution")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("policy_enforcement", trace_id, success=True, latency_ms=latency_ms)

    if should_block:
        metrics.record_transition("policy_enforcement", "finalizer", trace_id)
    else:
        metrics.record_transition("policy_enforcement", "executor", trace_id)

    return state


def should_proceed_after_policy(state: AgentState) -> str:
    """
    Determines if execution should proceed after policy enforcement

    Returns:
        "executor" if not blocked, "finalizer" if blocked by policy
    """
    if state.get("policy_blocked", False):
        return "finalize"
    return "execute"


def executor_node(state: AgentState) -> AgentState:
    """
    Executor node: Executes the current step in the plan
    """
    from graph import execute

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    goal = state["goal"]
    repo = state["repo"]
    current_step = state["current_step"]
    plan = state["plan"]

    metrics.record_node_start("executor", trace_id)

    logger.info(f"[Executor] Executing step {current_step + 1}/{len(plan)}", extra={
        "operation": "executor",
        "trace_id": trace_id,
        "step": plan[current_step] if current_step < len(plan) else "unknown"
    })

    success = True
    try:
        pr_url, ci_state, trace_id = execute(goal, repo, trace_id=trace_id)

        state["pr_url"] = pr_url
        state["ci_state"] = ci_state
        state["error"] = None
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Executed step: {plan[current_step]}. PR created: {pr_url}")
        ]

        logger.info("[Executor] Step completed successfully", extra={
            "operation": "executor",
            "trace_id": trace_id,
            "pr_url": pr_url,
            "ci_state": ci_state
        })

    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"[Executor] Step failed: {error_msg}", extra={
            "operation": "executor",
            "trace_id": trace_id,
            "error": error_msg
        })

        state["error"] = error_msg
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Error in step {plan[current_step]}: {error_msg}")
        ]

    state["current_step"] = current_step + 1
    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("executor", trace_id, success=success, latency_ms=latency_ms)
    return state


def ci_monitor_node(state: AgentState) -> AgentState:
    """
    CI Monitor node: Checks CI status and determines next action
    """
    from tools import github_api
    from exceptions import GitHubAuthenticationError, GitHubResourceNotFoundError

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    pr_number = state.get("pr_number")

    metrics.record_node_start("ci_monitor", trace_id)

    # Handle dry_run mode - skip CI checks entirely
    ci_state = state.get("ci_state")
    if ci_state == "dry_run":
        logger.info("[CI Monitor] Dry run mode - skipping CI checks", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "ci_state": ci_state
        })
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("ci_monitor", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Check if GitHub token is configured before attempting to call GitHub API
    # This prevents noisy Sentry alerts in environments where GitHub is not configured
    # Use github_api.GITHUB_TOKEN so tests can patch it (same source as the API layer)
    github_token_configured = bool(github_api.GITHUB_TOKEN)
    if not github_token_configured:
        logger.info("[CI Monitor] GitHub token not configured, skipping CI checks", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "reason": "no_github_token"
        })
        state["ci_state"] = "unknown"
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("ci_monitor", trace_id, success=True, latency_ms=latency_ms)
        return state

    if not pr_number:
        logger.warning("[CI Monitor] No PR number available", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id
        })
        state["ci_state"] = "unknown"
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("ci_monitor", trace_id, success=True, latency_ms=latency_ms)
        return state

    logger.info(f"[CI Monitor] Checking CI for PR #{pr_number}", extra={
        "operation": "ci_monitor",
        "trace_id": trace_id,
        "pr_number": pr_number
    })

    success = True
    try:
        repo = github_api.get_repo()
        ci_state, checks = github_api.get_pr_checks(repo, pr_number)

        state["ci_state"] = ci_state
        state["ci_checks"] = checks
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"CI state: {ci_state}, Checks: {len(checks) if checks else 0}")
        ]

        logger.info(f"[CI Monitor] CI state: {ci_state}", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "pr_number": pr_number,
            "ci_state": ci_state,
            "checks_count": len(checks) if checks else 0
        })

    except GitHubAuthenticationError as e:
        # Authentication errors are expected in environments without valid tokens
        # Log at warning level to avoid noisy Sentry alerts
        logger.warning(f"[CI Monitor] GitHub authentication error, disabling CI checks: {e}", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "error_type": "GitHubAuthenticationError",
            "error": str(e)
        })
        state["ci_state"] = "unknown"
        # Don't set state["error"] for auth errors - this is expected in some environments

    except GitHubResourceNotFoundError as e:
        # Resource not found errors (repo, PR) are expected in some cases
        # Log at warning level
        logger.warning(f"[CI Monitor] GitHub resource not found: {e}", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "error_type": "GitHubResourceNotFoundError",
            "error": str(e)
        })
        state["ci_state"] = "unknown"
        state["error"] = str(e)

    except Exception as e:
        # For other errors (rate limits, network issues), log at error level
        success = False
        error_msg = str(e)
        logger.error(f"[CI Monitor] Failed to check CI: {error_msg}", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "error_type": type(e).__name__,
            "error": error_msg
        })
        state["ci_state"] = "error"
        state["error"] = error_msg

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("ci_monitor", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("ci_monitor", "reviewer", trace_id)
    return state


def fixer_node(state: AgentState) -> AgentState:
    """
    Fixer node: Attempts to fix CI failures

    Phase 2 Step C Enhancement:
    - Integrates AutoFixer for automated fix attempts
    - Uses ReviewerAgent to analyze code issues
    - Uses ProjectEngineerAgent to generate fixes
    - Supports canary rollout via PROJECT_ENGINEER_FIXER_PERCENT
    """
    from common.config.settings import settings

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    retry_count = state.get("retry_count", 0)

    metrics.record_node_start("fixer", trace_id)

    AutoFixer = None
    max_retries = MAX_FIXER_RETRIES
    try:
        from project_engineer.fixer_integration import AutoFixer as _AutoFixer
        AutoFixer = _AutoFixer
        max_retries = getattr(AutoFixer, "MAX_FIX_RETRIES", MAX_FIXER_RETRIES)
    except ImportError:
        pass

    logger.info(f"[Fixer] Attempting to fix CI failures (retry {retry_count})", extra={
        "operation": "fixer",
        "trace_id": trace_id,
        "retry_count": retry_count
    })

    if retry_count >= max_retries:
        last_error = state.get("error") or "Unknown error"
        logger.warning(
            "[Fixer] Max retries reached (%d/%d), giving up. "
            "autofixer_max_retries_reached=true last_error=%s trace_id=%s",
            retry_count, max_retries, last_error, trace_id,
            extra={
                "operation": "fixer",
                "trace_id": trace_id,
                "retry_count": retry_count,
                "max_retries": max_retries,
                "autofixer_max_retries_reached": True,
                "last_error": last_error
            }
        )
        state["error"] = last_error if last_error != "Unknown error" else "Max retries exceeded"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"AutoFixer gave up after {retry_count} retries. Last error: {last_error}")
        ]
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_fixer_attempt(trace_id, retry_count, success=False)
        metrics.record_node_complete("fixer", trace_id, success=False, latency_ms=latency_ms)
        return state

    try:
        if AutoFixer is None:
            raise ImportError("AutoFixer not available")

        auto_fixer = AutoFixer(settings=settings)

        if auto_fixer.should_run_for_task(state):
            logger.info("[Fixer] Running AutoFixer for task", extra={
                "operation": "fixer",
                "trace_id": trace_id,
                "retry_count": retry_count
            })

            state = auto_fixer.run_auto_fix_sync(state)

            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"AutoFixer attempt {retry_count + 1}/{max_retries} completed")
            ]
        else:
            logger.info("[Fixer] AutoFixer disabled or not selected for this task", extra={
                "operation": "fixer",
                "trace_id": trace_id,
                "retry_count": retry_count
            })

            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"Attempting to fix CI failures (attempt {retry_count + 1}/{max_retries}) - AutoFixer disabled")
            ]

    except ImportError as e:
        logger.warning(f"[Fixer] AutoFixer not available: {e}", extra={
            "operation": "fixer",
            "trace_id": trace_id,
            "error": str(e)
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Attempting to fix CI failures (attempt {retry_count + 1}/{max_retries})")
        ]

    except Exception as e:
        logger.error(f"[Fixer] AutoFixer failed: {e}", extra={
            "operation": "fixer",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)

        state["error"] = f"AutoFixer error: {str(e)}"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"AutoFixer failed: {str(e)}")
        ]

    state["retry_count"] = retry_count + 1
    latency_ms = (time.time() - start_time) * 1000
    success = state.get("error") is None
    metrics.record_fixer_attempt(trace_id, retry_count, success=success)
    metrics.record_node_complete("fixer", trace_id, success=success, latency_ms=latency_ms)
    metrics.record_transition("fixer", "executor", trace_id)

    agent_eval = _get_agent_eval()
    agent_eval.record_node_latency(trace_id, "fixer", latency_ms)
    agent_eval.record_fixer_iteration(trace_id, retry_count + 1, success)

    return state


def _ci_only_review(ci_state: str) -> dict:
    """
    Generate CI-only review results based on CI state

    Args:
        ci_state: CI check state (success, failure, pending, unknown)

    Returns:
        Dict with review_result, code_quality_score, review_severity, review_comments
    """
    if ci_state == "success":
        return {
            "review_result": {"status": "passed", "reason": "CI passed"},
            "code_quality_score": 80,
            "review_severity": "none",
            "review_comments": []
        }
    elif ci_state == "failure":
        return {
            "review_result": {"status": "needs_attention", "reason": "CI failed"},
            "code_quality_score": 40,
            "review_severity": "high",
            "review_comments": [{"severity": "high", "message": "CI checks failed"}]
        }
    else:
        return {
            "review_result": {"status": "pending", "reason": "CI pending"},
            "code_quality_score": 60,
            "review_severity": "medium",
            "review_comments": []
        }


def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviewer node: Analyzes code changes and provides review feedback

    Phase 6 PR-3 Enhancement:
    - LLM-powered code review with A/B testing support (OpenAI vs Gemini)
    - Uses CI state as baseline, LLM provides additional risk assessment
    - CI score acts as ceiling (LLM cannot claim higher quality than CI)
    - Graceful fallback to CI-only review if LLM unavailable

    Feature Flag: USE_LLM_REVIEWER (default: False)

    Returns:
        Updated state with review_result, review_comments, review_severity, code_quality_score
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    pr_number = state.get("pr_number")
    pr_url = state.get("pr_url")

    metrics.record_node_start("reviewer", trace_id)

    logger.info("[Reviewer] Starting code review", extra={
        "operation": "reviewer",
        "trace_id": trace_id,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "use_llm_reviewer": getattr(settings, 'use_llm_reviewer', False)
    })

    state["review_result"] = {}
    state["review_comments"] = []
    state["review_severity"] = "none"
    state["code_quality_score"] = 100

    if not pr_number and not pr_url:
        logger.info("[Reviewer] No PR to review, skipping", extra={
            "operation": "reviewer",
            "trace_id": trace_id
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="No PR available for review, skipping reviewer step")
        ]
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("reviewer", trace_id, success=True, latency_ms=latency_ms)
        return state

    success = True
    llm_used = False
    llm_provider = None

    try:
        ci_state = state.get("ci_state", "unknown")
        ci_review = _ci_only_review(ci_state)

        state["review_result"] = ci_review["review_result"]
        state["code_quality_score"] = ci_review["code_quality_score"]
        state["review_severity"] = ci_review["review_severity"]
        state["review_comments"] = ci_review["review_comments"]

        use_llm = getattr(settings, 'use_llm_reviewer', False)

        if use_llm:
            logger.info("[Reviewer] LLM reviewer enabled, attempting LLM review", extra={
                "operation": "reviewer",
                "trace_id": trace_id
            })

            try:
                goal = state.get("goal", "")
                repo = state.get("repo", "")

                llm_review = generate_llm_review(
                    pr_number=pr_number,
                    pr_url=pr_url,
                    ci_state=ci_state,
                    goal=goal,
                    repo=repo,
                    trace_id=trace_id,
                    base_quality_score=ci_review["code_quality_score"],
                    base_severity=ci_review["review_severity"]
                )

                if llm_review.get("llm_used", False):
                    llm_used = True
                    llm_provider = llm_review.get("provider")

                    state["code_quality_score"] = llm_review["quality_score"]
                    state["review_severity"] = llm_review["severity"]

                    if llm_review.get("comments"):
                        state["review_comments"] = (
                            state["review_comments"] + llm_review["comments"]
                        )

                    llm_decision = llm_review.get("decision", "needs_changes")
                    llm_summary = llm_review.get("summary", "")

                    state["review_result"] = {
                        "status": ci_review["review_result"]["status"],
                        "reason": ci_review["review_result"]["reason"],
                        "llm_decision": llm_decision,
                        "llm_summary": llm_summary,
                        "llm_provider": llm_provider
                    }

                    logger.info("[Reviewer] LLM review completed", extra={
                        "operation": "reviewer",
                        "trace_id": trace_id,
                        "llm_provider": llm_provider,
                        "llm_score": llm_review["quality_score"],
                        "llm_severity": llm_review["severity"],
                        "review_time_ms": llm_review.get("review_time_ms", 0)
                    })
                else:
                    logger.info("[Reviewer] LLM not available, using CI-only review", extra={
                        "operation": "reviewer",
                        "trace_id": trace_id
                    })

            except Exception as llm_error:
                logger.warning(f"[Reviewer] LLM review failed, using CI-only: {llm_error}", extra={
                    "operation": "reviewer",
                    "trace_id": trace_id,
                    "error": str(llm_error)
                })

        logger.info("[Reviewer] Review completed", extra={
            "operation": "reviewer",
            "trace_id": trace_id,
            "ci_state": ci_state,
            "quality_score": state["code_quality_score"],
            "llm_used": llm_used,
            "llm_provider": llm_provider
        })

        review_method = f"LLM ({llm_provider})" if llm_used else "CI-only"
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Code review completed ({review_method}). Quality score: {state['code_quality_score']}, Severity: {state['review_severity']}")
        ]

    except Exception as e:
        success = False
        logger.error(f"[Reviewer] Review failed: {e}", extra={
            "operation": "reviewer",
            "trace_id": trace_id,
            "error": str(e)
        }, exc_info=True)

        state["review_result"] = {"status": "error", "error": str(e)}
        state["review_severity"] = "unknown"
        state["code_quality_score"] = 0
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Code review failed: {str(e)}")
        ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("reviewer", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("reviewer", "decision", trace_id)
    return state


def decision_node(state: AgentState) -> AgentState:
    """
    Decision node: Makes merge/fix decision based on review results

    Phase 3 Enhancement:
    - Analyzes review results and CI state
    - Determines if PR should be approved, needs changes, or needs fixing
    - Supports automatic approval for high-quality, passing PRs

    Decision Logic:
    - approve: CI passed + quality score >= 70 + no critical/high issues
    - needs_fix: CI failed or quality score < 50 or critical issues
    - request_changes: quality score 50-70 or high severity issues

    Returns:
        Updated state with merge_decision
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    ci_state = state.get("ci_state", "unknown")
    review_severity = state.get("review_severity", "none")
    code_quality_score = state.get("code_quality_score", 100)
    error = state.get("error")

    metrics.record_node_start("decision", trace_id)

    logger.info("[Decision] Evaluating merge decision", extra={
        "operation": "decision",
        "trace_id": trace_id,
        "ci_state": ci_state,
        "review_severity": review_severity,
        "code_quality_score": code_quality_score,
        "has_error": bool(error)
    })

    # Default decision
    merge_decision = "pending"
    decision_reason = ""

    # Check for errors first
    if error:
        merge_decision = "needs_fix"
        decision_reason = f"Error occurred: {error}"
        logger.info("[Decision] Decision: needs_fix (error)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "reason": decision_reason
        })

    # Check CI state
    elif ci_state == "failure":
        merge_decision = "needs_fix"
        decision_reason = "CI checks failed"
        logger.info("[Decision] Decision: needs_fix (CI failed)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision
        })

    # Handle dry_run mode - treat as approved to skip CI monitoring loop
    elif ci_state == "dry_run":
        merge_decision = "approve"
        decision_reason = "Dry run mode: skipping CI checks and treating as approved"
        logger.info("[Decision] Decision: approve (dry_run)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "ci_state": ci_state
        })

    # Check for critical issues
    elif review_severity == "critical":
        merge_decision = "needs_fix"
        decision_reason = "Critical issues found in review"
        logger.info("[Decision] Decision: needs_fix (critical issues)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision
        })

    # Check quality score
    elif code_quality_score < 50:
        merge_decision = "needs_fix"
        decision_reason = f"Quality score too low: {code_quality_score}"
        logger.info("[Decision] Decision: needs_fix (low quality)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "quality_score": code_quality_score
        })

    # Check for high severity issues
    elif review_severity == "high":
        merge_decision = "request_changes"
        decision_reason = "High severity issues found"
        logger.info("[Decision] Decision: request_changes (high severity)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision
        })

    # Check for medium quality
    elif code_quality_score < 70:
        merge_decision = "request_changes"
        decision_reason = f"Quality score needs improvement: {code_quality_score}"
        logger.info("[Decision] Decision: request_changes (medium quality)", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "quality_score": code_quality_score
        })

    # All checks passed - approve
    elif ci_state == "success" and code_quality_score >= 70:
        merge_decision = "approve"
        decision_reason = f"All checks passed. Quality score: {code_quality_score}"
        logger.info("[Decision] Decision: approve", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "quality_score": code_quality_score
        })

    # CI pending or unknown
    else:
        merge_decision = "pending"
        decision_reason = f"Waiting for CI. Current state: {ci_state}"
        logger.info("[Decision] Decision: pending", extra={
            "operation": "decision",
            "trace_id": trace_id,
            "decision": merge_decision,
            "ci_state": ci_state
        })

    state["merge_decision"] = merge_decision
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"Merge decision: {merge_decision}. Reason: {decision_reason}")
    ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_decision(
        decision=merge_decision,
        trace_id=trace_id,
        quality_score=code_quality_score,
        review_severity=review_severity
    )
    metrics.record_node_complete("decision", trace_id, success=True, latency_ms=latency_ms)
    return state


def should_fix_or_finalize(state: AgentState) -> str:
    """
    Determines next step after decision node

    Routes to:
    - fix: If merge_decision is needs_fix and retries available
    - monitor_ci: If merge_decision is pending (waiting for CI)
    - finalize: If approved, request_changes, or max retries reached
    """
    merge_decision = state.get("merge_decision", "pending")
    retry_count = state.get("retry_count", 0)
    trace_id = state.get("trace_id", "unknown")
    metrics = _get_metrics()

    outcome_to_node = {
        "fix": "fixer",
        "monitor_ci": "ci_monitor",
        "finalize": "finalizer",
    }

    # If decision is pending (CI still running), go back to monitor CI
    if merge_decision == "pending":
        outcome = "monitor_ci"
    elif merge_decision == "needs_fix":
        if retry_count >= MAX_FIXER_RETRIES:
            outcome = "finalize"
        else:
            outcome = "fix"
    else:
        # approve, request_changes all go to finalize
        outcome = "finalize"

    to_node = outcome_to_node[outcome]
    metrics.record_transition("decision", to_node, trace_id)
    return outcome


def _observe_failure_for_learning(state: AgentState) -> None:
    """
    Phase 2 PR-1811: Observer Node helper function

    Records workflow failures to pgvector for future learning.
    This enables the Planner to query past failures and learn from mistakes.

    Args:
        state: AgentState dictionary from orchestrator
    """
    try:
        from observer_node import observe_failure

        trace_id = state.get("trace_id", "unknown")

        result = observe_failure(dict(state), save_to_pgvector=True)

        if result.get("saved_to_pgvector"):
            logger.info("[Observer] Failure recorded for learning", extra={
                "operation": "observe_failure_for_learning",
                "trace_id": trace_id,
                "pair_id": result.get("pair_id"),
                "error_type": result.get("error_type")
            })
        else:
            logger.debug("[Observer] Failure not saved to pgvector", extra={
                "operation": "observe_failure_for_learning",
                "trace_id": trace_id
            })

    except ImportError as e:
        logger.debug(f"[Observer] observer_node module not available: {e}")
    except Exception as e:
        # Never break the main flow - just log the error
        logger.warning(f"[Observer] Failed to record failure for learning: {e}", extra={
            "operation": "observe_failure_for_learning",
            "error": str(e)
        })


def finalizer_node(state: AgentState) -> AgentState:
    """
    Finalizer node: Prepares final result

    Phase 5 PR-1: Records failures when status=error or fixer exhausted retries
    PR-2: Handles policy-blocked tasks with status="blocked"
    Phase 2 PR-1811: Integrates Observer Node for failure learning
    """
    start_time = time.time()
    metrics = _get_metrics()
    failure_recorder = _get_failure_recorder()

    trace_id = state["trace_id"]
    pr_url = state.get("pr_url")
    ci_state = state.get("ci_state")
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    policy_blocked = state.get("policy_blocked", False)
    policy_block_reason = state.get("policy_block_reason", "")

    metrics.record_node_start("finalizer", trace_id)

    logger.info("[Finalizer] Preparing final result", extra={
        "operation": "finalizer",
        "trace_id": trace_id,
        "pr_url": pr_url,
        "ci_state": ci_state,
        "has_error": bool(error),
        "policy_blocked": policy_blocked
    })

    if policy_blocked:
        final_status = "blocked"
    elif error:
        final_status = "error"
    else:
        final_status = "success"

    final_result = {
        "trace_id": trace_id,
        "pr_url": pr_url,
        "ci_state": ci_state,
        "status": final_status,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }

    if policy_blocked:
        final_result["policy_block_reason"] = policy_block_reason
        final_result["security_risk"] = state.get("security_risk", "info")
        final_result["governance_risk"] = state.get("governance_risk", "info")
        final_result["cost_risk"] = state.get("cost_risk", "info")
        final_result["permission_risk"] = state.get("permission_risk", "info")

        failure_recorder.record_failure_from_state(
            state=dict(state),
            error_type="policy_blocked",
            error_message=policy_block_reason
        )

        # Phase 2 PR-1811: Observer Node - record failure to pgvector for learning
        _observe_failure_for_learning(state)

    elif final_status == "error":
        error_type = "workflow_error"
        if retry_count >= MAX_FIXER_RETRIES:
            error_type = "fixer_exhausted"
        elif ci_state in ["failure", "error"]:
            error_type = "ci_failure"

        failure_recorder.record_failure_from_state(
            state=dict(state),
            error_type=error_type,
            error_message=error
        )

        # Phase 2 PR-1811: Observer Node - record failure to pgvector for learning
        _observe_failure_for_learning(state)

    state["final_result"] = final_result
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"Workflow completed. Status: {final_result['status']}")
    ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("finalizer", trace_id, success=True, latency_ms=latency_ms)
    return state


def evaluation_node(state: AgentState) -> AgentState:
    """
    Evaluation node: Detects capability regression (Phase 2 PR-1813)

    This is the "IQ test" for the agent - detecting catastrophic forgetting
    where the agent's performance degrades over time during self-modification.

    The node:
    1. Collects metrics from the completed workflow
    2. Compares against baseline thresholds
    3. Detects capability regression
    4. Generates evaluation report
    5. Triggers alerts if regression is detected

    This node runs after finalizer to evaluate the overall workflow performance.
    """
    start_time = time.time()
    metrics = _get_metrics()
    agent_eval = _get_agent_eval()

    trace_id = state["trace_id"]
    final_result = state.get("final_result", {})

    metrics.record_node_start("evaluation", trace_id)

    # Check both settings flag and integration enabled status
    # This handles cases where Redis is unavailable during initialization
    if not settings.enable_agent_eval or not getattr(agent_eval, "enabled", False):
        reason = "disabled via settings" if not settings.enable_agent_eval else "no metrics backend available"
        logger.info(f"[Evaluation] Agent evaluation {reason}", extra={
            "operation": "evaluation",
            "trace_id": trace_id,
            "settings_enabled": settings.enable_agent_eval,
            "integration_enabled": getattr(agent_eval, "enabled", False)
        })
        state["evaluation_result"] = {"enabled": False, "reason": reason}
        state["evaluation_health_status"] = "unknown"
        state["evaluation_has_regression"] = False

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("evaluation", trace_id, success=True, latency_ms=latency_ms)
        return state

    logger.info("[Evaluation] Running capability regression detection", extra={
        "operation": "evaluation",
        "trace_id": trace_id,
        "final_status": final_result.get("status")
    })

    try:
        regression_result = agent_eval.detect_capability_regression(
            success_rate_threshold=settings.agent_eval_success_rate_threshold,
            ci_pass_rate_threshold=settings.agent_eval_ci_pass_rate_threshold,
            fixer_success_threshold=settings.agent_eval_fixer_success_threshold,
            sample_size=settings.agent_eval_baseline_sample_size
        )

        has_regression = regression_result.get("has_regression", False)
        has_critical = regression_result.get("has_critical_regression", False)

        if has_regression:
            health_status = "critical" if has_critical else "degraded"
        else:
            health_status = "healthy"

        state["evaluation_result"] = regression_result
        state["evaluation_health_status"] = health_status
        state["evaluation_has_regression"] = has_regression

        if has_regression and settings.agent_eval_regression_alert_enabled:
            logger.warning(
                "[Evaluation] Capability regression detected - alerting",
                extra={
                    "operation": "evaluation_alert",
                    "trace_id": trace_id,
                    "health_status": health_status,
                    "regressions": regression_result.get("regressions", []),
                    "recommendations": regression_result.get("recommendations", [])
                }
            )

        logger.info("[Evaluation] Capability regression detection completed", extra={
            "operation": "evaluation",
            "trace_id": trace_id,
            "health_status": health_status,
            "has_regression": has_regression,
            "success_rate": regression_result.get("metrics", {}).get("success_rate"),
            "ci_pass_rate": regression_result.get("metrics", {}).get("ci_pass_rate")
        })

    except Exception as e:
        # Check if this is a Redis connectivity issue - treat as "eval disabled"
        # rather than an error to avoid noisy Sentry alerts for expected conditions
        error_str = str(e).lower()
        is_redis_error = (
            "redis" in error_str or
            "connection" in error_str or
            "timeout" in error_str or
            "refused" in error_str or
            hasattr(e, '__module__') and 'redis' in getattr(e, '__module__', '')
        )

        if is_redis_error:
            logger.warning("[Evaluation] Redis unavailable, skipping regression detection: %s", e, extra={
                "operation": "evaluation",
                "trace_id": trace_id,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            state["evaluation_result"] = {"enabled": False, "reason": "Redis unavailable", "error": str(e)}
        else:
            # For non-Redis errors, log at error level as these may indicate real bugs
            logger.error("[Evaluation] Failed to run capability regression detection: %s", e, extra={
                "operation": "evaluation",
                "trace_id": trace_id,
                "error_type": type(e).__name__,
                "error": str(e)
            })
            state["evaluation_result"] = {"error": str(e)}

        state["evaluation_health_status"] = "unknown"
        state["evaluation_has_regression"] = False

    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"Evaluation completed. Health status: {state['evaluation_health_status']}")
    ]

    # Calculate latency once and use for both metrics systems (Gemini #13)
    latency_ms = (time.time() - start_time) * 1000
    agent_eval.record_node_latency(trace_id, "evaluation", latency_ms)
    metrics.record_node_complete("evaluation", trace_id, success=True, latency_ms=latency_ms)
    return state


def should_continue_execution(state: AgentState) -> str:
    """
    Determines if execution should continue to next step or move to CI monitoring
    """
    error = state.get("error")
    current_step = state.get("current_step", 0)
    plan = state.get("plan", [])
    trace_id = state.get("trace_id", "unknown")
    metrics = _get_metrics()

    outcome_to_node = {
        "execute": "executor",
        "monitor_ci": "ci_monitor",
        "fix": "fixer",
        "finalize": "finalizer",
    }

    if error:
        retry_count = state.get("retry_count", 0)
        if retry_count >= MAX_FIXER_RETRIES:
            outcome = "finalize"
        else:
            outcome = "fix"
    elif current_step >= len(plan):
        outcome = "monitor_ci"
    else:
        outcome = "execute"

    to_node = outcome_to_node[outcome]
    metrics.record_transition("executor", to_node, trace_id)
    return outcome


def should_retry_or_finish(state: AgentState) -> str:
    """
    Determines if CI monitoring should continue, fix, or finish
    """
    ci_state = state.get("ci_state", "unknown")
    error = state.get("error")

    if error:
        return "finalize"

    if ci_state == "success":
        return "finalize"
    elif ci_state in ["failure", "error"]:
        retry_count = state.get("retry_count", 0)
        if retry_count >= MAX_FIXER_RETRIES:
            return "finalize"
        return "fix"
    else:
        return "monitor_ci"


def create_orchestrator_graph():
    """
    Creates the LangGraph StateGraph for orchestration

    Phase 2 PR-1813 Update (Agent Evaluation):
        planner → security_advisor → governance_advisor → cost_advisor → permission_advisor → reputation_advisor → policy_enforcement → (executor | finalizer) → ci_monitor → reviewer → decision → (fixer if needed) → finalizer → evaluation → END

    5-Agent Advisory Pipeline Nodes:
        1. security_advisor: Security analysis (Phase 4 PR-2)
        2. governance_advisor: Governance compliance analysis (Phase 4 PR-3)
        3. cost_advisor: Cost budget analysis (Phase 4 PR-4)
        4. permission_advisor: Permission verification (Phase 4 PR-4)
        5. reputation_advisor: Reputation assessment (Phase 4 PR-4)

    Policy Enforcement Node (PR-2):
        - policy_enforcement: Evaluates advisory results and enforces SECURITY_ENFORCEMENT_MODE
        - Routes to executor if allowed, finalizer if blocked

    Agent Evaluation Node (Phase 2 PR-1813):
        - evaluation: Detects capability regression ("IQ test" for catastrophic forgetting)
        - Runs after finalizer to evaluate overall workflow performance
        - Compares metrics against baseline thresholds
        - Triggers alerts if regression is detected

    Phase 3 PR-3 (#1815) PM Agent + Ops Agent Nodes:
        - pm_advisor: Task decomposition and planning analysis
        - ops_advisor: System health monitoring and operational recommendations

    Other Nodes:
        - planner: Task decomposition using LLM Planner
        - executor: Code generation execution
        - ci_monitor: CI status monitoring
        - reviewer: Code review and analysis
        - decision: Merge decision logic
        - fixer: Auto-fix CI failures
        - finalizer: Prepare final result

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("planner", planner_node)
    # Phase 3 PR-3 (#1815): PM Agent + Ops Agent nodes
    workflow.add_node("pm_advisor", pm_advisor_node)
    workflow.add_node("ops_advisor", ops_advisor_node)
    # 5-Agent Advisory Pipeline nodes
    workflow.add_node("security_advisor", security_advisor_node)
    workflow.add_node("governance_advisor", governance_advisor_node)
    workflow.add_node("cost_advisor", cost_advisor_node)
    workflow.add_node("permission_advisor", permission_advisor_node)
    workflow.add_node("reputation_advisor", reputation_advisor_node)
    # Policy Enforcement node (PR-2)
    workflow.add_node("policy_enforcement", policy_enforcement_node)
    # Execution nodes
    workflow.add_node("executor", executor_node)
    workflow.add_node("ci_monitor", ci_monitor_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("finalizer", finalizer_node)
    # Phase 2 PR-1813: Agent Evaluation node
    workflow.add_node("evaluation", evaluation_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Phase 3 PR-3 (#1815): PM Agent + Ops Agent edges
    # planner → pm_advisor (task decomposition after planning)
    workflow.add_edge("planner", "pm_advisor")

    # pm_advisor → ops_advisor (health check before security analysis)
    workflow.add_edge("pm_advisor", "ops_advisor")

    # ops_advisor → security_advisor (continue to security analysis)
    workflow.add_edge("ops_advisor", "security_advisor")

    # 5-Agent Advisory Pipeline edges (Phase 4 PR-4)

    # security_advisor → governance_advisor (Phase 4 PR-3)
    workflow.add_edge("security_advisor", "governance_advisor")

    # governance_advisor → cost_advisor (Phase 4 PR-4)
    workflow.add_edge("governance_advisor", "cost_advisor")

    # cost_advisor → permission_advisor (Phase 4 PR-4)
    workflow.add_edge("cost_advisor", "permission_advisor")

    # permission_advisor → reputation_advisor (Phase 4 PR-4)
    workflow.add_edge("permission_advisor", "reputation_advisor")

    # reputation_advisor → policy_enforcement (PR-2: policy enforcement gate)
    workflow.add_edge("reputation_advisor", "policy_enforcement")

    # policy_enforcement → (executor | finalizer) based on policy decision (PR-2)
    workflow.add_conditional_edges(
        "policy_enforcement",
        should_proceed_after_policy,
        {
            "execute": "executor",
            "finalize": "finalizer"
        }
    )

    # executor → (execute | monitor_ci | fix | finalize)
    workflow.add_conditional_edges(
        "executor",
        should_continue_execution,
        {
            "execute": "executor",
            "monitor_ci": "ci_monitor",
            "fix": "fixer",
            "finalize": "finalizer"
        }
    )

    # ci_monitor → reviewer (Phase 3: always go to reviewer after CI check)
    workflow.add_edge("ci_monitor", "reviewer")

    # reviewer → decision
    workflow.add_edge("reviewer", "decision")

    # decision → (fix | monitor_ci | finalize)
    workflow.add_conditional_edges(
        "decision",
        should_fix_or_finalize,
        {
            "fix": "fixer",
            "monitor_ci": "ci_monitor",
            "finalize": "finalizer"
        }
    )

    # fixer → executor (retry loop)
    workflow.add_edge("fixer", "executor")

    # finalizer → evaluation (Phase 2 PR-1813: Agent Evaluation)
    workflow.add_edge("finalizer", "evaluation")

    # evaluation → END (Phase 2 PR-1813)
    workflow.add_edge("evaluation", END)

    # Use factory function to get appropriate checkpointer (Redis or Memory)
    checkpointer = get_checkpointer()

    app = workflow.compile(checkpointer=checkpointer)

    logger.info("LangGraph orchestrator workflow compiled successfully (Phase 4 PR-4: 5-Agent Advisory Pipeline)")

    return app


def run_orchestrator(goal: str, repo: str, trace_id: str) -> dict:
    """
    Run the LangGraph orchestrator workflow

    Args:
        goal: User's goal/question
        repo: GitHub repository (owner/repo format)
        trace_id: Unique identifier for this task

    Returns:
        dict: Final result containing pr_url, ci_state, status, etc.
    """
    start_time = time.time()
    metrics = _get_metrics()

    logger.info("Starting LangGraph orchestrator", extra={
        "operation": "run_orchestrator",
        "trace_id": trace_id,
        "goal": goal[:50],
        "repo": repo
    })

    metrics.record_workflow_start(trace_id, goal)

    agent_eval = _get_agent_eval()
    agent_eval.start_workflow_metrics(trace_id, goal)

    app = create_orchestrator_graph()

    initial_state = {
        "messages": [HumanMessage(content=goal)],
        "goal": goal,
        "trace_id": trace_id,
        "repo": repo,
        "branch": "",
        "plan": [],
        "current_step": 0,
        "pr_url": "",
        "pr_number": 0,
        "ci_state": "pending",
        "ci_checks": {},
        "error": None,
        "retry_count": 0,
        "final_result": {},
        "review_result": {},
        "review_comments": [],
        "review_severity": "none",
        "merge_decision": "pending",
        "code_quality_score": 100,
        "security_advisory": {},
        "security_risk": "info",
        "security_findings": [],
        "security_is_safe": True,
        "governance_advisory": {},
        "governance_risk": "info",
        "governance_findings": [],
        "governance_is_compliant": True,
        "cost_advisory": {},
        "cost_risk": "info",
        "cost_within_budget": True,
        "permission_advisory": {},
        "permission_risk": "info",
        "permission_granted": True,
        "reputation_advisory": {},
        "reputation_score": 100,
        "reputation_level": "trusted",
        "policy_blocked": False,
        "policy_block_reason": "",
        "evaluation_result": {},
        "evaluation_health_status": "unknown",
        "evaluation_has_regression": False,
        # Phase 3 PR-3 (#1815): PM Agent + Ops Agent initial state
        "pm_advisory": {},
        "pm_sub_tasks": [],
        "pm_confidence_score": 0.0,
        "pm_risk": "info",
        "ops_advisory": {},
        "ops_health_status": "unknown",
        "ops_risk": "info",
        "ops_recommended_actions": []
    }

    config = {"configurable": {"thread_id": trace_id}}

    try:
        result = app.invoke(initial_state, config)

        final_result = result.get("final_result", {})

        logger.info("LangGraph orchestrator completed", extra={
            "operation": "run_orchestrator",
            "trace_id": trace_id,
            "status": final_result.get("status"),
            "pr_url": final_result.get("pr_url")
        })

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="success", latency_ms=latency_ms)

        agent_eval.record_workflow_result(
            trace_id,
            status="success",
            pr_created=bool(final_result.get("pr_url")),
            ci_passed=final_result.get("ci_state") == "success",
            code_quality_score=result.get("code_quality_score", 100)
        )
        agent_eval.complete_workflow_metrics(trace_id)

        return final_result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"LangGraph orchestrator failed: {error_msg}", extra={
            "operation": "run_orchestrator",
            "trace_id": trace_id,
            "error": error_msg
        })

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="error", latency_ms=latency_ms)

        failure_recorder = _get_failure_recorder()
        failure_recorder.record_failure_from_state(
            state={"trace_id": trace_id, "goal": goal, "repo": repo},
            error_type="workflow_exception",
            error_message=error_msg
        )

        agent_eval.record_workflow_result(
            trace_id,
            status="error",
            pr_created=False,
            ci_passed=False
        )
        agent_eval.complete_workflow_metrics(trace_id)

        return {
            "trace_id": trace_id,
            "pr_url": None,
            "ci_state": "error",
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
