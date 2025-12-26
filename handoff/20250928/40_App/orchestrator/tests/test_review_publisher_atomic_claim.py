#!/usr/bin/env python3
"""
Unit Tests for Review Publisher Atomic Claim Pattern

This module tests the atomic claim pattern implemented in github_api.py
to prevent duplicate reviews caused by race conditions.

The atomic claim pattern:
1. _check_review_already_posted() uses SET NX EX to atomically claim
2. If claim succeeds, proceed to post review
3. If claim fails, another worker has the claim or review was posted
4. _mark_review_posted() updates "claiming" to "posted" with longer TTL

Related Issues:
- Race condition fix for duplicate reviews
- Phase 1 Canary gate: duplicate_reviews = 0
"""
import os
import sys
from unittest.mock import MagicMock, patch
import redis as redis_module

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.github_api import (
    _check_review_already_posted,
    _mark_review_posted,
    REVIEW_CLAIM_TTL_SECONDS,
)
from utils.constants import REVIEW_DEDUP_TTL_SECONDS, REVIEWER_VERSION


class TestAtomicClaimPattern:
    """Tests for the atomic claim pattern in review publisher."""

    def test_first_worker_gets_claim(self):
        """Test that the first worker successfully claims the review."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.return_value = True  # SET NX succeeds

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                already_posted, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=123,
                    head_sha="abc123def456",
                )

                assert already_posted is False
                assert dedup_key is not None
                assert "RC918/morningai" in dedup_key
                assert "123" in dedup_key
                assert REVIEWER_VERSION in dedup_key

                # Verify SET NX EX was called with correct parameters
                mock_redis_instance.set.assert_called_once()
                call_args = mock_redis_instance.set.call_args
                assert call_args[0][0] == dedup_key
                assert call_args[0][1] == "claiming"
                assert call_args[1]["nx"] is True
                assert call_args[1]["ex"] == REVIEW_CLAIM_TTL_SECONDS

    def test_second_worker_blocked_by_claim(self):
        """Test that the second worker is blocked when claim already exists."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.return_value = None  # SET NX fails (key exists)
        mock_redis_instance.get.return_value = "claiming"  # Key is in claiming state

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                already_posted, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=123,
                    head_sha="abc123def456",
                )

                assert already_posted is True
                assert dedup_key is not None

    def test_worker_blocked_by_posted_review(self):
        """Test that worker is blocked when review was already posted."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.return_value = None  # SET NX fails (key exists)
        mock_redis_instance.get.return_value = "posted"  # Key is in posted state

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                already_posted, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=123,
                    head_sha="abc123def456",
                )

                assert already_posted is True

    def test_mark_review_posted_updates_to_posted(self):
        """Test that _mark_review_posted updates value to 'posted' with long TTL."""
        mock_redis_instance = MagicMock()

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                dedup_key = "review_posted:RC918/morningai:123:abc123def456:v1"
                _mark_review_posted(dedup_key)

                # Verify SETEX was called with "posted" value and long TTL
                mock_redis_instance.setex.assert_called_once_with(
                    dedup_key,
                    REVIEW_DEDUP_TTL_SECONDS,
                    "posted"
                )


class TestFailOpenBehavior:
    """Tests for fail-open behavior when Redis is unavailable."""

    def test_no_redis_url_allows_posting(self):
        """Test that missing Redis URL allows posting (fail-open)."""
        with patch('tools.github_api.settings') as mock_settings:
            mock_settings.redis_url = None

            already_posted, dedup_key = _check_review_already_posted(
                repo="RC918/morningai",
                pr_number=123,
                head_sha="abc123def456",
            )

            assert already_posted is False
            assert dedup_key is None

    def test_redis_error_allows_posting(self):
        """Test that Redis connection error allows posting (fail-open)."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = redis_module.exceptions.ConnectionError("Connection refused")

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                already_posted, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=123,
                    head_sha="abc123def456",
                )

                assert already_posted is False
                assert dedup_key is None

    def test_no_head_sha_allows_posting(self):
        """Test that missing head_sha allows posting (can't deduplicate)."""
        already_posted, dedup_key = _check_review_already_posted(
            repo="RC918/morningai",
            pr_number=123,
            head_sha=None,
        )

        assert already_posted is False
        assert dedup_key is None


class TestDedupKeyFormat:
    """Tests for dedup key format and consistency."""

    def test_dedup_key_format(self):
        """Test that dedup key has correct format."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.return_value = True

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                _, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=2849,
                    head_sha="abc123def456789",
                )

                # Key format: review_posted:{repo}:{pr}:{head_sha[:12]}:{version}
                expected_key = f"review_posted:RC918/morningai:2849:abc123def456:{REVIEWER_VERSION}"
                assert dedup_key == expected_key

    def test_head_sha_truncated_to_12_chars(self):
        """Test that head_sha is truncated to 12 characters."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.set.return_value = True

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                long_sha = "abc123def456789012345678901234567890"
                _, dedup_key = _check_review_already_posted(
                    repo="RC918/morningai",
                    pr_number=123,
                    head_sha=long_sha,
                )

                # Only first 12 chars of SHA should be in key
                assert "abc123def456" in dedup_key
                assert "789012345678" not in dedup_key


class TestClaimTTLConfiguration:
    """Tests for claim TTL configuration."""

    def test_claim_ttl_is_5_minutes(self):
        """Test that claim TTL is 5 minutes (300 seconds)."""
        assert REVIEW_CLAIM_TTL_SECONDS == 300

    def test_posted_ttl_is_24_hours(self):
        """Test that posted TTL is 24 hours (86400 seconds)."""
        assert REVIEW_DEDUP_TTL_SECONDS == 86400


class TestRaceConditionPrevention:
    """
    Tests specifically for race condition prevention.

    These tests verify that the atomic claim pattern prevents the
    check-then-act race condition that caused duplicate reviews.
    """

    def test_concurrent_workers_only_one_succeeds(self):
        """
        Simulate concurrent workers trying to claim the same review.

        Only the first SET NX should succeed, others should fail.
        """
        call_count = 0

        def mock_set(key, value, nx=False, ex=None):
            nonlocal call_count
            call_count += 1
            # First call succeeds, subsequent calls fail
            return call_count == 1

        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.return_value = "claiming"

        with patch.object(redis_module.Redis, 'from_url', return_value=mock_redis_instance):
            with patch('tools.github_api.settings') as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"

                # Simulate 3 concurrent workers
                results = []
                for _ in range(3):
                    already_posted, _ = _check_review_already_posted(
                        repo="RC918/morningai",
                        pr_number=123,
                        head_sha="abc123def456",
                    )
                    results.append(already_posted)

                # Only first worker should get the claim (already_posted=False)
                # Other workers should be blocked (already_posted=True)
                assert results[0] is False  # First worker gets claim
                assert results[1] is True   # Second worker blocked
                assert results[2] is True   # Third worker blocked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
