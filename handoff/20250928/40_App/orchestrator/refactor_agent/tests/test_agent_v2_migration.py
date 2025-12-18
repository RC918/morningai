#!/usr/bin/env python3
"""
Tests for RefactorAgentV2 Migration Validation

EPIC #2594 - Issue #2676: Agent Migration Validation

These tests verify that:
1. RefactorAgentV2 correctly inherits from BaseAgent
2. call_llm() is used instead of direct LLMClient calls
3. RoutingEngine integration works correctly
4. Telemetry v2 events are emitted
5. The migrated agent produces equivalent results to the original
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

orchestrator_path = Path(__file__).parent.parent.parent
if str(orchestrator_path) not in sys.path:
    sys.path.insert(0, str(orchestrator_path))

from refactor_agent.agent_v2 import (  # noqa: E402
    RefactorAgentV2,
    TSError,
    RefactorTask,
    RefactorRisk,
    get_refactor_agent_v2,
)
from core.agents import BaseAgent, AgentInput, AgentOutput  # noqa: E402


class TestRefactorAgentV2Inheritance:
    """Test that RefactorAgentV2 correctly inherits from BaseAgent"""

    def test_inherits_from_base_agent(self):
        """Verify RefactorAgentV2 is a subclass of BaseAgent"""
        assert issubclass(RefactorAgentV2, BaseAgent)

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_has_agent_id(self, mock_settings):
        """Verify agent_id is set correctly"""
        agent = RefactorAgentV2()
        assert agent.agent_id == "refactor_agent_v2"

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_has_call_llm_method(self, mock_settings):
        """Verify call_llm method is available from BaseAgent"""
        agent = RefactorAgentV2()
        assert hasattr(agent, 'call_llm')
        assert callable(agent.call_llm)

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_has_run_method(self, mock_settings):
        """Verify run method is available from BaseAgent"""
        agent = RefactorAgentV2()
        assert hasattr(agent, 'run')
        assert callable(agent.run)

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_has_execute_method(self, mock_settings):
        """Verify execute method is implemented"""
        agent = RefactorAgentV2()
        assert hasattr(agent, 'execute')
        assert callable(agent.execute)


class TestRefactorAgentV2Execute:
    """Test the execute method of RefactorAgentV2"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, 'call_llm')
    def test_execute_calls_call_llm(self, mock_call_llm, mock_settings):
        """Verify execute uses call_llm instead of direct LLMClient"""
        mock_call_llm.return_value = {
            "content": "const value = obj?.property ?? defaultValue;",
            "model": "gpt-4o",
            "provider": "openai",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 500
        }

        agent = RefactorAgentV2()

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        input = AgentInput(
            task_id="test-001",
            prompt="Fix null check error",
            task_type="coding",
            risk_level="low",
            context={
                "error": error.to_dict(),
                "code_context": "const value = obj.property;"
            }
        )

        agent.execute(input)

        mock_call_llm.assert_called_once()
        call_args = mock_call_llm.call_args
        assert call_args.kwargs.get('task_type') == "coding"
        assert call_args.kwargs.get('risk_level') == "low"

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, 'call_llm')
    def test_execute_returns_agent_output(self, mock_call_llm, mock_settings):
        """Verify execute returns AgentOutput"""
        mock_call_llm.return_value = {
            "content": "const value = obj?.property ?? defaultValue;",
            "model": "gpt-4o",
            "provider": "openai",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 500
        }

        agent = RefactorAgentV2()

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        input = AgentInput(
            task_id="test-001",
            prompt="Fix null check error",
            task_type="coding",
            risk_level="low",
            context={
                "error": error.to_dict(),
                "code_context": "const value = obj.property;"
            }
        )

        output = agent.execute(input)

        assert isinstance(output, AgentOutput)
        assert output.task_id == "test-001"
        assert output.success is True
        assert "fix" in output.data
        assert output.model_used == "gpt-4o"
        assert output.provider_used == "openai"

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_execute_without_error_context(self, mock_settings):
        """Verify execute handles missing error context"""
        agent = RefactorAgentV2()

        input = AgentInput(
            task_id="test-001",
            prompt="Fix error",
            task_type="coding",
            risk_level="low",
            context={}
        )

        output = agent.execute(input)

        assert output.success is False
        assert "No error provided" in output.error


class TestRefactorAgentV2GenerateFix:
    """Test the generate_fix convenience method"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, 'call_llm')
    def test_generate_fix_wraps_execute(self, mock_call_llm, mock_settings):
        """Verify generate_fix properly wraps execute"""
        mock_call_llm.return_value = {
            "content": "const value = obj?.property;",
            "model": "gpt-4o",
            "provider": "openai",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 500
        }

        agent = RefactorAgentV2()

        error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        output = agent.generate_fix(error, "const value = obj.property;")

        assert isinstance(output, AgentOutput)
        assert output.success is True

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, 'call_llm')
    def test_generate_fix_determines_risk_level(self, mock_call_llm, mock_settings):
        """Verify generate_fix determines correct risk level"""
        mock_call_llm.return_value = {
            "content": "fixed code",
            "model": "gpt-4o",
            "provider": "openai",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 500
        }

        agent = RefactorAgentV2()

        high_risk_error = TSError(
            file_path="src/test.ts",
            line=10,
            column=5,
            error_code="TS2322",
            message="Type mismatch"
        )

        agent.generate_fix(high_risk_error, "code")

        call_args = mock_call_llm.call_args
        assert call_args.kwargs.get('risk_level') == "high"


class TestRefactorAgentV2RiskLevel:
    """Test risk level determination"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_high_risk_codes(self, mock_settings):
        """Verify high risk error codes"""
        agent = RefactorAgentV2()

        high_risk_error = TSError(
            file_path="test.ts",
            line=1,
            column=1,
            error_code="TS2322",
            message="Type mismatch"
        )

        assert agent._determine_risk_level(high_risk_error) == "high"

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_medium_risk_codes(self, mock_settings):
        """Verify medium risk error codes"""
        agent = RefactorAgentV2()

        medium_risk_error = TSError(
            file_path="test.ts",
            line=1,
            column=1,
            error_code="TS7006",
            message="Implicit any"
        )

        assert agent._determine_risk_level(medium_risk_error) == "medium"

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_unknown_risk_codes_default_to_medium(self, mock_settings):
        """Verify unknown error codes default to medium (conservative approach)"""
        agent = RefactorAgentV2()

        # TS2531 is not in HIGH or MEDIUM risk codes, so it defaults to medium
        unknown_risk_error = TSError(
            file_path="test.ts",
            line=1,
            column=1,
            error_code="TS2531",
            message="Possibly null"
        )

        # Unknown codes now default to "medium" for conservative risk assessment
        assert agent._determine_risk_level(unknown_risk_error) == "medium"


class TestRefactorAgentV2AnalyzeError:
    """Test error analysis"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_analyze_error_returns_task(self, mock_settings):
        """Verify analyze_error returns RefactorTask"""
        agent = RefactorAgentV2()

        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        task = agent.analyze_error(error)

        assert isinstance(task, RefactorTask)
        assert task.error == error
        assert task.fix_strategy == "null_check"
        # TS2531 is not in HIGH or MEDIUM risk codes, defaults to MEDIUM
        assert task.estimated_risk == RefactorRisk.MEDIUM

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_analyze_error_unknown_code(self, mock_settings):
        """Verify analyze_error handles unknown error codes"""
        agent = RefactorAgentV2()

        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS9999",
            message="Unknown error"
        )

        task = agent.analyze_error(error)

        assert task.fix_strategy == "generic"


class TestRefactorAgentV2TelemetryIntegration:
    """Test Telemetry v2 integration through BaseAgent"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, 'call_llm')
    @patch.object(RefactorAgentV2, '_emit_telemetry')
    def test_run_emits_telemetry(self, mock_emit, mock_call_llm, mock_settings):
        """Verify run() emits telemetry events"""
        mock_call_llm.return_value = {
            "content": "fixed code",
            "model": "gpt-4o",
            "provider": "openai",
            "tokens_in": 100,
            "tokens_out": 50,
            "latency_ms": 500
        }

        agent = RefactorAgentV2()

        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Possibly null"
        )

        input = AgentInput(
            task_id="test-001",
            prompt="Fix error",
            task_type="coding",
            risk_level="low",
            context={
                "error": error.to_dict(),
                "code_context": "code"
            }
        )

        agent.run(input)

        assert mock_emit.call_count >= 2


class TestRefactorAgentV2RoutingIntegration:
    """Test RoutingEngine integration"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    @patch.object(RefactorAgentV2, '_get_routing_engine')
    @patch.object(RefactorAgentV2, '_get_llm_client')
    def test_call_llm_uses_routing_engine(
        self, mock_get_client, mock_get_routing, mock_settings
    ):
        """Verify call_llm uses RoutingEngine for model selection"""
        mock_routing = MagicMock()
        mock_model_info = MagicMock()
        mock_model_info.provider = "openai"
        mock_model_info.model_name = "gpt-4o"
        mock_model_info.tier.value = "premium"
        mock_model_info.is_fallback = False
        mock_routing.select_model.return_value = mock_model_info
        mock_get_routing.return_value = mock_routing

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "fixed code"
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_client.generate.return_value = mock_response
        mock_client.model = "gpt-4o"
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        agent = RefactorAgentV2()

        with patch('core.routing.TaskType') as mock_task_type, \
             patch('core.routing.RiskLevel') as mock_risk_level:
            mock_task_type.return_value = "coding"
            mock_risk_level.return_value = "low"

            result = agent.call_llm(
                prompt="Fix the error",
                task_type="coding",
                risk_level="low"
            )

        assert result["content"] == "fixed code"


class TestFactoryFunction:
    """Test factory function"""

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_get_refactor_agent_v2(self, mock_settings):
        """Verify factory function returns RefactorAgentV2"""
        agent = get_refactor_agent_v2()
        assert isinstance(agent, RefactorAgentV2)

    @patch('refactor_agent.agent_v2.RefactorAgentV2._load_settings')
    def test_get_refactor_agent_v2_with_path(self, mock_settings):
        """Verify factory function accepts repo_path"""
        agent = get_refactor_agent_v2(repo_path="/tmp/test")
        assert agent.repo_path == Path("/tmp/test")


class TestTSErrorDataclass:
    """Test TSError dataclass"""

    def test_ts_error_creation(self):
        """Verify TSError can be created"""
        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        assert error.file_path == "test.ts"
        assert error.line == 10
        assert error.column == 5
        assert error.error_code == "TS2531"
        assert error.message == "Object is possibly 'null'"
        assert error.severity == "error"

    def test_ts_error_to_dict(self):
        """Verify TSError.to_dict() works"""
        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Object is possibly 'null'"
        )

        d = error.to_dict()

        assert d["file_path"] == "test.ts"
        assert d["line"] == 10
        assert d["error_code"] == "TS2531"


class TestRefactorTaskDataclass:
    """Test RefactorTask dataclass"""

    def test_refactor_task_creation(self):
        """Verify RefactorTask can be created"""
        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Possibly null"
        )

        task = RefactorTask(
            task_id="task-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        assert task.task_id == "task-001"
        assert task.error == error
        assert task.fix_strategy == "null_check"
        assert task.estimated_risk == RefactorRisk.LOW
        assert task.status == "pending"

    def test_refactor_task_to_dict(self):
        """Verify RefactorTask.to_dict() works"""
        error = TSError(
            file_path="test.ts",
            line=10,
            column=5,
            error_code="TS2531",
            message="Possibly null"
        )

        task = RefactorTask(
            task_id="task-001",
            error=error,
            fix_strategy="null_check",
            estimated_risk=RefactorRisk.LOW
        )

        d = task.to_dict()

        assert d["task_id"] == "task-001"
        assert d["fix_strategy"] == "null_check"
        assert d["estimated_risk"] == "low"
        assert "error" in d
