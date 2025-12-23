"""
Unit tests for the Reviewer Stability Scorecard tool.

These tests use mocked API responses to test the scorecard logic
without requiring a real GitHub token.
"""

import os
import sys

import pytest
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reviewer_stability_scorecard import (  # noqa: E402
    MORNINGAI_REVIEW_MARKER,
    DUPLICATE_PENALTY,
    SLOW_REVIEW_PENALTY,
    SLOW_REVIEW_THRESHOLD_SECONDS,
    STATUS_GOOD_THRESHOLD,
    STATUS_FAIR_THRESHOLD,
    EXCELLENT_COVERAGE_THRESHOLD,
    STATUS_SEVERITY,
    is_morningai_review,
    analyze_pr_reviews,
    compute_duplicates,
    compute_latency_stats,
    compute_health_score,
    check_regression,
    check_rate_limit,
    RateLimitError,
)


class TestIsMorningaiReview:
    """Tests for the is_morningai_review function."""

    def test_review_with_marker_returns_true(self):
        """Review containing the marker should be identified as MorningAI review."""
        review = {
            "body": f"## MorningAI Code Review\n\n{MORNINGAI_REVIEW_MARKER}\n\nSome feedback"
        }
        assert is_morningai_review(review) is True

    def test_review_without_marker_returns_false(self):
        """Review without the marker should not be identified as MorningAI review."""
        review = {"body": "This is a regular human review"}
        assert is_morningai_review(review) is False

    def test_review_with_empty_body_returns_false(self):
        """Review with empty body should not be identified as MorningAI review."""
        review = {"body": ""}
        assert is_morningai_review(review) is False

    def test_review_with_none_body_returns_false(self):
        """Review with None body should not be identified as MorningAI review."""
        review = {"body": None}
        assert is_morningai_review(review) is False

    def test_review_missing_body_key_returns_false(self):
        """Review missing body key should not be identified as MorningAI review."""
        review = {}
        assert is_morningai_review(review) is False

    def test_marker_at_start_of_body(self):
        """Marker at the start of body should be detected."""
        review = {"body": f"{MORNINGAI_REVIEW_MARKER}\nReview content"}
        assert is_morningai_review(review) is True

    def test_marker_at_end_of_body(self):
        """Marker at the end of body should be detected."""
        review = {"body": f"Review content\n{MORNINGAI_REVIEW_MARKER}"}
        assert is_morningai_review(review) is True


class TestAnalyzePrReviews:
    """Tests for the analyze_pr_reviews function."""

    def test_pr_with_morningai_reviews(self):
        """PR with MorningAI reviews should be correctly analyzed."""
        pr = {
            "number": 123,
            "title": "Test PR",
            "state": "open",
            "head": {"sha": "abc123def456"},
            "created_at": "2025-12-20T10:00:00Z",
        }
        reviews = [
            {
                "id": 1,
                "body": f"## Review\n{MORNINGAI_REVIEW_MARKER}",
                "commit_id": "abc123def456",
                "submitted_at": "2025-12-20T10:05:00Z",
            },
            {
                "id": 2,
                "body": "Human review",
                "commit_id": "abc123def456",
                "submitted_at": "2025-12-20T10:10:00Z",
            },
        ]

        pr_info, morningai_reviews, latencies = analyze_pr_reviews(pr, reviews)

        assert pr_info["number"] == 123
        assert pr_info["morningai_reviews"] == 1
        assert pr_info["total_reviews"] == 2
        assert len(morningai_reviews) == 1
        assert len(latencies) == 1
        assert latencies[0] == 300.0  # 5 minutes

    def test_pr_without_morningai_reviews(self):
        """PR without MorningAI reviews should return empty lists."""
        pr = {
            "number": 456,
            "title": "Another PR",
            "state": "closed",
            "head": {"sha": "xyz789"},
            "created_at": "2025-12-20T10:00:00Z",
        }
        reviews = [
            {"id": 1, "body": "Human review", "commit_id": "xyz789"},
        ]

        pr_info, morningai_reviews, latencies = analyze_pr_reviews(pr, reviews)

        assert pr_info["morningai_reviews"] == 0
        assert len(morningai_reviews) == 0
        assert len(latencies) == 0

    def test_review_with_missing_commit_id(self):
        """Reviews with missing commit_id should not be added to commit tracking."""
        pr = {
            "number": 789,
            "title": "PR with missing commit_id",
            "state": "open",
            "head": {"sha": "def456"},
            "created_at": "2025-12-20T10:00:00Z",
        }
        reviews = [
            {
                "id": 1,
                "body": f"{MORNINGAI_REVIEW_MARKER}",
                "commit_id": None,
                "submitted_at": "2025-12-20T10:05:00Z",
            },
        ]

        pr_info, morningai_reviews, latencies = analyze_pr_reviews(pr, reviews)

        assert pr_info["morningai_reviews"] == 1
        assert len(pr_info["morningai_review_commits"]) == 0
        assert len(latencies) == 1


class TestComputeDuplicates:
    """Tests for the compute_duplicates function."""

    def test_no_duplicates(self):
        """No duplicates when each commit has one review."""
        reviews_by_commit = {
            "abc123": [{"pr_number": 1, "review_id": 100}],
            "def456": [{"pr_number": 2, "review_id": 200}],
        }

        count, commits = compute_duplicates(reviews_by_commit)

        assert count == 0
        assert len(commits) == 0

    def test_single_duplicate(self):
        """Single commit with two reviews should count as one duplicate."""
        reviews_by_commit = {
            "abc123": [
                {"pr_number": 1, "review_id": 100},
                {"pr_number": 1, "review_id": 101},
            ],
        }

        count, commits = compute_duplicates(reviews_by_commit)

        assert count == 1
        assert len(commits) == 1
        assert commits[0]["review_count"] == 2

    def test_multiple_duplicates(self):
        """Multiple commits with duplicates should be counted correctly."""
        reviews_by_commit = {
            "abc123": [
                {"pr_number": 1, "review_id": 100},
                {"pr_number": 1, "review_id": 101},
                {"pr_number": 1, "review_id": 102},
            ],
            "def456": [
                {"pr_number": 2, "review_id": 200},
                {"pr_number": 2, "review_id": 201},
            ],
        }

        count, commits = compute_duplicates(reviews_by_commit)

        assert count == 3  # 2 extra for abc123, 1 extra for def456
        assert len(commits) == 2


class TestComputeLatencyStats:
    """Tests for the compute_latency_stats function."""

    def test_empty_latencies(self):
        """Empty latencies should return None values."""
        stats = compute_latency_stats([])

        assert stats["avg_latency_seconds"] is None
        assert stats["min_latency_seconds"] is None
        assert stats["max_latency_seconds"] is None

    def test_single_latency(self):
        """Single latency should be used for all stats."""
        stats = compute_latency_stats([120.0])

        assert stats["avg_latency_seconds"] == 120.0
        assert stats["min_latency_seconds"] == 120.0
        assert stats["max_latency_seconds"] == 120.0

    def test_multiple_latencies(self):
        """Multiple latencies should be correctly aggregated."""
        stats = compute_latency_stats([60.0, 120.0, 180.0])

        assert stats["avg_latency_seconds"] == 120.0
        assert stats["min_latency_seconds"] == 60.0
        assert stats["max_latency_seconds"] == 180.0


class TestComputeHealthScore:
    """Tests for the compute_health_score function."""

    def test_excellent_status(self):
        """Zero duplicates and high coverage should result in EXCELLENT status."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=100.0,
            avg_latency_seconds=60.0,
        )

        assert score == 0
        assert status == "EXCELLENT"

    def test_excellent_status_at_threshold(self):
        """Coverage at exactly threshold should result in EXCELLENT status."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=EXCELLENT_COVERAGE_THRESHOLD,
            avg_latency_seconds=60.0,
        )

        assert score == 0
        assert status == "EXCELLENT"

    def test_low_coverage_not_excellent(self):
        """Low coverage should NOT result in EXCELLENT even with score=0."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=49.0,
            avg_latency_seconds=60.0,
        )

        assert score == 0
        assert status == "GOOD"

    def test_zero_coverage_not_excellent(self):
        """Zero coverage should NOT result in EXCELLENT even with score=0."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=0.0,
            avg_latency_seconds=60.0,
        )

        assert score == 0
        assert status == "GOOD"

    def test_good_status(self):
        """Low score should result in GOOD status."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=50.0,
            avg_latency_seconds=60.0,
        )

        assert score == 0
        assert status == "EXCELLENT"

    def test_duplicate_penalty(self):
        """Duplicates should add penalty to score."""
        score, status = compute_health_score(
            duplicate_reviews=1,
            coverage_percent=100.0,
            avg_latency_seconds=60.0,
        )

        assert score == 0  # 50 - 100 = -50, clamped to 0
        assert status == "GOOD"  # Has duplicates, so not EXCELLENT

    def test_slow_review_penalty(self):
        """Slow reviews should add penalty to score."""
        score, status = compute_health_score(
            duplicate_reviews=0,
            coverage_percent=0.0,
            avg_latency_seconds=400.0,  # > 300 seconds
        )

        assert score == SLOW_REVIEW_PENALTY
        assert status == "GOOD"

    def test_needs_attention_status(self):
        """High score should result in NEEDS ATTENTION status."""
        score, status = compute_health_score(
            duplicate_reviews=3,
            coverage_percent=0.0,
            avg_latency_seconds=400.0,
        )

        # 3 * 50 + 10 = 160
        assert score == 160
        assert status == "NEEDS ATTENTION"

    def test_fair_status(self):
        """Medium score should result in FAIR status."""
        score, status = compute_health_score(
            duplicate_reviews=2,
            coverage_percent=50.0,
            avg_latency_seconds=60.0,
        )

        # 2 * 50 - 50 = 50
        assert score == 50
        assert status == "FAIR"


class TestCheckRateLimit:
    """Tests for the check_rate_limit function."""

    def test_rate_limit_not_exceeded(self):
        """Should not raise when rate limit is not exceeded."""
        response = Mock()
        response.headers = {"X-RateLimit-Remaining": "100"}

        check_rate_limit(response)

    def test_rate_limit_exceeded(self):
        """Should raise RateLimitError when rate limit is exceeded."""
        response = Mock()
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1735000000",
        }

        with pytest.raises(RateLimitError) as exc_info:
            check_rate_limit(response)

        assert exc_info.value.reset_time == 1735000000

    def test_missing_rate_limit_header(self):
        """Should not raise when rate limit header is missing."""
        response = Mock()
        response.headers = {}

        check_rate_limit(response)


class TestCheckRegression:
    """Tests for the check_regression function (workflow regression detection)."""

    # --- Force notify tests ---
    def test_force_notify_always_notifies(self):
        """Force notify should always return True regardless of status."""
        notify, reason = check_regression("GOOD", "GOOD", force_notify=True)
        assert notify is True
        assert reason == "Force notification requested"

    def test_force_notify_overrides_improvement(self):
        """Force notify should notify even on improvement."""
        notify, reason = check_regression("FAIR", "EXCELLENT", force_notify=True)
        assert notify is True
        assert reason == "Force notification requested"

    # --- ERROR status tests ---
    def test_error_status_always_notifies(self):
        """ERROR status should always trigger notification."""
        notify, reason = check_regression("GOOD", "ERROR", force_notify=False)
        assert notify is True
        assert reason == "Scorecard execution failed"

    def test_error_from_unknown_notifies(self):
        """ERROR status should notify even from UNKNOWN baseline."""
        notify, reason = check_regression("UNKNOWN", "ERROR", force_notify=False)
        assert notify is True
        assert reason == "Scorecard execution failed"

    # --- UNKNOWN baseline tests ---
    def test_unknown_baseline_no_notify(self):
        """First run (UNKNOWN baseline) should not notify."""
        notify, reason = check_regression("UNKNOWN", "GOOD", force_notify=False)
        assert notify is False
        assert reason == "First run, establishing baseline"

    def test_unknown_to_excellent_no_notify(self):
        """UNKNOWN to EXCELLENT should not notify (establishing baseline)."""
        notify, reason = check_regression("UNKNOWN", "EXCELLENT", force_notify=False)
        assert notify is False
        assert reason == "First run, establishing baseline"

    def test_unknown_to_needs_attention_no_notify(self):
        """UNKNOWN to NEEDS ATTENTION should not notify (establishing baseline)."""
        notify, reason = check_regression("UNKNOWN", "NEEDS ATTENTION", force_notify=False)
        assert notify is False
        assert reason == "First run, establishing baseline"

    # --- Regression tests (status worsens) ---
    def test_excellent_to_good_regression(self):
        """EXCELLENT to GOOD is a regression."""
        notify, reason = check_regression("EXCELLENT", "GOOD", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from EXCELLENT to GOOD"

    def test_excellent_to_fair_regression(self):
        """EXCELLENT to FAIR is a regression."""
        notify, reason = check_regression("EXCELLENT", "FAIR", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from EXCELLENT to FAIR"

    def test_excellent_to_needs_attention_regression(self):
        """EXCELLENT to NEEDS ATTENTION is a regression."""
        notify, reason = check_regression("EXCELLENT", "NEEDS ATTENTION", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from EXCELLENT to NEEDS ATTENTION"

    def test_good_to_fair_regression(self):
        """GOOD to FAIR is a regression."""
        notify, reason = check_regression("GOOD", "FAIR", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from GOOD to FAIR"

    def test_good_to_needs_attention_regression(self):
        """GOOD to NEEDS ATTENTION is a regression."""
        notify, reason = check_regression("GOOD", "NEEDS ATTENTION", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from GOOD to NEEDS ATTENTION"

    def test_fair_to_needs_attention_regression(self):
        """FAIR to NEEDS ATTENTION is a regression."""
        notify, reason = check_regression("FAIR", "NEEDS ATTENTION", force_notify=False)
        assert notify is True
        assert reason == "Status regressed from FAIR to NEEDS ATTENTION"

    # --- Improvement tests (status improves, no notify) ---
    def test_good_to_excellent_improvement(self):
        """GOOD to EXCELLENT is an improvement, no notify."""
        notify, reason = check_regression("GOOD", "EXCELLENT", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (GOOD -> EXCELLENT)"

    def test_fair_to_good_improvement(self):
        """FAIR to GOOD is an improvement, no notify."""
        notify, reason = check_regression("FAIR", "GOOD", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (FAIR -> GOOD)"

    def test_fair_to_excellent_improvement(self):
        """FAIR to EXCELLENT is an improvement, no notify."""
        notify, reason = check_regression("FAIR", "EXCELLENT", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (FAIR -> EXCELLENT)"

    def test_needs_attention_to_fair_improvement(self):
        """NEEDS ATTENTION to FAIR is an improvement, no notify."""
        notify, reason = check_regression("NEEDS ATTENTION", "FAIR", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (NEEDS ATTENTION -> FAIR)"

    def test_needs_attention_to_good_improvement(self):
        """NEEDS ATTENTION to GOOD is an improvement, no notify."""
        notify, reason = check_regression("NEEDS ATTENTION", "GOOD", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (NEEDS ATTENTION -> GOOD)"

    def test_needs_attention_to_excellent_improvement(self):
        """NEEDS ATTENTION to EXCELLENT is an improvement, no notify."""
        notify, reason = check_regression("NEEDS ATTENTION", "EXCELLENT", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (NEEDS ATTENTION -> EXCELLENT)"

    # --- Same status tests (no change, no notify) ---
    def test_excellent_to_excellent_no_change(self):
        """EXCELLENT to EXCELLENT is no change, no notify."""
        notify, reason = check_regression("EXCELLENT", "EXCELLENT", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (EXCELLENT -> EXCELLENT)"

    def test_good_to_good_no_change(self):
        """GOOD to GOOD is no change, no notify."""
        notify, reason = check_regression("GOOD", "GOOD", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (GOOD -> GOOD)"

    def test_fair_to_fair_no_change(self):
        """FAIR to FAIR is no change, no notify."""
        notify, reason = check_regression("FAIR", "FAIR", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (FAIR -> FAIR)"

    def test_needs_attention_to_needs_attention_no_change(self):
        """NEEDS ATTENTION to NEEDS ATTENTION is no change, no notify."""
        notify, reason = check_regression("NEEDS ATTENTION", "NEEDS ATTENTION", force_notify=False)
        assert notify is False
        assert reason == "No regression detected (NEEDS ATTENTION -> NEEDS ATTENTION)"

    # --- Unknown status handling ---
    def test_invalid_current_status_triggers_regression(self):
        """Invalid/unknown current status triggers regression notification."""
        notify, reason = check_regression("GOOD", "INVALID_STATUS", force_notify=False)
        assert notify is True
        assert "regressed" in reason


class TestStatusSeverity:
    """Tests for the STATUS_SEVERITY constant."""

    def test_severity_ordering(self):
        """Verify severity values are correctly ordered (lower = better)."""
        assert STATUS_SEVERITY["EXCELLENT"] < STATUS_SEVERITY["GOOD"]
        assert STATUS_SEVERITY["GOOD"] < STATUS_SEVERITY["FAIR"]
        assert STATUS_SEVERITY["FAIR"] < STATUS_SEVERITY["NEEDS ATTENTION"]
        assert STATUS_SEVERITY["NEEDS ATTENTION"] < STATUS_SEVERITY["ERROR"]

    def test_all_statuses_defined(self):
        """Verify all expected statuses are defined."""
        expected = {"EXCELLENT", "GOOD", "FAIR", "NEEDS ATTENTION", "ERROR"}
        assert set(STATUS_SEVERITY.keys()) == expected


class TestConstants:
    """Tests to verify constants are properly defined."""

    def test_marker_constant(self):
        """Marker constant should be the expected HTML comment."""
        assert MORNINGAI_REVIEW_MARKER == "<!-- morningai:autogen-review -->"

    def test_penalty_constants(self):
        """Penalty constants should have expected values."""
        assert DUPLICATE_PENALTY == 50
        assert SLOW_REVIEW_PENALTY == 10
        assert SLOW_REVIEW_THRESHOLD_SECONDS == 300

    def test_threshold_constants(self):
        """Threshold constants should have expected values."""
        assert STATUS_GOOD_THRESHOLD == 50
        assert STATUS_FAIR_THRESHOLD == 100
        assert EXCELLENT_COVERAGE_THRESHOLD == 50
