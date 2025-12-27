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
    create_orchestrator_graph,
    _create_base_initial_state,
    _get_workflow_config,
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


class TestCreateBaseInitialState:
    """
    Test _create_base_initial_state helper function.

    Issue #2260: Extract common initial_state initialization helper
    """

    def test_create_base_initial_state_default(self):
        """Test helper creates state with default task_type"""
        state = _create_base_initial_state(
            goal="Test goal",
            trace_id="test-trace-123",
            repo="RC918/morningai",
        )

        assert state["goal"] == "Test goal"
        assert state["trace_id"] == "test-trace-123"
        assert state["repo"] == "RC918/morningai"
        assert state["branch"] == ""
        assert state["task_type"] == "default"
        assert state["current_step"] == 0
        assert state["ci_state"] == "pending"
        assert state["code_quality_score"] == 100
        assert state["security_is_safe"] is True
        assert state["governance_is_compliant"] is True
        assert state["policy_blocked"] is False
        assert len(state["messages"]) == 1

    def test_create_base_initial_state_with_branch(self):
        """Test helper creates state with custom branch"""
        state = _create_base_initial_state(
            goal="Fix bug",
            trace_id="test-456",
            repo="RC918/morningai",
            branch="feature/test-branch",
        )

        assert state["branch"] == "feature/test-branch"
        assert state["goal"] == "Fix bug"

    def test_create_base_initial_state_review_follow_up(self):
        """Test helper creates state for review_follow_up task type"""
        state = _create_base_initial_state(
            goal="Address review comment",
            trace_id="test-789",
            repo="RC918/morningai",
            branch="fix/review-comment",
            task_type="review_follow_up",
        )

        assert state["task_type"] == "review_follow_up"
        assert state["branch"] == "fix/review-comment"
        assert state["original_pr_number"] == 0
        assert state["comment_url"] == ""
        assert state["requires_hitl_approval"] is False

    def test_create_base_initial_state_internal_review(self):
        """Test helper creates state for internal_review task type"""
        state = _create_base_initial_state(
            goal="Re-review AI assessment",
            trace_id="test-internal-123",
            repo="RC918/morningai",
            task_type="internal_review",
        )

        assert state["task_type"] == "internal_review"
        assert state["ci_state"] == "pending"
        assert state["code_quality_score"] == 100

    def test_create_base_initial_state_all_fields_present(self):
        """Test helper creates state with all required AgentState fields"""
        state = _create_base_initial_state(
            goal="Test all fields",
            trace_id="test-all",
            repo="RC918/morningai",
        )

        required_fields = [
            "messages", "goal", "trace_id", "repo", "branch",
            "plan", "current_step", "pr_url", "pr_number",
            "ci_state", "ci_checks", "error", "retry_count", "final_result",
            "review_result", "review_comments", "review_severity",
            "merge_decision", "code_quality_score",
            "security_advisory", "security_risk", "security_findings", "security_is_safe",
            "governance_advisory", "governance_risk", "governance_findings", "governance_is_compliant",
            "cost_advisory", "cost_risk", "cost_within_budget",
            "permission_advisory", "permission_risk", "permission_granted",
            "reputation_advisory", "reputation_score", "reputation_level",
            "policy_blocked", "policy_block_reason",
            "evaluation_result", "evaluation_health_status", "evaluation_has_regression",
            "pm_advisory", "pm_sub_tasks", "pm_confidence_score", "pm_risk",
            "ops_advisory", "ops_health_status", "ops_risk", "ops_recommended_actions",
            "task_type", "original_pr_number", "comment_url", "comment_body",
            "review_file_path", "review_line_number", "triage_result", "pr_context",
            "review_follow_up_action", "requires_hitl_approval",
        ]

        for field in required_fields:
            assert field in state, f"Missing field: {field}"

    def test_create_base_initial_state_can_be_updated(self):
        """Test helper state can be updated with task-specific fields"""
        state = _create_base_initial_state(
            goal="Test update",
            trace_id="test-update",
            repo="RC918/morningai",
            task_type="review_follow_up",
        )

        state.update({
            "original_pr_number": 123,
            "comment_url": "https://github.com/RC918/morningai/pull/123#comment-1",
            "comment_body": "Please fix this issue",
        })

        assert state["original_pr_number"] == 123
        assert state["comment_url"] == "https://github.com/RC918/morningai/pull/123#comment-1"
        assert state["comment_body"] == "Please fix this issue"
        assert state["task_type"] == "review_follow_up"


class TestGetWorkflowConfig:
    """
    Test _get_workflow_config helper function.

    Issue: P0 DB Optimization - Step Cap protection
    Blueprint: Flow Controller v3 Fail-Fast Recovery

    This helper centralizes workflow configuration to ensure consistent
    recursion_limit across all orchestrator entry points.
    """

    @patch('orchestrator.langgraph_orchestrator.settings')
    def test_get_workflow_config_includes_recursion_limit(self, mock_settings):
        """Test helper returns config with recursion_limit from settings"""
        mock_settings.orchestrator_recursion_limit = 30

        config = _get_workflow_config("test-trace-123")

        assert "recursion_limit" in config
        assert config["recursion_limit"] == 30

    @patch('orchestrator.langgraph_orchestrator.settings')
    def test_get_workflow_config_includes_thread_id(self, mock_settings):
        """Test helper returns config with thread_id in configurable"""
        mock_settings.orchestrator_recursion_limit = 30

        config = _get_workflow_config("my-unique-trace-id")

        assert "configurable" in config
        assert config["configurable"]["thread_id"] == "my-unique-trace-id"

    @patch('orchestrator.langgraph_orchestrator.settings')
    def test_get_workflow_config_custom_limit(self, mock_settings):
        """Test helper respects custom recursion_limit from settings"""
        mock_settings.orchestrator_recursion_limit = 50

        config = _get_workflow_config("test-trace")

        assert config["recursion_limit"] == 50

    @patch('orchestrator.langgraph_orchestrator.settings')
    def test_get_workflow_config_structure(self, mock_settings):
        """Test helper returns correct config structure for LangGraph invoke"""
        mock_settings.orchestrator_recursion_limit = 30

        config = _get_workflow_config("trace-id-123")

        # Verify structure matches what LangGraph expects
        assert isinstance(config, dict)
        assert isinstance(config.get("configurable"), dict)
        assert isinstance(config.get("recursion_limit"), int)
        # Verify no extra keys that could cause issues
        assert set(config.keys()) == {"configurable", "recursion_limit"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
