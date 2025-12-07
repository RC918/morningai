"""
Tests for ENABLE_FAILURE_LEARNING_CONTEXT feature flag (#1811)

Tests the failure learning context integration in the Planner node.
Verifies that the feature flag properly gates the learning context functionality.
"""
import pytest
from unittest.mock import patch

langgraph = pytest.importorskip("langgraph", reason="langgraph not installed")


class TestGetLearningContextForPlanner:
    """Tests for _get_learning_context_for_planner function."""

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_returns_context_when_enabled(self, mock_settings, mock_get_context):
        """Test that learning context is returned when flag is enabled."""
        mock_settings.enable_failure_learning_context = True
        mock_get_context.return_value = "## Past Experience\nCase 1: Similar error"

        from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

        result = _get_learning_context_for_planner("Fix authentication bug")

        assert result == "## Past Experience\nCase 1: Similar error"
        mock_get_context.assert_called_once_with(
            "Fix authentication bug",
            task_type=None,
            limit=3
        )

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_returns_empty_when_disabled(self, mock_settings, mock_get_context):
        """Test that empty string is returned when flag is disabled."""
        mock_settings.enable_failure_learning_context = False

        from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

        result = _get_learning_context_for_planner("Fix authentication bug")

        assert result == ""
        mock_get_context.assert_not_called()

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_passes_task_type_to_observer(self, mock_settings, mock_get_context):
        """Test that task_type is passed to get_learning_context."""
        mock_settings.enable_failure_learning_context = True
        mock_get_context.return_value = "Context with task type"

        from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

        result = _get_learning_context_for_planner(
            "Fix bug",
            task_type="bug_fix"
        )

        assert result == "Context with task type"
        mock_get_context.assert_called_once_with(
            "Fix bug",
            task_type="bug_fix",
            limit=3
        )

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_returns_empty_on_no_past_failures(self, mock_settings, mock_get_context):
        """Test that empty string is returned when no past failures found."""
        mock_settings.enable_failure_learning_context = True
        mock_get_context.return_value = ""

        from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

        result = _get_learning_context_for_planner("New unique task")

        assert result == ""

    @patch('common.config.settings.settings')
    def test_handles_import_error_gracefully(self, mock_settings):
        """Test that ImportError is handled gracefully."""
        mock_settings.enable_failure_learning_context = True

        with patch.dict('sys.modules', {'observer_node': None}):
            from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

            result = _get_learning_context_for_planner("Test goal")

            assert result == ""

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_handles_exception_gracefully(self, mock_settings, mock_get_context):
        """Test that exceptions are handled gracefully."""
        mock_settings.enable_failure_learning_context = True
        mock_get_context.side_effect = Exception("Database connection failed")

        from orchestrator.langgraph_orchestrator import _get_learning_context_for_planner

        result = _get_learning_context_for_planner("Test goal")

        assert result == ""


class TestPlannerNodeWithLearningContext:
    """Tests for planner_node with learning context integration."""

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_planner_includes_learning_context_when_enabled(
        self, mock_settings, mock_get_context
    ):
        """Test that planner includes learning context in state when enabled."""
        mock_settings.enable_failure_learning_context = True
        mock_settings.use_llm_planner = False
        mock_get_context.return_value = "## Past Experience\nCase 1: Auth fix"

        from orchestrator.langgraph_orchestrator import planner_node, AgentState

        state: AgentState = {
            "messages": [],
            "goal": "Fix authentication",
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

        assert "learning_context" in result
        assert result["learning_context"] == "## Past Experience\nCase 1: Auth fix"

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_planner_skips_learning_context_when_disabled(
        self, mock_settings, mock_get_context
    ):
        """Test that planner skips learning context when flag is disabled."""
        mock_settings.enable_failure_learning_context = False
        mock_settings.use_llm_planner = False

        from orchestrator.langgraph_orchestrator import planner_node, AgentState

        state: AgentState = {
            "messages": [],
            "goal": "Fix authentication",
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

        assert result.get("learning_context") is None or result.get("learning_context") == ""
        mock_get_context.assert_not_called()

    @patch('observer_node.get_learning_context')
    @patch('common.config.settings.settings')
    def test_planner_continues_without_learning_context_on_error(
        self, mock_settings, mock_get_context
    ):
        """Test that planner continues even if learning context fails."""
        mock_settings.enable_failure_learning_context = True
        mock_settings.use_llm_planner = False
        mock_get_context.side_effect = Exception("pgvector unavailable")

        from orchestrator.langgraph_orchestrator import planner_node, AgentState

        state: AgentState = {
            "messages": [],
            "goal": "Fix bug",
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


class TestFeatureFlagConfiguration:
    """Tests for ENABLE_FAILURE_LEARNING_CONTEXT configuration."""

    def test_flag_exists_in_settings(self):
        """Test that the feature flag is defined in settings."""
        from common.config.settings import Settings

        settings_fields = Settings.model_fields
        assert "enable_failure_learning_context" in settings_fields

    def test_flag_has_correct_default(self):
        """Test that the feature flag has the correct default value."""
        from common.config.settings import Settings

        field = Settings.model_fields["enable_failure_learning_context"]
        assert field.default is True

    def test_flag_has_correct_alias(self):
        """Test that the feature flag has the correct environment variable alias."""
        from common.config.settings import Settings

        field = Settings.model_fields["enable_failure_learning_context"]
        assert field.alias == "ENABLE_FAILURE_LEARNING_CONTEXT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
