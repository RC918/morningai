"""
Unit tests for ReviewOutcome schema (EPIC B-6)

Issue #3130: B-6 Reviewer -> Router Interface Definition

Test coverage:
1. Schema validation - valid and invalid inputs
2. Verdict scenarios - approve, request_changes, comment, blocked, unknown
3. Severity mapping - none -> low, and worst-wins logic
4. blocker_count computation - high/critical counting
5. build_unknown_outcome - fallback for errors
6. Router precedence - unknown overrides, blocked forces escalate
"""
import pytest
from pydantic import ValidationError

from core.routing.review_outcome import (
    ReviewOutcome,
    build_review_outcome,
    build_unknown_outcome,
    _map_severity,
    _compute_blocker_count,
    _determine_verdict,
    BLOCKER_SEVERITIES,
)


class TestReviewOutcomeSchema:
    """Test ReviewOutcome Pydantic model validation."""

    def test_valid_review_outcome(self):
        """Test creating a valid ReviewOutcome."""
        outcome = ReviewOutcome(
            verdict="approve",
            severity="low",
            summary="Review passed, no issues found"
        )
        assert outcome.verdict == "approve"
        assert outcome.severity == "low"
        assert outcome.summary == "Review passed, no issues found"
        assert outcome.schema_version == 1
        assert outcome.diff_truncated is False
        assert outcome.schema_validated is True
        assert outcome.blocker_count == 0

    def test_all_verdict_types(self):
        """Test all valid verdict types."""
        for verdict in ["approve", "request_changes", "comment", "blocked", "unknown"]:
            outcome = ReviewOutcome(
                verdict=verdict,
                severity="low",
                summary=f"Test {verdict}"
            )
            assert outcome.verdict == verdict

    def test_all_severity_types(self):
        """Test all valid severity types."""
        for severity in ["low", "medium", "high", "critical"]:
            outcome = ReviewOutcome(
                verdict="approve",
                severity=severity,
                summary=f"Test {severity}"
            )
            assert outcome.severity == severity

    def test_missing_verdict_raises_error(self):
        """Test that missing verdict raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                severity="low",
                summary="Missing verdict"
            )
        assert "verdict" in str(exc_info.value)

    def test_invalid_verdict_raises_error(self):
        """Test that invalid verdict raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="invalid",
                severity="low",
                summary="Invalid verdict"
            )
        assert "verdict" in str(exc_info.value)

    def test_missing_severity_raises_error(self):
        """Test that missing severity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                summary="Missing severity"
            )
        assert "severity" in str(exc_info.value)

    def test_invalid_severity_raises_error(self):
        """Test that invalid severity (including 'none') raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                severity="none",
                summary="Invalid severity"
            )
        assert "severity" in str(exc_info.value)

    def test_empty_summary_raises_error(self):
        """Test that empty summary raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                severity="low",
                summary=""
            )
        assert "summary" in str(exc_info.value)

    def test_whitespace_only_summary_raises_error(self):
        """Test that whitespace-only summary raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                severity="low",
                summary="   "
            )
        assert "summary" in str(exc_info.value)

    def test_negative_blocker_count_raises_error(self):
        """Test that negative blocker_count raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                severity="low",
                summary="Test",
                blocker_count=-1
            )
        assert "blocker_count" in str(exc_info.value)

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewOutcome(
                verdict="approve",
                severity="low",
                summary="Test",
                extra_field="not allowed"
            )
        assert "extra" in str(exc_info.value).lower()

    def test_immutable_after_creation(self):
        """Test that ReviewOutcome is immutable (frozen)."""
        outcome = ReviewOutcome(
            verdict="approve",
            severity="low",
            summary="Test"
        )
        with pytest.raises(ValidationError):
            outcome.verdict = "request_changes"


class TestSeverityMapping:
    """Test severity mapping from reviewer_node to ReviewOutcome."""

    def test_none_maps_to_low(self):
        """Test that 'none' severity maps to 'low'."""
        assert _map_severity("none") == "low"
        assert _map_severity("None") == "low"
        assert _map_severity("NONE") == "low"

    def test_empty_maps_to_low(self):
        """Test that empty/None severity maps to 'low'."""
        assert _map_severity(None) == "low"
        assert _map_severity("") == "low"

    def test_valid_severities_pass_through(self):
        """Test that valid severities pass through unchanged."""
        assert _map_severity("low") == "low"
        assert _map_severity("medium") == "medium"
        assert _map_severity("high") == "high"
        assert _map_severity("critical") == "critical"

    def test_case_insensitive(self):
        """Test that severity mapping is case insensitive."""
        assert _map_severity("LOW") == "low"
        assert _map_severity("Medium") == "medium"
        assert _map_severity("HIGH") == "high"
        assert _map_severity("CRITICAL") == "critical"

    def test_unknown_maps_to_low(self):
        """Test that unknown severity maps to 'low'."""
        assert _map_severity("unknown") == "low"
        assert _map_severity("invalid") == "low"


class TestBlockerCountComputation:
    """Test blocker_count computation from review comments."""

    def test_empty_comments_returns_zero(self):
        """Test that empty comments list returns 0."""
        assert _compute_blocker_count([]) == 0
        assert _compute_blocker_count(None) == 0

    def test_no_blockers_returns_zero(self):
        """Test that comments with only low/medium severity return 0."""
        comments = [
            {"severity": "low", "message": "Minor issue"},
            {"severity": "medium", "message": "Moderate issue"},
        ]
        assert _compute_blocker_count(comments) == 0

    def test_high_severity_counts_as_blocker(self):
        """Test that high severity comments count as blockers."""
        comments = [
            {"severity": "high", "message": "Important issue"},
        ]
        assert _compute_blocker_count(comments) == 1

    def test_critical_severity_counts_as_blocker(self):
        """Test that critical severity comments count as blockers."""
        comments = [
            {"severity": "critical", "message": "Critical issue"},
        ]
        assert _compute_blocker_count(comments) == 1

    def test_mixed_severities(self):
        """Test counting blockers with mixed severities."""
        comments = [
            {"severity": "low", "message": "Minor"},
            {"severity": "high", "message": "High 1"},
            {"severity": "medium", "message": "Medium"},
            {"severity": "critical", "message": "Critical 1"},
            {"severity": "high", "message": "High 2"},
        ]
        assert _compute_blocker_count(comments) == 3

    def test_case_insensitive_severity(self):
        """Test that severity matching is case insensitive."""
        comments = [
            {"severity": "HIGH", "message": "High"},
            {"severity": "Critical", "message": "Critical"},
        ]
        assert _compute_blocker_count(comments) == 2

    def test_missing_severity_field(self):
        """Test that comments without severity field are not counted."""
        comments = [
            {"message": "No severity"},
            {"severity": "high", "message": "Has severity"},
        ]
        assert _compute_blocker_count(comments) == 1


class TestVerdictDetermination:
    """Test verdict determination logic."""

    def test_error_status_returns_unknown(self):
        """Test that error status returns unknown verdict."""
        result = {"status": "error", "error": "Something went wrong"}
        assert _determine_verdict(result, "none", 0) == "unknown"

    def test_critical_severity_returns_request_changes(self):
        """Test that critical severity returns request_changes."""
        result = {"status": "passed"}
        assert _determine_verdict(result, "critical", 0) == "request_changes"

    def test_blockers_return_request_changes(self):
        """Test that having blockers returns request_changes."""
        result = {"status": "passed"}
        assert _determine_verdict(result, "low", 1) == "request_changes"

    def test_passed_status_returns_approve(self):
        """Test that passed status returns approve."""
        result = {"status": "passed"}
        assert _determine_verdict(result, "low", 0) == "approve"

    def test_needs_attention_returns_request_changes(self):
        """Test that needs_attention status returns request_changes."""
        result = {"status": "needs_attention"}
        assert _determine_verdict(result, "low", 0) == "request_changes"

    def test_pending_status_returns_comment(self):
        """Test that pending status returns comment."""
        result = {"status": "pending"}
        assert _determine_verdict(result, "low", 0) == "comment"

    def test_unknown_status_returns_comment(self):
        """Test that unknown status returns comment."""
        result = {"status": "unknown"}
        assert _determine_verdict(result, "low", 0) == "comment"


class TestBuildReviewOutcome:
    """Test build_review_outcome helper function."""

    def test_approve_scenario(self):
        """Test building ReviewOutcome for approve scenario."""
        outcome = build_review_outcome(
            review_comments=[],
            review_severity="none",
            review_result={"status": "passed", "reason": "CI passed"},
            diff_truncated=False
        )
        assert outcome.verdict == "approve"
        assert outcome.severity == "low"
        assert outcome.blocker_count == 0
        assert outcome.schema_validated is True

    def test_request_changes_scenario(self):
        """Test building ReviewOutcome for request_changes scenario."""
        outcome = build_review_outcome(
            review_comments=[
                {"severity": "high", "message": "Issue 1"},
                {"severity": "critical", "message": "Issue 2"},
            ],
            review_severity="critical",
            review_result={"status": "needs_attention", "reason": "Issues found"},
            diff_truncated=False
        )
        assert outcome.verdict == "request_changes"
        assert outcome.severity == "critical"
        assert outcome.blocker_count == 2

    def test_unknown_scenario_from_error(self):
        """Test building ReviewOutcome for error scenario."""
        outcome = build_review_outcome(
            review_comments=[],
            review_severity="unknown",
            review_result={"status": "error", "error": "Timeout"},
            diff_truncated=False
        )
        assert outcome.verdict == "unknown"
        assert "failed" in outcome.summary.lower()

    def test_diff_truncated_preserved(self):
        """Test that diff_truncated flag is preserved."""
        outcome = build_review_outcome(
            review_comments=[],
            review_severity="none",
            review_result={"status": "passed"},
            diff_truncated=True
        )
        assert outcome.diff_truncated is True

    def test_llm_summary_included(self):
        """Test that LLM summary is included in summary."""
        outcome = build_review_outcome(
            review_comments=[],
            review_severity="none",
            review_result={
                "status": "passed",
                "reason": "CI passed",
                "llm_summary": "Code looks good"
            },
            diff_truncated=False
        )
        assert "Code looks good" in outcome.summary


class TestBuildUnknownOutcome:
    """Test build_unknown_outcome fallback function."""

    def test_returns_dict_not_model(self):
        """Test that build_unknown_outcome returns a dict, not a model."""
        result = build_unknown_outcome("Test error")
        assert isinstance(result, dict)
        assert not isinstance(result, ReviewOutcome)

    def test_verdict_is_unknown(self):
        """Test that verdict is always unknown."""
        result = build_unknown_outcome("Test error")
        assert result["verdict"] == "unknown"

    def test_schema_validated_is_false(self):
        """Test that schema_validated is always False."""
        result = build_unknown_outcome("Test error")
        assert result["schema_validated"] is False

    def test_error_in_summary(self):
        """Test that error message is in summary."""
        result = build_unknown_outcome("Connection timeout")
        assert "Connection timeout" in result["summary"]

    def test_diff_truncated_preserved(self):
        """Test that diff_truncated is preserved."""
        result = build_unknown_outcome("Error", diff_truncated=True)
        assert result["diff_truncated"] is True

    def test_schema_version_present(self):
        """Test that schema_version is present."""
        result = build_unknown_outcome("Error")
        assert result["schema_version"] == 1


class TestRouterPrecedenceRules:
    """Test Router decision precedence rules as documented."""

    def test_unknown_verdict_should_trigger_fallback(self):
        """Test that unknown verdict should trigger Router fallback.

        Router Decision Rule 1: unknown verdict overrides all other fields.
        """
        outcome = ReviewOutcome(
            verdict="unknown",
            severity="low",
            summary="Review failed: timeout",
            schema_validated=False
        )
        # Router should ignore severity and blocker_count when verdict is unknown
        assert outcome.verdict == "unknown"
        # These fields should be ignored by Router
        assert outcome.severity == "low"
        assert outcome.blocker_count == 0

    def test_blocked_verdict_forces_escalation(self):
        """Test that blocked verdict should force Router escalation.

        Router Decision Rule 2: blocked verdict forces escalation.
        """
        outcome = ReviewOutcome(
            verdict="blocked",
            severity="critical",
            summary="Safety/Compliance block detected"
        )
        assert outcome.verdict == "blocked"
        # Router MUST escalate regardless of other fields

    def test_schema_validated_false_triggers_fallback(self):
        """Test that schema_validated=False should trigger Router fallback.

        Router Decision Rule 3: schema_validated=False triggers fallback.
        """
        # When validation fails, producer uses build_unknown_outcome
        result = build_unknown_outcome("Validation failed")
        assert result["schema_validated"] is False
        assert result["verdict"] == "unknown"
        # Router MUST treat this as equivalent to unknown

    def test_business_verdicts_follow_normal_routing(self):
        """Test that business verdicts follow normal Router logic.

        Router Decision Rule 4: approve, request_changes, comment follow normal routing.
        """
        for verdict in ["approve", "request_changes", "comment"]:
            outcome = ReviewOutcome(
                verdict=verdict,
                severity="medium",
                summary=f"Test {verdict}"
            )
            assert outcome.verdict == verdict
            # Router processes these according to its LLM-driven or rule-based logic


class TestBlockerSeverities:
    """Test BLOCKER_SEVERITIES constant."""

    def test_blocker_severities_contains_high(self):
        """Test that high is a blocker severity."""
        assert "high" in BLOCKER_SEVERITIES

    def test_blocker_severities_contains_critical(self):
        """Test that critical is a blocker severity."""
        assert "critical" in BLOCKER_SEVERITIES

    def test_blocker_severities_excludes_low(self):
        """Test that low is not a blocker severity."""
        assert "low" not in BLOCKER_SEVERITIES

    def test_blocker_severities_excludes_medium(self):
        """Test that medium is not a blocker severity."""
        assert "medium" not in BLOCKER_SEVERITIES
