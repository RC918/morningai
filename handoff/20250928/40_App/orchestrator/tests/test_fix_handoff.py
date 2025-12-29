"""
Tests for ReviewToFixHandoff Schema - EPIC D Interface Definition

Issue #3225: Review to Fix Handoff Schema - EPIC D Interface Definition

Tests cover:
1. FixSuggestion model validation
2. ReviewToFixHandoff model validation
3. build_fix_handoff() helper function
4. should_route_to_fixer() routing logic
5. Edge cases and error handling
"""
import pytest
from pydantic import ValidationError

from core.routing.fix_handoff import (
    FixSuggestion,
    ReviewToFixHandoff,
    build_fix_handoff,
    should_route_to_fixer,
    build_empty_handoff,
    _compute_total_lines,
    _determine_max_severity,
    _is_auto_fix_eligible,
)


class TestFixSuggestion:
    """Tests for FixSuggestion model."""

    def test_valid_suggestion(self):
        """Test creating a valid FixSuggestion."""
        suggestion = FixSuggestion(
            file_path="src/utils.py",
            line_start=10,
            line_end=15,
            original_code="def foo():",
            suggested_code="def foo() -> None:",
            reason="Add return type annotation",
            confidence=0.9,
            category="style"
        )
        assert suggestion.file_path == "src/utils.py"
        assert suggestion.line_start == 10
        assert suggestion.line_end == 15
        assert suggestion.confidence == 0.9
        assert suggestion.category == "style"

    def test_empty_file_path_raises(self):
        """Test that empty file_path raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FixSuggestion(
                file_path="",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=0.9,
                category="style"
            )
        assert "file_path cannot be empty" in str(exc_info.value)

    def test_empty_reason_raises(self):
        """Test that empty reason raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="",
                confidence=0.9,
                category="style"
            )
        assert "reason cannot be empty" in str(exc_info.value)

    def test_line_end_less_than_line_start_raises(self):
        """Test that line_end < line_start raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FixSuggestion(
                file_path="src/utils.py",
                line_start=15,
                line_end=10,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=0.9,
                category="style"
            )
        assert "line_end" in str(exc_info.value)

    def test_confidence_out_of_range_raises(self):
        """Test that confidence outside [0, 1] raises ValidationError."""
        with pytest.raises(ValidationError):
            FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=1.5,
                category="style"
            )

    def test_invalid_category_raises(self):
        """Test that invalid category raises ValidationError."""
        with pytest.raises(ValidationError):
            FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=0.9,
                category="invalid_category"
            )

    def test_all_categories_valid(self):
        """Test all valid categories."""
        categories = ["bug_fix", "style", "refactor", "security", "performance"]
        for category in categories:
            suggestion = FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Test",
                confidence=0.9,
                category=category
            )
            assert suggestion.category == category

    def test_immutable(self):
        """Test that FixSuggestion is immutable."""
        suggestion = FixSuggestion(
            file_path="src/utils.py",
            line_start=10,
            line_end=15,
            original_code="def foo():",
            suggested_code="def foo() -> None:",
            reason="Test",
            confidence=0.9,
            category="style"
        )
        with pytest.raises(ValidationError):
            suggestion.file_path = "other.py"


class TestReviewToFixHandoff:
    """Tests for ReviewToFixHandoff model."""

    def test_valid_handoff(self):
        """Test creating a valid ReviewToFixHandoff."""
        suggestion = FixSuggestion(
            file_path="src/utils.py",
            line_start=10,
            line_end=15,
            original_code="def foo():",
            suggested_code="def foo() -> None:",
            reason="Add return type annotation",
            confidence=0.9,
            category="style"
        )
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=[suggestion],
            auto_fix_eligible=True,
            requires_human_review=False,
            total_lines_affected=6,
            max_severity="low"
        )
        assert handoff.review_id == "review-abc123"
        assert handoff.pr_number == 123
        assert len(handoff.suggestions) == 1
        assert handoff.auto_fix_eligible is True
        assert handoff.requires_human_review is False
        assert handoff.total_lines_affected == 6
        assert handoff.max_severity == "low"
        assert handoff.schema_version == 1

    def test_empty_review_id_raises(self):
        """Test that empty review_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewToFixHandoff(
                review_id="",
                pr_number=123,
                suggestions=[]
            )
        assert "review_id cannot be empty" in str(exc_info.value)

    def test_negative_pr_number_raises(self):
        """Test that negative pr_number raises ValidationError."""
        with pytest.raises(ValidationError):
            ReviewToFixHandoff(
                review_id="review-abc123",
                pr_number=0,
                suggestions=[]
            )

    def test_default_values(self):
        """Test default values for optional fields."""
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123
        )
        assert handoff.suggestions == []
        assert handoff.auto_fix_eligible is False
        assert handoff.requires_human_review is True
        assert handoff.total_lines_affected == 0
        assert handoff.max_severity == "low"

    def test_get_high_confidence_suggestions(self):
        """Test get_high_confidence_suggestions method."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.5, category="style"
            ),
            FixSuggestion(
                file_path="c.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.85, category="style"
            ),
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions
        )
        high_conf = handoff.get_high_confidence_suggestions(threshold=0.8)
        assert len(high_conf) == 2
        assert all(s.confidence >= 0.8 for s in high_conf)

    def test_get_suggestions_by_category(self):
        """Test get_suggestions_by_category method."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="bug_fix"
            ),
            FixSuggestion(
                file_path="c.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            ),
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions
        )
        style_suggestions = handoff.get_suggestions_by_category("style")
        assert len(style_suggestions) == 2
        assert all(s.category == "style" for s in style_suggestions)


class TestBuildFixHandoff:
    """Tests for build_fix_handoff helper function."""

    def test_build_with_suggestions(self):
        """Test building handoff with suggestions."""
        suggestions = [
            FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=0.9,
                category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        assert handoff.pr_number == 123
        assert len(handoff.suggestions) == 1
        assert handoff.total_lines_affected == 6
        assert handoff.auto_fix_eligible is True
        assert handoff.review_id.startswith("review-")

    def test_build_with_custom_review_id(self):
        """Test building handoff with custom review_id."""
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=[],
            review_id="custom-review-id"
        )
        assert handoff.review_id == "custom-review-id"

    def test_build_empty_suggestions(self):
        """Test building handoff with no suggestions."""
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=[]
        )
        assert handoff.suggestions == []
        assert handoff.auto_fix_eligible is False
        assert handoff.total_lines_affected == 0

    def test_auto_fix_eligible_requires_low_severity(self):
        """Test that auto_fix_eligible requires low severity."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        review_outcome = {
            "severity": "medium",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        assert handoff.auto_fix_eligible is False

    def test_auto_fix_eligible_requires_schema_validated(self):
        """Test that auto_fix_eligible requires schema_validated."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": False
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        assert handoff.auto_fix_eligible is False

    def test_auto_fix_eligible_requires_no_diff_truncated(self):
        """Test that auto_fix_eligible requires diff_truncated=False."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": True,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        assert handoff.auto_fix_eligible is False

    def test_requires_human_review_default_true(self):
        """Test that requires_human_review defaults to True for safety."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="bug_fix"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # Default is True for safety - caller must explicitly set False
        assert handoff.requires_human_review is True

    def test_requires_human_review_can_be_set_false(self):
        """Test that requires_human_review can be explicitly set to False."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        # Caller (Router) explicitly sets requires_human_review=False
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome,
            requires_human_review=False
        )
        assert handoff.requires_human_review is False


class TestShouldRouteToFixer:
    """Tests for should_route_to_fixer routing logic.

    Note: should_route_to_fixer trusts the auto_fix_eligible flag and only
    adds a hard safety check for max_severity. High-confidence suggestion
    check is already part of auto_fix_eligible computation.
    """

    def test_route_when_eligible(self):
        """Test routing when all conditions are met."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions,
            auto_fix_eligible=True,
            max_severity="low"
        )
        assert should_route_to_fixer(handoff) is True

    def test_skip_when_not_eligible(self):
        """Test skipping when auto_fix_eligible is False."""
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=[],
            auto_fix_eligible=False
        )
        assert should_route_to_fixer(handoff) is False

    def test_skip_when_high_severity(self):
        """Test skipping when max_severity is high (hard safety check)."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="security"
            )
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions,
            auto_fix_eligible=True,
            max_severity="high"
        )
        assert should_route_to_fixer(handoff) is False

    def test_skip_when_critical_severity(self):
        """Test skipping when max_severity is critical (hard safety check)."""
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=[],
            auto_fix_eligible=True,
            max_severity="critical"
        )
        assert should_route_to_fixer(handoff) is False

    def test_route_trusts_auto_fix_eligible(self):
        """Test that should_route_to_fixer trusts auto_fix_eligible flag.

        High-confidence check is already part of auto_fix_eligible computation
        in _is_auto_fix_eligible(), so we don't duplicate it here.
        """
        # Even with low-confidence suggestions, if auto_fix_eligible is True,
        # we trust it (the eligibility check already validated confidence)
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.5, category="style"
            )
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions,
            auto_fix_eligible=True,  # Trusted - already validated
            max_severity="low"
        )
        # Routes because we trust auto_fix_eligible
        assert should_route_to_fixer(handoff) is True


class TestBuildEmptyHandoff:
    """Tests for build_empty_handoff helper function."""

    def test_build_empty_handoff(self):
        """Test building empty handoff dict."""
        result = build_empty_handoff(pr_number=123)
        assert result["schema_version"] == 1
        assert result["pr_number"] == 123
        assert result["suggestions"] == []
        assert result["auto_fix_eligible"] is False
        assert result["requires_human_review"] is True
        assert result["total_lines_affected"] == 0
        assert result["max_severity"] == "low"
        assert result["review_id"].startswith("review-")

    def test_build_empty_handoff_with_custom_id(self):
        """Test building empty handoff with custom review_id."""
        result = build_empty_handoff(pr_number=123, review_id="custom-id")
        assert result["review_id"] == "custom-id"


class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_compute_total_lines(self):
        """Test _compute_total_lines calculation."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=5,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=10, line_end=15,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            ),
        ]
        total = _compute_total_lines(suggestions)
        assert total == 11  # (5-1+1) + (15-10+1) = 5 + 6 = 11

    def test_determine_max_severity_from_review_outcome(self):
        """Test _determine_max_severity uses review_outcome."""
        review_outcome = {"severity": "high"}
        severity = _determine_max_severity([], review_outcome)
        assert severity == "high"

    def test_determine_max_severity_from_security_category(self):
        """Test _determine_max_severity infers high from security."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="security"
            )
        ]
        severity = _determine_max_severity(suggestions, None)
        assert severity == "high"

    def test_determine_max_severity_from_bug_fix_category(self):
        """Test _determine_max_severity infers medium from bug_fix."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="bug_fix"
            )
        ]
        severity = _determine_max_severity(suggestions, None)
        assert severity == "medium"

    def test_is_auto_fix_eligible_all_conditions(self):
        """Test _is_auto_fix_eligible with all conditions met."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.9, category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        result = _is_auto_fix_eligible(review_outcome, suggestions, "low")
        assert result is True

    def test_is_auto_fix_eligible_no_review_outcome(self):
        """Test _is_auto_fix_eligible with no review_outcome."""
        result = _is_auto_fix_eligible(None, [], "low")
        assert result is False


class TestConfidenceThresholdBoundary:
    """Boundary tests for HIGH_CONFIDENCE_THRESHOLD (0.8).

    These tests verify edge cases around the confidence threshold to ensure
    the auto-fix eligibility logic handles boundary values correctly.
    """

    def test_confidence_exactly_at_threshold(self):
        """Test suggestion with confidence exactly at 0.8 threshold."""
        from core.routing.fix_handoff import HIGH_CONFIDENCE_THRESHOLD
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=HIGH_CONFIDENCE_THRESHOLD,  # exactly 0.8
                category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # Confidence exactly at threshold should be eligible
        assert handoff.auto_fix_eligible is True

    def test_confidence_just_below_threshold(self):
        """Test suggestion with confidence just below 0.8 threshold (0.79)."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.79,  # just below 0.8
                category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # Confidence below threshold should NOT be eligible
        assert handoff.auto_fix_eligible is False

    def test_confidence_just_above_threshold(self):
        """Test suggestion with confidence just above 0.8 threshold (0.81)."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.81,  # just above 0.8
                category="style"
            )
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # Confidence above threshold should be eligible
        assert handoff.auto_fix_eligible is True

    def test_get_high_confidence_at_threshold(self):
        """Test get_high_confidence_suggestions with confidence exactly at threshold."""
        from core.routing.fix_handoff import HIGH_CONFIDENCE_THRESHOLD
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=HIGH_CONFIDENCE_THRESHOLD,  # exactly 0.8
                category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.79,  # just below
                category="style"
            ),
        ]
        handoff = ReviewToFixHandoff(
            review_id="review-abc123",
            pr_number=123,
            suggestions=suggestions
        )
        # Default threshold is HIGH_CONFIDENCE_THRESHOLD (0.8)
        high_conf = handoff.get_high_confidence_suggestions()
        assert len(high_conf) == 1
        assert high_conf[0].confidence == HIGH_CONFIDENCE_THRESHOLD

    def test_mixed_confidence_only_high_counted(self):
        """Test that only high-confidence suggestions count for eligibility."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.5,  # low confidence
                category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.6,  # low confidence
                category="style"
            ),
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # No high-confidence suggestions, should NOT be eligible
        assert handoff.auto_fix_eligible is False

    def test_at_least_one_high_confidence_required(self):
        """Test that at least one high-confidence suggestion is required."""
        suggestions = [
            FixSuggestion(
                file_path="a.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.5,  # low confidence
                category="style"
            ),
            FixSuggestion(
                file_path="b.py", line_start=1, line_end=1,
                original_code="x", suggested_code="y",
                reason="test", confidence=0.85,  # high confidence
                category="style"
            ),
        ]
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=suggestions,
            review_outcome=review_outcome
        )
        # At least one high-confidence suggestion, should be eligible
        assert handoff.auto_fix_eligible is True
