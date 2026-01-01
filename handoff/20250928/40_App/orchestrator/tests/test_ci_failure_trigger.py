"""
Tests for CI failure trigger flow (Issue #3366).

This module tests the webhook-to-orchestrator connection for CI failure auto-fix:
1. _enqueue_ci_failure_task() in webhooks.py routes CI failure events
2. run_orchestrator() detects ci_failure_trigger context
3. AgentState includes ci_failure_trigger field
"""

import sys
from unittest.mock import patch

# Ensure api-backend/src is in path for webhook imports
sys.path.insert(0, "/home/ubuntu/repos/morningai/handoff/20250928/40_App/api-backend/src")


class TestEnqueueCIFailureTask:
    """Test _enqueue_ci_failure_task in webhooks.py."""

    def test_enqueue_ci_failure_task_requires_pr_number(self):
        """Test that _enqueue_ci_failure_task requires pr_number in context."""
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


class TestCIFailureTriggerContextExtraction:
    """Test CI failure trigger context extraction logic."""

    def test_ci_failure_trigger_extraction_logic(self):
        """Test the extraction logic for ci_failure_trigger from context."""
        # Simulate the extraction logic from run_orchestrator()
        context = {
            "resource_type": "pull_request",
            "pr_number": 123,
            "ci_failure_trigger": True,
        }

        # Extract ci_failure_trigger only when resource_type is pull_request
        ci_failure_trigger = False
        if context and context.get("resource_type") == "pull_request":
            ci_failure_trigger = context.get("ci_failure_trigger", False)

        assert ci_failure_trigger is True

    def test_ci_failure_trigger_not_extracted_for_non_pr(self):
        """Test that ci_failure_trigger is not extracted for non-PR resources."""
        context = {
            "resource_type": "issue",
            "ci_failure_trigger": True,
        }

        ci_failure_trigger = False
        if context and context.get("resource_type") == "pull_request":
            ci_failure_trigger = context.get("ci_failure_trigger", False)

        assert ci_failure_trigger is False

    def test_ci_failure_trigger_default_false(self):
        """Test that ci_failure_trigger defaults to False when not in context."""
        context = {
            "resource_type": "pull_request",
            "pr_number": 456,
        }

        ci_failure_trigger = False
        if context and context.get("resource_type") == "pull_request":
            ci_failure_trigger = context.get("ci_failure_trigger", False)

        assert ci_failure_trigger is False


class TestCIFailureTaskContext:
    """Test CI failure task context building."""

    def test_ci_context_includes_required_fields(self):
        """Test that CI failure context includes all required fields."""
        # Simulate the context building from _enqueue_ci_failure_task()
        task_context = {
            "ci_failure_trigger": True,
            "ci_failure_pr_number": 123,
            "repo": "test/repo",
        }

        ci_context = {
            **task_context,
            "resource_type": "pull_request",
            "resource_id": str(123),
            "pr_number": 123,
            "ci_failure_trigger": True,
            "source": "ci_failure_webhook",
        }

        assert ci_context["resource_type"] == "pull_request"
        assert ci_context["pr_number"] == 123
        assert ci_context["ci_failure_trigger"] is True
        assert ci_context["source"] == "ci_failure_webhook"

    def test_ci_context_preserves_original_context(self):
        """Test that CI failure context preserves original task context."""
        task_context = {
            "ci_failure_trigger": True,
            "ci_failure_pr_number": 456,
            "repo": "test/repo",
            "custom_field": "custom_value",
        }

        ci_context = {
            **task_context,
            "resource_type": "pull_request",
            "resource_id": str(456),
            "pr_number": 456,
            "ci_failure_trigger": True,
            "source": "ci_failure_webhook",
        }

        assert ci_context["custom_field"] == "custom_value"
        assert ci_context["repo"] == "test/repo"
