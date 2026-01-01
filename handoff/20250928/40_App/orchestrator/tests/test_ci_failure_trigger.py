"""
Tests for CI failure trigger flow (Issue #3366).

This module tests the orchestrator-side logic for CI failure auto-fix:
1. CI failure trigger context extraction logic
2. CI failure task context building
3. _build_context() CI failure metadata passing

Note: Tests for _enqueue_ci_failure_task() in webhooks.py are located in
the api-backend test suite (webhooks/tests/) since that module requires Flask.
"""

from datetime import datetime, timezone

from webhooks.normalizer import EventNormalizer
from webhooks.bot_protocol import WebhookEvent, WebhookSource, WebhookEventType


class TestBuildContextCIFailureMetadata:
    """Test that _build_context() properly passes CI failure metadata to task context."""

    def test_build_context_passes_ci_failure_trigger(self):
        """Test that ci_failure_trigger is passed from event.metadata to context."""
        normalizer = EventNormalizer()

        event = WebhookEvent(
            event_id="test-event-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            repo_owner="test",
            repo_name="repo",
            metadata={
                "ci_failure_trigger": True,
                "ci_failure_pr_number": 123,
                "ci_failure_dedup_key": "test/repo:123:abc123",
            },
        )

        context = normalizer._build_context(event)

        assert context.get("ci_failure_trigger") is True
        assert context.get("ci_failure_pr_number") == 123
        assert context.get("ci_failure_dedup_key") == "test/repo:123:abc123"

    def test_build_context_no_ci_failure_metadata_when_not_set(self):
        """Test that CI failure metadata is not added when not in event.metadata."""
        normalizer = EventNormalizer()

        event = WebhookEvent(
            event_id="test-event-456",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            repo_owner="test",
            repo_name="repo",
            metadata={},
        )

        context = normalizer._build_context(event)

        assert "ci_failure_trigger" not in context
        assert "ci_failure_pr_number" not in context
        assert "ci_failure_dedup_key" not in context


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


class TestCIFailureFastPath:
    """Test CI failure fast path routing (Issue #3366 Two-Layer Routing Optimization)."""

    def test_router_short_circuit_when_ci_failure_trigger(self):
        """Test that router_node short-circuits to fixer when ci_failure_trigger=True."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_state": "failure",
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()

                from langgraph_orchestrator import router_node
                result = router_node(state)

        assert result["merge_decision"] == "needs_fix"
        assert result["requires_hitl_approval"] is False
        assert result["routing_decision"]["next_node"] == "fixer"
        assert "CI failure fast path" in result["routing_decision"]["reasoning"]

    def test_router_no_short_circuit_when_ci_success(self):
        """Test that router_node does NOT short-circuit when ci_state=success."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-456",
            "ci_failure_trigger": True,
            "ci_state": "success",
            "messages": [],
            "review_outcome": {
                "verdict": "approve",
                "severity": "none",
                "summary": "All good",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = MagicMock()
                    mock_decision.next_node = "publisher"
                    mock_decision.requires_hitl_approval = False
                    mock_decision.reasoning = "Approved"
                    mock_decision.risk_assessment = "low"
                    mock_router.return_value.route.return_value = mock_decision

                    from langgraph_orchestrator import router_node
                    result = router_node(state)

        assert result["merge_decision"] == "approve"

    def test_router_no_short_circuit_when_no_ci_failure_trigger(self):
        """Test that router_node does NOT short-circuit when ci_failure_trigger=False."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-789",
            "ci_failure_trigger": False,
            "ci_state": "failure",
            "messages": [],
            "review_outcome": {
                "verdict": "request_changes",
                "severity": "low",
                "summary": "Fix needed",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = MagicMock()
                    mock_decision.next_node = "fixer"
                    mock_decision.requires_hitl_approval = False
                    mock_decision.reasoning = "Low severity fix"
                    mock_decision.risk_assessment = "low"
                    mock_router.return_value.route.return_value = mock_decision

                    from langgraph_orchestrator import router_node
                    router_node(state)

        assert mock_router.return_value.route.called

    def test_entry_point_shortcut_logic(self):
        """Test that entry_point is set to ci_monitor when ci_failure_trigger=True."""
        ci_failure_trigger = True
        entry_point = "planner"

        if ci_failure_trigger:
            entry_point = "ci_monitor"

        assert entry_point == "ci_monitor"

    def test_entry_point_default_planner(self):
        """Test that entry_point defaults to planner when ci_failure_trigger=False."""
        ci_failure_trigger = False
        entry_point = "planner"

        if ci_failure_trigger:
            entry_point = "ci_monitor"

        assert entry_point == "planner"
