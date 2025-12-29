"""
Integration Tests for ReviewToFixHandoff Schema

Issue #3235: test(D-1): add integration tests for ReviewToFixHandoff schema

This module provides integration tests that verify the end-to-end flow
from Reviewer to Fixer, ensuring the ReviewToFixHandoff schema works
correctly in the actual workflow context.

Acceptance Criteria:
1. Integration test covers happy path (eligible PR routed to fixer)
2. Integration test covers safety path (high severity blocks routing)
3. Integration test covers edge cases (empty suggestions, low confidence)
4. Tests use realistic ReviewOutcome data

Related:
- PR #3233 (ReviewToFixHandoff schema)
- Issue #3225 (EPIC D Interface Definition)
- Issue #3213 (SimpleCoder E2E Integration Tests)
"""
import logging
from typing import Dict, Any

from core.routing.fix_handoff import (
    FixSuggestion,
    ReviewToFixHandoff,
    build_fix_handoff,
    should_route_to_fixer,
    build_empty_handoff,
    HIGH_CONFIDENCE_THRESHOLD,
)
from coder.autofix_gate import is_autofix_allowed


logger = logging.getLogger(__name__)


def create_realistic_review_outcome(
    severity: str = "low",
    diff_truncated: bool = False,
    schema_validated: bool = True,
    verdict: str = "request_changes",
    blocker_count: int = 1,
    suggestion_count: int = 1,
    **overrides
) -> Dict[str, Any]:
    """Create a realistic ReviewOutcome dict for integration testing.

    This mirrors the actual ReviewOutcome structure from B-6 Router Interface.
    """
    outcome = {
        "severity": severity,
        "diff_truncated": diff_truncated,
        "schema_validated": schema_validated,
        "verdict": verdict,
        "blocker_count": blocker_count,
        "suggestion_count": suggestion_count,
        "review_summary": "Code review completed with suggestions",
        "files_reviewed": ["src/utils.py", "src/main.py"],
    }
    outcome.update(overrides)
    return outcome


def create_realistic_suggestion(
    file_path: str = "src/utils.py",
    line_start: int = 10,
    line_end: int = 15,
    original_code: str = "def process_data(data):\n    return data",
    suggested_code: str = "def process_data(data: dict) -> dict:\n    return data",
    reason: str = "Add type hints for better code clarity",
    confidence: float = 0.9,
    category: str = "style",
) -> FixSuggestion:
    """Create a realistic FixSuggestion for integration testing."""
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


def create_mock_fixer_node_input(
    handoff: ReviewToFixHandoff,
    pr_number: int = 123,
    repo: str = "RC918/morningai",
    branch: str = "feature-branch",
) -> Dict[str, Any]:
    """Create a mock fixer_node input state from handoff.

    This simulates how the Router would prepare state for fixer_node.
    """
    return {
        "pr_number": pr_number,
        "repo": repo,
        "branch": branch,
        "fix_handoff": handoff.model_dump(),
        "trace_id": f"trace-{pr_number}",
        "review_outcome": {
            "severity": handoff.max_severity,
            "schema_validated": True,
            "diff_truncated": False,
        },
    }


class TestHappyPathIntegration:
    """Integration tests for happy path: eligible PR routed to fixer."""

    def test_full_flow_reviewer_to_fixer_routing(self):
        """Test complete flow: ReviewOutcome -> build_fix_handoff -> should_route_to_fixer.

        This is the primary happy path test verifying the entire integration.
        """
        review_outcome = create_realistic_review_outcome(
            severity="low",
            diff_truncated=False,
            schema_validated=True,
            verdict="request_changes",
        )

        assert is_autofix_allowed(review_outcome) is True

        suggestions = [
            create_realistic_suggestion(
                file_path="src/utils.py",
                confidence=0.9,
                category="style",
            ),
            create_realistic_suggestion(
                file_path="src/main.py",
                line_start=20,
                line_end=25,
                confidence=0.85,
                category="refactor",
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert handoff.max_severity == "low"
        assert len(handoff.suggestions) == 2
        assert handoff.total_lines_affected == 12

        assert should_route_to_fixer(handoff) is True

    def test_handoff_produces_valid_fixer_node_input(self):
        """Test that handoff produces valid input for fixer_node."""
        review_outcome = create_realistic_review_outcome()
        suggestions = [create_realistic_suggestion(confidence=0.9)]

        handoff = build_fix_handoff(
            pr_number=456,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        fixer_input = create_mock_fixer_node_input(handoff, pr_number=456)

        assert fixer_input["pr_number"] == 456
        assert "fix_handoff" in fixer_input
        assert fixer_input["fix_handoff"]["auto_fix_eligible"] is True
        assert len(fixer_input["fix_handoff"]["suggestions"]) == 1

        reconstructed = ReviewToFixHandoff(**fixer_input["fix_handoff"])
        assert reconstructed.pr_number == 456
        assert should_route_to_fixer(reconstructed) is True

    def test_multiple_high_confidence_suggestions_routed(self):
        """Test that multiple high-confidence suggestions are routed correctly."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(
                file_path=f"src/file{i}.py",
                line_start=i * 10,
                line_end=i * 10 + 5,
                confidence=0.85 + (i * 0.02),
                category="style",
            )
            for i in range(1, 4)
        ]

        handoff = build_fix_handoff(
            pr_number=789,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert len(handoff.suggestions) == 3
        assert all(s.confidence >= HIGH_CONFIDENCE_THRESHOLD for s in handoff.suggestions)
        assert should_route_to_fixer(handoff) is True

    def test_style_and_refactor_categories_eligible(self):
        """Test that style and refactor categories are eligible for auto-fix."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(category="style", confidence=0.9),
            create_realistic_suggestion(
                file_path="src/other.py",
                category="refactor",
                confidence=0.88,
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=101,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert handoff.max_severity == "low"
        assert should_route_to_fixer(handoff) is True


class TestSafetyPathIntegration:
    """Integration tests for safety path: high severity blocks routing."""

    def test_high_severity_blocks_routing(self):
        """Test that high severity in ReviewOutcome blocks routing to fixer."""
        review_outcome = create_realistic_review_outcome(
            severity="high",
            verdict="request_changes",
        )

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_realistic_suggestion(confidence=0.95)]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_critical_severity_blocks_routing(self):
        """Test that critical severity blocks routing even with high confidence."""
        review_outcome = create_realistic_review_outcome(
            severity="critical",
            verdict="request_changes",
        )

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_realistic_suggestion(confidence=0.99)]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_medium_severity_blocks_routing(self):
        """Test that medium severity blocks routing."""
        review_outcome = create_realistic_review_outcome(
            severity="medium",
        )

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_realistic_suggestion(confidence=0.9)]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_security_category_infers_high_severity(self):
        """Test that security category infers high severity when no review_outcome."""
        suggestions = [
            create_realistic_suggestion(
                category="security",
                confidence=0.95,
                reason="Fix SQL injection vulnerability",
            )
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=None,
        )

        assert handoff.max_severity == "high"
        assert should_route_to_fixer(handoff) is False

    def test_diff_truncated_blocks_routing(self):
        """Test that truncated diff blocks routing."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
            diff_truncated=True,
        )

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_realistic_suggestion(confidence=0.9)]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_schema_not_validated_blocks_routing(self):
        """Test that unvalidated schema blocks routing."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
            schema_validated=False,
        )

        assert is_autofix_allowed(review_outcome) is False

        suggestions = [create_realistic_suggestion(confidence=0.9)]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_hard_safety_check_overrides_auto_fix_eligible(self):
        """Test that hard safety check in should_route_to_fixer overrides auto_fix_eligible.

        Even if auto_fix_eligible is manually set to True, high severity should block.
        """
        suggestions = [create_realistic_suggestion(confidence=0.9)]

        handoff = ReviewToFixHandoff(
            review_id="test-review",
            pr_number=123,
            suggestions=suggestions,
            auto_fix_eligible=True,
            max_severity="high",
        )

        assert should_route_to_fixer(handoff) is False

    def test_bug_fix_category_infers_medium_severity(self):
        """Test that bug_fix category infers medium severity when no review_outcome."""
        suggestions = [
            create_realistic_suggestion(
                category="bug_fix",
                confidence=0.9,
                reason="Fix null pointer exception",
            )
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=None,
        )

        assert handoff.max_severity == "medium"


class TestEdgeCasesIntegration:
    """Integration tests for edge cases."""

    def test_empty_suggestions_not_routed(self):
        """Test that empty suggestions result in no routing."""
        review_outcome = create_realistic_review_outcome()

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=[],
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert handoff.suggestions == []
        assert should_route_to_fixer(handoff) is False

    def test_empty_handoff_helper(self):
        """Test build_empty_handoff for cases with no suggestions."""
        empty_handoff = build_empty_handoff(pr_number=123)

        assert empty_handoff["suggestions"] == []
        assert empty_handoff["auto_fix_eligible"] is False
        assert empty_handoff["requires_human_review"] is True
        assert empty_handoff["schema_version"] == 1

    def test_low_confidence_suggestions_not_routed(self):
        """Test that low confidence suggestions block auto-fix eligibility."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(confidence=0.5),
            create_realistic_suggestion(
                file_path="src/other.py",
                confidence=0.6,
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_mixed_confidence_with_one_high(self):
        """Test that at least one high-confidence suggestion enables routing."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(confidence=0.5),
            create_realistic_suggestion(
                file_path="src/other.py",
                confidence=0.9,
            ),
            create_realistic_suggestion(
                file_path="src/third.py",
                confidence=0.6,
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert should_route_to_fixer(handoff) is True

    def test_confidence_exactly_at_threshold(self):
        """Test confidence exactly at HIGH_CONFIDENCE_THRESHOLD."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(confidence=HIGH_CONFIDENCE_THRESHOLD),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert should_route_to_fixer(handoff) is True

    def test_confidence_just_below_threshold(self):
        """Test confidence just below HIGH_CONFIDENCE_THRESHOLD."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(confidence=HIGH_CONFIDENCE_THRESHOLD - 0.01),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_no_review_outcome_with_high_confidence(self):
        """Test behavior when review_outcome is None but suggestions have high confidence."""
        suggestions = [
            create_realistic_suggestion(
                category="style",
                confidence=0.9,
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=None,
        )

        assert handoff.auto_fix_eligible is False
        assert handoff.max_severity == "low"

    def test_single_line_suggestion(self):
        """Test suggestion affecting a single line."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(
                line_start=10,
                line_end=10,
                confidence=0.9,
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.total_lines_affected == 1
        assert handoff.auto_fix_eligible is True

    def test_large_multi_file_change(self):
        """Test large change spanning multiple files."""
        review_outcome = create_realistic_review_outcome()

        suggestions = [
            create_realistic_suggestion(
                file_path=f"src/module{i}/file.py",
                line_start=1,
                line_end=50,
                confidence=0.85,
            )
            for i in range(5)
        ]

        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.total_lines_affected == 250
        assert len(handoff.suggestions) == 5
        assert handoff.auto_fix_eligible is True


class TestRealisticWorkflowScenarios:
    """Integration tests with realistic workflow scenarios."""

    def test_typical_style_fix_workflow(self):
        """Test typical workflow for style fixes (most common case)."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
            verdict="request_changes",
            blocker_count=0,
            suggestion_count=2,
        )

        suggestions = [
            FixSuggestion(
                file_path="src/api/handlers.py",
                line_start=45,
                line_end=48,
                original_code="def get_user(id):\n    user = db.query(id)\n    return user",
                suggested_code="def get_user(user_id: int) -> User:\n    user = db.query(user_id)\n    return user",
                reason="Add type hints and rename parameter for clarity",
                confidence=0.92,
                category="style",
            ),
            FixSuggestion(
                file_path="src/api/handlers.py",
                line_start=60,
                line_end=62,
                original_code="def delete_user(id):\n    db.delete(id)",
                suggested_code="def delete_user(user_id: int) -> None:\n    db.delete(user_id)",
                reason="Add type hints and rename parameter for consistency",
                confidence=0.91,
                category="style",
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=1234,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert should_route_to_fixer(handoff) is True

        fixer_input = create_mock_fixer_node_input(handoff, pr_number=1234)
        assert fixer_input["fix_handoff"]["auto_fix_eligible"] is True

    def test_security_issue_blocked_workflow(self):
        """Test workflow where security issue blocks auto-fix."""
        review_outcome = create_realistic_review_outcome(
            severity="high",
            verdict="request_changes",
            blocker_count=1,
        )

        suggestions = [
            FixSuggestion(
                file_path="src/auth/login.py",
                line_start=30,
                line_end=35,
                original_code="password = request.form['password']",
                suggested_code="password = sanitize(request.form['password'])",
                reason="Sanitize user input to prevent injection",
                confidence=0.95,
                category="security",
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=5678,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
        assert should_route_to_fixer(handoff) is False

    def test_refactor_with_human_review_required(self):
        """Test refactor workflow where human review is explicitly required."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
        )

        suggestions = [
            create_realistic_suggestion(
                category="refactor",
                confidence=0.88,
                reason="Extract method for better readability",
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=9999,
            suggestions=suggestions,
            review_outcome=review_outcome,
            requires_human_review=True,
        )

        assert handoff.auto_fix_eligible is True
        assert handoff.requires_human_review is True
        assert should_route_to_fixer(handoff) is True

    def test_performance_fix_workflow(self):
        """Test workflow for performance fixes."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
        )

        suggestions = [
            FixSuggestion(
                file_path="src/data/processor.py",
                line_start=100,
                line_end=110,
                original_code="for item in items:\n    result.append(process(item))",
                suggested_code="result = [process(item) for item in items]",
                reason="Use list comprehension for better performance",
                confidence=0.87,
                category="performance",
            ),
        ]

        handoff = build_fix_handoff(
            pr_number=2468,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True
        assert handoff.max_severity == "low"
        assert should_route_to_fixer(handoff) is True


class TestHandoffSerializationIntegration:
    """Integration tests for handoff serialization/deserialization in workflow."""

    def test_handoff_survives_state_serialization(self):
        """Test that handoff survives being stored in and retrieved from state."""
        review_outcome = create_realistic_review_outcome()
        suggestions = [create_realistic_suggestion(confidence=0.9)]

        original_handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        state = {
            "pr_number": 123,
            "fix_handoff": original_handoff.model_dump(),
        }

        retrieved_dict = state["fix_handoff"]
        reconstructed = ReviewToFixHandoff(**retrieved_dict)

        assert reconstructed.pr_number == original_handoff.pr_number
        assert reconstructed.auto_fix_eligible == original_handoff.auto_fix_eligible
        assert reconstructed.max_severity == original_handoff.max_severity
        assert len(reconstructed.suggestions) == len(original_handoff.suggestions)
        assert should_route_to_fixer(reconstructed) == should_route_to_fixer(original_handoff)

    def test_handoff_json_roundtrip(self):
        """Test that handoff survives JSON serialization roundtrip."""
        import json

        review_outcome = create_realistic_review_outcome()
        suggestions = [
            create_realistic_suggestion(confidence=0.9),
            create_realistic_suggestion(
                file_path="src/other.py",
                confidence=0.85,
            ),
        ]

        original_handoff = build_fix_handoff(
            pr_number=456,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        json_str = json.dumps(original_handoff.model_dump())
        parsed_dict = json.loads(json_str)
        reconstructed = ReviewToFixHandoff(**parsed_dict)

        assert reconstructed.pr_number == original_handoff.pr_number
        assert reconstructed.schema_version == 1
        assert len(reconstructed.suggestions) == 2
        assert should_route_to_fixer(reconstructed) is True

    def test_suggestion_fields_preserved_through_serialization(self):
        """Test that all suggestion fields are preserved through serialization."""
        suggestion = FixSuggestion(
            file_path="src/special/file.py",
            line_start=42,
            line_end=50,
            original_code="original code here",
            suggested_code="suggested code here",
            reason="Detailed reason for the change",
            confidence=0.93,
            category="refactor",
        )

        handoff = build_fix_handoff(
            pr_number=789,
            suggestions=[suggestion],
        )

        handoff_dict = handoff.model_dump()
        reconstructed = ReviewToFixHandoff(**handoff_dict)

        s = reconstructed.suggestions[0]
        assert s.file_path == "src/special/file.py"
        assert s.line_start == 42
        assert s.line_end == 50
        assert s.original_code == "original code here"
        assert s.suggested_code == "suggested code here"
        assert s.reason == "Detailed reason for the change"
        assert s.confidence == 0.93
        assert s.category == "refactor"


class TestAutoFixGateAlignment:
    """Integration tests verifying alignment between autofix_gate and fix_handoff."""

    def test_gate_and_handoff_agree_on_all_eligible_conditions(self):
        """Test that gate and handoff agree when all conditions are met."""
        review_outcome = create_realistic_review_outcome(
            severity="low",
            diff_truncated=False,
            schema_validated=True,
        )

        gate_result = is_autofix_allowed(review_outcome)
        assert gate_result is True

        suggestions = [create_realistic_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is True

    def test_gate_and_handoff_agree_on_severity_rejection(self):
        """Test that gate and handoff agree on severity rejection."""
        for severity in ["medium", "high", "critical"]:
            review_outcome = create_realistic_review_outcome(severity=severity)

            gate_result = is_autofix_allowed(review_outcome)
            assert gate_result is False, f"Gate should reject {severity}"

            suggestions = [create_realistic_suggestion(confidence=0.9)]
            handoff = build_fix_handoff(
                pr_number=123,
                suggestions=suggestions,
                review_outcome=review_outcome,
            )

            assert handoff.auto_fix_eligible is False, f"Handoff should reject {severity}"

    def test_gate_and_handoff_agree_on_diff_truncated_rejection(self):
        """Test that gate and handoff agree on diff_truncated rejection."""
        review_outcome = create_realistic_review_outcome(diff_truncated=True)

        gate_result = is_autofix_allowed(review_outcome)
        assert gate_result is False

        suggestions = [create_realistic_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False

    def test_gate_and_handoff_agree_on_schema_validation_rejection(self):
        """Test that gate and handoff agree on schema_validated rejection."""
        review_outcome = create_realistic_review_outcome(schema_validated=False)

        gate_result = is_autofix_allowed(review_outcome)
        assert gate_result is False

        suggestions = [create_realistic_suggestion(confidence=0.9)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False

    def test_handoff_adds_confidence_check_beyond_gate(self):
        """Test that handoff adds confidence check that gate doesn't have."""
        review_outcome = create_realistic_review_outcome()

        gate_result = is_autofix_allowed(review_outcome)
        assert gate_result is True

        suggestions = [create_realistic_suggestion(confidence=0.5)]
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
        )

        assert handoff.auto_fix_eligible is False
