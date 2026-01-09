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
"""

from typing import Any, Dict, Optional

from .schema import (
    TelemetryRecordV3,
    SpanKind,
    StatusCode,
    VersionInfo,
    create_span_context,
)


def from_agent_telemetry_event(
    event: Any,
    trace_id: str,
    parent_span_id: Optional[str] = None,
    epic_tag: str = "EPIC-D",
) -> TelemetryRecordV3:
    """
    Convert a BaseAgent TelemetryEvent to TelemetryRecordV3.

    Args:
        event: TelemetryEvent from core.agents.base
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

    event_type = getattr(event, "event_type", None)
    if event_type:
        event_type_value = event_type.value if hasattr(event_type, "value") else str(event_type)
    else:
        event_type_value = "unknown"

    name = f"agent.{event_type_value}"

    success = getattr(event, "success", None)
    error = getattr(event, "error", None)

    if success is True:
        status_code = StatusCode.OK
    elif success is False or error:
        status_code = StatusCode.ERROR
    else:
        status_code = StatusCode.UNSET

    metrics: Dict[str, float] = {}
    latency_ms = getattr(event, "latency_ms", None)
    if latency_ms is not None:
        metrics["latency_ms"] = float(latency_ms)

    tokens_in = getattr(event, "tokens_in", None)
    if tokens_in is not None:
        metrics["tokens_in"] = float(tokens_in)

    tokens_out = getattr(event, "tokens_out", None)
    if tokens_out is not None:
        metrics["tokens_out"] = float(tokens_out)

    attributes: Dict[str, Any] = {}
    task_type = getattr(event, "task_type", None)
    if task_type:
        attributes["task_type"] = task_type

    model_selected = getattr(event, "model_selected", None)
    if model_selected:
        attributes["model_selected"] = model_selected

    provider = getattr(event, "provider", None)
    if provider:
        attributes["provider"] = provider

    metadata = getattr(event, "metadata", None)
    if metadata:
        attributes["metadata"] = metadata

    versions = None
    if model_selected or provider:
        versions = VersionInfo(
            model_config={
                "provider": provider,
                "model": model_selected,
            }
        )

    return TelemetryRecordV3.create(
        name=name,
        span_context=span_context,
        component="BaseAgent",
        kind=SpanKind.INTERNAL,
        status_code=status_code,
        status_message=error,
        agent_id=getattr(event, "agent_id", None),
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

    Args:
        event_dict: Event dictionary from RuntimePolicyEnforcer
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
    name = f"governance.{event_type}"

    action = event_dict.get("action", "unknown")
    if action == "allow":
        status_code = StatusCode.OK
    elif action == "block":
        status_code = StatusCode.ERROR
    elif action == "require_approval":
        status_code = StatusCode.SKIPPED
    else:
        status_code = StatusCode.UNSET

    metrics: Dict[str, float] = {}
    for key in ["current_tokens", "max_tokens", "current_usd", "max_usd"]:
        if key in event_dict and event_dict[key] is not None:
            metrics[key] = float(event_dict[key])

    # Issue #3712: Filter trace_id/parent_span_id from attributes since they are
    # already handled by span_context. This prevents data duplication.
    attributes = {k: v for k, v in event_dict.items() if k not in [
        "event_type", "timestamp", "component", "action",
        "current_tokens", "max_tokens", "current_usd", "max_usd",
        "trace_id", "parent_span_id",  # Already in span_context
    ]}

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
