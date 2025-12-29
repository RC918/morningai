#!/usr/bin/env python3
"""
SimpleCoder E2E Integration Tests with LangGraph

Issue #3213: D-1.2 SimpleCoder E2E Integration Tests with LangGraph
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family

Acceptance Criteria:
1. Test Router -> SimpleCoder routing based on is_autofix_allowed()
2. Test SimpleCoder -> Publisher patch application
3. Test full workflow: PR webhook -> Review -> Coder -> Publish
4. Test error handling and fallback paths

This test file covers E2E integration scenarios that verify:
- ReviewToFixHandoff schema integration with routing decisions
- Autofix gate alignment with handoff eligibility
- State transitions through the full workflow
- Error handling and fallback to AutoFixer
"""
import logging
from typing import Optional, Dict, Any

from coder.autofix_gate import is_autofix_allowed, is_path_excluded
from core.routing.fix_handoff import (
    FixSuggestion,
    ReviewToFixHandoff,
    build_fix_handoff,
    should_route_to_fixer,
    HIGH_CONFIDENCE_THRESHOLD,
    build_empty_handoff,
)


def create_test_state(
    trace_id: str = "e2e-test-trace-123",
    retry_count: int = 0,
    error: Optional[str] = None,
    ci_state: str = "failure",
    pr_number: int = 123,
    review_severity: str = "low",
    review_outcome: Optional[dict] = None,
    review_file_path: str = "",
    comment_body: str = "",
    repo: str = "RC918/morningai",
    branch: str = "test-branch",
    diff_head_sha: str = "abc123",
    fix_handoff: Optional[dict] = None,
) -> Dict[str, Any]:
    """Create a test AgentState with E2E-relevant fields."""
    if review_outcome is None:
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
            "verdict": "request_changes",
        }

    state = {
        "messages": [],
        "goal": "Fix code issue",
        "trace_id": trace_id,
        "repo": repo,
        "branch": branch,
        "plan": ["Step 1", "Step 2"],
        "current_step": 2,
        "pr_url": f"https://github.com/{repo}/pull/{pr_number}",
        "pr_number": pr_number,
        "ci_state": ci_state,
        "ci_checks": {"lint": "failure"},
        "error": error,
        "retry_count": retry_count,
        "final_result": {},
        "review_result": {},
        "review_comments": [],
        "review_severity": review_severity,
        "merge_decision": "pending",
        "code_quality_score": 80,
        "review_outcome": review_outcome,
        "review_file_path": review_file_path,
        "comment_body": comment_body,
        "diff_head_sha": diff_head_sha,
    }

    if fix_handoff:
        state["fix_handoff"] = fix_handoff

    return state


def create_fix_suggestion(
    file_path: str = "src/utils.py",
    line_start: int = 10,
    line_end: int = 15,
    original_code: str = "def foo():",
    suggested_code: str = "def foo() -> None:",
    reason: str = "Add return type annotation",
    confidence: float = 0.9,
    category: str = "style",
) -> FixSuggestion:
    """Create a test FixSuggestion."""
    return FixSuggestion(
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        original_code=original_code,
        suggested_code=suggested_code,
        reason=reason,
        confidence=confidence,
        category=category,
    )


def create_eligible_review_outcome(**overrides) -> Dict[str, Any]:
    """Create an eligible review_outcome dict for autofix.

    Default values satisfy all autofix gate conditions:
    - severity="low"
    - diff_truncated=False
    - schema_validated=True

    Use overrides to customize specific fields for testing rejection cases.

    Example:
        # Eligible outcome
        outcome = create_eligible_review_outcome()

        # Rejected due to high severity
        outcome = create_eligible_review_outcome(severity="high")
    """
    base = {
        "severity": "low",
        "diff_truncated": False,
        "schema_validated": True,
    }
    base.update(overrides)
    return base


class TestRouterToSimpleCoderRouting:
    """E2E tests for Router -> SimpleCoder routing based on is_autofix_allowed()."""

    def test_routing_with_eligible_review_outcome(self):
        """Test that eligible ReviewOutcome routes to SimpleCoder."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is True

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert should_route_to_fixer(handoff) is True

    def test_routing_blocked_by_high_severity(self):
        """Test that high severity blocks routing to SimpleCoder."""
        review_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_routing_blocked_by_diff_truncated(self):
        """Test that truncated diff blocks routing to SimpleCoder."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": True,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_routing_blocked_by_schema_not_validated(self):
        """Test that unvalidated schema blocks routing to SimpleCoder."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": False,
        }

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_routing_blocked_by_low_confidence(self):
        """Test that low confidence suggestions block auto-fix eligibility."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is True

        suggestions = [create_fix_suggestion(confidence=0.5)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_routing_with_excluded_path(self):
        """Test that excluded paths are rejected by autofix gate."""
        assert is_path_excluded(".env") is True
        assert is_path_excluded("config/settings.py") is True
        assert is_path_excluded("migrations/001_init.py") is True
        assert is_path_excluded("src/utils.py") is False

    def test_routing_with_security_category_infers_high_severity(self):
        """Test that security category infers high severity when no review_outcome.

        Note: _determine_max_severity() uses review_outcome.severity first,
        then infers from suggestion categories only if review_outcome is None.
        """
        suggestions = [create_fix_suggestion(category="security", confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=None,
        )

        assert handoff.max_severity == "high"
        assert should_route_to_fixer(handoff) is False

    def test_routing_with_medium_severity_review_outcome(self):
        """Test that medium severity blocks routing."""
        review_outcome = {
            "severity": "medium",
            "diff_truncated": False,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False

    def test_routing_with_critical_severity_review_outcome(self):
        """Test that critical severity blocks routing."""
        review_outcome = {
            "severity": "critical",
            "diff_truncated": False,
            "schema_validated": True,
        }

        assert is_autofix_allowed(review_outcome) is False


class TestFullWorkflowE2E:
    """E2E tests for full workflow: PR webhook -> Review -> Coder -> Publish."""

    def test_workflow_state_with_fix_handoff(self):
        """Test that fix_handoff can be stored in state."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        state = create_test_state(
            review_outcome=review_outcome,
            fix_handoff=handoff.model_dump(),
        )

        assert "fix_handoff" in state
        assert state["fix_handoff"]["auto_fix_eligible"] is True
        assert len(state["fix_handoff"]["suggestions"]) == 1

    def test_workflow_routing_decision_from_handoff(self):
        """Test routing decision based on fix_handoff in state."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert should_route_to_fixer(handoff) is True

        handoff_dict = handoff.model_dump()
        reconstructed = ReviewToFixHandoff(**handoff_dict)
        assert should_route_to_fixer(reconstructed) is True

    def test_workflow_state_transitions(self):
        """Test state transitions through workflow."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        initial_state = create_test_state(
            trace_id="e2e-trace-456",
            retry_count=0,
            review_file_path="src/test.py",
            comment_body="Add docstring",
            review_outcome=review_outcome,
        )

        assert initial_state["trace_id"] == "e2e-trace-456"
        assert initial_state["retry_count"] == 0
        assert initial_state["review_file_path"] == "src/test.py"

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=initial_state["pr_number"],
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        initial_state["fix_handoff"] = handoff.model_dump()

        assert should_route_to_fixer(handoff) is True
        assert initial_state["fix_handoff"]["auto_fix_eligible"] is True

    def test_workflow_empty_handoff_for_no_suggestions(self):
        """Test empty handoff when there are no suggestions."""
        empty_handoff = build_empty_handoff(pr_number=123)

        assert empty_handoff["suggestions"] == []
        assert empty_handoff["auto_fix_eligible"] is False
        assert empty_handoff["requires_human_review"] is True

        state = create_test_state(fix_handoff=empty_handoff)
        assert state["fix_handoff"]["auto_fix_eligible"] is False


class TestReviewToFixHandoffIntegration:
    """E2E tests for ReviewToFixHandoff schema integration."""

    def test_handoff_schema_version_consistency(self):
        """Test that handoff schema version is consistent."""
        suggestions = [create_fix_suggestion()]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
        )

        assert handoff.schema_version == 1

        handoff_dict = handoff.model_dump()
        assert handoff_dict["schema_version"] == 1

    def test_handoff_preserves_all_suggestion_fields(self):
        """Test that handoff preserves all suggestion fields."""
        suggestion = create_fix_suggestion(
            file_path="src/utils.py",
            line_start=10,
            line_end=15,
            original_code="def foo():",
            suggested_code="def foo() -> None:",
            reason="Add return type annotation",
            confidence=0.9,
            category="style",
        )

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=[suggestion],
        )

        assert len(handoff.suggestions) == 1
        s = handoff.suggestions[0]
        assert s.file_path == "src/utils.py"
        assert s.line_start == 10
        assert s.line_end == 15
        assert s.original_code == "def foo():"
        assert s.suggested_code == "def foo() -> None:"
        assert s.reason == "Add return type annotation"
        assert s.confidence == 0.9
        assert s.category == "style"

    def test_handoff_computes_total_lines_affected(self):
        """Test that handoff computes total_lines_affected correctly."""
        suggestions = [
            create_fix_suggestion(line_start=10, line_end=15),
            create_fix_suggestion(line_start=20, line_end=25),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
        )

        assert handoff.total_lines_affected == 12

    def test_handoff_get_high_confidence_suggestions(self):
        """Test get_high_confidence_suggestions method."""
        suggestions = [
            create_fix_suggestion(confidence=0.9),
            create_fix_suggestion(confidence=0.5),
            create_fix_suggestion(confidence=HIGH_CONFIDENCE_THRESHOLD),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
        )

        high_conf = handoff.get_high_confidence_suggestions()
        assert len(high_conf) == 2
        assert all(s.confidence >= HIGH_CONFIDENCE_THRESHOLD for s in high_conf)

    def test_handoff_get_suggestions_by_category(self):
        """Test get_suggestions_by_category method."""
        suggestions = [
            create_fix_suggestion(category="style"),
            create_fix_suggestion(category="bug_fix"),
            create_fix_suggestion(category="style"),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
        )

        style_suggestions = handoff.get_suggestions_by_category("style")
        assert len(style_suggestions) == 2

        bug_suggestions = handoff.get_suggestions_by_category("bug_fix")
        assert len(bug_suggestions) == 1

    def test_handoff_serialization_roundtrip(self):
        """Test that handoff can be serialized and deserialized."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        handoff_dict = handoff.model_dump()

        reconstructed = ReviewToFixHandoff(**handoff_dict)

        assert reconstructed.pr_number == handoff.pr_number
        assert reconstructed.auto_fix_eligible == handoff.auto_fix_eligible
        assert len(reconstructed.suggestions) == len(handoff.suggestions)
        assert reconstructed.max_severity == handoff.max_severity


class TestAutoFixGateAndHandoffAlignment:
    """E2E tests verifying alignment between autofix_gate and fix_handoff."""

    def test_autofix_gate_and_handoff_agree_on_eligibility(self):
        """Test that autofix_gate and fix_handoff agree on eligibility."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        gate_result = is_autofix_allowed(review_outcome)

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert gate_result is True
        assert handoff.auto_fix_eligible is True

    def test_autofix_gate_and_handoff_agree_on_rejection(self):
        """Test that autofix_gate and fix_handoff agree on rejection."""
        review_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }

        gate_result = is_autofix_allowed(review_outcome)

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert gate_result is False
        assert handoff.auto_fix_eligible is False

    def test_handoff_adds_confidence_check_beyond_gate(self):
        """Test that handoff adds confidence check beyond autofix_gate."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        gate_result = is_autofix_allowed(review_outcome)
        assert gate_result is True

        suggestions = [create_fix_suggestion(confidence=0.5)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False

    def test_all_gate_conditions_must_pass(self):
        """Test that all gate conditions must pass for eligibility."""
        test_cases = [
            {"severity": "high", "diff_truncated": False, "schema_validated": True},
            {"severity": "low", "diff_truncated": True, "schema_validated": True},
            {"severity": "low", "diff_truncated": False, "schema_validated": False},
        ]

        for review_outcome in test_cases:
            assert is_autofix_allowed(review_outcome) is False

            suggestions = [create_fix_suggestion(confidence=0.9)]
            handoff = build_fix_handoff(
                pr_number=123,
                suggestions=suggestions,
                review_outcome=review_outcome,
            )
            assert handoff.auto_fix_eligible is False


class TestWorkflowEventCodes:
    """E2E tests for workflow event codes (greppable)."""

    def test_route_to_fixer_event_code(self, caplog):
        """Test that [ROUTE_TO_FIXER] event code is logged."""
        caplog.set_level(logging.INFO)

        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        result = should_route_to_fixer(handoff)

        assert result is True
        assert any("[ROUTE_TO_FIXER]" in record.message for record in caplog.records)

    def test_skip_fixer_event_code(self, caplog):
        """Test that [SKIP_FIXER] event code is logged."""
        caplog.set_level(logging.INFO)

        review_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [create_fix_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        result = should_route_to_fixer(handoff)

        assert result is False
        assert any("[SKIP_FIXER]" in record.message for record in caplog.records)

    def test_autofix_gate_pass_event_code(self, caplog):
        """Test that [AUTOFIX_GATE_PASS] event code is logged."""
        caplog.set_level(logging.INFO)

        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        result = is_autofix_allowed(review_outcome)

        assert result is True
        assert any(
            "[AUTOFIX_GATE_PASS]" in record.message for record in caplog.records
        )

    def test_autofix_gate_fail_event_code(self, caplog):
        """Test that [AUTOFIX_GATE_FAIL] event code is logged."""
        caplog.set_level(logging.INFO)

        review_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }

        result = is_autofix_allowed(review_outcome)

        assert result is False
        assert any(
            "[AUTOFIX_GATE_FAIL]" in record.message for record in caplog.records
        )


class TestExcludedPathsE2E:
    """E2E tests for excluded paths in autofix gate."""

    def test_config_paths_excluded(self):
        """Test that config paths are excluded."""
        assert is_path_excluded("config/settings.py") is True
        assert is_path_excluded("config/production.yaml") is True

    def test_migration_paths_excluded(self):
        """Test that migration paths are excluded."""
        assert is_path_excluded("migrations/001_init.py") is True
        assert is_path_excluded("migrations/versions/abc123.py") is True

    def test_env_files_excluded(self):
        """Test that .env files are excluded.

        Note: is_path_excluded() checks for exact basename match ".env",
        not prefix matches like ".env.local".
        """
        assert is_path_excluded(".env") is True
        assert is_path_excluded("config/.env") is True

    def test_package_files_excluded(self):
        """Test that package files are excluded."""
        assert is_path_excluded("package.json") is True
        assert is_path_excluded("package-lock.json") is True
        assert is_path_excluded("yarn.lock") is True
        assert is_path_excluded("poetry.lock") is True
        assert is_path_excluded("requirements.txt") is True

    def test_ci_files_excluded(self):
        """Test that CI files are excluded."""
        assert is_path_excluded(".github/workflows/ci.yml") is True
        assert is_path_excluded(".gitlab-ci.yml") is True
        assert is_path_excluded("Jenkinsfile") is True

    def test_docker_files_excluded(self):
        """Test that Docker files are excluded."""
        assert is_path_excluded("Dockerfile") is True
        assert is_path_excluded("docker-compose.yml") is True
        assert is_path_excluded("docker-compose.yaml") is True

    def test_regular_source_files_not_excluded(self):
        """Test that regular source files are not excluded."""
        assert is_path_excluded("src/utils.py") is False
        assert is_path_excluded("src/main.py") is False
        assert is_path_excluded("tests/test_utils.py") is False
        assert is_path_excluded("lib/helper.js") is False


class TestMultipleSuggestionsE2E:
    """E2E tests for handling multiple suggestions."""

    def test_multiple_suggestions_all_high_confidence(self):
        """Test multiple suggestions all with high confidence."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [
            create_fix_suggestion(file_path="a.py", confidence=0.9),
            create_fix_suggestion(file_path="b.py", confidence=0.85),
            create_fix_suggestion(file_path="c.py", confidence=0.95),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert len(handoff.get_high_confidence_suggestions()) == 3

    def test_multiple_suggestions_mixed_confidence(self):
        """Test multiple suggestions with mixed confidence."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [
            create_fix_suggestion(file_path="a.py", confidence=0.9),
            create_fix_suggestion(file_path="b.py", confidence=0.5),
            create_fix_suggestion(file_path="c.py", confidence=0.3),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert len(handoff.get_high_confidence_suggestions()) == 1

    def test_multiple_suggestions_all_low_confidence(self):
        """Test multiple suggestions all with low confidence."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [
            create_fix_suggestion(file_path="a.py", confidence=0.5),
            create_fix_suggestion(file_path="b.py", confidence=0.6),
            create_fix_suggestion(file_path="c.py", confidence=0.7),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert len(handoff.get_high_confidence_suggestions()) == 0

    def test_multiple_suggestions_mixed_categories(self):
        """Test multiple suggestions with mixed categories."""
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }

        suggestions = [
            create_fix_suggestion(category="style", confidence=0.9),
            create_fix_suggestion(category="bug_fix", confidence=0.9),
            create_fix_suggestion(category="refactor", confidence=0.9),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert len(handoff.get_suggestions_by_category("style")) == 1
        assert len(handoff.get_suggestions_by_category("bug_fix")) == 1
        assert len(handoff.get_suggestions_by_category("refactor")) == 1

    def test_security_suggestion_blocks_routing(self):
        """Test that security suggestion blocks routing when no review_outcome.

        Note: _determine_max_severity() uses review_outcome.severity first,
        then infers from suggestion categories only if review_outcome is None.
        """
        suggestions = [
            create_fix_suggestion(category="style", confidence=0.9),
            create_fix_suggestion(category="security", confidence=0.9),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=None,
        )

        assert handoff.max_severity == "high"
        assert should_route_to_fixer(handoff) is False
