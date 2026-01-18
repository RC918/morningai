"""
Tests for SSOT Telemetry Adapters

Tests cover backward compatibility adapters:
1. from_agent_telemetry_event: Convert BaseAgent TelemetryEvent
2. from_resource_telemetry_event: Convert resource_telemetry events
3. from_policy_telemetry_event: Convert RuntimePolicyEnforcer events
4. from_routing_decision: Convert routing decisions (EPIC I Issue #4085)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from core.telemetry.adapters import (
    from_agent_telemetry_event,
    from_resource_telemetry_event,
    from_policy_telemetry_event,
    from_routing_decision,
)
from core.telemetry.schema import (
    StatusCode,
)


class MockTelemetryEventType(str, Enum):
    """Mock TelemetryEventType for testing"""
    MODEL_CALL = "model_call"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    ERROR = "error"


@dataclass
class MockTelemetryEvent:
    """Mock TelemetryEvent for testing adapters"""
    event_type: MockTelemetryEventType
    timestamp: str
    agent_id: str
    task_type: Optional[str] = None
    model_selected: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[float] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestFromAgentTelemetryEvent:
    """Tests for from_agent_telemetry_event adapter"""

    def test_basic_conversion(self):
        """Should convert basic TelemetryEvent to TelemetryRecordV3"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.name == "agent.model_call"
        assert record.span_context.trace_id == "trace123"
        assert record.agent_id == "test_agent"
        assert record.component == "BaseAgent"
        assert record.epic_tag == "EPIC-D"

    def test_success_status(self):
        """Should set OK status when success=True"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.AGENT_END,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
            success=True,
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.status_code == StatusCode.OK

    def test_error_status(self):
        """Should set ERROR status when success=False"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.ERROR,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
            success=False,
            error="Something went wrong",
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.status_code == StatusCode.ERROR
        assert record.status_message == "Something went wrong"

    def test_metrics_conversion(self):
        """Should convert latency_ms, tokens_in, tokens_out to metrics"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
            latency_ms=1500.5,
            tokens_in=500,
            tokens_out=200,
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.metrics["latency_ms"] == 1500.5
        assert record.metrics["tokens_in"] == 500.0
        assert record.metrics["tokens_out"] == 200.0

    def test_attributes_conversion(self):
        """Should convert task_type, model_selected, provider to attributes"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
            task_type="review",
            model_selected="qwen-max",
            provider="alicloud",
            metadata={"custom_key": "custom_value"},
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.attributes["task_type"] == "review"
        assert record.attributes["model_selected"] == "qwen-max"
        assert record.attributes["provider"] == "alicloud"
        assert record.attributes["metadata"]["custom_key"] == "custom_value"

    def test_version_info_from_model(self):
        """Should create VersionInfo from model_selected and provider"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
            model_selected="qwen-max",
            provider="alicloud",
        )

        record = from_agent_telemetry_event(event, trace_id="trace123")

        assert record.versions is not None
        assert record.versions.model_config["provider"] == "alicloud"
        assert record.versions.model_config["model"] == "qwen-max"

    def test_parent_span_id(self):
        """Should set parent_span_id when provided"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
        )

        record = from_agent_telemetry_event(
            event,
            trace_id="trace123",
            parent_span_id="parent456",
        )

        assert record.span_context.parent_span_id == "parent456"

    def test_custom_epic_tag(self):
        """Should use custom epic_tag when provided"""
        event = MockTelemetryEvent(
            event_type=MockTelemetryEventType.MODEL_CALL,
            timestamp="2025-01-01T00:00:00Z",
            agent_id="test_agent",
        )

        record = from_agent_telemetry_event(
            event,
            trace_id="trace123",
            epic_tag="EPIC-B",
        )

        assert record.epic_tag == "EPIC-B"


class TestFromResourceTelemetryEvent:
    """Tests for from_resource_telemetry_event adapter"""

    def test_resource_peak_conversion(self):
        """Should convert RESOURCE_PEAK event correctly"""
        record = from_resource_telemetry_event(
            event_code="RESOURCE_PEAK",
            trace_id="trace123",
            node_name="reviewer_node",
            metrics={"current_rss_mb": 512.5},
        )

        assert record.name == "resource.peak"
        assert record.span_context.trace_id == "trace123"
        assert record.node_name == "reviewer_node"
        assert record.component == "ResourceTelemetry"
        assert record.epic_tag == "EPIC-C"
        assert record.metrics["current_rss_mb"] == 512.5

    def test_diff_fetch_bytes_conversion(self):
        """Should convert DIFF_FETCH_BYTES event correctly"""
        record = from_resource_telemetry_event(
            event_code="DIFF_FETCH_BYTES",
            trace_id="trace123",
            metrics={"bytes": 1024},
            attributes={"pr_number": 123},
        )

        assert record.name == "github.diff_fetch"
        assert record.attributes["event_code"] == "DIFF_FETCH_BYTES"
        assert record.attributes["pr_number"] == 123

    def test_unknown_event_code(self):
        """Should handle unknown event codes gracefully"""
        record = from_resource_telemetry_event(
            event_code="CUSTOM_EVENT",
            trace_id="trace123",
        )

        assert record.name == "resource.custom_event"
        assert record.attributes["event_code"] == "CUSTOM_EVENT"

    def test_parent_span_id(self):
        """Should set parent_span_id when provided"""
        record = from_resource_telemetry_event(
            event_code="RESOURCE_PEAK",
            trace_id="trace123",
            parent_span_id="parent456",
        )

        assert record.span_context.parent_span_id == "parent456"

    def test_custom_epic_tag(self):
        """Should use custom epic_tag when provided"""
        record = from_resource_telemetry_event(
            event_code="RESOURCE_PEAK",
            trace_id="trace123",
            epic_tag="EPIC-I",
        )

        assert record.epic_tag == "EPIC-I"


class TestFromPolicyTelemetryEvent:
    """Tests for from_policy_telemetry_event adapter"""

    def test_allow_action_conversion(self):
        """Should convert allow action to OK status"""
        event_dict = {
            "event_type": "budget_check",
            "action": "allow",
            "current_tokens": 1000,
            "max_tokens": 5000,
        }

        record = from_policy_telemetry_event(event_dict, trace_id="trace123")

        assert record.name == "governance.budget_check"
        assert record.status_code == StatusCode.OK
        assert record.component == "RuntimePolicyEnforcer"
        assert record.epic_tag == "EPIC-I"
        assert record.metrics["current_tokens"] == 1000.0
        assert record.metrics["max_tokens"] == 5000.0

    def test_block_action_conversion(self):
        """Should convert block action to ERROR status"""
        event_dict = {
            "event_type": "budget_check",
            "action": "block",
            "error": "Budget exceeded",
            "current_usd": 10.5,
            "max_usd": 10.0,
        }

        record = from_policy_telemetry_event(event_dict, trace_id="trace123")

        assert record.status_code == StatusCode.ERROR
        assert record.status_message == "Budget exceeded"
        assert record.metrics["current_usd"] == 10.5
        assert record.metrics["max_usd"] == 10.0

    def test_require_approval_action_conversion(self):
        """Should convert require_approval action to SKIPPED status"""
        event_dict = {
            "event_type": "hitl_gate",
            "action": "require_approval",
            "reason": "High risk operation",
        }

        record = from_policy_telemetry_event(event_dict, trace_id="trace123")

        assert record.status_code == StatusCode.SKIPPED
        assert record.attributes["reason"] == "High risk operation"

    def test_attributes_filtering(self):
        """Should filter out known fields from attributes"""
        event_dict = {
            "event_type": "policy_check",
            "timestamp": "2025-01-01T00:00:00Z",
            "component": "PolicyEnforcer",
            "action": "allow",
            "current_tokens": 1000,
            "max_tokens": 5000,
            "custom_field": "custom_value",
        }

        record = from_policy_telemetry_event(event_dict, trace_id="trace123")

        assert "timestamp" not in record.attributes
        assert "component" not in record.attributes
        assert "action" not in record.attributes
        assert "current_tokens" not in record.attributes
        assert record.attributes["custom_field"] == "custom_value"

    def test_parent_span_id(self):
        """Should set parent_span_id when provided"""
        event_dict = {"event_type": "policy_check", "action": "allow"}

        record = from_policy_telemetry_event(
            event_dict,
            trace_id="trace123",
            parent_span_id="parent456",
        )

        assert record.span_context.parent_span_id == "parent456"

    def test_custom_epic_tag(self):
        """Should use custom epic_tag when provided"""
        event_dict = {"event_type": "policy_check", "action": "allow"}

        record = from_policy_telemetry_event(
            event_dict,
            trace_id="trace123",
            epic_tag="EPIC-E",
        )

        assert record.epic_tag == "EPIC-E"


class TestFromRoutingDecision:
    """
    Tests for from_routing_decision adapter

    EPIC I Integration (Issue #4085): Multi-Provider Governance
    Tests cover provider-aware telemetry for Gemini-first routing.
    """

    def test_basic_routing_decision(self):
        """Should create telemetry record for basic routing decision"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-pro-preview",
            trace_id="trace123",
        )

        assert record.name == "routing.decision"
        assert record.span_context.trace_id == "trace123"
        assert record.component == "RoutingEngine"
        assert record.epic_tag == "EPIC-I"
        assert record.provider == "gemini"
        assert record.model_name == "gemini-3-pro-preview"
        assert record.is_fallback is False
        assert record.status_code == StatusCode.OK

    def test_fallback_routing_decision(self):
        """Should create telemetry record for fallback routing decision"""
        record = from_routing_decision(
            provider="alicloud",
            model_name="qwen-max",
            trace_id="trace123",
            is_fallback=True,
            fallback_reason="Primary provider gemini unavailable",
        )

        assert record.name == "routing.fallback"
        assert record.provider == "alicloud"
        assert record.model_name == "qwen-max"
        assert record.is_fallback is True
        assert record.fallback_reason == "Primary provider gemini unavailable"
        assert record.status_message == "Primary provider gemini unavailable"

    def test_with_task_type(self):
        """Should include task_type in attributes"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-flash-preview",
            trace_id="trace123",
            task_type="review",
        )

        assert record.attributes["task_type"] == "review"

    def test_with_estimated_cost(self):
        """Should include estimated_cost in metrics and field"""
        record = from_routing_decision(
            provider="openai",
            model_name="gpt-4o",
            trace_id="trace123",
            estimated_cost=0.05,
        )

        assert record.estimated_cost == 0.05
        assert record.metrics["estimated_cost_usd"] == 0.05

    def test_parent_span_id(self):
        """Should set parent_span_id when provided"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-pro-preview",
            trace_id="trace123",
            parent_span_id="parent456",
        )

        assert record.span_context.parent_span_id == "parent456"

    def test_custom_epic_tag(self):
        """Should use custom epic_tag when provided"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-pro-preview",
            trace_id="trace123",
            epic_tag="EPIC-D",
        )

        assert record.epic_tag == "EPIC-D"

    def test_to_dict_includes_provider_fields(self):
        """Should include provider fields in to_dict output"""
        record = from_routing_decision(
            provider="alicloud",
            model_name="qwen-plus",
            trace_id="trace123",
            is_fallback=True,
            fallback_reason="Rate limit exceeded",
            estimated_cost=0.02,
        )

        result = record.to_dict()

        assert result["provider"] == "alicloud"
        assert result["model_name"] == "qwen-plus"
        assert result["is_fallback"] is True
        assert result["fallback_reason"] == "Rate limit exceeded"
        assert result["estimated_cost"] == 0.02

    def test_gemini_first_routing(self):
        """Should correctly capture Gemini-first routing decision"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-pro-preview",
            trace_id="trace123",
            task_type="planning",
            estimated_cost=0.01,
        )

        assert record.provider == "gemini"
        assert record.is_fallback is False
        assert record.attributes["task_type"] == "planning"

    def test_cross_provider_fallback(self):
        """Should correctly capture cross-provider fallback"""
        record = from_routing_decision(
            provider="openai",
            model_name="gpt-4o",
            trace_id="trace123",
            task_type="coding",
            is_fallback=True,
            fallback_reason="Gemini and AliCloud unavailable",
            estimated_cost=0.10,
        )

        assert record.provider == "openai"
        assert record.is_fallback is True
        assert record.fallback_reason == "Gemini and AliCloud unavailable"
        assert record.estimated_cost == 0.10

    def test_sanitizes_fallback_reason_and_task_type(self):
        """Should sanitize fallback_reason and task_type to prevent log injection (Issue #3718)"""
        record = from_routing_decision(
            provider="gemini",
            model_name="gemini-3-pro-preview",
            trace_id="trace123",
            task_type="malicious\ninjection\rattempt",
            is_fallback=True,
            fallback_reason="error\nwith\nnewlines",
        )

        # Newlines should be replaced with underscores
        assert "\n" not in record.status_message
        assert "\r" not in record.status_message
        assert "\n" not in record.attributes["task_type"]
        assert "\r" not in record.attributes["task_type"]
        # Verify sanitization replaced control characters
        assert record.status_message == "error_with_newlines"
        assert record.attributes["task_type"] == "malicious_injection_attempt"
