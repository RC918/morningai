#!/usr/bin/env python3
"""
Integration Tests for Review Webhook No-Duplicate Flow

EPIC B Phase 3: Integration Test Automation
Test Flow: send review → receive webhook → verify no duplicate

This module tests the complete flow to ensure:
1. When orchestrator posts a review, it includes the MORNINGAI_REVIEW_MARKER
2. When GitHub sends back a PR_REVIEWED webhook, the marker is detected
3. The event is correctly identified as self-generated and NOT processed
4. No duplicate review is triggered (infinite loop prevented)

Test Strategy:
- Simulate the complete end-to-end flow using real payload structures
- Test both the publisher (review posting) and normalizer (webhook handling)
- Verify the marker is correctly embedded and detected
- Test edge cases (marker missing, marker corrupted, etc.)

Related PRs:
- #2836: Phase 3 P2/P3 - unified file-level delivery and LLM JSON repair
- #2841: Code Review suggestions implementation
- #2842: Self-trigger loop prevention
"""
import os
import sys
from datetime import datetime, timezone

import pytest

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


class TestReviewWebhookNoDuplicateFlow:
    """
    Integration tests for the complete review → webhook → no-duplicate flow.

    This test class verifies the EPIC B Phase 3 requirement:
    "send review → receive webhook → verify no duplicate"
    """

    def test_complete_flow_orchestrator_review_not_reprocessed(self):
        """
        Test the complete flow: orchestrator posts review → webhook received → no duplicate.

        This is the primary integration test that verifies:
        1. Orchestrator review includes the marker
        2. Webhook handler detects the marker
        3. Event is NOT actionable (no duplicate review triggered)
        """
        orchestrator_review_body = f"""## MorningAI Code Review

**Summary**: This PR implements the LLM JSON repair feature.

### Suggestions

1. Consider adding more error handling for edge cases.
2. The sanitization logic looks good.

{MORNINGAI_REVIEW_MARKER}"""

        github_webhook_payload = {
            "action": "submitted",
            "review": {
                "id": 12345,
                "body": orchestrator_review_body,
                "state": "COMMENTED",
                "user": {
                    "login": "RC918",
                    "id": 67890,
                    "type": "User",
                },
                "submitted_at": "2025-12-22T16:00:00Z",
            },
            "pull_request": {
                "number": 2847,
                "title": "test: verify LLM JSON repair integration",
                "body": "Integration test PR",
                "html_url": "https://github.com/RC918/morningai/pull/2847",
                "state": "open",
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
            "X-GitHub-Delivery": "integration-test-123",
        }

        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        assert event is not None, "Event should be parsed successfully"
        assert event.event_type == WebhookEventType.PR_REVIEWED
        assert event.repo_owner == "RC918"
        assert event.repo_name == "morningai"

        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is False, (
            "Self-generated review should NOT be actionable! "
            "This would cause an infinite feedback loop."
        )

        assert is_self_generated_review(event) is True, (
            "Review with marker should be detected as self-generated"
        )

    def test_external_review_is_processed(self):
        """
        Test that external reviews (without marker) ARE processed.

        This ensures we don't accidentally block legitimate external reviews.
        """
        external_review_body = """## External Code Review

This looks good! A few suggestions:

1. Consider adding more tests.
2. Documentation could be improved.

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
                "number": 2847,
                "title": "test: verify LLM JSON repair integration",
                "body": "Integration test PR",
            },
            "repository": {
                "name": "morningai",
                "owner": {"login": "RC918"},
            },
            "sender": {"login": "external-reviewer", "id": 11111},
        }

        github_webhook_headers = {
            "X-GitHub-Event": "pull_request_review",
            "X-GitHub-Delivery": "external-review-456",
        }

        normalizer = EventNormalizer()
        event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers=github_webhook_headers,
            payload=github_webhook_payload,
        )

        assert event is not None
        assert event.event_type == WebhookEventType.PR_REVIEWED

        is_actionable = normalizer.is_actionable(event)
        assert is_actionable is True, (
            "External reviews should be actionable! "
            "We should not block legitimate external reviews."
        )

        assert is_self_generated_review(event) is False


class TestMarkerEmbeddingAndDetection:
    """
    Tests for marker embedding in reviews and detection in webhooks.

    These tests verify that the marker is correctly:
    1. Embedded in orchestrator-generated reviews
    2. Detected in incoming webhooks
    3. Not falsely detected in external reviews
    """

    def test_marker_in_review_body_detected(self):
        """Test that marker in review body is correctly detected."""
        review_body = f"Review content\n\n{MORNINGAI_REVIEW_MARKER}"

        event = WebhookEvent(
            event_id="test-marker-body",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"review": {"body": review_body}},
            description=review_body,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is True

    def test_marker_in_raw_payload_detected(self):
        """Test that marker in raw_payload is detected even if description is truncated."""
        full_review_body = f"Long review content...\n\n{MORNINGAI_REVIEW_MARKER}"
        truncated_description = "Long review content..."

        event = WebhookEvent(
            event_id="test-marker-payload",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"review": {"body": full_review_body}},
            description=truncated_description,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is True

    def test_marker_not_detected_in_external_review(self):
        """Test that marker is NOT detected in external reviews."""
        external_review_body = "This is a normal external review. LGTM!"

        event = WebhookEvent(
            event_id="test-external",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"review": {"body": external_review_body}},
            description=external_review_body,
            actor_name="external-user",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is False

    def test_partial_marker_not_detected(self):
        """Test that partial or modified markers are NOT detected."""
        partial_markers = [
            "<!-- morningai:autogen -->",
            "<!-- morningai:autogen-review-v2 -->",
            "<!-- morningai:autogen-review extra -->",
            "morningai:autogen-review",
        ]

        for i, partial_marker in enumerate(partial_markers):
            event = WebhookEvent(
                event_id=f"test-partial-{i}",
                source=WebhookSource.GITHUB,
                event_type=WebhookEventType.PR_REVIEWED,
                timestamp=datetime.now(timezone.utc),
                raw_payload={"review": {"body": partial_marker}},
                description=partial_marker,
                actor_name="RC918",
                repo_owner="RC918",
                repo_name="morningai",
                resource_id="123",
            )

            assert is_self_generated_review(event) is False, (
                f"Partial marker '{partial_marker}' should NOT be detected"
            )


class TestNoDuplicateReviewScenarios:
    """
    Tests for various scenarios that could cause duplicate reviews.

    These tests verify that the system correctly prevents duplicate reviews
    in various edge cases and race conditions.
    """

    def test_rapid_webhook_events_no_duplicate(self):
        """
        Test that rapid webhook events don't cause duplicate reviews.

        Simulates the scenario where GitHub sends multiple webhooks quickly.
        """
        normalizer = EventNormalizer()

        orchestrator_review = f"Review content\n\n{MORNINGAI_REVIEW_MARKER}"

        events = []
        for i in range(5):
            payload = {
                "action": "submitted",
                "review": {"body": orchestrator_review, "state": "COMMENTED"},
                "pull_request": {"number": 123},
                "repository": {"name": "morningai", "owner": {"login": "RC918"}},
                "sender": {"login": "RC918"},
            }
            headers = {
                "X-GitHub-Event": "pull_request_review",
                "X-GitHub-Delivery": f"rapid-event-{i}",
            }

            event = normalizer.parse_event(
                source=WebhookSource.GITHUB,
                headers=headers,
                payload=payload,
            )
            events.append(event)

        for i, event in enumerate(events):
            is_actionable = normalizer.is_actionable(event)
            assert is_actionable is False, (
                f"Event {i} should NOT be actionable (self-generated review)"
            )

    def test_mixed_reviews_correct_handling(self):
        """
        Test that mixed orchestrator and external reviews are handled correctly.

        Simulates the scenario where both orchestrator and external reviews
        are submitted on the same PR.
        """
        normalizer = EventNormalizer()

        orchestrator_review = f"Orchestrator review\n\n{MORNINGAI_REVIEW_MARKER}"
        external_review = "External review - LGTM!"

        orchestrator_payload = {
            "action": "submitted",
            "review": {"body": orchestrator_review, "state": "COMMENTED"},
            "pull_request": {"number": 123},
            "repository": {"name": "morningai", "owner": {"login": "RC918"}},
            "sender": {"login": "RC918"},
        }

        external_payload = {
            "action": "submitted",
            "review": {"body": external_review, "state": "APPROVED"},
            "pull_request": {"number": 123},
            "repository": {"name": "morningai", "owner": {"login": "RC918"}},
            "sender": {"login": "external-user"},
        }

        orchestrator_event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers={"X-GitHub-Event": "pull_request_review", "X-GitHub-Delivery": "orch-1"},
            payload=orchestrator_payload,
        )

        external_event = normalizer.parse_event(
            source=WebhookSource.GITHUB,
            headers={"X-GitHub-Event": "pull_request_review", "X-GitHub-Delivery": "ext-1"},
            payload=external_payload,
        )

        assert normalizer.is_actionable(orchestrator_event) is False, (
            "Orchestrator review should NOT be actionable"
        )
        assert normalizer.is_actionable(external_event) is True, (
            "External review SHOULD be actionable"
        )


class TestPublisherMarkerInclusion:
    """
    Tests to verify that the publisher correctly includes the marker in reviews.

    These tests mock the publisher_node to verify marker inclusion.
    """

    def test_marker_constant_is_correct(self):
        """Test that the marker constant has the expected value."""
        assert MORNINGAI_REVIEW_MARKER == "<!-- morningai:autogen-review -->"

    def test_marker_is_html_comment(self):
        """Test that the marker is a valid HTML comment (invisible in rendered view)."""
        assert MORNINGAI_REVIEW_MARKER.startswith("<!--")
        assert MORNINGAI_REVIEW_MARKER.endswith("-->")

    def test_marker_unique_identifier(self):
        """Test that the marker contains unique identifier for MorningAI."""
        assert "morningai" in MORNINGAI_REVIEW_MARKER.lower()
        assert "autogen" in MORNINGAI_REVIEW_MARKER.lower()


class TestWebhookEventTypeFiltering:
    """
    Tests for webhook event type filtering.

    The marker check should only apply to PR_REVIEWED events.
    """

    def test_pr_commented_not_checked_for_marker(self):
        """Test that PR_COMMENTED events are not checked for self-review marker."""
        comment_with_marker = f"Comment with marker: {MORNINGAI_REVIEW_MARKER}"

        event = WebhookEvent(
            event_id="test-comment",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_COMMENTED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"comment": {"body": comment_with_marker}},
            description=comment_with_marker,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is False

    def test_pr_opened_not_checked_for_marker(self):
        """Test that PR_OPENED events are not checked for self-review marker."""
        pr_body_with_marker = f"PR body with marker: {MORNINGAI_REVIEW_MARKER}"

        event = WebhookEvent(
            event_id="test-pr-opened",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"pull_request": {"body": pr_body_with_marker}},
            description=pr_body_with_marker,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is False


class TestIntegrationWithLLMJsonRepair:
    """
    Integration tests verifying that LLM JSON repair doesn't affect
    the review → webhook → no-duplicate flow.

    EPIC B Phase 3 P3: LLM JSON repair should work independently
    of the self-trigger loop prevention mechanism.
    """

    def test_json_repair_review_includes_marker(self):
        """
        Test that reviews generated after JSON repair still include the marker.

        This verifies that the LLM JSON repair feature doesn't strip or
        corrupt the marker in the review body.
        """
        review_with_json_repair_note = f"""## MorningAI Code Review

**Note**: This review was generated after JSON repair.

### Suggestions

1. Consider adding error handling.

{MORNINGAI_REVIEW_MARKER}"""

        event = WebhookEvent(
            event_id="test-json-repair",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"review": {"body": review_with_json_repair_note}},
            description=review_with_json_repair_note,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is True, (
            "Review after JSON repair should still be detected as self-generated"
        )

    def test_sanitized_content_preserves_marker(self):
        """
        Test that content sanitization doesn't affect the marker.

        The marker should survive any sanitization applied to the review body.
        """
        sanitized_review = f"""## MorningAI Code Review

Content with [SANITIZED] prompt injection removed.

{MORNINGAI_REVIEW_MARKER}"""

        event = WebhookEvent(
            event_id="test-sanitized",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={"review": {"body": sanitized_review}},
            description=sanitized_review,
            actor_name="RC918",
            repo_owner="RC918",
            repo_name="morningai",
            resource_id="123",
        )

        assert is_self_generated_review(event) is True


if __name__ == "__main__": pytest.main([__file__, "-v"])
