#!/usr/bin/env python3
"""
Integration Tests for Orchestrator PR Filtering

This module tests the enhanced filtering rules to prevent the orchestrator from
generating docs PRs for certain webhook events:

1. PRs from orchestrator/* branches (self-triggering prevention)
2. Config-only PRs (future enhancement)

Issue: Docs PR Noise Reduction
When the orchestrator creates a docs PR (branch: orchestrator/*), GitHub sends
PR webhooks back. Without filtering, the orchestrator would process its own
PR events and potentially create more docs PRs, causing noise.

Test Strategy:
- Use real payload structures (not mocks) to simulate GitHub webhooks
- Test the normalizer's is_actionable() decision point
- Verify both orchestrator branch detection and edge cases
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webhooks.bot_protocol import (  # noqa: E402
    WebhookEvent,
    WebhookEventType,
    WebhookSource,
)
from webhooks.normalizer import (  # noqa: E402
    EventNormalizer,
    should_skip_orchestrator_pr_event,
)


class TestOrchestratorBranchDetection:
    """
    Tests for should_skip_orchestrator_pr_event() function.

    This function detects PRs from orchestrator/* branches and skips them
    to prevent self-triggering loops and docs PR noise.
    """

    def _create_pr_event(
        self,
        event_type: WebhookEventType,
        head_ref: str,
        actor_name: str = "RC918",
        repo_owner: str = "RC918",
        repo_name: str = "morningai",
        pr_number: int = 123,
    ) -> WebhookEvent:
        """
        Create a PR WebhookEvent with the given head branch reference.

        This simulates the event that would be created by GitHubWebhookHandler.parse_event()
        when GitHub sends a pull_request webhook.
        """
        return WebhookEvent(
            event_id="test-event-123",
            source=WebhookSource.GITHUB,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "action": "opened",
                "pull_request": {
                    "number": pr_number,
                    "title": "Test PR",
                    "body": "Test PR body",
                    "head": {
                        "ref": head_ref,
                        "sha": "abc123",
                    },
                    "base": {
                        "ref": "main",
                    },
                },
                "repository": {
                    "owner": {"login": repo_owner},
                    "name": repo_name,
                },
                "sender": {"login": actor_name, "id": 12345},
            },
            title="Test PR",
            description="Test PR body",
            url=f"https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}",
            actor_id="12345",
            actor_name=actor_name,
            resource_id=str(pr_number),
            resource_type="pull_request",
            resource_url=f"https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}",
            repo_owner=repo_owner,
            repo_name=repo_name,
            labels=[],
            assignees=[],
            metadata={
                "github_event": "pull_request",
                "action": "opened",
            },
        )

    def test_orchestrator_docs_branch_is_skipped(self):
        """
        Test that PRs from orchestrator/docs-* branches are skipped.

        This is the primary use case - docs PRs created by the orchestrator
        use branches like orchestrator/docs-{path_slug}-{branch_hash}.
        """
        event = self._create_pr_event(
            event_type=WebhookEventType.PR_OPENED,
            head_ref="orchestrator/docs-readme-abc123",
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_orchestrator_any_branch_is_skipped(self):
        """
        Test that any PR from orchestrator/* branches is skipped.

        This covers all orchestrator-generated branches, not just docs.
        """
        test_branches = [
            "orchestrator/docs-readme-abc123",
            "orchestrator/fix-typo-def456",
            "orchestrator/update-config-ghi789",
            "orchestrator/some-other-task",
        ]
        for branch in test_branches:
            event = self._create_pr_event(
                event_type=WebhookEventType.PR_OPENED,
                head_ref=branch,
            )
            assert should_skip_orchestrator_pr_event(event) is True, f"Branch {branch} should be skipped"

    def test_regular_branch_is_not_skipped(self):
        """
        Test that PRs from regular branches are NOT skipped.

        This ensures we don't accidentally skip legitimate PRs.
        """
        test_branches = [
            "main",
            "develop",
            "feature/new-feature",
            "fix/bug-fix",
            "devin/1234567890-some-task",
            "user/my-branch",
        ]
        for branch in test_branches:
            event = self._create_pr_event(
                event_type=WebhookEventType.PR_OPENED,
                head_ref=branch,
            )
            assert should_skip_orchestrator_pr_event(event) is False, f"Branch {branch} should NOT be skipped"

    def test_orchestrator_prefix_must_be_exact(self):
        """
        Test that branches with 'orchestrator' in the name but not as prefix are NOT skipped.

        This ensures we don't have false positives from similar-looking branches.
        """
        test_branches = [
            "my-orchestrator/branch",
            "feature/orchestrator-update",
            "orchestrator-without-slash",
            "Orchestrator/uppercase",  # Case sensitive
        ]
        for branch in test_branches:
            event = self._create_pr_event(
                event_type=WebhookEventType.PR_OPENED,
                head_ref=branch,
            )
            assert should_skip_orchestrator_pr_event(event) is False, f"Branch {branch} should NOT be skipped"

    def test_all_pr_event_types_are_checked(self):
        """
        Test that all PR event types are checked for orchestrator branches.

        The filter should apply to PR_OPENED, PR_CLOSED, PR_MERGED, PR_UPDATED, and PR_REVIEWED.
        """
        pr_event_types = [
            WebhookEventType.PR_OPENED,
            WebhookEventType.PR_CLOSED,
            WebhookEventType.PR_MERGED,
            WebhookEventType.PR_UPDATED,
            WebhookEventType.PR_REVIEWED,
        ]
        for event_type in pr_event_types:
            event = self._create_pr_event(
                event_type=event_type,
                head_ref="orchestrator/docs-test-abc123",
            )
            assert should_skip_orchestrator_pr_event(event) is True, f"Event type {event_type} should be skipped"

    def test_non_pr_events_are_not_checked(self):
        """
        Test that non-PR events are NOT checked for orchestrator branches.

        The filter should only apply to PR-related events.
        """
        non_pr_event_types = [
            WebhookEventType.ISSUE_CREATED,
            WebhookEventType.ISSUE_CLOSED,
            WebhookEventType.ISSUE_COMMENTED,
            WebhookEventType.PUSH,
        ]
        for event_type in non_pr_event_types:
            event = self._create_pr_event(
                event_type=event_type,
                head_ref="orchestrator/docs-test-abc123",
            )
            assert should_skip_orchestrator_pr_event(event) is False, f"Event type {event_type} should NOT be checked"

    def test_missing_head_ref_is_handled(self):
        """
        Test that events with missing head.ref are handled gracefully.

        This covers edge cases where the payload might be malformed.
        """
        event = self._create_pr_event(
            event_type=WebhookEventType.PR_OPENED,
            head_ref="",
        )
        # Remove head.ref from payload
        event.raw_payload["pull_request"]["head"]["ref"] = ""
        assert should_skip_orchestrator_pr_event(event) is False

        # Test with missing head entirely
        event2 = self._create_pr_event(
            event_type=WebhookEventType.PR_OPENED,
            head_ref="",
        )
        del event2.raw_payload["pull_request"]["head"]
        assert should_skip_orchestrator_pr_event(event2) is False

    def test_missing_pull_request_is_handled(self):
        """
        Test that events with missing pull_request are handled gracefully.
        """
        event = self._create_pr_event(
            event_type=WebhookEventType.PR_OPENED,
            head_ref="orchestrator/docs-test",
        )
        del event.raw_payload["pull_request"]
        assert should_skip_orchestrator_pr_event(event) is False

    def test_none_raw_payload_is_handled(self):
        """
        Test that events with None raw_payload are handled gracefully.
        """
        event = self._create_pr_event(
            event_type=WebhookEventType.PR_OPENED,
            head_ref="orchestrator/docs-test",
        )
        event.raw_payload = None
        assert should_skip_orchestrator_pr_event(event) is False


class TestEventNormalizerOrchestratorFiltering:
    """
    Integration tests for EventNormalizer.is_actionable() with orchestrator PR filtering.

    These tests verify that the normalizer correctly uses should_skip_orchestrator_pr_event()
    to prevent docs PR noise.
    """

    def _create_pr_opened_event(
        self,
        head_ref: str,
        actor_name: str = "RC918",
    ) -> WebhookEvent:
        """Create a PR_OPENED event for testing."""
        return WebhookEvent(
            event_id="test-event-456",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "action": "opened",
                "pull_request": {
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test PR body",
                    "head": {"ref": head_ref},
                    "base": {"ref": "main"},
                },
                "repository": {"owner": {"login": "RC918"}, "name": "morningai"},
                "sender": {"login": actor_name},
            },
            title="Test PR",
            description="Test PR body",
            url="https://github.com/RC918/morningai/pull/123",
            actor_id="12345",
            actor_name=actor_name,
            resource_id="123",
            resource_type="pull_request",
            resource_url="https://github.com/RC918/morningai/pull/123",
            repo_owner="RC918",
            repo_name="morningai",
            labels=[],
            assignees=[],
            metadata={"github_event": "pull_request", "action": "opened"},
        )

    def test_orchestrator_pr_is_not_actionable(self):
        """
        Test that a PR from orchestrator/* branch is NOT actionable.

        This is the core integration test - verifying that the normalizer
        correctly identifies and skips orchestrator-generated PRs.
        """
        normalizer = EventNormalizer()
        event = self._create_pr_opened_event(head_ref="orchestrator/docs-readme-abc123")

        # The event should NOT be actionable because it's from an orchestrator branch
        assert normalizer.is_actionable(event) is False

    def test_regular_pr_is_actionable(self):
        """
        Test that a PR from a regular branch IS actionable.

        This ensures we don't accidentally block legitimate PRs.
        """
        normalizer = EventNormalizer()
        event = self._create_pr_opened_event(head_ref="feature/new-feature")

        # The event SHOULD be actionable because it's from a regular branch
        assert normalizer.is_actionable(event) is True

    def test_devin_branch_pr_is_actionable(self):
        """
        Test that a PR from devin/* branch IS actionable.

        Devin-generated PRs should still be processed by the orchestrator.
        """
        normalizer = EventNormalizer()
        event = self._create_pr_opened_event(head_ref="devin/1234567890-some-task")

        # The event SHOULD be actionable because devin branches are not orchestrator branches
        assert normalizer.is_actionable(event) is True


class TestFullWebhookFlowOrchestratorFiltering:
    """
    End-to-end integration tests simulating the complete webhook flow for orchestrator filtering.

    These tests simulate:
    1. Orchestrator creates a docs PR (branch: orchestrator/docs-*)
    2. GitHub sends a PR_OPENED webhook
    3. Normalizer parses the webhook
    4. Normalizer determines actionability
    5. Verify no new task is created (noise prevented)
    """

    def test_complete_orchestrator_pr_filtering_flow(self):
        """
        Test the complete flow from webhook payload to actionability decision.

        This simulates the exact scenario that causes docs PR noise:
        1. Orchestrator creates a docs PR with branch orchestrator/docs-*
        2. GitHub sends webhook with the PR data
        3. Normalizer should detect the orchestrator branch and skip
        """
        # Simulate the GitHub webhook payload for an orchestrator-generated PR
        github_webhook_payload = {
            "action": "opened",
            "pull_request": {
                "number": 2957,
                "title": "docs: update README for feature X",
                "body": "Auto-generated documentation update.",
                "html_url": "https://github.com/RC918/morningai/pull/2957",
                "state": "open",
                "head": {
                    "ref": "orchestrator/docs-readme-abc123def456",
                    "sha": "abc123def456",
                },
                "base": {
                    "ref": "main",
                },
                "user": {"login": "RC918"},  # Uses human PAT
            },
            "repository": {
                "id": 123456,
                "name": "morningai",
                "full_name": "RC918/morningai",
                "owner": {"login": "RC918"},
            },
            "sender": {
                "login": "RC918",
                "id": 67890,
                "type": "User",
            },
        }

        github_webhook_headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-123",
            "X-Hub-Signature-256": "sha256=fake_signature",
        }

        # Parse the webhook using the normalizer
        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        # Verify the event was parsed correctly
        assert event is not None
        assert event.event_type == WebhookEventType.PR_OPENED
        assert event.actor_name == "RC918"
        assert event.repo_owner == "RC918"
        assert event.repo_name == "morningai"

        # THE KEY ASSERTION: The event should NOT be actionable
        # because it's from an orchestrator/* branch
        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is False, (
            "Orchestrator-generated PR should NOT be actionable! "
            "This would cause docs PR noise."
        )

    def test_regular_pr_flow_is_actionable(self):
        """
        Test that regular PRs (not from orchestrator branches) are correctly processed.

        This ensures we don't accidentally block legitimate PRs.
        """
        github_webhook_payload = {
            "action": "opened",
            "pull_request": {
                "number": 2958,
                "title": "feat: add new feature",
                "body": "This PR adds a new feature.",
                "html_url": "https://github.com/RC918/morningai/pull/2958",
                "state": "open",
                "head": {
                    "ref": "feature/new-feature",
                    "sha": "xyz789",
                },
                "base": {
                    "ref": "main",
                },
                "user": {"login": "developer"},
            },
            "repository": {
                "name": "morningai",
                "owner": {"login": "RC918"},
            },
            "sender": {"login": "developer", "id": 11111},
        }

        github_webhook_headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-456",
        }

        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        assert event is not None
        assert event.event_type == WebhookEventType.PR_OPENED

        # Regular PRs SHOULD be actionable
        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is True, (
            "Regular PRs should be actionable! "
            "We should not block legitimate PRs."
        )

    def test_pr_merged_from_orchestrator_branch_is_not_actionable(self):
        """
        Test that PR_MERGED events from orchestrator branches are also filtered.

        When an orchestrator-generated docs PR is merged, we should also skip it.
        """
        github_webhook_payload = {
            "action": "closed",
            "pull_request": {
                "number": 2957,
                "title": "docs: update README",
                "body": "Auto-generated documentation update.",
                "merged": True,
                "head": {
                    "ref": "orchestrator/docs-readme-abc123",
                },
                "base": {
                    "ref": "main",
                },
            },
            "repository": {
                "name": "morningai",
                "owner": {"login": "RC918"},
            },
            "sender": {"login": "RC918"},
        }

        github_webhook_headers = {
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-789",
        }

        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        assert event is not None
        # PR_MERGED is determined by action=closed + merged=true
        assert event.event_type in {WebhookEventType.PR_MERGED, WebhookEventType.PR_CLOSED}

        # Orchestrator PRs should NOT be actionable even when merged
        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is False
