"""
Tests for Garbage PR Fix - Self-Trigger Loop Prevention

Issue: Garbage PR Fix (Dec 2025)
Root Cause: UNKNOWN events bypass should_skip_orchestrator_pr_event() and
trigger garbage PR creation via keyword matching in is_actionable().

This test file validates:
1. UNKNOWN events are not actionable (Fix 1)
2. should_skip_orchestrator_pr_event() checks PR events AND UNKNOWN events (Fix 2)
3. Branch detection works for CI events (check_suite, check_run, status)
4. Non-PR events (ISSUE_CREATED, etc.) are NOT checked by should_skip_orchestrator_pr_event
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource


# Create mock module for utils.constants
_mock_constants = MagicMock()
_mock_constants.LABEL_ORCHESTRATOR_DOCS = "orchestrator-docs"
_mock_constants.LABEL_ORCHESTRATOR_DOCS_TEST = "orchestrator-docs-test"


@pytest.fixture(autouse=True)
def mock_utils_constants():
    """Mock utils.constants module for tests"""
    with patch.dict("sys.modules", {"utils.constants": _mock_constants}):
        yield


from ..normalizer import EventNormalizer, should_skip_orchestrator_pr_event


@pytest.fixture
def event_normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


def create_mock_event(
    event_type: WebhookEventType = WebhookEventType.UNKNOWN,
    raw_payload: dict = None,
    title: str = "Test Event",
    description: str = "",
    labels: list = None,
) -> WebhookEvent:
    """Create a mock WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload=raw_payload or {},
        title=title,
        description=description,
        url="https://github.com/test/repo/pull/1",
        actor_name="test-actor",
        metadata={},
        labels=labels or [],
        repo_owner="test",
        repo_name="repo",
    )


class TestUnknownEventNotActionable:
    """Tests for Fix 1: UNKNOWN events should not be actionable"""

    def test_unknown_event_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events are not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            description="This contains add keyword",
        )
        assert event_normalizer.is_actionable(event) is False

    def test_unknown_event_with_action_keywords_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events with action keywords are still not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="Fix the bug",
            description="Please implement this feature and add tests",
        )
        assert event_normalizer.is_actionable(event) is False

    def test_unknown_event_with_ai_reviewer_metadata_not_actionable(self, event_normalizer):
        """Test that UNKNOWN events with AI reviewer metadata are not actionable"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            description="Suggestion: Consider refactoring",
        )
        event.metadata = {"is_ai_reviewer": True, "review_source": "gemini"}
        assert event_normalizer.is_actionable(event) is False

    def test_pr_opened_event_still_actionable(self, event_normalizer):
        """Test that PR_OPENED events are still actionable (regression test)"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            title="Fix the bug",
            description="This PR fixes a critical bug",
        )
        assert event_normalizer.is_actionable(event) is True


class TestShouldSkipOrchestratorEvent:
    """Tests for Fix 2: should_skip_orchestrator_pr_event() checks all event types"""

    def test_skip_pr_event_with_orchestrator_branch(self):
        """Test that PR events from orchestrator/* branches are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            raw_payload={
                "pull_request": {
                    "head": {"ref": "orchestrator/docs-test-123"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_check_suite(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (check_suite)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "head_branch": "orchestrator/docs-test-123"
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_check_run(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (check_run)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_run": {
                    "check_suite": {
                        "head_branch": "orchestrator/docs-test-123"
                    }
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_unknown_event_with_orchestrator_branch_in_status(self):
        """Test that UNKNOWN events from orchestrator/* branches are skipped (status)"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "branches": [
                    {"name": "orchestrator/docs-test-123"}
                ]
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_event_with_orchestrator_docs_label(self):
        """Test that events with orchestrator-docs label are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            labels=["orchestrator-docs"],
            raw_payload={
                "pull_request": {
                    "head": {"ref": "devin/some-branch"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_skip_event_with_orchestrator_docs_test_label(self):
        """Test that events with orchestrator-docs-test label are skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            labels=["orchestrator-docs-test"],
            raw_payload={
                "pull_request": {
                    "head": {"ref": "devin/some-branch"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is True

    def test_not_skip_regular_pr_event(self):
        """Test that regular PR events are not skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.PR_OPENED,
            raw_payload={
                "pull_request": {
                    "head": {"ref": "feature/new-feature"}
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_not_skip_unknown_event_without_orchestrator_branch(self):
        """Test that UNKNOWN events without orchestrator branch are not skipped"""
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            raw_payload={
                "check_suite": {
                    "head_branch": "main"
                }
            },
        )
        assert should_skip_orchestrator_pr_event(event) is False

    def test_non_pr_events_not_checked(self):
        """Test that non-PR events (ISSUE_CREATED, etc.) are NOT checked.

        This ensures we don't accidentally skip legitimate non-PR workflows
        that happen to have PR-like payload fragments.
        """
        non_pr_event_types = [
            WebhookEventType.ISSUE_CREATED,
            WebhookEventType.ISSUE_CLOSED,
            WebhookEventType.ISSUE_COMMENTED,
            WebhookEventType.PUSH,
        ]
        for event_type in non_pr_event_types:
            event = create_mock_event(
                event_type=event_type,
                raw_payload={
                    "pull_request": {
                        "head": {"ref": "orchestrator/docs-test-123"}
                    }
                },
            )
            assert should_skip_orchestrator_pr_event(event) is False, \
                f"Event type {event_type} should NOT be checked"


class TestGarbagePRScenario:
    """Integration tests for the garbage PR scenario"""

    def test_check_suite_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test the exact scenario that caused garbage PRs:
        1. Orchestrator creates a docs PR on orchestrator/* branch
        2. GitHub sends check_suite webhook (parsed as UNKNOWN)
        3. Event should NOT be actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add githubunknown-docs-add-test",
            description="This contains add keyword that would trigger actionable",
            raw_payload={
                "check_suite": {
                    "head_branch": "orchestrator/docs-test-123",
                    "pull_requests": [
                        {"head": {"ref": "orchestrator/docs-test-123"}}
                    ]
                }
            },
        )

        # Fix 1: UNKNOWN events are not actionable
        assert event_normalizer.is_actionable(event) is False

        # Fix 2: should_skip_orchestrator_pr_event also catches this
        assert should_skip_orchestrator_pr_event(event) is True

    def test_check_run_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test check_run events from orchestrator PRs are not actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            raw_payload={
                "check_run": {
                    "check_suite": {
                        "head_branch": "orchestrator/docs-fix-123"
                    }
                }
            },
        )

        assert event_normalizer.is_actionable(event) is False
        assert should_skip_orchestrator_pr_event(event) is True

    def test_status_event_from_orchestrator_pr_not_actionable(self, event_normalizer):
        """
        Test status events from orchestrator PRs are not actionable
        """
        event = create_mock_event(
            event_type=WebhookEventType.UNKNOWN,
            title="docs: Add something",
            raw_payload={
                "branches": [
                    {"name": "orchestrator/docs-update-123"}
                ]
            },
        )

        assert event_normalizer.is_actionable(event) is False
        assert should_skip_orchestrator_pr_event(event) is True
