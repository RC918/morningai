"""
Unit tests for PRSummary Schema - Issue #3221

Tests cover:
1. PRSummary Pydantic model validation
2. build_pr_summary() helper function
3. to_github_markdown() rendering
4. to_simple_markdown() rendering
5. File-level comments appendix
6. Error handling with build_unknown_pr_summary()
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from core.routing.pr_summary import (
    PRSummary,
    FileLevelComment,
    build_pr_summary,
    build_unknown_pr_summary,
    SENIOR_ARCHITECT_POLICY_NOTE,
    SCHEMA_VERSION,
)


class TestPRSummaryModel:
    """Tests for PRSummary Pydantic model validation"""

    def test_valid_pr_summary(self):
        """Valid PRSummary should pass validation"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=85,
            analysis="Code looks good, no issues found."
        )
        assert summary.verdict == "approve"
        assert summary.display_decision == "approve"
        assert summary.score == 85
        assert summary.analysis == "Code looks good, no issues found."
        assert summary.schema_version == 1

    def test_schema_version_is_1(self):
        """Schema version should be 1"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Test"
        )
        assert summary.schema_version == SCHEMA_VERSION
        assert summary.schema_version == 1

    def test_empty_analysis_gets_default(self):
        """Empty analysis should get default message"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis=""
        )
        assert summary.analysis == "No significant issues found."

    def test_whitespace_analysis_gets_default(self):
        """Whitespace-only analysis should get default message"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="   "
        )
        assert summary.analysis == "No significant issues found."

    def test_score_clamped_to_valid_range(self):
        """Score should be between 0 and 100"""
        with pytest.raises(ValueError):
            PRSummary(
                verdict="approve",
                display_decision="approve",
                score=-10,
                analysis="Test"
            )

        with pytest.raises(ValueError):
            PRSummary(
                verdict="approve",
                display_decision="approve",
                score=150,
                analysis="Test"
            )

    def test_immutable_after_creation(self):
        """PRSummary should be immutable (frozen)"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Test"
        )
        with pytest.raises(ValidationError):
            summary.score = 90

    def test_no_extra_fields_allowed(self):
        """Extra fields should be rejected"""
        with pytest.raises(ValidationError):
            PRSummary(
                verdict="approve",
                display_decision="approve",
                score=80,
                analysis="Test",
                extra_field="not allowed"
            )

    def test_optional_metadata_fields(self):
        """Optional metadata fields should work"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Test",
            trace_id="trace-123",
            pr_number=42,
            repo="owner/repo",
            head_sha="abc123"
        )
        assert summary.trace_id == "trace-123"
        assert summary.pr_number == 42
        assert summary.repo == "owner/repo"
        assert summary.head_sha == "abc123"

    def test_generated_at_auto_populated(self):
        """generated_at should be auto-populated with ISO timestamp"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Test"
        )
        assert summary.generated_at is not None
        # Should be parseable as ISO timestamp
        datetime.fromisoformat(summary.generated_at.replace("Z", "+00:00"))


class TestFileLevelComment:
    """Tests for FileLevelComment model"""

    def test_valid_file_level_comment(self):
        """Valid FileLevelComment should pass validation"""
        comment = FileLevelComment(
            file="src/test.py",
            message="Consider refactoring this function"
        )
        assert comment.file == "src/test.py"
        assert comment.message == "Consider refactoring this function"
        assert comment.reason is None

    def test_file_level_comment_with_reason(self):
        """FileLevelComment with reason should work"""
        comment = FileLevelComment(
            file="src/test.py",
            message="Consider refactoring",
            reason="Line not in diff"
        )
        assert comment.reason == "Line not in diff"


class TestBuildPrSummary:
    """Tests for build_pr_summary() helper function"""

    def test_build_from_approve_outcome(self):
        """Build PRSummary from approve outcome"""
        review_outcome = {"verdict": "approve"}
        review_result = {
            "llm_decision": "approve",
            "llm_summary": "Code looks good!"
        }

        summary = build_pr_summary(
            review_outcome=review_outcome,
            review_result=review_result,
            code_quality_score=90
        )

        assert summary.verdict == "approve"
        assert summary.display_decision == "approve"
        assert summary.score == 90
        assert summary.analysis == "Code looks good!"

    def test_build_from_request_changes_outcome(self):
        """Build PRSummary from request_changes outcome"""
        review_outcome = {"verdict": "request_changes"}
        review_result = {
            "llm_decision": "needs_changes",
            "llm_summary": "Found some issues"
        }

        summary = build_pr_summary(
            review_outcome=review_outcome,
            review_result=review_result,
            code_quality_score=60
        )

        assert summary.verdict == "request_changes"
        assert summary.display_decision == "needs_changes"
        assert summary.score == 60

    def test_build_with_file_level_comments(self):
        """Build PRSummary with file-level comments"""
        review_outcome = {"verdict": "comment"}
        review_result = {"llm_summary": "Some suggestions"}
        file_comments = [
            {"file": "src/a.py", "message": "Comment 1", "downgrade_reason": "Line not in diff"},
            {"file": "src/b.py", "message": "Comment 2"}
        ]

        summary = build_pr_summary(
            review_outcome=review_outcome,
            review_result=review_result,
            code_quality_score=75,
            file_level_comments=file_comments
        )

        assert len(summary.file_level_comments) == 2
        assert summary.file_level_comments[0].file == "src/a.py"
        assert summary.file_level_comments[0].reason == "Line not in diff"
        assert summary.file_level_comments[1].reason is None

    def test_build_with_metadata(self):
        """Build PRSummary with metadata"""
        summary = build_pr_summary(
            review_outcome={"verdict": "approve"},
            review_result={"llm_summary": "Good"},
            code_quality_score=80,
            trace_id="trace-456",
            pr_number=123,
            repo="owner/repo",
            head_sha="def456"
        )

        assert summary.trace_id == "trace-456"
        assert summary.pr_number == 123
        assert summary.repo == "owner/repo"
        assert summary.head_sha == "def456"

    def test_build_clamps_score(self):
        """build_pr_summary should clamp score to 0-100"""
        summary = build_pr_summary(
            review_outcome={"verdict": "approve"},
            review_result={},
            code_quality_score=150
        )
        assert summary.score == 100

        summary = build_pr_summary(
            review_outcome={"verdict": "approve"},
            review_result={},
            code_quality_score=-50
        )
        assert summary.score == 0

    def test_build_handles_empty_inputs(self):
        """build_pr_summary should handle empty inputs gracefully"""
        summary = build_pr_summary(
            review_outcome={},
            review_result={},
            code_quality_score=0
        )

        assert summary.verdict == "unknown"
        assert summary.display_decision == "reviewed"
        assert summary.score == 0
        assert summary.analysis == "No significant issues found."

    def test_llm_decision_takes_precedence(self):
        """llm_decision should take precedence over verdict for display_decision"""
        summary = build_pr_summary(
            review_outcome={"verdict": "comment"},
            review_result={"llm_decision": "approve"},
            code_quality_score=80
        )

        # verdict is from review_outcome
        assert summary.verdict == "comment"
        # display_decision is from llm_decision
        assert summary.display_decision == "approve"

    def test_build_from_blocked_outcome(self):
        """Build PRSummary from blocked outcome without llm_decision

        This test verifies that 'blocked' verdict maps to 'block' display_decision
        when no llm_decision is provided (regression test for verdict mapping fix).
        """
        review_outcome = {"verdict": "blocked"}
        review_result = {"llm_summary": "Critical issue found"}

        summary = build_pr_summary(
            review_outcome=review_outcome,
            review_result=review_result,
            code_quality_score=10
        )

        assert summary.verdict == "blocked"
        assert summary.display_decision == "block"
        assert summary.score == 10


class TestBuildUnknownPrSummary:
    """Tests for build_unknown_pr_summary() helper function"""

    def test_build_unknown_summary(self):
        """Build unknown PRSummary for error scenarios"""
        summary = build_unknown_pr_summary(
            error="Timeout during review",
            trace_id="trace-789",
            pr_number=456
        )

        assert summary.verdict == "unknown"
        assert summary.display_decision == "reviewed"
        assert summary.score == 0
        assert "Timeout during review" in summary.analysis
        assert summary.trace_id == "trace-789"
        assert summary.pr_number == 456


class TestToGithubMarkdown:
    """Tests for to_github_markdown() rendering"""

    def test_approve_markdown(self):
        """Approve verdict should render with check mark"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=90,
            analysis="Code looks great!"
        )
        markdown = summary.to_github_markdown()

        assert "## :robot: MorningAI Review Summary" in markdown
        assert ":white_check_mark:" in markdown
        assert "Approve" in markdown
        assert "(Score: 90)" in markdown
        assert "Code looks great!" in markdown
        assert SENIOR_ARCHITECT_POLICY_NOTE in markdown

    def test_needs_changes_markdown(self):
        """Needs changes verdict should render with warning"""
        summary = PRSummary(
            verdict="request_changes",
            display_decision="needs_changes",
            score=60,
            analysis="Found some issues"
        )
        markdown = summary.to_github_markdown()

        assert ":warning:" in markdown
        assert "Needs Changes" in markdown
        assert "(Score: 60)" in markdown

    def test_block_markdown(self):
        """Block verdict should render with X"""
        summary = PRSummary(
            verdict="blocked",
            display_decision="block",
            score=20,
            analysis="Critical issues found"
        )
        markdown = summary.to_github_markdown()

        assert ":x:" in markdown
        assert "Block" in markdown

    def test_reviewed_markdown(self):
        """Reviewed verdict should render with magnifying glass"""
        summary = PRSummary(
            verdict="comment",
            display_decision="reviewed",
            score=75,
            analysis="Some suggestions"
        )
        markdown = summary.to_github_markdown()

        assert ":mag:" in markdown
        assert "Reviewed" in markdown

    def test_markdown_without_policy_note(self):
        """Should be able to exclude policy note"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Good"
        )
        markdown = summary.to_github_markdown(include_policy_note=False)

        assert SENIOR_ARCHITECT_POLICY_NOTE not in markdown

    def test_markdown_with_file_level_comments(self):
        """Markdown should include file-level comments appendix"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Good",
            file_level_comments=[
                FileLevelComment(
                    file="src/test.py",
                    message="Consider refactoring",
                    reason="Line not in diff"
                )
            ]
        )
        markdown = summary.to_github_markdown()

        assert "### File-Level Comments" in markdown
        assert "`src/test.py`" in markdown
        assert "Consider refactoring" in markdown
        assert "Line not in diff" in markdown


class TestToSimpleMarkdown:
    """Tests for to_simple_markdown() rendering"""

    def test_simple_markdown_header(self):
        """Simple markdown should have basic header"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Good"
        )
        markdown = summary.to_simple_markdown()

        assert "## MorningAI Code Review" in markdown
        # Should NOT have full summary details
        assert "Score:" not in markdown
        assert SENIOR_ARCHITECT_POLICY_NOTE not in markdown

    def test_simple_markdown_with_file_level_comments(self):
        """Simple markdown should include file-level comments"""
        summary = PRSummary(
            verdict="approve",
            display_decision="approve",
            score=80,
            analysis="Good",
            file_level_comments=[
                FileLevelComment(
                    file="src/test.py",
                    message="Consider refactoring"
                )
            ]
        )
        markdown = summary.to_simple_markdown()

        assert "### File-Level Comments" in markdown
        assert "`src/test.py`" in markdown
        assert "Consider refactoring" in markdown
