"""
Smoke Tests for LangGraph Orchestrator

Phase 0-Lite Supplement: Basic smoke tests for LangGraph integration
Tests workflow creation and basic state management without external dependencies
"""
import pytest
from unittest.mock import patch

from orchestrator.langgraph_orchestrator import (
    AgentState,
    planner_node,
    finalizer_node,
    should_continue_execution,
    should_retry_or_finish,
    create_orchestrator_graph
)


class TestAgentState:
    """Test AgentState TypedDict structure"""

    def test_agent_state_structure(self):
        """Test AgentState can be created with required fields"""
        state: AgentState = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-trace-123",
            "repo": "RC918/morningai",
            "branch": "main",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        assert state["goal"] == "Test goal"
        assert state["trace_id"] == "test-trace-123"
        assert state["current_step"] == 0


class TestPlannerNode:
    """Test planner_node function"""

    @patch('common.config.settings.settings')
    def test_planner_node_static_mode(self, mock_settings):
        """Test planner node creates static plan when LLM planner disabled"""
        mock_settings.use_llm_planner = False

        state: AgentState = {
            "messages": [],
            "goal": "Generate FAQ",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = planner_node(state)

        assert len(result["plan"]) > 0
        assert result["planner_type"] == "static"
        assert result["current_step"] == 0
        assert len(result["messages"]) > 0

    @patch('llm_planner_adapter.generate_llm_plan')
    @patch('common.config.settings.settings')
    def test_planner_node_llm_mode(self, mock_settings, mock_generate_plan):
        """Test planner node uses LLM planner when enabled"""
        mock_settings.use_llm_planner = True
        mock_generate_plan.return_value = {
            "plan": ["Step 1", "Step 2", "Step 3"],
            "planner_type": "llm",
            "task_type": "bug_fix",
            "planning_time_ms": 150
        }

        state: AgentState = {
            "messages": [],
            "goal": "Fix bug in auth",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = planner_node(state)

        assert result["plan"] == ["Step 1", "Step 2", "Step 3"]
        assert result["planner_type"] == "llm"
        assert result["task_type"] == "bug_fix"
        assert result["planning_time_ms"] == 150


class TestFinalizerNode:
    """Test finalizer_node function"""

    def test_finalizer_node_success(self):
        """Test finalizer node creates success result"""
        state: AgentState = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "main",
            "plan": [],
            "current_step": 0,
            "pr_url": "https://github.com/RC918/morningai/pull/123",
            "pr_number": 123,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = finalizer_node(state)

        assert result["final_result"]["status"] == "success"
        assert result["final_result"]["pr_url"] == "https://github.com/RC918/morningai/pull/123"
        assert result["final_result"]["ci_state"] == "success"
        assert result["final_result"]["error"] is None

    def test_finalizer_node_error(self):
        """Test finalizer node creates error result"""
        state: AgentState = {
            "messages": [],
            "goal": "Test goal",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "main",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "error",
            "ci_checks": {},
            "error": "Test error message",
            "retry_count": 3,
            "final_result": {}
        }

        result = finalizer_node(state)

        assert result["final_result"]["status"] == "error"
        assert result["final_result"]["error"] == "Test error message"


class TestConditionalEdges:
    """Test conditional edge functions"""

    def test_should_continue_execution_with_error(self):
        """Test should_continue_execution returns finalize on max retries"""
        state: AgentState = {
            "messages": [],
            "goal": "Test",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": ["Step 1", "Step 2"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": "Test error",
            "retry_count": 3,
            "final_result": {}
        }

        result = should_continue_execution(state)
        assert result == "finalize"

    def test_should_continue_execution_next_step(self):
        """Test should_continue_execution continues to next step"""
        state: AgentState = {
            "messages": [],
            "goal": "Test",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": ["Step 1", "Step 2"],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "pending",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = should_continue_execution(state)
        assert result == "execute"

    def test_should_retry_or_finish_success(self):
        """Test should_retry_or_finish returns finalize on success"""
        state: AgentState = {
            "messages": [],
            "goal": "Test",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "success",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = should_retry_or_finish(state)
        assert result == "finalize"

    def test_should_retry_or_finish_failure(self):
        """Test should_retry_or_finish returns fix on failure"""
        state: AgentState = {
            "messages": [],
            "goal": "Test",
            "trace_id": "test-123",
            "repo": "RC918/morningai",
            "branch": "",
            "plan": [],
            "current_step": 0,
            "pr_url": "",
            "pr_number": 0,
            "ci_state": "failure",
            "ci_checks": {},
            "error": None,
            "retry_count": 0,
            "final_result": {}
        }

        result = should_retry_or_finish(state)
        assert result == "fix"


class TestCreateOrchestratorGraph:
    """Test create_orchestrator_graph function"""

    def test_create_orchestrator_graph(self):
        """Test orchestrator graph can be created"""
        graph = create_orchestrator_graph()

        assert graph is not None
        # Graph should be compiled and ready to use


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
