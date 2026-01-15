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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from common.config.settings import settings

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

        scope = MemorySearchScope.WORKFLOW if trace_id else MemorySearchScope.GLOBAL
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

        scope = MemorySearchScope.WORKFLOW if trace_id else MemorySearchScope.GLOBAL
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
        }
        return stats

    except Exception as e:
        return {"enabled": True, "error": str(e)}
