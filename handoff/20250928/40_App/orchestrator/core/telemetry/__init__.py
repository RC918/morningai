"""
SSOT Telemetry Schema v3 - Single Source of Truth for System Observability

Blueprint Section 9.1: Deterministic Guarantee
"All behavior can be reconstructed via Telemetry + Memory"

This module provides a unified telemetry schema that enables:
1. Causal tree reconstruction via span hierarchy (trace_id, span_id, parent_span_id)
2. Reproducibility via version tracking (schema, prompt, model config)
3. Privacy protection via redaction (hash inputs/outputs, drop PII)
4. Decision audit via evidence chain (retrieval refs, decision context)

Usage:
    from core.telemetry import TelemetryRecordV3, SpanContext, create_span_context

    # Create span context for a new trace
    ctx = create_span_context(trace_id="abc-123")

    # Create child span
    child_ctx = ctx.create_child()

    # Emit telemetry record
    record = TelemetryRecordV3.create(
        name="llm.call",
        span_context=child_ctx,
        component="ReviewerAgent",
        status_code="OK",
        metrics={"latency_ms": 1500, "tokens_in": 500},
        attributes={"model": "qwen-max", "provider": "alicloud"},
    )
"""

from .schema import (
    TelemetryRecordV3,
    SpanContext,
    SpanKind,
    StatusCode,
    RedactionStrategy,
    EvidenceRef,
    EvidenceKind,
    VersionInfo,
    RedactionInfo,
    create_span_context,
    generate_span_id,
)

from .adapters import (
    from_agent_telemetry_event,
    from_resource_telemetry_event,
    from_policy_telemetry_event,
)

__all__ = [
    # Core schema
    "TelemetryRecordV3",
    "SpanContext",
    "SpanKind",
    "StatusCode",
    "RedactionStrategy",
    "EvidenceRef",
    "EvidenceKind",
    "VersionInfo",
    "RedactionInfo",
    # Factory functions
    "create_span_context",
    "generate_span_id",
    # Adapters for backward compatibility
    "from_agent_telemetry_event",
    "from_resource_telemetry_event",
    "from_policy_telemetry_event",
]
