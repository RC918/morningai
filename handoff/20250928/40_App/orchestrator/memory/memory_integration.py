"""
Memory v2 Integration Layer

EPIC G: Memory v2 Orchestrator Integration

This module provides integration helpers for connecting Memory v2 to the
orchestrator components:

1. FlowController Integration - Short-Term Memory for flow state persistence
2. DebateEngine Integration - Agent Interaction Memory for debate context
3. Governance Integration - Governance Memory for safety patterns and routing decisions

All integrations are controlled by feature flags:
- ENABLE_MEMORY_V2: Master switch for all Memory v2 features
- ENABLE_MEMORY_V2_FLOW_STATE: Flow state persistence
- ENABLE_MEMORY_V2_DEBATE: Debate context persistence
- ENABLE_MEMORY_V2_GOVERNANCE: Governance memory persistence

Usage:
    from memory.memory_integration import (
        save_flow_state,
        restore_flow_state,
        save_debate_result,
        save_governance_event,
    )
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from common.config.settings import settings


def _calculate_expires_at(ttl_seconds: int) -> str:
    """
    Calculate expires_at timestamp based on TTL.

    Args:
        ttl_seconds: Time-to-live in seconds

    Returns:
        ISO format timestamp string for expiration
    """
    expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return expires.isoformat()


if TYPE_CHECKING:
    from .memory_v2 import MemoryV2

logger = logging.getLogger(__name__)


def _is_memory_v2_enabled() -> bool:
    """Check if Memory v2 is enabled via feature flag."""
    return settings.enable_memory_v2


def _is_flow_state_enabled() -> bool:
    """Check if flow state persistence is enabled."""
    return _is_memory_v2_enabled() and settings.enable_memory_v2_flow_state


def _is_debate_enabled() -> bool:
    """Check if debate context persistence is enabled."""
    return _is_memory_v2_enabled() and settings.enable_memory_v2_debate


def _is_governance_enabled() -> bool:
    """Check if governance memory is enabled."""
    return _is_memory_v2_enabled() and settings.enable_memory_v2_governance


def _is_review_feedback_enabled() -> bool:
    """Check if review feedback loop is enabled (B-13)."""
    return _is_memory_v2_enabled() and settings.enable_review_feedback_loop


def _is_review_pattern_retrieval_enabled() -> bool:
    """Check if review pattern retrieval is enabled (B-13)."""
    return _is_review_feedback_enabled() and settings.enable_review_pattern_retrieval


def _get_memory_v2() -> Optional["MemoryV2"]:
    """Get the Memory v2 singleton instance."""
    if not _is_memory_v2_enabled():
        return None

    try:
        from .memory_v2 import get_memory_v2
        return get_memory_v2()
    except Exception as e:
        logger.warning(f"[MemoryIntegration] Failed to get Memory v2 instance: {e}")
        return None


def save_flow_state(
    plan_id: str,
    trace_id: str,
    state_data: Dict[str, Any],
    current_stage: str = "",
    completed_tasks: Optional[List[str]] = None,
    failed_tasks: Optional[List[str]] = None,
) -> bool:
    """
    Save FlowController state to Short-Term Memory.

    This enables flow recovery if the orchestrator restarts mid-execution.

    Args:
        plan_id: Unique plan identifier
        trace_id: Workflow trace ID
        state_data: Full state dictionary to persist
        current_stage: Current execution stage name
        completed_tasks: List of completed task IDs
        failed_tasks: List of failed task IDs

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_flow_state_enabled():
        logger.debug("[MemoryIntegration] Flow state persistence disabled")
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        content = json.dumps({
            "plan_id": plan_id,
            "current_stage": current_stage,
            "completed_tasks": completed_tasks or [],
            "failed_tasks": failed_tasks or [],
            "state_data": state_data,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })

        entry = MemoryEntry(
            key=f"flow_state:{plan_id}",
            content=content,
            layer=MemoryLayer.SHORT_TERM,
            scope=MemoryScope.WORKFLOW,
            trace_id=trace_id,
            expires_at=_calculate_expires_at(settings.memory_v2_short_term_ttl),
            metadata={
                "plan_id": plan_id,
                "current_stage": current_stage,
                "completed_count": len(completed_tasks or []),
                "failed_count": len(failed_tasks or []),
            },
        )

        success = memory.save(entry, MemoryLayer.SHORT_TERM)
        if success:
            logger.info(
                "[MemoryIntegration] Saved flow state",
                extra={
                    "plan_id": plan_id,
                    "trace_id": trace_id,
                    "current_stage": current_stage,
                    "operation": "save_flow_state",
                }
            )
        return success

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save flow state: {e}",
            extra={
                "plan_id": plan_id,
                "trace_id": trace_id,
                "operation": "save_flow_state",
            }
        )
        return False


def restore_flow_state(
    plan_id: str,
    trace_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Restore FlowController state from Short-Term Memory.

    Args:
        plan_id: Unique plan identifier
        trace_id: Workflow trace ID

    Returns:
        State dictionary if found, None otherwise
    """
    if not _is_flow_state_enabled():
        logger.debug("[MemoryIntegration] Flow state persistence disabled")
        return None

    memory = _get_memory_v2()
    if memory is None:
        return None

    try:
        from .memory_v2 import MemoryLayer

        entry = memory.get(f"flow_state:{plan_id}", MemoryLayer.SHORT_TERM)
        if entry is None:
            logger.debug(
                "[MemoryIntegration] No flow state found",
                extra={
                    "plan_id": plan_id,
                    "trace_id": trace_id,
                    "operation": "restore_flow_state",
                }
            )
            return None

        state_data = json.loads(entry.content)
        logger.info(
            "[MemoryIntegration] Restored flow state",
            extra={
                "plan_id": plan_id,
                "trace_id": trace_id,
                "current_stage": state_data.get("current_stage"),
                "operation": "restore_flow_state",
            }
        )
        return state_data

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to restore flow state: {e}",
            extra={
                "plan_id": plan_id,
                "trace_id": trace_id,
                "operation": "restore_flow_state",
            }
        )
        return None


def clear_flow_state(plan_id: str) -> bool:
    """
    Clear FlowController state from Short-Term Memory.

    Called when a plan completes successfully to clean up.

    Args:
        plan_id: Unique plan identifier

    Returns:
        True if cleared successfully, False otherwise
    """
    if not _is_flow_state_enabled():
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryLayer

        success = memory.delete(f"flow_state:{plan_id}", MemoryLayer.SHORT_TERM)
        if success:
            logger.debug(
                "[MemoryIntegration] Cleared flow state",
                extra={"plan_id": plan_id, "operation": "clear_flow_state"}
            )
        return success

    except Exception as e:
        logger.warning(f"[MemoryIntegration] Failed to clear flow state: {e}")
        return False


def save_debate_result(
    debate_id: str,
    trace_id: str,
    topic: str,
    left_agent: str,
    right_agent: str,
    arguments: List[Dict[str, Any]],
    decision: Dict[str, Any],
    outcome: str,
    rounds_completed: int,
    debate_time_ms: float,
) -> bool:
    """
    Save debate result to Agent Interaction Memory.

    This preserves debate context for future reference and learning.

    Args:
        debate_id: Unique debate identifier
        trace_id: Workflow trace ID
        topic: Debate topic/question
        left_agent: Left agent identifier
        right_agent: Right agent identifier
        arguments: List of argument dictionaries
        decision: Judge decision dictionary
        outcome: Debate outcome (left_wins, right_wins, synthesis, inconclusive)
        rounds_completed: Number of debate rounds
        debate_time_ms: Total debate time in milliseconds

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_debate_enabled():
        logger.debug("[MemoryIntegration] Debate context persistence disabled")
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        # Use direct MemoryEntry construction to preserve full decision data
        # (Gemini Code Assist identified that decision dict was not being saved)
        content = f"Debate: {topic}\nOutcome: {outcome}"

        entry = MemoryEntry(
            key=f"debate:{debate_id}",
            content=content,
            layer=MemoryLayer.AGENT_INTERACTION,
            scope=MemoryScope.WORKFLOW,
            trace_id=trace_id,
            expires_at=_calculate_expires_at(settings.memory_v2_agent_interaction_ttl),
            metadata={
                "debate_id": debate_id,
                "topic": topic,
                "left_agent": left_agent,
                "right_agent": right_agent,
                "arguments": arguments,
                "decision": decision,  # Full decision dict now preserved
                "outcome": outcome,
                "rounds_completed": rounds_completed,
                "debate_time_ms": debate_time_ms,
            },
        )

        success = memory.save(entry, MemoryLayer.AGENT_INTERACTION)

        if success:
            logger.info(
                "[MemoryIntegration] Saved debate result",
                extra={
                    "debate_id": debate_id,
                    "trace_id": trace_id,
                    "outcome": outcome,
                    "rounds_completed": rounds_completed,
                    "operation": "save_debate_result",
                }
            )
        return success

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save debate result: {e}",
            extra={
                "debate_id": debate_id,
                "trace_id": trace_id,
                "operation": "save_debate_result",
            }
        )
        return False


def search_past_debates(
    query: str,
    trace_id: Optional[str] = None,
    limit: int = 5,
    agent_id: Optional[str] = None,
    agent_type: str = "unknown",
    permission_level: str = "sandbox_only",
) -> List[Dict[str, Any]]:
    """
    Search past debates for similar topics.

    EPIC G: Memory v2 Security (Blueprint Section 4.7)
    Issue: #3969 - Authorization checks for Memory v2 search functions

    Args:
        query: Search query (topic or keywords)
        trace_id: Optional trace ID to filter by workflow
        limit: Maximum number of results
        agent_id: Agent UUID performing the search (for authorization)
        agent_type: Type of agent (for authorization)
        permission_level: Agent's permission level (for authorization)

    Returns:
        List of debate result dictionaries (empty if unauthorized)
    """
    if not _is_debate_enabled():
        return []

    try:
        from governance.memory_authorizer import (
            authorize_memory_search,
            MemorySearchScope,
        )

        scope = MemorySearchScope.WORKFLOW if trace_id else MemorySearchScope.AGENT
        auth_result = authorize_memory_search(
            agent_id=agent_id,
            agent_type=agent_type,
            permission_level=permission_level,
            requested_scope=scope,
            trace_id=trace_id,
        )

        if not auth_result.authorized:
            logger.warning(
                "[MemoryIntegration] Search past debates denied: %s",
                auth_result.reason,
                extra={
                    "operation": "search_past_debates_denied",
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "trace_id": trace_id,
                }
            )
            return []

    except ImportError:
        logger.debug("[MemoryIntegration] MemoryAuthorizer not available, skipping auth")

    memory = _get_memory_v2()
    if memory is None:
        return []

    try:
        from .memory_v2 import MemoryLayer

        entries = memory.search(
            query=query,
            layer=MemoryLayer.AGENT_INTERACTION,
            limit=limit,
            trace_id=trace_id,
        )

        results = []
        for entry in entries:
            try:
                data = json.loads(entry.content) if isinstance(entry.content, str) else entry.content
                results.append(data)
            except (json.JSONDecodeError, TypeError):
                results.append({"content": entry.content, "key": entry.key})

        return results

    except Exception as e:
        logger.warning(f"[MemoryIntegration] Failed to search past debates: {e}")
        return []


def save_safety_pattern(
    pattern_id: str,
    trace_id: str,
    pattern_type: str,
    description: str,
    severity: str,
    action_taken: str,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Save a safety pattern to Governance Memory.

    Args:
        pattern_id: Unique pattern identifier
        trace_id: Workflow trace ID
        pattern_type: Type of safety pattern (e.g., "pii_detected", "security_risk")
        description: Human-readable description
        severity: Severity level (critical, high, medium, low)
        action_taken: Action taken in response
        context: Additional context data

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_governance_enabled():
        logger.debug("[MemoryIntegration] Governance memory disabled")
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        # Use direct MemoryEntry construction to preserve all metadata
        # (Gemini Code Assist identified parameter mismatch with GovernanceMemory)
        content = f"Safety Pattern: {pattern_type} - {description}"

        entry = MemoryEntry(
            key=f"safety_pattern:{pattern_id}",
            content=content,
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.GLOBAL,
            trace_id=trace_id,
            metadata={
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "description": description,
                "severity": severity,
                "action_taken": action_taken,
                "context": context or {},
            },
        )

        success = memory.save(entry, MemoryLayer.GOVERNANCE)

        if success:
            logger.info(
                "[MemoryIntegration] Saved safety pattern",
                extra={
                    "pattern_id": pattern_id,
                    "pattern_type": pattern_type,
                    "severity": severity,
                    "trace_id": trace_id,
                    "operation": "save_safety_pattern",
                }
            )
        return success

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save safety pattern: {e}",
            extra={
                "pattern_id": pattern_id,
                "trace_id": trace_id,
                "operation": "save_safety_pattern",
            }
        )
        return False


def save_drift_analysis(
    analysis_id: str,
    trace_id: str,
    provider: str,
    model: str,
    drift_detected: bool,
    drift_score: float,
    baseline_metrics: Dict[str, Any],
    current_metrics: Dict[str, Any],
    recommendation: str,
) -> bool:
    """
    Save drift analysis result to Governance Memory.

    Args:
        analysis_id: Unique analysis identifier
        trace_id: Workflow trace ID
        provider: LLM provider name
        model: Model name
        drift_detected: Whether drift was detected
        drift_score: Drift score (0.0 to 1.0)
        baseline_metrics: Baseline performance metrics
        current_metrics: Current performance metrics
        recommendation: Recommended action

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_governance_enabled():
        logger.debug("[MemoryIntegration] Governance memory disabled")
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        # Use direct MemoryEntry construction to preserve all metadata
        # (Gemini Code Assist identified parameter mismatch with GovernanceMemory)
        content = f"Drift Analysis: {provider}/{model} - Detected: {drift_detected}"

        entry = MemoryEntry(
            key=f"drift_analysis:{analysis_id}",
            content=content,
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.GLOBAL,
            trace_id=trace_id,
            metadata={
                "analysis_id": analysis_id,
                "provider": provider,
                "model": model,
                "drift_detected": drift_detected,
                "drift_score": drift_score,
                "baseline_metrics": baseline_metrics,
                "current_metrics": current_metrics,
                "recommendation": recommendation,
            },
        )

        success = memory.save(entry, MemoryLayer.GOVERNANCE)

        if success:
            logger.info(
                "[MemoryIntegration] Saved drift analysis",
                extra={
                    "analysis_id": analysis_id,
                    "provider": provider,
                    "model": model,
                    "drift_detected": drift_detected,
                    "drift_score": drift_score,
                    "trace_id": trace_id,
                    "operation": "save_drift_analysis",
                }
            )
        return success

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save drift analysis: {e}",
            extra={
                "analysis_id": analysis_id,
                "trace_id": trace_id,
                "operation": "save_drift_analysis",
            }
        )
        return False


def save_routing_decision(
    decision_id: str,
    trace_id: str,
    task_type: str,
    selected_provider: str,
    selected_model: str,
    selection_reason: str,
    candidates: List[Dict[str, Any]],
    latency_ms: float,
    success: bool,
) -> bool:
    """
    Save routing decision to Governance Memory.

    Args:
        decision_id: Unique decision identifier
        trace_id: Workflow trace ID
        task_type: Type of task being routed
        selected_provider: Selected provider name
        selected_model: Selected model name
        selection_reason: Reason for selection
        candidates: List of candidate providers/models considered
        latency_ms: Routing decision latency
        success: Whether the routed task succeeded

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_governance_enabled():
        logger.debug("[MemoryIntegration] Governance memory disabled")
        return False

    memory = _get_memory_v2()
    if memory is None:
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        # Use direct MemoryEntry construction to preserve all metadata
        # (GovernanceMemory.save_routing_decision has different parameter names)
        content = f"Routing: {task_type} -> {selected_provider}/{selected_model}"

        entry = MemoryEntry(
            key=f"routing:{decision_id}",
            content=content,
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.WORKFLOW,
            trace_id=trace_id,
            metadata={
                "decision_id": decision_id,
                "task_type": task_type,
                "selected_provider": selected_provider,
                "selected_model": selected_model,
                "selection_reason": selection_reason,
                "candidates": candidates,
                "latency_ms": latency_ms,
                "success": success,
            },
        )

        success_result = memory.save(entry, MemoryLayer.GOVERNANCE)

        if success_result:
            logger.info(
                "[MemoryIntegration] Saved routing decision",
                extra={
                    "decision_id": decision_id,
                    "task_type": task_type,
                    "selected_provider": selected_provider,
                    "selected_model": selected_model,
                    "success": success,
                    "trace_id": trace_id,
                    "operation": "save_routing_decision",
                }
            )
        return success_result

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save routing decision: {e}",
            extra={
                "decision_id": decision_id,
                "trace_id": trace_id,
                "operation": "save_routing_decision",
            }
        )
        return False


def search_knowledge_base(
    query: str,
    limit: int = 5,
    trace_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_type: str = "unknown",
    permission_level: str = "sandbox_only",
) -> List[Dict[str, Any]]:
    """
    Search the Knowledge Base for relevant past knowledge.

    EPIC G: Memory v2 Security (Blueprint Section 4.7)
    Issue: #3969 - Authorization checks for Memory v2 search functions

    This can be used by the Planner to retrieve learning context
    from past tasks.

    Args:
        query: Search query
        limit: Maximum number of results
        trace_id: Optional trace ID to filter by workflow
        agent_id: Agent UUID performing the search (for authorization)
        agent_type: Type of agent (for authorization)
        permission_level: Agent's permission level (for authorization)

    Returns:
        List of knowledge entries (empty if unauthorized)
    """
    if not _is_memory_v2_enabled():
        return []

    try:
        from governance.memory_authorizer import (
            authorize_memory_search,
            MemorySearchScope,
        )

        scope = MemorySearchScope.WORKFLOW if trace_id else MemorySearchScope.AGENT
        auth_result = authorize_memory_search(
            agent_id=agent_id,
            agent_type=agent_type,
            permission_level=permission_level,
            requested_scope=scope,
            trace_id=trace_id,
        )

        if not auth_result.authorized:
            logger.warning(
                "[MemoryIntegration] Search knowledge base denied: %s",
                auth_result.reason,
                extra={
                    "operation": "search_knowledge_base_denied",
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "trace_id": trace_id,
                }
            )
            return []

    except ImportError:
        logger.debug("[MemoryIntegration] MemoryAuthorizer not available, skipping auth")

    memory = _get_memory_v2()
    if memory is None:
        return []

    try:
        from .memory_v2 import MemoryLayer

        entries = memory.search(
            query=query,
            layer=MemoryLayer.KNOWLEDGE_BASE,
            limit=limit,
            trace_id=trace_id,
        )

        results = []
        for entry in entries:
            results.append({
                "key": entry.key,
                "content": entry.content,
                "similarity": entry.similarity,
                "metadata": entry.metadata,
                "created_at": entry.created_at,
            })

        return results

    except Exception as e:
        logger.warning(f"[MemoryIntegration] Failed to search knowledge base: {e}")
        return []


def get_memory_stats() -> Dict[str, Any]:
    """
    Get Memory v2 statistics.

    Returns:
        Dictionary with memory layer statistics
    """
    if not _is_memory_v2_enabled():
        return {"enabled": False}

    memory = _get_memory_v2()
    if memory is None:
        return {"enabled": True, "error": "Failed to get Memory v2 instance"}

    try:
        stats = memory.get_stats()
        stats["enabled"] = True
        stats["feature_flags"] = {
            "flow_state": _is_flow_state_enabled(),
            "debate": _is_debate_enabled(),
            "governance": _is_governance_enabled(),
            "review_feedback": _is_review_feedback_enabled(),
            "review_pattern_retrieval": _is_review_pattern_retrieval_enabled(),
        }
        return stats

    except Exception as e:
        return {"enabled": True, "error": str(e)}


def _sanitize_diff_for_storage(diff_snippet: Optional[str]) -> tuple[Optional[str], int]:
    """
    Sanitize diff snippet before storing in Knowledge Base.

    Issue #4007: Add sanitization for sensitive data in review feedback storage.
    Blueprint Section 4.7: Defense in Depth - prevent credential leakage.

    This reuses the secrets redaction patterns from llm_reviewer_adapter
    to ensure consistent sanitization across the codebase.

    Args:
        diff_snippet: Raw diff snippet to sanitize

    Returns:
        Tuple of (sanitized_diff, redaction_count)
    """
    if not diff_snippet:
        return diff_snippet, 0

    try:
        from llm_reviewer_adapter import sanitize_diff_content
        return sanitize_diff_content(diff_snippet)
    except ImportError:
        logger.warning(
            "[MemoryIntegration] Could not import sanitize_diff_content, "
            "storing diff without sanitization"
        )
        return diff_snippet, 0


def save_review_feedback(
    pr_number: int,
    repo: str,
    verdict: str,
    severity: str,
    summary: str,
    review_comments: List[Dict[str, Any]],
    file_paths: List[str],
    trace_id: Optional[str] = None,
    diff_snippet: Optional[str] = None,
    blocker_count: int = 0,
) -> bool:
    """
    Save review feedback to Knowledge Base for learning.

    EPIC B Phase B-13: Real-time Feedback Loop
    Blueprint: Reviewer feedback stored in Memory v2 for accumulated experience.

    This enables the system to learn from past reviews and provide
    better suggestions for similar code patterns in the future.

    Issue #4007: Diff snippets are now sanitized before storage to prevent
    credential leakage if secrets are present in the diff.

    Args:
        pr_number: Pull request number
        repo: Repository name (owner/repo format)
        verdict: Review verdict (approve, request_changes, comment, blocked, unknown)
        severity: Review severity (low, medium, high, critical)
        summary: One-line review summary
        review_comments: List of review comment dicts
        file_paths: List of files reviewed
        trace_id: Optional workflow trace ID
        diff_snippet: Optional code diff snippet for similarity search
        blocker_count: Number of blocking issues found

    Returns:
        True if saved successfully, False otherwise
    """
    if not _is_review_feedback_enabled():
        logger.info(
            "[MemoryIntegration] Review feedback loop disabled "
            "(ENABLE_MEMORY_V2=%s, ENABLE_REVIEW_FEEDBACK_LOOP=%s)",
            settings.enable_memory_v2,
            settings.enable_review_feedback_loop,
        )
        return False

    memory = _get_memory_v2()
    if memory is None:
        logger.warning(
            "[MemoryIntegration] Memory v2 instance not available - cannot save review feedback for PR #%d",
            pr_number,
        )
        return False

    try:
        from .memory_v2 import MemoryEntry, MemoryLayer, MemoryScope

        # Issue #4007: Sanitize diff snippet before storage to prevent credential leakage
        sanitized_diff, redaction_count = _sanitize_diff_for_storage(diff_snippet)
        if redaction_count > 0:
            logger.info(
                "[MemoryIntegration] Redacted %d potential secrets from diff_snippet",
                redaction_count,
                extra={
                    "pr_number": pr_number,
                    "repo": repo,
                    "redaction_count": redaction_count,
                    "trace_id": trace_id,
                    "operation": "sanitize_diff_for_storage",
                }
            )

        content = json.dumps({
            "pr_number": pr_number,
            "repo": repo,
            "verdict": verdict,
            "severity": severity,
            "summary": summary,
            "review_comments": review_comments,
            "file_paths": file_paths,
            "blocker_count": blocker_count,
            "diff_snippet": sanitized_diff,  # Sanitized for credential protection
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })

        entry = MemoryEntry(
            key=f"review_feedback:{repo}:{pr_number}",
            content=content,
            layer=MemoryLayer.KNOWLEDGE_BASE,
            scope=MemoryScope.GLOBAL,
            trace_id=trace_id,
            metadata={
                "type": "review_feedback",
                "pr_number": pr_number,
                "repo": repo,
                "verdict": verdict,
                "severity": severity,
                "blocker_count": blocker_count,
                "file_count": len(file_paths),
                "comment_count": len(review_comments),
            },
        )

        # PII sanitization bypass controlled by feature flag (REVIEW_FEEDBACK_SKIP_PII_SANITIZATION)
        # Default: True (skip sanitization)
        # Reason: Code review feedback contains code snippets, file paths, and technical
        # comments that frequently trigger PII false positives (e.g., "passport" in
        # passport validation code, "address" in address fields, numeric patterns
        # matching SSN/credit card regex). The content is LLM-generated, not user input.
        # Security: Operators can set REVIEW_FEEDBACK_SKIP_PII_SANITIZATION=false to enable
        # PII scanning if needed (may block legitimate review feedback due to false positives).
        # Issue: https://github.com/RC918/morningai/pull/4032 (discovered during B-13 testing)
        skip_pii = settings.review_feedback_skip_pii_sanitization
        # Log PII sanitization decision at INFO level for production visibility
        # MorningAI Code Review: DEBUG level may hide security-relevant behavior
        logger.info(
            "[MemoryIntegration] Review feedback PII sanitization: skip_pii=%s",
            skip_pii,
            extra={
                "pr_number": pr_number,
                "repo": repo,
                "verdict": verdict,
                "severity": severity,
                "content_length": len(content),
                "trace_id": trace_id,
                "skip_pii_sanitization": skip_pii,
                "operation": "save_review_feedback",
            }
        )
        success = memory.save(entry, MemoryLayer.KNOWLEDGE_BASE, skip_sanitization=skip_pii)
        if success:
            logger.info(
                "[MemoryIntegration] Saved review feedback",
                extra={
                    "pr_number": pr_number,
                    "repo": repo,
                    "verdict": verdict,
                    "severity": severity,
                    "trace_id": trace_id,
                    "operation": "save_review_feedback",
                }
            )
        return success

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to save review feedback: {e}",
            extra={
                "pr_number": pr_number,
                "repo": repo,
                "trace_id": trace_id,
                "operation": "save_review_feedback",
            }
        )
        return False


def list_review_feedback(
    limit: int = 100,
    trace_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all review feedback entries without vector similarity search.

    Issue #4305: Direct query method for debugging and verification.
    This bypasses vector similarity search and queries by metadata type directly.

    EPIC B Phase B-13: Real-time Feedback Loop
    Blueprint: Retrieve past review patterns for verification and debugging.

    Args:
        limit: Maximum number of entries to return (default 100)
        trace_id: Optional workflow trace ID for logging

    Returns:
        List of review feedback entries with their content and metadata
    """
    if not _is_review_pattern_retrieval_enabled():
        logger.debug("[MemoryIntegration] Review pattern retrieval disabled")
        return []

    memory = _get_memory_v2()
    if memory is None:
        return []

    try:
        kb_memory = memory.knowledge_base
        entries = kb_memory.list_by_metadata_type(
            metadata_type="review_feedback",
            limit=limit,
        )

        results = []
        for entry in entries:
            try:
                content = json.loads(entry.content)
                results.append({
                    "key": entry.key,
                    "created_at": entry.created_at,
                    "verdict": content.get("verdict"),
                    "severity": content.get("severity"),
                    "summary": content.get("summary"),
                    "review_comments": content.get("review_comments", []),
                    "file_paths": content.get("file_paths", []),
                    "pr_number": content.get("pr_number"),
                    "repo": content.get("repo"),
                    "blocker_count": content.get("blocker_count", 0),
                    "saved_at": content.get("saved_at"),
                })
            except (json.JSONDecodeError, TypeError):
                continue

        logger.info(
            "[MemoryIntegration] Listed %d review feedback entries",
            len(results),
            extra={
                "trace_id": trace_id,
                "operation": "list_review_feedback",
            }
        )

        return results

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to list review feedback: {e}",
            extra={
                "trace_id": trace_id,
                "operation": "list_review_feedback",
            }
        )
        return []


def _is_negative_pattern_retrieval_enabled() -> bool:
    """Check if negative pattern retrieval is enabled (B-18.3)."""
    return (
        _is_memory_v2_enabled()
        and settings.enable_review_comment_feedback
        and settings.enable_negative_pattern_retrieval
    )


def search_negative_patterns(
    query: str,
    file_paths: Optional[List[str]] = None,
    limit: Optional[int] = None,
    min_similarity: Optional[float] = None,
    trace_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for past rejected review suggestions (negative patterns).

    EPIC B-18 Phase B-18.3: Negative Pattern Retrieval
    Blueprint: Retrieve negative examples to avoid repeating false positives.

    This enables the Reviewer to learn from past rejections and avoid
    suggesting the same false positives again.

    Args:
        query: Search query (typically code snippet or diff content)
        file_paths: Optional list of file paths to filter by
        limit: Maximum number of patterns to return (default from settings)
        min_similarity: Minimum similarity threshold (default from settings)
        trace_id: Optional workflow trace ID

    Returns:
        List of past rejected suggestions with similarity scores
    """
    if not _is_negative_pattern_retrieval_enabled():
        logger.debug("[MemoryIntegration] Negative pattern retrieval disabled")
        return []

    memory = _get_memory_v2()
    if memory is None:
        return []

    if limit is None:
        limit = settings.negative_pattern_max_results
    if min_similarity is None:
        min_similarity = settings.negative_pattern_similarity_threshold

    try:
        from .memory_v2 import MemoryLayer

        # Search Knowledge Base for REVIEW_REJECTED entries
        entries = memory.search(
            query=query,
            layers=[MemoryLayer.KNOWLEDGE_BASE],
            limit=limit * 2,  # Fetch extra to filter
            trace_id=trace_id,
        )

        results = []
        for entry in entries:
            if entry.similarity is None or entry.similarity < min_similarity:
                continue

            # Only include REVIEW_REJECTED entries (negative examples)
            entry_type = entry.metadata.get("type", "")
            if entry_type != "REVIEW_REJECTED":
                continue

            # Optional file path filtering
            if file_paths:
                entry_path = entry.metadata.get("comment_path", "")
                if entry_path and entry_path not in file_paths:
                    # Check if any file path matches
                    if not any(fp in entry_path or entry_path in fp for fp in file_paths):
                        continue

            # Build result from metadata (content is natural language for embedding)
            results.append({
                "key": entry.key,
                "similarity": entry.similarity,
                "classification": entry.metadata.get("classification", "rejected"),
                "confidence": entry.metadata.get("confidence", 0.0),
                "importance": entry.metadata.get("importance", 0.0),
                "suggestion_text": entry.metadata.get("suggestion_text", ""),
                "comment_path": entry.metadata.get("comment_path"),
                "comment_line": entry.metadata.get("comment_line"),
                "ai_source": entry.metadata.get("ai_source"),
                "repo": entry.metadata.get("repo"),
                "pr_number": entry.metadata.get("pr_number"),
                "recorded_at": entry.metadata.get("recorded_at"),
                "content": entry.content,  # Natural language description
            })

            if len(results) >= limit:
                break

        logger.info(
            "[MemoryIntegration] Found %d negative patterns",
            len(results),
            extra={
                "query_length": len(query),
                "file_count": len(file_paths) if file_paths else 0,
                "trace_id": trace_id,
                "operation": "search_negative_patterns",
            }
        )

        return results

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to search negative patterns: {e}",
            extra={
                "trace_id": trace_id,
                "operation": "search_negative_patterns",
            }
        )
        return []


def search_review_patterns(
    query: str,
    file_paths: Optional[List[str]] = None,
    limit: Optional[int] = None,
    min_similarity: Optional[float] = None,
    trace_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for past review patterns similar to the current code.

    EPIC B Phase B-13: Real-time Feedback Loop
    Blueprint: Retrieve past review patterns to inform current reviews.

    This enables the Reviewer to learn from past reviews and provide
    more consistent and informed suggestions.

    Args:
        query: Search query (typically code snippet or file content)
        file_paths: Optional list of file paths to filter by
        limit: Maximum number of patterns to return (default from settings)
        min_similarity: Minimum similarity threshold (default from settings)
        trace_id: Optional workflow trace ID

    Returns:
        List of past review patterns with similarity scores
    """
    if not _is_review_pattern_retrieval_enabled():
        logger.debug("[MemoryIntegration] Review pattern retrieval disabled")
        return []

    memory = _get_memory_v2()
    if memory is None:
        return []

    if limit is None:
        limit = settings.review_feedback_max_patterns
    if min_similarity is None:
        min_similarity = settings.review_feedback_similarity_threshold

    try:
        from .memory_v2 import MemoryLayer

        # Issue #4131: MemoryV2.search() expects 'layers' (plural) parameter, not 'layer'
        entries = memory.search(
            query=query,
            layers=[MemoryLayer.KNOWLEDGE_BASE],
            limit=limit * 2,
            trace_id=trace_id,
        )

        results = []
        for entry in entries:
            if entry.similarity is None or entry.similarity < min_similarity:
                continue

            if entry.metadata.get("type") != "review_feedback":
                continue

            if file_paths:
                entry_files = set()
                try:
                    content = json.loads(entry.content)
                    entry_files = set(content.get("file_paths", []))
                except (json.JSONDecodeError, TypeError):
                    pass

                query_files = set(file_paths)
                if not entry_files.intersection(query_files):
                    continue

            try:
                content = json.loads(entry.content)
                results.append({
                    "key": entry.key,
                    "similarity": entry.similarity,
                    "verdict": content.get("verdict"),
                    "severity": content.get("severity"),
                    "summary": content.get("summary"),
                    "review_comments": content.get("review_comments", []),
                    "file_paths": content.get("file_paths", []),
                    "pr_number": content.get("pr_number"),
                    "repo": content.get("repo"),
                    "blocker_count": content.get("blocker_count", 0),
                    "saved_at": content.get("saved_at"),
                })
            except (json.JSONDecodeError, TypeError):
                continue

            if len(results) >= limit:
                break

        logger.info(
            "[MemoryIntegration] Found %d review patterns",
            len(results),
            extra={
                "query_length": len(query),
                "file_count": len(file_paths) if file_paths else 0,
                "trace_id": trace_id,
                "operation": "search_review_patterns",
            }
        )

        return results

    except Exception as e:
        logger.warning(
            f"[MemoryIntegration] Failed to search review patterns: {e}",
            extra={
                "trace_id": trace_id,
                "operation": "search_review_patterns",
            }
        )
        return []
