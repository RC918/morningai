"""
Tests for CommentTriageAgent - AI Reviewer Comment Classification

Issue: #2210 - Comment Triage Agent 設計與實作
Milestone: Phase 7 - 生態系閉環 (AI Review Closed Loop)
"""

import pytest
from datetime import datetime, timezone

from ..bot_protocol import WebhookEvent, WebhookEventType, WebhookSource
from ..comment_triage import (
    CommentTriageAgent,
    CommentTriageResult,
    CommentCategory,
    RiskLevel,
)
from ..normalizer import EventNormalizer


@pytest.fixture
def triage_agent():
    """Create a CommentTriageAgent instance for testing"""
    return CommentTriageAgent()


@pytest.fixture
def event_normalizer():
    """Create an EventNormalizer instance for testing"""
    return EventNormalizer()


def create_ai_reviewer_event(
    description: str,
    source: str = "gemini",
    event_type: WebhookEventType = WebhookEventType.PR_COMMENTED,
    raw_payload: dict = None,
) -> WebhookEvent:
    """Create a mock AI reviewer WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-123",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload=raw_payload or {},
        title="Test Comment",
        description=description,
        url="https://github.com/test/repo/pull/1",
        actor_name=f"{source}-code-assist[bot]",
        metadata={
            "is_ai_reviewer": True,
            "review_source": source,
        },
    )


def create_human_event(
    description: str,
    event_type: WebhookEventType = WebhookEventType.PR_COMMENTED,
) -> WebhookEvent:
    """Create a mock human WebhookEvent for testing"""
    return WebhookEvent(
        event_id="test-event-456",
        source=WebhookSource.GITHUB,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        raw_payload={},
        title="Test Comment",
        description=description,
        url="https://github.com/test/repo/pull/1",
        actor_name="human-reviewer",
        metadata={},
    )


class TestCommentTriageResult:
    """Tests for CommentTriageResult data class"""

    def test_to_dict(self):
        """Test that CommentTriageResult converts to dict correctly"""
        result = CommentTriageResult(
            comment_id="test-123",
            source="gemini",
            category=CommentCategory.BUG_FIX,
            risk_level=RiskLevel.MEDIUM,
            files_affected=["src/auth.py"],
            lines_affected=15,
            should_auto_fix=False,
            confidence=0.85,
            reason="Bug fix suggestion with medium risk",
            keywords_matched=["bug", "fix"],
        )

        result_dict = result.to_dict()

        assert result_dict["comment_id"] == "test-123"
        assert result_dict["source"] == "gemini"
        assert result_dict["category"] == "bug_fix"
        assert result_dict["risk_level"] == "medium"
        assert result_dict["files_affected"] == ["src/auth.py"]
        assert result_dict["lines_affected"] == 15
        assert result_dict["should_auto_fix"] is False
        assert result_dict["confidence"] == 0.85


class TestCommentTriageAgentClassification:
    """Tests for comment classification logic"""

    def test_classify_bug_fix(self, triage_agent):
        """Test classification of bug fix comments"""
        event = create_ai_reviewer_event(
            "There's a bug in this function that causes a crash when input is null"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.BUG_FIX
        assert "bug" in result.keywords_matched or "crash" in result.keywords_matched

    def test_classify_style(self, triage_agent):
        """Test classification of style comments"""
        event = create_ai_reviewer_event(
            "Nitpick: The naming convention here doesn't follow PEP8 style guidelines"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.STYLE
        assert any(
            kw in result.keywords_matched
            for kw in ["nitpick", "naming", "style", "pep8"]
        )

    def test_classify_refactor(self, triage_agent):
        """Test classification of refactoring comments"""
        event = create_ai_reviewer_event(
            "Consider refactoring this code to reduce duplication and improve maintainability"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.REFACTOR
        assert any(
            kw in result.keywords_matched
            for kw in ["refactor", "duplication", "maintainability"]
        )

    def test_classify_security(self, triage_agent):
        """Test classification of security comments"""
        event = create_ai_reviewer_event(
            "Security vulnerability: This code is susceptible to SQL injection attacks"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.SECURITY
        assert any(
            kw in result.keywords_matched
            for kw in ["security", "vulnerability", "injection"]
        )

    def test_classify_performance(self, triage_agent):
        """Test classification of performance comments"""
        event = create_ai_reviewer_event(
            "Performance issue: This query has N+1 problem and causes slow response times"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.PERFORMANCE
        assert any(
            kw in result.keywords_matched
            for kw in ["performance", "slow", "n+1"]
        )

    def test_classify_documentation(self, triage_agent):
        """Test classification of documentation comments"""
        event = create_ai_reviewer_event(
            "Missing documentation: Please add a docstring to explain this function"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.DOCUMENTATION
        assert any(
            kw in result.keywords_matched
            for kw in ["documentation", "docstring"]
        )

    def test_classify_unknown(self, triage_agent):
        """Test classification of comments with no matching keywords"""
        event = create_ai_reviewer_event(
            "Looks good to me!"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.category == CommentCategory.UNKNOWN
        assert result.confidence == 0.0


class TestCommentTriageAgentRiskAssessment:
    """Tests for risk assessment logic"""

    def test_high_risk_security(self, triage_agent):
        """Test that security issues are assessed as high risk"""
        event = create_ai_reviewer_event(
            "Security vulnerability: Authentication bypass detected"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.risk_level == RiskLevel.HIGH

    def test_high_risk_production(self, triage_agent):
        """Test that production-related comments are assessed as high risk"""
        event = create_ai_reviewer_event(
            "Bug: This will cause issues in production database"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.risk_level == RiskLevel.HIGH

    def test_low_risk_style(self, triage_agent):
        """Test that style comments are assessed as low risk"""
        event = create_ai_reviewer_event(
            "Nitpick: Minor formatting issue with whitespace"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.risk_level == RiskLevel.LOW

    def test_low_risk_documentation(self, triage_agent):
        """Test that documentation comments are assessed as low risk"""
        event = create_ai_reviewer_event(
            "Please add documentation for this function"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.risk_level == RiskLevel.LOW

    def test_medium_risk_default(self, triage_agent):
        """Test that ambiguous comments default to medium risk"""
        event = create_ai_reviewer_event(
            "Consider using a different approach here"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.risk_level == RiskLevel.MEDIUM


class TestCommentTriageAgentAutoFix:
    """Tests for auto-fix recommendation logic"""

    def test_no_auto_fix_high_risk(self, triage_agent):
        """Test that high-risk changes are not auto-fixed"""
        event = create_ai_reviewer_event(
            "Security vulnerability: SQL injection in authentication"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.should_auto_fix is False

    def test_no_auto_fix_security(self, triage_agent):
        """Test that security issues are never auto-fixed"""
        event = create_ai_reviewer_event(
            "Security concern: Credential exposure risk"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.should_auto_fix is False

    def test_auto_fix_style_high_confidence(self, triage_agent):
        """Test that style issues with high confidence can be auto-fixed"""
        event = create_ai_reviewer_event(
            "Nitpick: Style issue - formatting and naming convention violation"
        )
        result = triage_agent.triage(event)

        assert result is not None
        # Style issues with high confidence and low risk should be auto-fixable
        assert result.should_auto_fix is True

    def test_auto_fix_documentation(self, triage_agent):
        """Test that documentation updates can be auto-fixed"""
        event = create_ai_reviewer_event(
            "Missing documentation: Add docstring for this function"
        )
        result = triage_agent.triage(event)

        assert result is not None
        # Documentation with high confidence should be auto-fixable
        assert result.should_auto_fix is True


class TestCommentTriageAgentFileExtraction:
    """Tests for file extraction logic"""

    def test_extract_file_from_raw_payload(self, triage_agent):
        """Test file extraction from raw payload"""
        event = create_ai_reviewer_event(
            "Bug in this file",
            raw_payload={
                "comment": {
                    "path": "src/auth/login.py",
                    "body": "Bug in this file",
                }
            },
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert "src/auth/login.py" in result.files_affected

    def test_extract_file_from_comment_text(self, triage_agent):
        """Test file extraction from comment text"""
        event = create_ai_reviewer_event(
            "Bug in `src/utils/helper.py` - please fix the null check"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert "src/utils/helper.py" in result.files_affected

    def test_extract_multiple_files(self, triage_agent):
        """Test extraction of multiple files from comment"""
        event = create_ai_reviewer_event(
            "This affects both `src/auth.py` and `src/utils.py`"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert len(result.files_affected) >= 2


class TestCommentTriageAgentNonAIReviewer:
    """Tests for handling non-AI reviewer events"""

    def test_skip_human_event(self, triage_agent):
        """Test that human events are skipped"""
        event = create_human_event(
            "This looks like a bug to me"
        )
        result = triage_agent.triage(event)

        assert result is None

    def test_skip_event_without_ai_reviewer_flag(self, triage_agent):
        """Test that events without is_ai_reviewer flag are skipped"""
        event = WebhookEvent(
            event_id="test-789",
            source=WebhookSource.GITHUB,
            event_type=WebhookEventType.PR_COMMENTED,
            timestamp=datetime.now(timezone.utc),
            raw_payload={},
            description="Bug fix suggestion",
            actor_name="some-bot[bot]",
            metadata={},  # No is_ai_reviewer flag
        )
        result = triage_agent.triage(event)

        assert result is None


class TestCommentTriageAgentBatchProcessing:
    """Tests for batch processing"""

    def test_batch_triage(self, triage_agent):
        """Test batch triaging of multiple events"""
        events = [
            create_ai_reviewer_event("Bug: null pointer exception"),
            create_ai_reviewer_event("Style: naming convention issue"),
            create_human_event("Looks good to me"),  # Should be skipped
            create_ai_reviewer_event("Security: SQL injection risk"),
        ]

        results = triage_agent.batch_triage(events)

        # Should only have 3 results (human event skipped)
        assert len(results) == 3

        # Verify categories
        categories = [r.category for r in results]
        assert CommentCategory.BUG_FIX in categories
        assert CommentCategory.STYLE in categories
        assert CommentCategory.SECURITY in categories


class TestEventNormalizerIntegration:
    """Tests for EventNormalizer integration with CommentTriageAgent"""

    def test_triage_comment_method(self, event_normalizer):
        """Test that EventNormalizer.triage_comment works correctly"""
        event = create_ai_reviewer_event(
            "Bug: This function has a memory leak"
        )
        result = event_normalizer.triage_comment(event)

        assert result is not None
        assert result.category == CommentCategory.BUG_FIX

    def test_batch_triage_comments_method(self, event_normalizer):
        """Test that EventNormalizer.batch_triage_comments works correctly"""
        events = [
            create_ai_reviewer_event("Bug: crash on null input"),
            create_ai_reviewer_event("Performance: slow query"),
        ]

        results = event_normalizer.batch_triage_comments(events)

        assert len(results) == 2

    def test_triage_returns_none_for_human(self, event_normalizer):
        """Test that triage returns None for human events"""
        event = create_human_event("This is a human comment")
        result = event_normalizer.triage_comment(event)

        assert result is None


class TestCommentTriageResultOutput:
    """Tests for output format matching Issue #2210 specification"""

    def test_output_format_matches_spec(self, triage_agent):
        """Test that output format matches the Issue #2210 specification"""
        event = create_ai_reviewer_event(
            "Bug: Clear bug fix with limited scope in `src/auth.py`",
            source="codex",
            raw_payload={
                "comment": {
                    "path": "src/auth.py",
                    "line": 15,
                }
            },
        )
        result = triage_agent.triage(event)

        assert result is not None

        # Verify all required fields from Issue #2210 spec
        result_dict = result.to_dict()
        assert "comment_id" in result_dict
        assert "source" in result_dict
        assert result_dict["source"] == "codex"
        assert "category" in result_dict
        assert result_dict["category"] in [
            "bug_fix", "style", "refactor", "security", "performance",
            "documentation", "unknown"
        ]
        assert "risk_level" in result_dict
        assert result_dict["risk_level"] in ["high", "medium", "low"]
        assert "files_affected" in result_dict
        assert isinstance(result_dict["files_affected"], list)
        assert "lines_affected" in result_dict
        assert isinstance(result_dict["lines_affected"], int)
        assert "should_auto_fix" in result_dict
        assert isinstance(result_dict["should_auto_fix"], bool)
        assert "confidence" in result_dict
        assert 0.0 <= result_dict["confidence"] <= 1.0
        assert "reason" in result_dict
        assert isinstance(result_dict["reason"], str)


class TestCommentTriageAgentConfidence:
    """Tests for confidence calculation"""

    def test_high_confidence_multiple_keywords(self, triage_agent):
        """Test that multiple keyword matches increase confidence"""
        event = create_ai_reviewer_event(
            "Bug: This error causes a crash and exception when null pointer is accessed"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.confidence >= 0.5  # Should have reasonable confidence

    def test_low_confidence_single_keyword(self, triage_agent):
        """Test that single keyword match has lower confidence"""
        event = create_ai_reviewer_event(
            "There's an issue here"
        )
        result = triage_agent.triage(event)

        assert result is not None
        # Single weak keyword should have lower confidence
        assert result.confidence <= 0.5

    def test_zero_confidence_no_keywords(self, triage_agent):
        """Test that no keyword matches results in zero confidence"""
        event = create_ai_reviewer_event(
            "LGTM!"
        )
        result = triage_agent.triage(event)

        assert result is not None
        assert result.confidence == 0.0
        assert result.category == CommentCategory.UNKNOWN
