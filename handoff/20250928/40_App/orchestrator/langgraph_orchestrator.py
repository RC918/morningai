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

import contextlib
import functools
import gc
import logging
import re
import sys
import threading as _threading
import time
import traceback
from typing import TypedDict, Annotated, Sequence, Optional, Callable, Dict, Any, NotRequired
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from orchestrator_metrics import get_orchestrator_metrics, OrchestratorMetrics
from failure_recorder import init_failure_recorder_from_env, FailureRecorder
from agent_eval_integration import (
    init_agent_eval_from_env,
    AgentEvalIntegration
)
from common.config.settings import settings
from llm_reviewer_adapter import generate_llm_review, sanitize_diff_content
import hashlib
from webhooks.review_follow_up import determine_hitl_requirement
from tools.github_api import get_repo, get_pr_diff
from exceptions import DatabaseException
from meta_agent.sensitive_data_masker import mask_sensitive_data
from resource_telemetry import log_resource_peak, log_checkpoint_put_bytes

logger = logging.getLogger(__name__)

# Global metrics instance (lazy initialization)
_metrics: Optional[OrchestratorMetrics] = None
_failure_recorder: Optional[FailureRecorder] = None
_agent_eval: Optional[AgentEvalIntegration] = None

# Global PostgreSQL connection pool (lazy initialization)
# Issue: Connection Lifecycle Bug Fix - Use connection pooling instead of per-job connections
# Benefits:
# 1. Enterprise-grade: Reuse connections instead of dial/hangup per job
# 2. Auto-healing: Pool automatically validates and reconnects dead connections
# 3. Resource management: Prevents connection leaks and Supabase limit exhaustion
_postgres_pool = None
# Thread-safe lock for pool initialization - initialized at module level (eager init)
# to avoid race condition in lazy initialization pattern
_postgres_pool_lock = _threading.Lock()

# EPIC D Issue #3487: System error indicators for SeniorCoder abort classification
# These patterns distinguish system errors (LLM failures, parsing errors) from
# genuine complexity aborts that should trigger HITL gate.
# Note: Uses substring matching (case-insensitive). For structured error types,
# see follow-up issue for ArchitectureSpec error taxonomy.
_SENIOR_CODER_SYSTEM_ERROR_INDICATORS = (
    "JSON parsing failed",
    "LLM call failed",
    "parsing error",
    "timeout",
    "connection error",
)


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


def _update_span_id_in_state(
    state: "AgentState",
    span_id: str,
    node_name: str
) -> None:
    """
    Safely update current_span_id in LangGraph state for span hierarchy tracking.

    Issue #3707: This helper function encapsulates the intentional direct state
    mutation pattern used for span_id propagation in the node_metrics decorator.

    WHY DIRECT MUTATION IS INTENTIONAL HERE:
    =========================================
    In LangGraph, the standard convention is for nodes to return partial state
    updates that get merged after node completion. However, for span hierarchy
    tracking, we need to update current_span_id BEFORE the wrapped node runs,
    so that any child spans created during node execution can reference the
    correct parent span_id.

    This is a decorator pattern, not a node pattern - decorators that need to
    modify state before the wrapped function runs have different constraints
    than regular nodes.

    SAFETY MEASURES:
    ================
    1. Only mutates when ENABLE_SSOT_TELEMETRY=true (feature flag protection)
    2. Only mutates the current_span_id field (minimal scope)
    3. Logs the mutation for debugging and audit trail
    4. Validates state is a mutable mapping before mutation

    Args:
        state: The LangGraph AgentState to update
        span_id: The new span_id to set
        node_name: The node name (for logging)

    Event Codes (greppable):
        [SPAN_STATE_UPDATE] - Span ID updated in state for hierarchy tracking
    """
    # Issue #3707: gemini-code-assist suggestion - use MutableMapping for robustness
    from collections.abc import MutableMapping
    if not isinstance(state, MutableMapping):
        logger.warning(
            f"[SPAN_STATE_UPDATE] Cannot update span_id: state is not a mutable mapping "
            f"(type={type(state).__name__}, node={node_name})"
        )
        return

    old_span_id = state.get("current_span_id")
    state["current_span_id"] = span_id

    logger.debug(
        f"[SPAN_STATE_UPDATE] {node_name}: {old_span_id} -> {span_id}",
        extra={
            "event_type": "span_state_update",
            "node_name": node_name,
            "old_span_id": old_span_id,
            "new_span_id": span_id,
        }
    )


def node_metrics(node_name: str, epic_tag: str = "EPIC-C") -> Callable:
    """
    Decorator to extract common node boilerplate for metrics recording.

    Phase 3 Follow-up (#1858): Reduces duplication in advisor nodes by
    automatically handling:
    - start_time tracking
    - metrics.record_node_start()
    - latency_ms calculation
    - metrics.record_node_complete()

    Issue #3578 SSOT Telemetry v3: When ENABLE_SSOT_TELEMETRY=true, also emits
    TelemetryRecordV3 spans with proper parent-child hierarchy via current_span_id.

    Issue #3706: epic_tag is now configurable for more granular telemetry
    categorization per node. Defaults to "EPIC-C" for backward compatibility.

    Issue #3707: State mutation for span_id is handled via _update_span_id_in_state()
    helper function with proper documentation and safety measures.

    Args:
        node_name: Name of the node for metrics identification.
        epic_tag: Epic tag for telemetry categorization (default: "EPIC-C").

    Returns:
        Callable: A decorator that wraps the node function.

    Examples:
        The decorated function must accept a `success` keyword argument, which is a
        mutable list `[False]`. The function should set `success[0] = True` upon
        successful execution.

        Basic usage::

            @node_metrics("pm_advisor")
            def pm_advisor_node(state: AgentState, success: list) -> AgentState:
                # Node logic here
                success[0] = True
                return state

        With a custom epic tag::

            @node_metrics("review_node", epic_tag="EPIC-D")
            def review_node(state: AgentState, success: list) -> AgentState:
                # Node logic here
                success[0] = True
                return state
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state: "AgentState") -> "AgentState":
            start_time = time.time()
            metrics = _get_metrics()
            trace_id = state.get("trace_id", "unknown")

            metrics.record_node_start(node_name, trace_id)

            # Issue #3578: SSOT Telemetry v3 span creation
            span_context = None
            TelemetryRecordV3 = None
            StatusCode = None
            if settings.enable_ssot_telemetry:
                try:
                    from core.telemetry import (
                        TelemetryRecordV3,
                        create_span_context,
                        StatusCode,
                    )
                except ImportError as import_err:
                    logger.debug(
                        f"[node_metrics] core.telemetry not available, skipping SSOT spans: {import_err}"
                    )
                else:
                    # Only create span context if import succeeded
                    parent_span_id = state.get("current_span_id")
                    span_context = create_span_context(
                        trace_id=trace_id if trace_id != "unknown" else None,
                        parent_span_id=parent_span_id,
                    )

            success = [False]
            error_message = None
            try:
                # Issue #3707: Update current_span_id in state for child spans
                # Uses _update_span_id_in_state() helper for safe, documented mutation
                if span_context is not None:
                    _update_span_id_in_state(state, span_context.span_id, node_name)
                result = func(state, success)
            except Exception as e:
                error_message = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                metrics.record_node_complete(
                    node_name, trace_id, success=success[0], latency_ms=latency_ms
                )
                # P1 瘦身計畫 (#3197): Log RSS after each node for resource profiling
                log_resource_peak(node_name, trace_id)

                # Issue #3578: Emit SSOT telemetry span on completion
                # Note: span_context is only non-None if enable_ssot_telemetry was True
                if span_context is not None:
                    try:
                        status_code = StatusCode.OK if success[0] else StatusCode.ERROR
                        record = TelemetryRecordV3.create(
                            name=f"node.{node_name}",
                            span_context=span_context,
                            component="LangGraphOrchestrator",
                            status_code=status_code,
                            status_message=error_message,
                            node_name=node_name,
                            epic_tag=epic_tag,
                            metrics={"latency_ms": latency_ms},
                            attributes={
                                "trace_id": trace_id,
                                "success": success[0],
                            },
                        )
                        record.emit()
                    except Exception as emit_err:
                        logger.debug(
                            f"[node_metrics] Failed to emit SSOT span: {emit_err}",
                            exc_info=True
                        )

            return result
        return wrapper
    return decorator


def _get_postgres_pool():
    """
    Get or initialize the global PostgreSQL connection pool.

    Issue: Connection Lifecycle Bug Fix (Dec 2025)

    This function implements enterprise-grade connection pooling using psycopg_pool.
    Benefits:
    1. Connection reuse: No dial/hangup overhead per job
    2. Auto-healing: Pool validates connections and reconnects dead ones
    3. Resource management: Prevents connection leaks and Supabase limit exhaustion
    4. Thread-safe: Uses threading lock for initialization

    Pool Configuration:
    - min_size: 1 (minimum connections to keep open)
    - max_size: 5 (maximum connections, prevents Supabase limit exhaustion)
    - max_lifetime: 600 (10 minutes, aggressive recycling to prevent stale connections)
    - max_idle: 120 (2 minutes, aggressive recycling of idle connections)
    - reconnect_timeout: 60 (1 minute timeout for reconnection attempts)
    - check: ConnectionPool.check_connection (validates connection health)
    - TCP Keepalive (libpq seconds): idle=30, interval=10, count=5 (~80s worst-case detection)

    Returns:
        ConnectionPool: The global connection pool instance, or None if initialization fails
    """
    global _postgres_pool
    import os

    # Fast path: pool already initialized
    if _postgres_pool is not None:
        return _postgres_pool

    with _postgres_pool_lock:
        # Double-check after acquiring lock
        if _postgres_pool is not None:
            return _postgres_pool

        database_url = settings.database_url or os.environ.get("DATABASE_URL")
        if not database_url:
            logger.warning(
                "DATABASE_URL not configured, cannot create connection pool",
                extra={"operation": "_get_postgres_pool"}
            )
            return None

        try:
            from psycopg_pool import ConnectionPool
            from psycopg.rows import dict_row

            # Configure pool with health checks and auto-reconnect
            # These settings are optimized for Supabase PostgreSQL
            #
            # CRITICAL FIX (Dec 2025): Added prepare_threshold=0 to disable prepared
            # statement caching. This prevents "prepared statement _pg3_1 does not exist"
            # errors when Supabase resets connections mid-workflow. The official
            # PostgresSaver.from_conn_string() also uses prepare_threshold=0.
            # SSL Connection Fix (Dec 2025): Aggressive recycling + TCP Keepalive
            # to prevent "SSL connection has been closed unexpectedly" errors.
            # Root cause: Network layer (NAT/LB) may drop idle connections before
            # the pool's max_idle timeout, causing "flushing failed" errors.

            # Pool configuration - single source of truth for both pool creation and logging
            pool_max_lifetime = 600  # 10 minutes - aggressive recycling to prevent stale connections
            pool_max_idle = 120  # 2 minutes - aggressive recycling of idle connections
            pool_min_size = 1  # Keep at least 1 connection ready
            pool_max_size = 5  # Limit to prevent Supabase connection exhaustion

            # TCP Keepalive settings (vital for cloud NAT/LB)
            # These prevent network devices from dropping idle connections
            # All values are in seconds (libpq convention)
            # Worst-case dead peer detection: idle(30) + interval(10) * count(5) = ~80s
            keepalives = 1  # Enable TCP keepalive
            keepalives_idle = 30  # Start probing after 30s idle (seconds, libpq)
            keepalives_interval = 10  # Probe every 10s (~50s probe window)
            keepalives_count = 5  # Give up after 5 failed probes

            _postgres_pool = ConnectionPool(
                conninfo=database_url,
                min_size=pool_min_size,
                max_size=pool_max_size,
                max_lifetime=pool_max_lifetime,
                max_idle=pool_max_idle,
                reconnect_timeout=60,  # 1 minute timeout for reconnection
                kwargs={
                    "autocommit": True,  # Required by PostgresSaver
                    "row_factory": dict_row,  # Required by PostgresSaver
                    "prepare_threshold": 0,  # Disable prepared statements to avoid state loss on reconnect
                    "keepalives": keepalives,
                    "keepalives_idle": keepalives_idle,
                    "keepalives_interval": keepalives_interval,
                    "keepalives_count": keepalives_count,
                },
                # Health check: validates connection before returning from pool
                check=ConnectionPool.check_connection,
            )

            # Wait for pool to be ready (opens min_size connections)
            _postgres_pool.wait()

            logger.info(
                f"PostgreSQL connection pool initialized successfully "
                f"[max_lifetime={pool_max_lifetime} max_idle={pool_max_idle} keepalives={keepalives} "
                f"keepalives_idle={keepalives_idle} keepalives_interval={keepalives_interval} "
                f"keepalives_count={keepalives_count}]",
                extra={
                    "operation": "_get_postgres_pool",
                    "min_size": pool_min_size,
                    "max_size": pool_max_size,
                    "max_lifetime": pool_max_lifetime,
                    "max_idle": pool_max_idle,
                    "keepalives": keepalives,
                    "keepalives_idle": keepalives_idle,
                    "keepalives_interval": keepalives_interval,
                    "keepalives_count": keepalives_count,
                    "database_url_masked": database_url[:30] + "..." if len(database_url) > 30 else "[hidden]"
                }
            )

            return _postgres_pool

        except ImportError as e:
            logger.warning(
                f"psycopg_pool not installed, connection pooling unavailable: {e}",
                extra={
                    "operation": "_get_postgres_pool",
                    "error": str(e)
                }
            )
            return None
        except Exception as e:
            logger.error(
                f"Failed to initialize PostgreSQL connection pool: {e}",
                extra={
                    "operation": "_get_postgres_pool",
                    "error": str(e)
                }
            )
            return None


def _reset_postgres_pool():
    """
    Force reset the global PostgreSQL connection pool.

    OOM Fix (Dec 2025): When connection-lost errors occur (Pipeline [BAD], SSL closed,
    connection reset), the pool may contain poisoned connections that hold memory.
    This function closes the old pool and creates a fresh one.

    This should be called when:
    1. Transient connection errors are detected during checkpoint operations
    2. The pool appears to be in a bad state

    Thread Safety:
        Uses the same lock as _get_postgres_pool() to prevent races.
        IMPORTANT: To avoid deadlocks, we minimize lock-hold time by:
        1. Under lock: swap _postgres_pool to None and capture old_pool
        2. Outside lock: close old_pool (may block waiting for borrowers)
        3. Under lock: create and install new pool
        This prevents holding the lock during potentially blocking close() operations.

    Returns:
        ConnectionPool: The new pool instance, or None if reset failed
    """
    global _postgres_pool
    import os

    # Step 1: Under lock, capture old pool and clear global reference
    with _postgres_pool_lock:
        old_pool = _postgres_pool
        _postgres_pool = None

    # Step 2: Outside lock, close old pool (may block waiting for borrowers)
    if old_pool is not None:
        try:
            old_pool.close()
            logger.info(
                "PostgreSQL connection pool closed for reset",
                extra={"operation": "_reset_postgres_pool"}
            )
        except Exception as e:
            logger.warning(
                f"Error closing old PostgreSQL pool during reset: {e}",
                extra={
                    "operation": "_reset_postgres_pool",
                    "error": str(e)
                }
            )

    # Force garbage collection to release any lingering connection objects
    gc.collect()

    # Step 3: Create new pool and install under lock
    database_url = settings.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning(
            "DATABASE_URL not configured, cannot create new connection pool",
            extra={"operation": "_reset_postgres_pool"}
        )
        return None

    try:
        from psycopg_pool import ConnectionPool
        from psycopg.rows import dict_row

        new_pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=5,
            max_lifetime=1800,
            max_idle=300,
            reconnect_timeout=60,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
                "prepare_threshold": 0,
            },
            check=ConnectionPool.check_connection,
        )

        new_pool.wait()

        # Install new pool under lock with CAS pattern
        # This prevents race condition where another thread created a pool
        # while we were closing the old one and creating the new one
        pool_to_close = None
        with _postgres_pool_lock:
            if _postgres_pool is None:
                # Normal case: no one else created a pool, install ours
                _postgres_pool = new_pool
                installed_pool = new_pool
            else:
                # Race condition: another thread already created a pool
                # Keep the existing pool, close our newly created one
                pool_to_close = new_pool
                installed_pool = _postgres_pool
                logger.info(
                    "Pool reset: another thread already created pool, using existing",
                    extra={"operation": "_reset_postgres_pool"}
                )

        # Close unused pool outside lock to avoid blocking
        if pool_to_close is not None:
            try:
                pool_to_close.close()
            except Exception as close_err:
                logger.warning(
                    f"Error closing unused pool after race: {close_err}",
                    extra={"operation": "_reset_postgres_pool", "error": str(close_err)}
                )

        logger.info(
            "PostgreSQL connection pool reset successfully",
            extra={
                "operation": "_reset_postgres_pool",
                "min_size": 1,
                "max_size": 5,
            }
        )

        return installed_pool

    except Exception as e:
        logger.error(
            f"Failed to create new PostgreSQL connection pool during reset: {e}",
            extra={
                "operation": "_reset_postgres_pool",
                "error": str(e)
            }
        )
        return None


def get_postgres_checkpointer():
    """
    Get a PostgreSQL checkpointer with per-operation connection borrowing.

    CRITICAL FIX (Dec 2025): Changed from holding a single connection for entire
    workflow (~2 minutes) to per-operation connection borrowing.

    Previous approach (VULNERABLE):
        with pool.connection() as conn:
            checkpointer = PostgresSaver(conn)
            app.invoke(...)  # Holds connection for ~2 minutes
        # Connection dies mid-workflow → Pipeline [BAD], SSL closed errors

    New approach (RESILIENT):
        checkpointer = PostgresSaver(pool)  # Pass pool, not connection
        app.invoke(...)
        # Each checkpoint operation borrows connection briefly from pool
        # Network hiccups only affect single checkpoint, not entire workflow

    This change addresses Sentry errors:
    - "the connection is closed" (12 events)
    - "SSL connection has been closed unexpectedly" (5 events)
    - "psycopg.Pipeline [BAD]" state
    - "prepared statement _pg3_1 does not exist" (4 events)

    Returns:
        PostgresSaver: A checkpointer that borrows connections per-operation, or None if unavailable

    Blueprint alignment:
        - Design for Failure: Connection can die without killing entire workflow
        - Safety Governor v2: Graceful degradation under network instability
    """
    from langgraph.checkpoint.postgres import PostgresSaver

    pool = _get_postgres_pool()

    if pool is None:
        logger.warning(
            "Connection pool unavailable, PostgreSQL checkpointer not available",
            extra={"operation": "get_postgres_checkpointer"}
        )
        return None

    try:
        # CRITICAL: Pass pool directly to PostgresSaver, NOT a single connection
        # PostgresSaver._cursor() uses _internal.get_connection() which handles
        # ConnectionPool by borrowing a connection per-operation via pool.connection()
        # This means each checkpoint I/O is isolated - network hiccups only affect
        # that single operation, not the entire 2-minute workflow
        inner_checkpointer = PostgresSaver(pool)

        # Setup must be called once to create tables/run migrations
        # This will borrow a connection briefly for the setup SQL
        inner_checkpointer.setup()

        # OOM Fix (Dec 2025): Factory function to recreate inner saver after pool reset
        # When connection-lost errors occur, the pool is reset and we need to recreate
        # the inner PostgresSaver to use the new pool
        def create_inner_saver():
            new_pool = _get_postgres_pool()
            if new_pool is None:
                raise RuntimeError("Cannot recreate inner saver: pool unavailable")
            new_inner = PostgresSaver(new_pool)
            new_inner.setup()
            return new_inner

        # Issue #2968: Wrap with ResilientPostgresSaver for auto-retry on transient errors
        # This implements "Design for Failure" from Blueprint - transient DB errors
        # (SSL closed, connection reset, etc.) are automatically retried with backoff
        # Note: The inner_checkpointer already has the pool, so each retry will naturally
        # get a fresh connection from the pool via per-operation borrowing
        #
        # OOM Fix (Dec 2025): Pass inner_factory to allow recreating inner saver after
        # pool reset on connection-lost errors
        #
        # Issue #3109: Get retry log sample rate from settings for rate-limited logging
        # Use defensive type check to handle mocked settings (MagicMock returns MagicMock
        # for any attribute access, not the default value from getattr)
        raw_sample_rate = getattr(
            settings,
            "checkpoint_retry_log_sample_rate",
            ResilientPostgresSaver.DEFAULT_RETRY_LOG_SAMPLE_RATE
        )
        try:
            retry_log_sample_rate = int(raw_sample_rate)
        except (TypeError, ValueError):
            retry_log_sample_rate = ResilientPostgresSaver.DEFAULT_RETRY_LOG_SAMPLE_RATE
        checkpointer = ResilientPostgresSaver(
            inner_saver=inner_checkpointer,
            max_retries=3,
            base_delay=0.5,
            inner_factory=create_inner_saver,
            retry_log_sample_rate=retry_log_sample_rate,
        )

        # Get pool statistics safely
        try:
            stats = pool.get_stats()
            pool_size = getattr(stats, 'pool_size', 'unknown')
            pool_available = getattr(stats, 'pool_available', 'unknown')
        except Exception:
            pool_size = 'unknown'
            pool_available = 'unknown'

        logger.info(
            "PostgreSQL checkpointer initialized with ResilientPostgresSaver wrapper",
            extra={
                "operation": "get_postgres_checkpointer",
                "checkpointer_type": "resilient_postgres_pool_per_op",
                "max_retries": 3,
                "base_delay": 0.5,
                "retry_log_sample_rate": retry_log_sample_rate,
                "pool_stats": {
                    "size": pool_size,
                    "available": pool_available,
                },
            }
        )

        return checkpointer

    except Exception as e:
        logger.error(
            f"Failed to initialize PostgreSQL checkpointer: {e}",
            extra={
                "operation": "get_postgres_checkpointer",
                "error": str(e)
            }
        )
        return None


class ResilientPostgresSaverCircuitOpen(DatabaseException):
    """
    Exception raised when the checkpoint circuit breaker is open.

    This exception is raised when too many consecutive checkpoint operations
    have failed, indicating a persistent DB connectivity issue. The job should
    be terminated to prevent memory buildup from accumulated state/writes.

    Inherits from DatabaseException to allow upstream code to handle all
    database-related errors consistently (e.g., for logging, metrics, alerting).
    """
    pass


class DegradedCheckpointerCapacityExceeded(DatabaseException):
    """
    Exception raised when degraded checkpointer capacity is exceeded.

    Issue #3027: MemorySaver OOM Protection Strategy

    This exception is raised when the number of degraded workflows exceeds
    MAX_DEGRADED_WORKFLOWS_PER_WORKER, implementing fail-fast behavior to
    prevent OOM conditions on workers.

    Inherits from DatabaseException to allow upstream code to handle all
    database-related errors consistently.
    """
    pass


class DegradedCheckpointerMemoryExceeded(DatabaseException):
    """
    Exception raised when degraded checkpointer memory hard limit is exceeded.

    Issue #3027: MemorySaver OOM Protection Strategy (Dec 2025)

    This exception is raised when the estimated memory usage of the degraded
    checkpointer exceeds DEGRADED_CHECKPOINT_MEMORY_HARD_LIMIT_MB. This is the
    'safety airbag' that terminates the task to protect the worker from OOM kills.

    Unlike the warning threshold (DEGRADED_CHECKPOINT_MEMORY_WARNING_MB), this
    hard limit causes immediate task termination rather than just logging.

    Inherits from DatabaseException to allow upstream code to handle all
    database-related errors consistently.
    """
    pass


class OOMProtectedMemorySaver:
    """
    A memory-safe wrapper around MemorySaver with OOM protection.

    Issue #3027: MemorySaver OOM Protection Strategy

    When PostgreSQL fails and workflows degrade to MemorySaver, all checkpoint
    data is stored in worker process memory. This wrapper implements safeguards
    to prevent Out-Of-Memory (OOM) conditions:

    1. Workflow Limits: Limits concurrent degraded workflows per worker
       (MAX_DEGRADED_WORKFLOWS_PER_WORKER). Rejects new workflows when limit reached.

    2. Memory Monitoring: Tracks estimated memory usage and logs warnings
       when threshold exceeded (DEGRADED_CHECKPOINT_MEMORY_WARNING_MB).

    3. Hard Memory Limit (Dec 2025): Terminates task when memory exceeds
       DEGRADED_CHECKPOINT_MEMORY_HARD_LIMIT_MB. This is the 'safety airbag'
       that prevents OOM kills.

    4. Checkpoint Eviction (Dec 2025): Implements LRU eviction to keep only
       the most recent N checkpoints per thread (DEGRADED_CHECKPOINT_MAX_PER_THREAD).

    5. Metrics Exposure: Exposes checkpoint_memory_bytes, degraded_workflow_count,
       and checkpoint_count for monitoring.

    Blueprint Alignment:
        - Safety Governor v2: Self-Governed / 自我修復
        - Telemetry v2: Observable degradation events

    Usage:
        inner_saver = MemorySaver()
        protected_saver = OOMProtectedMemorySaver(
            inner_saver,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=10,
        )
    """

    def __init__(
        self,
        inner_saver,
        max_workflows: int = 100,
        memory_warning_mb: int = 512,
        memory_hard_limit_mb: int = 1024,
        max_checkpoints_per_thread: int = 10,
        trace_id: str = "unknown",
    ):
        """
        Initialize OOMProtectedMemorySaver.

        Args:
            inner_saver: The underlying MemorySaver instance
            max_workflows: Maximum number of concurrent workflows (thread_ids)
            memory_warning_mb: Memory threshold in MB for warning logs
            memory_hard_limit_mb: Hard memory limit in MB that triggers task termination
            max_checkpoints_per_thread: Maximum checkpoints per thread (LRU eviction)
            trace_id: Trace ID for logging context
        """
        self._inner = inner_saver
        self._max_workflows = max_workflows
        self._memory_warning_mb = memory_warning_mb
        self._memory_hard_limit_mb = memory_hard_limit_mb
        self._max_checkpoints_per_thread = max_checkpoints_per_thread
        self._trace_id = trace_id
        self._memory_warning_logged = False

    @property
    def workflow_count(self) -> int:
        """Get the number of unique workflows (thread_ids) in storage."""
        return len(self._inner.storage)

    @property
    def checkpoint_count(self) -> int:
        """Get the total number of checkpoints across all workflows."""
        count = 0
        for thread_storage in self._inner.storage.values():
            for ns_storage in thread_storage.values():
                count += len(ns_storage)
        return count

    def get_memory_estimate_bytes(self) -> int:
        """
        Estimate memory usage of the MemorySaver storage.

        This is a rough estimate using sys.getsizeof on the storage dicts.
        Actual memory usage may be higher due to object overhead.
        """
        total = 0
        total += sys.getsizeof(self._inner.storage)
        total += sys.getsizeof(self._inner.writes)
        total += sys.getsizeof(self._inner.blobs)
        for thread_id, thread_storage in self._inner.storage.items():
            total += sys.getsizeof(thread_id)
            total += sys.getsizeof(thread_storage)
            for ns, ns_storage in thread_storage.items():
                total += sys.getsizeof(ns)
                total += sys.getsizeof(ns_storage)
                for cp_id, cp_data in ns_storage.items():
                    total += sys.getsizeof(cp_id)
                    total += sys.getsizeof(cp_data)
                    if isinstance(cp_data, tuple):
                        for item in cp_data:
                            total += sys.getsizeof(item)
        for outer_key, inner_dict in self._inner.writes.items():
            total += sys.getsizeof(outer_key)
            if isinstance(outer_key, tuple):
                for item in outer_key:
                    total += sys.getsizeof(item)
            total += sys.getsizeof(inner_dict)
            if isinstance(inner_dict, dict):
                for inner_key, inner_value in inner_dict.items():
                    total += sys.getsizeof(inner_key)
                    if isinstance(inner_key, tuple):
                        for item in inner_key:
                            total += sys.getsizeof(item)
                    total += sys.getsizeof(inner_value)
                    if isinstance(inner_value, tuple):
                        for item in inner_value:
                            total += sys.getsizeof(item)
        for key, value in self._inner.blobs.items():
            total += sys.getsizeof(key)
            total += sys.getsizeof(value)
            if isinstance(value, tuple):
                for item in value:
                    total += sys.getsizeof(item)
        return total

    def get_metrics(self) -> dict:
        """
        Get OOM protection metrics for monitoring.

        Returns:
            Dict with checkpoint_memory_bytes, degraded_workflow_count,
            checkpoint_count, max_workflows, and memory_warning_mb.
        """
        return {
            "checkpoint_memory_bytes": self.get_memory_estimate_bytes(),
            "degraded_workflow_count": self.workflow_count,
            "checkpoint_count": self.checkpoint_count,
            "max_workflows": self._max_workflows,
            "memory_warning_mb": self._memory_warning_mb,
        }

    def _check_capacity(self, config) -> None:
        """
        Check if adding a new workflow would exceed capacity.

        Raises:
            DegradedCheckpointerCapacityExceeded: If capacity would be exceeded
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if thread_id is None:
            return
        if thread_id in self._inner.storage:
            return
        if self.workflow_count >= self._max_workflows:
            logger.error(
                f"DEGRADED CHECKPOINTER CAPACITY EXCEEDED: Cannot accept new workflow. "
                f"trace_id={self._trace_id} thread_id={thread_id} "
                f"current_workflows={self.workflow_count} max_workflows={self._max_workflows}",
                extra={
                    "operation": "oom_protected_memory_saver",
                    "event": "capacity_exceeded",
                    "trace_id": self._trace_id,
                    "thread_id": thread_id,
                    "current_workflows": self.workflow_count,
                    "max_workflows": self._max_workflows,
                }
            )
            raise DegradedCheckpointerCapacityExceeded(
                f"Degraded checkpointer capacity exceeded: {self.workflow_count}/{self._max_workflows} workflows. "
                f"Cannot accept new workflow {thread_id}. Consider increasing MAX_DEGRADED_WORKFLOWS_PER_WORKER "
                f"or resolving the primary checkpointer failure."
            )

    def _check_memory_warning(self) -> None:
        """Log warning if memory usage exceeds threshold."""
        memory_bytes = self.get_memory_estimate_bytes()
        memory_mb = memory_bytes / (1024 * 1024)
        if memory_mb >= self._memory_warning_mb and not self._memory_warning_logged:
            self._memory_warning_logged = True
            logger.warning(
                f"DEGRADED CHECKPOINTER MEMORY WARNING: Memory usage exceeds threshold. "
                f"trace_id={self._trace_id} memory_mb={memory_mb:.2f} "
                f"threshold_mb={self._memory_warning_mb} workflows={self.workflow_count}",
                extra={
                    "operation": "oom_protected_memory_saver",
                    "event": "memory_warning",
                    "trace_id": self._trace_id,
                    "memory_bytes": memory_bytes,
                    "memory_mb": memory_mb,
                    "threshold_mb": self._memory_warning_mb,
                    "workflow_count": self.workflow_count,
                    "checkpoint_count": self.checkpoint_count,
                }
            )

    def _check_memory_hard_limit(self) -> None:
        """
        Check if memory usage exceeds hard limit and raise exception if so.

        Issue #3027: Hard Memory Limit for OOM Protection (Dec 2025)

        This is the 'safety airbag' that terminates the task to protect the worker
        from OOM kills. Unlike the warning threshold, this causes immediate task
        termination.
        """
        memory_bytes = self.get_memory_estimate_bytes()
        memory_mb = memory_bytes / (1024 * 1024)
        if memory_mb >= self._memory_hard_limit_mb:
            logger.error(
                f"DEGRADED CHECKPOINTER HARD LIMIT EXCEEDED: Terminating task. "
                f"trace_id={self._trace_id} memory_mb={memory_mb:.2f} "
                f"hard_limit_mb={self._memory_hard_limit_mb} workflows={self.workflow_count}",
                extra={
                    "operation": "oom_protected_memory_saver",
                    "event": "memory_hard_limit_exceeded",
                    "trace_id": self._trace_id,
                    "memory_bytes": memory_bytes,
                    "memory_mb": memory_mb,
                    "hard_limit_mb": self._memory_hard_limit_mb,
                    "workflow_count": self.workflow_count,
                    "checkpoint_count": self.checkpoint_count,
                }
            )
            raise DegradedCheckpointerMemoryExceeded(
                f"Degraded checkpointer memory hard limit exceeded: "
                f"{memory_mb:.2f}MB >= {self._memory_hard_limit_mb}MB. "
                f"Task terminated to protect worker from OOM. trace_id={self._trace_id}"
            )

    def _evict_old_checkpoints(self, thread_id: str) -> int:
        """
        Evict oldest checkpoints for a thread by insertion order.

        Issue #3027: Checkpoint Eviction for OOM Protection (Dec 2025)

        Keeps only the most recently written N checkpoints per thread to prevent
        unbounded growth in MemorySaver. Uses dict insertion order (Python 3.7+)
        to determine recency - oldest inserted checkpoints are evicted first.

        Note: This is "keep last N checkpoints by write order", not true LRU
        (which would track reads). This is appropriate for the OOM safety goal.

        MemorySaver uses nested dict structure: storage[thread_id][checkpoint_ns][checkpoint_id]
        We iterate through all namespaces and checkpoint IDs for the given thread.

        Args:
            thread_id: The thread ID to evict checkpoints for

        Returns:
            Number of checkpoints evicted
        """
        if not hasattr(self._inner, 'storage'):
            return 0

        storage = self._inner.storage
        if thread_id not in storage:
            return 0

        thread_data = storage[thread_id]
        all_checkpoints = []
        for checkpoint_ns in list(thread_data.keys()):
            ns_data = thread_data[checkpoint_ns]
            if isinstance(ns_data, dict):
                for checkpoint_id in list(ns_data.keys()):
                    all_checkpoints.append((checkpoint_ns, checkpoint_id))

        if len(all_checkpoints) <= self._max_checkpoints_per_thread:
            return 0

        overage = len(all_checkpoints) - self._max_checkpoints_per_thread
        to_evict = all_checkpoints[:overage]
        evicted_count = 0
        for checkpoint_ns, checkpoint_id in to_evict:
            if checkpoint_ns in thread_data and checkpoint_id in thread_data[checkpoint_ns]:
                del thread_data[checkpoint_ns][checkpoint_id]
                evicted_count += 1

        if evicted_count > 0:
            logger.info(
                f"DEGRADED CHECKPOINTER EVICTION: Evicted old checkpoints. "
                f"trace_id={self._trace_id} thread_id={thread_id} "
                f"evicted={evicted_count} remaining={len(all_checkpoints) - evicted_count}",
                extra={
                    "operation": "oom_protected_memory_saver",
                    "event": "checkpoint_eviction",
                    "trace_id": self._trace_id,
                    "thread_id": thread_id,
                    "evicted_count": evicted_count,
                    "max_per_thread": self._max_checkpoints_per_thread,
                }
            )

        return evicted_count

    def setup(self):
        """Setup - delegate to inner saver."""
        return self._inner.setup()

    def get(self, config):
        """Get checkpoint - delegate to inner saver."""
        return self._inner.get(config)

    def get_tuple(self, config):
        """Get checkpoint tuple - delegate to inner saver."""
        return self._inner.get_tuple(config)

    def put(self, config, checkpoint, metadata, new_versions):
        """Put checkpoint with capacity check, hard limit check, and eviction.

        Order of operations:
        1. Check capacity (workflow count limit)
        2. Check hard memory limit (fail-fast before adding more data)
        3. Log checkpoint payload size for resource profiling
        4. Store the checkpoint
        5. Evict old checkpoints for this thread (keep last N by insertion order)
        6. Check memory warning (log if approaching limit)
        """
        self._check_capacity(config)
        self._check_memory_hard_limit()

        # P1 瘦身計畫 (#3197): Log checkpoint payload bytes for resource profiling
        thread_id = config.get("configurable", {}).get("thread_id")
        try:
            # Estimate payload size using sys.getsizeof for top-level objects
            payload_bytes = sys.getsizeof(checkpoint) + sys.getsizeof(metadata)
        except Exception:
            payload_bytes = 0
        log_checkpoint_put_bytes(
            trace_id=self._trace_id,
            payload_bytes=payload_bytes,
            checkpoint_count=self.checkpoint_count,
            thread_id=thread_id,
            is_degraded=False
        )

        result = self._inner.put(config, checkpoint, metadata, new_versions)
        if thread_id:
            self._evict_old_checkpoints(thread_id)
        self._check_memory_warning()
        return result

    def put_writes(self, config, writes, task_id):
        """Put writes with capacity check and hard limit check."""
        self._check_capacity(config)
        self._check_memory_hard_limit()
        result = self._inner.put_writes(config, writes, task_id)
        self._check_memory_warning()
        return result

    def list(self, config, *, filter=None, before=None, limit=None):
        """List checkpoints - delegate to inner saver."""
        return self._inner.list(config, filter=filter, before=before, limit=limit)

    def get_next_version(self, current, channel):
        """Get next version - delegate to inner saver."""
        return self._inner.get_next_version(current, channel)

    def delete_thread(self, thread_id: str) -> None:
        """Delete thread - delegate to inner saver and reset memory warning."""
        result = self._inner.delete_thread(thread_id)
        memory_bytes = self.get_memory_estimate_bytes()
        memory_mb = memory_bytes / (1024 * 1024)
        if memory_mb < self._memory_warning_mb:
            self._memory_warning_logged = False
        return result

    def __getattr__(self, name):
        """Pass through any other attributes to the inner saver."""
        return getattr(self._inner, name)


class ResilientPostgresSaver:
    """
    A resilient wrapper around PostgresSaver that handles transient DB errors.

    Issue #2968: ResilientPostgresSaver with auto-retry for transient errors

    This wrapper implements the "Design for Failure" principle from Blueprint by:
    1. Catching transient DB errors (SSL closed, connection reset, etc.)
    2. Retrying failed operations with exponential backoff
    3. Requesting fresh connections from the pool on retry
    4. Logging all retry attempts for observability
    5. Circuit breaker to fail-fast when DB is persistently unavailable (Dec 2025)

    Transient errors that trigger retry:
    - SSL connection has been closed unexpectedly
    - the connection is closed
    - server closed the connection unexpectedly
    - connection reset by peer
    - OperationalError with connection-related messages

    Non-transient errors (not retried):
    - Syntax errors
    - Constraint violations
    - Authentication failures
    - Permission denied

    Circuit Breaker (Dec 2025 fix):
        When consecutive checkpoint failures exceed the threshold, the circuit
        breaker opens and all subsequent operations fail immediately with
        ResilientPostgresSaverCircuitOpen. This prevents:
        1. Memory buildup from accumulated LangGraph state/writes waiting to flush
        2. Prolonged failure storms that exhaust worker memory
        3. Wasted retry attempts when DB is clearly unavailable
    """

    # Transient error patterns that should trigger retry
    # These patterns are based on actual Sentry errors observed in production
    TRANSIENT_ERROR_PATTERNS = [
        "ssl connection has been closed",
        "the connection is closed",
        "connection is closed",
        "server closed the connection",
        "connection reset by peer",
        "connection timed out",
        "could not connect to server",
        "consuming input failed",
        "pipeline [bad]",  # psycopg Pipeline [BAD] state - exact match to avoid false positives
        "pool is closed",  # psycopg_pool PoolClosed - occurs when pool reset races with checkpoint ops
        "pool is already closed",  # Catches exact match (compound check below handles pool name variants)
    ]

    # Default circuit breaker threshold: after this many consecutive failures, fail fast
    # This prevents memory buildup during prolonged DB outages
    # Can be overridden via __init__ parameter for different environments
    DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 3

    # Connection-lost error patterns that should trigger pool reset
    # These are more severe than general transient errors and indicate the pool may be poisoned
    CONNECTION_LOST_PATTERNS = [
        "ssl connection has been closed",
        "the connection is closed",
        "connection is closed",
        "server closed the connection",
        "connection reset by peer",
        "pipeline [bad]",
        "pool is closed",  # psycopg_pool PoolClosed - pool was reset by another operation
        "pool is already closed",  # Catches exact match (compound check below handles pool name variants)
    ]

    # Default retry log sample rate: log every Nth retry (1 = log all)
    # Can be overridden via settings.checkpoint_retry_log_sample_rate
    DEFAULT_RETRY_LOG_SAMPLE_RATE = 1

    def __init__(
        self,
        inner_saver,
        max_retries: int = 3,
        base_delay: float = 0.5,
        circuit_breaker_threshold: int = 3,
        inner_factory: Optional[Callable] = None,
        retry_log_sample_rate: int = 1,
    ):
        """
        Initialize ResilientPostgresSaver.

        Args:
            inner_saver: The underlying PostgresSaver instance (already configured with pool)
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 0.5)
            circuit_breaker_threshold: Number of consecutive failures before circuit opens
                                       (default: 3). Set higher for environments with
                                       frequent transient errors.
            inner_factory: Optional callable that returns a new PostgresSaver instance.
                          Used to recreate the inner saver after pool reset on connection
                          lost errors. If not provided, pool reset will still occur but
                          the inner saver will not be recreated.
            retry_log_sample_rate: Sample rate for retry warning logs (default: 1 = log all).
                                   Set to N to log every Nth retry. First and last retries
                                   are always logged regardless of this setting. (Issue #3109)

        Note: The inner_saver already receives the ConnectionPool directly, so each
        checkpoint operation borrows a connection per-operation. This wrapper adds
        retry logic on top of that - if a transient error occurs, the next retry
        will naturally get a fresh connection from the pool.

        OOM Fix (Dec 2025):
            When connection-lost errors occur, the pool may contain poisoned connections
            that hold memory. If inner_factory is provided, the pool will be reset and
            the inner saver recreated to ensure the next retry uses a fresh pool.
        """
        self._inner = inner_saver
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._inner_factory = inner_factory
        self._retry_log_sample_rate = max(1, retry_log_sample_rate)
        # Circuit breaker state (per-instance, not global)
        # This tracks consecutive failures within a single job/workflow
        self._consecutive_failures = 0
        self._circuit_open = False
        # Rate-limited logging state (Issue #3109)
        # Tracks retry attempts for log sampling to reduce noise during outages
        self._total_retry_attempts = 0
        self._retry_log_count = 0

    @staticmethod
    def _is_pool_closed_with_name(error_str: str) -> bool:
        """
        Check if error matches pool closed patterns with variable pool name.

        psycopg_pool emits two different error message formats:
        1. "the pool 'pool-1' is closed" - PoolClosed exception
        2. "the pool 'pool-1' is already closed" - PoolClosed exception (different code path)

        This compound check handles both production error formats where the pool name
        varies. Using a compound check avoids false positives from generic patterns
        like "connection is already closed" or "file handle is already closed".

        Assumptions & Limitations:
        - Only matches single-quote format: "the pool '<name>' is [already] closed"
        - Double-quote variants (e.g., 'the pool "pool-1" is closed') are NOT matched
        - Other quote/format variants are tracked in GitHub issue #3117
        - Exception type classification (PoolClosed) is tracked in GitHub issue #3108

        Args:
            error_str: Lowercase string representation of the error

        Returns:
            True if this is a pool-closed error with variable pool name
        """
        if "the pool '" not in error_str:
            return False
        # Match both "' is closed" and "' is already closed" variants
        return "' is closed" in error_str or "' is already closed" in error_str

    def _is_transient_error(self, error: Exception) -> bool:
        """Check if an error is transient and should be retried."""
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Check for known transient error patterns
        for pattern in self.TRANSIENT_ERROR_PATTERNS:
            if pattern in error_str:
                return True

        # Check for pool closed with variable pool name (e.g., "the pool 'pool-1' is closed")
        if self._is_pool_closed_with_name(error_str):
            return True

        # Check for psycopg-specific transient errors
        if "OperationalError" in error_type or "InterfaceError" in error_type:
            return True

        return False

    def _is_connection_lost_error(self, error_str: str) -> bool:
        """
        Check if an error indicates connection loss that should trigger pool reset.

        OOM Fix (Dec 2025): Connection-lost errors indicate the pool may contain
        poisoned connections. These are more severe than general transient errors
        and warrant resetting the entire pool.

        Args:
            error_str: Lowercase string representation of the error

        Returns:
            True if this is a connection-lost error that should trigger pool reset
        """
        for pattern in self.CONNECTION_LOST_PATTERNS:
            if pattern in error_str:
                return True

        # Check for pool closed with variable pool name (e.g., "the pool 'pool-1' is closed")
        if self._is_pool_closed_with_name(error_str):
            return True

        return False

    def _should_log_retry(self, is_first: bool, is_last: bool) -> bool:
        """
        Determine if this retry attempt should be logged based on sampling rate.

        Issue #3109: Rate-limited logging for repeated transient errors.
        During prolonged outages, each retry generates a log entry which can
        overwhelm log systems and make it harder to identify root causes.

        This method implements sampling: log every Nth retry, but always log
        the first and last attempts for visibility.

        Note: This is a pure function with no side effects. Counter increments
        are handled by the caller (_retry_with_backoff) before calling this method.

        Args:
            is_first: True if this is the first retry attempt
            is_last: True if this is the final retry attempt before exhaustion

        Returns:
            True if this retry should be logged, False to skip logging
        """
        # Always log first retry warning
        if is_first:
            return True

        # Always log last retry warning (before exhaustion)
        if is_last:
            return True

        # Sample based on configured rate
        # retry_log_count is 1-indexed (incremented before this call)
        if self._retry_log_sample_rate == 1:
            return True

        return self._retry_log_count % self._retry_log_sample_rate == 0

    def _reset_pool_and_inner(self) -> None:
        """
        Reset the connection pool and recreate the inner saver.

        OOM Fix (Dec 2025): When connection-lost errors occur, the pool may contain
        poisoned connections (Pipeline [BAD], Connection [BAD]) that hold memory.
        This method:
        1. Resets the global connection pool (closes old, creates new)
        2. Recreates the inner PostgresSaver using the factory (if provided)
        3. Forces garbage collection to release lingering connection objects

        This ensures the next retry attempt uses a completely fresh pool and saver.
        """
        logger.warning(
            "ResilientPostgresSaver: Resetting connection pool due to connection-lost error",
            extra={"operation": "resilient_postgres_saver", "action": "pool_reset"}
        )

        # Reset the global pool
        new_pool = _reset_postgres_pool()

        # Recreate the inner saver if factory is provided
        if self._inner_factory is not None and new_pool is not None:
            try:
                self._inner = self._inner_factory()
                logger.info(
                    "ResilientPostgresSaver: Inner saver recreated after pool reset",
                    extra={"operation": "resilient_postgres_saver", "action": "inner_recreated"}
                )
            except Exception as e:
                logger.error(
                    f"ResilientPostgresSaver: Failed to recreate inner saver: {e}",
                    extra={
                        "operation": "resilient_postgres_saver",
                        "action": "inner_recreate_failed",
                        "error": str(e)
                    }
                )
        # Note: gc.collect() is already called in _reset_postgres_pool(), no need to call again

    def _retry_with_backoff(self, operation_name: str, operation: Callable):
        """
        Execute an operation with retry and exponential backoff.

        Args:
            operation_name: Name of the operation (for logging)
            operation: A zero-argument callable to execute. Use a lambda to capture args.
                       IMPORTANT: Must be a lambda that resolves self._inner at call time,
                       not a bound method captured before the retry loop. This ensures
                       that after _reset_pool_and_inner() updates self._inner, subsequent
                       retries use the NEW inner saver.

        Returns:
            The result of the operation

        Raises:
            ResilientPostgresSaverCircuitOpen: If circuit breaker is open
            The last exception if all retries fail

        Memory Safety (Dec 2025 fix):
            This method avoids holding exception references across retry iterations.
            Exception objects in Python hold references to their traceback, which
            includes all local variables in the stack frames. If the exception
            contains large objects (like LangGraph state, checkpoint data), holding
            the reference would prevent garbage collection and cause memory buildup
            during failure storms.

            Key changes:
            1. time.sleep() is moved OUTSIDE the except block
            2. Exception traceback is cleared before sleep using traceback.clear_frames()
            3. Exception reference is deleted before sleep
            4. Pool is reset on connection-lost errors to release poisoned connections

        Circuit Breaker (Dec 2025 fix):
            After CIRCUIT_BREAKER_THRESHOLD consecutive operation failures, the
            circuit breaker opens and all subsequent operations fail immediately.
            This prevents memory buildup during prolonged DB outages.

        Pool Reset (Dec 2025 fix):
            On connection-lost errors (Pipeline [BAD], SSL closed, etc.), the pool
            is reset and the inner saver is recreated to ensure the next retry uses
            fresh connections. The operation lambda resolves self._inner on each call,
            so the retry will use the newly created inner saver.
        """
        # Check circuit breaker BEFORE attempting operation
        if self._circuit_open:
            logger.error(
                f"ResilientPostgresSaver: Circuit breaker OPEN, failing fast for {operation_name}",
                extra={
                    "operation": "resilient_postgres_saver",
                    "checkpoint_operation": operation_name,
                    "circuit_breaker": "open",
                    "consecutive_failures": self._consecutive_failures,
                }
            )
            raise ResilientPostgresSaverCircuitOpen(
                f"Circuit breaker open after {self._consecutive_failures} consecutive failures. "
                f"DB appears to be unavailable. Failing fast to prevent memory buildup."
            )

        for attempt in range(self._max_retries + 1):
            # Variables to track retry state OUTSIDE the except block
            # This prevents holding exception references during sleep
            should_retry = False
            delay = 0.0
            is_connection_lost = False

            try:
                result = operation()
                # Success! Reset consecutive failure counter
                self._consecutive_failures = 0
                return result
            except Exception as e:
                # Capture error info as strings BEFORE any potential re-raise
                # This avoids holding the exception object (and its traceback) in memory
                error_str = str(e)
                error_str_lower = error_str.lower()
                error_type = type(e).__name__
                # Sanitize error string to mask sensitive data (Issue #3107)
                # This prevents PostgreSQL DSNs, passwords, and other secrets from being logged
                # Wrap in try/except to ensure masking failure doesn't break retry/failover logic
                masking_failed = False
                try:
                    sanitized_error = mask_sensitive_data(error_str)
                except Exception:
                    # Fallback to original error string if masking fails
                    # This ensures retry/failover logic is not affected by masking issues
                    sanitized_error = error_str
                    masking_failed = True

                if not self._is_transient_error(e):
                    # Non-transient error, don't retry
                    logger.error(
                        f"ResilientPostgresSaver: Non-transient error in {operation_name}, not retrying. "
                        f"error_type={error_type} error={sanitized_error[:200]}",
                        extra={
                            "operation": "resilient_postgres_saver",
                            "checkpoint_operation": operation_name,
                            "error": sanitized_error,
                            "error_type": error_type,
                            "attempt": attempt + 1,
                            "masking_failed": masking_failed,
                        }
                    )
                    raise

                if attempt < self._max_retries:
                    # Calculate delay with exponential backoff
                    delay = self._base_delay * (2 ** attempt)
                    should_retry = True
                    is_connection_lost = self._is_connection_lost_error(error_str_lower)

                    # Issue #3109: Track retry attempts for metrics and sampling
                    # These counters are always incremented, even when log is sampled out
                    self._total_retry_attempts += 1
                    self._retry_log_count += 1

                    # Issue #3109: Rate-limited logging to reduce noise during outages
                    # Always log first and last retry warnings; sample intermediate retries
                    is_first_retry = (attempt == 0)
                    is_last_retry = (attempt == self._max_retries - 1)
                    if self._should_log_retry(is_first_retry, is_last_retry):
                        logger.warning(
                            f"ResilientPostgresSaver: Transient error in {operation_name}, "
                            f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self._max_retries + 1}). "
                            f"error_type={error_type} error={sanitized_error[:200]}",
                            extra={
                                "operation": "resilient_postgres_saver",
                                "checkpoint_operation": operation_name,
                                "error": sanitized_error,
                                "error_type": error_type,
                                "attempt": attempt + 1,
                                "max_retries": self._max_retries + 1,
                                "delay_seconds": delay,
                                "is_connection_lost": is_connection_lost,
                                "masking_failed": masking_failed,
                                "total_retry_attempts": self._total_retry_attempts,
                                "log_sampled": self._retry_log_sample_rate > 1,
                            }
                        )

                    # OOM Fix: Clear exception traceback BEFORE exiting except block
                    # This releases all local variables held in the traceback frames
                    if e.__traceback__ is not None:
                        traceback.clear_frames(e.__traceback__)
                    del e

                    # DO NOT sleep here - sleep is moved outside except block
                else:
                    # All retries exhausted - update circuit breaker state
                    self._consecutive_failures += 1

                    # Check if we should open the circuit breaker
                    if self._consecutive_failures >= self._circuit_breaker_threshold:
                        self._circuit_open = True
                        logger.error(
                            f"ResilientPostgresSaver: Circuit breaker OPENED after "
                            f"{self._consecutive_failures} consecutive failures",
                            extra={
                                "operation": "resilient_postgres_saver",
                                "checkpoint_operation": operation_name,
                                "circuit_breaker": "opened",
                                "consecutive_failures": self._consecutive_failures,
                                "threshold": self._circuit_breaker_threshold,
                            }
                        )

                    # Log and raise directly instead of storing exception
                    logger.error(
                        f"ResilientPostgresSaver: All retries exhausted for {operation_name}. "
                        f"error_type={error_type} error={sanitized_error[:200]}",
                        extra={
                            "operation": "resilient_postgres_saver",
                            "checkpoint_operation": operation_name,
                            "error": sanitized_error,
                            "error_type": error_type,
                            "total_attempts": self._max_retries + 1,
                            "consecutive_failures": self._consecutive_failures,
                            "masking_failed": masking_failed,
                        }
                    )
                    raise

            # OOM Fix: Sleep and pool reset OUTSIDE the except block
            # This ensures exception references are not held during sleep
            if should_retry:
                # Reset pool on connection-lost errors before sleeping
                if is_connection_lost:
                    self._reset_pool_and_inner()

                # Now safe to sleep - no exception references held
                time.sleep(delay)

    # Delegate all PostgresSaver methods with retry logic
    #
    # IMPORTANT (Dec 2025 fix): We use lambdas instead of passing self._inner.method directly.
    # This ensures that after _reset_pool_and_inner() updates self._inner, the retry loop
    # uses the NEW inner saver, not the old one that was captured when the method was called.
    # Without this, pool reset would be ineffective because retries would still use the old
    # (potentially poisoned) inner saver.

    def setup(self):
        """Setup checkpoint tables with retry."""
        return self._retry_with_backoff("setup", lambda: self._inner.setup())

    def get(self, config):
        """Get checkpoint with retry."""
        return self._retry_with_backoff("get", lambda: self._inner.get(config))

    def put(self, config, checkpoint, metadata, new_versions):
        """Put checkpoint with retry."""
        return self._retry_with_backoff(
            "put", lambda: self._inner.put(config, checkpoint, metadata, new_versions)
        )

    def put_writes(self, config, writes, task_id):
        """Put writes with retry."""
        return self._retry_with_backoff(
            "put_writes", lambda: self._inner.put_writes(config, writes, task_id)
        )

    def list(self, config, *, filter=None, before=None, limit=None):
        """List checkpoints with retry."""
        # Use default-arg binding to capture filter/before/limit at lambda creation time
        # This addresses reviewer concern about late-binding closure issues
        return self._retry_with_backoff(
            "list",
            lambda _cfg=config, _filter=filter, _before=before, _limit=limit: (
                self._inner.list(_cfg, filter=_filter, before=_before, limit=_limit)
            )
        )

    def get_tuple(self, config):
        """Get checkpoint tuple with retry."""
        return self._retry_with_backoff("get_tuple", lambda: self._inner.get_tuple(config))

    # Pass through any other attributes to the inner saver
    def __getattr__(self, name):
        return getattr(self._inner, name)


class DegradedPersistenceCheckpointer:
    """
    A failover checkpointer that implements 'soft landing' resilience.

    Blueprint Alignment:
        - Flow Controller v3: Fail-Fast Recovery (快速回復)
        - Safety Governor v2: Self-Governed / 自我修復
        - Telemetry v2: Observable degradation events

    When the primary checkpointer (PostgreSQL) fails at runtime, this wrapper
    automatically switches to a fallback checkpointer (MemorySaver) and marks
    the workflow as running in "degraded persistence" mode.

    Key Design Decisions:
        1. Sticky Degradation: Once degraded, ALL subsequent operations use fallback.
           This prevents "write to A, read from B" inconsistency that would cause
           agent logic errors (hallucinations).

        2. Loud Telemetry: Degradation events are logged at WARNING/ERROR level
           to ensure visibility in monitoring dashboards.

        3. MemorySaver Fallback: Uses in-memory storage (not Redis) to avoid
           additional complexity from RediSearch requirements on Upstash.

    Trade-offs:
        - Crash-recovery: Degraded workflows cannot resume from checkpoint after restart
        - Deterministic: Degradation events are logged for traceability (Telemetry v2)

    Configuration:
        - ENABLE_CHECKPOINT_FAILOVER: Feature flag to enable/disable (default: True)

    Usage:
        primary = get_postgres_checkpointer()
        fallback = MemorySaver()
        checkpointer = DegradedPersistenceCheckpointer(primary, fallback)
        app = create_orchestrator_graph(checkpointer=checkpointer)
    """

    # Transient error patterns that trigger failover to fallback checkpointer.
    # These patterns are matched against lowercased error messages.
    # Centralized here for maintainability and consistency across all methods.
    TRANSIENT_ERROR_PATTERNS = frozenset((
        "ssl connection has been closed",
        "the connection is closed",
        "connection is closed",
        "server closed the connection",
        "connection reset by peer",
        "connection timed out",
        "could not connect to server",
        "pipeline [bad]",
        "circuit breaker open",
        "all retries exhausted",
    ))

    def __init__(
        self,
        primary,
        fallback,
        trace_id: str = "unknown",
    ):
        """
        Initialize DegradedPersistenceCheckpointer.

        Args:
            primary: The primary checkpointer (typically ResilientPostgresSaver)
            fallback: The fallback checkpointer (typically MemorySaver)
            trace_id: Trace ID for logging context
        """
        self._primary = primary
        self._fallback = fallback
        self._trace_id = trace_id
        self._degraded = False
        self._degraded_since: Optional[str] = None
        self._degraded_operation: Optional[str] = None
        self._degraded_error: Optional[str] = None

    @property
    def is_degraded(self) -> bool:
        """Check if the checkpointer is in degraded mode."""
        return self._degraded

    def _maybe_failover(self, operation_name: str, error: Exception) -> None:
        """
        Handle failover to fallback checkpointer.

        This method implements sticky degradation: once triggered, all subsequent
        operations will use the fallback checkpointer.

        Loud Telemetry: Logs at WARNING level to ensure visibility.
        """
        if self._degraded:
            return

        self._degraded = True
        self._degraded_since = datetime.utcnow().isoformat()
        self._degraded_operation = operation_name
        # Sanitize error string to mask sensitive data (Issue #3107)
        # This prevents PostgreSQL DSNs, passwords, and other secrets from being logged
        # Wrap in try/except to ensure masking failure doesn't break failover logic
        error_str = str(error)
        masking_failed = False
        try:
            self._degraded_error = mask_sensitive_data(error_str)
        except Exception:
            # Fallback to original error string if masking fails
            # This ensures failover logic is not affected by masking issues
            self._degraded_error = error_str
            masking_failed = True

        logger.warning(
            f"CHECKPOINT DEGRADED: Primary checkpointer failed, switching to fallback. "
            f"trace_id={self._trace_id} operation={operation_name} error='{self._degraded_error}' "
            f"degraded_since={self._degraded_since}",
            extra={
                "operation": "degraded_persistence_checkpointer",
                "event": "checkpoint_degraded",
                "trace_id": self._trace_id,
                "failed_operation": operation_name,
                "error": self._degraded_error,
                "error_type": type(error).__name__,
                "degraded_since": self._degraded_since,
                "checkpointer_mode": "degraded",
                "masking_failed": masking_failed,
            }
        )

    def _is_transient_error(self, error: Exception) -> bool:
        """
        Check if an error is transient and should trigger failover.

        Args:
            error: The exception to check

        Returns:
            True if the error is transient (connection/SSL issues), False otherwise
        """
        if isinstance(error, ResilientPostgresSaverCircuitOpen):
            return True
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in self.TRANSIENT_ERROR_PATTERNS)

    def _execute_with_failover(self, operation_name: str, primary_op, fallback_op, *args, **kwargs):
        """
        Execute an operation with automatic failover on transient errors.

        If already degraded, uses fallback directly (sticky degradation).
        Otherwise, tries primary first and fails over on transient errors.
        """
        if self._degraded:
            return fallback_op(*args, **kwargs)

        try:
            return primary_op(*args, **kwargs)
        except Exception as e:
            if self._is_transient_error(e):
                self._maybe_failover(operation_name, e)
                return fallback_op(*args, **kwargs)
            else:
                raise

    def setup(self):
        """Setup checkpoint tables with failover."""
        if self._degraded:
            return self._fallback.setup()

        try:
            return self._primary.setup()
        except Exception as e:
            self._maybe_failover("setup", e)
            return self._fallback.setup()

    def get(self, config):
        """Get checkpoint with failover."""
        return self._execute_with_failover(
            "get",
            lambda c: self._primary.get(c),
            lambda c: self._fallback.get(c),
            config
        )

    def get_tuple(self, config):
        """Get checkpoint tuple with failover."""
        return self._execute_with_failover(
            "get_tuple",
            lambda c: self._primary.get_tuple(c),
            lambda c: self._fallback.get_tuple(c),
            config
        )

    def put(self, config, checkpoint, metadata, new_versions):
        """Put checkpoint with failover."""
        return self._execute_with_failover(
            "put",
            lambda c, cp, m, nv: self._primary.put(c, cp, m, nv),
            lambda c, cp, m, nv: self._fallback.put(c, cp, m, nv),
            config, checkpoint, metadata, new_versions
        )

    def put_writes(self, config, writes, task_id):
        """Put writes with failover."""
        return self._execute_with_failover(
            "put_writes",
            lambda c, w, t: self._primary.put_writes(c, w, t),
            lambda c, w, t: self._fallback.put_writes(c, w, t),
            config, writes, task_id
        )

    def list(self, config, *, filter=None, before=None, limit=None):
        """List checkpoints with failover."""
        return self._execute_with_failover(
            "list",
            lambda c, **kw: self._primary.list(c, **kw),
            lambda c, **kw: self._fallback.list(c, **kw),
            config, filter=filter, before=before, limit=limit
        )

    def get_next_version(self, current, channel):
        """Get next version - delegate to active checkpointer."""
        if self._degraded:
            return self._fallback.get_next_version(current, channel)
        return self._primary.get_next_version(current, channel)

    def __getattr__(self, name):
        """Pass through any other attributes to the active checkpointer."""
        if self._degraded:
            return getattr(self._fallback, name)
        return getattr(self._primary, name)


def _get_validated_int_setting(
    setting_name: str,
    default: int,
    min_value: int = 1,
    trace_id: str = "unknown",
    fallback_to_default_on_invalid: bool = False,
) -> int:
    """
    Get and validate an integer setting with boundary checks.

    Issue #3181: Config Boundary Validation for OOM Protection (Dec 2025)

    This helper function:
    1. Gets the setting value from settings object
    2. Converts to int (falls back to default on failure)
    3. For values below min_value:
       - If fallback_to_default_on_invalid=True: returns default (safer for memory limits)
       - Otherwise: clamps to min_value (for count-based settings)
    4. Logs a warning when values are corrected

    Args:
        setting_name: Name of the setting attribute on settings object
        default: Default value if setting is missing or invalid
        min_value: Minimum allowed value (values below this trigger correction)
        trace_id: Trace ID for logging context
        fallback_to_default_on_invalid: If True, invalid values fallback to default
            instead of clamping to min_value. Use True for memory limits where
            clamping to 1MB would be dangerous.

    Returns:
        Validated integer value, guaranteed to be >= min_value
    """
    raw_value = getattr(settings, setting_name, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid {setting_name} value '{raw_value}', using default {default}. "
            f"trace_id={trace_id}",
            extra={
                "operation": "get_degraded_persistence_checkpointer",
                "event": "config_validation_fallback",
                "trace_id": trace_id,
                "setting_name": setting_name,
                "raw_value": str(raw_value),
                "default_value": default,
            }
        )
        return default

    if value < min_value:
        if fallback_to_default_on_invalid:
            logger.warning(
                f"Config {setting_name}={value} is invalid (below {min_value}), "
                f"using default {default}. trace_id={trace_id}",
                extra={
                    "operation": "get_degraded_persistence_checkpointer",
                    "event": "config_validation_fallback",
                    "trace_id": trace_id,
                    "setting_name": setting_name,
                    "original_value": value,
                    "default_value": default,
                    "min_value": min_value,
                }
            )
            return default
        else:
            logger.warning(
                f"Config {setting_name}={value} is below minimum {min_value}, "
                f"clamping to {min_value}. trace_id={trace_id}",
                extra={
                    "operation": "get_degraded_persistence_checkpointer",
                    "event": "config_validation_clamped",
                    "trace_id": trace_id,
                    "setting_name": setting_name,
                    "original_value": value,
                    "clamped_value": min_value,
                    "min_value": min_value,
                }
            )
            return min_value

    return value


def get_degraded_persistence_checkpointer(
    primary,
    trace_id: str = "unknown",
):
    """
    Factory function to create a DegradedPersistenceCheckpointer.

    This function wraps the primary checkpointer with automatic failover
    to OOMProtectedMemorySaver when ENABLE_CHECKPOINT_FAILOVER is True.

    Issue #3027: The fallback MemorySaver is now wrapped with OOMProtectedMemorySaver
    to prevent OOM conditions when many workflows degrade simultaneously.

    Args:
        primary: The primary checkpointer (typically ResilientPostgresSaver)
        trace_id: Trace ID for logging context

    Returns:
        DegradedPersistenceCheckpointer if failover is enabled, otherwise primary
    """
    if not settings.enable_checkpoint_failover:
        logger.info(
            f"Checkpoint failover disabled, using primary checkpointer only trace_id={trace_id}",
            extra={
                "operation": "get_degraded_persistence_checkpointer",
                "trace_id": trace_id,
                "failover_enabled": False,
            }
        )
        return primary

    # Issue #3027 & #3181: Get validated config values with boundary checks
    max_workflows = _get_validated_int_setting(
        "max_degraded_workflows_per_worker",
        default=100,
        min_value=1,
        trace_id=trace_id,
    )

    # Memory settings use fallback_to_default_on_invalid=True because clamping
    # to 1MB would be dangerous (almost immediately trigger hard limit)
    memory_warning_mb = _get_validated_int_setting(
        "degraded_checkpoint_memory_warning_mb",
        default=512,
        min_value=1,
        trace_id=trace_id,
        fallback_to_default_on_invalid=True,
    )

    memory_hard_limit_mb = _get_validated_int_setting(
        "degraded_checkpoint_memory_hard_limit_mb",
        default=1024,
        min_value=1,
        trace_id=trace_id,
        fallback_to_default_on_invalid=True,
    )

    max_checkpoints_per_thread = _get_validated_int_setting(
        "degraded_checkpoint_max_per_thread",
        default=10,
        min_value=1,
        trace_id=trace_id,
    )

    inner_saver = MemorySaver()
    fallback = OOMProtectedMemorySaver(
        inner_saver=inner_saver,
        max_workflows=max_workflows,
        memory_warning_mb=memory_warning_mb,
        memory_hard_limit_mb=memory_hard_limit_mb,
        max_checkpoints_per_thread=max_checkpoints_per_thread,
        trace_id=trace_id,
    )

    logger.info(
        f"Checkpoint failover enabled, wrapping with DegradedPersistenceCheckpointer trace_id={trace_id}",
        extra={
            "operation": "get_degraded_persistence_checkpointer",
            "trace_id": trace_id,
            "failover_enabled": True,
            "primary_type": type(primary).__name__,
            "fallback_type": "OOMProtectedMemorySaver",
            "max_degraded_workflows": max_workflows,
            "memory_warning_mb": memory_warning_mb,
            "memory_hard_limit_mb": memory_hard_limit_mb,
            "max_checkpoints_per_thread": max_checkpoints_per_thread,
        }
    )

    return DegradedPersistenceCheckpointer(
        primary=primary,
        fallback=fallback,
        trace_id=trace_id,
    )


@contextlib.contextmanager
def postgres_checkpointer_context():
    """
    DEPRECATED: Use get_postgres_checkpointer() instead for better resilience.

    This context manager is kept for backward compatibility but now simply
    delegates to get_postgres_checkpointer().

    The old approach of holding a single connection for the entire workflow
    was vulnerable to network hiccups causing "Pipeline [BAD]" errors.
    The new approach uses per-operation connection borrowing.
    """
    checkpointer = get_postgres_checkpointer()
    if checkpointer is None:
        yield None
        return

    try:
        yield checkpointer
    except Exception as e:
        logger.error(
            f"Error in PostgreSQL checkpointer context: {e}",
            extra={
                "operation": "postgres_checkpointer_context",
                "error": str(e)
            }
        )
        raise


def get_checkpointer():
    """
    Factory function to create the appropriate checkpointer based on configuration.

    IMPORTANT: For PostgreSQL checkpointer with connection pooling, prefer using
    postgres_checkpointer_context() instead of this function to ensure proper
    connection lifecycle management.

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

    Fix (Dec 2025) - Connection Pooling:
        Previous implementation created a new psycopg connection per job without cleanup,
        causing connection leaks and Supabase limit exhaustion. This led to:
        - "the connection is closed" errors (psycopg.Pipeline [BAD] state)
        - "invalid memory alloc request size" errors (corrupted protocol state)
        - Health check timeouts (DB connection exhaustion)

        New implementation: For PostgreSQL, use postgres_checkpointer_context() instead.
        This function now only returns Redis or Memory checkpointers for backward compatibility.
    """
    import os

    # For PostgreSQL, we now recommend using postgres_checkpointer_context()
    # This function skips PostgreSQL to avoid connection leaks
    use_postgres = settings.use_postgres_checkpointer
    if use_postgres:
        logger.info(
            "PostgreSQL checkpointer configured - use postgres_checkpointer_context() for proper connection management",
            extra={"operation": "get_checkpointer"}
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


def _get_workflow_config(trace_id: str) -> dict:
    """Creates the config dictionary for a LangGraph workflow invocation.

    Centralizes workflow configuration to ensure consistent settings across all
    orchestrator entry points (run_orchestrator, run_review_follow_up_orchestrator,
    run_internal_review_orchestrator).

    Args:
        trace_id: Unique identifier for this workflow execution (used as thread_id)

    Returns:
        Config dict with thread_id and recursion_limit for LangGraph invoke()

    Blueprint: Flow Controller v3 Fail-Fast Recovery (Step Cap protection)
    """
    return {
        "configurable": {"thread_id": trace_id},
        "recursion_limit": settings.orchestrator_recursion_limit,
    }


def prune_messages_reducer(
    old: Sequence[BaseMessage],
    new: Sequence[BaseMessage]
) -> list[BaseMessage]:
    """Custom reducer that appends new messages then prunes to bounded size.

    This reducer solves the OOM problem caused by unbounded message accumulation
    in LangGraph's AgentState. Unlike operator.add which only appends, this reducer
    enforces a maximum message window size after each update.

    Pruning Strategy:
        - Keep the FIRST SystemMessage (system prompt, never changes)
        - Keep the last K non-system messages (configurable via MESSAGE_WINDOW_SIZE)
        - Prune oldest non-system messages when limit exceeded

    CTO Directive (Issue #3027):
        - This is Global Logic, applies to both Postgres and MemorySaver modes
        - Prevents Postgres from storing 1GB+ state
        - Prevents MemorySaver from causing OOM in degraded mode

    Blueprint: Safety Governor v2 (Self-Governed/Self-Healing)

    Contract Assumption:
        This reducer assumes LangGraph passes incremental deltas in `new` (standard
        reducer contract). If a node mistakenly returns full state instead of delta,
        the reducer still produces bounded output but with temporary duplication.

    Breaking Change Notice:
        This change modifies AgentState.messages behavior. Old messages beyond the
        window are permanently pruned. To rollback: set MESSAGE_WINDOW_SIZE=200 or
        revert this commit. For audit/analytics, use [STATE_PRUNED] telemetry logs.

    Args:
        old: Existing messages in state
        new: New messages to append (incremental delta from node)

    Returns:
        Pruned list of messages (SystemMessage + last K non-system messages)
    """
    combined = list(old) + list(new)

    first_system_msg = None
    other_msgs = []
    for m in combined:
        if isinstance(m, SystemMessage):
            if first_system_msg is None:
                first_system_msg = m
        else:
            other_msgs.append(m)

    first_system = [first_system_msg] if first_system_msg else []

    window_size = settings.message_window_size

    if len(other_msgs) > window_size:
        pruned_count = len(other_msgs) - window_size
        other_msgs = other_msgs[-window_size:]
        current_size = len(first_system) + len(other_msgs)
        logger.info(
            f"[STATE_PRUNED] Pruned {pruned_count} messages. "
            f"Current size: {current_size}"
        )

    return first_system + other_msgs


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

    EPIC B Phase B-3 New Fields (Diff-aware review for commit pinning):
        diff_head_sha: Optional[str] - PR head commit SHA (40-char hex, case-insensitive)
        diff_content: Optional[str] - Sanitized diff content (max 100KB per DIFF_MAX_SIZE_BYTES)
        diff_truncated: Optional[bool] - Whether diff was truncated due to size limits

    Issue #3259: diff_head_sha Contract Definition
    -----------------------------------------------
    Source: Captured from GitHub API via get_pr_diff() -> pr.head.sha
    Format: 40-character hex string (case-insensitive), or None if unavailable
    Availability: Best-effort; may be None if get_pr_diff() fails or PR fetch fails

    Usage by path:
    - Inline comments path: MUST use diff_head_sha from get_pr_diff() to ensure
      line positions align with the diff. If None, commit pinning is disabled
      (commit_id=None) to avoid 422 errors from line drift.
    - Summary-only / file-level fallback path: Can use any valid PR head SHA
      since no line positions are involved. Safe to use fallback if available.
    - Redis dedup: Uses diff_head_sha[:12] as part of dedup key. If None,
      dedup is skipped (fail-open) per _check_review_already_posted().

    Important: diff_head_sha represents the PR head at "review time" (when
    get_pr_diff was called), NOT the current/latest head. Do not confuse with
    a "live" head SHA which may have changed due to new commits.
    """
    messages: Annotated[list[BaseMessage], prune_messages_reducer]
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
    # EPIC B Phase B-3: Diff-aware review fields for commit pinning
    # Set by reviewer_node, read by publisher_node. See docstring for field details.
    diff_head_sha: Optional[str]
    diff_content: Optional[str]
    diff_truncated: Optional[bool]
    # EPIC B Phase B-6: Reviewer -> Router interface (Issue #3130)
    # Set by reviewer_node, read by Router for routing decisions.
    # Contains verdict, severity, summary, blocker_count, and data quality signals.
    # See core/routing/review_outcome.py for schema definition.
    review_outcome: Optional[dict]
    # EPIC C Phase C-5: HITL Wiring (Issue #3155)
    # Set by hitl_gate_node after human approval is received via Command(resume=True).
    # Reset to False by finalizer_node to prevent state leakage between executions.
    # CTO Directive: Router DECIDES (requires_hitl_approval=True), Orchestrator EXECUTES (interrupt).
    hitl_approved: bool
    # Issue #3366: CI Failure Reflex Integration
    # Set by run_orchestrator() when CI failure webhook triggers auto-fix flow.
    # When True, workflow routes directly to fixer_node for auto-fix without planner.
    ci_failure_trigger: Optional[bool]
    # Issue #3529: CI Failure Context for AutoFixer
    # Set by run_orchestrator() when CI failure webhook provides structured error context.
    # Contains CiFailureContext.to_dict() with failed_check_name, conclusion, pr_number,
    # head_sha, head_branch, logs_url, error_summary, check_run_id.
    # Used by fixer_integration.py to use CI evidence directly instead of ReviewerAgent.
    ci_failure_context: Optional[dict]
    # Issue #3541: CI Failure Fast Path Consumed Flag
    # Set by ci_monitor_node on first pass when ci_failure_trigger=True.
    # Prevents infinite loop: after fixer applies fix and routes back to ci_monitor,
    # this flag ensures ci_monitor makes actual API call to check real CI status
    # instead of forcing ci_state="failure" again.
    ci_failure_fast_path_consumed: Optional[bool]
    # Issue #3640: Escalation Ladder Hard Cap State Tracking
    # Tracks the number of tier escalations for cost optimization.
    # Used by RoutingEngine.select_model() to enforce max_escalations limit.
    # Incremented when a task escalates to a higher tier (lower tier number).
    # Default: 0 (no escalations yet)
    escalation_count: int
    # Issue #3693: review_files for D-1b GeneralCoder multi-file support
    # Set by run_orchestrator() from ci_error_file_paths (extracted from GitHub Annotations API)
    # Used by GeneralCoder to know which files to fix in multi-file CI failures.
    # Format: List of dicts with "path" key, e.g., [{"path": "src/foo.py"}, {"path": "src/bar.py"}]
    # IMPORTANT: This field must be defined in AgentState for LangGraph to properly propagate it.
    review_files: Optional[list]
    # Issue #3578: SSOT Telemetry Schema v3 - Span hierarchy tracking
    # Set by node_metrics decorator when ENABLE_SSOT_TELEMETRY=true.
    # Used to establish parent-child relationships between node spans.
    # Each node creates a child span with this as parent_span_id, then updates this field.
    current_span_id: Optional[str]
    # PR #3741: Loop Protection State Flag
    # Set by fixer_node when AutoFixLoopProtection triggers (max retries exceeded).
    # Read by should_proceed_after_fixer to route to finalizer instead of ci_monitor.
    # CRITICAL: This field MUST be defined in AgentState for LangGraph to properly
    # propagate it between nodes. Without this definition, the flag may be lost.
    loop_protection_triggered: Optional[bool]


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
            model="qwen-plus"
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

    Issue #2918: Pass source_pr_number to execute() for more precise dedup key generation.
    The pr_number in state comes from webhook context (resource_id) and represents
    the source PR that triggered this workflow.
    """
    from graph import execute

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    goal = state["goal"]
    repo = state["repo"]
    current_step = state["current_step"]
    plan = state["plan"]
    # Issue #2918: Extract source PR number from state for dedup key generation
    # pr_number comes from webhook context (resource_id) via run_orchestrator()
    # Defensive type handling: explicitly convert to int and validate
    raw_pr_number = state.get("pr_number")
    source_pr_number: Optional[int] = None
    if raw_pr_number:
        try:
            num = int(raw_pr_number)
            if num > 0:
                source_pr_number = num
        except (ValueError, TypeError):
            logger.warning(f"[Executor] Could not parse pr_number from state: {raw_pr_number}", extra={
                "operation": "executor",
                "trace_id": trace_id,
                "raw_pr_number": str(raw_pr_number),
            })

    metrics.record_node_start("executor", trace_id)

    # Defensive bounds check: Extract step name before try block to prevent secondary
    # IndexError in exception handler if current_step is out of bounds
    current_step_name = plan[current_step] if current_step < len(plan) else "unknown"
    logger.info(f"[Executor] Executing step {current_step + 1}/{len(plan)} source_pr_number={source_pr_number}", extra={
        "operation": "executor",
        "trace_id": trace_id,
        "step": current_step_name,
        "source_pr_number": source_pr_number,
    })

    success = True
    try:
        # Issue #2918: Pass source_pr_number for more precise dedup key generation
        pr_url, ci_state, trace_id = execute(
            goal, repo, trace_id=trace_id, source_pr_number=source_pr_number
        )

        state["pr_url"] = pr_url
        state["ci_state"] = ci_state
        state["error"] = None
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Executed step: {current_step_name}. PR created: {pr_url}")
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
        logger.error(f"[Executor] Step failed: {error_msg}", exc_info=True, extra={
            "operation": "executor",
            "trace_id": trace_id,
            "error": error_msg
        })

        state["error"] = error_msg
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Error in step {current_step_name}: {error_msg}")
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

    ci_state = state.get("ci_state")
    ci_failure_trigger = state.get("ci_failure_trigger")

    if ci_state == "dry_run":
        logger.info("[CI Monitor] Dry run mode - skipping CI checks", extra={
            "operation": "ci_monitor",
            "trace_id": trace_id,
            "ci_state": ci_state
        })
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("ci_monitor", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Issue #3516: Fix CI failure fast path - skip API call when ci_failure_trigger=True
    # Previously required ci_state=="failure", but ci_state might be "pending" or other value
    # from _create_base_initial_state() before run_orchestrator() sets it to "failure".
    # The key insight: when ci_failure_trigger=True, we KNOW CI failed (from webhook),
    # so we should preserve that state and skip the API call that would overwrite it.
    #
    # Issue #3541: Make fast path one-shot to prevent infinite loop
    # After fixer applies fix and routes back to ci_monitor (via should_proceed_after_fixer),
    # we need to check real CI status to see if the fix worked. The consumed flag ensures
    # we only skip the API call on the FIRST pass, then do normal CI check on subsequent passes.
    fast_path_consumed = state.get("ci_failure_fast_path_consumed") is True
    if ci_failure_trigger and not fast_path_consumed:
        # Mark fast path as consumed so subsequent ci_monitor calls check real CI status
        state["ci_failure_fast_path_consumed"] = True
        # Ensure ci_state is "failure" for downstream router fast path
        if ci_state != "failure":
            logger.warning(
                f"[CI Monitor] CI failure trigger active but ci_state={ci_state}, "
                "forcing ci_state=failure for fast path (first pass)",
                extra={
                    "operation": "ci_monitor",
                    "trace_id": trace_id,
                    "ci_failure_trigger": ci_failure_trigger,
                    "original_ci_state": ci_state,
                    "fast_path_consumed": False,
                }
            )
            state["ci_state"] = "failure"
        else:
            logger.info(
                "[CI Monitor] CI failure trigger active with ci_state=failure, "
                "preserving state and skipping API call for fast path (first pass)",
                extra={
                    "operation": "ci_monitor",
                    "trace_id": trace_id,
                    "ci_failure_trigger": ci_failure_trigger,
                    "ci_state": ci_state,
                    "fast_path_consumed": False,
                }
            )
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_node_complete("ci_monitor", trace_id, success=True, latency_ms=latency_ms)
        return state

    # Issue #3541: Log when fast path was already consumed (post-fix CI check)
    if ci_failure_trigger and fast_path_consumed:
        logger.info(
            "[CI Monitor] CI failure trigger active but fast path already consumed, "
            "proceeding to check real CI status (post-fix verification)",
            extra={
                "operation": "ci_monitor",
                "trace_id": trace_id,
                "ci_failure_trigger": ci_failure_trigger,
                "fast_path_consumed": True,
            }
        )

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


def _attempt_senior_coder_plan(
    task_description: str,
    files_with_content: list,
    trace_id: str,
    state: Optional[AgentState] = None
) -> tuple[bool, Optional[dict], Optional[str]]:
    """Attempt to create an architecture plan using SeniorCoder.

    This implements D-2b: SeniorCoder integration into LangGraph orchestrator.
    SeniorCoder analyzes task complexity and creates an architecture spec
    before delegating to GeneralCoder for implementation.

    EPIC D Issue #3487: When SeniorCoder determines task complexity is too high
    (complexity abort), this function sets HITL flags on state to trigger
    human-in-the-loop approval gate.

    Args:
        task_description: Description of the fix task
        files_with_content: List of dicts with "path" and "content" keys
        trace_id: Trace ID for logging
        state: Optional AgentState for setting HITL flags on complexity abort

    Returns:
        Tuple of (should_proceed, spec_dict, message):
        - (True, spec_dict, message) if SeniorCoder created a valid plan
        - (False, None, message) if SeniorCoder aborted or failed

    Event Codes (greppable):
        [SENIOR_CODER_PLAN_ATTEMPT] - SeniorCoder planning started
        [SENIOR_CODER_PLAN_CREATED] - Plan created successfully
        [SENIOR_CODER_PLAN_ABORTED] - Task too complex, aborting
        [SENIOR_CODER_PLAN_FAILED] - Planning failed due to error
        [SENIOR_CODER_DISABLED] - Feature flag disabled
        [SENIOR_CODER_UNAVAILABLE] - Import/dependency failure
        [SENIOR_CODER_HITL_ESCALATION] - Complexity abort triggers HITL gate
    """
    if not settings.enable_senior_coder:
        logger.debug("[SENIOR_CODER_DISABLED] Feature flag disabled")
        return True, None, "SeniorCoder disabled, proceeding without plan"

    try:
        from coder.senior_coder import get_senior_coder
    except ImportError as e:
        logger.debug(f"[SENIOR_CODER_UNAVAILABLE] Import failed: {e}")
        return True, None, f"SeniorCoder not available: {e}"

    logger.info(
        f"[SENIOR_CODER_PLAN_ATTEMPT] Starting architecture planning. "
        f"file_count={len(files_with_content)}, trace_id={trace_id}"
    )

    try:
        senior_coder = get_senior_coder()
        spec = senior_coder.analyze_and_plan(
            task_description=task_description,
            files=files_with_content
        )

        if not spec.should_proceed:
            abort_reason = spec.abort_reason or "Task complexity too high"
            logger.info(
                f"[SENIOR_CODER_PLAN_ABORTED] {abort_reason}. "
                f"trace_id={trace_id}"
            )

            # EPIC D Issue #3487: Set HITL flags for complexity abort
            # Only trigger HITL for genuine complexity aborts, not system errors
            # Complexity abort is identified by:
            # 1. spec.should_proceed is False (checked above)
            # 2. abort_reason does NOT indicate a system error
            is_system_error = any(
                indicator.lower() in abort_reason.lower()
                for indicator in _SENIOR_CODER_SYSTEM_ERROR_INDICATORS
            )

            if state is not None and not is_system_error:
                # Reset hitl_approved to ensure this new HITL request is processed
                # (previous approval was for a different gate/reason)
                state["requires_hitl_approval"] = True
                state["hitl_approved"] = False
                state["hitl_reason"] = "senior_coder_complexity_abort"
                state["hitl_details"] = {
                    "version": "1.0",
                    "abort_reason": abort_reason,
                    "task_description": task_description,
                    "file_count": len(files_with_content),
                    "escalation_source": "SeniorCoder",
                }
                logger.info(
                    f"[SENIOR_CODER_HITL_ESCALATION] Complexity abort triggers HITL gate. "
                    f"abort_reason={abort_reason}, trace_id={trace_id}",
                    extra={
                        "operation": "senior_coder_hitl_escalation",
                        "trace_id": trace_id,
                        "event_code": "SENIOR_CODER_HITL_ESCALATION",
                        "abort_reason": abort_reason,
                    }
                )

            return False, None, f"SeniorCoder aborted: {abort_reason}"

        spec_dict = spec.to_dict()
        complexity = spec_dict.get("task_analysis", {}).get("complexity", "unknown")
        step_count = len(spec_dict.get("implementation_plan", []))

        logger.info(
            f"[SENIOR_CODER_PLAN_CREATED] Plan created. "
            f"complexity={complexity}, steps={step_count}, trace_id={trace_id}"
        )
        return True, spec_dict, f"Plan created with {step_count} steps"

    except Exception as e:
        logger.warning(
            f"[SENIOR_CODER_PLAN_FAILED] Planning failed: {e}. "
            f"trace_id={trace_id}"
        )
        return True, None, f"SeniorCoder planning failed: {e}"


def _attempt_senior_coder_review(
    task_description: str,
    spec_dict: Optional[dict],
    patches: list,
    trace_id: str
) -> tuple[bool, Optional[str]]:
    """Attempt to review GeneralCoder's implementation using SeniorCoder.

    This implements D-2b: SeniorCoder review step.
    SeniorCoder reviews the patches before commit to ensure quality.

    Args:
        task_description: Original task description
        spec_dict: Architecture spec from planning phase (may be None)
        patches: List of patch dicts from GeneralCoder
        trace_id: Trace ID for logging

    Returns:
        Tuple of (approved, message):
        - (True, message) if review approved or skipped
        - (False, message) if review rejected

    Event Codes (greppable):
        [SENIOR_CODER_REVIEW_ATTEMPT] - SeniorCoder review started
        [SENIOR_CODER_REVIEW_APPROVED] - Implementation approved
        [SENIOR_CODER_REVIEW_REJECTED] - Implementation rejected
        [SENIOR_CODER_REVIEW_FAILED] - Review failed due to error
        [SENIOR_CODER_REVIEW_SKIPPED] - Review skipped (no spec or disabled)
        [SENIOR_CODER_UNAVAILABLE] - Import/dependency failure
    """
    if not settings.enable_senior_coder:
        logger.debug("[SENIOR_CODER_REVIEW_SKIPPED] Feature flag disabled")
        return True, "SeniorCoder review skipped (disabled)"

    if spec_dict is None:
        logger.debug("[SENIOR_CODER_REVIEW_SKIPPED] No spec available for review")
        return True, "SeniorCoder review skipped (no spec)"

    try:
        from coder.senior_coder import get_senior_coder
    except ImportError as e:
        logger.debug(f"[SENIOR_CODER_UNAVAILABLE] Import failed: {e}")
        return True, f"SeniorCoder review skipped: {e}"

    logger.info(
        f"[SENIOR_CODER_REVIEW_ATTEMPT] Starting implementation review. "
        f"patch_count={len(patches)}, trace_id={trace_id}"
    )

    implementation = {
        "patches": [
            {
                "file_path": p.get("file_path", ""),
                "status": "patch_generated",
                "syntax_valid": p.get("syntax_valid", True)
            }
            for p in patches
        ],
        "total_files": len(patches),
        "all_syntax_valid": all(p.get("syntax_valid", True) for p in patches)
    }

    try:
        senior_coder = get_senior_coder()
        result = senior_coder.review_implementation(
            task_description=task_description,
            spec_dict=spec_dict,
            implementation=implementation
        )

        if result.approved:
            logger.info(
                f"[SENIOR_CODER_REVIEW_APPROVED] Implementation approved. "
                f"feedback={result.feedback[:100] if result.feedback else 'None'}... "
                f"trace_id={trace_id}"
            )
            return True, f"Review approved: {result.feedback}"
        else:
            changes_summary = ", ".join(result.required_changes[:3]) if result.required_changes else "None"
            feedback_truncated = result.feedback[:100] if result.feedback else "None"
            logger.info(
                f"[SENIOR_CODER_REVIEW_REJECTED] Implementation rejected. "
                f"required_changes={changes_summary}, "
                f"feedback={feedback_truncated}..., trace_id={trace_id}"
            )
            return False, f"Review rejected: {result.feedback}"

    except Exception as e:
        logger.warning(
            f"[SENIOR_CODER_REVIEW_FAILED] Review failed: {e}. "
            f"trace_id={trace_id}"
        )
        return True, f"SeniorCoder review failed: {e}"


# Required fields for a valid ArchitectureSpec (Design Doc Gate validation)
# These fields must be present and non-empty for the gate to pass
_DESIGN_DOC_REQUIRED_FIELDS = [
    "task_analysis",
    "architecture",
    "implementation_plan",
]


def _escalate_design_doc_gate_failure(
    state: AgentState,
    trace_id: str,
    hitl_reason: str,
    failure_reason: str,
    task_description: str,
    file_count: int,
    recommendation: str,
    log_message: str,
    extra_details: Optional[dict] = None,
) -> None:
    """Set HITL escalation flags for Design Doc Gate failure.

    This helper encapsulates the common HITL escalation logic for both
    missing spec and invalid spec cases, reducing code duplication.

    Issue #3750: [P3] Refactor Design Doc Gate HITL escalation logic

    Args:
        state: AgentState for setting HITL flags
        trace_id: Trace ID for logging
        hitl_reason: HITL reason code (e.g., "design_doc_gate_missing_spec")
        failure_reason: Human-readable failure reason for hitl_details
        task_description: Description of the task
        file_count: Number of files being processed
        recommendation: Recommendation message for hitl_details
        log_message: Message for the warning log
        extra_details: Optional additional fields for hitl_details
    """
    state["requires_hitl_approval"] = True
    state["hitl_approved"] = False
    state["hitl_reason"] = hitl_reason

    hitl_details = {
        "version": "1.0",
        "gate_failure_reason": failure_reason,
        "task_description": task_description,
        "file_count": file_count,
        "escalation_source": "DesignDocGate",
        "recommendation": recommendation,
    }
    if extra_details:
        hitl_details.update(extra_details)
    state["hitl_details"] = hitl_details

    # Extract failure type from hitl_reason for logging
    failure_type = hitl_reason.replace("design_doc_gate_", "")

    logger.warning(
        f"[DESIGN_DOC_GATE_HITL_ESCALATION] {log_message} trace_id={trace_id}",
        extra={
            "operation": "design_doc_gate_hitl_escalation",
            "trace_id": trace_id,
            "event_code": "DESIGN_DOC_GATE_HITL_ESCALATION",
            "failure_reason": failure_type,
            **(extra_details or {}),
        }
    )


def _validate_design_doc_gate(
    spec_dict: Optional[dict],
    trace_id: str,
    state: AgentState,
    task_description: str,
    file_count: int,
) -> tuple[bool, str]:
    """Validate Design Doc Gate - 強制架構審查 (Blueprint Section 4.1 Safety Governor v2).

    This gate ensures that GeneralCoder cannot proceed without a valid ArchitectureSpec
    from SeniorCoder. This implements mandatory architecture review as part of the
    Safety Governor v2 governance layer.

    Args:
        spec_dict: ArchitectureSpec dictionary from SeniorCoder planning phase
        trace_id: Trace ID for logging
        state: AgentState for setting HITL flags on gate failure
        task_description: Description of the task for HITL details
        file_count: Number of files being processed

    Returns:
        Tuple of (gate_passed, reason):
        - (True, reason) if gate passed (valid spec exists)
        - (False, reason) if gate failed (no spec or invalid spec)

    Event Codes (greppable):
        [DESIGN_DOC_GATE_PASS] - Gate passed, valid ArchitectureSpec exists
        [DESIGN_DOC_GATE_FAIL] - Gate failed, no valid ArchitectureSpec
        [DESIGN_DOC_GATE_HITL_ESCALATION] - Gate failure triggers HITL escalation
    """
    # Case 1: No spec_dict at all (SeniorCoder disabled or failed)
    if spec_dict is None:
        reason = "No ArchitectureSpec available (SeniorCoder may be disabled or failed)"

        # Use helper to set HITL escalation flags (Issue #3750 refactor)
        _escalate_design_doc_gate_failure(
            state=state,
            trace_id=trace_id,
            hitl_reason="design_doc_gate_missing_spec",
            failure_reason=reason,
            task_description=task_description,
            file_count=file_count,
            recommendation=(
                "GeneralCoder cannot proceed without architecture review. "
                "Please ensure SeniorCoder is enabled and functioning, or "
                "manually approve this task after reviewing the changes."
            ),
            log_message="Missing ArchitectureSpec triggers HITL gate.",
        )

        return False, reason

    # Case 2: spec_dict exists but may be invalid (missing required fields)
    missing_fields = []
    for field in _DESIGN_DOC_REQUIRED_FIELDS:
        if field not in spec_dict or not spec_dict[field]:
            missing_fields.append(field)

    if missing_fields:
        reason = f"ArchitectureSpec missing required fields: {', '.join(missing_fields)}"

        # Use helper to set HITL escalation flags (Issue #3750 refactor)
        _escalate_design_doc_gate_failure(
            state=state,
            trace_id=trace_id,
            hitl_reason="design_doc_gate_invalid_spec",
            failure_reason=reason,
            task_description=task_description,
            file_count=file_count,
            recommendation=(
                f"ArchitectureSpec is incomplete (missing: {', '.join(missing_fields)}). "
                "Please review the SeniorCoder output and ensure proper architecture "
                "planning before proceeding with implementation."
            ),
            log_message=f"Invalid ArchitectureSpec triggers HITL gate. missing_fields={missing_fields}",
            extra_details={"missing_fields": missing_fields},
        )

        return False, reason

    # Case 3: Valid spec_dict with all required fields
    complexity = spec_dict.get("task_analysis", {}).get("complexity", "unknown")
    step_count = len(spec_dict.get("implementation_plan", []))

    logger.info(
        f"[DESIGN_DOC_GATE_PASS] Valid ArchitectureSpec found. "
        f"complexity={complexity}, steps={step_count}, trace_id={trace_id}",
        extra={
            "operation": "design_doc_gate_pass",
            "trace_id": trace_id,
            "event_code": "DESIGN_DOC_GATE_PASS",
            "complexity": complexity,
            "step_count": step_count,
        }
    )

    return True, f"Valid ArchitectureSpec (complexity={complexity}, steps={step_count})"


def _attempt_general_coder_fix(
    state: AgentState,
    trace_id: str
) -> tuple[bool, Optional[str]]:
    """Attempt to fix using GeneralCoder for multi-file issues.

    This implements D-1b: GeneralCoder multi-file support (<=5 files).
    D-2b Enhancement: When ENABLE_SENIOR_CODER=True, SeniorCoder acts as
    supervisor with plan-execute-review pattern:
    1. SeniorCoder analyzes task and creates architecture spec
    2. GeneralCoder executes the fix based on the spec
    3. SeniorCoder reviews the implementation before commit

    GeneralCoder extends SimpleCoder with:
    1. Multi-file editing support (<=5 files)
    2. Import relationship understanding
    3. Atomic commits via commit_files()
    4. Per-file syntax validation

    Args:
        state: Current AgentState with review_outcome and file context
        trace_id: Trace ID for logging

    Returns:
        Tuple of (success, message):
        - (True, message) if GeneralCoder successfully applied fixes
        - (False, message) if GeneralCoder skipped or failed (fallback to SimpleCoder)

    Event Codes (greppable):
        [GENERAL_CODER_ATTEMPT] - GeneralCoder fix attempt started
        [GENERAL_CODER_GATE_FAIL] - Gate check failed, skipping GeneralCoder
        [GENERAL_CODER_SKIP] - GeneralCoder decided to skip (low confidence)
        [GENERAL_CODER_PATCH_APPLIED] - Patches successfully applied via GitHub API
        [GENERAL_CODER_PATCH_FAILED] - Patch application failed
        [GENERAL_CODER_DISABLED] - Feature flag disabled
        [SENIOR_CODER_SINGLE_FILE_CI_FAILURE] - Single file CI failure, SeniorCoder invoked
    """
    try:
        from coder.autofix_gate import is_autofix_allowed, is_senior_coder_required
        from coder.general_coder import get_general_coder, CoderStatus
        from core.agents import AgentInput
        from tools.github_api import get_repo, commit_files
    except ImportError as e:
        logger.info(f"[GENERAL_CODER_DISABLED] Import failed: {e}")
        return False, f"GeneralCoder not available: {e}"

    if not settings.enable_general_coder:
        logger.info("[GENERAL_CODER_DISABLED] Feature flag disabled")
        return False, "GeneralCoder feature flag disabled"

    # Issue #3366: Use smart gate logic for CI failure scenarios
    # is_senior_coder_required() bypasses severity check when ci_failure_trigger=True
    # This allows SeniorCoder to handle high-severity CI failures (lint errors, etc.)
    review_outcome = state.get("review_outcome")
    ci_failure_trigger = state.get("ci_failure_trigger", False)

    if ci_failure_trigger:
        # CI failure scenario: use relaxed gate (only requires schema_validated)
        if not is_senior_coder_required(state, review_outcome):
            logger.info(
                f"[GENERAL_CODER_GATE_FAIL] SeniorCoder gate failed for CI failure. "
                f"trace_id={trace_id}"
            )
            return False, "SeniorCoder gate check failed for CI failure"
    else:
        # Non-CI failure scenario: use strict gate (requires severity=low)
        if not is_autofix_allowed(review_outcome):
            logger.info(
                f"[GENERAL_CODER_GATE_FAIL] Autofix not allowed for review_outcome. "
                f"trace_id={trace_id}"
            )
            return False, "Autofix gate check failed"

    # Get review files - GeneralCoder needs multiple files
    review_files = state.get("review_files", [])
    file_path = state.get("review_file_path", "")

    # Issue #3720: For CI failure scenarios, do NOT skip SeniorCoder for single files
    # SeniorCoder should evaluate complexity regardless of file count for CI failures
    # This aligns with CTO directive in Issue #3366: "如果 ci_failure_trigger 為 True，
    # 無視 severity == 'low' 的限制" - same principle applies to single-file bypass
    # Blueprint alignment: SeniorCoder (Tier 1) is for "Deep reasoning" - complexity
    # detection IS deep reasoning, regardless of file count
    if len(review_files) <= 1 and file_path and not ci_failure_trigger:
        logger.info(
            f"[GENERAL_CODER_GATE_FAIL] Single file detected, deferring to SimpleCoder. "
            f"review_files_count={len(review_files)}, file_path={file_path}, trace_id={trace_id}"
        )
        return False, "Single file - deferring to SimpleCoder"

    # Log when SeniorCoder is invoked for single-file CI failure (Probe 2 scenario)
    if len(review_files) <= 1 and file_path and ci_failure_trigger:
        logger.info(
            f"[SENIOR_CODER_SINGLE_FILE_CI_FAILURE] Single file CI failure, "
            f"invoking SeniorCoder for complexity evaluation. "
            f"file_path={file_path}, trace_id={trace_id}",
            extra={
                "operation": "senior_coder_single_file_ci_failure",
                "trace_id": trace_id,
                "event_code": "SENIOR_CODER_SINGLE_FILE_CI_FAILURE",
                "file_path": file_path,
            }
        )

    # Build files list from review_files or single file
    # Issue: HITL 6+ files escalation requires passing all files to GeneralCoder
    # so it can detect "Too many files" and trigger HITL escalation (PR #3732).
    # Previously this was limited to settings.general_coder_max_files (5), which
    # prevented GeneralCoder from ever seeing 6+ files and triggering HITL.
    # Use MAX_FILES_FOR_GENERAL_CODER (20) as upper limit to prevent extreme edge cases.
    MAX_FILES_FOR_GENERAL_CODER = 20
    files_to_fix = []
    if review_files:
        total_files = len(review_files)
        files_to_fix = review_files[:MAX_FILES_FOR_GENERAL_CODER]
        # Telemetry: Log when files are truncated (Blueprint 4.2 observability)
        if total_files > MAX_FILES_FOR_GENERAL_CODER:
            logger.warning(
                f"[GENERAL_CODER_FILES_TRUNCATED] Files truncated for GeneralCoder. "
                f"total_files={total_files}, max_files={MAX_FILES_FOR_GENERAL_CODER}, "
                f"trace_id={trace_id}",
                extra={
                    "operation": "general_coder_files_truncated",
                    "trace_id": trace_id,
                    "event_code": "GENERAL_CODER_FILES_TRUNCATED",
                    "total_files": total_files,
                    "max_files": MAX_FILES_FOR_GENERAL_CODER,
                }
            )
    elif file_path:
        files_to_fix = [{"path": file_path}]

    if not files_to_fix:
        logger.info(f"[GENERAL_CODER_GATE_FAIL] No files to fix. trace_id={trace_id}")
        return False, "No files available"

    review_comment = state.get("comment_body", "")
    if not review_comment:
        review_comments = state.get("review_comments", [])
        if review_comments and isinstance(review_comments[0], dict):
            review_comment = review_comments[0].get("body", "")
        elif review_comments and isinstance(review_comments[0], str):
            review_comment = review_comments[0]

    if not review_comment:
        logger.info(f"[GENERAL_CODER_GATE_FAIL] No review comment. trace_id={trace_id}")
        return False, "No review comment available"

    repo_name = state.get("repo", "")
    branch = state.get("branch", "")
    diff_head_sha = state.get("diff_head_sha", "")

    if not repo_name or not branch:
        logger.info(
            f"[GENERAL_CODER_GATE_FAIL] Missing repo or branch. "
            f"repo={repo_name}, branch={branch}, trace_id={trace_id}"
        )
        return False, "Missing repo or branch"

    try:
        # Issue #3618: Fix get_repo() signature - function takes no parameters
        # It reads GITHUB_REPO from environment internally
        repo = get_repo()
        if repo is None:
            logger.warning(f"[GENERAL_CODER_GATE_FAIL] Could not get repo. trace_id={trace_id}")
            return False, "Could not access repository"

        # Fetch content for all files
        ref = diff_head_sha if diff_head_sha else branch
        files_with_content = []
        for f in files_to_fix:
            f_path = f.get("path", "") if isinstance(f, dict) else f
            if not f_path:
                continue
            try:
                file_obj = repo.get_contents(f_path, ref=ref)
                if hasattr(file_obj, 'decoded_content'):
                    content = file_obj.decoded_content.decode('utf-8')
                    files_with_content.append({"path": f_path, "content": content})
            except Exception as e:
                logger.warning(
                    f"[GENERAL_CODER_GATE_FAIL] Failed to fetch file {f_path}: {e}. "
                    f"trace_id={trace_id}"
                )
                # Continue with other files

        if not files_with_content:
            logger.warning(
                f"[GENERAL_CODER_GATE_FAIL] Could not fetch any file content. "
                f"trace_id={trace_id}"
            )
            return False, "Could not fetch file content"

    except Exception as e:
        logger.warning(
            f"[GENERAL_CODER_GATE_FAIL] Failed to fetch files: {e}. "
            f"trace_id={trace_id}"
        )
        return False, f"Failed to fetch files: {e}"

    logger.info(
        f"[GENERAL_CODER_ATTEMPT] Attempting multi-file fix. "
        f"file_count={len(files_with_content)}, trace_id={trace_id}"
    )

    severity = "low"
    if review_outcome and isinstance(review_outcome, dict):
        severity = review_outcome.get("severity", "low")

    task_description = f"Fix the multi-file issue based on review comment: {review_comment}"

    # EPIC D Issue #3487: Pass state to _attempt_senior_coder_plan for HITL flag setting
    should_proceed, spec_dict, plan_msg = _attempt_senior_coder_plan(
        task_description=task_description,
        files_with_content=files_with_content,
        trace_id=trace_id,
        state=state
    )

    if not should_proceed:
        logger.info(
            f"[GENERAL_CODER_SKIP] SeniorCoder aborted task. "
            f"reason={plan_msg}, trace_id={trace_id}"
        )
        return False, f"SeniorCoder aborted: {plan_msg}"

    # P2 Feature: Design Doc Gate - 強制架構審查 (Blueprint Section 4.1 Safety Governor v2)
    # When require_design_doc_gate is enabled, GeneralCoder MUST have a valid ArchitectureSpec
    # before proceeding. This ensures all code changes have proper architecture planning.
    if settings.require_design_doc_gate and settings.enable_senior_coder:
        gate_passed, gate_reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id=trace_id,
            state=state,
            task_description=task_description,
            file_count=len(files_with_content),
        )
        if not gate_passed:
            logger.info(
                f"[DESIGN_DOC_GATE_FAIL] {gate_reason}. trace_id={trace_id}",
                extra={
                    "operation": "design_doc_gate_fail",
                    "trace_id": trace_id,
                    "event_code": "DESIGN_DOC_GATE_FAIL",
                    "reason": gate_reason,
                }
            )
            return False, f"Design Doc Gate failed: {gate_reason}"

    general_coder = get_general_coder()

    context = {
        "files": files_with_content,
        "review_comment": review_comment,
        "severity": severity
    }
    if spec_dict:
        context["architecture_spec"] = spec_dict

    agent_input = AgentInput(
        task_id=trace_id,
        prompt=task_description,
        context=context
    )

    try:
        output = general_coder.execute(agent_input)
    except Exception as e:
        logger.warning(f"[GENERAL_CODER_SKIP] Execution failed: {e}. trace_id={trace_id}")
        return False, f"GeneralCoder execution failed: {e}"

    if not output.success:
        reason = output.data.get("reason", "Unknown") if output.data else "Unknown"
        logger.info(f"[GENERAL_CODER_SKIP] {reason}. trace_id={trace_id}")

        # P1 Feature: HITL escalation for 6+ files
        # When GeneralCoder skips due to too many files, trigger HITL escalation
        # instead of silently falling back to SimpleCoder/AutoFixer
        if "Too many files" in reason and settings.enable_multi_file_hitl_escalation:
            import re
            from resource_telemetry import log_multi_file_hitl_escalation

            # Extract file count from reason (e.g., "Too many files: 7 > 5")
            # Robust parsing with explicit handling of parse failures
            match = re.search(r"Too many files: (\d+) > (\d+)", reason)
            if match:
                file_count = int(match.group(1))
                max_files = int(match.group(2))
            else:
                # Sanitize reason string to prevent log injection
                sanitized_reason = reason.replace('\n', '\\n').replace('\r', '\\r')
                logger.warning(
                    f"[GENERAL_CODER_HITL_PARSE_WARNING] Could not parse file count from "
                    f"skip reason: '{sanitized_reason}'. Using defaults. trace_id={trace_id}",
                    extra={
                        "operation": "general_coder_hitl_parse",
                        "trace_id": trace_id,
                        "event_code": "GENERAL_CODER_HITL_PARSE_WARNING",
                    }
                )
                file_count = 0
                max_files = settings.general_coder_max_files

            # Set HITL escalation flags in state
            state["requires_hitl_approval"] = True
            state["hitl_approved"] = False
            state["hitl_reason"] = "multi_file_limit_exceeded"
            state["hitl_details"] = {
                "version": "1.0",
                "escalation_reason": reason,
                "file_count": file_count,
                "max_files_limit": max_files,
                "recommendation": (
                    f"GeneralCoder cannot handle {file_count} files (limit: {max_files}). "
                    "Consider breaking down the task into smaller chunks or "
                    "manually reviewing the multi-file changes."
                ),
            }

            # Log telemetry event
            pr_number = state.get("pr_number")
            log_multi_file_hitl_escalation(
                file_count=file_count,
                max_files=max_files,
                skip_reason=reason,
                trace_id=trace_id,
                pr_number=pr_number,
            )

            logger.warning(
                f"[GENERAL_CODER_MULTI_FILE_HITL_ESCALATION] "
                f"HITL escalation triggered for {file_count} files. trace_id={trace_id}",
                extra={
                    "operation": "general_coder_multi_file_hitl_escalation",
                    "trace_id": trace_id,
                    "event_code": "GENERAL_CODER_MULTI_FILE_HITL_ESCALATION",
                    "file_count": file_count,
                    "max_files_limit": max_files,
                }
            )

        return False, f"GeneralCoder skipped: {reason}"

    coder_data = output.data or {}
    status = coder_data.get("status", "")
    if status != CoderStatus.PATCH.value:
        reason = coder_data.get("reason", "Unknown")
        logger.info(f"[GENERAL_CODER_SKIP] Status={status}, reason={reason}. trace_id={trace_id}")
        return False, f"GeneralCoder skipped: {reason}"

    patches = coder_data.get("patches", [])
    if not patches:
        logger.warning(f"[GENERAL_CODER_SKIP] No patches returned. trace_id={trace_id}")
        return False, "GeneralCoder returned no patches"

    # Build files list for atomic commit
    commit_files_list = []
    for patch in patches:
        p_path = patch.get("file_path", "")
        p_content = patch.get("patch", "")
        syntax_valid = patch.get("syntax_valid")

        if not p_path or not p_content:
            continue

        # Check syntax validation result
        if p_path.endswith(".py") and syntax_valid is False:
            logger.warning(
                f"[GENERAL_CODER_SKIP] Syntax validation failed for {p_path}. "
                f"trace_id={trace_id}"
            )
            return False, f"Syntax validation failed for {p_path}"

        commit_files_list.append({"path": p_path, "content": p_content})

    if not commit_files_list:
        logger.warning(f"[GENERAL_CODER_SKIP] No valid patches to commit. trace_id={trace_id}")
        return False, "No valid patches to commit"

    review_approved, review_msg = _attempt_senior_coder_review(
        task_description=task_description,
        spec_dict=spec_dict,
        patches=patches,
        trace_id=trace_id
    )

    if not review_approved:
        logger.info(
            f"[GENERAL_CODER_SKIP] SeniorCoder review rejected implementation. "
            f"reason={review_msg}, trace_id={trace_id}"
        )
        return False, f"SeniorCoder review rejected: {review_msg}"

    # Atomic commit via commit_files()
    file_paths_str = ", ".join([f["path"] for f in commit_files_list])
    commit_message = f"fix: GeneralCoder auto-fix for {len(commit_files_list)} files"
    result = commit_files(repo, branch, commit_files_list, commit_message)

    if result.success:
        logger.info(
            f"[GENERAL_CODER_PATCH_APPLIED] Successfully applied {len(commit_files_list)} patches. "
            f"files={file_paths_str}, branch={branch}, sha={result.sha}, trace_id={trace_id}"
        )
        return True, f"GeneralCoder successfully fixed {len(commit_files_list)} files"
    else:
        logger.error(
            f"[GENERAL_CODER_PATCH_FAILED] Failed to apply patches: {result.status} - {result.message}. "
            f"trace_id={trace_id}"
        )
        return False, f"Failed to apply patches: {result.message}"


def _attempt_simple_coder_fix(
    state: AgentState,
    trace_id: str
) -> tuple[bool, Optional[str]]:
    """Attempt to fix using SimpleCoder before falling back to AutoFixer.

    This implements D-1 Phase 1: SimpleCoder wiring into LangGraph workflow.
    SimpleCoder is a minimal coder agent with Three Don'ts safety guardrails:
    1. Low Confidence = Abort (structured output)
    2. Side-effect Gate (is_autofix_allowed check)
    3. Verification Gate (Python syntax validation)

    Args:
        state: Current AgentState with review_outcome and file context
        trace_id: Trace ID for logging

    Returns:
        Tuple of (success, message):
        - (True, message) if SimpleCoder successfully applied a fix
        - (False, message) if SimpleCoder skipped or failed (fallback to AutoFixer)

    Event Codes (greppable):
        [SIMPLE_CODER_ATTEMPT] - SimpleCoder fix attempt started
        [SIMPLE_CODER_GATE_FAIL] - Gate check failed, skipping SimpleCoder
        [SIMPLE_CODER_SKIP] - SimpleCoder decided to skip (low confidence)
        [SIMPLE_CODER_PATCH_APPLIED] - Patch successfully applied via GitHub API
        [SIMPLE_CODER_PATCH_FAILED] - Patch application failed
        [SIMPLE_CODER_DISABLED] - Feature flag disabled
    """
    try:
        from coder.autofix_gate import is_autofix_allowed, is_path_excluded
        from coder.simple_coder import get_simple_coder, CoderStatus
        from core.agents import AgentInput
        from tools.github_api import get_repo, commit_file
    except ImportError as e:
        logger.debug(f"[SIMPLE_CODER_DISABLED] Import failed: {e}")
        return False, f"SimpleCoder not available: {e}"

    if not settings.enable_simple_coder:
        logger.debug("[SIMPLE_CODER_DISABLED] Feature flag disabled")
        return False, "SimpleCoder feature flag disabled"

    review_outcome = state.get("review_outcome")
    if not is_autofix_allowed(review_outcome):
        logger.info(
            f"[SIMPLE_CODER_GATE_FAIL] Autofix not allowed for review_outcome. "
            f"trace_id={trace_id}"
        )
        return False, "Autofix gate check failed"

    file_path = state.get("review_file_path", "")
    if not file_path:
        logger.info(f"[SIMPLE_CODER_GATE_FAIL] No file path in state. trace_id={trace_id}")
        return False, "No file path available"

    if is_path_excluded(file_path):
        logger.info(
            f"[SIMPLE_CODER_GATE_FAIL] File path excluded: {file_path}. "
            f"trace_id={trace_id}"
        )
        return False, f"File path excluded: {file_path}"

    review_comment = state.get("comment_body", "")
    if not review_comment:
        review_comments = state.get("review_comments", [])
        if review_comments and isinstance(review_comments[0], dict):
            review_comment = review_comments[0].get("body", "")
        elif review_comments and isinstance(review_comments[0], str):
            review_comment = review_comments[0]

    if not review_comment:
        logger.info(f"[SIMPLE_CODER_GATE_FAIL] No review comment. trace_id={trace_id}")
        return False, "No review comment available"

    repo_name = state.get("repo", "")
    branch = state.get("branch", "")
    diff_head_sha = state.get("diff_head_sha", "")

    if not repo_name or not branch:
        logger.info(
            f"[SIMPLE_CODER_GATE_FAIL] Missing repo or branch. "
            f"repo={repo_name}, branch={branch}, trace_id={trace_id}"
        )
        return False, "Missing repo or branch"

    try:
        # Issue #3618: Fix get_repo() signature - function takes no parameters
        # It reads GITHUB_REPO from environment internally
        repo = get_repo()
        if repo is None:
            logger.warning(f"[SIMPLE_CODER_GATE_FAIL] Could not get repo. trace_id={trace_id}")
            return False, "Could not access repository"

        ref = diff_head_sha if diff_head_sha else branch
        file_obj = repo.get_contents(file_path, ref=ref)
        if hasattr(file_obj, 'decoded_content'):
            file_content = file_obj.decoded_content.decode('utf-8')
        else:
            logger.warning(
                f"[SIMPLE_CODER_GATE_FAIL] Could not decode file content. "
                f"file_path={file_path}, trace_id={trace_id}"
            )
            return False, "Could not decode file content"
    except Exception as e:
        logger.warning(
            f"[SIMPLE_CODER_GATE_FAIL] Failed to fetch file: {e}. "
            f"file_path={file_path}, trace_id={trace_id}"
        )
        return False, f"Failed to fetch file: {e}"

    logger.info(
        f"[SIMPLE_CODER_ATTEMPT] Attempting fix. "
        f"file_path={file_path}, trace_id={trace_id}"
    )

    severity = "low"
    if review_outcome and isinstance(review_outcome, dict):
        severity = review_outcome.get("severity", "low")

    simple_coder = get_simple_coder()
    agent_input = AgentInput(
        task_id=trace_id,
        prompt=f"Fix the issue in {file_path}",
        context={
            "file_path": file_path,
            "file_content": file_content,
            "review_comment": review_comment,
            "severity": severity
        }
    )

    try:
        output = simple_coder.execute(agent_input)
    except Exception as e:
        logger.warning(f"[SIMPLE_CODER_SKIP] Execution failed: {e}. trace_id={trace_id}")
        return False, f"SimpleCoder execution failed: {e}"

    if not output.success:
        reason = output.data.get("reason", "Unknown") if output.data else "Unknown"
        logger.info(f"[SIMPLE_CODER_SKIP] {reason}. trace_id={trace_id}")
        return False, f"SimpleCoder skipped: {reason}"

    coder_data = output.data or {}
    status = coder_data.get("status", "")
    if status != CoderStatus.PATCH.value:
        reason = coder_data.get("reason", "Unknown")
        logger.info(f"[SIMPLE_CODER_SKIP] Status={status}, reason={reason}. trace_id={trace_id}")
        return False, f"SimpleCoder skipped: {reason}"

    patch_content = coder_data.get("patch", "")
    if not patch_content:
        logger.warning(f"[SIMPLE_CODER_SKIP] No patch content. trace_id={trace_id}")
        return False, "SimpleCoder returned empty patch"

    syntax_valid = coder_data.get("syntax_valid")
    if file_path.endswith(".py") and syntax_valid is False:
        logger.warning(
            f"[SIMPLE_CODER_SKIP] Syntax validation failed. "
            f"file_path={file_path}, trace_id={trace_id}"
        )
        return False, "Patch failed syntax validation"

    commit_message = f"fix: SimpleCoder auto-fix for {file_path}"
    result = commit_file(repo, branch, file_path, patch_content, commit_message)

    if result.success:
        logger.info(
            f"[SIMPLE_CODER_PATCH_APPLIED] Successfully applied patch. "
            f"file_path={file_path}, branch={branch}, sha={result.sha}, trace_id={trace_id}"
        )
        return True, f"SimpleCoder successfully fixed {file_path}"
    else:
        logger.error(
            f"[SIMPLE_CODER_PATCH_FAILED] Failed to apply patch: {result.status} - {result.message}. "
            f"file_path={file_path}, trace_id={trace_id}"
        )
        return False, f"Failed to apply patch: {result.message}"


# Supported file extensions for CI error path extraction (Issue #3567)
# Used by _extract_file_path_from_error() to identify source files in lint output
_SUPPORTED_SOURCE_EXTENSIONS = r'py|js|ts|jsx|tsx|go|rs|java|rb|php|c|cpp|h|hpp'


def _extract_file_path_from_error(error_summary: str) -> str:
    """Extract file path from CI error summary.

    Parses common lint error formats to extract the file path:
    - "path/to/file.py:123:45: E501 line too long"
    - "path/to/file.py(123): error"
    - "Error in path/to/file.py"

    Issue #3567: Enable SimpleCoder for CI failures by extracting file path

    Args:
        error_summary: CI error output text

    Returns:
        Extracted file path or empty string if not found
    """
    if not error_summary:
        return ""

    # Pattern 1: "path/file.py:line:col: error" (flake8, pylint, eslint)
    match = re.search(
        fr'^([^\s:]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS})):',
        error_summary,
        re.MULTILINE
    )
    if match:
        return match.group(1)

    # Pattern 2: "path/file.py(line): error" (some compilers)
    match = re.search(
        fr'^([^\s(]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS}))\(',
        error_summary,
        re.MULTILINE
    )
    if match:
        return match.group(1)

    # Pattern 3: "Error in path/file.py" or "File path/file.py"
    match = re.search(
        fr'(?:Error in|File|in file)\s+([^\s:]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS}))',
        error_summary,
        re.IGNORECASE
    )
    if match:
        return match.group(1)

    return ""


def _extract_file_paths_from_error(error_summary: str) -> list:
    """Extract ALL file paths from CI error summary for multi-file support.

    Issue #3675: D-1b GeneralCoder needs multiple file paths for multi-file fixes.
    This function extracts all unique file paths from CI error output, enabling
    GeneralCoder to handle multi-file lint errors.

    Parses common lint error formats:
    - "path/to/file.py:123:45: E501 line too long"
    - "path/to/file.py(123): error"
    - "Error in path/to/file.py"

    Args:
        error_summary: CI error output text

    Returns:
        List of unique file paths (max 5 for D-1b limit), empty list if none found

    Event Codes (greppable):
        [MULTI_FILE_EXTRACT_SUCCESS] - Successfully extracted multiple file paths
        [MULTI_FILE_EXTRACT_SINGLE] - Only one file path found
        [MULTI_FILE_EXTRACT_NONE] - No file paths found
    """
    if not error_summary:
        logger.debug("[MULTI_FILE_EXTRACT_NONE] Empty error_summary")
        return []

    file_paths = set()

    # Pattern 1: "path/file.py:line:col: error" (flake8, pylint, eslint)
    pattern1_matches = re.findall(
        fr'^([^\s:]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS})):',
        error_summary,
        re.MULTILINE
    )
    file_paths.update(pattern1_matches)

    # Pattern 2: "path/file.py(line): error" (some compilers)
    pattern2_matches = re.findall(
        fr'^([^\s(]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS}))\(',
        error_summary,
        re.MULTILINE
    )
    file_paths.update(pattern2_matches)

    # Pattern 3: "Error in path/file.py" or "File path/file.py"
    pattern3_matches = re.findall(
        fr'(?:Error in|File|in file)\s+([^\s:]+\.(?:{_SUPPORTED_SOURCE_EXTENSIONS}))',
        error_summary,
        re.IGNORECASE
    )
    file_paths.update(pattern3_matches)

    # Convert to list and limit to configurable max files (D-1b default: 5)
    result = list(file_paths)[:settings.general_coder_max_files]

    if len(result) == 0:
        logger.debug("[MULTI_FILE_EXTRACT_NONE] No file paths found in error_summary")
    elif len(result) == 1:
        logger.debug(f"[MULTI_FILE_EXTRACT_SINGLE] Found 1 file: {result[0]}")
    else:
        logger.info(
            f"[MULTI_FILE_EXTRACT_SUCCESS] Found {len(result)} files: {result}",
            extra={
                "operation": "multi_file_extract",
                "file_count": len(result),
                "file_paths": result,
            }
        )

    return result


def _ensure_comment_body_for_ci_failure(state: dict, trace_id: str) -> None:
    """Synthesize comment_body and review_outcome from ci_failure_context for CI failure scenarios.

    When ci_failure_trigger=True, there's no PR review comment, but the coders
    need a comment_body to understand what to fix. This function synthesizes one
    from the CI failure context.

    Additionally, CI failure fast path bypasses reviewer_node which normally
    populates review_outcome. Without review_outcome, is_autofix_allowed() gate
    always fails. This function synthesizes a minimal review_outcome for CI failures.

    Only synthesizes when:
    - ci_failure_trigger=True
    - comment_body is empty (for comment_body)
    - review_outcome is empty/None (for review_outcome)

    Note: We intentionally do NOT check review_comments here. The review_comments
    list contains ALL historical PR comments (including bot comments, previous
    test comments, etc.), not just the triggering comment. For CI failure scenarios,
    there is no triggering comment - the webhook comes from CI, not a PR review.
    The existing_comment check is sufficient to avoid overwriting real human input.

    Issue #3564: Root Cause #10 - Coders skip due to missing comment_body
    Issue #3567: Root Cause #11 - SimpleCoder needs review_file_path
    Issue #3572: Root Cause #12 - review_comments gate blocks CI failure synthesis
    Issue #3618: Root Cause #13 - CI failure path bypasses reviewer_node, review_outcome never set
    """
    ci_failure_trigger = state.get("ci_failure_trigger", False)

    # Debug logging for early return diagnosis (Issue #3567)
    if not ci_failure_trigger:
        logger.debug(
            f"[Fixer] _ensure_comment_body skipped: ci_failure_trigger=False. "
            f"trace_id={trace_id}"
        )
        return

    # Issue #3618: Synthesize review_outcome for CI failure path
    # CI failure fast path bypasses reviewer_node which normally populates review_outcome.
    # Without review_outcome, is_autofix_allowed() gate always fails.
    #
    # These are the MINIMAL fields required by is_autofix_allowed() in coder/autofix_gate.py:
    # - schema_validated: Must be True for autofix to proceed
    # - severity: Must be "low" for SimpleCoder (higher severity blocks autofix)
    # - diff_truncated: Must be False for autofix to proceed
    #
    # We use setdefault() to only fill missing keys, preserving any values set by upstream.
    # This avoids brittleness if reviewer_node adds more fields in the future.
    existing_review_outcome = state.get("review_outcome")
    if existing_review_outcome is None:
        # No review_outcome at all - create minimal dict for autofix gate
        ci_context = state.get("ci_failure_context", {})
        failed_check_name = (ci_context.get("failed_check_name") or "").lower()

        # Infer severity from CI failure type to prevent unsafe auto-fixes
        # Security/vulnerability scans and build failures should NOT be auto-fixed
        severity = "low"
        if any(k in failed_check_name for k in ["security", "scan", "vulnerability"]):
            severity = "critical"
        elif any(k in failed_check_name for k in ["build", "compile"]):
            severity = "high"

        state["review_outcome"] = {
            "schema_validated": True,
            "severity": severity,
            "diff_truncated": False,
        }
        logger.info(
            f"[Fixer] Synthesized review_outcome for CI failure path. "
            f"failed_check={failed_check_name}, severity={severity}, trace_id={trace_id}",
            extra={
                "operation": "fixer_synthesize_review_outcome",
                "trace_id": trace_id,
                "failed_check_name": failed_check_name,
                "severity": severity,
            }
        )
    elif isinstance(existing_review_outcome, dict):
        # review_outcome exists but may be missing required keys - fill only missing ones
        # This preserves any upstream-set values (e.g., severity from reviewer_node)
        existing_review_outcome.setdefault("schema_validated", True)
        existing_review_outcome.setdefault("severity", "low")
        existing_review_outcome.setdefault("diff_truncated", False)
        logger.debug(
            f"[Fixer] Filled missing review_outcome keys for CI failure path. "
            f"trace_id={trace_id}",
            extra={
                "operation": "fixer_fill_review_outcome",
                "trace_id": trace_id,
            }
        )

    existing_comment = state.get("comment_body", "")
    if existing_comment:
        logger.debug(
            f"[Fixer] _ensure_comment_body skipped: comment_body already set. "
            f"len={len(existing_comment)}, repr={repr(existing_comment[:50])}... "
            f"trace_id={trace_id}"
        )
        return

    # Issue #3572: Do NOT check review_comments here. The review_comments list
    # contains ALL historical PR comments, not just the triggering comment.
    # For CI failure scenarios, there is no triggering comment.
    review_comments = state.get("review_comments", [])
    if review_comments:
        logger.info(
            f"[Fixer] CI failure synthesis proceeding despite {len(review_comments)} "
            f"historical review_comments (Issue #3572).",
            extra={
                "operation": "fixer_ci_synthesis_with_comments",
                "trace_id": trace_id,
                "review_comments_count": len(review_comments),
            }
        )

    ci_context = state.get("ci_failure_context", {})
    ci_context_type = type(ci_context).__name__

    if not ci_context:
        logger.warning(
            f"[Fixer] CI failure trigger set but no ci_failure_context. "
            f"ci_context_type={ci_context_type}, ci_context_is_none={ci_context is None}, "
            f"trace_id={trace_id}"
        )
        return

    failed_check = ci_context.get("failed_check_name", "unknown")
    error_summary = ci_context.get("error_summary", "")

    if error_summary:
        if not isinstance(error_summary, str):
            error_summary = str(error_summary)
        error_summary_truncated = error_summary[:500]
        synthesized = f"Fix CI failure in {failed_check}: {error_summary_truncated}"

        # Issue #3675: Extract ALL file paths for GeneralCoder multi-file support
        # This enables D-1b GeneralCoder to handle multi-file lint errors
        # Issue #3693: Only extract from error_summary if review_files is not already set
        # from Annotations API (high precision). This prevents fallback (error_summary)
        # from overriding the high-precision Annotations extraction.
        existing_review_files = state.get("review_files")
        if existing_review_files and len(existing_review_files) > 0:
            # review_files already set from Annotations API - do NOT override
            logger.info(
                f"[Fixer] Skipping error_summary extraction - review_files already set from Annotations. "
                f"existing_count={len(existing_review_files)}, trace_id={trace_id}",
                extra={
                    "operation": "fixer_skip_error_summary_extraction",
                    "trace_id": trace_id,
                    "existing_review_files_count": len(existing_review_files),
                    "existing_review_files": existing_review_files,
                }
            )
        else:
            # Fallback: extract from error_summary text
            extracted_file_paths = _extract_file_paths_from_error(error_summary)
            if extracted_file_paths:
                # Set review_files for GeneralCoder (multi-file support)
                state["review_files"] = [{"path": fp} for fp in extracted_file_paths]
                logger.info(
                    f"[Fixer] Extracted review_files from error_summary for GeneralCoder (fallback). "
                    f"file_count={len(extracted_file_paths)}, files={extracted_file_paths}, trace_id={trace_id}",
                    extra={
                        "operation": "fixer_extract_review_files",
                        "trace_id": trace_id,
                        "file_count": len(extracted_file_paths),
                        "file_paths": extracted_file_paths,
                    }
                )

        # Issue #3567: Extract single file path for SimpleCoder (backward compatibility)
        extracted_file_path = _extract_file_path_from_error(error_summary)
        if extracted_file_path and not state.get("review_file_path"):
            state["review_file_path"] = extracted_file_path
            logger.info(
                f"[Fixer] Extracted review_file_path from error_summary. "
                f"file_path={extracted_file_path}, trace_id={trace_id}",
                extra={
                    "operation": "fixer_extract_file_path",
                    "trace_id": trace_id,
                    "file_path": extracted_file_path,
                }
            )
    else:
        synthesized = f"Fix CI failure in {failed_check} check"

    state["comment_body"] = synthesized

    logger.info(
        f"[Fixer] Synthesized comment_body for CI failure. "
        f"failed_check={failed_check}, trace_id={trace_id}",
        extra={
            "operation": "fixer_synthesize_comment",
            "trace_id": trace_id,
            "failed_check": failed_check,
            "has_error_summary": bool(error_summary),
            "review_files_count": len(state.get("review_files", [])),
        }
    )


def fixer_node(state: AgentState) -> AgentState:
    """
    Fixer node: Attempts to fix CI failures

    Phase 2 Step C Enhancement:
    - Integrates AutoFixer for automated fix attempts
    - Uses ReviewerAgent to analyze code issues
    - Uses ProjectEngineerAgent to generate fixes
    - Supports canary rollout via PROJECT_ENGINEER_FIXER_PERCENT

    D-1 Phase 1 Enhancement:
    - Attempts SimpleCoder fix first (if enabled and gate passes)
    - Falls back to AutoFixer if SimpleCoder skips or fails
    - SimpleCoder uses Three Don'ts safety guardrails

    D-1b Enhancement:
    - Attempts GeneralCoder multi-file fix first (if enabled)
    - Falls back to SimpleCoder for single-file issues
    - Falls back to AutoFixer if both coders skip or fail

    Issue #3564 Enhancement:
    - Synthesizes comment_body from ci_failure_context for CI failure scenarios
    - Ensures coders don't skip due to missing comment_body

    Cost Optimization Enhancement:
    - Adds AutoFixLoopProtection to prevent infinite retry loops
    - Tracks attempts per PR in Redis to enforce max_retries across webhook triggers
    - Adds CI signature deduplication to avoid re-processing identical failures
    """
    from common.config.settings import settings

    start_time = time.time()
    metrics = _get_metrics()

    trace_id = state["trace_id"]
    retry_count = state.get("retry_count", 0)

    # Cost Optimization: Check loop protection BEFORE any LLM calls
    # This prevents infinite loops where CI failure → fix attempt → CI failure → ...
    repo = state.get("repo", "")
    pr_number = state.get("pr_number")
    pr_id = f"{repo}#{pr_number}" if repo and pr_number else trace_id

    try:
        from utils.auto_fix_policy import AutoFixLoopProtection
        loop_protection = AutoFixLoopProtection(settings)
        loop_allowed, current_attempts = loop_protection.check_and_increment(pr_id)

        if not loop_allowed:
            max_retries = getattr(settings, 'auto_fix_max_retries', 3)
            logger.warning(
                f"[Fixer] Loop protection triggered - max retries exceeded. "
                f"pr_id={pr_id}, attempts={current_attempts}, max={max_retries}, trace_id={trace_id}",
                extra={
                    "operation": "fixer_loop_protection",
                    "trace_id": trace_id,
                    "pr_id": pr_id,
                    "current_attempts": current_attempts,
                    "max_retries": max_retries,
                    "loop_protection_triggered": True,
                }
            )
            state["error"] = f"Loop protection: max retries ({max_retries}) exceeded after {current_attempts} attempts"
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"AutoFixer stopped by loop protection after {current_attempts} attempts")
            ]
            # Set flag to signal should_proceed_after_fixer to route to finalizer
            # This prevents infinite recursion: fixer → ci_monitor → reviewer → fixer → ...
            state["loop_protection_triggered"] = True
            latency_ms = (time.time() - start_time) * 1000
            metrics.record_fixer_attempt(trace_id, retry_count, success=False)
            metrics.record_node_complete("fixer", trace_id, success=False, latency_ms=latency_ms)
            return state

        logger.info(
            f"[Fixer] Loop protection check passed. pr_id={pr_id}, attempt={current_attempts}, trace_id={trace_id}",
            extra={
                "operation": "fixer_loop_protection_passed",
                "trace_id": trace_id,
                "pr_id": pr_id,
                "current_attempts": current_attempts,
            }
        )
    except ImportError as e:
        logger.warning(
            f"[Fixer] AutoFixLoopProtection not available, proceeding without loop protection: {e}",
            extra={"trace_id": trace_id, "error": str(e)}
        )
    except Exception as e:
        # Fail-open: if loop protection fails, continue with fix attempt
        # but log for observability
        logger.error(
            f"[Fixer] Loop protection check failed, proceeding (fail-open): {e}",
            extra={"trace_id": trace_id, "error": str(e), "pr_id": pr_id}
        )

    # Cost Optimization: CI signature deduplication
    # Prevents re-processing the EXACT SAME CI failure within 24 hours
    ci_context_for_dedup = state.get("ci_failure_context")
    if ci_context_for_dedup and isinstance(ci_context_for_dedup, dict):
        try:
            from utils.auto_fix_policy import CISignatureDeduplication
            dedup = CISignatureDeduplication(settings)
            failed_check_name = ci_context_for_dedup.get("failed_check_name", "unknown")
            error_summary = ci_context_for_dedup.get("error_summary", "")

            is_new, signature = dedup.check_and_mark(pr_id, failed_check_name, error_summary)

            if not is_new:
                logger.warning(
                    f"[Fixer] CI signature deduplication triggered - identical failure already processed. "
                    f"pr_id={pr_id}, signature={signature}, trace_id={trace_id}",
                    extra={
                        "operation": "fixer_ci_signature_dedup",
                        "trace_id": trace_id,
                        "pr_id": pr_id,
                        "signature": signature,
                        "failed_check_name": failed_check_name,
                        "ci_signature_duplicate": True,
                    }
                )
                state["error"] = f"CI signature deduplication: identical failure already processed (signature={signature})"
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content="AutoFixer skipped - identical CI failure already processed within 24h")
                ]
                latency_ms = (time.time() - start_time) * 1000
                metrics.record_fixer_attempt(trace_id, retry_count, success=False)
                metrics.record_node_complete("fixer", trace_id, success=False, latency_ms=latency_ms)
                return state

            logger.debug(
                f"[Fixer] CI signature deduplication passed. signature={signature}, trace_id={trace_id}",
                extra={
                    "operation": "fixer_ci_signature_dedup_passed",
                    "trace_id": trace_id,
                    "signature": signature,
                }
            )
        except ImportError as e:
            logger.warning(
                f"[Fixer] CISignatureDeduplication not available: {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )
        except Exception as e:
            # Fail-open: if dedup fails, continue with fix attempt
            logger.error(
                f"[Fixer] CI signature deduplication failed, proceeding (fail-open): {e}",
                extra={"trace_id": trace_id, "error": str(e)}
            )

    # Issue #3567: Diagnostic log for coder prerequisites debugging
    # This log helps diagnose why coders skip in CI failure scenarios
    ci_failure_trigger = state.get("ci_failure_trigger", False)
    comment_body = state.get("comment_body", "")
    review_comments = state.get("review_comments", [])
    review_file_path = state.get("review_file_path", "")
    review_files = state.get("review_files", [])
    ci_context = state.get("ci_failure_context")
    review_outcome = state.get("review_outcome")

    # Safe access to settings attributes (handles None settings in tests)
    enable_general_coder = getattr(settings, 'enable_general_coder', False) if settings else False
    enable_simple_coder = getattr(settings, 'enable_simple_coder', False) if settings else False

    # Extract review_outcome fields for diagnostic
    review_outcome_severity = review_outcome.get("severity", "N/A") if isinstance(review_outcome, dict) else "N/A"
    review_outcome_schema_validated = review_outcome.get("schema_validated", "N/A") if isinstance(review_outcome, dict) else "N/A"

    logger.info(
        f"[FIXER_ENTRY_DIAGNOSTIC] Coder prerequisites at fixer_node entry. "
        f"ci_failure_trigger={ci_failure_trigger}, "
        f"comment_body_len={len(comment_body)}, "
        f"comment_body_repr={repr(comment_body[:50]) if comment_body else 'empty'}..., "
        f"review_comments_count={len(review_comments)}, "
        f"review_file_path={review_file_path or 'empty'}, "
        f"review_files_count={len(review_files)}, "
        f"review_outcome_present={review_outcome is not None}, "
        f"review_outcome_severity={review_outcome_severity}, "
        f"review_outcome_schema_validated={review_outcome_schema_validated}, "
        f"ci_context_present={ci_context is not None}, "
        f"ci_context_type={type(ci_context).__name__}, "
        f"enable_general_coder={enable_general_coder}, "
        f"enable_simple_coder={enable_simple_coder}, "
        f"trace_id={trace_id}",
        extra={
            "operation": "fixer_entry_diagnostic",
            "trace_id": trace_id,
            "ci_failure_trigger": ci_failure_trigger,
            "comment_body_len": len(comment_body),
            "review_comments_count": len(review_comments),
            "review_file_path": review_file_path,
            "review_files_count": len(review_files),
            "review_outcome_present": review_outcome is not None,
            "review_outcome_severity": review_outcome_severity,
            "review_outcome_schema_validated": review_outcome_schema_validated,
            "ci_context_present": ci_context is not None,
            "enable_general_coder": enable_general_coder,
            "enable_simple_coder": enable_simple_coder,
        }
    )

    _ensure_comment_body_for_ci_failure(state, trace_id)

    # Log state after synthesis attempt
    comment_body_after = state.get("comment_body", "")
    review_file_path_after = state.get("review_file_path", "")
    if comment_body_after != comment_body or review_file_path_after != review_file_path:
        logger.info(
            f"[FIXER_ENTRY_DIAGNOSTIC] State after _ensure_comment_body_for_ci_failure. "
            f"comment_body_len={len(comment_body_after)}, "
            f"review_file_path={review_file_path_after or 'empty'}, "
            f"trace_id={trace_id}",
            extra={
                "operation": "fixer_entry_diagnostic_after",
                "trace_id": trace_id,
                "comment_body_len": len(comment_body_after),
                "review_file_path": review_file_path_after,
            }
        )

    metrics.record_node_start("fixer", trace_id)

    # D-1b: Try GeneralCoder first for multi-file issues
    general_coder_success, general_coder_msg = _attempt_general_coder_fix(state, trace_id)
    if general_coder_success:
        logger.info(
            f"[Fixer] GeneralCoder fix succeeded, skipping SimpleCoder/AutoFixer. "
            f"message={general_coder_msg}, trace_id={trace_id}",
            extra={
                "operation": "fixer",
                "trace_id": trace_id,
                "general_coder_success": True
            }
        )
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"GeneralCoder fix applied: {general_coder_msg}")
        ]
        state["retry_count"] = retry_count + 1
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_fixer_attempt(trace_id, retry_count, success=True)
        metrics.record_node_complete("fixer", trace_id, success=True, latency_ms=latency_ms)
        metrics.record_transition("fixer", "executor", trace_id)

        agent_eval = _get_agent_eval()
        agent_eval.record_node_latency(trace_id, "fixer", latency_ms)
        agent_eval.record_fixer_iteration(trace_id, retry_count + 1, True)
        return state

    logger.info(
        f"[Fixer] GeneralCoder did not apply fix, trying SimpleCoder. "
        f"reason={general_coder_msg}, trace_id={trace_id}"
    )

    # D-1: Try SimpleCoder for single-file issues
    simple_coder_success, simple_coder_msg = _attempt_simple_coder_fix(state, trace_id)
    if simple_coder_success:
        logger.info(
            f"[Fixer] SimpleCoder fix succeeded, skipping AutoFixer. "
            f"message={simple_coder_msg}, trace_id={trace_id}",
            extra={
                "operation": "fixer",
                "trace_id": trace_id,
                "simple_coder_success": True
            }
        )
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"SimpleCoder fix applied: {simple_coder_msg}")
        ]
        state["retry_count"] = retry_count + 1
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_fixer_attempt(trace_id, retry_count, success=True)
        metrics.record_node_complete("fixer", trace_id, success=True, latency_ms=latency_ms)
        metrics.record_transition("fixer", "executor", trace_id)

        agent_eval = _get_agent_eval()
        agent_eval.record_node_latency(trace_id, "fixer", latency_ms)
        agent_eval.record_fixer_iteration(trace_id, retry_count + 1, True)
        return state

    logger.debug(
        f"[Fixer] SimpleCoder did not apply fix, falling back to AutoFixer. "
        f"reason={simple_coder_msg}, trace_id={trace_id}"
    )

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

        # Issue #3379: Fetch PR diff BEFORE LLM check to support CI-only mode discovery audit
        # Previously, diff was only fetched inside `if use_llm:` block, causing discovery audit
        # to be skipped in CI-only mode (governance blind spot).
        # Now diff is fetched independently, enabling discovery audit for both modes.
        diff_data = None
        diff_content = None
        diff_truncated = False
        diff_files = None
        diff_head_sha = None
        github_repo = None

        if pr_number:
            try:
                github_repo = get_repo()
                if github_repo:
                    diff_data = get_pr_diff(github_repo, pr_number, trace_id=trace_id)
                    if diff_data and not diff_data.get("error"):
                        diff_content = diff_data.get("diff", "")
                        diff_truncated = diff_data.get("truncated", False)
                        diff_files = diff_data.get("files", [])
                        diff_head_sha = diff_data.get("head_sha")
                        truncation_info = diff_data.get("truncation_info", {})
                        github_total_files = truncation_info.get("original_file_count", 0)
                        included_file_count = truncation_info.get("included_file_count", 0)
                        original_line_count = truncation_info.get("original_line_count", 0)
                        included_line_count = truncation_info.get("included_line_count", 0)
                        ignored_file_count = truncation_info.get("ignored_file_count", 0)
                        lockfile_only = (
                            included_file_count == 0 and
                            ignored_file_count > 0 and
                            github_total_files == ignored_file_count
                        )

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

                        diff_hash = hashlib.sha256(diff_content.encode()).hexdigest()[:16] if diff_content else "empty"
                        logger.info(
                            "[Reviewer] Retrieved PR diff for review",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "pr_number": pr_number,
                                "diff_file_count": len(diff_files) if diff_files else 0,
                                "diff_truncated": diff_truncated,
                                "github_total_files": github_total_files,
                                "diff_content_hash": diff_hash,
                                "diff_content_length": len(diff_content) if diff_content else 0,
                                "diff_head_sha": diff_head_sha[:8] if diff_head_sha else None,
                                "truncation_info": {
                                    "original_file_count": github_total_files,
                                    "included_file_count": included_file_count,
                                    "original_line_count": original_line_count,
                                    "included_line_count": included_line_count,
                                    "ignored_file_count": ignored_file_count
                                }
                            }
                        )

                        # Store diff in state for discovery audit (both LLM and CI-only modes)
                        if diff_head_sha:
                            state["diff_head_sha"] = diff_head_sha
                        if diff_content:
                            sanitized_diff, redaction_count = sanitize_diff_content(diff_content)
                            if redaction_count > 0:
                                logger.info("[Reviewer] Sanitized diff before state storage", extra={
                                    "operation": "reviewer",
                                    "trace_id": trace_id,
                                    "redaction_count": redaction_count
                                })
                            state["diff_content"] = sanitized_diff
                            state["diff_truncated"] = diff_truncated

                        # Issue #3223: File Reference Resolution - Cross-file context gathering
                        # Extract import statements from diff and fetch referenced file content
                        # This provides additional context for more accurate code reviews
                        if diff_content and diff_head_sha and github_repo:
                            try:
                                from tools.file_reference_resolver import resolve_file_references

                                ref_result = resolve_file_references(
                                    repo=github_repo,
                                    diff_content=diff_content,
                                    head_sha=diff_head_sha,
                                    trace_id=trace_id,
                                )

                                if ref_result.total_contexts_fetched > 0:
                                    state["reference_context_v1"] = ref_result.to_dict()
                                    logger.info(
                                        f"[Reviewer] File references resolved: {ref_result.total_contexts_fetched} files",
                                        extra={
                                            "operation": "reviewer",
                                            "trace_id": trace_id,
                                            "total_references": ref_result.total_references_found,
                                            "contexts_fetched": ref_result.total_contexts_fetched,
                                            "total_bytes": ref_result.total_bytes,
                                            "truncated": ref_result.truncated,
                                        }
                                    )

                            except Exception as ref_error:
                                logger.warning(
                                    f"[Reviewer] File reference resolution failed (non-blocking): {ref_error}",
                                    extra={
                                        "operation": "reviewer",
                                        "trace_id": trace_id,
                                        "error": str(ref_error)
                                    }
                                )
                    else:
                        metrics.record_diff_fetch(trace_id=trace_id, success=False)
                        logger.warning(
                            f"[Reviewer] Failed to get PR diff: {diff_data.get('error', 'unknown') if diff_data else 'no data'}",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "pr_number": pr_number
                            }
                        )
            except Exception as diff_error:
                metrics.record_diff_fetch(trace_id=trace_id, success=False)
                logger.warning(
                    f"[Reviewer] Error fetching PR diff: {diff_error}",
                    extra={
                        "operation": "reviewer",
                        "trace_id": trace_id,
                        "error": str(diff_error)
                    }
                )

        use_llm = getattr(settings, 'use_llm_reviewer', False)

        if use_llm:
            logger.info("[Reviewer] LLM reviewer enabled, attempting LLM review", extra={
                "operation": "reviewer",
                "trace_id": trace_id
            })

            try:
                goal = state.get("goal", "")
                repo = state.get("repo", "")

                # Early PR state check (best-effort optimization for LLM mode)
                # Skip LLM review for closed/merged PRs to avoid posting reviews
                if pr_number and github_repo:
                    try:
                        pr_obj = github_repo.get_pull(pr_number)
                        pr_state = getattr(pr_obj, 'state', None)
                        pr_merged = getattr(pr_obj, 'merged', None)
                        if pr_state != "open" or pr_merged is True:
                            logger.info(
                                "[Reviewer] Skipping LLM review for non-open/merged PR",
                                extra={
                                    "operation": "reviewer",
                                    "trace_id": trace_id,
                                    "pr_number": pr_number,
                                    "pr_state": pr_state,
                                    "pr_merged": pr_merged,
                                    "reason": "pr_not_open_or_merged",
                                    "outcome": "skipped"
                                }
                            )
                            state["review_skipped_reason"] = "pr_closed_or_merged"
                            state["messages"] = state.get("messages", []) + [
                                AIMessage(content=f"Review skipped: PR #{pr_number} is {pr_state} (merged={pr_merged})")
                            ]
                            latency_ms = (time.time() - start_time) * 1000
                            metrics.record_node_complete("reviewer", trace_id, success=True, latency_ms=latency_ms)
                            return state
                    except Exception as pr_state_error:
                        # Fail open: if PR state check fails, continue with LLM review
                        # Publisher node's PR state guard will still catch merged/closed PRs
                        logger.warning(
                            "[Reviewer] PR state check failed, continuing with review",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "pr_number": pr_number,
                                "error": str(pr_state_error),
                                "pr_state_check": "error",
                                "outcome": "continue"
                            }
                        )

                # Issue #3379: diff_content is now fetched BEFORE this block
                # and stored in state, so LLM review can use it directly
                # Issue #3640: Pass escalation/retry counts for cost optimization hard cap
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
                    diff_files=diff_files,
                    escalation_count=state.get("escalation_count", 0),
                    retry_count=state.get("retry_count", 0)
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

                        # DIAGNOSTIC: Log LLM raw comment output for 422 debugging
                        # Extract only structural fields (file, line, start_line, end_line) - no message content
                        # Uses diagnostic_helper for consistent formatting, fallback, and size limits
                        from diagnostic_helper import format_diagnostic
                        raw_comment_structures = [
                            {
                                "file": c.get("file") or c.get("path") or c.get("file_path"),
                                "line": c.get("line"),
                                "start_line": c.get("start_line"),
                                "end_line": c.get("end_line"),
                                "severity": c.get("severity")
                            }
                            for c in raw_llm_comments
                        ]
                        diagnostic_data = {
                            "trace_id": trace_id,
                            "pr_number": pr_number,
                            "llm_provider": llm_provider,
                            "raw_comment_count": raw_comment_count,
                            "raw_comment_structures": raw_comment_structures
                        }
                        logger.info(
                            f"[Reviewer] DIAGNOSTIC: LLM raw comment output{format_diagnostic(diagnostic_data)}",
                            extra={"operation": "reviewer_diagnostic"}
                        )

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

                    # Issue #3379: diff_head_sha and diff_content are now stored BEFORE
                    # the LLM block (outside `if use_llm:`), enabling discovery audit
                    # for both LLM and CI-only modes. No need to store them again here.

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

        # Issue #3222: Deterministic Signals Ingestion - CI/Linters integration
        # Fetch deterministic signals from check runs and workflow annotations
        # This runs AFTER the LLM review to augment review_comments with factual data
        if pr_number and state.get("diff_head_sha"):
            try:
                from tools.signal_ingestion import (
                    fetch_signals,
                    signals_to_review_comments,
                    SignalSeverity
                )
                from tools.github_api import get_repo as get_repo_for_signals

                # Get repo object for signal ingestion
                signal_repo = None
                try:
                    signal_repo = github_repo
                except NameError:
                    signal_repo = get_repo_for_signals()

                if signal_repo:
                    # Fetch deterministic signals from CI/linters
                    signals = fetch_signals(
                        repo=signal_repo,
                        pr_number=pr_number,
                        head_sha=state["diff_head_sha"],
                        trace_id=trace_id
                    )

                    if signals:
                        # Store signals in state for downstream use
                        state["deterministic_signals_v1"] = [s.to_dict() for s in signals]

                        # Convert high-severity signals to review comments
                        signal_comments = signals_to_review_comments(signals, include_info=False)
                        if signal_comments:
                            state["review_comments"] = state.get("review_comments", []) + signal_comments

                            # Escalate severity if error-level signals found
                            error_count = sum(1 for s in signals if s.severity == SignalSeverity.ERROR)
                            if error_count > 0:
                                current_severity = state.get("review_severity", "none")
                                if current_severity in ("none", "low", "medium"):
                                    state["review_severity"] = "high"

                        logger.info(
                            f"[Reviewer] Deterministic signals ingested: {len(signals)} signals",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "signal_count": len(signals),
                                "error_count": sum(1 for s in signals if s.severity == SignalSeverity.ERROR),
                                "warning_count": sum(1 for s in signals if s.severity == SignalSeverity.WARNING),
                                "comment_count": len(signal_comments) if signal_comments else 0
                            }
                        )

            except Exception as signal_error:
                # Fail-open: signal ingestion failure should not block review
                logger.warning(
                    f"[Reviewer] Signal ingestion failed (non-blocking): {signal_error}",
                    extra={
                        "operation": "reviewer",
                        "trace_id": trace_id,
                        "error": str(signal_error)
                    }
                )

        # Issue #3369: Discovery Audit - Layer 2 of Discovery 全鏈路治理
        # Cross-reference PR diff with CI logs to detect silent test failures
        # This runs AFTER the LLM review but BEFORE building ReviewOutcome
        # State versioning: Use discovery_audit_v1 sub-object for forward compatibility
        if pr_number and state.get("diff_content"):
            try:
                from core.routing.discovery_auditor import (
                    DiscoveryAuditor,
                    AuditStatus
                )
                from tools.github_api import get_ci_test_logs, get_repo as get_repo_for_discovery

                # Reuse github_repo if available, otherwise fetch fresh
                discovery_repo = github_repo or get_repo_for_discovery()

                # Fetch CI test logs
                ci_logs_result = get_ci_test_logs(
                    repo=discovery_repo,
                    pr_number=pr_number,
                    head_sha=state.get("diff_head_sha"),
                    trace_id=trace_id
                )

                if ci_logs_result.get("success"):
                    # Run discovery audit
                    auditor = DiscoveryAuditor()
                    audit_result = auditor.audit_test_execution(
                        pr_diff=state["diff_content"],
                        ci_logs=ci_logs_result["logs"]
                    )

                    # Store results in versioned sub-object for forward compatibility
                    state["discovery_audit_v1"] = {
                        "status": audit_result.status.value,
                        "missing_tests": audit_result.missing_tests,
                        "new_test_files": audit_result.new_test_files,
                        "executed_tests": list(audit_result.executed_tests),
                        "message": audit_result.message
                    }

                    logger.info(
                        f"[Reviewer] Discovery audit completed: {audit_result.status.value}",
                        extra={
                            "operation": "reviewer",
                            "trace_id": trace_id,
                            "discovery_audit_status": audit_result.status.value,
                            "missing_tests_count": len(audit_result.missing_tests),
                            "new_test_files_count": len(audit_result.new_test_files)
                        }
                    )

                    # If silent failures detected, add to review comments and escalate severity
                    if audit_result.status == AuditStatus.REQUEST_CHANGES:
                        # Add discovery audit comment to review_comments
                        discovery_comment = {
                            "severity": "high",
                            "message": audit_result.to_review_comment() or audit_result.message,
                            "source": "discovery_auditor",
                            "missing_tests": audit_result.missing_tests
                        }
                        state["review_comments"] = state.get("review_comments", []) + [discovery_comment]

                        # Escalate severity to at least "high" if silent failures detected
                        current_severity = state.get("review_severity", "none")
                        if current_severity in ("none", "low", "medium"):
                            state["review_severity"] = "high"

                        # Update review_result to indicate discovery audit failure
                        if state.get("review_result"):
                            state["review_result"]["discovery_audit"] = "request_changes"
                            state["review_result"]["discovery_audit_message"] = audit_result.message

                        logger.warning(
                            "[Reviewer] Discovery audit detected silent test failures",
                            extra={
                                "operation": "reviewer",
                                "trace_id": trace_id,
                                "missing_tests": audit_result.missing_tests,
                                "severity_escalated_to": "high"
                            }
                        )

                else:
                    # CI logs not available (workflow still running or error)
                    # Fail-open: skip discovery audit but log the reason
                    logger.info(
                        f"[Reviewer] Discovery audit skipped: {ci_logs_result.get('error', 'unknown')}",
                        extra={
                            "operation": "reviewer",
                            "trace_id": trace_id,
                            "ci_status": ci_logs_result.get("ci_status"),
                            "skip_reason": ci_logs_result.get("error")
                        }
                    )
                    state["discovery_audit_v1"] = {
                        "status": "skipped",
                        "skip_reason": ci_logs_result.get("error"),
                        "ci_status": ci_logs_result.get("ci_status")
                    }

            except Exception as discovery_error:
                # Discovery audit failed - fail-open, don't block the review
                logger.warning(
                    f"[Reviewer] Discovery audit failed (fail-open): {discovery_error}",
                    extra={
                        "operation": "reviewer",
                        "trace_id": trace_id,
                        "error": str(discovery_error)
                    }
                )
                state["discovery_audit_v1"] = {
                    "status": "error",
                    "error": str(discovery_error)
                }

        # EPIC B-6: Build ReviewOutcome for Router interface (Issue #3130)
        # This provides a stable interface for Router to make routing decisions
        try:
            from core.routing.review_outcome import build_review_outcome
            review_outcome = build_review_outcome(
                review_comments=state.get("review_comments", []),
                review_severity=state.get("review_severity", "none"),
                review_result=state.get("review_result", {}),
                diff_truncated=state.get("diff_truncated", False)
            )
            state["review_outcome"] = review_outcome.model_dump()
            logger.info("[Reviewer] ReviewOutcome built successfully", extra={
                "operation": "reviewer",
                "trace_id": trace_id,
                "verdict": review_outcome.verdict,
                "severity": review_outcome.severity,
                "blocker_count": review_outcome.blocker_count
            })
        except Exception as outcome_error:
            # Fallback: build unknown outcome if ReviewOutcome construction fails
            from core.routing.review_outcome import build_unknown_outcome
            error_type = type(outcome_error).__name__
            error_msg = str(outcome_error)[:500]  # Truncate to avoid log bloat
            state["review_outcome"] = build_unknown_outcome(
                error=f"{error_type}: {error_msg}",
                diff_truncated=state.get("diff_truncated", False)
            )
            logger.warning(
                f"[Reviewer] ReviewOutcome build failed ({error_type}), using fallback",
                extra={
                    "operation": "reviewer",
                    "trace_id": trace_id,
                    "error_type": error_type,
                    "error_message": error_msg
                }
            )

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

        # EPIC B-6: Build unknown ReviewOutcome for error case
        from core.routing.review_outcome import build_unknown_outcome
        error_type = type(e).__name__
        error_msg = str(e)[:500]  # Truncate to avoid log bloat
        state["review_outcome"] = build_unknown_outcome(
            error=f"{error_type}: {error_msg}",
            diff_truncated=state.get("diff_truncated", False)
        )

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("reviewer", trace_id, success=success, latency_ms=latency_ms)
    if success:
        metrics.record_transition("reviewer", "decision", trace_id)
    return state


def should_use_dynamic_routing(state: AgentState) -> str:
    """
    #3431: Deterministic Canary Gating - Runtime routing decision.

    Determines whether to use dynamic routing (router) or legacy routing (decision)
    based on deterministic hash-based bucketing of the trace_id.

    This function is called at runtime for each workflow, enabling per-workflow
    canary gating. The decision is deterministic: same trace_id always routes
    to the same path.

    Decision Logic:
    1. If DYNAMIC_ROUTING_SAMPLE_RATE > 0: Use hash-based bucketing
       - Compute bucket from trace_id hash (0-99)
       - Route to "router" if bucket < sample_rate, else "decision"
    2. If DYNAMIC_ROUTING_SAMPLE_RATE == 0: Use ENABLE_DYNAMIC_ROUTING flag
       - Route to "router" if flag is True, else "decision"

    Returns:
        "router" for dynamic routing path, "decision" for legacy path
    """
    from core.flow.canary_gating import should_enable_dynamic_routing

    trace_id = state.get("trace_id", "unknown")
    metrics = _get_metrics()

    try:
        use_dynamic = should_enable_dynamic_routing(trace_id)

        if use_dynamic:
            logger.info(
                f"[CANARY_ROUTING] trace_id={trace_id[:8]}... -> router (dynamic)"
            )
            metrics.record_transition("reviewer", "router", trace_id)
            return "router"
        else:
            logger.info(
                f"[CANARY_ROUTING] trace_id={trace_id[:8]}... -> decision (legacy)"
            )
            metrics.record_transition("reviewer", "decision", trace_id)
            return "decision"

    except Exception as e:
        # Fail-safe: default to legacy routing on any error
        logger.warning(
            f"[CANARY_ROUTING] Error determining routing for trace_id={trace_id}: {e}, "
            f"defaulting to legacy decision path"
        )
        metrics.record_transition("reviewer", "decision", trace_id)
        return "decision"


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


def router_node(state: AgentState) -> AgentState:
    """
    Router Node: LLM-driven dynamic routing using Hybrid Router (C-2).

    EPIC C Phase C-6: Graph Wiring for Hybrid Router (Issue #3182)

    This node replaces decision_node when ENABLE_DYNAMIC_ROUTING=true.
    It uses the HybridRoutingPolicy to make routing decisions based on
    ReviewOutcome fields (verdict, severity, summary, blocker_count).

    Issue #3366: CI Failure Fast Path (Two-Layer Routing Optimization)
    When ci_failure_trigger=True and ci_state != "success", short-circuit
    to fixer without LLM routing. This implements the "disaster recovery"
    response level for self-healing systems.

    Routing Rules (from HybridRoutingPolicy):
    1. approve -> publisher (Fast Path)
    2. blocked/unknown -> decision + HITL (Fast Path)
    3. request_changes + low severity -> fixer (Fast Path)
    4. request_changes + medium+ severity -> LLM decides (Slow Path)
    5. comment -> fixer (Fast Path)

    Event Codes (greppable):
    - [ROUTER_FAST_PATH] - Deterministic routing
    - [ROUTER_SLOW_PATH] - LLM-driven routing
    - [ROUTER_HITL] - Human-in-the-loop required
    - [ROUTER_LLM_FALLBACK] - LLM failed, using deterministic fallback
    - [CI_FAILURE_ROUTER_SHORT_CIRCUIT] - CI failure fast path triggered

    Args:
        state: Current agent state with review_outcome fields

    Returns:
        Updated state with merge_decision and requires_hitl_approval
    """
    from core.flow.hybrid_router import get_hybrid_router
    from core.flow.router_metrics import get_router_metrics, DecisionMode
    from metrics import get_canary_metrics

    start_time = time.time()
    router_metrics = get_router_metrics()
    canary_metrics = get_canary_metrics()
    metrics = _get_metrics()

    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("router", trace_id)

    ci_failure_trigger = state.get("ci_failure_trigger", False)
    ci_state = state.get("ci_state", "unknown")

    # Issue #3366: Observability log for CI failure fast path debugging
    # This log helps diagnose if ci_failure_trigger is being lost in state transitions
    logger.info(
        f"[ROUTER_STATE_DEBUG] Router entry state: ci_failure_trigger={ci_failure_trigger} ci_state={ci_state}",
        extra={
            "operation": "router",
            "trace_id": trace_id,
            "ci_failure_trigger": ci_failure_trigger,
            "ci_failure_trigger_type": type(ci_failure_trigger).__name__,
            "ci_state": ci_state,
        }
    )

    if ci_failure_trigger and ci_state != "success":
        # Issue #3366: CI failure fast path - use monotonic time for accurate latency
        # (time.monotonic() is immune to system clock adjustments like NTP)
        fast_path_start = time.monotonic()
        logger.info(
            f"[CI_FAILURE_ROUTER_SHORT_CIRCUIT] CI failure fast path triggered "
            f"trace_id={trace_id} ci_state={ci_state}",
            extra={
                "operation": "router",
                "trace_id": trace_id,
                "ci_failure_trigger": True,
                "ci_state": ci_state,
            }
        )
        state["merge_decision"] = "needs_fix"
        state["requires_hitl_approval"] = False
        state["routing_decision"] = {
            "version": 1,
            "next_node": "fixer",
            "reasoning": "CI failure fast path: bypassing LLM routing for auto-fix",
            "risk_assessment": "low",
            "requires_hitl_approval": False,
        }
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Router: CI failure fast path -> fixer")
        ]
        latency_ms = (time.monotonic() - fast_path_start) * 1000
        metrics.record_node_complete("router", trace_id, success=True, latency_ms=latency_ms)

        router_metrics.record_decision(
            trace_id=trace_id,
            latency_ms=latency_ms,
            success=True,
            chosen_node="fixer",
            fallback_reason=None,
            decision_mode=DecisionMode.CI_FAILURE_FAST_PATH,
        )

        if canary_metrics:
            canary_metrics.record_router_decision(
                next_node="fixer",
                success=True,
                latency_ms=latency_ms,
                decision_mode=DecisionMode.CI_FAILURE_FAST_PATH,
                fallback_reason=None,
            )

        return state

    # Extract ReviewOutcome fields from state
    # These are set by reviewer_node via ReviewOutcome schema
    review_outcome = state.get("review_outcome", {})
    verdict = review_outcome.get("verdict") or state.get("merge_decision", "pending")
    severity = review_outcome.get("severity") or state.get("review_severity", "none")
    summary = review_outcome.get("summary", "")
    blocker_count = review_outcome.get("blocker_count", 0)

    # Map old decision values to verdict if needed
    if verdict == "approve":
        pass  # Already correct
    elif verdict == "needs_fix":
        verdict = "request_changes"
    elif verdict == "request_changes":
        pass  # Already correct
    elif verdict == "pending":
        verdict = "unknown"

    logger.info("[Router] Starting Hybrid Router decision", extra={
        "operation": "router",
        "trace_id": trace_id,
        "verdict": verdict,
        "severity": severity,
        "blocker_count": blocker_count,
    })

    routing_start = time.monotonic()
    routing_success = False
    routing_next_node = "decision"
    routing_fallback_reason = None
    routing_decision_mode = DecisionMode.FAST_PATH

    try:
        # Get Hybrid Router instance (with LLM for slow path)
        router = get_hybrid_router(use_llm=True)

        # Make routing decision with structured metadata (Issue #3496)
        # route_with_meta() returns RoutingResult with decision_mode as structured field
        # This eliminates the need for string inference from reasoning text
        routing_result = router.route_with_meta(
            verdict=verdict,
            severity=severity,
            summary=summary,
            blocker_count=blocker_count
        )
        decision = routing_result.decision

        # Map routing decision to state fields
        next_node = decision.next_node
        requires_hitl = decision.requires_hitl_approval
        routing_success = True
        routing_next_node = next_node

        # Use structured decision_mode from RoutingResult (Issue #3496)
        # No more string inference - decision_mode is set by the router itself
        routing_decision_mode = routing_result.decision_mode
        routing_fallback_reason = routing_result.fallback_reason

        # Map next_node to merge_decision for compatibility with existing flow
        if next_node == "publisher":
            merge_decision = "approve"
        elif next_node == "fixer":
            merge_decision = "needs_fix"
        elif next_node == "executor":
            merge_decision = "needs_fix"  # Executor also means we need to fix/regenerate
        elif next_node == "decision":
            # HITL required - force request_changes to prevent infinite loop
            # (state.get could return "pending" which routes to monitor_ci, causing loop)
            merge_decision = "request_changes"
        else:
            merge_decision = "request_changes"

        state["merge_decision"] = merge_decision
        state["requires_hitl_approval"] = requires_hitl
        state["routing_decision"] = {
            "version": 1,
            "next_node": next_node,
            "reasoning": decision.reasoning,
            "risk_assessment": decision.risk_assessment,
            "requires_hitl_approval": requires_hitl,
        }

        logger.info("[Router] Hybrid Router decision complete", extra={
            "operation": "router",
            "trace_id": trace_id,
            "next_node": next_node,
            "merge_decision": merge_decision,
            "requires_hitl_approval": requires_hitl,
            "reasoning": decision.reasoning,
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Router decision: {next_node}.")
        ]

    except Exception as e:
        # Fallback to deterministic decision on any error
        logger.error(f"[Router] Hybrid Router failed, falling back to decision_node: {e}", extra={
            "operation": "router",
            "trace_id": trace_id,
            "error": str(e),
        })

        # Use decision_node logic as fallback
        ci_state = state.get("ci_state", "unknown")
        code_quality_score = state.get("code_quality_score", 100)

        if ci_state == "failure" or severity == "critical" or code_quality_score < 50:
            merge_decision = "needs_fix"
            routing_next_node = "fixer"
        elif severity == "high" or code_quality_score < 70:
            merge_decision = "request_changes"
            routing_next_node = "decision"
        elif ci_state == "success" and code_quality_score >= 70:
            merge_decision = "approve"
            routing_next_node = "publisher"
        else:
            merge_decision = "pending"
            routing_next_node = "decision"

        state["merge_decision"] = merge_decision
        state["requires_hitl_approval"] = False

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Router fallback decision: {merge_decision}")
        ]

        routing_success = False
        routing_fallback_reason = "router_exception"
        routing_decision_mode = DecisionMode.OUTER_FALLBACK

    routing_latency_ms = (time.monotonic() - routing_start) * 1000
    router_metrics.record_decision(
        trace_id=trace_id,
        latency_ms=routing_latency_ms,
        success=routing_success,
        chosen_node=routing_next_node,
        fallback_reason=routing_fallback_reason,
        decision_mode=routing_decision_mode,
    )

    if canary_metrics:
        canary_metrics.record_router_decision(
            next_node=routing_next_node,
            success=routing_success,
            latency_ms=routing_latency_ms,
            decision_mode=routing_decision_mode,
            fallback_reason=routing_fallback_reason,
        )

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("router", trace_id, success=True, latency_ms=latency_ms)

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


def hitl_gate_node(state: AgentState) -> AgentState:
    """
    HITL Gate Node: Controls human-in-the-loop approval flow.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    This node is placed downstream of the decision node (router) and implements
    the interrupt/resume mechanism for human approval.

    CTO Directive (Separation of Concerns):
    - Router's Job: DECIDE (set requires_hitl_approval=True in state)
    - Orchestrator's Job: EXECUTE (implement interrupt logic in LangGraph)

    Flow:
    1. If requires_hitl_approval=True AND hitl_approved=False:
       - Call interrupt() to pause the graph
       - Wait for human approval via Command(resume=True)
    2. If requires_hitl_approval=True AND hitl_approved=True:
       - Continue (approval already granted)
    3. If requires_hitl_approval=False:
       - Continue without interruption

    The hitl_approved flag is set to True after resume to prevent infinite loops.
    It is reset to False by finalizer_node to prevent state leakage.

    Args:
        state: Current agent state

    Returns:
        Updated state with hitl_approved set appropriately
    """
    start_time = time.time()
    metrics = _get_metrics()
    trace_id = state.get("trace_id", "unknown")

    metrics.record_node_start("hitl_gate", trace_id)

    requires_hitl = state.get("requires_hitl_approval", False)
    hitl_approved = state.get("hitl_approved", False)

    logger.info("[HITL_GATE] Checking HITL approval requirement", extra={
        "operation": "hitl_gate",
        "trace_id": trace_id,
        "requires_hitl_approval": requires_hitl,
        "hitl_approved": hitl_approved,
    })

    if requires_hitl and not hitl_approved:
        logger.info("[HITL_GATE] HITL approval required, pausing workflow", extra={
            "operation": "hitl_gate",
            "trace_id": trace_id,
            "event_code": "ROUTER_HITL",
        })

        state["messages"] = state.get("messages", []) + [
            AIMessage(content="[HITL_GATE] Workflow paused. Human approval required before proceeding.")
        ]

        approval = interrupt({
            "type": "hitl_approval_required",
            "trace_id": trace_id,
            "message": "Human approval required before proceeding with this action.",
            "merge_decision": state.get("merge_decision", "unknown"),
            "review_severity": state.get("review_severity", "unknown"),
            "code_quality_score": state.get("code_quality_score", 100),
        })

        if approval:
            logger.info("[HITL_GATE] HITL approval received, resuming workflow", extra={
                "operation": "hitl_gate",
                "trace_id": trace_id,
                "approval": approval,
            })
            state["hitl_approved"] = True
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"[HITL_GATE] Human approval received: {approval}. Resuming workflow.")
            ]
        else:
            # HIGH SEVERITY FIX: Prevent infinite loop on rejection
            # If approval is falsy (rejected/None), we must terminate the workflow
            # by setting merge_decision to a value that routes to finalizer.
            # The should_fix_or_finalize routing logic sends all non-pending,
            # non-needs_fix values to finalizer, so "rejected" will work.
            logger.warning("[HITL_GATE] HITL approval not received or rejected. Terminating workflow.", extra={
                "operation": "hitl_gate",
                "trace_id": trace_id,
                "event_code": "ROUTER_HITL_REJECTED",
            })
            state["hitl_approved"] = False
            state["error"] = "Workflow terminated due to HITL rejection."
            state["merge_decision"] = "rejected"
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="[HITL_GATE] Human approval rejected. Workflow will terminate.")
            ]

    elif requires_hitl and hitl_approved:
        logger.info("[HITL_GATE] HITL already approved, continuing", extra={
            "operation": "hitl_gate",
            "trace_id": trace_id,
        })
    else:
        logger.info("[HITL_GATE] No HITL approval required, continuing", extra={
            "operation": "hitl_gate",
            "trace_id": trace_id,
        })

    latency_ms = (time.time() - start_time) * 1000
    metrics.record_node_complete("hitl_gate", trace_id, success=True, latency_ms=latency_ms)

    return state


def should_proceed_after_hitl_gate(state: AgentState) -> str:
    """
    Determines next step after HITL gate node.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    Routes based on the original decision from should_fix_or_finalize:
    - fix: If merge_decision is needs_fix and retries available
    - monitor_ci: If merge_decision is pending (waiting for CI)
    - finalize: If approved, request_changes, or max retries reached

    This function mirrors should_fix_or_finalize but is called after HITL gate.

    EPIC D Issue #3487: Extended to handle SeniorCoder complexity abort flow.
    When hitl_reason is "senior_coder_complexity_abort" and hitl_approved is True,
    route to executor to continue the workflow (skip re-running fixer).
    """
    trace_id = state.get("trace_id", "unknown")
    hitl_reason = state.get("hitl_reason", "")
    # Use strict boolean check to prevent truthy string values like "False"
    hitl_approved = state.get("hitl_approved") is True
    metrics = _get_metrics()

    # EPIC D Issue #3487: After HITL approval for SeniorCoder complexity abort,
    # route directly to executor instead of back to fixer
    if hitl_reason == "senior_coder_complexity_abort" and hitl_approved:
        logger.info(
            f"[HITL_GATE_ROUTING] SeniorCoder complexity abort approved, routing to executor. "
            f"trace_id={trace_id}",
            extra={
                "operation": "hitl_gate_routing",
                "trace_id": trace_id,
                "event_code": "SENIOR_CODER_HITL_APPROVED",
                "hitl_reason": hitl_reason,
            }
        )
        metrics.record_transition("hitl_gate", "executor", trace_id)
        return "executor"

    # P1 Feature: After HITL approval for multi-file limit exceeded,
    # route directly to executor (human has acknowledged the limitation)
    if hitl_reason == "multi_file_limit_exceeded" and hitl_approved:
        logger.info(
            f"[HITL_GATE_ROUTING] Multi-file limit exceeded approved, routing to executor. "
            f"trace_id={trace_id}",
            extra={
                "operation": "hitl_gate_routing",
                "trace_id": trace_id,
                "event_code": "MULTI_FILE_HITL_APPROVED",
                "hitl_reason": hitl_reason,
            }
        )
        metrics.record_transition("hitl_gate", "executor", trace_id)
        return "executor"

    return should_fix_or_finalize(state)


def should_proceed_after_fixer(state: AgentState) -> str:
    """
    Determines next step after fixer node.

    EPIC D Issue #3487: SeniorCoder HITL Gate

    Routes based on HITL requirement:
    - finalizer: If loop_protection_triggered is True (prevents infinite recursion)
    - hitl_gate: If requires_hitl_approval is True and hitl_approved is False
      (SeniorCoder determined task complexity is too high)
    - ci_monitor: If ci_failure_trigger is True (CI failure auto-fix flow)
      This bypasses executor_node which calls graph.execute() (FAQ doc flow)
      that has ValueGate blocking low-significance changesets.
    - executor: Default path for normal fixer completion

    CTO Directive (Separation of Concerns):
    - Fixer's Job: DECIDE (set requires_hitl_approval=True in state)
    - HITL Gate's Job: EXECUTE (implement interrupt logic in LangGraph)

    This follows the Blueprint architecture where Router DECIDES and
    Orchestrator EXECUTES, keeping HITL interrupt logic centralized.
    """
    trace_id = state.get("trace_id", "unknown")
    # Use strict boolean checks to prevent truthy string values like "False"
    requires_hitl = state.get("requires_hitl_approval") is True
    hitl_approved = state.get("hitl_approved") is True
    hitl_reason = state.get("hitl_reason", "")
    ci_failure_trigger = state.get("ci_failure_trigger") is True
    loop_protection_triggered = state.get("loop_protection_triggered") is True
    metrics = _get_metrics()

    # CRITICAL: Route to finalizer if loop protection triggered
    # This prevents infinite recursion: fixer → ci_monitor → reviewer → fixer → ...
    if loop_protection_triggered:
        logger.warning(
            f"[FIXER_ROUTING] Loop protection triggered, routing to finalizer to prevent recursion. "
            f"trace_id={trace_id}",
            extra={
                "operation": "fixer_routing",
                "trace_id": trace_id,
                "event_code": "FIXER_LOOP_PROTECTION_TO_FINALIZER",
                "loop_protection_triggered": True,
            }
        )
        metrics.record_transition("fixer", "finalizer", trace_id)
        return "finalizer"

    # Route to HITL gate if approval is required and not yet approved
    if requires_hitl and not hitl_approved:
        logger.info(
            f"[FIXER_ROUTING] HITL approval required, routing to hitl_gate. "
            f"hitl_reason={hitl_reason}, trace_id={trace_id}",
            extra={
                "operation": "fixer_routing",
                "trace_id": trace_id,
                "event_code": "FIXER_TO_HITL_GATE",
                "hitl_reason": hitl_reason,
            }
        )
        metrics.record_transition("fixer", "hitl_gate", trace_id)
        return "hitl_gate"

    # CI failure auto-fix: bypass executor_node (which calls graph.execute with ValueGate)
    # Route directly to ci_monitor to check if the fix was successful
    if ci_failure_trigger:
        logger.info(
            f"[FIXER_ROUTING] CI failure auto-fix complete, routing to ci_monitor. "
            f"ci_failure_trigger={ci_failure_trigger}, trace_id={trace_id}",
            extra={
                "operation": "fixer_routing",
                "trace_id": trace_id,
                "event_code": "CI_FAILURE_FIXER_TO_CI_MONITOR",
                "ci_failure_trigger": ci_failure_trigger,
            }
        )
        metrics.record_transition("fixer", "ci_monitor", trace_id)
        return "ci_monitor"

    # Default: proceed to executor
    metrics.record_transition("fixer", "executor", trace_id)
    return "executor"


class FileLevelComment(TypedDict):
    """
    TypedDict for file-level comment structure.

    EPIC B Phase 3: Structured type for file-level comments (MorningAI Code Review feedback)
    Provides better IDE support and type safety for comment handling.
    """
    file: str
    message: str
    severity: NotRequired[str]
    line: NotRequired[int]


def _build_file_level_appendix(
    file_level_comments: list[FileLevelComment],
    line_drift_detected: bool = False,
    max_comments: int = 10,
    non_diff_filtered_count: int = 0,
    non_diff_filtered_files: int = 0
) -> str:
    """
    Build markdown appendix for file-level comments.

    EPIC B Phase 3 P2: Unified file-level delivery logic
    This helper ensures consistent formatting across all file-level delivery paths.

    Args:
        file_level_comments: List of file-level comment dicts (see FileLevelComment TypedDict)
        line_drift_detected: Whether line drift was detected (adds note)
        max_comments: Maximum comments to include (default: 10)
        non_diff_filtered_count: Number of comments filtered for non-diff files (EPIC B Optimization)
        non_diff_filtered_files: Number of files that had comments filtered (EPIC B Optimization)

    Returns:
        Markdown string for file-level comments appendix
    """
    if not file_level_comments and non_diff_filtered_count == 0:
        return ""

    # Use list + join for efficient string building (Gemini feedback)
    parts: list[str] = []

    if line_drift_detected:
        parts.append("\n\n*Note: New commits detected since review. Comments delivered as file-level for safety.*")

    # EPIC B Optimization: Add transparency note for filtered non-diff comments
    if non_diff_filtered_count > 0:
        parts.append(
            f"\n\n*Note: {non_diff_filtered_count} comments for {non_diff_filtered_files} "
            f"files not in this PR diff were filtered to reduce noise from pre-existing issues.*"
        )

    if file_level_comments:
        parts.append("\n\n### File-Level Comments\n\n")

    # Limit comments to prevent overly long review bodies
    comments_to_show = file_level_comments[:max_comments]
    truncated_count = len(file_level_comments) - len(comments_to_show)

    for comment in comments_to_show:
        file_path = comment.get("file", "General")
        message = comment.get("message", "")
        severity = comment.get("severity", "info")
        parts.append(f"**{file_path}** ({severity})\n{message}\n\n")

    if truncated_count > 0:
        parts.append(f"*...and {truncated_count} more file-level comments (truncated)*\n\n")

    return "".join(parts)


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
        logger.info("[Publisher] No review comments to publish, posting summary report", extra={
            "operation": "publisher",
            "trace_id": trace_id,
            "pr_number": pr_number
        })

        # Issue #3220: Post Summary Report when no inline comments
        # This provides visibility that the Reviewer Agent ran and what it found
        # Issue #3221: Use standardized PRSummary schema for consistent output
        try:
            from tools.github_api import get_repo, post_pr_review
            from core.routing.pr_summary import build_pr_summary

            # Build Summary Report using standardized PRSummary schema (Issue #3221)
            review_outcome = state.get("review_outcome", {})
            review_result = state.get("review_result", {})
            code_quality_score = state.get("code_quality_score", 0)

            # Build PRSummary artifact
            pr_summary = build_pr_summary(
                review_outcome=review_outcome,
                review_result=review_result,
                code_quality_score=code_quality_score,
                trace_id=trace_id,
                pr_number=pr_number,
                repo=state.get("repo"),
                head_sha=state.get("diff_head_sha")
            )

            # Render to GitHub markdown
            summary_body = pr_summary.to_github_markdown()

            # Extract display values for logging
            verdict_emoji = pr_summary.verdict_label
            llm_decision = pr_summary.display_decision

            repo = get_repo()
            # Issue #3253: Get commit_id for Redis dedup idempotency
            # Normalize to None if not a valid non-empty string (defensive)
            raw_head_sha = state.get("diff_head_sha")
            stored_head_sha = raw_head_sha if isinstance(raw_head_sha, str) and raw_head_sha else None
            if repo:
                result = post_pr_review(
                    repo=repo,
                    pr_number=pr_number,
                    comments=[],
                    summary=summary_body,
                    commit_id=stored_head_sha  # Enable Redis dedup
                )

                state["publish_result"]["success"] = result.get("success", False)
                state["publish_result"]["summary_report_posted"] = result.get("success", False)
                state["publish_result"]["dry_run"] = result.get("dry_run", False)

                if result.get("success"):
                    mode = "[DRY-RUN]" if result.get("dry_run") else ""
                    logger.info(f"[Publisher] Summary report posted {mode}", extra={
                        "operation": "publisher",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "verdict": llm_decision,
                        "score": code_quality_score,
                        "dry_run": result.get("dry_run", False)
                    })
                    state["messages"] = state.get("messages", []) + [
                        AIMessage(content=f"Summary report posted {mode}: {verdict_emoji} (Score: {code_quality_score})")
                    ]
                else:
                    logger.warning("[Publisher] Failed to post summary report", extra={
                        "operation": "publisher",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "error": result.get("error")
                    })
                    state["publish_result"]["error"] = result.get("error")
                    state["messages"] = state.get("messages", []) + [
                        AIMessage(content="Failed to post summary report")
                    ]
            else:
                logger.warning("[Publisher] Repository not available for summary report", extra={
                    "operation": "publisher",
                    "trace_id": trace_id,
                    "pr_number": pr_number
                })
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content="Repository not available for summary report")
                ]

        except Exception as e:
            logger.warning(f"[Publisher] Failed to post summary report: {e}", extra={
                "operation": "publisher",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "error": str(e)
            })
            state["publish_result"]["error"] = str(e)
            state["messages"] = state.get("messages", []) + [
                AIMessage(content=f"Failed to post summary report: {e}")
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
        validate_inline_comments,
        filter_non_diff_file_comments
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
    # Phase 2: Get stored head_sha for commit pinning
    # Fix: This should now always be set by reviewer_node (moved outside if diff_content: block)
    # Issue #3253: Normalize to None if not a valid non-empty string (defensive)
    _raw_head_sha = state.get("diff_head_sha")
    stored_head_sha = _raw_head_sha if isinstance(_raw_head_sha, str) and _raw_head_sha else None
    downgraded_count = 0
    line_drift_detected = False

    # DIAGNOSTIC: Log stored_head_sha presence for commit pinning verification
    # Note: diff_content is already sanitized by reviewer_node, so length reflects sanitized content
    # Emit both sanitized_diff_length (new) and diff_content_length (legacy) for backward compatibility
    _diff_len = len(diff_content) if diff_content else 0
    logger.info("[Publisher] Retrieved state for commit pinning", extra={
        "operation": "publisher",
        "trace_id": trace_id,
        "pr_number": pr_number,
        "stored_head_sha": stored_head_sha[:8] if stored_head_sha else None,
        "has_diff_content": bool(diff_content),
        "sanitized_diff_length": _diff_len,
        "diff_content_length": _diff_len  # Legacy key for backward compatibility
    })

    if diff_content and inline_comments:
        allowed_lines_map = parse_diff_allowed_lines(diff_content)

        # EPIC B Optimization: Filter comments for files NOT in the PR diff
        # This reduces noise from pre-existing issues in unchanged files
        # Controlled by REVIEWER_FILTER_NON_DIFF_FILES feature flag (default: True)
        non_diff_filtered_count = 0
        if settings.reviewer_filter_non_diff_files:
            kept_comments, filtered_comments, filter_stats = filter_non_diff_file_comments(
                inline_comments,
                allowed_lines_map
            )
            non_diff_filtered_count = filter_stats["filtered_count"]

            if non_diff_filtered_count > 0:
                logger.info(
                    f"[Publisher] EPIC B Optimization: Filtered {non_diff_filtered_count} "
                    f"comments for {filter_stats['filtered_file_count']} files not in PR diff",
                    extra={
                        "operation": "publisher",
                        "trace_id": trace_id,
                        "pr_number": pr_number,
                        "filtered_count": non_diff_filtered_count,
                        "kept_count": filter_stats["kept_count"],
                        "filtered_files": filter_stats["filtered_files"][:5],
                    }
                )
                inline_comments = kept_comments

            # Store filter stats in publish_result for telemetry
            state["publish_result"]["non_diff_filtered_count"] = non_diff_filtered_count
            state["publish_result"]["non_diff_filtered_files"] = filter_stats["filtered_file_count"]

        # DIAGNOSTIC: Log allowed_lines_map summary for 422 debugging
        # Uses diagnostic_helper for consistent formatting, fallback, and size limits
        from diagnostic_helper import format_diagnostic
        from review_comment_schema import get_diff_coverage_info
        diff_coverage = get_diff_coverage_info(allowed_lines_map)
        coverage_diagnostic = {
            "trace_id": trace_id,
            "pr_number": pr_number,
            "diff_coverage": diff_coverage,
            "sanitized_diff_length": _diff_len,
            "diff_content_length": _diff_len,  # Legacy key for backward compatibility
            "diff_truncated": diff_truncated,
            "stored_head_sha": stored_head_sha[:8] if stored_head_sha else None,
            "non_diff_filtered_count": non_diff_filtered_count
        }
        logger.info(
            f"[Publisher] DIAGNOSTIC: Diff coverage for validation{format_diagnostic(coverage_diagnostic)}",
            extra={"operation": "publisher_diagnostic"}
        )

        # DIAGNOSTIC: Log each comment's validation decision
        for idx, comment in enumerate(inline_comments):
            file_path = comment.get("file")
            start_line = comment.get("start_line")
            end_line = comment.get("end_line")
            file_info = allowed_lines_map.get(file_path)
            file_in_diff = file_path in allowed_lines_map
            allowed_lines = file_info["allowed_lines"] if file_info else set()
            line_in_allowed = end_line in allowed_lines if end_line else False
            start_in_allowed = start_line in allowed_lines if start_line else True
            validation_diagnostic = {
                "trace_id": trace_id,
                "comment_index": idx,
                "file": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "file_in_diff": file_in_diff,
                "end_line_in_allowed": line_in_allowed,
                "start_line_in_allowed": start_in_allowed,
                "allowed_lines_sample": sorted(list(allowed_lines))[:20] if allowed_lines else []
            }
            logger.info(
                f"[Publisher] DIAGNOSTIC: Comment {idx + 1} validation check{format_diagnostic(validation_diagnostic)}",
                extra={"operation": "publisher_diagnostic"}
            )

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
                # EPIC B Optimization: Include filtered non-diff comments count for transparency
                _non_diff_filtered = state["publish_result"].get("non_diff_filtered_count", 0)
                _non_diff_files = state["publish_result"].get("non_diff_filtered_files", 0)
                file_level_body = "## MorningAI Code Review"
                file_level_body += _build_file_level_appendix(
                    file_level_comments,
                    line_drift_detected=line_drift_detected,
                    non_diff_filtered_count=_non_diff_filtered,
                    non_diff_filtered_files=_non_diff_files
                )

                repo = get_repo()
                # Issue #3253: Pass commit_id for Redis dedup idempotency
                result = post_pr_review(
                    repo=repo,
                    pr_number=pr_number,
                    comments=[],
                    summary=file_level_body,
                    commit_id=stored_head_sha  # Enable Redis dedup
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
        from core.routing.pr_summary import build_pr_summary

        repo = get_repo()

        # Issue #3221: Use standardized PRSummary schema for consistent output
        # EPIC B Phase 3 P2: Build summary with file-level comments appendix
        # This ensures file-level comments are delivered even when inline comments exist
        review_outcome = state.get("review_outcome", {})
        review_result = state.get("review_result", {})
        code_quality_score = state.get("code_quality_score", 0)

        # Convert file_level_comments to format expected by PRSummary
        file_level_comment_dicts = [
            {
                "file": c.get("file", c.get("path", "unknown")),
                "message": c.get("body", c.get("message", "")),
                "downgrade_reason": c.get("downgrade_reason")
            }
            for c in file_level_comments
        ] if file_level_comments else []

        # Build PRSummary artifact with file-level comments
        pr_summary = build_pr_summary(
            review_outcome=review_outcome,
            review_result=review_result,
            code_quality_score=code_quality_score,
            file_level_comments=file_level_comment_dicts,
            trace_id=trace_id,
            pr_number=pr_number,
            repo=state.get("repo"),
            head_sha=stored_head_sha
        )

        # Render simple markdown (header + file-level appendix) for inline comment reviews
        review_summary = pr_summary.to_simple_markdown()

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
            skipped_reason = result.get("skipped_reason")
            if skipped_reason:
                state["publish_result"]["skipped_reason"] = skipped_reason
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content=f"Review skipped for PR #{pr_number}: {skipped_reason}")
                ]
                logger.info("[Publisher] Review skipped", extra={
                    "operation": "publisher",
                    "trace_id": trace_id,
                    "pr_number": pr_number,
                    "skipped_reason": skipped_reason,
                    "outcome": "skipped"
                })
            else:
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
                    "downgraded": is_fallback,
                    "outcome": "published"
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

    # EPIC C Phase C-5: HITL Wiring (Issue #3155)
    # Reset HITL-related flags to prevent state leakage between executions.
    # CTO Directive: "實作 hitl_approved 時，請確保它在任務完成後會被重置 (Reset)，
    # 以免影響同一個 Session 的下一次執行。"
    # Refactored per code review: consolidated into loop for maintainability
    hitl_flags_to_reset = ["hitl_approved", "requires_hitl_approval"]
    for flag in hitl_flags_to_reset:
        if state.get(flag):
            logger.info(f"[Finalizer] Resetting {flag} to False", extra={
                "operation": "finalizer",
                "trace_id": trace_id,
            })
            state[flag] = False

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

        regression_metrics = regression_result.get("metrics", {})
        logger.info("[Evaluation] Capability regression detection completed", extra={
            "operation": "evaluation",
            "trace_id": trace_id,
            "health_status": health_status,
            "has_regression": has_regression,
            "sample_count": regression_result.get("sample_count"),
            "code_changing_count": regression_result.get("code_changing_count"),
            "success_rate": regression_metrics.get("success_rate"),
            "ci_pass_rate": regression_metrics.get("ci_pass_rate"),
            "ci_observed_rate": regression_metrics.get("ci_observed_rate"),
            "fixer_success_rate": regression_metrics.get("fixer_success_rate"),
            "pr_creation_rate": regression_metrics.get("pr_creation_rate"),
            "regressions": regression_result.get("regressions", []),
            "thresholds": regression_result.get("thresholds", {})
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


def create_orchestrator_graph(entry_point: str = "planner", checkpointer=None):
    """
    Creates the LangGraph StateGraph for orchestration

    Phase 2 PR-1813 Update (Agent Evaluation):
        planner → security_advisor → governance_advisor → cost_advisor → permission_advisor → reputation_advisor → policy_enforcement → (executor | finalizer) → ci_monitor → reviewer → decision → hitl_gate → (fixer if needed) → finalizer → evaluation → END

    EPIC C Phase C-5: HITL Wiring (Issue #3155):
        - hitl_gate: Human-in-the-loop approval gate node
        - Placed downstream of decision node (router)
        - Checks requires_hitl_approval flag and calls interrupt() if needed
        - CTO Directive: Router DECIDES, Orchestrator EXECUTES

    Phase 7 Issue #2211 Review Follow-up Mode:
        review_intake → planner → ... (same as above)
        Entry point can be "review_intake" for review follow-up tasks

    Issue #3366: CI Failure Fast Path (Two-Layer Routing Optimization)
        ci_monitor → reviewer → router → hitl_gate → fixer → ...
        Entry point can be "ci_monitor" for CI failure auto-fix tasks.
        This skips planner + 5 advisors for faster disaster recovery.
        Combined with router_node short-circuit for defense-in-depth.

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

    Fix (Dec 2025) - Connection Pooling:
        Added checkpointer parameter to allow callers to pass in a checkpointer
        with proper connection lifecycle management (e.g., from postgres_checkpointer_context()).
        If checkpointer is None, falls back to get_checkpointer() for Redis/Memory.

    Args:
        entry_point: Entry point node name ("planner", "review_intake", "internal_review", or "ci_monitor")
        checkpointer: Optional checkpointer instance. If None, uses get_checkpointer() fallback.

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
    # EPIC C Phase C-6: Router node for Hybrid Router (Issue #3182)
    # Only added when ENABLE_DYNAMIC_ROUTING=true
    workflow.add_node("router", router_node)
    workflow.add_node("fixer", fixer_node)
    # EPIC B Phase B-3: Publisher node for GitHub inline comment posting
    workflow.add_node("publisher", publisher_node)
    workflow.add_node("finalizer", finalizer_node)
    # Phase 2 PR-1813: Agent Evaluation node
    workflow.add_node("evaluation", evaluation_node)
    # EPIC C Phase C-5: HITL Gate node for human-in-the-loop approval (Issue #3155)
    workflow.add_node("hitl_gate", hitl_gate_node)

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

    # EPIC C Phase C-6: Graph Wiring for Hybrid Router (Issue #3182)
    # #3431: Deterministic Canary Gating for Flow Router v3
    #
    # Per-workflow routing decision using conditional_edges:
    # - Both paths (router and decision) are wired in the graph
    # - Runtime decision based on should_use_dynamic_routing(state)
    # - Uses hash-based bucketing of trace_id for deterministic assignment
    # - Same trace_id always routes to same path (no random flipping)
    #
    # Decision Logic (in should_use_dynamic_routing):
    # 1. If DYNAMIC_ROUTING_SAMPLE_RATE > 0: Use hash-based bucketing
    #    - Compute bucket from trace_id hash (0-99)
    #    - Route to "router" if bucket < sample_rate, else "decision"
    # 2. If DYNAMIC_ROUTING_SAMPLE_RATE == 0: Use ENABLE_DYNAMIC_ROUTING flag
    sample_rate = getattr(settings, 'dynamic_routing_sample_rate', 0)
    enable_flag = getattr(settings, 'enable_dynamic_routing', False)

    logger.info(
        f"[Graph] Canary gating configured: "
        f"DYNAMIC_ROUTING_SAMPLE_RATE={sample_rate}%, "
        f"ENABLE_DYNAMIC_ROUTING={enable_flag}"
    )

    # Wire both paths using conditional_edges for per-workflow routing
    # The routing function should_use_dynamic_routing reads trace_id from state
    # and returns "router" or "decision" based on deterministic bucketing
    workflow.add_conditional_edges(
        "reviewer",
        should_use_dynamic_routing,
        {
            "router": "router",
            "decision": "decision"
        }
    )

    # Both router and decision lead to hitl_gate
    workflow.add_edge("router", "hitl_gate")
    # EPIC C Phase C-5: HITL Wiring (Issue #3155)
    # decision → hitl_gate (always route through HITL gate for approval check)
    # CTO Directive: "請將 HITL Gate Node 設計為一個獨立的節點，置於 router_node 下游。
    # 這樣我們可以保持 Router 的純粹性（只做決策），將控制權交給 Gate。"
    workflow.add_edge("decision", "hitl_gate")

    # hitl_gate → (fix | monitor_ci | publisher | executor)
    # EPIC B Phase B-3: Route finalize through publisher for review posting
    # EPIC C Phase C-5: HITL gate checks requires_hitl_approval before routing
    # EPIC D Issue #3487: Added executor route for SeniorCoder complexity abort approval
    workflow.add_conditional_edges(
        "hitl_gate",
        should_proceed_after_hitl_gate,
        {
            "fix": "fixer",
            "monitor_ci": "ci_monitor",
            "finalize": "publisher",
            "executor": "executor"
        }
    )

    # fixer → (executor | hitl_gate | ci_monitor | finalizer)
    # EPIC D Issue #3487: SeniorCoder HITL Gate
    # Changed from direct edge to conditional edge to support HITL escalation
    # when SeniorCoder determines task complexity is too high
    # Issue #3541: Added ci_monitor route for CI failure auto-fix to bypass
    # executor_node (which calls graph.execute with ValueGate)
    # Fix: Added finalizer route for loop protection to prevent infinite recursion
    workflow.add_conditional_edges(
        "fixer",
        should_proceed_after_fixer,
        {
            "executor": "executor",
            "hitl_gate": "hitl_gate",
            "ci_monitor": "ci_monitor",
            "finalizer": "finalizer"
        }
    )

    # EPIC B Phase B-3: publisher → finalizer
    workflow.add_edge("publisher", "finalizer")

    # finalizer → evaluation (Phase 2 PR-1813: Agent Evaluation)
    workflow.add_edge("finalizer", "evaluation")

    # evaluation → END (Phase 2 PR-1813)
    workflow.add_edge("evaluation", END)

    # Use provided checkpointer or fall back to get_checkpointer() for Redis/Memory
    # Fix (Dec 2025): For PostgreSQL, callers should use postgres_checkpointer_context()
    # and pass the checkpointer to this function for proper connection lifecycle management
    if checkpointer is None:
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
        # Issue #3640: Escalation Ladder Hard Cap State Tracking
        "escalation_count": 0,
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
        # Issue #3366: CI Failure Reflex Integration
        "ci_failure_trigger": None,
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
    ci_failure_trigger = False
    if context and context.get("resource_type") == "pull_request":
        # Handle pr_number: could be int or string from webhook
        raw_pr_number = context.get("pr_number") or context.get("resource_id")
        if raw_pr_number:
            try:
                pr_number = int(raw_pr_number)
            except (ValueError, TypeError):
                pr_number = 0
        pr_url = context.get("pr_url") or context.get("url") or ""
        # Issue: #3366 - CI Failure Reflex Integration
        # Detect CI failure trigger from webhook context
        ci_failure_trigger = context.get("ci_failure_trigger", False)

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
    agent_eval.start_workflow_metrics(trace_id, goal, task_type="default")

    # CRITICAL FIX (Dec 2025): Use get_postgres_checkpointer() for per-operation connection borrowing
    # This prevents "Pipeline [BAD]" and "connection is closed" errors during long workflows
    # by borrowing connections briefly per checkpoint operation instead of holding one for ~2 minutes
    #
    # ENHANCEMENT (Dec 2025): Wrap with DegradedPersistenceCheckpointer for runtime failover
    # When PostgreSQL fails at runtime (SSL disconnect, etc.), automatically switch to MemorySaver
    # This implements "soft landing" resilience - workflow continues with degraded persistence
    # instead of failing entirely. See: Blueprint Flow Controller v3 "Fail-Fast Recovery"
    pg_checkpointer = get_postgres_checkpointer()
    if pg_checkpointer is not None:
        # Wrap with DegradedPersistenceCheckpointer for runtime failover to MemorySaver
        # Feature flag: ENABLE_CHECKPOINT_FAILOVER (default: True)
        checkpointer = get_degraded_persistence_checkpointer(pg_checkpointer, trace_id=trace_id)
        checkpointer_mode = "degraded_persistence" if settings.enable_checkpoint_failover else "postgres_only"
        logger.info(
            f"Using PostgreSQL checkpointer with runtime failover enabled trace_id={trace_id} "
            f"failover_enabled={settings.enable_checkpoint_failover}",
            extra={
                "operation": "run_orchestrator",
                "trace_id": trace_id,
                "checkpointer": checkpointer_mode,
                "failover_enabled": settings.enable_checkpoint_failover,
            }
        )
    else:
        checkpointer = get_checkpointer()
        logger.info(
            f"Using fallback checkpointer (Redis/Memory) trace_id={trace_id}",
            extra={"operation": "run_orchestrator", "trace_id": trace_id, "checkpointer": "fallback"}
        )

    # Issue #3366: CI Failure Fast Path (Two-Layer Routing Optimization)
    # Layer 1: Entry Point Shortcut - use ci_monitor as entry point for CI failures
    # This skips planner + 5 advisors for faster disaster recovery
    entry_point = "planner"
    if ci_failure_trigger:
        entry_point = "ci_monitor"
        logger.info(
            f"[CI_FAILURE_FAST_PATH_ENTRY] Using ci_monitor entry point for CI failure "
            f"trace_id={trace_id} pr_number={pr_number}",
            extra={
                "operation": "run_orchestrator",
                "trace_id": trace_id,
                "pr_number": pr_number,
                "entry_point": "ci_monitor",
                "ci_failure_trigger": True,
            }
        )

    app = create_orchestrator_graph(entry_point=entry_point, checkpointer=checkpointer)

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

    # Issue: #3366 - CI Failure Reflex Integration
    # Pass CI failure trigger flag to workflow for auto-fix routing
    # Layer 2: Router Short-circuit uses this flag to bypass LLM routing
    # Fix: Also set ci_state="failure" so router_node's fast path condition
    # (ci_failure_trigger and ci_state != "success") evaluates correctly.
    # Without this, ci_state would be determined by ci_monitor_node which may
    # return "success" if other CI checks pass, breaking the fast path.
    if ci_failure_trigger:
        initial_state["ci_failure_trigger"] = True
        initial_state["ci_state"] = "failure"
        # Issue #3510: Pass CiFailureContext for structured CI error propagation
        if context and (ci_context := context.get("ci_failure_context")):
            initial_state["ci_failure_context"] = ci_context
            # Issue #3695: Extract branch from ci_failure_context for GeneralCoder
            # Without this, GeneralCoder gate fails with "Missing repo or branch"
            # because branch is not passed from normalizer to initial_state
            if head_branch := ci_context.get("head_branch"):
                initial_state["branch"] = head_branch
                logger.info(
                    f"[Orchestrator] Set branch from ci_failure_context for GeneralCoder. "
                    f"branch={head_branch}, trace_id={trace_id}",
                    extra={
                        "operation": "set_branch_from_ci_context",
                        "trace_id": trace_id,
                        "branch": head_branch,
                    }
                )
        # Issue #3676: Pass ci_error_file_paths for D-1b GeneralCoder multi-file support
        # These file paths are extracted from GitHub Annotations API in normalizer
        if context and (ci_error_file_paths := context.get("ci_error_file_paths")):
            initial_state["review_files"] = [{"path": fp} for fp in ci_error_file_paths]
            logger.info(
                f"[Orchestrator] Set review_files from ci_error_file_paths for GeneralCoder. "
                f"file_count={len(ci_error_file_paths)}, trace_id={trace_id}",
                extra={
                    "operation": "set_review_files_from_annotations",
                    "trace_id": trace_id,
                    "file_count": len(ci_error_file_paths),
                    "ci_error_file_paths": ci_error_file_paths,
                }
            )

    config = _get_workflow_config(trace_id)

    try:
        result = app.invoke(initial_state, config)

        final_result = result.get("final_result", {})

        # Note: extra fields are not output by worker.py's basicConfig formatter, so we put key fields in message
        # Use default values to avoid "status=None" in logs
        result_status = final_result.get("status") or "unknown"
        result_pr_url = final_result.get("pr_url") or ""
        # Track degraded persistence mode for monitoring ratio of degraded workflows
        persistence_degraded = getattr(checkpointer, "is_degraded", False)
        logger.info(
            f"LangGraph orchestrator completed trace_id={trace_id} status={result_status} "
            f"pr_url='{result_pr_url}' persistence_degraded={persistence_degraded}",
            extra={
                "operation": "run_orchestrator",
                "trace_id": trace_id,
                "status": result_status,
                "pr_url": result_pr_url,
                "persistence_degraded": persistence_degraded,
            }
        )

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="success", latency_ms=latency_ms)

        ci_state = final_result.get("ci_state", "unknown")
        agent_eval.record_workflow_result(
            trace_id,
            status="success",
            pr_created=bool(final_result.get("pr_url")),
            ci_passed=ci_state == "success",
            code_quality_score=result.get("code_quality_score", 100),
            pr_touched=bool(final_result.get("pr_url")),
            pr_opened=bool(final_result.get("pr_url")),
            code_changed=True,
            ci_state=ci_state
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
            ci_passed=False,
            pr_touched=False,
            pr_opened=False,
            code_changed=True,
            ci_state="error"
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
    agent_eval.start_workflow_metrics(trace_id, goal, task_type="review_follow_up")

    # CRITICAL FIX (Dec 2025): Use get_postgres_checkpointer() for per-operation connection borrowing
    # ENHANCEMENT (Dec 2025): Wrap with DegradedPersistenceCheckpointer for runtime failover
    pg_checkpointer = get_postgres_checkpointer()
    if pg_checkpointer is not None:
        checkpointer = get_degraded_persistence_checkpointer(pg_checkpointer, trace_id=trace_id)
        checkpointer_mode = "degraded_persistence" if settings.enable_checkpoint_failover else "postgres_only"
        logger.info(
            f"Using PostgreSQL checkpointer with runtime failover enabled trace_id={trace_id} "
            f"failover_enabled={settings.enable_checkpoint_failover}",
            extra={
                "operation": "run_review_follow_up_orchestrator",
                "trace_id": trace_id,
                "checkpointer": checkpointer_mode,
                "failover_enabled": settings.enable_checkpoint_failover,
            }
        )
    else:
        checkpointer = get_checkpointer()
        logger.info(
            f"Using fallback checkpointer (Redis/Memory) trace_id={trace_id}",
            extra={"operation": "run_review_follow_up_orchestrator", "trace_id": trace_id, "checkpointer": "fallback"}
        )

    # Create graph with review_intake as entry point
    app = create_orchestrator_graph(entry_point="review_intake", checkpointer=checkpointer)

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

    config = _get_workflow_config(trace_id)

    try:
        result = app.invoke(initial_state, config)

        final_result = result.get("final_result", {})

        # Track degraded persistence mode for monitoring ratio of degraded workflows
        persistence_degraded = getattr(checkpointer, "is_degraded", False)
        logger.info(
            f"Review Follow-up orchestrator completed trace_id={trace_id} "
            f"persistence_degraded={persistence_degraded}",
            extra={
                "operation": "run_review_follow_up_orchestrator",
                "trace_id": trace_id,
                "status": final_result.get("status"),
                "pr_url": final_result.get("pr_url"),
                "original_pr_number": original_pr_number,
                "persistence_degraded": persistence_degraded,
            }
        )

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="success", latency_ms=latency_ms)

        ci_state = final_result.get("ci_state", "unknown")
        agent_eval.record_workflow_result(
            trace_id,
            status="success",
            pr_created=bool(final_result.get("pr_url")),
            ci_passed=ci_state == "success",
            code_quality_score=result.get("code_quality_score", 100),
            pr_touched=bool(final_result.get("pr_url")),
            pr_opened=False,
            code_changed=True,
            ci_state=ci_state
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
            ci_passed=False,
            pr_touched=False,
            pr_opened=False,
            code_changed=True,
            ci_state="error"
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
    agent_eval.start_workflow_metrics(trace_id, goal, task_type="internal_review")

    # CRITICAL FIX (Dec 2025): Use get_postgres_checkpointer() for per-operation connection borrowing
    # ENHANCEMENT (Dec 2025): Wrap with DegradedPersistenceCheckpointer for runtime failover
    pg_checkpointer = get_postgres_checkpointer()
    if pg_checkpointer is not None:
        checkpointer = get_degraded_persistence_checkpointer(pg_checkpointer, trace_id=trace_id)
        checkpointer_mode = "degraded_persistence" if settings.enable_checkpoint_failover else "postgres_only"
        logger.info(
            f"Using PostgreSQL checkpointer with runtime failover enabled trace_id={trace_id} "
            f"failover_enabled={settings.enable_checkpoint_failover}",
            extra={
                "operation": "run_internal_review_orchestrator",
                "trace_id": trace_id,
                "checkpointer": checkpointer_mode,
                "failover_enabled": settings.enable_checkpoint_failover,
            }
        )
    else:
        checkpointer = get_checkpointer()
        logger.info(
            f"Using fallback checkpointer (Redis/Memory) trace_id={trace_id}",
            extra={"operation": "run_internal_review_orchestrator", "trace_id": trace_id, "checkpointer": "fallback"}
        )

    app = create_orchestrator_graph(entry_point="internal_review", checkpointer=checkpointer)

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

    config = _get_workflow_config(trace_id)

    try:
        result = app.invoke(initial_state, config)

        internal_review_result = result.get("internal_review_result", {})
        final_result = result.get("final_result", {})

        # Track degraded persistence mode for monitoring ratio of degraded workflows
        persistence_degraded = getattr(checkpointer, "is_degraded", False)
        logger.info(
            f"Internal Review orchestrator completed trace_id={trace_id} "
            f"persistence_degraded={persistence_degraded}",
            extra={
                "operation": "run_internal_review_orchestrator",
                "trace_id": trace_id,
                "internal_review_decision": result.get("internal_review_decision"),
                "ai_reviewer_agreement": result.get("ai_reviewer_agreement"),
                "requires_hitl": result.get("requires_hitl_approval"),
                "original_pr_number": original_pr_number,
                "persistence_degraded": persistence_degraded,
            }
        )

        latency_ms = (time.time() - start_time) * 1000
        metrics.record_workflow_complete(trace_id, status="success", latency_ms=latency_ms)

        agent_eval.record_workflow_result(
            trace_id,
            status="success",
            pr_created=bool(final_result.get("pr_url")),
            ci_passed=False,
            code_quality_score=result.get("code_quality_score", 100),
            pr_touched=bool(final_result.get("pr_url")),
            pr_opened=False,
            code_changed=False,
            ci_state="unknown"
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
            ci_passed=False,
            pr_touched=False,
            pr_opened=False,
            code_changed=False,
            ci_state="unknown"
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
