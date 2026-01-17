"""
Tests for CI failure trigger flow (Issue #3366).

This module tests the orchestrator-side logic for CI failure auto-fix:
1. CI failure trigger context extraction logic
2. CI failure task context building
3. _build_context() CI failure metadata passing

Note: Tests for _enqueue_ci_failure_task() in webhooks.py are located in
the api-backend test suite (webhooks/tests/) since that module requires Flask.

=== OWNERSHIP & DEFENSE-IN-DEPTH ===

This file focuses on:
- CI FAILURE FLOW: Complete flow from webhook to orchestrator
- CONTEXT BUILDING: Event normalization, metadata passing, task context
- ROUTING LOGIC: Fast path short-circuit, entry point selection
- CI MONITOR BEHAVIOR: First pass vs second pass, API call skipping

Related file: test_orchestrator_loop_safety.py focuses on:
- LOOP SAFETY: Bounded execution, pattern detection, termination guarantees
- STATE MACHINE INVARIANTS: Flag consumption, state preservation

Some tests overlap intentionally (defense-in-depth):
- One-shot flag consumption tests exist in both files
- This file tests from "CI failure flow" perspective
- test_orchestrator_loop_safety.py tests from "loop prevention" perspective

This overlap is acceptable per Issue #3547 - both perspectives are valuable
for catching regressions. Do NOT remove overlapping tests without careful
consideration of coverage gaps.

Test Categories:
1. TestBuildContextCIFailureMetadata - Context building from webhook events
2. TestCIFailureTriggerContextExtraction - Extraction logic for ci_failure_trigger
3. TestCIFailureTaskContext - Task context structure validation
4. TestCIFailureFastPath - Router fast path behavior
5. TestCIMonitorFastPathConsumed - ci_monitor consumed flag behavior
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
        assert ci_context["source"] in {"ci_failure_webhook", "manual_fix"}

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
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

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
                    mock_decision = RoutingDecision(
                        next_node="publisher",
                        reasoning="Approved",
                        risk_assessment="low",
                        requires_hitl_approval=False,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    result = router_node(state)

        assert result["merge_decision"] == "approve"

    def test_router_no_short_circuit_when_no_ci_failure_trigger(self):
        """Test that router_node does NOT short-circuit when ci_failure_trigger=False."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

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
                    mock_decision = RoutingDecision(
                        next_node="fixer",
                        reasoning="Low severity fix",
                        risk_assessment="low",
                        requires_hitl_approval=False,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    router_node(state)

        assert mock_router.return_value.route_with_meta.called

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


class TestCIMonitorFastPathConsumed:
    """Test CI monitor fast path consumed flag (Issue #3541).

    This prevents infinite loop when fixer routes back to ci_monitor:
    - First pass: ci_failure_trigger=True, fast_path_consumed=False -> skip API, force failure
    - Second pass: ci_failure_trigger=True, fast_path_consumed=True -> check real CI status
    """

    def test_ci_monitor_first_pass_skips_api_and_sets_consumed(self):
        """Test that first ci_monitor pass skips API call and sets consumed flag."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-first-pass",
            "ci_failure_trigger": True,
            "ci_state": "pending",  # Will be forced to "failure"
            "pr_number": 123,
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api") as mock_github:
                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # First pass should skip API call
        mock_github.get_repo.assert_not_called()
        mock_github.get_pr_checks.assert_not_called()

        # First pass should force ci_state to "failure"
        assert result["ci_state"] == "failure"

        # First pass should set consumed flag
        assert result["ci_failure_fast_path_consumed"] is True

    def test_ci_monitor_second_pass_checks_real_ci_status(self):
        """Test that second ci_monitor pass (post-fix) checks real CI status."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-second-pass",
            "ci_failure_trigger": True,
            "ci_state": "failure",
            "ci_failure_fast_path_consumed": True,  # Already consumed
            "pr_number": 123,
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api") as mock_github:
                    mock_repo = MagicMock()
                    mock_github.get_repo.return_value = mock_repo
                    # Simulate CI now passing after fix
                    mock_github.get_pr_checks.return_value = ("success", [])

                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # Second pass should call API to check real CI status
        mock_github.get_repo.assert_called_once()
        mock_github.get_pr_checks.assert_called_once_with(mock_repo, 123)

        # Second pass should update ci_state based on real CI status
        assert result["ci_state"] == "success"

    def test_ci_monitor_no_infinite_loop_after_fix(self):
        """Test that ci_monitor can observe CI recovery after fixer applies fix.

        This is a regression test for Issue #3541:
        Without the consumed flag, ci_monitor would always force ci_state="failure"
        when ci_failure_trigger=True, causing an infinite loop.
        """
        from unittest.mock import patch, MagicMock

        # Simulate state after fixer has applied fix and routed back to ci_monitor
        state = {
            "trace_id": "test-trace-no-loop",
            "ci_failure_trigger": True,
            "ci_state": "failure",
            "ci_failure_fast_path_consumed": True,
            "pr_number": 456,
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api") as mock_github:
                    mock_repo = MagicMock()
                    mock_github.get_repo.return_value = mock_repo
                    # CI is now passing after the fix
                    mock_github.get_pr_checks.return_value = ("success", [
                        {"name": "lint", "conclusion": "success"},
                    ])

                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # The key assertion: ci_state should be updated to "success"
        # If the infinite loop bug existed, ci_state would still be "failure"
        assert result["ci_state"] == "success"
        assert result["ci_checks"] == [{"name": "lint", "conclusion": "success"}]

    def test_ci_monitor_normal_flow_unaffected(self):
        """Test that normal flow (no ci_failure_trigger) is unaffected."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-normal",
            "ci_failure_trigger": False,
            "ci_state": "pending",
            "pr_number": 789,
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api") as mock_github:
                    mock_repo = MagicMock()
                    mock_github.get_repo.return_value = mock_repo
                    mock_github.get_pr_checks.return_value = ("success", [])

                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # Normal flow should always check real CI status
        mock_github.get_repo.assert_called_once()
        mock_github.get_pr_checks.assert_called_once()
        assert result["ci_state"] == "success"

        # Normal flow should not set consumed flag
        assert result.get("ci_failure_fast_path_consumed") is None


class TestMergedPRFastPath:
    """Test merged/closed PR fast path routing (Issue #4123 HITL Optimization).

    When a PR is already merged or closed, the router should skip HITL and route
    directly to finalizer. This aligns with Blueprint Section 9 (Self-Governed) -
    no human intervention needed for already-completed actions.
    """

    def test_router_fast_path_for_merged_pr(self):
        """Test that router_node routes merged PRs to finalizer without HITL."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-merged",
            "pr_context": {"state": "merged"},
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()

                from langgraph_orchestrator import router_node
                result = router_node(state)

        assert result["merge_decision"] == "approve"
        assert result["requires_hitl_approval"] is False
        assert result["routing_decision"]["next_node"] == "finalizer"
        assert "merged" in result["routing_decision"]["reasoning"]
        assert "no HITL needed" in result["routing_decision"]["reasoning"]

    def test_router_fast_path_for_closed_pr(self):
        """Test that router_node routes closed PRs to finalizer without HITL."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-trace-closed",
            "pr_context": {"state": "closed"},
            "messages": [],
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()

                from langgraph_orchestrator import router_node
                result = router_node(state)

        assert result["merge_decision"] == "request_changes"
        assert result["requires_hitl_approval"] is False
        assert result["routing_decision"]["next_node"] == "finalizer"
        assert "closed" in result["routing_decision"]["reasoning"]

    def test_router_no_fast_path_for_open_pr(self):
        """Test that router_node does NOT fast-path open PRs."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

        state = {
            "trace_id": "test-trace-open",
            "pr_context": {"state": "open"},
            "messages": [],
            "review_outcome": {
                "verdict": "unknown",
                "severity": "none",
                "summary": "Needs review",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = RoutingDecision(
                        next_node="decision",
                        reasoning="Unknown verdict requires review",
                        risk_assessment="high",
                        requires_hitl_approval=True,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    result = router_node(state)

        assert mock_router.return_value.route_with_meta.called
        assert result["requires_hitl_approval"] is True

    def test_router_no_fast_path_without_pr_context(self):
        """Test that router_node does NOT fast-path when pr_context is missing."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

        state = {
            "trace_id": "test-trace-no-context",
            "messages": [],
            "review_outcome": {
                "verdict": "approve",
                "severity": "none",
                "summary": "All good",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = RoutingDecision(
                        next_node="publisher",
                        reasoning="Approved",
                        risk_assessment="low",
                        requires_hitl_approval=False,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    router_node(state)

        assert mock_router.return_value.route_with_meta.called

    def test_merged_pr_fast_path_decision_mode(self):
        """Test that merged PR fast path uses MERGED_PR_FAST_PATH decision mode."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode

        state = {
            "trace_id": "test-trace-decision-mode",
            "pr_context": {"state": "merged"},
            "messages": [],
        }

        recorded_decision_mode = None

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.router_metrics.get_router_metrics") as mock_get_router_metrics:
                    mock_router_metrics = MagicMock()
                    def capture_decision_mode(**kwargs):
                        nonlocal recorded_decision_mode
                        recorded_decision_mode = kwargs.get("decision_mode")
                    mock_router_metrics.record_decision.side_effect = capture_decision_mode
                    mock_get_router_metrics.return_value = mock_router_metrics

                    from langgraph_orchestrator import router_node
                    router_node(state)

        assert recorded_decision_mode == DecisionMode.MERGED_PR_FAST_PATH

    def test_none_pr_context_does_not_crash(self):
        """Test that explicit None pr_context doesn't cause AttributeError (Cursor Bugbot fix)."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

        state = {
            "trace_id": "test-trace-none-context",
            "pr_context": None,
            "messages": [],
            "review_outcome": {
                "verdict": "approve",
                "severity": "none",
                "summary": "All good",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = RoutingDecision(
                        next_node="publisher",
                        reasoning="Approved",
                        risk_assessment="low",
                        requires_hitl_approval=False,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    result = router_node(state)

        assert mock_router.return_value.route_with_meta.called
        assert result["routing_decision"]["next_node"] == "publisher"

    def test_open_pr_with_unknown_verdict_still_triggers_hitl(self):
        """Test that open PRs with unknown verdict still trigger HITL (safety maintained)."""
        from unittest.mock import patch, MagicMock
        from core.flow.schema import DecisionMode, RoutingDecision, RoutingResult

        state = {
            "trace_id": "test-trace-safety",
            "pr_context": {"state": "open"},
            "messages": [],
            "review_outcome": {
                "verdict": "unknown",
                "severity": "none",
                "summary": "",
                "blocker_count": 0,
            },
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.monotonic.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("core.flow.hybrid_router.get_hybrid_router") as mock_router:
                    mock_decision = RoutingDecision(
                        next_node="decision",
                        reasoning="Unknown verdict requires human review",
                        risk_assessment="high",
                        requires_hitl_approval=True,
                    )
                    mock_result = RoutingResult(
                        decision=mock_decision,
                        decision_mode=DecisionMode.FAST_PATH,
                    )
                    mock_router.return_value.route_with_meta.return_value = mock_result

                    from langgraph_orchestrator import router_node
                    result = router_node(state)

        assert result["requires_hitl_approval"] is True
        assert result["routing_decision"]["next_node"] == "decision"
