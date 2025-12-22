#!/usr/bin/env python3
"""
Integration Tests for Self-Trigger Loop Prevention

This module tests the complete flow of self-trigger loop prevention:
1. Orchestrator posts a review with marker → GitHub sends PR_REVIEWED webhook
2. Normalizer detects the marker and skips the event
3. No new review is triggered (loop prevented)

Issue: Self-Trigger Loop Prevention
PR: #2842 - fix(orchestrator): prevent self-trigger feedback loop in PR reviews

Test Strategy:
- Use real payload structures (not mocks) to simulate GitHub webhooks
- Test the normalizer's is_actionable() decision point
- Verify both marker detection paths (description and raw_payload)
- Test edge cases (no marker, partial marker, marker in wrong location)
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import MORNINGAI_REVIEW_MARKER  # noqa: E402
from webhooks.bot_protocol import (  # noqa: E402
    WebhookEvent,
    WebhookEventType,
    WebhookSource,
)
from webhooks.normalizer import (  # noqa: E402
    EventNormalizer,
    is_self_generated_review,
)


class TestSelfTriggerLoopPrevention:
    """
    Integration tests for the self-trigger loop prevention mechanism.

    These tests verify the complete flow from webhook payload to actionability decision,
    ensuring that orchestrator-generated reviews are correctly identified and skipped.
    """

    def _create_pr_reviewed_event(
        self,
        review_body: str,
        actor_name: str = "RC918",
        repo_owner: str = "RC918",
        repo_name: str = "morningai",
        pr_number: int = 123,
    ) -> WebhookEvent:
        """
        Create a PR_REVIEWED WebhookEvent with the given review body.

        This simulates the event that would be created by GitHubWebhookHandler.parse_event()
        when GitHub sends a pull_request_review webhook.
        """
        return WebhookEvent(
            event_id="test-event-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "action": "submitted",
                "review": {
                    "body": review_body,
                    "state": "COMMENTED",
                    "user": {"login": actor_name},
                },
                "pull_request": {
                    "number": pr_number,
                    "title": "Test PR",
                    "body": "Test PR body",
                },
                "repository": {
                    "owner": {"login": repo_owner},
                    "name": repo_name,
                },
                "sender": {"login": actor_name, "id": 12345},
            },
            title="Test PR",
            description=review_body,  # PR_REVIEWED events use review body as description
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
                "github_event": "pull_request_review",
                "action": "submitted",
            },
        )

    def test_self_generated_review_detected_via_description(self):
        """
        Test that a review with the marker in description is detected as self-generated.

        This is the primary detection path - the marker is in the review body which
        becomes the event description.
        """
        review_body = f"## Code Review\n\nThis is a test review.\n\n{MORNINGAI_REVIEW_MARKER}"
        event = self._create_pr_reviewed_event(review_body=review_body)

        assert is_self_generated_review(event) is True

    def test_self_generated_review_detected_via_raw_payload(self):
        """
        Test that a review with the marker in raw_payload is detected as self-generated.

        This is the fallback detection path - if description is truncated, we check
        the raw payload's review.body field.
        """
        review_body = f"## Code Review\n\n{MORNINGAI_REVIEW_MARKER}\n\nThis is a test review."

        # Create event with truncated description but full marker in raw_payload
        event = self._create_pr_reviewed_event(review_body="## Code Review...")
        event.raw_payload["review"]["body"] = review_body

        assert is_self_generated_review(event) is True

    def test_external_review_not_detected_as_self_generated(self):
        """
        Test that a review WITHOUT the marker is NOT detected as self-generated.

        This ensures we don't accidentally skip legitimate external reviews.
        """
        review_body = "## Code Review\n\nThis is a legitimate external review.\n\nLGTM!"
        event = self._create_pr_reviewed_event(review_body=review_body)

        assert is_self_generated_review(event) is False

    def test_non_pr_reviewed_event_not_detected_as_self_generated(self):
        """
        Test that non-PR_REVIEWED events are never detected as self-generated.

        The marker check should only apply to PR_REVIEWED events.
        """
        event = self._create_pr_reviewed_event(
            review_body=f"Test with marker: {MORNINGAI_REVIEW_MARKER}"
        )
        # Change event type to something else
        event.event_type = WebhookEventType.PR_COMMENTED

        assert is_self_generated_review(event) is False

    def test_marker_must_be_exact_match(self):
        """
        Test that partial or modified markers are NOT detected.

        This ensures we don't have false positives from similar-looking comments.
        """
        # Partial marker
        event1 = self._create_pr_reviewed_event(review_body="<!-- morningai:autogen -->")
        assert is_self_generated_review(event1) is False

        # Modified marker
        event2 = self._create_pr_reviewed_event(review_body="<!-- morningai:autogen-review-v2 -->")
        assert is_self_generated_review(event2) is False

        # Marker with extra content inside
        event3 = self._create_pr_reviewed_event(review_body="<!-- morningai:autogen-review extra -->")
        assert is_self_generated_review(event3) is False


class TestEventNormalizerSelfTriggerIntegration:
    """
    Integration tests for EventNormalizer.is_actionable() with self-trigger prevention.

    These tests verify that the normalizer correctly uses is_self_generated_review()
    to prevent self-trigger loops.
    """

    def _create_pr_reviewed_event(
        self,
        review_body: str,
        actor_name: str = "RC918",
    ) -> WebhookEvent:
        """Create a PR_REVIEWED event for testing."""
        return WebhookEvent(
            event_id="test-event-456",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "action": "submitted",
                "review": {"body": review_body, "state": "COMMENTED"},
                "pull_request": {"number": 123},
                "repository": {"owner": {"login": "RC918"}, "name": "morningai"},
                "sender": {"login": actor_name},
            },
            title="Test PR",
            description=review_body,
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
            metadata={"github_event": "pull_request_review", "action": "submitted"},
        )

    def test_self_generated_review_is_not_actionable(self):
        """
        Test that a self-generated review is NOT actionable.

        This is the core integration test - verifying that the normalizer
        correctly identifies and skips orchestrator-generated reviews.
        """
        normalizer = EventNormalizer()
        review_body = f"## MorningAI Code Review\n\n{MORNINGAI_REVIEW_MARKER}\n\nTest review content."
        event = self._create_pr_reviewed_event(review_body=review_body)

        # The event should NOT be actionable because it contains our marker
        assert normalizer.is_actionable(event) is False

    def test_external_review_is_actionable(self):
        """
        Test that an external review (without marker) IS actionable.

        This ensures we don't accidentally block legitimate external reviews.
        """
        normalizer = EventNormalizer()
        review_body = "## External Review\n\nThis is a legitimate review from a human or external bot."
        event = self._create_pr_reviewed_event(review_body=review_body)

        # The event SHOULD be actionable because it doesn't contain our marker
        assert normalizer.is_actionable(event) is True


class TestFullWebhookFlowIntegration:
    """
    End-to-end integration tests simulating the complete webhook flow.

    These tests simulate:
    1. Orchestrator posts a review (with marker)
    2. GitHub sends a PR_REVIEWED webhook
    3. Normalizer parses the webhook
    4. Normalizer determines actionability
    5. Verify no new task is created (loop prevented)
    """

    def test_complete_self_trigger_prevention_flow(self):
        """
        Test the complete flow from webhook payload to actionability decision.

        This simulates the exact scenario that caused the infinite loop:
        1. Orchestrator posts a review with marker
        2. GitHub sends webhook with the review body
        3. Normalizer should detect the marker and skip
        """
        # Simulate the review body that orchestrator would post
        orchestrator_review_body = f"""## MorningAI Code Review

**Summary**: This PR looks good overall.

### Suggestions

1. Consider adding more tests.
2. Documentation could be improved.

{MORNINGAI_REVIEW_MARKER}"""

        # Simulate the GitHub webhook payload
        github_webhook_payload = {
            "action": "submitted",
            "review": {
                "id": 12345,
                "body": orchestrator_review_body,
                "state": "COMMENTED",
                "user": {
                    "login": "RC918",  # Human PAT, not a bot
                    "id": 67890,
                    "type": "User",
                },
                "submitted_at": "2025-12-22T12:00:00Z",
            },
            "pull_request": {
                "number": 2842,
                "title": "fix: prevent self-trigger feedback loop",
                "body": "This PR fixes the self-trigger loop issue.",
                "html_url": "https://github.com/RC918/morningai/pull/2842",
                "state": "open",
                "user": {"login": "devin-ai-integration[bot]"},
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
            "X-GitHub-Event": "pull_request_review",
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
        assert event.event_type == WebhookEventType.PR_REVIEWED
        assert event.actor_name == "RC918"
        assert event.repo_owner == "RC918"
        assert event.repo_name == "morningai"

        # THE KEY ASSERTION: The event should NOT be actionable
        # because it contains our self-review marker
        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is False, (
            "Self-generated review should NOT be actionable! "
            "This would cause an infinite feedback loop."
        )

    def test_external_review_flow_is_actionable(self):
        """
        Test that external reviews (without marker) are correctly processed.

        This ensures we don't accidentally block legitimate reviews.
        """
        # Simulate an external review (e.g., from a human reviewer)
        external_review_body = """## Code Review

This looks good! A few minor suggestions:

1. Consider renaming this variable for clarity.
2. Add a docstring to this function.

LGTM!"""

        github_webhook_payload = {
            "action": "submitted",
            "review": {
                "id": 99999,
                "body": external_review_body,
                "state": "APPROVED",
                "user": {"login": "external-reviewer", "id": 11111, "type": "User"},
            },
            "pull_request": {
                "number": 2842,
                "title": "fix: prevent self-trigger feedback loop",
                "body": "This PR fixes the self-trigger loop issue.",
                "html_url": "https://github.com/RC918/morningai/pull/2842",
            },
            "repository": {
                "name": "morningai",
                "owner": {"login": "RC918"},
            },
            "sender": {"login": "external-reviewer", "id": 11111},
        }

        github_webhook_headers = {
            "X-GitHub-Event": "pull_request_review",
            "X-GitHub-Delivery": "test-delivery-456",
        }

        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        assert event is not None
        assert event.event_type == WebhookEventType.PR_REVIEWED

        # External reviews SHOULD be actionable
        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is True, (
            "External reviews should be actionable! "
            "We should not block legitimate external reviews."
        )


class TestMarkerSpoofingProtection:
    """
    Tests for marker spoofing protection.

    Issue: External reviewers could potentially add the marker to their reviews
    to bypass processing. These tests document the current behavior and
    potential future enhancements.

    Note: Current implementation does NOT protect against spoofing.
    This is documented as a known limitation in PR #2842.
    """

    def test_spoofed_marker_is_currently_detected(self):
        """
        Test that a spoofed marker IS currently detected (known limitation).

        This documents the current behavior where an external reviewer could
        add the marker to their review to bypass processing.

        Future enhancement: Add additional validation (e.g., check reviewer ID,
        check if review was posted via our API, etc.)
        """
        # Simulate an external reviewer adding our marker to their review
        spoofed_review_body = f"""## Malicious Review

I'm adding the marker to bypass processing:
{MORNINGAI_REVIEW_MARKER}

This review should probably still be processed."""

        event = WebhookEvent(
            event_id="spoofed-event",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={
                "review": {"body": spoofed_review_body},
                "sender": {"login": "malicious-user"},
            },
            description=spoofed_review_body,
            actor_name="malicious-user",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        # Current behavior: spoofed marker IS detected (known limitation)
        # This test documents the current behavior, not the desired behavior
        assert is_self_generated_review(event) is True, (
            "Current implementation detects spoofed markers. "
            "This is a known limitation documented in PR #2842."
        )
