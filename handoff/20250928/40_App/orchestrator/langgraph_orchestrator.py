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

import logging
import time
from typing import TypedDict, Annotated, Sequence, Optional
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from orchestrator_metrics import get_orchestrator_metrics, OrchestratorMetrics

logger = logging.getLogger(__name__)

# Global metrics instance (lazy initialization)
_metrics: Optional[OrchestratorMetrics] = None


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


def planner_node(state: AgentState) -> AgentState:
    """
    Planning node: Analyzes the goal and creates a plan

    Phase 1: Integrates LLM-powered dynamic planning when USE_LLM_PLANNER=true
    """
    from common.config.settings import settings

    start_time = time.time()
    metrics = _get_metrics()

    goal = state["goal"]
    repo = state.get("repo", "RC918/morningai")
    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("planner", trace_id)

    logger.info("[Planner] Analyzing goal", extra={
        "operation": "planner",
        "trace_id": trace_id,
        "goal": goal[:50],
        "use_llm_planner": settings.use_llm_planner
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
        metrics.record_transition("reputation_advisor", "executor", trace_id)
    return state


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
    from tools.github_api import get_repo, get_pr_checks

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    pr_number = state.get("pr_number")

    metrics.record_node_start("ci_monitor", trace_id)

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
        repo = get_repo()
        ci_state, checks = get_pr_checks(repo, pr_number)

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

    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"[CI Monitor] Failed to check CI: {error_msg}", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
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
    return state


def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviewer node: Analyzes code changes and provides review feedback

    Phase 3 Enhancement:
    - Uses CI state as primary review signal (ReviewerAgent integration planned for Phase 3 PR-4)
    - Identifies code quality issues based on CI results
    - Provides structured review with severity levels
    - Calculates code quality score

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
        "pr_url": pr_url
    })

    # Initialize review state
    state["review_result"] = {}
    state["review_comments"] = []
    state["review_severity"] = "none"
    state["code_quality_score"] = 100

    # Skip review if no PR exists
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
    try:
        # CI-based review (ReviewerAgent integration planned for Phase 3 PR-4)
        ci_state = state.get("ci_state", "unknown")

        if ci_state == "success":
            state["review_result"] = {"status": "passed", "reason": "CI passed"}
            state["code_quality_score"] = 80
            state["review_severity"] = "none"
        elif ci_state == "failure":
            state["review_result"] = {"status": "needs_attention", "reason": "CI failed"}
            state["code_quality_score"] = 40
            state["review_severity"] = "high"
            state["review_comments"] = [{"severity": "high", "message": "CI checks failed"}]
        else:
            state["review_result"] = {"status": "pending", "reason": "CI pending"}
            state["code_quality_score"] = 60
            state["review_severity"] = "medium"

        logger.info("[Reviewer] Review completed", extra={
            "operation": "reviewer",
            "trace_id": trace_id,
            "ci_state": ci_state,
            "quality_score": state["code_quality_score"]
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Code review completed. Quality score: {state['code_quality_score']}, Severity: {state['review_severity']}")
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


def finalizer_node(state: AgentState) -> AgentState:
    """
    Finalizer node: Prepares final result
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    pr_url = state.get("pr_url")
    ci_state = state.get("ci_state")
    error = state.get("error")

    metrics.record_node_start("finalizer", trace_id)

    logger.info("[Finalizer] Preparing final result", extra={
        "operation": "finalizer",
        "trace_id": trace_id,
        "pr_url": pr_url,
        "ci_state": ci_state,
        "has_error": bool(error)
    })

    final_result = {
        "trace_id": trace_id,
        "pr_url": pr_url,
        "ci_state": ci_state,
        "status": "success" if not error else "error",
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }

    state["final_result"] = final_result
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"Workflow completed. Status: {final_result['status']}")
    ]

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("finalizer", trace_id, success=True, latency_ms=latency_ms)
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

    Phase 4 PR-4: 5-Agent Advisory Pipeline:
        planner → security_advisor → governance_advisor → cost_advisor → permission_advisor → reputation_advisor → executor → ci_monitor → reviewer → decision → (fixer if needed) → finalizer

    5-Agent Advisory Pipeline Nodes:
        1. security_advisor: Security analysis (Phase 4 PR-2)
        2. governance_advisor: Governance compliance analysis (Phase 4 PR-3)
        3. cost_advisor: Cost budget analysis (Phase 4 PR-4)
        4. permission_advisor: Permission verification (Phase 4 PR-4)
        5. reputation_advisor: Reputation assessment (Phase 4 PR-4)

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
    # 5-Agent Advisory Pipeline nodes
    workflow.add_node("security_advisor", security_advisor_node)
    workflow.add_node("governance_advisor", governance_advisor_node)
    workflow.add_node("cost_advisor", cost_advisor_node)
    workflow.add_node("permission_advisor", permission_advisor_node)
    workflow.add_node("reputation_advisor", reputation_advisor_node)
    # Execution nodes
    workflow.add_node("executor", executor_node)
    workflow.add_node("ci_monitor", ci_monitor_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("finalizer", finalizer_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # 5-Agent Advisory Pipeline edges (Phase 4 PR-4)
    # planner → security_advisor (Phase 4 PR-2)
    workflow.add_edge("planner", "security_advisor")

    # security_advisor → governance_advisor (Phase 4 PR-3)
    workflow.add_edge("security_advisor", "governance_advisor")

    # governance_advisor → cost_advisor (Phase 4 PR-4)
    workflow.add_edge("governance_advisor", "cost_advisor")

    # cost_advisor → permission_advisor (Phase 4 PR-4)
    workflow.add_edge("cost_advisor", "permission_advisor")

    # permission_advisor → reputation_advisor (Phase 4 PR-4)
    workflow.add_edge("permission_advisor", "reputation_advisor")

    # reputation_advisor → executor (Phase 4 PR-4: advisory only, always proceeds)
    workflow.add_edge("reputation_advisor", "executor")

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

    # finalizer → END
    workflow.add_edge("finalizer", END)

    memory = MemorySaver()

    app = workflow.compile(checkpointer=memory)

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
        "reputation_level": "trusted"
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

        return {
            "trace_id": trace_id,
            "pr_url": None,
            "ci_state": "error",
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
