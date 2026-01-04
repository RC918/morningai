"""
SSOT Telemetry Schema v3 - Core Schema Definitions

Blueprint Section 9.1: Deterministic Guarantee
"All behavior can be reconstructed via Telemetry + Memory"

This module defines the core schema for SSOT telemetry events that enable:
1. Causal tree reconstruction via span hierarchy
2. Reproducibility via version tracking
3. Privacy protection via redaction
4. Decision audit via evidence chain

Design Principles:
- Envelope + Payload: Minimal required fields, extensible attributes
- OpenTelemetry-inspired: trace_id/span_id/parent_span_id vocabulary
- Backward compatible: Adapters for existing TelemetryEvent, resource_telemetry
- Redaction-first: Default to not recording raw inputs/outputs
"""

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SpanKind(str, Enum):
    """Kind of span, inspired by OpenTelemetry"""
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class StatusCode(str, Enum):
    """Status code for span/event outcome"""
    OK = "OK"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    UNSET = "UNSET"


class RedactionStrategy(str, Enum):
    """Strategy for redacting sensitive data"""
    NONE = "none"
    HASH = "hash"
    TRUNCATE = "truncate"
    DROP = "drop"
    ALLOWLIST = "allowlist"


class EvidenceKind(str, Enum):
    """Kind of evidence in the decision chain"""
    RETRIEVAL_DOC = "retrieval_doc"
    DIFF = "diff"
    CI_LOG = "ci_log"
    POLICY = "policy"
    MEMORY = "memory"
    TOOL_OUTPUT = "tool_output"
    USER_INPUT = "user_input"
    MODEL_OUTPUT = "model_output"


def generate_span_id() -> str:
    """Generate a unique span ID (16-byte hex string)"""
    return uuid.uuid4().hex[:16]


def generate_trace_id() -> str:
    """Generate a unique trace ID (32-byte hex string)"""
    return uuid.uuid4().hex


def _get_timestamp_iso() -> str:
    """Get current timestamp in ISO 8601 format with timezone"""
    return datetime.now(timezone.utc).isoformat()


def _get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds (UTC) for cross-service correlation"""
    return time.time_ns() // 1_000_000


def _compute_hash(data: Any, algorithm: str = "sha256") -> str:
    """Compute hash of data for redaction purposes"""
    if data is None:
        return ""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.new(algorithm, serialized.encode()).hexdigest()[:16]


@dataclass
class SpanContext:
    """
    Span context for distributed tracing.

    Provides trace_id, span_id, and parent_span_id for building
    causal trees that enable execution replay.
    """
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None

    def create_child(self) -> "SpanContext":
        """Create a child span context"""
        return SpanContext(
            trace_id=self.trace_id,
            span_id=generate_span_id(),
            parent_span_id=self.span_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id
        return result


def create_span_context(
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
) -> SpanContext:
    """
    Create a new span context.

    Args:
        trace_id: Existing trace ID or None to generate new
        parent_span_id: Parent span ID for child spans

    Returns:
        SpanContext with trace_id, span_id, and optional parent_span_id
    """
    return SpanContext(
        trace_id=trace_id or generate_trace_id(),
        span_id=generate_span_id(),
        parent_span_id=parent_span_id,
    )


@dataclass
class VersionInfo:
    """
    Version information for reproducibility.

    Tracks versions of schema, code, prompts, and configurations
    to enable deterministic replay.
    """
    schema: str = "3.0"
    code_sha: Optional[str] = None
    prompt_template: Optional[Dict[str, str]] = None
    model_config: Optional[Dict[str, Any]] = None
    routing_policy: Optional[str] = None
    governance_policy: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting None values"""
        result = {"schema": self.schema}
        if self.code_sha:
            result["code_sha"] = self.code_sha
        if self.prompt_template:
            result["prompt_template"] = self.prompt_template
        if self.model_config:
            result["model_config"] = self.model_config
        if self.routing_policy:
            result["routing_policy"] = self.routing_policy
        if self.governance_policy:
            result["governance_policy"] = self.governance_policy
        return result


@dataclass
class RedactionInfo:
    """
    Redaction information for privacy protection.

    Tracks what was redacted and how, enabling audit while
    protecting sensitive data.
    """
    strategy: RedactionStrategy = RedactionStrategy.HASH
    fields_dropped: List[str] = field(default_factory=list)
    fields_hashed: List[str] = field(default_factory=list)
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    payload_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, omitting empty values"""
        result = {"strategy": self.strategy.value}
        if self.fields_dropped:
            result["fields_dropped"] = self.fields_dropped
        if self.fields_hashed:
            result["fields_hashed"] = self.fields_hashed
        if self.input_hash:
            result["input_hash"] = self.input_hash
        if self.output_hash:
            result["output_hash"] = self.output_hash
        if self.payload_ref:
            result["payload_ref"] = self.payload_ref
        return result


@dataclass
class EvidenceRef:
    """
    Reference to evidence in the decision chain.

    Tracks what information led to a decision, enabling
    audit and debugging of AI behavior.
    """
    kind: EvidenceKind
    ref: str
    hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "kind": self.kind.value,
            "ref": self.ref,
        }
        if self.hash:
            result["hash"] = self.hash
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class TelemetryRecordV3:
    """
    SSOT Telemetry Record v3 - Single Source of Truth for System Observability.

    This is the unified telemetry schema that all components should emit.
    It provides:
    1. Span hierarchy for causal tree reconstruction
    2. Version tracking for reproducibility
    3. Redaction for privacy protection
    4. Evidence chain for decision audit

    Blueprint Alignment:
    - Section 9.1 Deterministic: trace_id + span hierarchy enables replay
    - Section 9.2 Safe by Design: redaction protects PII/secrets
    - Section 9.3 Self-Governed: version tracking enables policy audit
    """

    # Envelope (required)
    name: str
    timestamp: str
    timestamp_ms: int
    span_context: SpanContext
    component: str
    kind: SpanKind = SpanKind.INTERNAL
    status_code: StatusCode = StatusCode.UNSET
    status_message: Optional[str] = None

    # Actor context (optional)
    agent_id: Optional[str] = None
    node_name: Optional[str] = None
    epic_tag: Optional[str] = None

    # Versions (optional)
    versions: Optional[VersionInfo] = None

    # Redaction (optional)
    redaction: Optional[RedactionInfo] = None

    # Evidence chain (optional)
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    decision_context: Dict[str, Any] = field(default_factory=dict)

    # Metrics (optional)
    metrics: Dict[str, float] = field(default_factory=dict)

    # Attributes (extensible)
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        span_context: SpanContext,
        component: str,
        kind: SpanKind = SpanKind.INTERNAL,
        status_code: StatusCode = StatusCode.UNSET,
        status_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        node_name: Optional[str] = None,
        epic_tag: Optional[str] = None,
        versions: Optional[VersionInfo] = None,
        redaction: Optional[RedactionInfo] = None,
        evidence_refs: Optional[List[EvidenceRef]] = None,
        decision_context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        redact_inputs: bool = True,
        redact_outputs: bool = True,
    ) -> "TelemetryRecordV3":
        """
        Create a new TelemetryRecordV3 with automatic timestamp and redaction.

        Args:
            name: Human-readable event name (e.g., "llm.call", "agent.run")
            span_context: Span context with trace_id, span_id, parent_span_id
            component: Component name (e.g., "FlowController", "ReviewerAgent")
            kind: Span kind (internal, client, server, etc.)
            status_code: Status code (OK, ERROR, SKIPPED, etc.)
            status_message: Optional status message
            agent_id: Optional agent identifier
            node_name: Optional LangGraph node name
            epic_tag: Optional EPIC tag (e.g., "EPIC-C", "EPIC-D")
            versions: Optional version information
            redaction: Optional redaction information (auto-generated if None)
            evidence_refs: Optional list of evidence references
            decision_context: Optional decision context dictionary
            metrics: Optional metrics dictionary
            attributes: Optional attributes dictionary
            input_data: Optional input data (will be hashed if redact_inputs=True)
            output_data: Optional output data (will be hashed if redact_outputs=True)
            redact_inputs: Whether to hash input data (default: True)
            redact_outputs: Whether to hash output data (default: True)

        Returns:
            TelemetryRecordV3 instance
        """
        # Auto-generate redaction info if input/output data provided
        if redaction is None and (input_data is not None or output_data is not None):
            fields_hashed = []
            input_hash = None
            output_hash = None

            if input_data is not None and redact_inputs:
                input_hash = _compute_hash(input_data)
                fields_hashed.append("input")
            if output_data is not None and redact_outputs:
                output_hash = _compute_hash(output_data)
                fields_hashed.append("output")

            redaction = RedactionInfo(
                strategy=RedactionStrategy.HASH,
                fields_hashed=fields_hashed,
                input_hash=input_hash,
                output_hash=output_hash,
            )

        return cls(
            name=name,
            timestamp=_get_timestamp_iso(),
            timestamp_ms=_get_timestamp_ms(),
            span_context=span_context,
            component=component,
            kind=kind,
            status_code=status_code,
            status_message=status_message,
            agent_id=agent_id,
            node_name=node_name,
            epic_tag=epic_tag,
            versions=versions or VersionInfo(),
            redaction=redaction,
            evidence_refs=evidence_refs or [],
            decision_context=decision_context or {},
            metrics=metrics or {},
            attributes=attributes or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Omits None/empty values to keep payload compact.
        """
        result = {
            "schema_version": "3.0",
            "name": self.name,
            "timestamp": self.timestamp,
            "timestamp_ms": self.timestamp_ms,
            "span": self.span_context.to_dict(),
            "component": self.component,
            "kind": self.kind.value,
            "status": {
                "code": self.status_code.value,
            },
        }

        if self.status_message:
            result["status"]["message"] = self.status_message

        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.node_name:
            result["node_name"] = self.node_name
        if self.epic_tag:
            result["epic_tag"] = self.epic_tag

        if self.versions:
            result["versions"] = self.versions.to_dict()

        if self.redaction:
            result["redaction"] = self.redaction.to_dict()

        if self.evidence_refs:
            result["evidence_refs"] = [ref.to_dict() for ref in self.evidence_refs]

        if self.decision_context:
            result["decision_context"] = self.decision_context

        if self.metrics:
            result["metrics"] = self.metrics

        if self.attributes:
            result["attributes"] = self.attributes

        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    def emit(self) -> None:
        """
        Emit this telemetry record to the logging system.

        Uses structured logging with telemetry_v3=True marker
        for downstream filtering.
        """
        if not _is_telemetry_enabled():
            return

        logger.info(
            f"[TelemetryV3] {self.name}",
            extra={
                "telemetry_v3": True,
                "ssot": self.to_dict(),
                "trace_id": self.span_context.trace_id,
                "span_id": self.span_context.span_id,
            }
        )


def _is_telemetry_enabled() -> bool:
    """
    Check if telemetry is enabled via environment variable.

    Respects RESOURCE_TELEMETRY_ENABLED for consistency with
    existing resource_telemetry.py behavior.
    """
    value = os.environ.get("RESOURCE_TELEMETRY_ENABLED", "true").strip().lower()
    return value not in ("false", "0", "no", "off", "")
