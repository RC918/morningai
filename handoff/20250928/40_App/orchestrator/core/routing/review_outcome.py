"""
ReviewOutcome Schema - EPIC B Phase B-6 Implementation
Stable interface contract between Reviewer and Router

This module provides:
1. ReviewOutcome Pydantic model for structured review results
2. Verdict semantics for Router decision making
3. Helper functions for constructing ReviewOutcome from reviewer_node state

Issue #3130: B-6 Reviewer -> Router Interface Definition
Related: EPIC B - Diff-Aware Review Roadmap (Phase 6)

Usage:
    from core.routing.review_outcome import ReviewOutcome, build_review_outcome

    # Build from reviewer_node state
    outcome = build_review_outcome(
        review_comments=state["review_comments"],
        review_severity=state["review_severity"],
        review_result=state["review_result"],
        diff_truncated=state.get("diff_truncated", False)
    )

    # Store in state
    state["review_outcome"] = outcome.model_dump()

Router Decision Rules:
    1. unknown verdict overrides all other fields -> fallback to rule-based routing
    2. blocked verdict forces escalation -> reserved for Safety/Compliance blocks
    3. schema_validated=False triggers fallback -> treat as unknown
    4. Business verdicts (approve, request_changes, comment) follow normal routing
"""
import logging
from typing import Literal, List, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Verdict types for Router decision making
VerdictType = Literal["approve", "request_changes", "comment", "blocked", "unknown"]

# Severity levels (excludes "none" - must be mapped to "low")
SeverityType = Literal["low", "medium", "high", "critical"]

# Severity levels that count as blockers
BLOCKER_SEVERITIES = frozenset({"high", "critical"})


class ReviewOutcome(BaseModel):
    """Reviewer -> Router stable interface (EPIC B-6)

    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    Breaking changes require version bump and Router compatibility handling.

    This is the contract between reviewer_node and Router. Router MUST read
    this schema to make routing decisions. See module docstring for decision rules.
    """

    # Schema version for backward-compatible evolution
    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for backward compatibility"
    )

    # Decision signals (Router uses these)
    verdict: VerdictType = Field(
        description="Review verdict for Router decision making"
    )
    severity: SeverityType = Field(
        description="Worst severity across all comments (none maps to low)"
    )
    summary: str = Field(
        description="One-line summary for Router (human-readable)"
    )

    # Data quality signals (Router uses for fail-safe decisions)
    diff_truncated: bool = Field(
        default=False,
        description="Whether PR diff was truncated due to size limits"
    )
    schema_validated: bool = Field(
        default=True,
        description="Whether this ReviewOutcome passed Pydantic validation. "
                    "Producer MUST set to False if validation failed and a "
                    "minimal fallback dict was constructed."
    )
    blocker_count: int = Field(
        default=0,
        ge=0,
        description="Count of comments where severity in {high, critical}"
    )

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        """Ensure summary is not empty."""
        if not v or not v.strip():
            raise ValueError("summary cannot be empty")
        return v.strip()

    class Config:
        """Pydantic model configuration."""
        frozen = True  # Immutable after creation
        extra = "forbid"  # No extra fields allowed


def _map_severity(severity: Optional[str]) -> SeverityType:
    """
    Map reviewer_node severity to ReviewOutcome severity.

    reviewer_node can output "none" but ReviewOutcome.severity does NOT include it.
    Mapping: "none" -> "low" (baseline when no issues found)

    Args:
        severity: Raw severity from reviewer_node (none/low/medium/high/critical)

    Returns:
        Mapped severity (low/medium/high/critical)
    """
    if not severity or severity.lower() == "none":
        return "low"

    severity_lower = severity.lower()
    if severity_lower in ("low", "medium", "high", "critical"):
        return severity_lower  # type: ignore
    return "low"


def _compute_blocker_count(review_comments: List[Dict[str, Any]]) -> int:
    """
    Compute blocker count from review comments.

    Blockers are comments where severity in {"high", "critical"}.

    Args:
        review_comments: List of review comment dicts with severity field

    Returns:
        Count of blocker comments
    """
    if not review_comments:
        return 0

    count = 0
    for comment in review_comments:
        severity = comment.get("severity", "").lower()
        if severity in BLOCKER_SEVERITIES:
            count += 1
    return count


def _determine_verdict(
    review_result: Dict[str, Any],
    review_severity: str,
    blocker_count: int
) -> VerdictType:
    """
    Determine verdict from review result and severity.

    Logic:
    - If review_result status is "error" -> "unknown"
    - If severity is "critical" or blocker_count > 0 with high severity -> "request_changes"
    - If review_result status is "passed" -> "approve"
    - If review_result status is "needs_attention" -> "request_changes"
    - Otherwise -> "comment"

    Args:
        review_result: Dict with status and reason
        review_severity: Aggregate severity from reviewer_node
        blocker_count: Number of high/critical comments

    Returns:
        Verdict for Router
    """
    status = review_result.get("status", "").lower()

    # Error state -> unknown verdict
    if status == "error":
        return "unknown"

    # Check for blocking issues
    severity_lower = review_severity.lower() if review_severity else "none"
    if severity_lower == "critical" or blocker_count > 0:
        return "request_changes"

    # Map status to verdict
    if status == "passed":
        return "approve"
    elif status == "needs_attention":
        return "request_changes"
    elif status == "pending":
        return "comment"

    # Default to comment for unknown status
    return "comment"


def _build_summary(
    verdict: VerdictType,
    review_result: Dict[str, Any],
    blocker_count: int,
    severity: SeverityType
) -> str:
    """
    Build human-readable summary for Router.

    Args:
        verdict: Determined verdict
        review_result: Dict with status and reason
        blocker_count: Number of blocker comments
        severity: Mapped severity

    Returns:
        One-line summary string
    """
    reason = review_result.get("reason", "")
    llm_summary = review_result.get("llm_summary", "")

    if verdict == "unknown":
        error = review_result.get("error", "unknown error")
        return f"Review failed: {error}"

    if verdict == "blocked":
        return "Safety/Compliance block detected"

    if verdict == "approve":
        if llm_summary:
            return f"Approved: {llm_summary}"
        return reason or "Review passed, no blocking issues"

    if verdict == "request_changes":
        if blocker_count > 0:
            return f"{blocker_count} blocking issue(s) found (severity: {severity})"
        if llm_summary:
            return f"Changes requested: {llm_summary}"
        return reason or "Issues found that need attention"

    # comment verdict
    if llm_summary:
        return f"Suggestions: {llm_summary}"
    return reason or "Review completed with suggestions"


def build_review_outcome(
    review_comments: List[Dict[str, Any]],
    review_severity: str,
    review_result: Dict[str, Any],
    diff_truncated: bool = False
) -> ReviewOutcome:
    """
    Build ReviewOutcome from reviewer_node state fields.

    This is the primary entry point for constructing ReviewOutcome.
    It handles all the mapping and computation logic.

    Args:
        review_comments: List of review comment dicts from state["review_comments"]
        review_severity: Aggregate severity from state["review_severity"]
        review_result: Review result dict from state["review_result"]
        diff_truncated: Whether diff was truncated from state["diff_truncated"]

    Returns:
        ReviewOutcome instance ready to be stored in state

    Example:
        outcome = build_review_outcome(
            review_comments=state["review_comments"],
            review_severity=state["review_severity"],
            review_result=state["review_result"],
            diff_truncated=state.get("diff_truncated", False)
        )
        state["review_outcome"] = outcome.model_dump()
    """
    # Compute derived fields
    blocker_count = _compute_blocker_count(review_comments)
    severity = _map_severity(review_severity)
    verdict = _determine_verdict(review_result, review_severity, blocker_count)
    summary = _build_summary(verdict, review_result, blocker_count, severity)

    return ReviewOutcome(
        verdict=verdict,
        severity=severity,
        summary=summary,
        diff_truncated=diff_truncated,
        schema_validated=True,
        blocker_count=blocker_count
    )


def build_unknown_outcome(error: str, diff_truncated: bool = False) -> Dict[str, Any]:
    """
    Build a minimal ReviewOutcome dict for error/timeout scenarios.

    When Pydantic validation fails or reviewer_node encounters a runtime error,
    the producer MUST catch the exception and call this function to construct
    a fallback dict. Router MUST treat schema_validated=False as equivalent to
    verdict="unknown".

    Args:
        error: Error message describing what went wrong
        diff_truncated: Whether diff was truncated

    Returns:
        Dict representation of ReviewOutcome with verdict="unknown"

    Example:
        try:
            outcome = build_review_outcome(...)
            state["review_outcome"] = outcome.model_dump()
        except Exception as e:
            state["review_outcome"] = build_unknown_outcome(str(e))
    """
    return {
        "schema_version": 1,
        "verdict": "unknown",
        "severity": "low",
        "summary": f"Review failed: {error}",
        "diff_truncated": diff_truncated,
        "schema_validated": False,
        "blocker_count": 0
    }
