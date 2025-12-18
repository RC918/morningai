"""
E2E Tests and TelemetryEvent JSON Schema Validation

Issue #2677 - EPIC #2594: Qwen3 Provider Integration

Tests cover:
- Integration tests with real RoutingEngine (not mocked)
- BaseAgent subclass with routing integration
- TelemetryEvent JSON schema compliance
- Required and optional field validation
"""
import json
import logging
import pytest  # noqa: F401 - pytest fixtures are used implicitly
from datetime import datetime, timezone
from typing import Dict, Any

from core.routing import RoutingEngine, Tier, TaskType, RiskLevel
from core.agents.base import (
    BaseAgent,
    TelemetryEvent,
    TelemetryEventType,
    AgentInput,
    AgentOutput
)


# JSON Schema for TelemetryEvent (based on Ticket #2655 spec)
TELEMETRY_EVENT_SCHEMA = {
    "type": "object",
    "required": ["event_type", "timestamp", "agent_id"],
    "properties": {
        "event_type": {
            "type": "string",
            "enum": ["model_call", "agent_start", "agent_end",
                     "task_start", "task_end", "error"]
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "agent_id": {
            "type": "string",
            "minLength": 1
        },
        "task_type": {
            "type": "string"
        },
        "model_selected": {
            "type": "string"
        },
        "provider": {
            "type": "string"
        },
        "latency_ms": {
            "type": "number",
            "minimum": 0
        },
        "tokens_in": {
            "type": "integer",
            "minimum": 0
        },
        "tokens_out": {
            "type": "integer",
            "minimum": 0
        },
        "success": {
            "type": "boolean"
        },
        "error": {
            "type": "string"
        },
        "metadata": {
            "type": "object"
        }
    },
    "additionalProperties": False
}


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:  # noqa: C901
    """
    Simple JSON schema validation without external dependencies

    Returns True if valid, raises ValueError if invalid
    """
    # Check required fields
    for field in schema.get("required", []):
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Check property types
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key not in properties:
            if schema.get("additionalProperties") is False:
                raise ValueError(f"Unexpected field: {key}")
            continue

        prop_schema = properties[key]
        expected_type = prop_schema.get("type")

        # Type checking
        if expected_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Field {key} should be string, got {type(value)}")
            if "minLength" in prop_schema and len(value) < prop_schema["minLength"]:
                raise ValueError(f"Field {key} too short")
            if "enum" in prop_schema and value not in prop_schema["enum"]:
                raise ValueError(f"Field {key} has invalid value: {value}")
        elif expected_type == "number":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Field {key} should be number, got {type(value)}")
            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                raise ValueError(f"Field {key} below minimum")
        elif expected_type == "integer":
            if not isinstance(value, int):
                raise ValueError(f"Field {key} should be integer, got {type(value)}")
            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                raise ValueError(f"Field {key} below minimum")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"Field {key} should be boolean, got {type(value)}")
        elif expected_type == "object":
            if not isinstance(value, dict):
                raise ValueError(f"Field {key} should be object, got {type(value)}")

    return True


class TestTelemetryEventSchemaCompliance:
    """Tests for TelemetryEvent JSON schema compliance"""

    def test_model_call_event_schema_compliance(self):
        """TelemetryEvent for model_call should match JSON schema"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            task_type="coding",
            model_selected="qwen-max",
            provider="alicloud",
            latency_ms=1500.5,
            tokens_in=500,
            tokens_out=200,
            success=True
        )

        event_dict = event.to_dict()
        assert validate_against_schema(event_dict, TELEMETRY_EVENT_SCHEMA)

    def test_agent_start_event_schema_compliance(self):
        """TelemetryEvent for agent_start should match JSON schema"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.AGENT_START,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="dev_agent",
            task_type="planning",
            metadata={"task_id": "task-123"}
        )

        event_dict = event.to_dict()
        assert validate_against_schema(event_dict, TELEMETRY_EVENT_SCHEMA)

    def test_agent_end_event_schema_compliance(self):
        """TelemetryEvent for agent_end should match JSON schema"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.AGENT_END,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="dev_agent",
            task_type="planning",
            latency_ms=5000.0,
            success=True,
            metadata={"task_id": "task-123"}
        )

        event_dict = event.to_dict()
        assert validate_against_schema(event_dict, TELEMETRY_EVENT_SCHEMA)

    def test_error_event_schema_compliance(self):
        """TelemetryEvent for error should match JSON schema"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.ERROR,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            task_type="coding",
            latency_ms=100.0,
            success=False,
            error="Connection timeout"
        )

        event_dict = event.to_dict()
        assert validate_against_schema(event_dict, TELEMETRY_EVENT_SCHEMA)

    def test_minimal_event_has_required_fields(self):
        """Minimal TelemetryEvent should have all required fields"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent"
        )

        event_dict = event.to_dict()

        # Check required fields are present
        assert "event_type" in event_dict
        assert "timestamp" in event_dict
        assert "agent_id" in event_dict

    def test_optional_fields_omitted_when_none(self):
        """Optional fields should be omitted when None"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            task_type=None,
            model_selected=None,
            provider=None,
            latency_ms=None,
            tokens_in=None,
            tokens_out=None,
            success=None,
            error=None
        )

        event_dict = event.to_dict()

        # Optional fields should not be present
        assert "task_type" not in event_dict
        assert "model_selected" not in event_dict
        assert "provider" not in event_dict
        assert "latency_ms" not in event_dict
        assert "tokens_in" not in event_dict
        assert "tokens_out" not in event_dict
        assert "success" not in event_dict
        assert "error" not in event_dict

    def test_metadata_omitted_when_empty(self):
        """Metadata should be omitted when empty dict"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            metadata={}
        )

        event_dict = event.to_dict()
        assert "metadata" not in event_dict

    def test_metadata_included_when_present(self):
        """Metadata should be included when not empty"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            metadata={"key": "value"}
        )

        event_dict = event.to_dict()
        assert "metadata" in event_dict
        assert event_dict["metadata"] == {"key": "value"}

    def test_event_type_values_are_valid(self):
        """All TelemetryEventType values should be valid"""
        valid_types = ["model_call", "agent_start", "agent_end",
                       "task_start", "task_end", "error"]

        for event_type in TelemetryEventType:
            assert event_type.value in valid_types

    def test_to_json_produces_valid_json(self):
        """to_json() should produce valid JSON string"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent",
            task_type="coding",
            model_selected="qwen-max",
            provider="alicloud",
            latency_ms=1500.5,
            tokens_in=500,
            tokens_out=200,
            success=True
        )

        json_str = event.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["event_type"] == "model_call"
        assert parsed["agent_id"] == "test_agent"


class TestRoutingEngineE2EIntegration:
    """E2E integration tests with real RoutingEngine (not mocked)"""

    def test_routing_engine_selects_correct_tier_for_planning(self):
        """Real RoutingEngine should select Tier 0 for planning tasks"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_info = engine.select_model(TaskType.PLANNING)

        assert model_info.tier == Tier.TIER_0
        assert model_info.model_name == "qwen-max"
        assert model_info.provider == "alicloud"

    def test_routing_engine_selects_correct_tier_for_coding(self):
        """Real RoutingEngine should select Tier 1 for coding tasks"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_info = engine.select_model(TaskType.CODING)

        assert model_info.tier == Tier.TIER_1
        assert model_info.model_name == "qwen-plus"
        assert model_info.provider == "alicloud"

    def test_routing_engine_selects_correct_tier_for_ux_copy(self):
        """Real RoutingEngine should select Tier 3 for UX copy tasks"""
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.UX_COPY)

        assert model_info.tier == Tier.TIER_3
        assert model_info.provider == "siliconflow"

    def test_routing_engine_handles_risk_level_adjustment(self):
        """Real RoutingEngine should adjust tier based on risk level"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # High risk should upgrade tier (lower number)
        high_risk_model = engine.select_model(TaskType.CODING, risk_level=RiskLevel.HIGH)
        assert high_risk_model.tier == Tier.TIER_0

        # Low risk should downgrade tier (higher number)
        low_risk_model = engine.select_model(TaskType.CODING, risk_level=RiskLevel.LOW)
        assert low_risk_model.tier == Tier.TIER_2

    def test_routing_engine_handles_context_size(self):
        """Real RoutingEngine should adjust tier based on context size"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Large context should upgrade to higher capability tier
        model_info = engine.select_model(
            TaskType.UX_COPY,
            context_size=50000  # Exceeds Tier 3 (8000) and Tier 2 (32000) limits
        )

        # Should upgrade to Tier 0 or 1 (128000 limit)
        assert model_info.tier.value <= Tier.TIER_1.value

    def test_routing_engine_fallback_mechanism(self):
        """Real RoutingEngine should use fallback when primary tier unavailable"""
        # Only siliconflow available, but planning needs Tier 0 (alicloud)
        engine = RoutingEngine(available_providers=["siliconflow"])

        model_info = engine.select_model(TaskType.PLANNING)

        # Should fallback to available provider
        assert model_info.provider == "siliconflow"
        assert model_info.is_fallback is True

    def test_routing_engine_all_task_types(self):
        """Real RoutingEngine should handle all task types"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        for task_type in TaskType:
            model_info = engine.select_model(task_type)
            assert model_info is not None
            assert model_info.model_name is not None
            assert model_info.provider is not None


class TestBaseAgentE2EIntegration:
    """E2E integration tests for BaseAgent with real RoutingEngine"""

    def test_base_agent_initialization(self):
        """BaseAgent should initialize with agent_id"""
        class TestAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(task_id=input.task_id, success=True)

        agent = TestAgent(agent_id="test_agent")
        assert agent.agent_id == "test_agent"

    def test_base_agent_telemetry_emission(self, caplog):
        """BaseAgent should emit telemetry events"""
        class TestAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(task_id=input.task_id, success=True)

        agent = TestAgent(agent_id="test_agent")

        with caplog.at_level(logging.INFO):
            output = agent.run(AgentInput(
                task_id="task-123",
                prompt="Test prompt",
                task_type="coding"
            ))

        assert output.success is True
        # Should have emitted telemetry events
        assert "agent_start" in caplog.text.lower() or "Telemetry" in caplog.text

    def test_base_agent_run_wraps_execute(self):
        """BaseAgent.run() should wrap execute() with telemetry"""
        class TestAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(
                    task_id=input.task_id,
                    success=True,
                    data={"result": "test"}
                )

        agent = TestAgent(agent_id="test_agent")
        output = agent.run(AgentInput(
            task_id="task-123",
            prompt="Test prompt",
            task_type="coding"
        ))

        assert output.success is True
        assert output.data == {"result": "test"}
        assert output.latency_ms > 0

    def test_base_agent_handles_execute_error(self):
        """BaseAgent.run() should handle errors in execute()"""
        class FailingAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                raise ValueError("Test error")

        agent = FailingAgent(agent_id="failing_agent")
        output = agent.run(AgentInput(
            task_id="task-123",
            prompt="Test prompt",
            task_type="coding"
        ))

        assert output.success is False
        assert "Test error" in output.error

    def test_base_agent_get_routing_engine(self):
        """BaseAgent should be able to get RoutingEngine"""
        class TestAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(task_id=input.task_id, success=True)

            def test_routing(self):
                return self._get_routing_engine()

        agent = TestAgent(agent_id="test_agent")
        routing_engine = agent.test_routing()

        # May be None if providers not configured, but should not raise
        # The test verifies the method exists and is callable
        assert routing_engine is None or isinstance(routing_engine, RoutingEngine)


class TestAgentInputOutputSchemas:
    """Tests for AgentInput and AgentOutput schemas"""

    def test_agent_input_to_dict(self):
        """AgentInput.to_dict() should produce valid dict"""
        input = AgentInput(
            task_id="task-123",
            prompt="Test prompt",
            task_type="coding",
            risk_level="high",
            context={"key": "value"},
            metadata={"meta": "data"}
        )

        input_dict = input.to_dict()

        assert input_dict["task_id"] == "task-123"
        assert input_dict["prompt"] == "Test prompt"
        assert input_dict["task_type"] == "coding"
        assert input_dict["risk_level"] == "high"
        assert input_dict["context"] == {"key": "value"}
        assert input_dict["metadata"] == {"meta": "data"}

    def test_agent_input_from_dict(self):
        """AgentInput.from_dict() should create valid instance"""
        data = {
            "task_id": "task-123",
            "prompt": "Test prompt",
            "task_type": "coding",
            "risk_level": "high",
            "context": {"key": "value"},
            "metadata": {"meta": "data"}
        }

        input = AgentInput.from_dict(data)

        assert input.task_id == "task-123"
        assert input.prompt == "Test prompt"
        assert input.task_type == "coding"
        assert input.risk_level == "high"

    def test_agent_output_to_dict(self):
        """AgentOutput.to_dict() should produce valid dict"""
        output = AgentOutput(
            task_id="task-123",
            success=True,
            data={"result": "test"},
            latency_ms=100.5,
            model_used="qwen-max",
            provider_used="alicloud",
            tokens_in=500,
            tokens_out=200
        )

        output_dict = output.to_dict()

        assert output_dict["task_id"] == "task-123"
        assert output_dict["success"] is True
        assert output_dict["data"] == {"result": "test"}
        assert output_dict["latency_ms"] == 100.5
        assert output_dict["model_used"] == "qwen-max"
        assert output_dict["provider_used"] == "alicloud"
        assert output_dict["tokens_in"] == 500
        assert output_dict["tokens_out"] == 200

    def test_agent_output_omits_none_fields(self):
        """AgentOutput.to_dict() should omit None fields"""
        output = AgentOutput(
            task_id="task-123",
            success=True
        )

        output_dict = output.to_dict()

        assert "error" not in output_dict
        assert "model_used" not in output_dict
        assert "provider_used" not in output_dict
        assert "tokens_in" not in output_dict
        assert "tokens_out" not in output_dict


class TestTelemetryEventTimestamp:
    """Tests for TelemetryEvent timestamp format"""

    def test_timestamp_is_iso_format(self):
        """Timestamp should be in ISO 8601 format"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id="test_agent"
        )

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
        assert parsed is not None

    def test_timestamp_includes_timezone(self):
        """Timestamp should include timezone info"""
        timestamp = datetime.now(timezone.utc).isoformat()
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp=timestamp,
            agent_id="test_agent"
        )

        # Should contain timezone indicator
        assert '+' in event.timestamp or 'Z' in event.timestamp


class TestTelemetryEventTypes:
    """Tests for all TelemetryEventType values"""

    def test_model_call_event_type(self):
        """MODEL_CALL event type should have correct value"""
        assert TelemetryEventType.MODEL_CALL.value == "model_call"

    def test_agent_start_event_type(self):
        """AGENT_START event type should have correct value"""
        assert TelemetryEventType.AGENT_START.value == "agent_start"

    def test_agent_end_event_type(self):
        """AGENT_END event type should have correct value"""
        assert TelemetryEventType.AGENT_END.value == "agent_end"

    def test_task_start_event_type(self):
        """TASK_START event type should have correct value"""
        assert TelemetryEventType.TASK_START.value == "task_start"

    def test_task_end_event_type(self):
        """TASK_END event type should have correct value"""
        assert TelemetryEventType.TASK_END.value == "task_end"

    def test_error_event_type(self):
        """ERROR event type should have correct value"""
        assert TelemetryEventType.ERROR.value == "error"


class TestRoutingDecisionVerification:
    """Tests to verify routing decisions match expected tier for different task types"""

    def test_planning_task_uses_tier_0(self):
        """Planning task should use Tier 0 (highest capability)"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model = engine.select_model(TaskType.PLANNING)
        assert model.tier == Tier.TIER_0

    def test_coding_task_uses_tier_1(self):
        """Coding task should use Tier 1"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model = engine.select_model(TaskType.CODING)
        assert model.tier == Tier.TIER_1

    def test_review_task_uses_tier_1(self):
        """Review task should use Tier 1"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model = engine.select_model(TaskType.REVIEW)
        assert model.tier == Tier.TIER_1

    def test_analysis_task_uses_tier_1(self):
        """Analysis task should use Tier 1"""
        engine = RoutingEngine(available_providers=["alicloud"])
        model = engine.select_model(TaskType.ANALYSIS)
        assert model.tier == Tier.TIER_1

    def test_chat_task_uses_tier_2(self):
        """Chat task should use Tier 2"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        model = engine.select_model(TaskType.CHAT)
        assert model.tier == Tier.TIER_2

    def test_translation_task_uses_tier_2(self):
        """Translation task should use Tier 2"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        model = engine.select_model(TaskType.TRANSLATION)
        assert model.tier == Tier.TIER_2

    def test_summarization_task_uses_tier_2(self):
        """Summarization task should use Tier 2"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        model = engine.select_model(TaskType.SUMMARIZATION)
        assert model.tier == Tier.TIER_2

    def test_ux_copy_task_uses_tier_3(self):
        """UX copy task should use Tier 3 (basic capability)"""
        engine = RoutingEngine(available_providers=["siliconflow"])
        model = engine.select_model(TaskType.UX_COPY)
        assert model.tier == Tier.TIER_3
