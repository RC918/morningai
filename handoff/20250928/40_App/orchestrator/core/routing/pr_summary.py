"""
PRSummary Schema - Track C Interface & Output Contract

Standardized PR Summary artifact for consistent review output across all sinks
(GitHub comments, Slack/Jira/Linear notifications, Signals ingestion).

Issue #3221: PR Summary artifact standardization

This module provides:
1. PRSummary Pydantic model for structured PR summary data
2. Helper functions for building PRSummary from reviewer state
3. Renderers for different output formats (GitHub markdown, etc.)

Usage:
    from core.routing.pr_summary import PRSummary, build_pr_summary

    # Build from reviewer state
    summary = build_pr_summary(
        review_outcome=state.get("review_outcome", {}),
        review_result=state.get("review_result", {}),
        code_quality_score=state.get("code_quality_score", 0),
        trace_id=state.get("trace_id"),
        pr_number=state.get("pr_number"),
        repo=state.get("repo"),
        head_sha=state.get("diff_head_sha")
    )

    # Render to GitHub markdown
    markdown = summary.to_github_markdown()

Design Principles (Blueprint aligned):
- Deterministic: No LLM in rendering, pure transformation
- Versioned: schema_version for backward compatibility
- Sink-agnostic: Core data separate from presentation
"""
import logging
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger(__name__)

# Verdict types aligned with ReviewOutcome
VerdictType = Literal["approve", "request_changes", "comment", "blocked", "unknown"]

# Display decision types (what's shown to users)
DisplayDecisionType = Literal["approve", "needs_changes", "block", "reviewed"]

# Schema version for backward-compatible evolution
SCHEMA_VERSION = 1

# Senior Architect policy note (shared constant)
SENIOR_ARCHITECT_POLICY_NOTE = (
    "This review follows the Senior Architect policy - style, formatting, "
    "and naming convention issues are intentionally filtered out to reduce noise. "
    "The reviewer focuses on logic errors, security vulnerabilities, performance "
    "problems, and API contract changes."
)


class FileLevelComment(BaseModel):
    """File-level comment that couldn't be posted inline."""
    file: str = Field(description="File path")
    message: str = Field(description="Comment message")
    reason: Optional[str] = Field(
        default=None,
        description="Why this was downgraded to file-level"
    )


class PRSummary(BaseModel):
    """Standardized PR Summary artifact (Issue #3221)

    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    Breaking changes require version bump and consumer compatibility handling.

    This is the contract for PR summary output. All sinks (GitHub, Slack, etc.)
    should consume this schema rather than re-deriving their own summaries.
    """

    # Schema version for backward compatibility
    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for backward compatibility"
    )

    # Core review data
    verdict: VerdictType = Field(
        description="Router verdict (from ReviewOutcome)"
    )
    display_decision: DisplayDecisionType = Field(
        description="User-facing decision label (approve/needs_changes/block/reviewed)"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Code quality score (0-100)"
    )
    analysis: str = Field(
        description="LLM analysis summary (llm_summary from review_result)"
    )

    # File-level comments (for appendix rendering)
    file_level_comments: List[FileLevelComment] = Field(
        default_factory=list,
        description="Comments that couldn't be posted inline"
    )

    # Metadata (optional, for tracing and debugging)
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for debugging"
    )
    pr_number: Optional[int] = Field(
        default=None,
        description="PR number"
    )
    repo: Optional[str] = Field(
        default=None,
        description="Repository in owner/repo format"
    )
    head_sha: Optional[str] = Field(
        default=None,
        description="Head commit SHA"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when summary was generated"
    )

    # Pydantic V2 configuration
    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        extra="forbid"  # No extra fields allowed
    )

    @field_validator("analysis")
    @classmethod
    def analysis_default_if_empty(cls, v: str) -> str:
        """Provide default analysis if empty."""
        if not v or not v.strip():
            return "No significant issues found."
        return v.strip()

    def _get_verdict_icon(self) -> str:
        """Get GitHub emoji icon for verdict."""
        icon_map = {
            "approve": "white_check_mark",
            "needs_changes": "warning",
            "block": "x",
            "reviewed": "mag",
        }
        return icon_map.get(self.display_decision, "mag")

    def _get_verdict_label(self) -> str:
        """Get human-readable verdict label."""
        label_map = {
            "approve": "Approve",
            "needs_changes": "Needs Changes",
            "block": "Block",
            "reviewed": "Reviewed",
        }
        return label_map.get(self.display_decision, "Reviewed")

    def to_github_markdown(self, include_policy_note: bool = True) -> str:
        """
        Render PR summary to GitHub-flavored markdown.

        Args:
            include_policy_note: Whether to include the Senior Architect policy note

        Returns:
            GitHub markdown string ready for posting
        """
        icon = self._get_verdict_icon()
        label = self._get_verdict_label()

        parts = [
            "## :robot: MorningAI Review Summary",
            "",
            f"**Verdict:** :{icon}: {label} (Score: {self.score})",
            "",
            "**Analysis:**",
            self.analysis,
        ]

        # Add file-level comments appendix if present
        if self.file_level_comments:
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("### File-Level Comments")
            parts.append("")
            parts.append("*The following comments could not be posted inline:*")
            parts.append("")
            for comment in self.file_level_comments:
                parts.append(f"**`{comment.file}`**")
                parts.append(f"> {comment.message}")
                if comment.reason:
                    parts.append(f"> *(Reason: {comment.reason})*")
                parts.append("")

        # Add policy note
        if include_policy_note:
            parts.append("")
            parts.append("---")
            parts.append(f"*Note: {SENIOR_ARCHITECT_POLICY_NOTE}*")

        return "\n".join(parts)

    def to_simple_markdown(self) -> str:
        """
        Render simple markdown header for inline comment reviews.

        This is used when there are inline comments - the full summary
        is not needed, just a header with optional file-level appendix.

        Returns:
            Simple markdown header string
        """
        parts = ["## MorningAI Code Review"]

        # Add file-level comments appendix if present
        if self.file_level_comments:
            parts.append("")
            parts.append("### File-Level Comments")
            parts.append("")
            parts.append("*The following comments could not be posted inline:*")
            parts.append("")
            for comment in self.file_level_comments:
                parts.append(f"**`{comment.file}`**")
                parts.append(f"> {comment.message}")
                if comment.reason:
                    parts.append(f"> *(Reason: {comment.reason})*")
                parts.append("")

        return "\n".join(parts)


def _map_verdict_to_display_decision(
    verdict: str,
    llm_decision: Optional[str] = None
) -> DisplayDecisionType:
    """
    Map ReviewOutcome verdict to display decision.

    Uses llm_decision if available (for backward compatibility with existing
    summary format), otherwise maps from verdict.

    Args:
        verdict: ReviewOutcome verdict
        llm_decision: Optional llm_decision from review_result

    Returns:
        Display decision for user-facing output
    """
    # Prefer llm_decision if available (backward compatibility)
    if llm_decision:
        llm_lower = llm_decision.lower()
        if llm_lower == "approve":
            return "approve"
        elif llm_lower in ("needs_changes", "request_changes"):
            return "needs_changes"
        elif llm_lower == "block":
            return "block"
        return "reviewed"

    # Map from verdict
    verdict_lower = verdict.lower() if verdict else "unknown"
    if verdict_lower == "approve":
        return "approve"
    elif verdict_lower in ("request_changes", "blocked"):
        return "needs_changes"
    elif verdict_lower == "comment":
        return "reviewed"
    return "reviewed"


def build_pr_summary(
    review_outcome: Dict[str, Any],
    review_result: Dict[str, Any],
    code_quality_score: int = 0,
    file_level_comments: Optional[List[Dict[str, Any]]] = None,
    trace_id: Optional[str] = None,
    pr_number: Optional[int] = None,
    repo: Optional[str] = None,
    head_sha: Optional[str] = None
) -> PRSummary:
    """
    Build PRSummary from reviewer state fields.

    This is the primary entry point for constructing PRSummary.
    It handles all the mapping and normalization logic.

    Args:
        review_outcome: ReviewOutcome dict from state["review_outcome"]
        review_result: Review result dict from state["review_result"]
        code_quality_score: Code quality score from state["code_quality_score"]
        file_level_comments: Optional list of file-level comment dicts
        trace_id: Optional trace ID for debugging
        pr_number: Optional PR number
        repo: Optional repository in owner/repo format
        head_sha: Optional head commit SHA

    Returns:
        PRSummary instance ready for rendering

    Example:
        summary = build_pr_summary(
            review_outcome=state.get("review_outcome", {}),
            review_result=state.get("review_result", {}),
            code_quality_score=state.get("code_quality_score", 0),
            file_level_comments=downgraded_comments,
            trace_id=state.get("trace_id"),
            pr_number=state.get("pr_number")
        )
        markdown = summary.to_github_markdown()
    """
    # Extract fields from review_outcome and review_result
    verdict = review_outcome.get("verdict", "unknown")
    llm_decision = review_result.get("llm_decision")
    llm_summary = review_result.get("llm_summary", "")

    # Map to display decision
    display_decision = _map_verdict_to_display_decision(verdict, llm_decision)

    # Convert file-level comments to FileLevelComment objects
    file_comments = []
    if file_level_comments:
        for c in file_level_comments:
            file_comments.append(FileLevelComment(
                file=c.get("file", "unknown"),
                message=c.get("message", ""),
                reason=c.get("downgrade_reason")
            ))

    return PRSummary(
        verdict=verdict if verdict in ("approve", "request_changes", "comment", "blocked", "unknown") else "unknown",
        display_decision=display_decision,
        score=max(0, min(100, code_quality_score)),  # Clamp to 0-100
        analysis=llm_summary,
        file_level_comments=file_comments,
        trace_id=trace_id,
        pr_number=pr_number,
        repo=repo,
        head_sha=head_sha
    )


def build_unknown_pr_summary(
    error: str,
    trace_id: Optional[str] = None,
    pr_number: Optional[int] = None
) -> PRSummary:
    """
    Build a minimal PRSummary for error/timeout scenarios.

    Args:
        error: Error message describing what went wrong
        trace_id: Optional trace ID for debugging
        pr_number: Optional PR number

    Returns:
        PRSummary with unknown verdict and error analysis
    """
    return PRSummary(
        verdict="unknown",
        display_decision="reviewed",
        score=0,
        analysis=f"Review failed: {error}",
        trace_id=trace_id,
        pr_number=pr_number
    )
