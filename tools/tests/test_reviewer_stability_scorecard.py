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
    is_morningai_review,
    analyze_pr_reviews,
    compute_duplicates,
    compute_latency_stats,
    compute_health_score,
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
