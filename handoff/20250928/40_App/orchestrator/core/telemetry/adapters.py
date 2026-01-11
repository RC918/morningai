"""
SSOT Telemetry Adapters - Backward Compatibility Layer

This module provides adapters to convert existing telemetry events
to the new TelemetryRecordV3 format, enabling gradual migration.

Supported adapters:
1. from_agent_telemetry_event: Convert BaseAgent TelemetryEvent
2. from_resource_telemetry_event: Convert resource_telemetry events
3. from_policy_telemetry_event: Convert RuntimePolicyEnforcer events

Usage:
    from core.telemetry import from_agent_telemetry_event
    from core.agents.base import TelemetryEvent

    # Convert existing event to SSOT format
    old_event = TelemetryEvent(...)
    ssot_record = from_agent_telemetry_event(old_event, trace_id="abc-123")

Type Safety (Issue #3575):
    This module uses Protocol classes to define expected interfaces for
    telemetry events, improving type safety while maintaining backward
    compatibility with varying event shapes.
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .schema import (
    TelemetryRecordV3,
    SpanKind,
    StatusCode,
    VersionInfo,
    create_span_context,
)


@runtime_checkable
class AgentTelemetryEventProtocol(Protocol):
    """
    Protocol defining the expected interface for agent telemetry events.

    Issue #3575: This Protocol improves type safety by explicitly declaring
    expected fields, enabling static analysis tools to catch typos and
    type mismatches while maintaining backward compatibility.

    Required fields:
        event_type: Event type (enum or string)
        agent_id: Agent identifier

    Optional fields (may not exist on all event variants):
        success: Whether the operation succeeded
        error: Error message if failed
        latency_ms: Operation latency in milliseconds
        tokens_in: Input token count
        tokens_out: Output token count
        task_type: Type of task being performed
        model_selected: Selected model name
        provider: Model provider name
        metadata: Additional metadata dictionary
    """
    event_type: Any
    agent_id: str


class PolicyTelemetryEventDict:
    """
    TypedDict-like documentation for policy telemetry event dictionaries.

    Issue #3575: While we use Dict[str, Any] for flexibility, this class
    documents the expected structure for policy events.

    Expected keys:
        event_type (str): Event type (e.g., "budget_check", "hitl_gate")
        action (str): Action taken ("allow", "block", "require_approval")
        timestamp (str, optional): ISO timestamp
        component (str, optional): Component name
        error (str, optional): Error message
        current_tokens (float, optional): Current token usage
        max_tokens (float, optional): Maximum allowed tokens
        current_usd (float, optional): Current USD cost
        max_usd (float, optional): Maximum allowed USD cost
    """
    pass


POLICY_EVENT_KNOWN_KEYS = frozenset([
    "event_type", "timestamp", "component", "action",
    "current_tokens", "max_tokens", "current_usd", "max_usd",
    "trace_id", "parent_span_id",  # Issue #3712: Already in span_context
])

POLICY_EVENT_METRIC_KEYS = frozenset([
    "current_tokens", "max_tokens", "current_usd", "max_usd",
])


def _sanitize_event_type(event_type: str) -> str:
    """
    Sanitize event_type to prevent log injection.

    Issue #3718: Defense-in-depth sanitization to prevent log forging,
    misleading monitoring systems, or corrupting log data through
    newline characters or other control characters in event_type values.

    Args:
        event_type: Event type string to sanitize

    Returns:
        Sanitized string safe for use in span names
    """
    if not event_type:
        return "unknown"
    # Remove control characters (ASCII 0-31) including newlines and carriage returns
    sanitized = ''.join(c if ord(c) >= 32 else '_' for c in event_type)
    # Limit length to prevent log flooding
    return sanitized[:100]


def _get_optional_attr(obj: Any, name: str, default: Any = None) -> Any:
    """
    Safely get an optional attribute from an object.

    Issue #3575: This helper centralizes optional attribute access,
    making it explicit that certain fields may not exist on all event variants.
    Using a dedicated function instead of scattered getattr calls improves
    maintainability and makes the optional nature of fields explicit.

    Args:
        obj: Object to get attribute from
        name: Attribute name
        default: Default value if attribute doesn't exist

    Returns:
        Attribute value or default
    """
    return getattr(obj, name, default)


def from_agent_telemetry_event(
    event: AgentTelemetryEventProtocol,
    trace_id: str,
    parent_span_id: Optional[str] = None,
    epic_tag: str = "EPIC-D",
) -> TelemetryRecordV3:
    """
    Convert a BaseAgent TelemetryEvent to TelemetryRecordV3.

    Issue #3575: The event parameter now uses AgentTelemetryEventProtocol
    to improve type safety. Required fields (event_type, agent_id) are
    accessed directly, while optional fields use _get_optional_attr.

    Args:
        event: TelemetryEvent conforming to AgentTelemetryEventProtocol
        trace_id: Trace ID for correlation
        parent_span_id: Optional parent span ID
        epic_tag: EPIC tag (default: EPIC-D for agent events)

    Returns:
        TelemetryRecordV3 instance
    """
    span_context = create_span_context(
        trace_id=trace_id,
        parent_span_id=parent_span_id,
    )

    # Required field: event_type (accessed directly per Protocol)
    event_type = event.event_type
    if event_type:
        event_type_value = event_type.value if hasattr(event_type, "value") else str(event_type)
    else:
        event_type_value = "unknown"

    # Issue #3718: Sanitize event_type to prevent log injection
    name = f"agent.{_sanitize_event_type(event_type_value)}"

    # Optional fields: use _get_optional_attr for fields that may not exist
    success = _get_optional_attr(event, "success")
    error = _get_optional_attr(event, "error")

    if success is True:
        status_code = StatusCode.OK
    elif success is False or error:
        status_code = StatusCode.ERROR
    else:
        status_code = StatusCode.UNSET

    # Build metrics from optional numeric fields
    metrics: Dict[str, float] = {}
    latency_ms = _get_optional_attr(event, "latency_ms")
    if latency_ms is not None:
        metrics["latency_ms"] = float(latency_ms)

    tokens_in = _get_optional_attr(event, "tokens_in")
    if tokens_in is not None:
        metrics["tokens_in"] = float(tokens_in)

    tokens_out = _get_optional_attr(event, "tokens_out")
    if tokens_out is not None:
        metrics["tokens_out"] = float(tokens_out)

    # Build attributes from optional string fields
    attributes: Dict[str, Any] = {}
    task_type = _get_optional_attr(event, "task_type")
    if task_type:
        attributes["task_type"] = task_type

    model_selected = _get_optional_attr(event, "model_selected")
    if model_selected:
        attributes["model_selected"] = model_selected

    provider = _get_optional_attr(event, "provider")
    if provider:
        attributes["provider"] = provider

    metadata = _get_optional_attr(event, "metadata")
    if metadata:
        attributes["metadata"] = metadata

    # Build version info if model/provider available
    versions = None
    if model_selected or provider:
        versions = VersionInfo(
            model_config={
                "provider": provider,
                "model": model_selected,
            }
        )

    # Required field: agent_id (accessed directly per Protocol)
    return TelemetryRecordV3.create(
        name=name,
        span_context=span_context,
        component="BaseAgent",
        kind=SpanKind.INTERNAL,
        status_code=status_code,
        status_message=error,
        agent_id=event.agent_id,
        epic_tag=epic_tag,
        versions=versions,
        metrics=metrics,
        attributes=attributes,
    )


def from_resource_telemetry_event(
    event_code: str,
    trace_id: str,
    node_name: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    metrics: Optional[Dict[str, float]] = None,
    attributes: Optional[Dict[str, Any]] = None,
    epic_tag: str = "EPIC-C",
) -> TelemetryRecordV3:
    """
    Convert a resource_telemetry event to TelemetryRecordV3.

    Args:
        event_code: Event code (e.g., "RESOURCE_PEAK", "DIFF_FETCH_BYTES")
        trace_id: Trace ID for correlation
        node_name: Optional LangGraph node name
        parent_span_id: Optional parent span ID
        metrics: Optional metrics dictionary
        attributes: Optional attributes dictionary
        epic_tag: EPIC tag (default: EPIC-C for flow events)

    Returns:
        TelemetryRecordV3 instance
    """
    span_context = create_span_context(
        trace_id=trace_id,
        parent_span_id=parent_span_id,
    )

    event_code_to_name = {
        "RESOURCE_PEAK": "resource.peak",
        "DIFF_FETCH_BYTES": "github.diff_fetch",
        "PROMPT_BUILD_BYTES": "llm.prompt_build",
        "LLM_RESPONSE_BYTES": "llm.response",
        "CHECKPOINT_PUT_BYTES": "checkpoint.put",
    }

    name = event_code_to_name.get(event_code, f"resource.{event_code.lower()}")

    final_attributes = attributes or {}
    final_attributes["event_code"] = event_code

    return TelemetryRecordV3.create(
        name=name,
        span_context=span_context,
        component="ResourceTelemetry",
        kind=SpanKind.INTERNAL,
        status_code=StatusCode.OK,
        node_name=node_name,
        epic_tag=epic_tag,
        metrics=metrics or {},
        attributes=final_attributes,
    )


def from_policy_telemetry_event(
    event_dict: Dict[str, Any],
    trace_id: str,
    parent_span_id: Optional[str] = None,
    epic_tag: str = "EPIC-I",
) -> TelemetryRecordV3:
    """
    Convert a RuntimePolicyEnforcer telemetry event to TelemetryRecordV3.

    Issue #3575: Uses POLICY_EVENT_KNOWN_KEYS and POLICY_EVENT_METRIC_KEYS
    constants to improve maintainability. See PolicyTelemetryEventDict for
    documentation of expected event_dict structure.

    Args:
        event_dict: Event dictionary from RuntimePolicyEnforcer
                   (see PolicyTelemetryEventDict for expected structure)
        trace_id: Trace ID for correlation
        parent_span_id: Optional parent span ID
        epic_tag: EPIC tag (default: EPIC-I for governance events)

    Returns:
        TelemetryRecordV3 instance
    """
    span_context = create_span_context(
        trace_id=trace_id,
        parent_span_id=parent_span_id,
    )

    event_type = event_dict.get("event_type", "policy_check")
    # Issue #3718: Sanitize event_type to prevent log injection
    name = f"governance.{_sanitize_event_type(event_type)}"

    # Map action to status code
    action = event_dict.get("action", "unknown")
    action_to_status = {
        "allow": StatusCode.OK,
        "block": StatusCode.ERROR,
        "require_approval": StatusCode.SKIPPED,
    }
    status_code = action_to_status.get(action, StatusCode.UNSET)

    # Extract metrics using defined constant keys
    metrics: Dict[str, float] = {}
    for key in POLICY_EVENT_METRIC_KEYS:
        if key in event_dict and event_dict[key] is not None:
            metrics[key] = float(event_dict[key])

    # Filter out known keys from attributes using defined constant
    # Issue #3712: trace_id/parent_span_id already in span_context
    attributes = {k: v for k, v in event_dict.items() if k not in POLICY_EVENT_KNOWN_KEYS}

    return TelemetryRecordV3.create(
        name=name,
        span_context=span_context,
        component="RuntimePolicyEnforcer",
        kind=SpanKind.INTERNAL,
        status_code=status_code,
        status_message=event_dict.get("error"),
        epic_tag=epic_tag,
        metrics=metrics,
        attributes=attributes,
    )
