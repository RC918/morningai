#!/usr/bin/env python3
"""
SeniorCoder LangGraph Integration Tests

D-2b: Tests for SeniorCoder integration into LangGraph orchestrator.

Tests cover:
1. Feature flag gating (ENABLE_SENIOR_CODER)
2. SeniorCoder planning phase (_attempt_senior_coder_plan)
3. SeniorCoder review phase (_attempt_senior_coder_review)
4. Integration with _attempt_general_coder_fix
5. Fallback behavior when SeniorCoder is disabled or fails
"""
import sys
from unittest.mock import MagicMock, patch
from types import ModuleType


def setup_fake_modules():
    """Set up fake modules to avoid ImportError in tests."""
    if "langgraph" not in sys.modules:
        langgraph = ModuleType("langgraph")
        sys.modules["langgraph"] = langgraph

    if "langgraph.graph" not in sys.modules:
        langgraph_graph = ModuleType("langgraph.graph")
        langgraph_graph.StateGraph = MagicMock()
        langgraph_graph.END = "END"
        sys.modules["langgraph.graph"] = langgraph_graph
        sys.modules["langgraph"].graph = langgraph_graph

    if "langgraph.checkpoint" not in sys.modules:
        langgraph_checkpoint = ModuleType("langgraph.checkpoint")
        sys.modules["langgraph.checkpoint"] = langgraph_checkpoint
        sys.modules["langgraph"].checkpoint = langgraph_checkpoint

    if "langgraph.checkpoint.postgres" not in sys.modules:
        langgraph_checkpoint_postgres = ModuleType("langgraph.checkpoint.postgres")
        langgraph_checkpoint_postgres.PostgresSaver = MagicMock()
        sys.modules["langgraph.checkpoint.postgres"] = langgraph_checkpoint_postgres

    if "langgraph.checkpoint.memory" not in sys.modules:
        langgraph_checkpoint_memory = ModuleType("langgraph.checkpoint.memory")
        langgraph_checkpoint_memory.MemorySaver = MagicMock()
        sys.modules["langgraph.checkpoint.memory"] = langgraph_checkpoint_memory

    if "langgraph.types" not in sys.modules:
        langgraph_types = ModuleType("langgraph.types")
        langgraph_types.interrupt = MagicMock(return_value={"approved": True})
        sys.modules["langgraph.types"] = langgraph_types
        sys.modules["langgraph"].types = langgraph_types

    if "common" not in sys.modules:
        common = ModuleType("common")
        sys.modules["common"] = common

    if "common.agents" not in sys.modules:
        common_agents = ModuleType("common.agents")
        sys.modules["common.agents"] = common_agents
        sys.modules["common"].agents = common_agents

    if "common.agents.base_agent" not in sys.modules:
        base_agent = ModuleType("common.agents.base_agent")

        class FakeAgentInput:
            def __init__(self, task_id="", prompt="", context=None):
                self.task_id = task_id
                self.prompt = prompt
                self.context = context or {}

        base_agent.AgentInput = FakeAgentInput
        sys.modules["common.agents.base_agent"] = base_agent
        sys.modules["common.agents"].base_agent = base_agent


setup_fake_modules()

from langgraph_orchestrator import (
    _attempt_senior_coder_plan,
    _attempt_senior_coder_review,
    should_proceed_after_fixer,
    should_proceed_after_hitl_gate,
)


class TestSeniorCoderPlanFeatureFlag:
    """Tests for SeniorCoder planning feature flag gating."""

    def test_plan_disabled_by_default(self):
        """Test that SeniorCoder plan is skipped when feature flag is False."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = False

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[{"path": "test.py", "content": "x = 1"}],
                trace_id="test-trace-123"
            )

            assert should_proceed is True
            assert spec_dict is None
            assert "disabled" in message.lower()

    @patch("coder.senior_coder.get_senior_coder")
    def test_plan_enabled_creates_spec(self, mock_get_coder):
        """Test that SeniorCoder creates spec when enabled."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = True
            mock_spec.abort_reason = None
            mock_spec.to_dict.return_value = {
                "task_analysis": {"complexity": "simple"},
                "implementation_plan": [{"step": 1}]
            }

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[{"path": "test.py", "content": "x = 1"}],
                trace_id="test-trace-123"
            )

            assert should_proceed is True
            assert spec_dict is not None
            assert spec_dict["task_analysis"]["complexity"] == "simple"
            assert "1 steps" in message


class TestSeniorCoderPlanAbort:
    """Tests for SeniorCoder planning abort scenarios."""

    @patch("coder.senior_coder.get_senior_coder")
    def test_plan_aborts_on_complex_task(self, mock_get_coder):
        """Test that SeniorCoder aborts on complex tasks."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "Task complexity too high"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Implement OAuth2",
                files_with_content=[],
                trace_id="test-trace-123"
            )

            assert should_proceed is False
            assert spec_dict is None
            assert "aborted" in message.lower()

    @patch("coder.senior_coder.get_senior_coder")
    def test_plan_handles_llm_error(self, mock_get_coder):
        """Test that SeniorCoder handles LLM errors gracefully."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.side_effect = Exception("LLM unavailable")
            mock_get_coder.return_value = mock_coder

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123"
            )

            assert should_proceed is True
            assert spec_dict is None
            assert "failed" in message.lower()


class TestSeniorCoderReviewFeatureFlag:
    """Tests for SeniorCoder review feature flag gating."""

    def test_review_disabled_by_default(self):
        """Test that SeniorCoder review is skipped when feature flag is False."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = False

            approved, message = _attempt_senior_coder_review(
                task_description="Fix the issue",
                spec_dict={"task_analysis": {"complexity": "simple"}},
                patches=[{"file_path": "test.py", "patch": "x = 2"}],
                trace_id="test-trace-123"
            )

            assert approved is True
            assert "disabled" in message.lower()

    def test_review_skipped_without_spec(self):
        """Test that SeniorCoder review is skipped when no spec available."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            approved, message = _attempt_senior_coder_review(
                task_description="Fix the issue",
                spec_dict=None,
                patches=[{"file_path": "test.py", "patch": "x = 2"}],
                trace_id="test-trace-123"
            )

            assert approved is True
            assert "no spec" in message.lower()


class TestSeniorCoderReviewExecution:
    """Tests for SeniorCoder review execution."""

    @patch("coder.senior_coder.get_senior_coder")
    def test_review_approves_good_implementation(self, mock_get_coder):
        """Test that SeniorCoder approves good implementation."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_result = MagicMock()
            mock_result.approved = True
            mock_result.feedback = "Implementation looks good"
            mock_result.required_changes = []

            mock_coder = MagicMock()
            mock_coder.review_implementation.return_value = mock_result
            mock_get_coder.return_value = mock_coder

            approved, message = _attempt_senior_coder_review(
                task_description="Fix the issue",
                spec_dict={"task_analysis": {"complexity": "simple"}},
                patches=[{"file_path": "test.py", "patch": "x = 2", "syntax_valid": True}],
                trace_id="test-trace-123"
            )

            assert approved is True
            assert "approved" in message.lower()

    @patch("coder.senior_coder.get_senior_coder")
    def test_review_rejects_bad_implementation(self, mock_get_coder):
        """Test that SeniorCoder rejects bad implementation."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_result = MagicMock()
            mock_result.approved = False
            mock_result.feedback = "Missing error handling"
            mock_result.required_changes = ["Add try/except block"]

            mock_coder = MagicMock()
            mock_coder.review_implementation.return_value = mock_result
            mock_get_coder.return_value = mock_coder

            approved, message = _attempt_senior_coder_review(
                task_description="Fix the issue",
                spec_dict={"task_analysis": {"complexity": "simple"}},
                patches=[{"file_path": "test.py", "patch": "x = 2"}],
                trace_id="test-trace-123"
            )

            assert approved is False
            assert "rejected" in message.lower()

    @patch("coder.senior_coder.get_senior_coder")
    def test_review_handles_llm_error(self, mock_get_coder):
        """Test that SeniorCoder review handles LLM errors gracefully."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_coder = MagicMock()
            mock_coder.review_implementation.side_effect = Exception("LLM unavailable")
            mock_get_coder.return_value = mock_coder

            approved, message = _attempt_senior_coder_review(
                task_description="Fix the issue",
                spec_dict={"task_analysis": {"complexity": "simple"}},
                patches=[{"file_path": "test.py", "patch": "x = 2"}],
                trace_id="test-trace-123"
            )

            assert approved is True
            assert "failed" in message.lower()


class TestSeniorCoderEventCodes:
    """Tests for SeniorCoder event code logging."""

    def test_plan_disabled_event_code(self, caplog):
        """Test SENIOR_CODER_DISABLED event code is logged."""
        import logging
        caplog.set_level(logging.DEBUG)

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = False

            _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123"
            )

            assert any("SENIOR_CODER_DISABLED" in record.message for record in caplog.records)

    @patch("coder.senior_coder.get_senior_coder")
    def test_plan_created_event_code(self, mock_get_coder, caplog):
        """Test SENIOR_CODER_PLAN_CREATED event code is logged."""
        import logging
        caplog.set_level(logging.INFO)

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = True
            mock_spec.abort_reason = None
            mock_spec.to_dict.return_value = {
                "task_analysis": {"complexity": "simple"},
                "implementation_plan": []
            }

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123"
            )

            assert any("SENIOR_CODER_PLAN_CREATED" in record.message for record in caplog.records)

    @patch("coder.senior_coder.get_senior_coder")
    def test_plan_aborted_event_code(self, mock_get_coder, caplog):
        """Test SENIOR_CODER_PLAN_ABORTED event code is logged."""
        import logging
        caplog.set_level(logging.INFO)

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "Too complex"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123"
            )

            assert any("SENIOR_CODER_PLAN_ABORTED" in record.message for record in caplog.records)


class TestSeniorCoderHITLGate:
    """
    Tests for EPIC D Issue #3487: SeniorCoder HITL Gate.

    Tests cover:
    1. HITL flags being set on complexity abort
    2. HITL flags NOT being set on system errors
    3. HITL escalation event code logging
    """

    @patch("coder.senior_coder.get_senior_coder")
    def test_complexity_abort_sets_hitl_flags(self, mock_get_coder):
        """Test that complexity abort sets HITL flags on state."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "Task complexity too high for automated fix"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            # Create a state dict to pass
            state = {"trace_id": "test-trace-123"}

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Implement complex feature",
                files_with_content=[{"path": "test.py", "content": "x = 1"}],
                trace_id="test-trace-123",
                state=state
            )

            assert should_proceed is False
            assert state.get("requires_hitl_approval") is True
            assert state.get("hitl_approved") is False
            assert state.get("hitl_reason") == "senior_coder_complexity_abort"
            assert "abort_reason" in state.get("hitl_details", {})

    @patch("coder.senior_coder.get_senior_coder")
    def test_system_error_does_not_set_hitl_flags(self, mock_get_coder):
        """Test that system errors (JSON parsing, LLM failures) do NOT set HITL flags."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "JSON parsing failed: invalid response"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            state = {"trace_id": "test-trace-123"}

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123",
                state=state
            )

            assert should_proceed is False
            # HITL flags should NOT be set for system errors
            assert state.get("requires_hitl_approval") is not True

    @patch("coder.senior_coder.get_senior_coder")
    def test_llm_call_failed_does_not_set_hitl_flags(self, mock_get_coder):
        """Test that LLM call failures do NOT set HITL flags."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "LLM call failed during planning phase"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            state = {"trace_id": "test-trace-123"}

            should_proceed, spec_dict, message = _attempt_senior_coder_plan(
                task_description="Fix the issue",
                files_with_content=[],
                trace_id="test-trace-123",
                state=state
            )

            assert should_proceed is False
            assert state.get("requires_hitl_approval") is not True

    @patch("coder.senior_coder.get_senior_coder")
    def test_hitl_escalation_event_code(self, mock_get_coder, caplog):
        """Test SENIOR_CODER_HITL_ESCALATION event code is logged."""
        import logging
        caplog.set_level(logging.INFO)

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_senior_coder = True

            mock_spec = MagicMock()
            mock_spec.should_proceed = False
            mock_spec.abort_reason = "Task complexity too high"

            mock_coder = MagicMock()
            mock_coder.analyze_and_plan.return_value = mock_spec
            mock_get_coder.return_value = mock_coder

            state = {"trace_id": "test-trace-123"}

            _attempt_senior_coder_plan(
                task_description="Implement complex feature",
                files_with_content=[],
                trace_id="test-trace-123",
                state=state
            )

            assert any("SENIOR_CODER_HITL_ESCALATION" in record.message for record in caplog.records)


class TestShouldProceedAfterFixer:
    """
    Tests for should_proceed_after_fixer routing function.

    EPIC D Issue #3487: SeniorCoder HITL Gate
    """

    def test_routes_to_hitl_gate_when_approval_required(self):
        """Test routing to hitl_gate when HITL approval is required."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "requires_hitl_approval": True,
                "hitl_approved": False,
                "hitl_reason": "senior_coder_complexity_abort"
            }

            result = should_proceed_after_fixer(state)

            assert result == "hitl_gate"

    def test_routes_to_executor_when_no_approval_required(self):
        """Test routing to executor when no HITL approval is required."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "requires_hitl_approval": False,
                "hitl_approved": False
            }

            result = should_proceed_after_fixer(state)

            assert result == "executor"

    def test_routes_to_executor_when_already_approved(self):
        """Test routing to executor when HITL is already approved."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "requires_hitl_approval": True,
                "hitl_approved": True,
                "hitl_reason": "senior_coder_complexity_abort"
            }

            result = should_proceed_after_fixer(state)

            assert result == "executor"


class TestShouldProceedAfterHITLGateExtended:
    """
    Tests for extended should_proceed_after_hitl_gate routing function.

    EPIC D Issue #3487: SeniorCoder HITL Gate
    Tests the new executor routing for SeniorCoder complexity abort approval.
    """

    def test_routes_to_executor_after_complexity_abort_approval(self):
        """Test routing to executor after SeniorCoder complexity abort is approved."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "hitl_reason": "senior_coder_complexity_abort",
                "hitl_approved": True,
                "merge_decision": "needs_fix",
                "retry_count": 0
            }

            result = should_proceed_after_hitl_gate(state)

            assert result == "executor"

    def test_routes_to_fix_for_normal_hitl_approval(self):
        """Test routing to fix for normal HITL approval (not complexity abort)."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "hitl_reason": "other_reason",
                "hitl_approved": True,
                "merge_decision": "needs_fix",
                "retry_count": 0
            }

            result = should_proceed_after_hitl_gate(state)

            assert result == "fix"

    def test_routes_to_finalize_when_approved(self):
        """Test routing to finalize when merge_decision is approved."""
        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            state = {
                "trace_id": "test-trace-123",
                "hitl_reason": "",
                "hitl_approved": True,
                "merge_decision": "approved",
                "retry_count": 0
            }

            result = should_proceed_after_hitl_gate(state)

            assert result == "finalize"
