#!/usr/bin/env python3
"""
Unit tests for 422 fallback metrics recording - Phase B-B C-lite Telemetry

Tests cover:
1. Fault injection safety gates (_should_inject_422_fault)
2. Metrics recording when fallback is used (record_inline_comment_result)
3. Correct counter increments (fallback_comments_total vs posted_total)
4. delivery_rate calculation with fallback comments

Issue #2741: C-lite Telemetry for EPIC B KPIs
Phase B-B: 422 Fallback Verification
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

try:
    from github import GithubException  # noqa: E402
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False
    GithubException = None


class MockSettings:
    """Mock settings object for testing fault injection"""
    def __init__(
        self,
        enable_fault_injection=False,
        is_staging=False,
        fault_injection_422_rate=1.0,
        enable_github_review_posting=True,
        github_review_posting_dry_run=False,
        github_review_posting_max_comments=10,
        internal_repos_whitelist="RC918/morningai",
        redis_url=None,  # Disable Redis dedup in tests
    ):
        self.enable_fault_injection = enable_fault_injection
        self.is_staging = is_staging
        self.fault_injection_422_rate = fault_injection_422_rate
        self.enable_github_review_posting = enable_github_review_posting
        self.github_review_posting_dry_run = github_review_posting_dry_run
        self.github_review_posting_max_comments = github_review_posting_max_comments
        self.internal_repos_whitelist = internal_repos_whitelist
        self.redis_url = redis_url


class TestShouldInject422Fault:
    """Tests for _should_inject_422_fault() safety gates

    P2 Update: Now tests 4 safety gates including internal repo whitelist.
    Removed PyGithub dependency to enable CI coverage.
    """

    def test_returns_false_when_fault_injection_disabled(self):
        """Fault injection disabled should return False"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=False,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai"
        )
        assert _should_inject_422_fault(settings, "RC918/morningai") is False

    def test_returns_false_when_not_staging(self):
        """Non-staging environment should return False (safety gate)"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=False,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai"
        )
        assert _should_inject_422_fault(settings, "RC918/morningai") is False

    def test_returns_false_when_repo_not_in_whitelist(self):
        """Repo not in whitelist should return False (safety gate 3)"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai"
        )
        # External repo should not trigger fault injection
        assert _should_inject_422_fault(settings, "external/repo") is False

    def test_returns_false_when_whitelist_empty(self):
        """Empty whitelist should return False"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist=""
        )
        assert _should_inject_422_fault(settings, "RC918/morningai") is False

    def test_returns_false_when_repo_is_none(self):
        """None repo should return False"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai"
        )
        assert _should_inject_422_fault(settings, None) is False

    def test_returns_false_when_rate_is_zero(self):
        """Zero injection rate should return False"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=0.0,
            internal_repos_whitelist="RC918/morningai"
        )
        # With rate=0.0, random.random() > 0.0 is always True, so returns False
        assert _should_inject_422_fault(settings, "RC918/morningai") is False

    def test_returns_true_when_all_conditions_met(self):
        """All conditions met with rate=1.0 should return True"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai"
        )
        # With rate=1.0, random.random() > 1.0 is always False, so returns True
        assert _should_inject_422_fault(settings, "RC918/morningai") is True

    def test_respects_injection_rate(self):
        """Injection rate should be respected (probabilistic test)"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=0.5,
            internal_repos_whitelist="RC918/morningai"
        )

        # Run multiple times and check that we get both True and False
        results = [_should_inject_422_fault(settings, "RC918/morningai") for _ in range(100)]
        # With 50% rate, we should get some True and some False
        assert True in results
        assert False in results

    def test_whitelist_with_multiple_repos(self):
        """Whitelist with multiple repos should work correctly"""
        from tools.github_api import _should_inject_422_fault

        settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            internal_repos_whitelist="RC918/morningai, RC918/other-repo"
        )
        assert _should_inject_422_fault(settings, "RC918/morningai") is True
        assert _should_inject_422_fault(settings, "RC918/other-repo") is True
        assert _should_inject_422_fault(settings, "external/repo") is False


class TestFallbackMetricsRecording:
    """Tests for metrics recording when 422 fallback is used"""

    def _create_mock_redis_with_pipeline(self):
        """Create a mock Redis client that tracks pipeline incrby calls"""
        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(
            return_value=mock_pipeline
        )
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)
        return mock_redis, mock_pipeline

    def test_fallback_used_increments_fallback_counters(self):
        """When fallback_used=True, should increment fallback_* counters"""
        from orchestrator_metrics import OrchestratorMetrics

        mock_redis, mock_pipeline = self._create_mock_redis_with_pipeline()

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        metrics.record_inline_comment_result(
            trace_id="test-trace-123",
            eligible_count=3,
            validated_count=3,
            downgraded_count=0,
            posted_count=3,
            post_failed=False,
            fallback_used=True,
            dry_run=False,
            feature_disabled=False
        )

        incrby_calls = [str(c) for c in mock_pipeline.incrby.call_args_list]

        assert any("fallback_comments_total" in c for c in incrby_calls)
        assert any("fallback_events_total" in c for c in incrby_calls)
        assert not any(
            "posted_total" in c and "fallback" not in c
            for c in incrby_calls
        )

    def test_no_fallback_increments_posted_counters(self):
        """When fallback_used=False, should increment posted_total counter"""
        from orchestrator_metrics import OrchestratorMetrics

        mock_redis, mock_pipeline = self._create_mock_redis_with_pipeline()

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        metrics.record_inline_comment_result(
            trace_id="test-trace-456",
            eligible_count=3,
            validated_count=3,
            downgraded_count=0,
            posted_count=3,
            post_failed=False,
            fallback_used=False,
            dry_run=False,
            feature_disabled=False
        )

        incrby_calls = [str(c) for c in mock_pipeline.incrby.call_args_list]

        assert any(
            "posted_total" in c and "fallback" not in c
            for c in incrby_calls
        )
        assert not any("fallback_comments_total" in c for c in incrby_calls)
        assert not any("fallback_events_total" in c for c in incrby_calls)

    def test_fallback_comments_count_matches_posted_count(self):
        """fallback_comments_total should be incremented by posted_count"""
        from orchestrator_metrics import OrchestratorMetrics

        mock_redis, mock_pipeline = self._create_mock_redis_with_pipeline()

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        metrics.record_inline_comment_result(
            trace_id="test-trace-789",
            eligible_count=5,
            validated_count=5,
            downgraded_count=0,
            posted_count=5,
            post_failed=False,
            fallback_used=True,
            dry_run=False,
            feature_disabled=False
        )

        for call_obj in mock_pipeline.incrby.call_args_list:
            args = call_obj[0]
            if "fallback_comments_total" in str(args[0]):
                assert args[1] == 5
                break


class TestDeliveryRateCalculation:
    """Tests for delivery_rate calculation with fallback comments"""

    def test_delivery_rate_includes_fallback_comments(self):
        """delivery_rate should include both inline and fallback comments"""
        from orchestrator_metrics import OrchestratorMetrics

        mock_redis = MagicMock()

        # Mock get_window_count to return specific values
        def mock_get(key):
            if "eligible_total" in key:
                return b"10"  # 10 eligible comments
            elif "posted_total" in key:
                return b"5"  # 5 posted inline
            elif "fallback_comments_total" in key:
                return b"3"  # 3 delivered via fallback
            return b"0"

        mock_redis.get.side_effect = mock_get

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        summary = metrics.get_review_summary(window_minutes=15)

        # delivery_rate = (posted + fallback_comments) / eligible * 100
        # = (5 + 3) / 10 * 100 = 80%
        assert summary["inline"]["delivery_rate"] == 80.0
        assert summary["kpis"]["delivery_rate"] == 80.0

    def test_delivery_rate_zero_when_no_eligible(self):
        """delivery_rate should be 0 when no eligible comments"""
        from orchestrator_metrics import OrchestratorMetrics

        mock_redis = MagicMock()
        mock_redis.get.return_value = b"0"

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        summary = metrics.get_review_summary(window_minutes=15)

        # No eligible comments = 0% delivery rate
        assert summary["inline"]["delivery_rate"] == 0
        assert summary["kpis"]["delivery_rate"] == 0


class TestIsRepoInInternalWhitelist:
    """Tests for _is_repo_in_internal_whitelist() helper function

    P2: New test class for the internal repo whitelist helper.
    """

    def test_returns_false_when_repo_is_none(self):
        """None repo should return False"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(internal_repos_whitelist="RC918/morningai")
        assert _is_repo_in_internal_whitelist(settings, None) is False

    def test_returns_false_when_repo_is_empty(self):
        """Empty repo should return False"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(internal_repos_whitelist="RC918/morningai")
        assert _is_repo_in_internal_whitelist(settings, "") is False

    def test_returns_false_when_whitelist_is_empty(self):
        """Empty whitelist should return False"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(internal_repos_whitelist="")
        assert _is_repo_in_internal_whitelist(settings, "RC918/morningai") is False

    def test_returns_false_when_repo_not_in_whitelist(self):
        """Repo not in whitelist should return False"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(internal_repos_whitelist="RC918/morningai")
        assert _is_repo_in_internal_whitelist(settings, "external/repo") is False

    def test_returns_true_when_repo_in_whitelist(self):
        """Repo in whitelist should return True"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(internal_repos_whitelist="RC918/morningai")
        assert _is_repo_in_internal_whitelist(settings, "RC918/morningai") is True

    def test_handles_multiple_repos_in_whitelist(self):
        """Multiple repos in whitelist should all be recognized"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(
            internal_repos_whitelist="RC918/morningai,RC918/other-repo,RC918/third"
        )
        assert _is_repo_in_internal_whitelist(settings, "RC918/morningai") is True
        assert _is_repo_in_internal_whitelist(settings, "RC918/other-repo") is True
        assert _is_repo_in_internal_whitelist(settings, "RC918/third") is True
        assert _is_repo_in_internal_whitelist(settings, "external/repo") is False

    def test_handles_whitespace_in_whitelist(self):
        """Whitespace around repo names should be trimmed"""
        from tools.github_api import _is_repo_in_internal_whitelist

        settings = MockSettings(
            internal_repos_whitelist="  RC918/morningai  ,  RC918/other-repo  "
        )
        assert _is_repo_in_internal_whitelist(settings, "RC918/morningai") is True
        assert _is_repo_in_internal_whitelist(settings, "RC918/other-repo") is True

    def test_handles_missing_whitelist_attribute(self):
        """Missing whitelist attribute should return False"""
        from tools.github_api import _is_repo_in_internal_whitelist

        # Create a settings object without internal_repos_whitelist
        class SettingsWithoutWhitelist:
            pass

        settings = SettingsWithoutWhitelist()
        assert _is_repo_in_internal_whitelist(settings, "RC918/morningai") is False


@pytest.mark.skipif(not HAS_GITHUB, reason="PyGithub not installed")
class TestFaultInjectionIntegration:
    """Integration tests for fault injection triggering fallback

    Note: These tests require PyGithub for GithubException.
    P2: Updated to include internal_repos_whitelist and mock_repo.full_name.
    """

    def test_fault_injection_triggers_fallback_path(self):
        """Fault injection should trigger the 422 fallback path"""
        mock_settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10,
            internal_repos_whitelist="RC918/morningai"
        )

        mock_repo = MagicMock()
        mock_repo.full_name = "RC918/morningai"
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        # Track create_review calls
        call_count = [0]

        def create_review_side_effect(**kwargs):
            call_count[0] += 1
            # First call is the fallback (after 422 injection)
            # Second call would be the actual fallback post

        mock_pr.create_review.side_effect = create_review_side_effect

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[
                    {"file": "test.py", "end_line": 10, "message": "Test 1"},
                    {"file": "test.py", "end_line": 20, "message": "Test 2"},
                    {"file": "test.py", "end_line": 30, "message": "Test 3"},
                ]
            )

            # Should succeed via fallback
            assert result["success"] is True
            assert result.get("downgraded") is True
            assert result["posted_count"] == 3
            # create_review should be called once (fallback body post)
            assert mock_pr.create_review.call_count == 1

    def test_fault_injection_disabled_posts_normally(self):
        """With fault injection disabled, should post normally"""
        mock_settings = MockSettings(
            enable_fault_injection=False,  # Disabled
            is_staging=True,
            fault_injection_422_rate=1.0,
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10,
            internal_repos_whitelist="RC918/morningai"
        )

        mock_repo = MagicMock()
        mock_repo.full_name = "RC918/morningai"
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[
                    {"file": "test.py", "end_line": 10, "message": "Test 1"},
                ]
            )

            # Should succeed normally (no fallback)
            assert result["success"] is True
            assert result.get("downgraded") is not True
            # create_review should be called once with inline comments
            assert mock_pr.create_review.call_count == 1
            # Verify it was called with comments parameter
            call_kwargs = mock_pr.create_review.call_args[1]
            assert "comments" in call_kwargs

    def test_fault_injection_skipped_for_external_repo(self):
        """Fault injection should be skipped for repos not in whitelist"""
        mock_settings = MockSettings(
            enable_fault_injection=True,
            is_staging=True,
            fault_injection_422_rate=1.0,
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10,
            internal_repos_whitelist="RC918/morningai"
        )

        mock_repo = MagicMock()
        mock_repo.full_name = "external/repo"  # Not in whitelist
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[
                    {"file": "test.py", "end_line": 10, "message": "Test 1"},
                ]
            )

            # Should succeed normally (no fallback, no fault injection)
            assert result["success"] is True
            assert result.get("downgraded") is not True
            # create_review should be called once with inline comments
            assert mock_pr.create_review.call_count == 1
            # Verify it was called with comments parameter
            call_kwargs = mock_pr.create_review.call_args[1]
            assert "comments" in call_kwargs
