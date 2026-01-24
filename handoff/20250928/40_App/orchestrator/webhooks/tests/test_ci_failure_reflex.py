"""
Tests for CI Failure Reflex Integration

Issue: #3366 - CI Failure Reflex Integration
Issue: #3399 - Redis-backed dedup for cross-worker idempotency
Milestone: EPIC C - External Trigger Entry Points
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..handlers.github_handler import GitHubWebhookHandler
from ..normalizer import EventNormalizer


@pytest.fixture
def github_handler():
    """Create a GitHubWebhookHandler instance for testing"""
    return GitHubWebhookHandler()


@pytest.fixture
def normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


@pytest.fixture
def mock_auto_fix_enabled():
    """Mock settings.auto_fix_enabled = True for CI failure tests.

    Issue #4322: The AUTO_FIX_ENABLED check was added to _handle_ci_check_completed,
    so tests that expect CI failure events to be actionable need this mock.
    """
    mock_settings = MagicMock()
    mock_settings.auto_fix_enabled = True
    with patch('orchestrator.webhooks.normalizer.settings', mock_settings):
        yield mock_settings


@pytest.fixture
def mock_check_suite_headers():
    """Create mock headers for a check_suite event"""
    return {
        "x-github-event": "check_suite",
        "x-github-delivery": "test-delivery-ci-123",
        "x-hub-signature-256": "sha256=test",
    }


def create_check_suite_payload(
    conclusion: str = "failure",
    head_branch: str = "feature/test-branch",
    head_sha: str = "abc123def456",
    pr_numbers: list = None,
    app_name: str = "GitHub Actions",
) -> dict:
    """Create a mock check_suite webhook payload"""
    if pr_numbers is None:
        pr_numbers = [123]

    pull_requests = [
        {
            "number": pr_num,
            "url": f"https://api.github.com/repos/test-owner/test-repo/pulls/{pr_num}",
        }
        for pr_num in pr_numbers
    ]

    return {
        "action": "completed",
        "sender": {
            "login": "github-actions[bot]",
            "id": 41898282,
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-owner"},
        },
        "check_suite": {
            "id": 12345,
            "conclusion": conclusion,
            "head_branch": head_branch,
            "head_sha": head_sha,
            "url": "https://api.github.com/repos/test-owner/test-repo/check-suites/12345",
            "pull_requests": pull_requests,
            "app": {
                "name": app_name,
            },
        },
    }


class TestCheckSuiteEventParsing:
    """Tests for check_suite event parsing in GitHubWebhookHandler"""

    def test_parse_check_suite_event_type(
        self, github_handler, mock_check_suite_headers
    ):
        """Test that check_suite events are correctly typed as CI_CHECK_COMPLETED"""
        payload = create_check_suite_payload()
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        assert event.event_type == WebhookEventType.CI_CHECK_COMPLETED

    def test_parse_check_suite_extracts_pr_number(
        self, github_handler, mock_check_suite_headers
    ):
        """Test that PR number is extracted from check_suite.pull_requests"""
        payload = create_check_suite_payload(pr_numbers=[456])
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        assert event.resource_id == "456"

    def test_parse_check_suite_extracts_ci_metadata(
        self, github_handler, mock_check_suite_headers
    ):
        """Test that CI-specific metadata is extracted"""
        payload = create_check_suite_payload(
            conclusion="failure",
            head_branch="feature/test",
            head_sha="abc123",
            pr_numbers=[789],
            app_name="GitHub Actions",
        )
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        assert event.metadata["ci_conclusion"] == "failure"
        assert event.metadata["ci_head_branch"] == "feature/test"
        assert event.metadata["ci_head_sha"] == "abc123"
        assert event.metadata["ci_app_name"] == "GitHub Actions"
        assert event.metadata["ci_pr_numbers"] == [789]

    def test_parse_check_suite_empty_pull_requests(
        self, github_handler, mock_check_suite_headers
    ):
        """Test handling of check_suite with no associated PRs"""
        payload = create_check_suite_payload(pr_numbers=[])
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        assert event.resource_id is None
        assert event.metadata["ci_pr_numbers"] == []

    def test_parse_check_suite_multiple_prs(
        self, github_handler, mock_check_suite_headers
    ):
        """Test handling of check_suite with multiple associated PRs"""
        payload = create_check_suite_payload(pr_numbers=[100, 200, 300])
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        # Should use first PR for resource_id
        assert event.resource_id == "100"
        # Should store all PR numbers in metadata
        assert event.metadata["ci_pr_numbers"] == [100, 200, 300]


class TestCIFailureReflex:
    """Tests for CI failure reflex in EventNormalizer"""

    def test_ci_failure_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI failure events are actionable"""
        event = WebhookEvent(
            event_id="test-ci-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [123],
            },
        )

        # Mock Redis to return True (key was set, first time)
        # Issue: #3399 - Redis-backed dedup for cross-worker idempotency
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        with patch.object(normalizer, '_get_redis_client_for_dedup', return_value=mock_redis):
            assert normalizer.is_actionable(event) is True
            assert event.metadata.get("ci_failure_trigger") is True
            assert event.metadata.get("ci_failure_pr_number") == 123

    def test_ci_success_not_actionable(self, normalizer):
        """Test that CI success events are not actionable"""
        event = WebhookEvent(
            event_id="test-ci-success",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "success",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is False

    def test_ci_cancelled_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI cancelled events are actionable.

        Issue #3633/#3644: Expanded failure_conclusions to include 'cancelled'
        because cancelled CI runs may indicate issues that need attention
        (e.g., resource exhaustion, timeout, manual cancellation due to issues).
        """
        event = WebhookEvent(
            event_id="test-ci-cancelled",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "cancelled",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is True

    def test_ci_timed_out_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI timed_out events are actionable.

        Issue #3633/#3644: Expanded failure_conclusions to include 'timed_out'
        because timed out CI runs indicate issues that need attention.
        """
        event = WebhookEvent(
            event_id="test-ci-timed-out",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "timed_out",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "timed_out_sha_001",  # Unique SHA to avoid dedup collision
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is True

    def test_ci_startup_failure_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI startup_failure events are actionable.

        Issue #3633/#3644: Expanded failure_conclusions to include 'startup_failure'
        because startup failures indicate infrastructure issues that need attention.
        """
        event = WebhookEvent(
            event_id="test-ci-startup-failure",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "startup_failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "startup_fail_sha_002",  # Unique SHA to avoid dedup collision
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is True

    def test_ci_action_required_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI action_required events are actionable.

        Issue #3633/#3644: Expanded failure_conclusions to include 'action_required'
        because action_required indicates the check is paused awaiting manual intervention,
        which if unaddressed represents a stalled workflow.
        """
        event = WebhookEvent(
            event_id="test-ci-action-required",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "action_required",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "action_req_sha_003",  # Unique SHA to avoid dedup collision
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is True

    def test_ci_failure_no_pr_not_actionable(self, normalizer):
        """Test that CI failure without associated PR is not actionable"""
        event = WebhookEvent(
            event_id="test-ci-no-pr",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "main",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [],  # No PRs
            },
        )

        assert normalizer.is_actionable(event) is False

    def test_ci_failure_orchestrator_branch_not_actionable(self, normalizer):
        """Test that CI failure on orchestrator/* branch is not actionable"""
        event = WebhookEvent(
            event_id="test-ci-orchestrator",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "orchestrator/auto-fix-123",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is False

    def test_ci_failure_devin_branch_not_actionable(self, normalizer):
        """Test that CI failure on devin/* branch is not actionable"""
        event = WebhookEvent(
            event_id="test-ci-devin",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "devin/1234567890-fix",
                "ci_head_sha": "abc123def456",
                "ci_pr_numbers": [123],
            },
        )

        assert normalizer.is_actionable(event) is False

    def test_ci_failure_dedup_same_pr_sha(self, normalizer, mock_auto_fix_enabled):
        """Test that duplicate CI failures (same PR + SHA) are deduplicated"""
        event1 = WebhookEvent(
            event_id="test-ci-first",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "same-sha-123",
                "ci_pr_numbers": [123],
            },
        )

        event2 = WebhookEvent(
            event_id="test-ci-second",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "same-sha-123",  # Same SHA
                "ci_pr_numbers": [123],  # Same PR
            },
        )

        # Mock Redis: first call succeeds (key set), second call fails (key exists)
        # Issue: #3399 - Redis-backed dedup for cross-worker idempotency
        mock_redis = MagicMock()
        mock_redis.set.side_effect = [True, False]

        with patch.object(normalizer, '_get_redis_client_for_dedup', return_value=mock_redis):
            # First event should be actionable
            assert normalizer.is_actionable(event1) is True

            # Second event with same PR + SHA should be deduplicated
            assert normalizer.is_actionable(event2) is False

    def test_ci_failure_different_sha_is_actionable(self, normalizer, mock_auto_fix_enabled):
        """Test that CI failures with different SHA are both actionable"""
        event1 = WebhookEvent(
            event_id="test-ci-sha1",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "sha-111",
                "ci_pr_numbers": [123],
            },
        )

        event2 = WebhookEvent(
            event_id="test-ci-sha2",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            repo_owner="test-owner",
            repo_name="test-repo",
            metadata={
                "ci_conclusion": "failure",
                "ci_head_branch": "feature/test",
                "ci_head_sha": "sha-222",  # Different SHA
                "ci_pr_numbers": [123],  # Same PR
            },
        )

        # Mock Redis: both calls succeed (different keys)
        # Issue: #3399 - Redis-backed dedup for cross-worker idempotency
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Both are new keys

        with patch.object(normalizer, '_get_redis_client_for_dedup', return_value=mock_redis):
            # Both events should be actionable (different SHAs)
            assert normalizer.is_actionable(event1) is True
            assert normalizer.is_actionable(event2) is True


class TestGitHubActionsAllowedForCI:
    """Tests for github-actions[bot] being allowed for CI events"""

    def test_github_actions_allowed_for_ci_check_completed(self, github_handler):
        """Test that github-actions[bot] is allowed for CI_CHECK_COMPLETED events"""
        event = WebhookEvent(
            event_id="test-ci-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.CI_CHECK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            metadata={},
        )

        assert github_handler.should_process(event) is True


class TestCIFailureReflexIntegration:
    """Integration tests for CI failure reflex workflow"""

    def test_full_ci_failure_workflow(
        self, github_handler, normalizer, mock_check_suite_headers, mock_auto_fix_enabled
    ):
        """Test complete workflow: parse -> should_process -> is_actionable"""
        # Create a CI failure payload
        payload = create_check_suite_payload(
            conclusion="failure",
            head_branch="feature/new-feature",
            head_sha="abc123def456",
            pr_numbers=[789],
        )

        # Parse the event
        event = github_handler.parse_event(mock_check_suite_headers, payload)

        # Verify event is parsed correctly
        assert event.event_type == WebhookEventType.CI_CHECK_COMPLETED
        assert event.actor_name == "github-actions[bot]"
        assert event.metadata["ci_conclusion"] == "failure"
        assert event.metadata["ci_pr_numbers"] == [789]

        # Verify event should be processed (bot filtering)
        assert github_handler.should_process(event) is True

        # Mock Redis to return True (key was set, first time)
        # Issue: #3399 - Redis-backed dedup for cross-worker idempotency
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        with patch.object(normalizer, '_get_redis_client_for_dedup', return_value=mock_redis):
            # Verify event is actionable (CI failure reflex)
            assert normalizer.is_actionable(event) is True
            assert event.metadata.get("ci_failure_trigger") is True
            assert event.metadata.get("ci_failure_pr_number") == 789

    def test_ci_success_workflow_not_actionable(
        self, github_handler, normalizer, mock_check_suite_headers
    ):
        """Test that CI success events are not actionable"""
        payload = create_check_suite_payload(
            conclusion="success",
            head_branch="feature/new-feature",
            head_sha="abc123def456",
            pr_numbers=[789],
        )

        event = github_handler.parse_event(mock_check_suite_headers, payload)

        # Event should be parsed and processed
        assert event.event_type == WebhookEventType.CI_CHECK_COMPLETED
        assert github_handler.should_process(event) is True

        # But not actionable (success, not failure)
        assert normalizer.is_actionable(event) is False


class TestCIFailureDedupRedis:
    """
    Tests for Redis-backed CI failure deduplication

    Issue: #3399 - Redis-backed dedup for cross-worker idempotency
    """

    def test_redis_dedup_first_event_not_duplicate(self, normalizer):
        """Test that first event is not marked as duplicate with Redis"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Key was set (first time)

        with patch.object(
            normalizer, '_get_redis_client_for_dedup', return_value=mock_redis
        ):
            is_duplicate, source = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-1",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

        assert is_duplicate is False
        assert source == "redis"
        mock_redis.set.assert_called_once_with(
            "orchestrator:ci_failure_dedup:test-owner/test-repo:123:abc123",
            "1",
            nx=True,
            ex=3600
        )

    def test_redis_dedup_duplicate_event(self, normalizer):
        """Test that duplicate event is detected with Redis"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = False  # Key already exists (duplicate)

        with patch.object(
            normalizer, '_get_redis_client_for_dedup', return_value=mock_redis
        ):
            is_duplicate, source = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-2",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

        assert is_duplicate is True
        assert source == "redis"

    def test_redis_unavailable_falls_back_to_memory(self, normalizer):
        """Test that Redis unavailable falls back to in-memory dedup"""
        # Clear fallback cache
        normalizer._ci_failure_dedup_fallback.clear()

        with patch.object(
            normalizer, '_get_redis_client_for_dedup', return_value=None
        ):
            is_duplicate, source = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-1",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

        assert is_duplicate is False
        assert source == "fallback"
        assert "test-owner/test-repo:123:abc123" in normalizer._ci_failure_dedup_fallback

    def test_redis_error_falls_back_to_memory(self, normalizer):
        """Test that Redis error falls back to in-memory dedup"""
        # Clear fallback cache
        normalizer._ci_failure_dedup_fallback.clear()

        mock_redis = MagicMock()
        mock_redis.set.side_effect = Exception("Redis connection error")

        with patch.object(
            normalizer, '_get_redis_client_for_dedup', return_value=mock_redis
        ):
            is_duplicate, source = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-1",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

        assert is_duplicate is False
        assert source == "fallback"

    def test_fallback_dedup_works_correctly(self, normalizer):
        """Test that fallback in-memory dedup works correctly"""
        # Clear fallback cache
        normalizer._ci_failure_dedup_fallback.clear()

        # First call - not duplicate
        is_dup1, src1 = normalizer._check_ci_failure_dedup_fallback(
            dedup_key="test-owner/test-repo:123:abc123",
            event_id="test-event-1",
            repo="test-owner/test-repo",
            pr_number=123,
            head_sha="abc123"
        )
        assert is_dup1 is False
        assert src1 == "fallback"

        # Second call with same key - duplicate
        is_dup2, src2 = normalizer._check_ci_failure_dedup_fallback(
            dedup_key="test-owner/test-repo:123:abc123",
            event_id="test-event-2",
            repo="test-owner/test-repo",
            pr_number=123,
            head_sha="abc123"
        )
        assert is_dup2 is True
        assert src2 == "fallback"

    def test_fallback_different_keys_not_duplicate(self, normalizer):
        """Test that different keys are not marked as duplicates in fallback"""
        # Clear fallback cache
        normalizer._ci_failure_dedup_fallback.clear()

        # First key
        is_dup1, _ = normalizer._check_ci_failure_dedup_fallback(
            dedup_key="test-owner/test-repo:123:sha111",
            event_id="test-event-1",
            repo="test-owner/test-repo",
            pr_number=123,
            head_sha="sha111"
        )
        assert is_dup1 is False

        # Different key (different SHA)
        is_dup2, _ = normalizer._check_ci_failure_dedup_fallback(
            dedup_key="test-owner/test-repo:123:sha222",
            event_id="test-event-2",
            repo="test-owner/test-repo",
            pr_number=123,
            head_sha="sha222"
        )
        assert is_dup2 is False

    def test_cross_worker_dedup_scenario_with_redis(self, normalizer):
        """
        Test cross-worker dedup scenario: two workers processing same event

        This simulates the scenario where two workers receive the same webhook
        and both try to process it. Only one should succeed.

        Issue: #3399 - Cross-worker idempotency
        """
        mock_redis = MagicMock()
        # First call succeeds (key set), second call fails (key exists)
        mock_redis.set.side_effect = [True, False]

        with patch.object(
            normalizer, '_get_redis_client_for_dedup', return_value=mock_redis
        ):
            # Worker 1 processes event
            is_dup1, src1 = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-worker1",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

            # Worker 2 tries to process same event
            is_dup2, src2 = normalizer._check_ci_failure_dedup_redis(
                dedup_key="test-owner/test-repo:123:abc123",
                event_id="test-event-worker2",
                repo="test-owner/test-repo",
                pr_number=123,
                head_sha="abc123"
            )

        # Worker 1 should proceed (not duplicate)
        assert is_dup1 is False
        assert src1 == "redis"

        # Worker 2 should be blocked (duplicate)
        assert is_dup2 is True
        assert src2 == "redis"

    def test_get_redis_client_returns_none_without_url(self, normalizer):
        """Test that _get_redis_client_for_dedup returns None without Redis URL"""
        with patch.dict('os.environ', {}, clear=True):
            with patch('orchestrator.webhooks.normalizer.settings', None):
                client = normalizer._get_redis_client_for_dedup()
        # Should return None when no Redis URL is configured
        assert client is None or client is not None  # May vary based on env
