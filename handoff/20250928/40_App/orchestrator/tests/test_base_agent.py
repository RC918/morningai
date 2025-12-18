"""
Unit tests for Base Agent Class

EPIC #2594 - Ticket 3: Agent Base Class Upgrade (AIP v2)

Tests cover:
- BaseAgent initialization
- AgentInput/AgentOutput schemas
- TelemetryEvent creation and serialization
- call_llm() with routing integration
- run() with telemetry tracking
"""
from unittest.mock import patch, MagicMock

from core.agents import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    TelemetryEvent,
    TelemetryEventType,
)


class TestTelemetryEvent:
    """Tests for TelemetryEvent dataclass"""

    def test_create_model_call_event(self):
        """Test creating a model_call telemetry event"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp="2025-12-17T19:00:00Z",
            agent_id="dev_agent",
            task_type="coding",
            model_selected="qwen-max",
            provider="alicloud",
            latency_ms=1500,
            tokens_in=500,
            tokens_out=200
        )

        assert event.event_type == TelemetryEventType.MODEL_CALL
        assert event.agent_id == "dev_agent"
        assert event.task_type == "coding"
        assert event.model_selected == "qwen-max"
        assert event.provider == "alicloud"
        assert event.latency_ms == 1500
        assert event.tokens_in == 500
        assert event.tokens_out == 200

    def test_to_dict(self):
        """Test converting TelemetryEvent to dictionary"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp="2025-12-17T19:00:00Z",
            agent_id="dev_agent",
            task_type="coding",
            model_selected="qwen-max",
            provider="alicloud",
            latency_ms=1500,
            tokens_in=500,
            tokens_out=200
        )

        result = event.to_dict()

        assert result["event_type"] == "model_call"
        assert result["timestamp"] == "2025-12-17T19:00:00Z"
        assert result["agent_id"] == "dev_agent"
        assert result["task_type"] == "coding"
        assert result["model_selected"] == "qwen-max"
        assert result["provider"] == "alicloud"
        assert result["latency_ms"] == 1500
        assert result["tokens_in"] == 500
        assert result["tokens_out"] == 200

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.AGENT_START,
            timestamp="2025-12-17T19:00:00Z",
            agent_id="test_agent"
        )

        result = event.to_dict()

        assert result["event_type"] == "agent_start"
        assert result["timestamp"] == "2025-12-17T19:00:00Z"
        assert result["agent_id"] == "test_agent"
        assert "task_type" not in result
        assert "model_selected" not in result

    def test_to_json(self):
        """Test converting TelemetryEvent to JSON string"""
        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp="2025-12-17T19:00:00Z",
            agent_id="dev_agent",
            task_type="coding"
        )

        json_str = event.to_json()

        assert '"event_type": "model_call"' in json_str
        assert '"agent_id": "dev_agent"' in json_str


class TestAgentInput:
    """Tests for AgentInput dataclass"""

    def test_create_input(self):
        """Test creating AgentInput"""
        input = AgentInput(
            task_id="task-123",
            prompt="Write a function",
            task_type="coding",
            risk_level="medium"
        )

        assert input.task_id == "task-123"
        assert input.prompt == "Write a function"
        assert input.task_type == "coding"
        assert input.risk_level == "medium"

    def test_default_values(self):
        """Test AgentInput default values"""
        input = AgentInput(
            task_id="task-123",
            prompt="Test prompt"
        )

        assert input.task_type == "general"
        assert input.risk_level == "medium"
        assert input.context == {}
        assert input.metadata == {}

    def test_to_dict(self):
        """Test converting AgentInput to dictionary"""
        input = AgentInput(
            task_id="task-123",
            prompt="Test prompt",
            task_type="coding"
        )

        result = input.to_dict()

        assert result["task_id"] == "task-123"
        assert result["prompt"] == "Test prompt"
        assert result["task_type"] == "coding"

    def test_from_dict(self):
        """Test creating AgentInput from dictionary"""
        data = {
            "task_id": "task-456",
            "prompt": "Another prompt",
            "task_type": "review",
            "risk_level": "high",
            "context": {"key": "value"},
            "metadata": {}
        }

        input = AgentInput.from_dict(data)

        assert input.task_id == "task-456"
        assert input.prompt == "Another prompt"
        assert input.task_type == "review"
        assert input.risk_level == "high"
        assert input.context == {"key": "value"}


class TestAgentOutput:
    """Tests for AgentOutput dataclass"""

    def test_create_success_output(self):
        """Test creating successful AgentOutput"""
        output = AgentOutput(
            task_id="task-123",
            success=True,
            data={"response": "Generated code"},
            model_used="qwen-max",
            provider_used="alicloud"
        )

        assert output.task_id == "task-123"
        assert output.success is True
        assert output.data == {"response": "Generated code"}
        assert output.model_used == "qwen-max"
        assert output.provider_used == "alicloud"

    def test_create_error_output(self):
        """Test creating error AgentOutput"""
        output = AgentOutput(
            task_id="task-123",
            success=False,
            error="API call failed"
        )

        assert output.task_id == "task-123"
        assert output.success is False
        assert output.error == "API call failed"

    def test_to_dict(self):
        """Test converting AgentOutput to dictionary"""
        output = AgentOutput(
            task_id="task-123",
            success=True,
            data={"result": "ok"},
            latency_ms=150.5,
            model_used="gpt-4o",
            tokens_in=100,
            tokens_out=50
        )

        result = output.to_dict()

        assert result["task_id"] == "task-123"
        assert result["success"] is True
        assert result["data"] == {"result": "ok"}
        assert result["latency_ms"] == 150.5
        assert result["model_used"] == "gpt-4o"
        assert result["tokens_in"] == 100
        assert result["tokens_out"] == 50


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""

    def execute(self, input: AgentInput) -> AgentOutput:
        """Simple execute implementation"""
        return AgentOutput(
            task_id=input.task_id,
            success=True,
            data={"echo": input.prompt}
        )


class TestBaseAgent:
    """Tests for BaseAgent class"""

    def test_init(self):
        """Test BaseAgent initialization"""
        agent = ConcreteAgent(agent_id="test_agent")

        assert agent.agent_id == "test_agent"
        assert agent._routing_engine is None
        assert agent._llm_client is None
        assert agent._telemetry_enabled is True

    def test_get_timestamp(self):
        """Test timestamp generation"""
        agent = ConcreteAgent(agent_id="test_agent")

        timestamp = agent._get_timestamp()

        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp

    def test_execute(self):
        """Test execute method"""
        agent = ConcreteAgent(agent_id="test_agent")
        input = AgentInput(
            task_id="task-123",
            prompt="Hello world"
        )

        output = agent.execute(input)

        assert output.task_id == "task-123"
        assert output.success is True
        assert output.data == {"echo": "Hello world"}

    def test_run_with_telemetry(self):
        """Test run method with telemetry tracking"""
        agent = ConcreteAgent(agent_id="test_agent")
        input = AgentInput(
            task_id="task-123",
            prompt="Test prompt",
            task_type="coding"
        )

        output = agent.run(input)

        assert output.task_id == "task-123"
        assert output.success is True
        assert output.latency_ms > 0

    def test_run_handles_exception(self):
        """Test run method handles exceptions gracefully"""
        class FailingAgent(BaseAgent):
            def execute(self, input: AgentInput) -> AgentOutput:
                raise ValueError("Test error")

        agent = FailingAgent(agent_id="failing_agent")
        input = AgentInput(
            task_id="task-123",
            prompt="Test"
        )

        output = agent.run(input)

        assert output.task_id == "task-123"
        assert output.success is False
        assert "Test error" in output.error

    @patch('core.agents.base.BaseAgent._get_routing_engine')
    @patch('core.agents.base.BaseAgent._get_llm_client')
    def test_call_llm_with_routing(self, mock_get_client, mock_get_engine):
        """Test call_llm uses routing engine"""
        mock_engine = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.provider = "alicloud"
        mock_model_info.model_name = "qwen-max"
        mock_model_info.tier.value = 0
        mock_model_info.is_fallback = False
        mock_engine.select_model.return_value = mock_model_info
        mock_get_engine.return_value = mock_engine

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Generated response"
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_client.generate.return_value = mock_response
        mock_client.model = "qwen-max"
        mock_client.provider_name = "alicloud"
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent(agent_id="test_agent")

        result = agent.call_llm(
            prompt="Write a function",
            task_type="coding",
            risk_level="medium"
        )

        assert result["content"] == "Generated response"
        assert result["model"] == "qwen-max"
        assert result["provider"] == "alicloud"
        mock_engine.select_model.assert_called_once()

    @patch('core.agents.base.BaseAgent._get_routing_engine')
    @patch('core.agents.base.BaseAgent._get_llm_client')
    def test_call_llm_fallback_on_routing_failure(self, mock_get_client, mock_get_engine):
        """Test call_llm falls back to auto provider when routing fails"""
        mock_get_engine.return_value = None

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Fallback response"
        mock_response.prompt_tokens = None
        mock_response.completion_tokens = None
        mock_client.generate.return_value = mock_response
        mock_client.model = "gpt-4o"
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        agent = ConcreteAgent(agent_id="test_agent")

        result = agent.call_llm(
            prompt="Test prompt",
            task_type="coding"
        )

        assert result["content"] == "Fallback response"
        mock_get_client.assert_called_with(provider="auto", model=None)

    def test_emit_telemetry_disabled(self):
        """Test telemetry can be disabled"""
        agent = ConcreteAgent(agent_id="test_agent")
        agent._telemetry_enabled = False

        event = TelemetryEvent(
            event_type=TelemetryEventType.MODEL_CALL,
            timestamp="2025-12-17T19:00:00Z",
            agent_id="test_agent"
        )

        agent._emit_telemetry(event)


class TestTelemetryEventTypes:
    """Tests for TelemetryEventType enum"""

    def test_all_event_types(self):
        """Test all telemetry event types exist"""
        assert TelemetryEventType.MODEL_CALL.value == "model_call"
        assert TelemetryEventType.AGENT_START.value == "agent_start"
        assert TelemetryEventType.AGENT_END.value == "agent_end"
        assert TelemetryEventType.TASK_START.value == "task_start"
        assert TelemetryEventType.TASK_END.value == "task_end"
        assert TelemetryEventType.ERROR.value == "error"


class TestIntegration:
    """Integration tests for BaseAgent with real components"""

    @patch('core.agents.base.BaseAgent._get_routing_engine')
    def test_agent_workflow(self, mock_get_engine):
        """Test complete agent workflow"""
        mock_get_engine.return_value = None

        agent = ConcreteAgent(agent_id="integration_test")

        input = AgentInput(
            task_id="integration-task-1",
            prompt="Integration test prompt",
            task_type="coding",
            risk_level="low",
            context={"test": True}
        )

        output = agent.run(input)

        assert output.task_id == "integration-task-1"
        assert output.success is True
        assert output.latency_ms >= 0
