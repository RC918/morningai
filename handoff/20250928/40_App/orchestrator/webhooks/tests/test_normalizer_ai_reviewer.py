"""
Tests for EventNormalizer - AI Reviewer Integration

Issue: #2209 - 修復 AI Reviewer 評論接收機制
Milestone: Phase 7 - 生態系閉環 (AI Review Closed Loop)
"""

import pytest
from datetime import datetime, timezone

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..normalizer import EventNormalizer


@pytest.fixture
def event_normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


def create_mock_event(
    description: str = "",
    metadata: dict = None,
    event_type: WebhookEventType = WebhookEventType.PR_COMMENTED,
) -> WebhookEvent:
    """Create a mock WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload={},
        title="Test Event",
        description=description,
        url="https://github.com/test/repo/pull/1",
        actor_name="test-actor",
        metadata=metadata or {},
    )


class TestEventNormalizerAIReviewerKeywords:
    """Tests for AI reviewer keyword detection"""

    def test_ai_reviewer_keywords_defined(self, event_normalizer):
        """Test that AI reviewer keywords are defined"""
        assert hasattr(event_normalizer, "AI_REVIEWER_KEYWORDS")
        assert len(event_normalizer.AI_REVIEWER_KEYWORDS) > 0

    def test_contains_codex_keywords(self, event_normalizer):
        """Test that Codex/Copilot keywords are included"""
        keywords = event_normalizer.AI_REVIEWER_KEYWORDS
        assert "suggestion:" in keywords
        assert "consider:" in keywords
        assert "recommend:" in keywords

    def test_contains_gemini_keywords(self, event_normalizer):
        """Test that Gemini Code Assist keywords are included"""
        keywords = event_normalizer.AI_REVIEWER_KEYWORDS
        assert "code review" in keywords
        assert "best practice" in keywords
        assert "security concern" in keywords

    def test_contains_coderabbit_keywords(self, event_normalizer):
        """Test that CodeRabbit keywords are included"""
        keywords = event_normalizer.AI_REVIEWER_KEYWORDS
        assert "actionable comment" in keywords
        assert "nitpick:" in keywords


class TestEventNormalizerIsActionable:
    """Tests for EventNormalizer.is_actionable with AI reviewers"""

    def test_is_actionable_for_ai_reviewer_event(self, event_normalizer):
        """Test that AI reviewer events are always actionable"""
        event = create_mock_event(
            description="Some comment",
            metadata={"is_ai_reviewer": True, "review_source": "gemini"},
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_ai_reviewer_with_empty_description(
        self, event_normalizer
    ):
        """Test that AI reviewer events are actionable even with empty description"""
        event = create_mock_event(
            description="",
            metadata={"is_ai_reviewer": True, "review_source": "copilot"},
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_suggestion_keyword(self, event_normalizer):
        """Test that 'suggestion:' keyword triggers actionable"""
        event = create_mock_event(
            description="Suggestion: Consider using a more descriptive variable name",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_consider_keyword(self, event_normalizer):
        """Test that 'consider:' keyword triggers actionable"""
        event = create_mock_event(
            description="Consider: This function could be simplified",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_security_concern_keyword(self, event_normalizer):
        """Test that 'security concern' keyword triggers actionable"""
        event = create_mock_event(
            description="Security concern: This input is not sanitized",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_code_review_keyword(self, event_normalizer):
        """Test that 'code review' keyword triggers actionable"""
        event = create_mock_event(
            description="Code review: The implementation looks good overall",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_refactor_keyword(self, event_normalizer):
        """Test that 'refactor' keyword triggers actionable"""
        event = create_mock_event(
            description="You should refactor this method to improve readability",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_vulnerability_keyword(self, event_normalizer):
        """Test that 'vulnerability' keyword triggers actionable"""
        event = create_mock_event(
            description="Potential vulnerability detected in authentication flow",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_actionable_for_deprecated_keyword(self, event_normalizer):
        """Test that 'deprecated' keyword triggers actionable"""
        event = create_mock_event(
            description="This API is deprecated and should be updated",
        )
        assert event_normalizer.is_actionable(event) is True

    def test_is_not_actionable_for_generic_comment(self, event_normalizer):
        """Test that generic comments without keywords are not actionable"""
        event = create_mock_event(
            description="Looks good to me!",
            event_type=WebhookEventType.UNKNOWN,
        )
        assert event_normalizer.is_actionable(event) is False

    def test_is_actionable_case_insensitive(self, event_normalizer):
        """Test that keyword detection is case insensitive"""
        event = create_mock_event(
            description="SUGGESTION: Use async/await here",
        )
        assert event_normalizer.is_actionable(event) is True


class TestEventNormalizerExtractTask:
    """Tests for EventNormalizer.extract_task with AI reviewers"""

    def test_extract_task_from_ai_reviewer_event(self, event_normalizer):
        """Test that tasks are extracted from AI reviewer events"""
        event = create_mock_event(
            description="Suggestion: Refactor this function",
            metadata={"is_ai_reviewer": True, "review_source": "gemini"},
            event_type=WebhookEventType.PR_COMMENTED,
        )

        task = event_normalizer.extract_task(event)

        assert task is not None
        assert task.source_event == event

    def test_extract_task_preserves_ai_reviewer_metadata(self, event_normalizer):
        """Test that AI reviewer metadata is preserved in extracted task"""
        event = create_mock_event(
            description="Code review: Consider adding error handling",
            metadata={"is_ai_reviewer": True, "review_source": "copilot"},
            event_type=WebhookEventType.PR_REVIEWED,
        )

        task = event_normalizer.extract_task(event)

        assert task is not None
        assert task.source_event.metadata.get("is_ai_reviewer") is True
        assert task.source_event.metadata.get("review_source") == "copilot"


class TestAIReviewerIntegration:
    """Integration tests for AI reviewer workflow in normalizer"""

    def test_full_ai_reviewer_workflow(self, event_normalizer):
        """Test complete workflow: is_actionable -> extract_task"""
        # Simulate a Gemini Code Assist review comment
        event = create_mock_event(
            description="Suggestion: This code could be improved by using a map instead of a loop",
            metadata={"is_ai_reviewer": True, "review_source": "gemini"},
            event_type=WebhookEventType.PR_COMMENTED,
        )

        # Verify event is actionable
        assert event_normalizer.is_actionable(event) is True

        # Verify task is extracted
        task = event_normalizer.extract_task(event)
        assert task is not None
        assert "Suggestion" in task.source_event.description

    def test_ai_reviewer_with_security_concern(self, event_normalizer):
        """Test AI reviewer detecting security concern"""
        event = create_mock_event(
            description="Security concern: SQL injection vulnerability detected",
            metadata={"is_ai_reviewer": True, "review_source": "coderabbit"},
            event_type=WebhookEventType.PR_REVIEWED,
        )

        assert event_normalizer.is_actionable(event) is True

        task = event_normalizer.extract_task(event)
        assert task is not None
        # Security-related tasks should require approval
        assert task.requires_approval is True
