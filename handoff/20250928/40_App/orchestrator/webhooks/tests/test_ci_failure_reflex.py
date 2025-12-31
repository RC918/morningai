"""
Tests for CI Failure Reflex Integration

Issue: #3366 - CI Failure Reflex Integration
Milestone: EPIC C - External Trigger Entry Points
"""

import pytest
from datetime import datetime, timezone

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

    def test_ci_failure_is_actionable(self, normalizer):
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

        # Clear dedup cache for clean test
        normalizer._ci_failure_dedup.clear()

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

    def test_ci_cancelled_not_actionable(self, normalizer):
        """Test that CI cancelled events are not actionable"""
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

        assert normalizer.is_actionable(event) is False

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

    def test_ci_failure_dedup_same_pr_sha(self, normalizer):
        """Test that duplicate CI failures (same PR + SHA) are deduplicated"""
        # Clear dedup cache for clean test
        normalizer._ci_failure_dedup.clear()

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

        # First event should be actionable
        assert normalizer.is_actionable(event1) is True

        # Second event with same PR + SHA should be deduplicated
        assert normalizer.is_actionable(event2) is False

    def test_ci_failure_different_sha_is_actionable(self, normalizer):
        """Test that CI failures with different SHA are both actionable"""
        # Clear dedup cache for clean test
        normalizer._ci_failure_dedup.clear()

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
        self, github_handler, normalizer, mock_check_suite_headers
    ):
        """Test complete workflow: parse -> should_process -> is_actionable"""
        # Clear dedup cache for clean test
        normalizer._ci_failure_dedup.clear()

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
