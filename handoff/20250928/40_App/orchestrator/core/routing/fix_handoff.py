"""
ReviewToFixHandoff Schema - EPIC D Interface Definition
Stable interface contract between Reviewer and Coder Agent

This module provides:
1. FixSuggestion Pydantic model for individual fix suggestions
2. ReviewToFixHandoff Pydantic model for Reviewer -> Fixer interface
3. Helper functions for constructing handoff from ReviewOutcome

Issue #3225: Review to Fix Handoff Schema - EPIC D Interface Definition
Related: EPIC D - Coder Agent Family
Related: #3130 (B-6 Router Interface)

Usage:
    from core.routing.fix_handoff import (
        FixSuggestion,
        ReviewToFixHandoff,
        build_fix_handoff,
        should_route_to_fixer,
        HIGH_CONFIDENCE_THRESHOLD
    )

    # Build from ReviewOutcome and suggestions
    handoff = build_fix_handoff(
        pr_number=state["pr_number"],
        suggestions=[
            FixSuggestion(
                file_path="src/utils.py",
                line_start=10,
                line_end=15,
                original_code="def foo():",
                suggested_code="def foo() -> None:",
                reason="Add return type annotation",
                confidence=0.9,
                category="style"
            )
        ],
        review_outcome=state.get("review_outcome"),
        requires_human_review=False  # Router determines this
    )

    # Check if should route to fixer (trusts auto_fix_eligible flag)
    if should_route_to_fixer(handoff):
        # Route to fixer_node
        ...

Relationship with ReviewOutcome:
    ReviewOutcome (B-6)
        |
        +-- verdict: "request_changes"
        |
        +-- blocker_count > 0
        |
        v
    ReviewToFixHandoff (this module)
        |
        +-- suggestions: [FixSuggestion, ...]
        |
        +-- auto_fix_eligible: bool
        |
        v
    fixer_node (EPIC D)
"""
import logging
import uuid
from typing import Literal, List, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Category types for fix suggestions
FixCategoryType = Literal["bug_fix", "style", "refactor", "security", "performance"]

# Severity levels (aligned with ReviewOutcome)
SeverityType = Literal["low", "medium", "high", "critical"]

# Confidence threshold for auto-fix eligibility (single source of truth)
# Suggestions with confidence >= this threshold are considered "high confidence"
HIGH_CONFIDENCE_THRESHOLD = 0.8


class FixSuggestion(BaseModel):
    """Single fix suggestion from Reviewer.

    Each suggestion represents a specific code change that the Coder Agent
    can apply. The confidence score helps the Router decide whether to
    auto-apply or require human review.

    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    """

    file_path: str = Field(
        description="Path to the file to modify (relative to repo root)"
    )
    line_start: int = Field(
        ge=1,
        description="Starting line number (1-indexed)"
    )
    line_end: int = Field(
        ge=1,
        description="Ending line number (1-indexed, inclusive)"
    )
    original_code: str = Field(
        description="Original code snippet to replace"
    )
    suggested_code: str = Field(
        description="Suggested replacement code"
    )
    reason: str = Field(
        description="Human-readable explanation for the change"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) for this suggestion"
    )
    category: FixCategoryType = Field(
        description="Category of the fix (bug_fix, style, refactor, security, performance)"
    )

    @field_validator("file_path")
    @classmethod
    def file_path_not_empty(cls, v: str) -> str:
        """Ensure file_path is not empty."""
        if not v or not v.strip():
            raise ValueError("file_path cannot be empty")
        return v.strip()

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        """Ensure reason is not empty."""
        if not v or not v.strip():
            raise ValueError("reason cannot be empty")
        return v.strip()

    @field_validator("line_end")
    @classmethod
    def line_end_gte_line_start(cls, v: int, info) -> int:
        """Ensure line_end >= line_start."""
        line_start = info.data.get("line_start", 1)
        if v < line_start:
            raise ValueError(
                f"line_end ({v}) must be >= line_start ({line_start})"
            )
        return v

    class Config:
        """Pydantic model configuration."""
        frozen = True  # Immutable after creation
        extra = "forbid"  # No extra fields allowed


class ReviewToFixHandoff(BaseModel):
    """Reviewer -> Fixer stable interface (EPIC D)

    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    Breaking changes require version bump and Fixer compatibility handling.

    This is the contract between Reviewer and Coder Agent. The Router uses
    this schema along with ReviewOutcome to decide whether to route to fixer_node.
    """

    # Schema version for backward-compatible evolution
    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for backward compatibility"
    )

    # Source information
    review_id: str = Field(
        description="Unique identifier for this review (for tracing)"
    )
    pr_number: int = Field(
        ge=1,
        description="Pull request number being reviewed"
    )

    # Fix suggestions
    suggestions: List[FixSuggestion] = Field(
        default_factory=list,
        description="List of fix suggestions from Reviewer"
    )

    # Decision signals (Router uses these)
    auto_fix_eligible: bool = Field(
        default=False,
        description="Whether this PR is eligible for auto-fix. "
                    "Set to True only when all safety conditions are met."
    )
    requires_human_review: bool = Field(
        default=True,
        description="Whether human review is required before applying fixes. "
                    "Default True for safety."
    )

    # Risk assessment
    total_lines_affected: int = Field(
        default=0,
        ge=0,
        description="Total number of lines affected by all suggestions"
    )
    max_severity: SeverityType = Field(
        default="low",
        description="Maximum severity across all suggestions"
    )

    @field_validator("review_id")
    @classmethod
    def review_id_not_empty(cls, v: str) -> str:
        """Ensure review_id is not empty."""
        if not v or not v.strip():
            raise ValueError("review_id cannot be empty")
        return v.strip()

    def get_high_confidence_suggestions(
        self,
        threshold: float = HIGH_CONFIDENCE_THRESHOLD
    ) -> List[FixSuggestion]:
        """Get suggestions with confidence >= threshold.

        Args:
            threshold: Minimum confidence score (default HIGH_CONFIDENCE_THRESHOLD)

        Returns:
            List of high-confidence suggestions
        """
        return [s for s in self.suggestions if s.confidence >= threshold]

    def get_suggestions_by_category(
        self,
        category: FixCategoryType
    ) -> List[FixSuggestion]:
        """Get suggestions filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of suggestions in the specified category
        """
        return [s for s in self.suggestions if s.category == category]

    class Config:
        """Pydantic model configuration."""
        frozen = True  # Immutable after creation
        extra = "forbid"  # No extra fields allowed


def _compute_total_lines(suggestions: List[FixSuggestion]) -> int:
    """Compute total lines affected by all suggestions.

    Args:
        suggestions: List of fix suggestions

    Returns:
        Total number of lines affected
    """
    return sum(
        s.line_end - s.line_start + 1
        for s in suggestions
    )


def _determine_max_severity(
    suggestions: List[FixSuggestion],
    review_outcome: Optional[Dict[str, Any]] = None
) -> SeverityType:
    """Determine maximum severity from suggestions and review outcome.

    Priority:
    1. If review_outcome has severity, use it
    2. Otherwise, infer from suggestion categories

    Args:
        suggestions: List of fix suggestions
        review_outcome: Optional ReviewOutcome dict

    Returns:
        Maximum severity level
    """
    # Use review_outcome severity if available
    if review_outcome:
        severity = review_outcome.get("severity", "").lower()
        if severity in ("low", "medium", "high", "critical"):
            return severity  # type: ignore

    # Infer from suggestion categories
    if not suggestions:
        return "low"

    # Security and bug_fix are higher severity
    has_security = any(s.category == "security" for s in suggestions)
    has_bug_fix = any(s.category == "bug_fix" for s in suggestions)

    if has_security:
        return "high"
    if has_bug_fix:
        return "medium"
    return "low"


def _is_auto_fix_eligible(
    review_outcome: Optional[Dict[str, Any]],
    suggestions: List[FixSuggestion],
    max_severity: SeverityType
) -> bool:
    """Determine if auto-fix is eligible.

    Conditions for auto-fix eligibility:
    1. review_outcome.severity == "low"
    2. review_outcome.diff_truncated == False
    3. review_outcome.schema_validated == True
    4. max_severity in ("low", "medium") - no high/critical
    5. At least one suggestion with confidence >= 0.8

    Args:
        review_outcome: ReviewOutcome dict
        suggestions: List of fix suggestions
        max_severity: Maximum severity level

    Returns:
        True if auto-fix is eligible
    """
    if not review_outcome:
        return False

    # Check ReviewOutcome conditions (aligned with autofix_gate.py)
    severity = review_outcome.get("severity", "").lower()
    diff_truncated = review_outcome.get("diff_truncated", True)
    schema_validated = review_outcome.get("schema_validated", False)

    if severity != "low":
        logger.debug(
            f"[FIX_HANDOFF] auto_fix_eligible=False: severity={severity}"
        )
        return False

    if diff_truncated:
        logger.debug(
            "[FIX_HANDOFF] auto_fix_eligible=False: diff_truncated=True"
        )
        return False

    if not schema_validated:
        logger.debug(
            "[FIX_HANDOFF] auto_fix_eligible=False: schema_validated=False"
        )
        return False

    # Check max_severity
    if max_severity in ("high", "critical"):
        logger.debug(
            f"[FIX_HANDOFF] auto_fix_eligible=False: max_severity={max_severity}"
        )
        return False

    # Check for high-confidence suggestions (use any() for efficiency)
    if not any(s.confidence >= HIGH_CONFIDENCE_THRESHOLD for s in suggestions):
        logger.debug(
            "[FIX_HANDOFF] auto_fix_eligible=False: no high-confidence suggestions"
        )
        return False

    logger.debug("[FIX_HANDOFF] auto_fix_eligible=True")
    return True


def build_fix_handoff(
    pr_number: int,
    suggestions: List[FixSuggestion],
    review_outcome: Optional[Dict[str, Any]] = None,
    review_id: Optional[str] = None,
    requires_human_review: bool = True
) -> ReviewToFixHandoff:
    """Build ReviewToFixHandoff from suggestions and review outcome.

    This is the primary entry point for constructing ReviewToFixHandoff.
    It handles data assembly and derived metrics computation.

    Note: `requires_human_review` is passed as a parameter rather than computed
    here. The decision of whether human review is required should be made by
    the Router or upstream producer, not by this schema builder. This avoids
    the contract anti-pattern of duplicating decision-making logic across
    components.

    Args:
        pr_number: Pull request number
        suggestions: List of fix suggestions
        review_outcome: Optional ReviewOutcome dict for eligibility checks
        review_id: Optional review ID (auto-generated if not provided)
        requires_human_review: Whether human review is required (default True
            for safety). The caller (Router/producer) should determine this.

    Security Warning:
        Setting `requires_human_review=False` bypasses human review for auto-fix.
        Only set this to False when ALL of the following are true:
        1. The suggestions are low-risk (style, refactor only)
        2. The confidence scores are high (>= HIGH_CONFIDENCE_THRESHOLD)
        3. The PR is from a trusted source
        4. The repository has adequate test coverage
        Misuse of this parameter can lead to unreviewed code changes.

    Returns:
        ReviewToFixHandoff instance ready to be stored in state

    Example:
        handoff = build_fix_handoff(
            pr_number=123,
            suggestions=[
                FixSuggestion(
                    file_path="src/utils.py",
                    line_start=10,
                    line_end=15,
                    original_code="def foo():",
                    suggested_code="def foo() -> None:",
                    reason="Add return type annotation",
                    confidence=0.9,
                    category="style"
                )
            ],
            review_outcome=state.get("review_outcome"),
            requires_human_review=False  # Router determined this
        )
        state["fix_handoff"] = handoff.model_dump()
    """
    # Generate review_id if not provided
    if not review_id:
        review_id = f"review-{uuid.uuid4().hex[:8]}"

    # Compute derived fields (data assembly only, no policy decisions)
    total_lines = _compute_total_lines(suggestions)
    max_severity = _determine_max_severity(suggestions, review_outcome)
    auto_fix_eligible = _is_auto_fix_eligible(
        review_outcome, suggestions, max_severity
    )

    return ReviewToFixHandoff(
        review_id=review_id,
        pr_number=pr_number,
        suggestions=suggestions,
        auto_fix_eligible=auto_fix_eligible,
        requires_human_review=requires_human_review,
        total_lines_affected=total_lines,
        max_severity=max_severity
    )


def should_route_to_fixer(handoff: ReviewToFixHandoff) -> bool:
    """Decide whether to route to fixer_node.

    This function is used by the Router to decide if the PR should be
    routed to fixer_node for auto-fix. It trusts the `auto_fix_eligible`
    flag computed by `build_fix_handoff()` and only adds a hard safety
    check for max_severity.

    Note: High-confidence suggestion check is already part of auto_fix_eligible
    computation in `_is_auto_fix_eligible()`. We don't duplicate it here to
    avoid maintenance cost and risk of divergence.

    Conditions:
    1. handoff.auto_fix_eligible must be True
    2. handoff.max_severity must NOT be "high" or "critical" (hard safety check)

    Args:
        handoff: ReviewToFixHandoff instance

    Returns:
        True if should route to fixer_node

    Event Codes (greppable):
        [ROUTE_TO_FIXER] - Routing to fixer_node
        [SKIP_FIXER] - Not routing to fixer_node
    """
    # Check auto_fix_eligible (trusts the eligibility computation)
    if not handoff.auto_fix_eligible:
        logger.info("[SKIP_FIXER] auto_fix_eligible=False")
        return False

    # Hard safety check for max_severity (defensive, even if auto_fix_eligible)
    if handoff.max_severity in ("high", "critical"):
        logger.info(
            f"[SKIP_FIXER] max_severity={handoff.max_severity} (hard safety check)"
        )
        return False

    logger.info(
        f"[ROUTE_TO_FIXER] pr_number={handoff.pr_number}, "
        f"suggestions={len(handoff.suggestions)}"
    )
    return True


def build_empty_handoff(
    pr_number: int,
    review_id: Optional[str] = None
) -> Dict[str, Any]:
    """Build an empty handoff dict for cases with no suggestions.

    Use this when Reviewer has no fix suggestions but we still need
    to populate the fix_handoff field in state.

    Args:
        pr_number: Pull request number
        review_id: Optional review ID (auto-generated if not provided)

    Returns:
        Dict representation of empty ReviewToFixHandoff
    """
    if not review_id:
        review_id = f"review-{uuid.uuid4().hex[:8]}"

    return {
        "schema_version": 1,
        "review_id": review_id,
        "pr_number": pr_number,
        "suggestions": [],
        "auto_fix_eligible": False,
        "requires_human_review": True,
        "total_lines_affected": 0,
        "max_severity": "low"
    }
