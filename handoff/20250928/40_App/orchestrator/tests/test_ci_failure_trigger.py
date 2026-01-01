"""
Tests for CI failure trigger flow (Issue #3366).

This module tests the webhook-to-orchestrator connection for CI failure auto-fix:
1. _enqueue_ci_failure_task() in webhooks.py routes CI failure events
2. run_orchestrator() detects ci_failure_trigger context
3. AgentState includes ci_failure_trigger field
"""

from unittest.mock import MagicMock, patch


class TestCIFailureTriggerContext:
    """Test CI failure trigger context handling in run_orchestrator."""

    def test_ci_failure_trigger_extracted_from_context(self):
        """Test that ci_failure_trigger is extracted from webhook context."""
        from langgraph_orchestrator import run_orchestrator

        context = {
            "resource_type": "pull_request",
            "pr_number": 123,
            "ci_failure_trigger": True,
        }

        with patch("langgraph_orchestrator.create_orchestrator_graph") as mock_graph:
            mock_app = MagicMock()
            mock_app.invoke.return_value = {"final_result": {"status": "success"}}
            mock_graph.return_value = mock_app

            with patch("langgraph_orchestrator.get_postgres_checkpointer", return_value=None):
                with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                    mock_metrics.return_value = MagicMock()
                    with patch("langgraph_orchestrator._get_agent_eval") as mock_eval:
                        mock_eval.return_value = MagicMock()

                        run_orchestrator(
                            goal="Fix CI failure",
                            repo="test/repo",
                            trace_id="test-trace-123",
                            context=context,
                        )

                        call_args = mock_app.invoke.call_args
                        initial_state = call_args[0][0]
                        assert initial_state.get("ci_failure_trigger") is True
                        assert initial_state.get("pr_number") == 123

    def test_ci_failure_trigger_not_set_without_flag(self):
        """Test that ci_failure_trigger is None when not in context."""
        from langgraph_orchestrator import run_orchestrator

        context = {
            "resource_type": "pull_request",
            "pr_number": 456,
        }

        with patch("langgraph_orchestrator.create_orchestrator_graph") as mock_graph:
            mock_app = MagicMock()
            mock_app.invoke.return_value = {"final_result": {"status": "success"}}
            mock_graph.return_value = mock_app

            with patch("langgraph_orchestrator.get_postgres_checkpointer", return_value=None):
                with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                    mock_metrics.return_value = MagicMock()
                    with patch("langgraph_orchestrator._get_agent_eval") as mock_eval:
                        mock_eval.return_value = MagicMock()

                        run_orchestrator(
                            goal="Review PR",
                            repo="test/repo",
                            trace_id="test-trace-456",
                            context=context,
                        )

                        call_args = mock_app.invoke.call_args
                        initial_state = call_args[0][0]
                        assert initial_state.get("ci_failure_trigger") is None

    def test_ci_failure_trigger_requires_pull_request_resource_type(self):
        """Test that ci_failure_trigger only works with pull_request resource_type."""
        from langgraph_orchestrator import run_orchestrator

        context = {
            "resource_type": "issue",
            "ci_failure_trigger": True,
        }

        with patch("langgraph_orchestrator.create_orchestrator_graph") as mock_graph:
            mock_app = MagicMock()
            mock_app.invoke.return_value = {"final_result": {"status": "success"}}
            mock_graph.return_value = mock_app

            with patch("langgraph_orchestrator.get_postgres_checkpointer", return_value=None):
                with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                    mock_metrics.return_value = MagicMock()
                    with patch("langgraph_orchestrator._get_agent_eval") as mock_eval:
                        mock_eval.return_value = MagicMock()

                        run_orchestrator(
                            goal="Fix issue",
                            repo="test/repo",
                            trace_id="test-trace-789",
                            context=context,
                        )

                        call_args = mock_app.invoke.call_args
                        initial_state = call_args[0][0]
                        assert initial_state.get("ci_failure_trigger") is None


class TestAgentStateCIFailureTrigger:
    """Test AgentState includes ci_failure_trigger field."""

    def test_agent_state_has_ci_failure_trigger_field(self):
        """Test that AgentState TypedDict includes ci_failure_trigger."""
        from langgraph_orchestrator import AgentState
        from typing import get_type_hints

        hints = get_type_hints(AgentState)
        assert "ci_failure_trigger" in hints

    def test_base_initial_state_includes_ci_failure_trigger(self):
        """Test that _create_base_initial_state includes ci_failure_trigger."""
        from langgraph_orchestrator import _create_base_initial_state

        state = _create_base_initial_state(
            goal="Test goal",
            trace_id="test-trace",
            repo="test/repo",
        )

        assert "ci_failure_trigger" in state
        assert state["ci_failure_trigger"] is None


class TestEnqueueCIFailureTask:
    """Test _enqueue_ci_failure_task in webhooks.py."""

    def test_enqueue_ci_failure_task_requires_pr_number(self):
        """Test that _enqueue_ci_failure_task requires pr_number in context."""
        import sys
        sys.path.insert(0, "/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/src")

        from routes.webhooks import _enqueue_ci_failure_task

        class MockTask:
            task_id = "test-task-123"
            goal_text = "Fix CI failure"
            context = {"ci_failure_trigger": True}

        task = MockTask()
        result = _enqueue_ci_failure_task(task)
        assert result is None

    def test_enqueue_ci_failure_task_with_valid_context(self):
        """Test that _enqueue_ci_failure_task works with valid context."""
        import sys
        sys.path.insert(0, "/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/src")

        from routes.webhooks import _enqueue_ci_failure_task

        class MockTask:
            task_id = "test-task-456"
            goal_text = "Fix CI failure"
            context = {
                "ci_failure_trigger": True,
                "ci_failure_pr_number": 123,
                "repo": "test/repo",
            }

        task = MockTask()

        with patch("routes.webhooks.settings") as mock_settings:
            mock_settings.redis_url = None
            result = _enqueue_ci_failure_task(task)
            assert result is None
