"""
Observer Node - Phase 2 Brain Layer (#1811)

Implements the "post-mortem" flow for failed workflows:
1. Captures failure context (Trace ID, Error Log, Last attempt)
2. Generates a summary of the failure
3. Stores the error-fix pair to pgvector for future learning

This node is triggered when:
- Workflow completes with status=error
- Fixer exhausts all retries (MAX_FIXER_RETRIES reached)

The stored data enables the Planner to query past failures and
learn from previous mistakes.
"""

import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def _generate_failure_summary(state: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the failure.

    Args:
        state: AgentState dictionary from orchestrator

    Returns:
        Summary text suitable for embedding and recall
    """
    parts = []

    goal = state.get("goal", "")
    if goal:
        parts.append(f"Goal: {goal[:200]}")

    task_type = state.get("task_type", "unknown")
    parts.append(f"Task Type: {task_type}")

    error = state.get("error", "")
    if error:
        parts.append(f"Error: {error[:500]}")

    ci_state = state.get("ci_state", "")
    if ci_state:
        parts.append(f"CI State: {ci_state}")

    retry_count = state.get("retry_count", 0)
    parts.append(f"Fixer Retries: {retry_count}")

    merge_decision = state.get("merge_decision", "")
    if merge_decision:
        parts.append(f"Merge Decision: {merge_decision}")

    security_risk = state.get("security_risk", "")
    if security_risk and security_risk != "info":
        parts.append(f"Security Risk: {security_risk}")

    governance_risk = state.get("governance_risk", "")
    if governance_risk and governance_risk != "info":
        parts.append(f"Governance Risk: {governance_risk}")

    review_severity = state.get("review_severity", "")
    if review_severity:
        parts.append(f"Review Severity: {review_severity}")

    code_quality_score = state.get("code_quality_score")
    if code_quality_score is not None:
        parts.append(f"Code Quality Score: {code_quality_score}")

    return "\n".join(parts)


def _extract_error_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured error context from state.

    Args:
        state: AgentState dictionary

    Returns:
        Dictionary with error context for storage
    """
    return {
        "trace_id": state.get("trace_id"),
        "task_type": state.get("task_type"),
        "ci_state": state.get("ci_state"),
        "ci_checks": state.get("ci_checks"),
        "retry_count": state.get("retry_count", 0),
        "merge_decision": state.get("merge_decision"),
        "security_risk": state.get("security_risk"),
        "governance_risk": state.get("governance_risk"),
        "review_severity": state.get("review_severity"),
        "code_quality_score": state.get("code_quality_score"),
        "planner_type": state.get("planner_type"),
        "pr_url": state.get("pr_url"),
        "repo": state.get("repo"),
    }


def _categorize_error(state: Dict[str, Any]) -> str:
    """
    Categorize the error type based on state.

    Args:
        state: AgentState dictionary

    Returns:
        Error type category string
    """
    error = state.get("error", "").lower()
    ci_state = state.get("ci_state", "")
    merge_decision = state.get("merge_decision", "")
    retry_count = state.get("retry_count", 0)

    if "timeout" in error:
        return "timeout"
    elif "rate limit" in error or "rate_limit" in error:
        return "rate_limit"
    elif "authentication" in error or "auth" in error:
        return "authentication"
    elif "permission" in error or "forbidden" in error:
        return "permission"
    elif ci_state == "failure":
        return "ci_failure"
    elif merge_decision == "request_changes":
        return "review_rejection"
    elif retry_count >= 3:
        return "max_retries_exceeded"
    elif "syntax" in error or "parse" in error:
        return "syntax_error"
    elif "import" in error or "module" in error:
        return "import_error"
    else:
        return "unknown"


def observe_failure(
    state: Dict[str, Any],
    save_to_pgvector: bool = True
) -> Dict[str, Any]:
    """
    Observe and record a workflow failure.

    This is the main entry point for the Observer Node. It:
    1. Generates a failure summary
    2. Categorizes the error
    3. Stores the error-fix pair to pgvector (if enabled)

    Args:
        state: AgentState dictionary from orchestrator
        save_to_pgvector: Whether to save to pgvector (default True)

    Returns:
        Dictionary with observation results
    """
    start_time = time.time()
    trace_id = state.get("trace_id", "unknown")

    logger.info("[Observer] Starting failure observation", extra={
        "operation": "observe_failure",
        "trace_id": trace_id
    })

    summary = _generate_failure_summary(state)
    error_type = _categorize_error(state)
    error_context = _extract_error_context(state)

    result = {
        "trace_id": trace_id,
        "error_type": error_type,
        "summary": summary,
        "error_context": error_context,
        "saved_to_pgvector": False,
        "pair_id": None,
    }

    if save_to_pgvector:
        try:
            from memory.error_fix_pairs import save_error_fix_pair

            error_text = state.get("error", "") or summary
            fix_text = f"[PENDING] Failure recorded for trace_id: {trace_id}"

            pair_id = save_error_fix_pair(
                error_text=error_text,
                fix_text=fix_text,
                error_type=error_type,
                fix_type="pending",
                error_context=error_context,
                fix_metadata={"status": "pending_fix", "recorded_at": time.time()},
                trace_id=trace_id,
                task_type=state.get("task_type"),
            )

            if pair_id:
                result["saved_to_pgvector"] = True
                result["pair_id"] = pair_id
                logger.info("[Observer] Saved failure to pgvector", extra={
                    "operation": "observe_failure",
                    "trace_id": trace_id,
                    "pair_id": pair_id,
                    "error_type": error_type
                })
            else:
                logger.warning("[Observer] Failed to save to pgvector", extra={
                    "operation": "observe_failure",
                    "trace_id": trace_id
                })

        except ImportError as e:
            logger.warning(f"[Observer] error_fix_pairs module not available: {e}")
        except Exception as e:
            logger.warning(f"[Observer] Failed to save failure: {e}", extra={
                "operation": "observe_failure",
                "trace_id": trace_id,
                "error": str(e)
            })

    latency_ms = (time.time() - start_time) * 1000
    result["latency_ms"] = latency_ms

    logger.info("[Observer] Failure observation complete", extra={
        "operation": "observe_failure",
        "trace_id": trace_id,
        "error_type": error_type,
        "saved_to_pgvector": result["saved_to_pgvector"],
        "latency_ms": latency_ms
    })

    return result


def query_past_failures(
    error_text: str,
    limit: int = 3,
    threshold: float = 0.7,
    error_type_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query past failures similar to the given error.

    This function is used by the Planner to retrieve past experience
    before planning a new task.

    Args:
        error_text: Error text to search for similar failures
        limit: Maximum number of results
        threshold: Minimum similarity score (0.0 to 1.0)
        error_type_filter: Optional filter by error type

    Returns:
        List of similar past failures with their fixes
    """
    try:
        from memory.error_fix_pairs import find_similar_errors

        similar_pairs = find_similar_errors(
            error_text=error_text,
            limit=limit,
            threshold=threshold,
            error_type_filter=error_type_filter
        )

        results = []
        for pair in similar_pairs:
            results.append({
                "id": pair.id,
                "error_text": pair.error_text,
                "fix_text": pair.fix_text,
                "error_type": pair.error_type,
                "similarity": pair.similarity,
                "confidence_score": pair.confidence_score,
                "success_count": pair.success_count,
                "failure_count": pair.failure_count,
            })

        logger.debug(f"[Observer] Found {len(results)} similar past failures")
        return results

    except ImportError as e:
        logger.debug(f"[Observer] error_fix_pairs module not available: {e}")
        return []
    except Exception as e:
        logger.warning(f"[Observer] Failed to query past failures: {e}")
        return []


def get_learning_context(
    goal: str,
    task_type: Optional[str] = None,
    limit: int = 3
) -> str:
    """
    Get learning context from past failures for the Planner.

    This function queries past failures and formats them as context
    that can be included in the Planner's prompt.

    Args:
        goal: The current task goal
        task_type: Optional task type for filtering
        limit: Maximum number of past failures to include

    Returns:
        Formatted context string for the Planner
    """
    try:
        past_failures = query_past_failures(
            error_text=goal,
            limit=limit,
            threshold=0.6
        )

        if not past_failures:
            return ""

        context_parts = ["## Past Experience (Similar Failures):\n"]

        for i, failure in enumerate(past_failures, 1):
            context_parts.append(f"### Case {i} (Similarity: {failure.get('similarity', 0):.2f})")
            context_parts.append(f"Error Type: {failure.get('error_type', 'unknown')}")
            context_parts.append(f"Error: {failure.get('error_text', '')[:200]}")

            fix_text = failure.get("fix_text", "")
            if fix_text and not fix_text.startswith("[PENDING]"):
                context_parts.append(f"Fix: {fix_text[:200]}")
                context_parts.append(f"Confidence: {failure.get('confidence_score', 0):.2f}")

            context_parts.append("")

        return "\n".join(context_parts)

    except Exception as e:
        logger.warning(f"[Observer] Failed to get learning context: {e}")
        return ""


def update_fix_for_failure(
    trace_id: str,
    fix_text: str,
    was_successful: bool = True
) -> bool:
    """
    Update the fix for a previously recorded failure.

    Call this when a fix is found for a previously recorded failure
    to update the error-fix pair with the actual solution.

    Args:
        trace_id: Trace ID of the original failure
        fix_text: The fix that resolved the error
        was_successful: Whether the fix was successful

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        from memory.error_fix_pairs import (
            update_pair_feedback,
            _get_supabase_client,
            ERROR_FIX_PAIRS_TABLE,
            _embed
        )

        client = _get_supabase_client()
        if client is None:
            logger.debug("[Observer] Supabase client not available")
            return False

        result = client.table(ERROR_FIX_PAIRS_TABLE).select("id").eq(
            "trace_id", trace_id
        ).limit(1).execute()

        if not result.data:
            logger.warning(f"[Observer] No error-fix pair found for trace_id: {trace_id}")
            return False

        pair_id = result.data[0]["id"]

        fix_embedding = _embed(fix_text)

        update_data = {
            "fix_text": fix_text,
            "fix_embedding": fix_embedding,
            "fix_type": "resolved" if was_successful else "attempted",
            "fix_metadata": {
                "status": "resolved" if was_successful else "attempted",
                "updated_at": time.time()
            }
        }

        client.table(ERROR_FIX_PAIRS_TABLE).update(update_data).eq(
            "id", pair_id
        ).execute()

        if was_successful:
            update_pair_feedback(pair_id, was_successful=True)

        logger.info("[Observer] Updated fix for failure", extra={
            "operation": "update_fix_for_failure",
            "trace_id": trace_id,
            "pair_id": pair_id,
            "was_successful": was_successful
        })

        return True

    except ImportError as e:
        logger.warning(f"[Observer] error_fix_pairs module not available: {e}")
        return False
    except Exception as e:
        logger.warning(f"[Observer] Failed to update fix: {e}", extra={
            "operation": "update_fix_for_failure",
            "trace_id": trace_id,
            "error": str(e)
        })
        return False
