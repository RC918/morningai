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

================================================================================
ORCHESTRATOR GRAPH NODE RESPONSIBILITIES (Issue #2265)
================================================================================

This section documents the responsibilities of each node in the orchestrator
graph, with special attention to the internal_review and reviewer nodes.

NODE RESPONSIBILITY MATRIX
--------------------------

| Node              | Responsibility                                    | Trigger Condition           |
|-------------------|---------------------------------------------------|----------------------------|
| planner           | Task decomposition and planning                   | All tasks                  |
| review_intake     | Process incoming review requests                  | Review follow-up tasks     |
| internal_review   | Validate AI reviewer assessments after fixes      | task_type=internal_review  |
| reviewer          | Perform code review (CI-based or LLM-based)       | PR available               |
| decision          | Make merge/fix decision based on review           | After reviewer             |
| executor          | Execute planned tasks                             | After planner              |
| fixer             | Auto-fix CI failures                              | CI failure detected        |
| finalizer         | Complete workflow and report results              | After decision             |

INTERNAL_REVIEW_NODE vs REVIEWER_NODE (Issue #2265)
---------------------------------------------------

These two nodes serve DIFFERENT purposes and are NOT redundant:

**internal_review_node** (Phase 7 - Issue #2212):
  - Purpose: Validate if AI reviewer's ORIGINAL assessment was correct
  - When: After follow-up actions are applied to address AI reviewer comments
  - Input: Original AI review, follow-up result, triage result, CI state
  - Output: internal_review_decision (approve/request_changes/escalate),
            ai_reviewer_agreement (agree/partial/disagree),
            requires_hitl_approval (bool)
  - Logic: Compares initial AI assessment with current state to determine
           if the fix correctly addressed the original comment

**reviewer_node** (Phase 3):
  - Purpose: Perform actual code review on PR changes
  - When: PR is available for review
  - Input: PR number, PR URL, CI state
  - Output: review_result, review_comments, review_severity, code_quality_score
  - Logic: Uses CI state as baseline, optionally LLM for additional analysis

INTERNAL_REVIEW → REVIEWER EDGE DESIGN RATIONALE
------------------------------------------------

The edge from internal_review to reviewer exists because:

1. **State Consistency**: After internal review validates the AI assessment,
   the reviewer node updates the review state (code_quality_score, severity)
   based on the current CI state. This ensures decision_node has accurate data.

2. **Separation of Concerns**:
   - internal_review_node: "Was the AI reviewer's assessment correct?"
   - reviewer_node: "What is the current code quality?"

3. **Reusability**: The reviewer_node logic is reused for both:
   - Standard PR review flow (planner → ... → reviewer → decision)
   - Internal review flow (internal_review → reviewer → decision)

4. **No Redundant Computation**: internal_review_node does NOT perform
   code review - it only validates the AI reviewer's assessment.
   reviewer_node does NOT validate AI assessments - it only reviews code.

GRAPH FLOWS
-----------

Standard PR Flow:
  planner → executor → reviewer → decision → (fixer) → finalizer → evaluation → END

Review Follow-up Flow (Issue #2211):
  review_intake → planner → executor → reviewer → decision → finalizer → evaluation → END

Internal Review Flow (Issue #2212):
  internal_review → reviewer → decision → finalizer → evaluation → END

Note: All flows end with evaluation_node which records metrics and learning data
before transitioning to END state.

================================================================================
"""

import functools
import logging
import time
from typing import TypedDict, Annotated, Sequence, Optional, Callable, Dict, Any
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
from webhooks.review_follow_up import determine_hitl_requirement
from tools.github_api import get_repo, get_pr_diff

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
        - PostgresSaver if USE_POSTGRES_CHECKPOINTER=true and DATABASE_URL is configured
        - RedisSaver if USE_REDIS_CHECKPOINTER=true and REDIS_URL is configured
        - MemorySaver as fallback (default)

    Configuration:
        - USE_POSTGRES_CHECKPOINTER: Enable PostgreSQL-based checkpointer (default: false)
        - DATABASE_URL: PostgreSQL connection URL (required for PostgreSQL checkpointer)
        - USE_REDIS_CHECKPOINTER: Enable Redis-based checkpointer (default: false)
        - REDIS_CHECKPOINTER_TTL: TTL in seconds for checkpoint entries (default: 86400)
        - REDIS_URL: Redis connection URL (required for Redis checkpointer)

    Note:
        PostgreSQL checkpointer is recommended over Redis for Upstash Redis,
        which doesn't support RediSearch (required by langgraph-checkpoint-redis).

    Fix (Dec 2025):
        PostgresSaver.from_conn_string() returns a context manager in langgraph-checkpoint-postgres>=2.0.0.
        We use psycopg.connect() directly with autocommit=True and row_factory=dict_row as required
        by the PostgresSaver implementation. This allows us to control the connection lifecycle
        and avoid the context manager issue.
    """
    import os

    use_postgres = settings.use_postgres_checkpointer
    database_url = settings.database_url or os.environ.get("DATABASE_URL")

    if use_postgres and database_url:
        conn = None
        try:
            import psycopg
            from psycopg.rows import dict_row
            from langgraph.checkpoint.postgres import PostgresSaver

            conn = psycopg.connect(database_url, autocommit=True, row_factory=dict_row)
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()

            logger.info(
                "Using PostgreSQL checkpointer for LangGraph state persistence",
                extra={
                    "operation": "get_checkpointer",
                    "checkpointer_type": "postgres",
                    "database_url_masked": database_url[:30] + "..." if len(database_url) > 30 else "[hidden]"
                }
            )

            return checkpointer

        except ImportError as e:
            logger.warning(
                f"langgraph-checkpoint-postgres or psycopg not installed, trying Redis checkpointer: {e}",
                extra={
                    "operation": "get_checkpointer",
                    "error": str(e)
                }
            )
        except Exception as e:
            if conn is not None:
                try:
                    conn.close()
                    logger.info(
                        "Closed PostgreSQL connection after setup failure",
                        extra={"operation": "get_checkpointer"}
                    )
                except Exception:
                    pass
            logger.error(
                f"Failed to initialize PostgreSQL checkpointer, trying Redis checkpointer: {e}",
                extra={
                    "operation": "get_checkpointer",
                    "error": str(e)
                }
            )

    use_redis = settings.use_redis_checkpointer
    redis_url = settings.redis_url or os.environ.get("REDIS_URL")

    if use_redis and redis_url:
        try:
            from langgraph.checkpoint.redis import RedisSaver

            ttl_seconds = settings.redis_checkpointer_ttl

            ttl_config = None
            if ttl_seconds and ttl_seconds > 0:
                ttl_minutes = ttl_seconds / 60
                ttl_config = {
                    "default_ttl": ttl_minutes,
                    "refresh_on_read": True
                }

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

    logger.info(
        "Using in-memory MemorySaver for LangGraph state persistence",
        extra={
            "operation": "get_checkpointer",
            "checkpointer_type": "memory",
            "use_postgres_configured": use_postgres,
            "database_url_available": bool(database_url),
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

    Phase 7 New Fields (Issue #2211 Review Follow-up Mode):
        task_type: Type of task (default, review_follow_up, internal_review)
        original_pr_number: Original PR number for review follow-up tasks
        comment_url: URL to the review comment being addressed
        comment_body: Body of the review comment
        review_file_path: File path mentioned in the review comment
        review_line_number: Line number mentioned in the review comment
        triage_result: Result from CommentTriageAgent
        pr_context: Context about the original PR (diff, files, comments)
        review_follow_up_action: Action to take (auto_fix, manual_review, skip, escalate)
        requires_hitl_approval: Whether HITL approval is required

    Phase 7 New Fields (Issue #2212 Internal Reviewer Agent Re-review):
        internal_review_mode: Boolean indicating if this is an internal re-review
        initial_ai_review: Initial AI reviewer assessment being re-reviewed
        follow_up_summary: Summary of follow-up actions taken
        internal_review_result: Result from internal re-review
        internal_review_decision: Decision (approve, request_changes, escalate)
        ai_reviewer_agreement: Agreement level (agree, partial, disagree)
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
    # Phase 7 Issue #2211 Review Follow-up Mode
    task_type: str
    original_pr_number: int
    comment_url: str
    comment_body: str
    review_file_path: str
    review_line_number: int
    triage_result: dict
    pr_context: dict
    review_follow_up_action: str
    requires_hitl_approval: bool
    # Phase 7 Issue #2212 Internal Reviewer Agent Re-review
    internal_review_mode: bool
    initial_ai_review: dict
    follow_up_summary: dict
    internal_review_result: dict
    internal_review_decision: str
    ai_reviewer_agreement: str


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


def review_intake_node(state: AgentState) -> AgentState:
    """
    Review Intake node: Entry point for review follow-up tasks.

    Issue #2211: Orchestrator Review Follow-up Mode

    This node:
    1. Validates the review follow-up task
    2. Fetches PR context (diff, files, comments)
    3. Determines if HITL approval is required
    4. Prepares state for the planner

    The node is used when task_type == "review_follow_up" to handle
    AI reviewer comments that need to be addressed.
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    task_type = state.get("task_type", "default")

    metrics.record_node_start("review_intake", trace_id)

    logger.info("[ReviewIntake] Processing review follow-up task", extra={
        "operation": "review_intake",
        "trace_id": trace_id,
        "task_type": task_type,
        "original_pr_number": state.get("original_pr_number"),
        "review_file_path": state.get("review_file_path"),
    })

    # Validate this is a review follow-up task
    if task_type != "review_follow_up":
        logger.warning(
            "[ReviewIntake] Not a review follow-up task, skipping",
            extra={"operation": "review_intake", "trace_id": trace_id}
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("review_intake", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Extract review context
    original_pr_number = state.get("original_pr_number", 0)
    repo = state.get("repo", "")
    comment_body = state.get("comment_body", "")
    review_file_path = state.get("review_file_path", "")
    review_line_number = state.get("review_line_number", 0)
    triage_result = state.get("triage_result", {})

    # Fetch PR context if not already present
    pr_context = state.get("pr_context", {})
    if not pr_context and original_pr_number > 0:
        try:
            pr_context = _fetch_pr_context_for_review(repo, original_pr_number, trace_id)
            state["pr_context"] = pr_context
            logger.info(
                "[ReviewIntake] Fetched PR context",
                extra={
                    "operation": "review_intake",
                    "trace_id": trace_id,
                    "pr_number": original_pr_number,
                    "files_count": len(pr_context.get("files_changed", [])),
                }
            )
        except Exception as e:
            logger.warning(
                f"[ReviewIntake] Failed to fetch PR context: {e}",
                extra={"operation": "review_intake", "trace_id": trace_id, "error": str(e)}
            )

    # Determine if HITL approval is required
    requires_approval = _determine_hitl_requirement(triage_result, review_file_path)
    state["requires_hitl_approval"] = requires_approval

    # Determine action based on triage result
    action = state.get("review_follow_up_action", "manual_review")
    if triage_result:
        if triage_result.get("should_auto_fix", False):
            action = "auto_fix"
        elif triage_result.get("risk_level") == "high":
            action = "escalate"
        elif triage_result.get("category") == "security":
            action = "escalate"
    state["review_follow_up_action"] = action

    # Build enhanced goal text for review follow-up
    enhanced_goal = _build_review_follow_up_goal(
        comment_body, review_file_path, review_line_number, triage_result, pr_context
    )
    state["goal"] = enhanced_goal

    # Add message about review intake
    state["messages"] = state.get("messages", []) + [
        SystemMessage(content=f"[ReviewIntake] Processing review comment on PR #{original_pr_number}: {comment_body[:100]}...")
    ]

    logger.info(
        "[ReviewIntake] Review intake complete",
        extra={
            "operation": "review_intake",
            "trace_id": trace_id,
            "action": action,
            "requires_approval": requires_approval,
        }
    )

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("review_intake", trace_id, success=True, latency_ms=latency_ms)
    metrics.record_transition("review_intake", "planner", trace_id)

    return state


def internal_review_node(state: AgentState) -> AgentState:
    """
    Internal Review node: Entry point for internal re-review tasks.

    Issue #2212: Internal Reviewer Agent Re-review Mechanism
    Issue #2265: Node responsibility documentation

    PURPOSE (see module docstring for full details):
    Validate if the AI reviewer's ORIGINAL assessment was correct after
    follow-up actions have been applied. This is NOT a code review node -
    it validates the AI reviewer's judgment, not the code itself.

    RESPONSIBILITIES:
    1. Validates the internal re-review task (task_type == "internal_review")
    2. Loads context (original review, triage result, follow-up actions, CI state)
    3. Performs internal re-review using InternalReviewerService
    4. Determines agreement level (agree/partial/disagree) with original AI review
    5. Determines if HITL approval is required for high-risk decisions
    6. Prepares state for decision making

    OUTPUTS:
    - internal_review_decision: "approve" | "request_changes" | "escalate"
    - ai_reviewer_agreement: "agree" | "partial" | "disagree"
    - requires_hitl_approval: bool
    - internal_review_result: dict with detailed assessment

    NEXT NODE: reviewer_node (to update code quality state before decision)

    NOTE: This node is DIFFERENT from reviewer_node:
    - internal_review_node: "Was the AI reviewer's assessment correct?"
    - reviewer_node: "What is the current code quality?"
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    task_type = state.get("task_type", "default")

    metrics.record_node_start("internal_review", trace_id)

    logger.info("[InternalReview] Processing internal re-review task", extra={
        "operation": "internal_review",
        "trace_id": trace_id,
        "task_type": task_type,
        "original_pr_number": state.get("original_pr_number"),
        "internal_review_mode": state.get("internal_review_mode", False),
    })

    if task_type != "internal_review":
        logger.warning(
            "[InternalReview] Not an internal review task, skipping",
            extra={"operation": "internal_review", "trace_id": trace_id}
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("internal_review", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Issue #2263: Validate required fields before processing
    required_fields = ["original_pr_number", "repo"]
    missing_fields = [f for f in required_fields if not state.get(f)]

    if missing_fields:
        logger.error(
            f"[InternalReview] Missing required fields: {missing_fields}",
            extra={
                "operation": "internal_review",
                "trace_id": trace_id,
                "missing_fields": missing_fields,
            }
        )
        state["internal_review_mode"] = True
        state["internal_review_decision"] = "escalate"
        state["internal_review_error"] = f"Missing required fields: {missing_fields}"
        state["internal_review_result"] = {
            "status": "failed",
            "error": f"Missing required fields: {missing_fields}",
        }
        state["ai_reviewer_agreement"] = "disagree"
        state["requires_hitl_approval"] = True

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("internal_review", trace_id, success=False, latency_ms=latency_ms)
        return state

    state["internal_review_mode"] = True

    original_pr_number = state.get("original_pr_number", 0)
    repo = state.get("repo", "")
    comment_body = state.get("comment_body", "")
    review_file_path = state.get("review_file_path", "")
    review_line_number = state.get("review_line_number", 0)
    triage_result = state.get("triage_result", {})
    initial_ai_review = state.get("initial_ai_review", {})
    follow_up_summary = state.get("follow_up_summary", {})
    ci_state = state.get("ci_state", "unknown")
    code_quality_score = state.get("code_quality_score", 100)

    try:
        from webhooks.internal_reviewer import (
            InternalReviewerService,
            create_internal_review_task,
        )

        service = InternalReviewerService()

        task = create_internal_review_task(
            trace_id=trace_id,
            original_pr_number=original_pr_number,
            repo=repo,
            initial_ai_review=initial_ai_review,
            follow_up_result=follow_up_summary,
            triage_result=triage_result,
            comment_body=comment_body,
            file_path=review_file_path,
            line_number=review_line_number,
            ci_state=ci_state,
            code_quality_score=code_quality_score,
        )

        result = service.perform_internal_review(task)

        state["internal_review_result"] = {
            "task_id": result.task_id,
            "status": result.status.value,
            "action": result.action.value,
            "agreement": result.agreement.value,
            "comment_addressed": result.comment_addressed,
            "addressing_quality": result.addressing_quality,
            "quality_score_delta": result.quality_score_delta,
            "severity_assessment": result.severity_assessment,
            "regression_risk": result.regression_risk,
            "summary": result.summary,
            "recommendations": result.recommendations,
            "review_time_ms": result.review_time_ms,
        }
        state["internal_review_decision"] = result.action.value
        state["ai_reviewer_agreement"] = result.agreement.value
        state["requires_hitl_approval"] = result.requires_hitl

        logger.info(
            "[InternalReview] Internal re-review completed",
            extra={
                "operation": "internal_review",
                "trace_id": trace_id,
                "action": result.action.value,
                "agreement": result.agreement.value,
                "requires_hitl": result.requires_hitl,
                "review_time_ms": result.review_time_ms,
            }
        )

        state["messages"] = state.get("messages", []) + [
            SystemMessage(content=f"[InternalReview] Re-review completed: {result.summary}")
        ]

    except ImportError as e:
        logger.warning(
            f"[InternalReview] InternalReviewerService not available: {e}",
            extra={"operation": "internal_review", "trace_id": trace_id}
        )
        state["internal_review_result"] = {
            "status": "skipped",
            "reason": "InternalReviewerService not available",
        }
        state["internal_review_decision"] = "request_changes"
        state["ai_reviewer_agreement"] = "partial"

    except Exception as e:
        logger.error(
            f"[InternalReview] Internal re-review failed: {e}",
            extra={"operation": "internal_review", "trace_id": trace_id, "error": str(e)},
            exc_info=True
        )
        state["internal_review_result"] = {
            "status": "failed",
            "error": str(e),
        }
        state["internal_review_decision"] = "escalate"
        state["ai_reviewer_agreement"] = "disagree"
        state["requires_hitl_approval"] = True

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("internal_review", trace_id, success=True, latency_ms=latency_ms)
    metrics.record_transition("internal_review", "reviewer", trace_id)

    return state


def _fetch_pr_context_for_review(repo: str, pr_number: int, trace_id: str) -> dict:
    """
    Fetch PR context for review follow-up.

    Issue #2211: Pulls diff, files, and comments from the PR.

    Args:
        repo: Repository in owner/repo format
        pr_number: PR number
        trace_id: Trace ID for logging

    Returns:
        Dictionary with PR context
    """
    try:
        from tools.github_api import get_repo as get_github_repo

        logger.debug(
            "[ReviewIntake] Fetching PR context",
            extra={"operation": "fetch_pr_context", "trace_id": trace_id, "pr_number": pr_number}
        )

        github_repo = get_github_repo(repo)
        pr = github_repo.get_pull(pr_number)

        # Get changed files
        files_changed = [f.filename for f in pr.get_files()]

        # Build context
        return {
            "pr_number": pr_number,
            "repo": repo,
            "branch": pr.head.ref,
            "base_branch": pr.base.ref,
            "title": pr.title,
            "description": pr.body or "",
            "author": pr.user.login,
            "files_changed": files_changed,
            "labels": [label.name for label in pr.labels],
            "state": pr.state,
            "mergeable": pr.mergeable,
        }

    except ImportError:
        logger.warning("[ReviewIntake] GitHub API not available, using stub context")
        return {
            "pr_number": pr_number,
            "repo": repo,
            "branch": "unknown",
            "base_branch": "main",
            "title": f"PR #{pr_number}",
            "description": "",
            "author": "unknown",
            "files_changed": [],
            "labels": [],
            "state": "unknown",
            "mergeable": None,
            "stub": True,
        }

    except Exception as e:
        logger.error(f"[ReviewIntake] Error fetching PR context: {e}")
        raise


def _determine_hitl_requirement(triage_result: dict, file_path: str) -> bool:
    """
    Determine if HITL (Human-in-the-Loop) approval is required.

    Issue #2258: Delegates to unified determine_hitl_requirement() function
    in webhooks.review_follow_up module.

    Args:
        triage_result: Result from CommentTriageAgent
        file_path: File path being modified

    Returns:
        True if HITL approval is required
    """
    return determine_hitl_requirement(
        triage_result=triage_result,
        file_path=file_path,
    )


def _build_review_follow_up_goal(
    comment_body: str,
    file_path: str,
    line_number: int,
    triage_result: dict,
    pr_context: dict,
) -> str:
    """
    Build an enhanced goal text for review follow-up tasks.

    Issue #2211: Creates a detailed goal for the planner.

    Args:
        comment_body: Body of the review comment
        file_path: File path mentioned in comment
        line_number: Line number mentioned in comment
        triage_result: Result from CommentTriageAgent
        pr_context: Context about the PR

    Returns:
        Enhanced goal text
    """
    parts = []

    # Add task type prefix
    category = triage_result.get("category", "unknown")
    parts.append(f"[Review Follow-up: {category}]")

    # Add file context
    if file_path:
        if line_number > 0:
            parts.append(f"In file {file_path} at line {line_number}:")
        else:
            parts.append(f"In file {file_path}:")

    # Add the comment (truncated if too long)
    comment = comment_body[:500] if comment_body else "No comment body"
    parts.append(f"Address review comment: {comment}")

    # Add PR context
    pr_number = pr_context.get("pr_number", 0)
    repo = pr_context.get("repo", "")
    branch = pr_context.get("branch", "")
    if pr_number:
        parts.append(f"(PR #{pr_number} on branch '{branch}' in {repo})")

    # Add action hint based on triage
    if triage_result.get("should_auto_fix"):
        parts.append("[Auto-fix recommended]")
    elif triage_result.get("risk_level") == "high":
        parts.append("[High risk - manual review required]")

    return " ".join(parts)


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

        # Resolve agent_type to UUID for DB operations
        # Use 'ops_agent' as the canonical agent_type for orchestrator operations
        # Valid agent_types: ops_agent, dev_agent, pm_agent, growth_strategist, meta_agent
        agent_uuid = None
        if agent.reputation_engine:
            agent_uuid = agent.reputation_engine.resolve_agent_uuid("ops_agent")

        # Fail-open: skip DB operations if UUID resolution fails
        if agent_uuid:
            advisory = agent.analyze_task(
                task_type=task_type,
                trace_id=trace_id,
                agent_id=agent_uuid,
                file_paths=[],
                operations=plan,
                content=goal,
                labels=[],
                environment="sandbox"
            )
            advisory_dict = advisory.to_dict()
        else:
            # UUID resolution failed - use safe defaults without DB operations
            logger.warning("[GovernanceAdvisor] Could not resolve agent UUID, using defaults", extra={
                "operation": "governance_advisor",
                "trace_id": trace_id
            })
            from governance_agent.agent import GovernanceRisk
            advisory_dict = {
                "is_compliant": True,
                "overall_risk": GovernanceRisk.INFO.value,
                "findings": [],
                "summary": "Governance check skipped: agent UUID could not be resolved"
            }
        state["governance_advisory"] = advisory_dict
        state["governance_risk"] = advisory_dict["overall_risk"]
        state["governance_findings"] = advisory_dict["findings"]
        state["governance_is_compliant"] = advisory_dict["is_compliant"]

        logger.info("[GovernanceAdvisor] Analysis complete", extra={
            "operation": "governance_advisor",
            "trace_id": trace_id,
            "is_compliant": advisory_dict["is_compliant"],
            "risk_level": advisory_dict["overall_risk"],
            "findings_count": len(advisory_dict["findings"])
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Governance analysis: risk={advisory_dict['overall_risk']}, findings={len(advisory_dict['findings'])}, compliant={advisory_dict['is_compliant']}")
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

        # Resolve agent_type to UUID for DB operations
        # Use 'ops_agent' as fallback - must be a valid agent_type from DB constraint
        # Valid agent_types: ops_agent, dev_agent, pm_agent, growth_strategist, meta_agent
        agent_identifier = state.get("agent_id", "ops_agent")
        agent_uuid = None
        if agent.reputation_engine:
            agent_uuid = agent.reputation_engine.resolve_agent_uuid(agent_identifier)

        # Fail-open: skip DB operations if UUID resolution fails
        if agent_uuid:
            advisory = agent.analyze_permissions(
                agent_id=agent_uuid,
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
        else:
            # UUID resolution failed - use safe defaults without DB operations (fail-open)
            logger.warning("[PermissionAdvisor] Could not resolve agent UUID, using defaults", extra={
                "operation": "permission_advisor",
                "trace_id": trace_id,
                "agent_identifier": agent_identifier
            })
            from governance_agent.agent import GovernanceRisk
            state["permission_advisory"] = {
                "is_compliant": True,
                "overall_risk": GovernanceRisk.INFO.value,
                "findings": [],
                "summary": "Permission check skipped: agent UUID could not be resolved"
            }
            state["permission_risk"] = GovernanceRisk.INFO.value
            state["permission_granted"] = True
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="Permission analysis skipped (agent UUID could not be resolved)")
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

        # Resolve agent_type to UUID for DB operations
        # Use 'ops_agent' as the canonical agent_type for orchestrator operations
        # Valid agent_types: ops_agent, dev_agent, pm_agent, growth_strategist, meta_agent
        agent_uuid = None
        if agent.reputation_engine:
            agent_uuid = agent.reputation_engine.resolve_agent_uuid("ops_agent")

        reputation_data = {
            "agent_id": agent_uuid,  # Allow None for data consistency
            "score": 100,
            "level": "trusted",
            "history": []
        }

        if agent.reputation_engine and agent_uuid:
            try:
                reputation_data = agent.reputation_engine.get_reputation(agent_uuid) or reputation_data
            except Exception as e:
                logger.warning(f"[ReputationAdvisor] ReputationEngine query failed: {e}")
        elif not agent_uuid:
            logger.warning("[ReputationAdvisor] Could not resolve agent UUID, using defaults", extra={
                "operation": "reputation_advisor",
                "trace_id": trace_id
            })

        score = reputation_data.get("score", 100)
        level = reputation_data.get("level", "trusted")

        state["reputation_advisory"] = {
            "agent_id": reputation_data.get("agent_id", agent_uuid),  # Allow None for data consistency
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

    # Note: We don't check for GitHub token here - instead we rely on exception handling
    # below to catch GitHubAuthenticationError when the token is missing/invalid.
    # This allows tests to patch github_api.get_repo/get_pr_checks and still exercise
    # the success/error paths.

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
    Reviewer node: Analyzes code changes and provides review feedback.

    Phase 6 PR-3 Enhancement
    Issue #2265: Node responsibility documentation

    PURPOSE (see module docstring for full details):
    Perform actual code review on PR changes. This node evaluates the
    CURRENT code quality, not the AI reviewer's judgment.

    RESPONSIBILITIES:
    1. Analyze code changes in the PR
    2. Use CI state as baseline quality indicator
    3. Optionally use LLM for additional risk assessment (A/B testing)
    4. Generate review comments and severity assessment
    5. Calculate code quality score

    OUTPUTS:
    - review_result: Dict[str, str] with keys:
        - status: "passed" | "needs_attention" | "pending"
        - reason: Human-readable explanation of the review outcome
    - review_comments: List[Dict] with each comment containing:
        - severity: "low" | "medium" | "high" | "critical"
        - message: Description of the issue found
    - review_severity: "none" | "low" | "medium" | "high" | "critical"
        - Aggregate severity based on CI state and LLM analysis
    - code_quality_score: int (0-100)
        - 80+ for CI success, 40 for CI failure, 60 for pending

    NEXT NODE: decision_node

    NOTE: This node is DIFFERENT from internal_review_node:
    - reviewer_node: "What is the current code quality?"
    - internal_review_node: "Was the AI reviewer's assessment correct?"

    Feature Flag: USE_LLM_REVIEWER (default: False)
    - LLM-powered code review with A/B testing support (OpenAI vs Gemini)
    - CI score acts as ceiling (LLM cannot claim higher quality than CI)
    - Graceful fallback to CI-only review if LLM unavailable

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

                # EPIC B Phase B-1: Fetch PR diff for diff-aware review
                diff_data = None
                diff_content = None
                diff_truncated = False
                diff_files = None
                # Phase 2: Capture head_sha for line drift protection
                diff_head_sha = None

                if pr_number:
                    try:
                        github_repo = get_repo()
                        if github_repo:
                            diff_data = get_pr_diff(github_repo, pr_number)
                            if diff_data and not diff_data.get("error"):
                                diff_content = diff_data.get("diff", "")
                                diff_truncated = diff_data.get("truncated", False)
                                diff_files = diff_data.get("files", [])
                                # Phase 2: Capture head_sha for line drift protection
                                diff_head_sha = diff_data.get("head_sha")
                                # Phase B-B: Extract truncation_info for metrics
                                truncation_info = diff_data.get("truncation_info", {})
                                github_total_files = truncation_info.get(
                                    "original_file_count", 0
                                )
                                included_file_count = truncation_info.get(
                                    "included_file_count", 0
                                )
                                original_line_count = truncation_info.get(
                                    "original_line_count", 0
                                )
                                included_line_count = truncation_info.get(
                                    "included_line_count", 0
                                )
                                # Phase B-B C-lite: Check if lockfile-only PR
                                # Fix: More robust detection to avoid false positives
                                # when included_file_count == 0 due to truncation
                                ignored_file_count = truncation_info.get(
                                    "ignored_file_count", 0
                                )
                                lockfile_only = (
                                    included_file_count == 0 and
                                    ignored_file_count > 0 and
                                    github_total_files == ignored_file_count
                                )

                                # Phase B-B C-lite: Record diff fetch metrics
                                metrics.record_diff_fetch(
                                    trace_id=trace_id,
                                    success=True,
                                    truncated=diff_truncated,
                                    original_files=github_total_files,
                                    included_files=included_file_count,
                                    original_lines=original_line_count,
                                    included_lines=included_line_count,
                                    lockfile_only=lockfile_only
                                )

                                logger.info(
                                    "[Reviewer] Retrieved PR diff for review",
                                    extra={
                                        "operation": "reviewer",
                                        "trace_id": trace_id,
                                        "pr_number": pr_number,
                                        "diff_file_count": len(diff_files) if diff_files else 0,
                                        "diff_truncated": diff_truncated,
                                        # Phase B-B Telemetry: GitHub's total changed files
                                        "github_total_files": github_total_files
                                    }
                                )
                            else:
                                # Phase B-B C-lite: Record diff fetch failure
                                metrics.record_diff_fetch(
                                    trace_id=trace_id,
                                    success=False
                                )
                                logger.warning(
                                    f"[Reviewer] Failed to get PR diff: {diff_data.get('error', 'unknown')}",
                                    extra={
                                        "operation": "reviewer",
                                        "trace_id": trace_id,
                                        "pr_number": pr_number
                                    }
                                )
                    except Exception as diff_error:
                        # Phase B-B C-lite: Record diff fetch failure on exception
                        metrics.record_diff_fetch(
                            trace_id=trace_id,
                            success=False
                        )
                        logger.warning(
                            f"[Reviewer] Error fetching PR diff: {diff_error}",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "error": str(diff_error)
                            }
                        )

                llm_review = generate_llm_review(
                    pr_number=pr_number,
                    pr_url=pr_url,
                    ci_state=ci_state,
                    goal=goal,
                    repo=repo,
                    trace_id=trace_id,
                    base_quality_score=ci_review["code_quality_score"],
                    base_severity=ci_review["review_severity"],
                    diff=diff_content,
                    diff_truncated=diff_truncated,
                    diff_files=diff_files
                )

                if llm_review.get("llm_used", False):
                    llm_used = True
                    llm_provider = llm_review.get("provider")

                    state["code_quality_score"] = llm_review["quality_score"]
                    state["review_severity"] = llm_review["severity"]

                    if llm_review.get("comments"):
                        # Phase B-B Telemetry: raw_comment_count before normalization
                        raw_llm_comments = llm_review["comments"]
                        raw_comment_count = len(raw_llm_comments)

                        # Phase B-3.1: Normalize LLM comments using canonical schema
                        # This ensures start_line/end_line are properly set
                        from review_comment_schema import normalize_review_comments
                        normalized_llm_comments = normalize_review_comments(
                            raw_llm_comments, source="llm"
                        )
                        normalized_comment_count = len(normalized_llm_comments)

                        # Phase B-B C-lite: Record schema validation metrics
                        metrics.record_schema_validation(
                            trace_id=trace_id,
                            raw_count=raw_comment_count,
                            normalized_count=normalized_comment_count,
                            llm_api_failed=False
                        )

                        # Phase B-B Telemetry: Log schema pass rate metrics
                        logger.info(
                            "[Reviewer] LLM comments normalized",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "raw_comment_count": raw_comment_count,
                                "normalized_comment_count": normalized_comment_count,
                                "schema_filtered_count": raw_comment_count - normalized_comment_count
                            }
                        )

                        state["review_comments"] = (
                            state["review_comments"] + normalized_llm_comments
                        )
                    else:
                        # Phase B-B C-lite: Record empty LLM output
                        metrics.record_schema_validation(
                            trace_id=trace_id,
                            raw_count=0,
                            normalized_count=0,
                            llm_api_failed=False
                        )

                    # Phase B-3.1: Store diff content in state for publisher validation
                    # This allows publisher_node to validate inline comments against
                    # the actual diff that was shown to the LLM
                    # Phase 3: Sanitize diff before storing to prevent secrets exposure
                    # via LangGraph checkpointer persistence (PostgreSQL/Redis)
                    if diff_content:
                        from llm_reviewer_adapter import sanitize_diff_content
                        sanitized_diff, redaction_count = sanitize_diff_content(diff_content)
                        if redaction_count > 0:
                            logger.info("[Reviewer] Sanitized diff before state storage", extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "redaction_count": redaction_count
                            })
                        state["diff_content"] = sanitized_diff
                        state["diff_truncated"] = diff_truncated
                        # Phase 2: Store head_sha for line drift protection
                        # publisher_node will compare this with current head_sha
                        if diff_head_sha:
                            state["diff_head_sha"] = diff_head_sha

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
                    # Phase 1 Quick Win: Distinguish fallback reasons in logs
                    fallback_reason = llm_review.get("fallback_reason", "llm_unavailable")
                    logger.info(f"[Reviewer] LLM fallback ({fallback_reason}), using CI-only review", extra={
                        "operation": "reviewer",
                        "trace_id": trace_id,
                        "fallback_reason": fallback_reason
                    })

            except Exception as llm_error:
                # Phase B-B C-lite: Record LLM API failure (excluded from schema KPI)
                metrics.record_schema_validation(
                    trace_id=trace_id,
                    raw_count=0,
                    normalized_count=0,
                    llm_api_failed=True
                )
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


def _build_file_level_appendix(
    file_level_comments: list,
    line_drift_detected: bool = False,
    max_comments: int = 10
) -> str:
    """
    Build markdown appendix for file-level comments.

    EPIC B Phase 3 P2: Unified file-level delivery logic
    This helper ensures consistent formatting across all file-level delivery paths.

    Args:
        file_level_comments: List of file-level comment dicts
        line_drift_detected: Whether line drift was detected (adds note)
        max_comments: Maximum comments to include (default: 10)

    Returns:
        Markdown string for file-level comments appendix
    """
    if not file_level_comments:
        return ""

    appendix = ""
    if line_drift_detected:
        appendix += "\n\n*Note: New commits detected since review. Comments delivered as file-level for safety.*"

    appendix += "\n\n### File-Level Comments\n\n"

    # Limit comments to prevent overly long review bodies
    comments_to_show = file_level_comments[:max_comments]
    truncated_count = len(file_level_comments) - len(comments_to_show)

    for comment in comments_to_show:
        file_path = comment.get("file", "General")
        message = comment.get("message", "")
        severity = comment.get("severity", "info")
        appendix += f"**{file_path}** ({severity})\n{message}\n\n"

    if truncated_count > 0:
        appendix += f"*...and {truncated_count} more file-level comments (truncated)*\n\n"

    return appendix


def publisher_node(state: AgentState) -> AgentState:
    """
    Publisher node: Posts review comments to GitHub as inline PR review.

    EPIC B Phase B-3: GitHub Inline Comment Posting
    Issue #2595: Diff-Aware Review Plumbing

    PURPOSE:
    Batch and atomically post review comments to GitHub PR as inline review.
    This node is placed between decision and finalizer to ensure:
    1. All comments are collected before posting (batching)
    2. Single notification to PR author (atomicity)
    3. Proper separation of concerns (reviewer generates, publisher posts)

    FEATURE FLAGS:
    - ENABLE_GITHUB_REVIEW_POSTING: Master switch (default: False)
    - GITHUB_REVIEW_POSTING_DRY_RUN: Log-only mode (default: True)
    - GITHUB_REVIEW_POSTING_MAX_COMMENTS: Limit per review (default: 10)

    INPUTS:
    - review_comments: List[Dict] from reviewer_node
    - pr_number: PR number to post to

    OUTPUTS:
    - publish_result: Dict with posting status and counts

    NEXT NODE: finalizer_node
    """
    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")
    pr_number = state.get("pr_number")
    review_comments = state.get("review_comments", [])

    metrics.record_node_start("publisher", trace_id)

    # Initialize publish result
    state["publish_result"] = {
        "attempted": False,
        "success": False,
        "posted_count": 0,
        "skipped_count": 0,
        "truncated_count": 0,
        "dry_run": False,
        "error": None
    }

    # Short-circuit: Skip entirely if feature is disabled (pure no-op)
    # This avoids calling get_repo() or any GitHub API when feature is off
    if not settings.enable_github_review_posting:
        # Phase B-B C-lite: Record feature disabled (excluded from KPI)
        metrics.record_inline_comment_result(
            trace_id=trace_id,
            eligible_count=0,
            validated_count=0,
            downgraded_count=0,
            posted_count=0,
            feature_disabled=True
        )
        logger.info("[Publisher] Feature disabled, skipping", extra={
            "operation": "publisher",
            "trace_id": trace_id
        })
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("publisher", trace_id, success=True, latency_ms=latency_ms)
        return state

    logger.info("[Publisher] Starting review publishing", extra={
        "operation": "publisher",
        "trace_id": trace_id,
        "pr_number": pr_number,
        "comment_count": len(review_comments)
    })

    # Skip if no PR or no comments
    if not pr_number:
        logger.info("[Publisher] No PR number, skipping publish", extra={
            "operation": "publisher",
            "trace_id": trace_id
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="No PR available for review publishing, skipping")
        ]
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("publisher", trace_id, success=True, latency_ms=latency_ms)
        return state

    if not review_comments:
        logger.info("[Publisher] No review comments to publish", extra={
            "operation": "publisher",
            "trace_id": trace_id,
            "pr_number": pr_number
        })
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="No review comments to publish")
        ]
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("publisher", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Fix: Initialize variables before any code that might raise exceptions
    # This prevents UnboundLocalError in the exception handler
    inline_eligible_count = 0
    inline_comments = []
    downgraded_count = 0

    # Filter comments that can be posted as inline (have file and line info)
    from review_comment_schema import (
        is_inline_comment,
        parse_diff_allowed_lines,
        validate_inline_comments
    )

    inline_comments = [c for c in review_comments if is_inline_comment(c)]
    file_level_comments = [c for c in review_comments if not is_inline_comment(c)]

    # Phase B-B Telemetry: inline_eligible_count before validation
    inline_eligible_count = len(inline_comments)

    logger.info("[Publisher] Filtered comments for inline posting", extra={
        "operation": "publisher",
        "trace_id": trace_id,
        "total_comments": len(review_comments),
        "inline_comments": len(inline_comments),
        "inline_eligible_count": inline_eligible_count,
        "file_level_comments": len(file_level_comments)
    })

    # Phase B-3.1: Validate inline comments against diff
    # This prevents 422 errors from GitHub when line numbers are invalid
    diff_content = state.get("diff_content")
    diff_truncated = state.get("diff_truncated", False)
    # Phase 2: Get stored head_sha for line drift protection
    stored_head_sha = state.get("diff_head_sha")
    downgraded_count = 0
    line_drift_detected = False

    if diff_content and inline_comments:
        allowed_lines_map = parse_diff_allowed_lines(diff_content)

        # Use strict mode for truncated diffs (safer)
        # Phase B-B: validate_inline_comments now returns downgrade_reasons
        valid_inline, invalid_inline, downgrade_reasons = validate_inline_comments(
            inline_comments,
            allowed_lines_map,
            strict_truncated=diff_truncated
        )

        downgraded_count = len(invalid_inline)
        if downgraded_count > 0:
            # Phase B-B Telemetry: Log downgrade reasons breakdown
            logger.warning(
                f"[Publisher] Downgraded {downgraded_count} comments due to "
                f"line validation failures",
                extra={
                    "operation": "publisher",
                    "trace_id": trace_id,
                    "downgraded_count": downgraded_count,
                    "diff_truncated": diff_truncated,
                    # Phase B-B Telemetry: Downgrade reason bucketing
                    "downgrade_file_not_in_diff": downgrade_reasons.get(
                        "file_not_in_diff", 0
                    ),
                    "downgrade_line_not_in_diff": downgrade_reasons.get(
                        "line_not_in_diff", 0
                    ),
                    "downgrade_missing_end_line": downgrade_reasons.get(
                        "missing_end_line", 0
                    ),
                    "downgrade_strict_truncated": downgrade_reasons.get(
                        "strict_truncated", 0
                    ),
                    "downgrade_other": downgrade_reasons.get("other", 0)
                }
            )
            # Move invalid inline comments to file-level
            file_level_comments.extend(invalid_inline)
            inline_comments = valid_inline

        state["publish_result"]["validation_downgraded"] = downgraded_count
        # Phase B-B Telemetry: Store downgrade reasons in state
        state["publish_result"]["downgrade_reasons"] = downgrade_reasons

    # Phase 2: Line drift protection - check if PR head has changed since review
    # MUST run before any comment posting to detect drift early
    # If head_sha changed, new commits were pushed and line numbers may be stale
    if stored_head_sha and pr_number and inline_comments:
        try:
            from tools.github_api import get_repo
            repo = get_repo()
            if repo:
                pr = repo.get_pull(pr_number)
                current_head_sha = pr.head.sha
                if current_head_sha != stored_head_sha:
                    line_drift_detected = True
                    logger.warning(
                        "[Publisher] Line drift detected - PR head changed since review",
                        extra={
                            "operation": "publisher",
                            "trace_id": trace_id,
                            "pr_number": pr_number,
                            "stored_head_sha": stored_head_sha[:8],
                            "current_head_sha": current_head_sha[:8],
                            "inline_comment_count": len(inline_comments)
                        }
                    )
                    # Conservative strategy: downgrade all inline comments to file-level
                    # This prevents 422 errors from stale line numbers
                    drift_downgrade_count = len(inline_comments)
                    file_level_comments.extend(inline_comments)
                    inline_comments = []
                    state["publish_result"]["line_drift_detected"] = True
                    # Store only drift-related downgrades (separate from validation downgrades)
                    state["publish_result"]["line_drift_downgraded"] = drift_downgrade_count
                    # P2 Follow-up: Record metrics for drift downgrade path
                    # This ensures inline comment delivery metrics are captured even when drift occurs
                    # Metrics semantics:
                    # - eligible_count: original inline-eligible before validation (funnel start)
                    # - validated_count: comments that passed validation (drift_downgrade_count)
                    # - downgraded_count: total downgrades (validation + drift)
                    # - posted_count: 0 (no inline comments posted due to drift)
                    metrics.record_inline_comment_result(
                        trace_id=trace_id,
                        eligible_count=inline_eligible_count,  # Original eligible before validation
                        validated_count=drift_downgrade_count,  # Validated comments at drift time
                        downgraded_count=downgraded_count + drift_downgrade_count,  # Total: validation + drift
                        posted_count=0,  # No inline comments posted due to drift
                        post_failed=False,
                        fallback_used=True,  # Comments delivered via file-level fallback
                        dry_run=settings.github_review_posting_dry_run,
                        feature_disabled=False
                    )
        except Exception as drift_check_error:
            # Fail-open: if we can't check head_sha, proceed with posting
            logger.warning(
                f"[Publisher] Failed to check line drift: {drift_check_error}",
                extra={
                    "operation": "publisher",
                    "trace_id": trace_id,
                    "error": str(drift_check_error)
                }
            )

    # Unified file-level delivery path
    # Handles: (1) no inline comments after validation, (2) all comments downgraded due to drift
    if not inline_comments:
        if file_level_comments and pr_number:
            logger.info("[Publisher] No inline-eligible comments, publishing file-level in review body", extra={
                "operation": "publisher",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "file_level_count": len(file_level_comments),
                "line_drift_detected": line_drift_detected
            })
            try:
                from tools.github_api import get_repo, post_pr_review

                # EPIC B Phase 3 P2: Use unified helper for file-level appendix
                file_level_body = "## MorningAI Code Review"
                file_level_body += _build_file_level_appendix(
                    file_level_comments,
                    line_drift_detected=line_drift_detected
                )

                repo = get_repo()
                result = post_pr_review(
                    repo=repo,
                    pr_number=pr_number,
                    comments=[],
                    summary=file_level_body
                )

                state["publish_result"]["success"] = result.get("success", False)
                state["publish_result"]["posted_count"] = 0
                state["publish_result"]["file_level_in_body"] = len(file_level_comments)
                state["publish_result"]["dry_run"] = result.get("dry_run", False)

                if result.get("success"):
                    mode = "[DRY-RUN]" if result.get("dry_run") else ""
                    drift_note = "[LINE-DRIFT]" if line_drift_detected else ""
                    state["messages"] = state.get("messages", []) + [
                        AIMessage(content=f"Review published {mode}{drift_note}: {len(file_level_comments)} file-level comments in review body")
                    ]
                    logger.info("[Publisher] File-level comments published in review body", extra={
                        "operation": "publisher",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "file_level_count": len(file_level_comments),
                        "line_drift_detected": line_drift_detected,
                        "dry_run": result.get("dry_run", False)
                    })
            except Exception as e:
                logger.warning(f"[Publisher] Failed to publish file-level comments: {e}", extra={
                    "operation": "publisher",
                    "trace_id": trace_id,
                    "error": str(e)
                })
                state["publish_result"]["error"] = str(e)
        else:
            logger.info("[Publisher] No comments to publish", extra={
                "operation": "publisher",
                "trace_id": trace_id,
                "pr_number": pr_number
            })
            state["publish_result"]["skipped_count"] = len(file_level_comments)
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="No comments to publish")
            ]

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("publisher", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Post inline comments to GitHub
    state["publish_result"]["attempted"] = True

    try:
        from tools.github_api import get_repo, post_pr_review

        repo = get_repo()

        # EPIC B Phase 3 P2: Build summary with file-level comments appendix
        # This ensures file-level comments are delivered even when inline comments exist
        review_summary = "## MorningAI Code Review"
        if file_level_comments:
            review_summary += _build_file_level_appendix(file_level_comments)

        # Phase 3 P2: Pass commit_id to pin review to specific commit
        # This prevents 422 errors from race conditions where new commits
        # are pushed between diff generation and review posting
        result = post_pr_review(
            repo=repo,
            pr_number=pr_number,
            comments=inline_comments,
            summary=review_summary,
            commit_id=stored_head_sha
        )

        state["publish_result"]["success"] = result.get("success", False)
        state["publish_result"]["posted_count"] = result.get("posted_count", 0)
        # EPIC B Phase 3 P2: file_level_comments are now delivered in body, not skipped
        state["publish_result"]["file_level_in_body"] = len(file_level_comments)
        state["publish_result"]["skipped_count"] = result.get("skipped_count", 0)
        state["publish_result"]["truncated_count"] = result.get("truncated_count", 0)
        state["publish_result"]["dry_run"] = result.get("dry_run", False)
        state["publish_result"]["downgraded"] = result.get("downgraded", False)
        state["publish_result"]["error"] = result.get("error")

        # Phase B-B C-lite: Record inline comment result metrics
        is_dry_run = result.get("dry_run", False)
        is_fallback = result.get("downgraded", False)
        posted_count = result.get("posted_count", 0)

        metrics.record_inline_comment_result(
            trace_id=trace_id,
            eligible_count=inline_eligible_count,
            validated_count=len(inline_comments),
            downgraded_count=downgraded_count,
            posted_count=posted_count,
            post_failed=not result.get("success", False),
            fallback_used=is_fallback,
            dry_run=is_dry_run,
            feature_disabled=False
        )

        if result.get("success"):
            mode = "[DRY-RUN]" if is_dry_run else ""
            downgraded = "[FALLBACK]" if is_fallback else ""
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"Review published {mode}{downgraded}: {posted_count} comments posted to PR #{pr_number}")
            ]
            logger.info("[Publisher] Review published successfully", extra={
                "operation": "publisher",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "posted_count": posted_count,
                "dry_run": is_dry_run,
                "downgraded": is_fallback
            })
        else:
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"Review publishing failed: {result.get('error', 'unknown error')}")
            ]
            logger.warning("[Publisher] Review publishing failed", extra={
                "operation": "publisher",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "error": result.get("error")
            })

    except Exception as e:
        # Phase B-B C-lite: Record inline comment failure on exception
        metrics.record_inline_comment_result(
            trace_id=trace_id,
            eligible_count=inline_eligible_count,
            validated_count=len(inline_comments),
            downgraded_count=downgraded_count,
            posted_count=0,
            post_failed=True,
            fallback_used=False,
            dry_run=False,
            feature_disabled=False
        )
        error_msg = str(e)
        state["publish_result"]["error"] = error_msg
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Review publishing error: {error_msg}")
        ]
        logger.error(f"[Publisher] Error publishing review: {e}", extra={
            "operation": "publisher",
            "trace_id": trace_id,
            "pr_number": pr_number,
            "error": error_msg
        }, exc_info=True)

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete(
        "publisher",
        trace_id,
        success=state["publish_result"].get("success", False),
        latency_ms=latency_ms
    )
    return state


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


def create_orchestrator_graph(entry_point: str = "planner"):
    """
    Creates the LangGraph StateGraph for orchestration

    Phase 2 PR-1813 Update (Agent Evaluation):
        planner → security_advisor → governance_advisor → cost_advisor → permission_advisor → reputation_advisor → policy_enforcement → (executor | finalizer) → ci_monitor → reviewer → decision → (fixer if needed) → finalizer → evaluation → END

    Phase 7 Issue #2211 Review Follow-up Mode:
        review_intake → planner → ... (same as above)
        Entry point can be "review_intake" for review follow-up tasks

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
        - review_intake: Entry point for review follow-up tasks (Issue #2211)
        - internal_review: Entry point for internal re-review tasks (Issue #2212)
        - planner: Task decomposition using LLM Planner
        - executor: Code generation execution
        - ci_monitor: CI status monitoring
        - reviewer: Code review and analysis
        - decision: Merge decision logic
        - fixer: Auto-fix CI failures
        - finalizer: Prepare final result

    Phase 7 Issue #2212 Internal Reviewer Agent Re-review Mode:
        internal_review → reviewer → decision → ... (same as above)
        Entry point can be "internal_review" for internal re-review tasks

    Args:
        entry_point: Entry point node name ("planner", "review_intake", or "internal_review")

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = StateGraph(AgentState)

    # Add all nodes
    # Phase 7 Issue #2211: Review Intake node for review follow-up tasks
    workflow.add_node("review_intake", review_intake_node)
    # Phase 7 Issue #2212: Internal Review node for internal re-review tasks
    workflow.add_node("internal_review", internal_review_node)
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
    # EPIC B Phase B-3: Publisher node for GitHub inline comment posting
    workflow.add_node("publisher", publisher_node)
    workflow.add_node("finalizer", finalizer_node)
    # Phase 2 PR-1813: Agent Evaluation node
    workflow.add_node("evaluation", evaluation_node)

    # Set entry point (Issue #2211: support review_intake as alternative entry point)
    workflow.set_entry_point(entry_point)

    # Phase 7 Issue #2211: Review Intake → Planner edge
    # review_intake → planner (for review follow-up tasks)
    workflow.add_edge("review_intake", "planner")

    # Phase 7 Issue #2212: Internal Review → Reviewer edge
    # internal_review → reviewer (for internal re-review tasks)
    workflow.add_edge("internal_review", "reviewer")

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

    # policy_enforcement → (executor | publisher) based on policy decision (PR-2)
    # EPIC B Phase B-3: Route finalize through publisher for review posting
    workflow.add_conditional_edges(
        "policy_enforcement",
        should_proceed_after_policy,
        {
            "execute": "executor",
            "finalize": "publisher"
        }
    )

    # executor → (execute | monitor_ci | fix | publisher)
    # EPIC B Phase B-3: Route finalize through publisher for review posting
    workflow.add_conditional_edges(
        "executor",
        should_continue_execution,
        {
            "execute": "executor",
            "monitor_ci": "ci_monitor",
            "fix": "fixer",
            "finalize": "publisher"
        }
    )

    # ci_monitor → reviewer (Phase 3: always go to reviewer after CI check)
    workflow.add_edge("ci_monitor", "reviewer")

    # reviewer → decision
    workflow.add_edge("reviewer", "decision")

    # decision → (fix | monitor_ci | publisher)
    # EPIC B Phase B-3: Route finalize through publisher for review posting
    workflow.add_conditional_edges(
        "decision",
        should_fix_or_finalize,
        {
            "fix": "fixer",
            "monitor_ci": "ci_monitor",
            "finalize": "publisher"
        }
    )

    # fixer → executor (retry loop)
    workflow.add_edge("fixer", "executor")

    # EPIC B Phase B-3: publisher → finalizer
    workflow.add_edge("publisher", "finalizer")

    # finalizer → evaluation (Phase 2 PR-1813: Agent Evaluation)
    workflow.add_edge("finalizer", "evaluation")

    # evaluation → END (Phase 2 PR-1813)
    workflow.add_edge("evaluation", END)

    # Use factory function to get appropriate checkpointer (Redis or Memory)
    checkpointer = get_checkpointer()

    app = workflow.compile(checkpointer=checkpointer)

    logger.info("LangGraph orchestrator workflow compiled successfully (Phase 4 PR-4: 5-Agent Advisory Pipeline)")

    return app


def _create_base_initial_state(
    goal: str,
    trace_id: str,
    repo: str,
    branch: str = "",
    task_type: str = "default",
) -> dict:
    """
    Create base initial state for orchestrator workflows.

    Issue #2260: Extract common initial_state initialization helper

    This helper function creates the base initial state dictionary that is
    shared across all orchestrator entry points (run_orchestrator,
    run_review_follow_up_orchestrator, run_internal_review_orchestrator).

    Args:
        goal: User's goal/question
        trace_id: Unique identifier for this task
        repo: GitHub repository (owner/repo format)
        branch: Git branch name (default: "")
        task_type: Type of task (default, review_follow_up, internal_review)

    Returns:
        dict: Base initial state dictionary with all common fields initialized
    """
    return {
        "messages": [HumanMessage(content=goal)],
        "goal": goal,
        "trace_id": trace_id,
        "repo": repo,
        "branch": branch,
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
        "pm_advisory": {},
        "pm_sub_tasks": [],
        "pm_confidence_score": 0.0,
        "pm_risk": "info",
        "ops_advisory": {},
        "ops_health_status": "unknown",
        "ops_risk": "info",
        "ops_recommended_actions": [],
        "task_type": task_type,
        "original_pr_number": 0,
        "comment_url": "",
        "comment_body": "",
        "review_file_path": "",
        "review_line_number": 0,
        "triage_result": {},
        "pr_context": {},
        "review_follow_up_action": "",
        "requires_hitl_approval": False,
    }


def run_orchestrator(
    goal: str,
    repo: str,
    trace_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Run the LangGraph orchestrator workflow

    Args:
        goal: User's goal/question
        repo: GitHub repository (owner/repo format)
        trace_id: Unique identifier for this task
        context: Optional context dict from webhook/caller containing:
            - pr_number: PR number (int) for PR-related tasks
            - pr_url: PR URL (str) for PR-related tasks
            - resource_id: Resource ID from webhook event
            - resource_type: Resource type (e.g., "pull_request")
            - event_type: Webhook event type

    Returns:
        dict: Final result containing pr_url, ci_state, status, etc.

    Issue: Phase B-B - Fix PR context passing from webhook to orchestrator
    """
    start_time = time.time()
    metrics = _get_metrics()

    # Extract PR context from webhook context (only necessary fields)
    # Issue: Phase B-B - Avoid "No PR to review" by passing PR number
    # Use positive validation: only extract PR info when resource_type == "pull_request"
    pr_number = 0
    pr_url = ""
    if context and context.get("resource_type") == "pull_request":
        # Handle pr_number: could be int or string from webhook
        raw_pr_number = context.get("pr_number") or context.get("resource_id")
        if raw_pr_number:
            try:
                pr_number = int(raw_pr_number)
            except (ValueError, TypeError):
                pr_number = 0
        pr_url = context.get("pr_url") or context.get("url") or ""

    # Observability log: always print pr_number, pr_url, trace_id in message
    # Issue: Phase B-B - Avoid black-box issues where upstream extracts but downstream doesn't receive
    # Note: extra fields are not output by worker.py's basicConfig formatter, so we put key fields in message
    has_context = context is not None
    # TODO: Remove these diagnostic fields after pr_number=0 root cause is identified (Phase B-B)
    # Diagnostic fields to debug pr_number=0 issue - use structure info instead of raw content to avoid JSON breakage
    resource_type = context.get("resource_type", "MISSING") if context else "NO_CONTEXT"
    context_keys = ",".join(sorted(context.keys())) if context else ""
    # Use payload structure info instead of raw content (raw content may contain quotes that break JSON)
    payload = context.get("payload", {}) if context else {}
    payload_keys = ",".join(sorted(payload.keys())) if isinstance(payload, dict) else "NOT_DICT"
    payload_len = len(str(payload)) if payload else 0
    # Capture raw values before extraction to diagnose pr_number=0
    raw_pr_number = context.get("pr_number") or context.get("resource_id") if context else "MISSING"
    raw_pr_url = context.get("pr_url") or context.get("url") if context else "MISSING"
    logger.info(
        f"Starting LangGraph orchestrator trace_id={trace_id} pr_number={pr_number} pr_url='{pr_url}' has_context={has_context} resource_type='{resource_type}' context_keys=[{context_keys}] payload_keys=[{payload_keys}] payload_len={payload_len} raw_pr_number={raw_pr_number} raw_pr_url='{raw_pr_url}'",
        extra={
            "operation": "run_orchestrator",
            "trace_id": trace_id,
            "goal": goal[:50],
            "repo": repo,
            "pr_number": pr_number,
            "pr_url": pr_url,
            "has_context": has_context,
        }
    )

    metrics.record_workflow_start(trace_id, goal)

    agent_eval = _get_agent_eval()
    agent_eval.start_workflow_metrics(trace_id, goal)

    app = create_orchestrator_graph()

    # Issue #2260: Use helper to create base initial state
    initial_state = _create_base_initial_state(
        goal=goal,
        trace_id=trace_id,
        repo=repo,
        task_type="default",
    )

    # Issue: Phase B-B - Merge PR context into initial state
    # pr_number: 0 is treated as "no PR" by downstream nodes, so only set if valid
    if pr_number > 0:
        initial_state["pr_number"] = pr_number
    if pr_url:
        initial_state["pr_url"] = pr_url

    config = {"configurable": {"thread_id": trace_id}}

    try:
        result = app.invoke(initial_state, config)

        final_result = result.get("final_result", {})

        # Note: extra fields are not output by worker.py's basicConfig formatter, so we put key fields in message
        # Use default values to avoid "status=None" in logs
        result_status = final_result.get("status") or "unknown"
        result_pr_url = final_result.get("pr_url") or ""
        logger.info(
            f"LangGraph orchestrator completed trace_id={trace_id} status={result_status} pr_url='{result_pr_url}'",
            extra={
                "operation": "run_orchestrator",
                "trace_id": trace_id,
                "status": result_status,
                "pr_url": result_pr_url
            }
        )

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


def run_review_follow_up_orchestrator(
    review_task: dict,
    trace_id: str,
) -> dict:
    """
    Run the LangGraph orchestrator workflow for review follow-up tasks.

    Issue #2211: Orchestrator Review Follow-up Mode

    This function is the entry point for processing AI reviewer comments
    that have been triaged and need to be addressed.

    Args:
        review_task: Dictionary containing review follow-up task data:
            - task_type: "review_follow_up"
            - original_pr_number: PR number being reviewed
            - repo: Repository in owner/repo format
            - branch: Branch name
            - comment_url: URL to the review comment
            - comment_body: Body of the review comment
            - file_path: File path mentioned in comment
            - line_number: Line number mentioned in comment
            - triage_result: Result from CommentTriageAgent
        trace_id: Unique identifier for this task

    Returns:
        dict: Final result containing pr_url, ci_state, status, etc.
    """
    start_time = time.time()
    metrics = _get_metrics()

    # Extract task data
    repo = review_task.get("repo", "")
    goal = review_task.get("goal", "")
    original_pr_number = review_task.get("original_pr_number", 0)
    comment_body = review_task.get("comment_body", "")

    # Build goal if not provided
    if not goal:
        goal = f"[Review Follow-up] Address comment on PR #{original_pr_number}: {comment_body[:100]}..."

    logger.info("Starting Review Follow-up orchestrator", extra={
        "operation": "run_review_follow_up_orchestrator",
        "trace_id": trace_id,
        "original_pr_number": original_pr_number,
        "repo": repo,
        "task_type": "review_follow_up",
    })

    metrics.record_workflow_start(trace_id, goal)

    agent_eval = _get_agent_eval()
    agent_eval.start_workflow_metrics(trace_id, goal)

    # Create graph with review_intake as entry point
    app = create_orchestrator_graph(entry_point="review_intake")

    # Issue #2260: Use helper to create base initial state
    initial_state = _create_base_initial_state(
        goal=goal,
        trace_id=trace_id,
        repo=repo,
        branch=review_task.get("branch", ""),
        task_type="review_follow_up",
    )
    # Add review follow-up specific fields
    initial_state.update({
        "original_pr_number": original_pr_number,
        "comment_url": review_task.get("comment_url", ""),
        "comment_body": comment_body,
        "review_file_path": review_task.get("file_path", ""),
        "review_line_number": review_task.get("line_number", 0),
        "triage_result": review_task.get("triage_result", {}),
        "pr_context": review_task.get("pr_context", {}),
        "review_follow_up_action": review_task.get("review_follow_up_action", ""),
        "requires_hitl_approval": review_task.get("requires_approval", False),
    })

    config = {"configurable": {"thread_id": trace_id}}

    try:
        result = app.invoke(initial_state, config)

        final_result = result.get("final_result", {})

        logger.info("Review Follow-up orchestrator completed", extra={
            "operation": "run_review_follow_up_orchestrator",
            "trace_id": trace_id,
            "status": final_result.get("status"),
            "pr_url": final_result.get("pr_url"),
            "original_pr_number": original_pr_number,
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
        logger.error(f"Review Follow-up orchestrator failed: {error_msg}", extra={
            "operation": "run_review_follow_up_orchestrator",
            "trace_id": trace_id,
            "error": error_msg,
            "original_pr_number": original_pr_number,
        })

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="error", latency_ms=latency_ms)

        failure_recorder = _get_failure_recorder()
        failure_recorder.record_failure_from_state(
            state={
                "trace_id": trace_id,
                "goal": goal,
                "repo": repo,
                "task_type": "review_follow_up",
                "original_pr_number": original_pr_number,
            },
            error_type="review_follow_up_exception",
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
            "task_type": "review_follow_up",
            "original_pr_number": original_pr_number,
            "timestamp": datetime.utcnow().isoformat()
        }


def run_internal_review_orchestrator(
    internal_review_task: dict,
    trace_id: str,
) -> dict:
    """
    Run the LangGraph orchestrator workflow for internal re-review tasks.

    Issue #2212: Internal Reviewer Agent Re-review Mechanism

    This function is the entry point for performing internal re-reviews
    of AI reviewer assessments after fixes have been applied.

    Args:
        internal_review_task: Dictionary containing internal review task data:
            - task_type: "internal_review"
            - original_pr_number: PR number being re-reviewed
            - repo: Repository in owner/repo format
            - branch: Branch name
            - comment_url: URL to the original review comment
            - comment_body: Body of the original review comment
            - file_path: File path mentioned in comment
            - line_number: Line number mentioned in comment
            - triage_result: Result from CommentTriageAgent
            - initial_ai_review: Initial AI reviewer assessment
            - follow_up_summary: Summary of follow-up actions taken
            - ci_state: Current CI state
            - code_quality_score: Current code quality score
        trace_id: Unique identifier for this task

    Returns:
        dict: Final result containing internal review decision, agreement, etc.
    """
    start_time = time.time()
    metrics = _get_metrics()

    repo = internal_review_task.get("repo", "")
    goal = internal_review_task.get("goal", "")
    original_pr_number = internal_review_task.get("original_pr_number", 0)
    comment_body = internal_review_task.get("comment_body", "")

    if not goal:
        goal = f"[Internal Review] Re-review AI assessment on PR #{original_pr_number}: {comment_body[:100]}..."

    logger.info("Starting Internal Review orchestrator", extra={
        "operation": "run_internal_review_orchestrator",
        "trace_id": trace_id,
        "original_pr_number": original_pr_number,
        "repo": repo,
        "task_type": "internal_review",
    })

    metrics.record_workflow_start(trace_id, goal)

    agent_eval = _get_agent_eval()
    agent_eval.start_workflow_metrics(trace_id, goal)

    app = create_orchestrator_graph(entry_point="internal_review")

    # Issue #2260: Use helper to create base initial state
    initial_state = _create_base_initial_state(
        goal=goal,
        trace_id=trace_id,
        repo=repo,
        branch=internal_review_task.get("branch", ""),
        task_type="internal_review",
    )
    # Override fields with task-specific values
    initial_state.update({
        "pr_url": internal_review_task.get("pr_url", ""),
        "pr_number": internal_review_task.get("pr_number", 0),
        "ci_state": internal_review_task.get("ci_state", "unknown"),
        "ci_checks": internal_review_task.get("ci_checks", {}),
        "code_quality_score": internal_review_task.get("code_quality_score", 100),
        "original_pr_number": original_pr_number,
        "comment_url": internal_review_task.get("comment_url", ""),
        "comment_body": comment_body,
        "review_file_path": internal_review_task.get("file_path", ""),
        "review_line_number": internal_review_task.get("line_number", 0),
        "triage_result": internal_review_task.get("triage_result", {}),
        "pr_context": internal_review_task.get("pr_context", {}),
        "requires_hitl_approval": internal_review_task.get("requires_approval", False),
        # Internal review specific fields
        "internal_review_mode": True,
        "initial_ai_review": internal_review_task.get("initial_ai_review", {}),
        "follow_up_summary": internal_review_task.get("follow_up_summary", {}),
        "internal_review_result": {},
        "internal_review_decision": "",
        "ai_reviewer_agreement": "",
    })

    config = {"configurable": {"thread_id": trace_id}}

    try:
        result = app.invoke(initial_state, config)

        internal_review_result = result.get("internal_review_result", {})
        final_result = result.get("final_result", {})

        logger.info("Internal Review orchestrator completed", extra={
            "operation": "run_internal_review_orchestrator",
            "trace_id": trace_id,
            "internal_review_decision": result.get("internal_review_decision"),
            "ai_reviewer_agreement": result.get("ai_reviewer_agreement"),
            "requires_hitl": result.get("requires_hitl_approval"),
            "original_pr_number": original_pr_number,
        })

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="success", latency_ms=latency_ms)

        agent_eval.record_workflow_result(
            trace_id,
            status="success",
            pr_created=bool(final_result.get("pr_url")),
            ci_passed=result.get("ci_state") == "success",
            code_quality_score=result.get("code_quality_score", 100)
        )
        agent_eval.complete_workflow_metrics(trace_id)

        return {
            "trace_id": trace_id,
            "task_type": "internal_review",
            "original_pr_number": original_pr_number,
            "internal_review_result": internal_review_result,
            "internal_review_decision": result.get("internal_review_decision", ""),
            "ai_reviewer_agreement": result.get("ai_reviewer_agreement", ""),
            "requires_hitl_approval": result.get("requires_hitl_approval", False),
            "ci_state": result.get("ci_state", "unknown"),
            "code_quality_score": result.get("code_quality_score", 100),
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Internal Review orchestrator failed: {error_msg}", extra={
            "operation": "run_internal_review_orchestrator",
            "trace_id": trace_id,
            "error": error_msg,
            "original_pr_number": original_pr_number,
        })

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="error", latency_ms=latency_ms)

        failure_recorder = _get_failure_recorder()
        failure_recorder.record_failure_from_state(
            state={
                "trace_id": trace_id,
                "goal": goal,
                "repo": repo,
                "task_type": "internal_review",
                "original_pr_number": original_pr_number,
            },
            error_type="internal_review_exception",
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
            "task_type": "internal_review",
            "original_pr_number": original_pr_number,
            "internal_review_result": {},
            "internal_review_decision": "escalate",
            "ai_reviewer_agreement": "disagree",
            "requires_hitl_approval": True,
            "ci_state": "error",
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }
