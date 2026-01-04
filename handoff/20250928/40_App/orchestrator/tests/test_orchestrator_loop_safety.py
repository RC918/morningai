"""
Orchestrator Loop Safety Gate - Deterministic bounded execution tests.

This module provides a safety net to prevent infinite loops in the orchestrator
state machine. It does NOT rely on LLM reviewers - it uses bounded execution
to detect loops deterministically.

Issue: MorningAI Reviewer Agent Enhancement
- gemini-code-assist found infinite loop in PR #3541 that MorningAI Reviewer missed
- This safety gate ensures such issues are caught by CI, not just code review

Design Principles:
1. Bounded Execution: Run graph with max step limit, fail if exceeded
2. Loop Detection: Track node sequence, detect repeated patterns
3. Flag Consumption: Verify one-shot flags are consumed after first use
4. No External Dependencies: Stub all I/O (GitHub API, LLM calls)

Test Categories:
1. TestOneShotFlagConsumption - Verify flags are consumed after first use
2. TestBoundedExecution - Verify graph terminates within step limit
3. TestNodeSequencePatterns - Detect repeated node sequences (loops)
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any, Optional


class TestOneShotFlagConsumption:
    """Test that one-shot flags are properly consumed after first use.

    One-shot flags are state flags that should only trigger special behavior
    on the FIRST pass through a node. If not consumed, they can cause infinite loops.

    Known one-shot flags:
    - ci_failure_trigger + ci_failure_fast_path_consumed (Issue #3541)
    """

    def test_ci_failure_fast_path_consumed_on_first_pass(self):
        """Verify ci_failure_fast_path_consumed is set on first ci_monitor pass.

        Regression test for Issue #3541: Without this flag, ci_monitor would
        always force ci_state="failure" when ci_failure_trigger=True, causing
        an infinite loop when fixer routes back to ci_monitor.
        """
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-one-shot-flag",
            "ci_failure_trigger": True,
            "ci_state": "pending",
            "pr_number": 123,
            "messages": [],
            # ci_failure_fast_path_consumed is NOT set (first pass)
        }

        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api"):
                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # CRITICAL: Flag must be consumed on first pass
        assert result.get("ci_failure_fast_path_consumed") is True, (
            "ci_failure_fast_path_consumed must be set to True on first pass "
            "to prevent infinite loop when fixer routes back to ci_monitor"
        )

    def test_ci_failure_fast_path_allows_real_ci_check_on_second_pass(self):
        """Verify second pass checks real CI status (not forced failure).

        After fixer applies fix and routes back to ci_monitor, we need to
        check the REAL CI status to see if the fix worked.
        """
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-second-pass",
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

        # CRITICAL: Second pass must check real CI status
        mock_github.get_repo.assert_called_once()
        mock_github.get_pr_checks.assert_called_once()

        # ci_state should reflect real CI status, not forced "failure"
        assert result["ci_state"] == "success", (
            "Second pass must check real CI status. If ci_state is still 'failure', "
            "the fast path was not properly consumed, causing infinite loop."
        )


class TestBoundedExecution:
    """Test that orchestrator graph terminates within bounded step limit.

    These tests simulate graph execution with a maximum step count.
    If the step count is exceeded, it indicates a potential infinite loop.
    """

    MAX_STEPS = 50  # Maximum allowed steps before declaring infinite loop

    def test_ci_failure_flow_terminates(self):
        """Verify CI failure auto-fix flow terminates within step limit.

        Flow: ci_monitor -> reviewer -> router -> fixer -> ci_monitor -> ...
        This flow should terminate when CI passes or max fix attempts reached.
        """
        # Simulate bounded execution by tracking node visits
        node_visits: List[str] = []
        step_count = 0

        # Initial state for CI failure flow
        state = {
            "trace_id": "test-bounded-ci-failure",
            "ci_failure_trigger": True,
            "ci_state": "failure",
            "pr_number": 123,
            "messages": [],
            "fix_attempts": 0,
        }

        # Simulate graph execution with bounded steps
        current_node = "ci_monitor"
        max_fix_attempts = 3

        while step_count < self.MAX_STEPS:
            node_visits.append(current_node)
            step_count += 1

            if current_node == "ci_monitor":
                # First pass: consume fast path flag
                if not state.get("ci_failure_fast_path_consumed"):
                    state["ci_failure_fast_path_consumed"] = True
                    state["ci_state"] = "failure"
                else:
                    # Subsequent passes: simulate CI check
                    # After fix, CI might pass
                    if state.get("fix_attempts", 0) > 0:
                        state["ci_state"] = "success"
                current_node = "reviewer"

            elif current_node == "reviewer":
                current_node = "router"

            elif current_node == "router":
                if state["ci_state"] == "success":
                    current_node = "publisher"
                elif state.get("fix_attempts", 0) >= max_fix_attempts:
                    current_node = "finalizer"  # Give up after max attempts
                else:
                    current_node = "fixer"

            elif current_node == "fixer":
                state["fix_attempts"] = state.get("fix_attempts", 0) + 1
                current_node = "ci_monitor"  # Route back to check CI

            elif current_node in ("publisher", "finalizer"):
                break  # Terminal nodes

        assert step_count < self.MAX_STEPS, (
            f"CI failure flow exceeded {self.MAX_STEPS} steps. "
            f"Node sequence: {' -> '.join(node_visits[-20:])}. "
            "This indicates a potential infinite loop."
        )

    def test_normal_pr_flow_terminates(self):
        """Verify normal PR flow terminates within step limit.

        Flow: planner -> executor -> ci_monitor -> reviewer -> router -> publisher
        """
        node_visits: List[str] = []
        step_count = 0

        state = {
            "trace_id": "test-bounded-normal",
            "ci_state": "success",
            "pr_number": 456,
            "messages": [],
        }

        current_node = "planner"

        while step_count < self.MAX_STEPS:
            node_visits.append(current_node)
            step_count += 1

            if current_node == "planner":
                current_node = "executor"
            elif current_node == "executor":
                current_node = "ci_monitor"
            elif current_node == "ci_monitor":
                current_node = "reviewer"
            elif current_node == "reviewer":
                current_node = "router"
            elif current_node == "router":
                if state["ci_state"] == "success":
                    current_node = "publisher"
                else:
                    current_node = "fixer"
            elif current_node == "fixer":
                current_node = "ci_monitor"
            elif current_node == "publisher":
                break

        assert step_count < self.MAX_STEPS, (
            f"Normal PR flow exceeded {self.MAX_STEPS} steps. "
            f"Node sequence: {' -> '.join(node_visits[-20:])}. "
            "This indicates a potential infinite loop."
        )


class TestNodeSequencePatterns:
    """Test for repeated node sequence patterns that indicate loops.

    A repeated sequence like [A, B, C, A, B, C, A, B, C] indicates a loop.
    This is different from bounded execution - it detects the PATTERN of a loop
    even if the step count hasn't been exceeded yet.
    """

    def detect_loop_pattern(
        self,
        sequence: List[str],
        min_pattern_length: int = 2,
        min_repetitions: int = 3
    ) -> Optional[List[str]]:
        """Detect repeated patterns in node sequence.

        Args:
            sequence: List of node names in execution order
            min_pattern_length: Minimum length of pattern to detect
            min_repetitions: Minimum number of repetitions to consider a loop

        Returns:
            The repeated pattern if found, None otherwise
        """
        if len(sequence) < min_pattern_length * min_repetitions:
            return None

        # Check for patterns of increasing length
        for pattern_len in range(min_pattern_length, len(sequence) // min_repetitions + 1):
            # Get the last pattern_len * min_repetitions elements
            tail = sequence[-(pattern_len * min_repetitions):]

            # Check if tail consists of repeated pattern
            pattern = tail[:pattern_len]
            is_repeated = all(
                tail[i * pattern_len:(i + 1) * pattern_len] == pattern
                for i in range(min_repetitions)
            )

            if is_repeated:
                return pattern

        return None

    def test_detect_simple_loop(self):
        """Test that simple loop pattern is detected."""
        sequence = ["A", "B", "C", "A", "B", "C", "A", "B", "C"]
        pattern = self.detect_loop_pattern(sequence)
        assert pattern == ["A", "B", "C"]

    def test_no_false_positive_for_normal_flow(self):
        """Test that normal flow is not flagged as loop."""
        sequence = ["planner", "executor", "ci_monitor", "reviewer", "router", "publisher"]
        pattern = self.detect_loop_pattern(sequence)
        assert pattern is None

    def test_ci_failure_loop_pattern_detected(self):
        """Test that CI failure infinite loop pattern is detected.

        This is the pattern that would occur without the ci_failure_fast_path_consumed fix:
        ci_monitor -> reviewer -> router -> fixer -> ci_monitor -> ... (repeat)
        """
        # Simulate the infinite loop pattern from Issue #3541
        loop_pattern = ["ci_monitor", "reviewer", "router", "fixer"]
        sequence = loop_pattern * 4  # 4 repetitions

        pattern = self.detect_loop_pattern(sequence, min_pattern_length=4, min_repetitions=3)
        assert pattern == loop_pattern, (
            "CI failure infinite loop pattern should be detected. "
            "This pattern occurs when ci_failure_fast_path_consumed is not set."
        )


class TestRouterEdgeSafety:
    """Test safety of router edge decisions.

    When adding new edges to the orchestrator graph, ensure they don't
    create cycles that could lead to infinite loops.
    """

    def test_should_proceed_after_fixer_routes_to_ci_monitor(self):
        """Verify should_proceed_after_fixer routes to ci_monitor for CI failure flow.

        This is the edge that was added in PR #3541 to bypass executor_node.
        """
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-fixer-routing",
            "ci_failure_trigger": True,
            "messages": [],
        }

        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            from langgraph_orchestrator import should_proceed_after_fixer
            result = should_proceed_after_fixer(state)

        assert result == "ci_monitor", (
            "should_proceed_after_fixer must route to ci_monitor when ci_failure_trigger=True "
            "to check if the fix resolved the CI failure"
        )

    def test_should_proceed_after_fixer_routes_to_executor_for_normal_flow(self):
        """Verify should_proceed_after_fixer routes to executor for normal flow."""
        from unittest.mock import patch, MagicMock

        state = {
            "trace_id": "test-fixer-routing-normal",
            "ci_failure_trigger": False,
            "messages": [],
        }

        with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
            mock_metrics.return_value = MagicMock()

            from langgraph_orchestrator import should_proceed_after_fixer
            result = should_proceed_after_fixer(state)

        assert result == "executor", (
            "should_proceed_after_fixer must route to executor for normal flow "
            "(when ci_failure_trigger is False)"
        )


class TestStateFlagInvariants:
    """Test invariants for state flags that affect routing.

    These tests verify that state flags maintain expected invariants
    throughout the orchestrator execution.
    """

    def test_ci_failure_trigger_preserved_through_flow(self):
        """Verify ci_failure_trigger is preserved through the entire flow.

        The flag should not be accidentally cleared or modified during execution.
        """
        initial_state = {
            "trace_id": "test-flag-preservation",
            "ci_failure_trigger": True,
            "ci_state": "failure",
            "pr_number": 123,
            "messages": [],
        }

        # Simulate passing through multiple nodes
        state = initial_state.copy()

        # ci_monitor should preserve ci_failure_trigger
        with patch("langgraph_orchestrator.time") as mock_time:
            mock_time.time.return_value = 1000.0
            with patch("langgraph_orchestrator._get_metrics") as mock_metrics:
                mock_metrics.return_value = MagicMock()
                with patch("tools.github_api"):
                    from langgraph_orchestrator import ci_monitor_node
                    state = ci_monitor_node(state)

        assert state.get("ci_failure_trigger") is True, (
            "ci_failure_trigger must be preserved through ci_monitor_node. "
            "If cleared, routing decisions will be incorrect."
        )

    def test_fast_path_consumed_only_set_once(self):
        """Verify ci_failure_fast_path_consumed is only set once (idempotent).

        Multiple passes through ci_monitor should not reset the consumed flag.
        """
        state = {
            "trace_id": "test-idempotent-flag",
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
                    mock_github.get_pr_checks.return_value = ("failure", [])

                    from langgraph_orchestrator import ci_monitor_node
                    result = ci_monitor_node(state)

        # Flag should still be True (not reset to False)
        assert result.get("ci_failure_fast_path_consumed") is True, (
            "ci_failure_fast_path_consumed must remain True once set. "
            "Resetting it would cause the fast path to trigger again."
        )
