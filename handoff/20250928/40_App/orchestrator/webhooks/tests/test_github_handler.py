"""
Tests for GitHubWebhookHandler - AI Reviewer Integration

Issue: #2209 - 修復 AI Reviewer 評論接收機制
Milestone: Phase 7 - 生態系閉環 (AI Review Closed Loop)
"""

import pytest
from datetime import datetime, timezone

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..handlers.github_handler import (
    GitHubWebhookHandler,
    AI_REVIEWER_BOTS,
)


@pytest.fixture
def github_handler():
    """Create a GitHubWebhookHandler instance for testing"""
    return GitHubWebhookHandler()


@pytest.fixture
def mock_pr_review_headers():
    """Create mock headers for a PR review event (lowercase keys per HTTP best practice)"""
    return {
        "x-github-event": "pull_request_review",
        "x-github-delivery": "test-delivery-123",
        "x-hub-signature-256": "sha256=test",
    }


@pytest.fixture
def mock_pr_comment_headers():
    """Create mock headers for a PR comment event (lowercase keys per HTTP best practice)"""
    return {
        "x-github-event": "pull_request_review_comment",
        "x-github-delivery": "test-delivery-456",
        "x-hub-signature-256": "sha256=test",
    }


@pytest.fixture
def mock_pr_review_headers_mixed_case():
    """Create mock headers with mixed case to test defensive normalization"""
    return {
        "X-GitHub-Event": "pull_request_review",
        "X-GitHub-Delivery": "test-delivery-789",
        "X-Hub-Signature-256": "sha256=test",
    }


def create_mock_payload(actor_name: str, actor_id: int = 12345) -> dict:
    """Create a mock GitHub webhook payload with specified actor"""
    return {
        "action": "submitted",
        "sender": {
            "login": actor_name,
            "id": actor_id,
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-owner"},
        },
        "pull_request": {
            "number": 123,
            "title": "Test PR",
            "body": "Test PR description",
            "html_url": "https://github.com/test-owner/test-repo/pull/123",
            "labels": [],
            "assignees": [],
        },
        "review": {
            "body": "This code looks good, but consider refactoring the function.",
            "state": "commented",
        },
    }


class TestAIReviewerBotWhitelist:
    """Tests for AI Reviewer bot whitelist"""

    def test_whitelist_contains_expected_bots(self):
        """Test that the whitelist contains expected AI reviewer bots"""
        expected_bots = [
            "github-copilot[bot]",
            "copilot[bot]",
            "gemini-code-assist[bot]",
            "coderabbitai[bot]",
            "devin-ai-integration[bot]",
        ]
        for bot in expected_bots:
            assert bot in AI_REVIEWER_BOTS, f"Expected {bot} in whitelist"

    def test_whitelist_maps_to_correct_sources(self):
        """Test that bots map to correct review sources"""
        assert AI_REVIEWER_BOTS["github-copilot[bot]"] == "copilot"
        assert AI_REVIEWER_BOTS["gemini-code-assist[bot]"] == "gemini"
        assert AI_REVIEWER_BOTS["coderabbitai[bot]"] == "coderabbit"
        assert AI_REVIEWER_BOTS["devin-ai-integration[bot]"] == "devin"


class TestGitHubHandlerShouldProcess:
    """Tests for GitHubWebhookHandler.should_process with AI reviewers"""

    def test_should_process_human_user(self, github_handler):
        """Test that human user events are processed"""
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="human-user",
            metadata={},
        )
        assert github_handler.should_process(event) is True

    def test_should_process_whitelisted_ai_reviewer(self, github_handler):
        """Test that whitelisted AI reviewer events are processed"""
        for bot_name in AI_REVIEWER_BOTS.keys():
            event = WebhookEvent(
                event_id="test-123",
                source=WebhookSource.GITHUB,
                event_type=WebhookEventType.PR_REVIEWED,
                timestamp=datetime.now(timezone.utc),
                raw_payload={},
                actor_name=bot_name,
                metadata={},
            )
            assert github_handler.should_process(event) is True, \
                f"Expected {bot_name} to be processed"

    def test_should_not_process_non_whitelisted_bot(self, github_handler):
        """Test that non-whitelisted bot events are filtered out"""
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_REVIEWED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="random-bot[bot]",
            metadata={},
        )
        assert github_handler.should_process(event) is False

    def test_should_process_dependabot_for_pr_events(self, github_handler):
        """Test that dependabot is allowed for PR events (automation bot allowlist)"""
        # Dependabot is in ALLOWED_AUTOMATION_BOTS and should be allowed for PR events
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="dependabot[bot]",
            metadata={},
        )
        assert github_handler.should_process(event) is True

    def test_should_not_process_dependabot_for_non_pr_events(self, github_handler):
        """Test that dependabot is filtered out for non-PR events"""
        # Dependabot should be rejected for non-PR events to avoid loops
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.ISSUE_CREATED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="dependabot[bot]",
            metadata={},
        )
        assert github_handler.should_process(event) is False

    def test_should_process_github_actions_for_pr_events(self, github_handler):
        """Test that github-actions[bot] is allowed for PR events"""
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_OPENED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            metadata={},
        )
        assert github_handler.should_process(event) is True

    def test_should_not_process_github_actions_for_non_pr_events(self, github_handler):
        """Test that github-actions[bot] is filtered out for non-PR events"""
        event = WebhookEvent(
            event_id="test-123",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.ISSUE_COMMENTED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            actor_name="github-actions[bot]",
            metadata={},
        )
        assert github_handler.should_process(event) is False


class TestGitHubHandlerParseEvent:
    """Tests for GitHubWebhookHandler.parse_event with AI reviewers"""

    def test_parse_event_adds_review_source_for_ai_reviewer(
        self, github_handler, mock_pr_review_headers
    ):
        """Test that parse_event adds review_source metadata for AI reviewers"""
        payload = create_mock_payload("gemini-code-assist[bot]")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.metadata.get("review_source") == "gemini"
        assert event.metadata.get("is_ai_reviewer") is True

    def test_parse_event_adds_review_source_for_copilot(
        self, github_handler, mock_pr_review_headers
    ):
        """Test that parse_event adds review_source for Copilot"""
        payload = create_mock_payload("github-copilot[bot]")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.metadata.get("review_source") == "copilot"
        assert event.metadata.get("is_ai_reviewer") is True

    def test_parse_event_adds_review_source_for_coderabbit(
        self, github_handler, mock_pr_review_headers
    ):
        """Test that parse_event adds review_source for CodeRabbit"""
        payload = create_mock_payload("coderabbitai[bot]")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.metadata.get("review_source") == "coderabbit"
        assert event.metadata.get("is_ai_reviewer") is True

    def test_parse_event_no_review_source_for_human(
        self, github_handler, mock_pr_review_headers
    ):
        """Test that parse_event does not add review_source for human users"""
        payload = create_mock_payload("human-reviewer")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.metadata.get("review_source") is None
        assert event.metadata.get("is_ai_reviewer") is None

    def test_parse_event_no_review_source_for_non_whitelisted_bot(
        self, github_handler, mock_pr_review_headers
    ):
        """Test that parse_event does not add review_source for non-whitelisted bots"""
        payload = create_mock_payload("random-bot[bot]")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.metadata.get("review_source") is None
        assert event.metadata.get("is_ai_reviewer") is None


class TestGitHubHandlerEventTypes:
    """Tests for GitHub event type mapping"""

    def test_pr_review_event_type(self, github_handler, mock_pr_review_headers):
        """Test that PR review events are correctly typed"""
        payload = create_mock_payload("gemini-code-assist[bot]")
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        assert event.event_type == WebhookEventType.PR_REVIEWED

    def test_pr_comment_event_type(self, github_handler, mock_pr_comment_headers):
        """Test that PR comment events are correctly typed"""
        payload = create_mock_payload("gemini-code-assist[bot]")
        payload["action"] = "created"
        event = github_handler.parse_event(mock_pr_comment_headers, payload)

        assert event.event_type == WebhookEventType.PR_COMMENTED

    def test_pr_review_event_type_with_mixed_case_headers(
        self, github_handler, mock_pr_review_headers_mixed_case
    ):
        """Test that PR review events work with mixed-case headers (defensive normalization)"""
        payload = create_mock_payload("gemini-code-assist[bot]")
        event = github_handler.parse_event(mock_pr_review_headers_mixed_case, payload)

        # Should still correctly parse event type despite mixed-case headers
        assert event.event_type == WebhookEventType.PR_REVIEWED
        assert event.event_id == "test-delivery-789"


class TestAIReviewerIntegration:
    """Integration tests for AI reviewer workflow"""

    def test_full_ai_reviewer_workflow(
        self, github_handler, mock_pr_review_headers
    ):
        """Test complete workflow: parse -> should_process -> metadata"""
        # Simulate Gemini Code Assist review
        payload = create_mock_payload("gemini-code-assist[bot]")

        # Parse the event
        event = github_handler.parse_event(mock_pr_review_headers, payload)

        # Verify event is parsed correctly
        assert event.actor_name == "gemini-code-assist[bot]"
        assert event.event_type == WebhookEventType.PR_REVIEWED

        # Verify metadata is set
        assert event.metadata["review_source"] == "gemini"
        assert event.metadata["is_ai_reviewer"] is True

        # Verify event should be processed
        assert github_handler.should_process(event) is True

    def test_multiple_ai_reviewers_workflow(
        self, github_handler, mock_pr_review_headers
    ):
        """Test workflow with multiple AI reviewers"""
        ai_reviewers = [
            ("gemini-code-assist[bot]", "gemini"),
            ("github-copilot[bot]", "copilot"),
            ("coderabbitai[bot]", "coderabbit"),
            ("devin-ai-integration[bot]", "devin"),
        ]

        for bot_name, expected_source in ai_reviewers:
            payload = create_mock_payload(bot_name)
            event = github_handler.parse_event(mock_pr_review_headers, payload)

            assert event.metadata["review_source"] == expected_source
            assert github_handler.should_process(event) is True
