"""
Tests for Observer Node - Phase 2 Brain Layer (#1811)

Tests the failure observation and learning context functionality.
"""

import sys
from unittest.mock import patch, MagicMock

import pytest

# Check if Knowledge Graph module is available for tests that require it
KG_MODULE_PATH = "agents.dev_agent.knowledge_graph.knowledge_graph_manager"
try:
    import importlib
    KG_MODULE = importlib.import_module(KG_MODULE_PATH)
    KG_AVAILABLE = True
except ImportError:
    KG_MODULE = None
    KG_AVAILABLE = False


class TestObserverNodeConstants:
    """Tests for Observer Node named constants (#1839)."""

    def test_constants_are_exported(self):
        """Test that all named constants are exported and have expected values."""
        from observer_node import (
            MAX_FIXER_RETRIES,
            DEFAULT_SIMILARITY_THRESHOLD,
            DEFAULT_QUERY_LIMIT,
            MAX_GOAL_CHARS,
            MAX_ERROR_CHARS,
            MAX_CONTEXT_SNIPPET_CHARS,
        )

        assert MAX_FIXER_RETRIES == 3
        assert DEFAULT_SIMILARITY_THRESHOLD == 0.6
        assert DEFAULT_QUERY_LIMIT == 3
        assert MAX_GOAL_CHARS == 200
        assert MAX_ERROR_CHARS == 500
        assert MAX_CONTEXT_SNIPPET_CHARS == 200

    def test_truncation_constants_are_positive(self):
        """Test that truncation constants are positive integers."""
        from observer_node import (
            MAX_GOAL_CHARS,
            MAX_ERROR_CHARS,
            MAX_CONTEXT_SNIPPET_CHARS,
        )

        assert MAX_GOAL_CHARS > 0
        assert MAX_ERROR_CHARS > 0
        assert MAX_CONTEXT_SNIPPET_CHARS > 0


mock_supabase = MagicMock()
mock_openai = MagicMock()
sys.modules['supabase'] = mock_supabase
sys.modules['openai'] = mock_openai

import memory.error_fix_pairs  # noqa: E402,F401 - needed for mocking


class TestGenerateFailureSummary:
    """Tests for _generate_failure_summary function."""

    def test_basic_summary(self):
        """Test basic failure summary generation."""
        from observer_node import _generate_failure_summary

        state = {
            "goal": "Fix the bug in the login page",
            "task_type": "bug_fix",
            "error": "TypeError: Cannot read property 'user' of undefined",
            "ci_state": "failure",
            "retry_count": 2,
        }

        summary = _generate_failure_summary(state)

        assert "Goal: Fix the bug in the login page" in summary
        assert "Task Type: bug_fix" in summary
        assert "Error: TypeError" in summary
        assert "CI State: failure" in summary
        assert "Fixer Retries: 2" in summary

    def test_summary_with_security_risk(self):
        """Test summary includes security risk when not info."""
        from observer_node import _generate_failure_summary

        state = {
            "goal": "Deploy to production",
            "task_type": "deployment",
            "error": "Permission denied",
            "security_risk": "high",
            "governance_risk": "medium",
        }

        summary = _generate_failure_summary(state)

        assert "Security Risk: high" in summary
        assert "Governance Risk: medium" in summary

    def test_summary_truncates_long_goal(self):
        """Test that long goals are truncated."""
        from observer_node import _generate_failure_summary

        long_goal = "A" * 500
        state = {"goal": long_goal, "task_type": "test"}

        summary = _generate_failure_summary(state)

        assert len(summary.split("\n")[0]) <= 210


class TestCategorizeError:
    """Tests for _categorize_error function."""

    def test_timeout_error(self):
        """Test timeout error categorization."""
        from observer_node import _categorize_error

        state = {"error": "Request timeout after 30 seconds"}
        assert _categorize_error(state) == "timeout"

    def test_rate_limit_error(self):
        """Test rate limit error categorization."""
        from observer_node import _categorize_error

        state = {"error": "Rate limit exceeded"}
        assert _categorize_error(state) == "rate_limit"

    def test_ci_failure(self):
        """Test CI failure categorization."""
        from observer_node import _categorize_error

        state = {"error": "", "ci_state": "failure"}
        assert _categorize_error(state) == "ci_failure"

    def test_max_retries_exceeded(self):
        """Test max retries exceeded categorization."""
        from observer_node import _categorize_error

        state = {"error": "", "ci_state": "pending", "retry_count": 3}
        assert _categorize_error(state) == "max_retries_exceeded"

    def test_review_rejection(self):
        """Test review rejection categorization."""
        from observer_node import _categorize_error

        state = {"error": "", "merge_decision": "request_changes"}
        assert _categorize_error(state) == "review_rejection"

    def test_unknown_error(self):
        """Test unknown error categorization."""
        from observer_node import _categorize_error

        state = {"error": "Something went wrong"}
        assert _categorize_error(state) == "unknown"


class TestObserveFailure:
    """Tests for observe_failure function."""

    def test_observe_failure_without_pgvector(self):
        """Test observe_failure when pgvector save is disabled."""
        from observer_node import observe_failure

        state = {
            "trace_id": "test-trace-123",
            "goal": "Test goal",
            "task_type": "test",
            "error": "Test error",
            "ci_state": "failure",
            "retry_count": 1,
        }

        result = observe_failure(state, save_to_pgvector=False)

        assert result["trace_id"] == "test-trace-123"
        assert result["error_type"] == "ci_failure"
        assert "summary" in result
        assert result["saved_to_pgvector"] is False
        assert result["pair_id"] is None

    @patch("memory.error_fix_pairs.save_error_fix_pair")
    def test_observe_failure_with_pgvector_success(self, mock_save):
        """Test observe_failure when pgvector save succeeds."""
        mock_save.return_value = 42

        from observer_node import observe_failure

        state = {
            "trace_id": "test-trace-456",
            "goal": "Test goal",
            "task_type": "test",
            "error": "Test error",
        }

        result = observe_failure(state, save_to_pgvector=True)

        assert result["saved_to_pgvector"] is True
        assert result["pair_id"] == 42
        mock_save.assert_called_once()

    @patch("memory.error_fix_pairs.save_error_fix_pair")
    def test_observe_failure_with_pgvector_failure(self, mock_save):
        """Test observe_failure when pgvector save fails."""
        mock_save.return_value = None

        from observer_node import observe_failure

        state = {
            "trace_id": "test-trace-789",
            "goal": "Test goal",
            "error": "Test error",
        }

        result = observe_failure(state, save_to_pgvector=True)

        assert result["saved_to_pgvector"] is False
        assert result["pair_id"] is None


class TestQueryPastFailures:
    """Tests for query_past_failures function."""

    @patch("memory.error_fix_pairs.find_similar_errors")
    def test_query_past_failures_success(self, mock_find):
        """Test query_past_failures returns formatted results."""
        mock_pair = MagicMock()
        mock_pair.id = 1
        mock_pair.error_text = "Test error"
        mock_pair.fix_text = "Test fix"
        mock_pair.error_type = "ci_failure"
        mock_pair.similarity = 0.85
        mock_pair.confidence_score = 0.9
        mock_pair.success_count = 5
        mock_pair.failure_count = 1

        mock_find.return_value = [mock_pair]

        from observer_node import query_past_failures

        results = query_past_failures("Similar error", limit=3)

        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["error_text"] == "Test error"
        assert results[0]["similarity"] == 0.85

    @patch("memory.error_fix_pairs.find_similar_errors")
    def test_query_past_failures_empty(self, mock_find):
        """Test query_past_failures returns empty list when no matches."""
        mock_find.return_value = []

        from observer_node import query_past_failures

        results = query_past_failures("No matching error")

        assert results == []


class TestGetLearningContext:
    """Tests for get_learning_context function."""

    @patch("observer_node.query_past_failures")
    def test_get_learning_context_with_failures(self, mock_query):
        """Test get_learning_context formats past failures."""
        mock_query.return_value = [
            {
                "id": 1,
                "error_text": "Connection timeout",
                "fix_text": "Increase timeout to 60s",
                "error_type": "timeout",
                "similarity": 0.8,
                "confidence_score": 0.9,
            }
        ]

        from observer_node import get_learning_context

        context = get_learning_context("Connection error")

        assert "Past Experience" in context
        assert "Case 1" in context
        assert "timeout" in context
        assert "0.80" in context

    @patch("observer_node.query_past_failures")
    def test_get_learning_context_empty(self, mock_query):
        """Test get_learning_context returns empty string when no failures."""
        mock_query.return_value = []

        from observer_node import get_learning_context

        context = get_learning_context("New error")

        assert context == ""

    @patch("observer_node.query_past_failures")
    def test_get_learning_context_skips_pending_fixes(self, mock_query):
        """Test get_learning_context skips pending fixes."""
        mock_query.return_value = [
            {
                "id": 1,
                "error_text": "Test error",
                "fix_text": "[PENDING] Failure recorded",
                "error_type": "unknown",
                "similarity": 0.7,
                "confidence_score": 0.5,
            }
        ]

        from observer_node import get_learning_context

        context = get_learning_context("Test error")

        assert "Fix:" not in context


class TestExtractErrorContext:
    """Tests for _extract_error_context function."""

    def test_extract_error_context(self):
        """Test error context extraction."""
        from observer_node import _extract_error_context

        state = {
            "trace_id": "test-123",
            "task_type": "bug_fix",
            "ci_state": "failure",
            "ci_checks": {"lint": "failed"},
            "retry_count": 2,
            "merge_decision": "needs_fix",
            "security_risk": "low",
            "governance_risk": "info",
            "review_severity": "medium",
            "code_quality_score": 75,
            "planner_type": "llm",
            "pr_url": "https://github.com/test/pr/1",
            "repo": "test/repo",
        }

        context = _extract_error_context(state)

        assert context["trace_id"] == "test-123"
        assert context["task_type"] == "bug_fix"
        assert context["ci_state"] == "failure"
        assert context["retry_count"] == 2
        assert context["security_risk"] == "low"
        assert context["code_quality_score"] == 75


class TestUpdateFixForFailure:
    """Tests for update_fix_for_failure function."""

    @patch("memory.error_fix_pairs._get_supabase_client")
    @patch("memory.error_fix_pairs.update_pair_feedback")
    @patch("memory.error_fix_pairs._embed")
    def test_update_fix_success(self, mock_embed, mock_feedback, mock_client):
        """Test update_fix_for_failure succeeds."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"id": 42}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_embed.return_value = [0.1] * 1536
        mock_feedback.return_value = 0.9

        from observer_node import update_fix_for_failure

        result = update_fix_for_failure("test-trace", "Fixed the bug", was_successful=True)

        assert result is True
        mock_feedback.assert_called_once_with(42, was_successful=True)

    @patch("memory.error_fix_pairs._get_supabase_client")
    def test_update_fix_no_pair_found(self, mock_client):
        """Test update_fix_for_failure when no pair found."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

        from observer_node import update_fix_for_failure

        result = update_fix_for_failure("nonexistent-trace", "Fix")

        assert result is False

    @patch("memory.error_fix_pairs._get_supabase_client")
    def test_update_fix_no_client(self, mock_client):
        """Test update_fix_for_failure when Supabase not available."""
        mock_client.return_value = None

        from observer_node import update_fix_for_failure

        result = update_fix_for_failure("test-trace", "Fix")

        assert result is False


class TestKnowledgeGraphContext:
    """Tests for Knowledge Graph integration in learning context."""

    @patch("observer_node.query_past_failures")
    @patch("observer_node._get_knowledge_graph_context")
    def test_get_learning_context_includes_kg_context(self, mock_kg_context, mock_query):
        """Test get_learning_context includes Knowledge Graph context when available."""
        mock_query.return_value = [
            {
                "id": 1,
                "error_text": "Test error",
                "fix_text": "Test fix",
                "error_type": "ci_failure",
                "similarity": 0.8,
                "confidence_score": 0.9,
            }
        ]
        mock_kg_context.return_value = "## Knowledge Graph Patterns:\n\n### Pattern 1: fix_1234\nType: fix_pattern\n"

        from observer_node import get_learning_context

        context = get_learning_context("Test goal", task_type="python_bug_fix")

        assert "Past Experience" in context
        assert "Knowledge Graph Patterns" in context
        mock_kg_context.assert_called_once_with("Test goal", "python_bug_fix")

    @patch("observer_node.query_past_failures")
    @patch("observer_node._get_knowledge_graph_context")
    def test_get_learning_context_without_kg_context(self, mock_kg_context, mock_query):
        """Test get_learning_context works when KG context is empty."""
        mock_query.return_value = [
            {
                "id": 1,
                "error_text": "Test error",
                "fix_text": "Test fix",
                "error_type": "ci_failure",
                "similarity": 0.8,
                "confidence_score": 0.9,
            }
        ]
        mock_kg_context.return_value = ""

        from observer_node import get_learning_context

        context = get_learning_context("Test goal")

        assert "Past Experience" in context
        assert "Knowledge Graph Patterns" not in context

    @patch("common.config.settings.settings")
    def test_kg_context_disabled_by_flag(self, mock_settings):
        """Test _get_knowledge_graph_context returns empty when flag is disabled."""
        mock_settings.enable_knowledge_graph_learning = False

        from observer_node import _get_knowledge_graph_context

        result = _get_knowledge_graph_context("Test goal")

        assert result == ""

    @pytest.mark.skipif(not KG_AVAILABLE, reason="Knowledge Graph module not available")
    @patch("common.config.settings.settings")
    @patch("agents.dev_agent.knowledge_graph.knowledge_graph_manager.get_knowledge_graph_manager")
    def test_kg_context_with_patterns(self, mock_get_kg, mock_settings):
        """Test _get_knowledge_graph_context formats patterns correctly."""
        mock_settings.enable_knowledge_graph_learning = True
        mock_settings.knowledge_graph_max_patterns = 3

        mock_kg_manager = MagicMock()
        mock_kg_manager.search_relevant_patterns.return_value = {
            "success": True,
            "data": {
                "patterns": [
                    {
                        "pattern_name": "fix_timeout_1234",
                        "pattern_type": "fix_pattern",
                        "pattern_template": "Fix: Increase timeout",
                        "confidence_score": 0.9,
                        "frequency": 5,
                        "examples": [{"fix_strategy": "Increase timeout to 60s"}],
                    }
                ],
                "count": 1,
            }
        }
        mock_get_kg.return_value = mock_kg_manager

        from observer_node import _get_knowledge_graph_context

        result = _get_knowledge_graph_context("Connection timeout error", task_type="python_bug_fix")

        assert "Knowledge Graph Patterns" in result
        assert "fix_timeout_1234" in result
        assert "fix_pattern" in result
        assert "0.90" in result
        assert "Increase timeout" in result

    @pytest.mark.skipif(not KG_AVAILABLE, reason="Knowledge Graph module not available")
    @patch("common.config.settings.settings")
    @patch("agents.dev_agent.knowledge_graph.knowledge_graph_manager.get_knowledge_graph_manager")
    def test_kg_context_no_patterns_found(self, mock_get_kg, mock_settings):
        """Test _get_knowledge_graph_context returns empty when no patterns found."""
        mock_settings.enable_knowledge_graph_learning = True
        mock_settings.knowledge_graph_max_patterns = 3

        mock_kg_manager = MagicMock()
        mock_kg_manager.search_relevant_patterns.return_value = {
            "success": True,
            "data": {"patterns": [], "count": 0}
        }
        mock_get_kg.return_value = mock_kg_manager

        from observer_node import _get_knowledge_graph_context

        result = _get_knowledge_graph_context("New error type")

        assert result == ""

    @pytest.mark.skipif(not KG_AVAILABLE, reason="Knowledge Graph module not available")
    @patch("common.config.settings.settings")
    @patch("agents.dev_agent.knowledge_graph.knowledge_graph_manager.get_knowledge_graph_manager")
    def test_kg_context_handles_kg_error(self, mock_get_kg, mock_settings):
        """Test _get_knowledge_graph_context handles KG errors gracefully."""
        mock_settings.enable_knowledge_graph_learning = True
        mock_settings.knowledge_graph_max_patterns = 3

        mock_kg_manager = MagicMock()
        mock_kg_manager.search_relevant_patterns.return_value = {
            "success": False,
            "error": "Database connection failed"
        }
        mock_get_kg.return_value = mock_kg_manager

        from observer_node import _get_knowledge_graph_context

        result = _get_knowledge_graph_context("Test goal")

        assert result == ""

    @patch("common.config.settings.settings")
    def test_kg_context_handles_import_error(self, mock_settings):
        """Test _get_knowledge_graph_context handles import errors gracefully."""
        mock_settings.enable_knowledge_graph_learning = True

        # Temporarily remove the module to simulate import error
        import sys

        # Remove the knowledge_graph_manager module if it exists
        modules_to_remove = [k for k in sys.modules.keys() if 'knowledge_graph_manager' in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Mock the import to raise ImportError
        with patch.dict(sys.modules, {'agents.dev_agent.knowledge_graph.knowledge_graph_manager': None}):
            from observer_node import _get_knowledge_graph_context

            result = _get_knowledge_graph_context("Test goal")

            # Should return empty string on import error
            assert result == ""

    @pytest.mark.skipif(not KG_AVAILABLE, reason="Knowledge Graph module not available")
    def test_kg_context_language_detection_python(self):
        """Test language detection for Python task types."""
        with patch("common.config.settings.settings") as mock_settings:
            mock_settings.enable_knowledge_graph_learning = True
            mock_settings.knowledge_graph_max_patterns = 3

            with patch("agents.dev_agent.knowledge_graph.knowledge_graph_manager.get_knowledge_graph_manager") as mock_get_kg:
                mock_kg_manager = MagicMock()
                mock_kg_manager.search_relevant_patterns.return_value = {
                    "success": True,
                    "data": {"patterns": [], "count": 0}
                }
                mock_get_kg.return_value = mock_kg_manager

                from observer_node import _get_knowledge_graph_context

                _get_knowledge_graph_context("Test goal", task_type="python_bug_fix")

                # Verify language was detected and passed
                call_args = mock_kg_manager.search_relevant_patterns.call_args
                assert call_args[1]["language"] == "python"

    @pytest.mark.skipif(not KG_AVAILABLE, reason="Knowledge Graph module not available")
    def test_kg_context_language_detection_javascript(self):
        """Test language detection for JavaScript task types."""
        with patch("common.config.settings.settings") as mock_settings:
            mock_settings.enable_knowledge_graph_learning = True
            mock_settings.knowledge_graph_max_patterns = 3

            with patch("agents.dev_agent.knowledge_graph.knowledge_graph_manager.get_knowledge_graph_manager") as mock_get_kg:
                mock_kg_manager = MagicMock()
                mock_kg_manager.search_relevant_patterns.return_value = {
                    "success": True,
                    "data": {"patterns": [], "count": 0}
                }
                mock_get_kg.return_value = mock_kg_manager

                from observer_node import _get_knowledge_graph_context

                _get_knowledge_graph_context("Test goal", task_type="javascript_feature")

                call_args = mock_kg_manager.search_relevant_patterns.call_args
                assert call_args[1]["language"] == "javascript"
