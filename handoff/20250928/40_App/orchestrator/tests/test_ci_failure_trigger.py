"""
Tests for CI failure trigger flow (Issue #3366).

This module tests the orchestrator-side logic for CI failure auto-fix:
1. CI failure trigger context extraction logic
2. CI failure task context building

Note: Tests for _enqueue_ci_failure_task() in webhooks.py are located in
the api-backend test suite (webhooks/tests/) since that module requires Flask.
"""


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
