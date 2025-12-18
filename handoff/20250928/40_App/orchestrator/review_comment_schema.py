#!/usr/bin/env python3
"""
Review Comment Schema - EPIC B Phase B-2 Implementation
Canonical schema definition for review comments with backward compatibility

This module provides:
1. Canonical ReviewComment schema with start_line/end_line support
2. Parser that handles both old (line) and new (start_line/end_line) formats
3. Validation and normalization logic for edge cases
4. Severity mapping between different taxonomies

Issue #2595: EPIC B - Diff-Aware Review Plumbing
Phase B-2: Review Comment Schema Definition

Usage:
    from review_comment_schema import parse_review_comment, normalize_review_comments

    # Parse a single comment (handles both old and new formats)
    comment = parse_review_comment({
        "file": "src/utils.py",
        "line": 42,
        "message": "Consider using list comprehension"
    })

    # Normalize a list of comments
    normalized = normalize_review_comments(raw_comments)
"""
import logging
from typing import Any, Dict, List, Optional, TypedDict, Literal, get_args

logger = logging.getLogger(__name__)

# Canonical severity levels for internal use
# Maps to GitHub inline comment importance
CanonicalSeverity = Literal["info", "suggestion", "warning", "error", "critical"]

# LLM output severity (from llm_reviewer_adapter.py prompt)
LLMSeverity = Literal["nit", "suggestion", "warning", "error"]

# CI-only severity (from langgraph_orchestrator.py _ci_only_review)
CISeverity = Literal["low", "medium", "high", "critical"]

# Comment categories
CommentCategory = Literal[
    "style", "bug", "performance", "security",
    "maintainability", "documentation", "other"
]


class ReviewComment(TypedDict, total=False):
    """
    Canonical review comment schema.

    This is the normalized format used internally after parsing.
    All consumers of review comments should expect this format.

    Required fields:
        message: The review comment text

    Optional fields:
        file: File path (required for inline comments)
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed, >= start_line)
        severity: Canonical severity level
        category: Comment category
        source: Origin of the comment ("llm", "ci", "human")
        raw: Original unparsed comment dict (for debugging)
    """
    message: str
    file: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    severity: CanonicalSeverity
    category: CommentCategory
    source: Literal["llm", "ci", "human"]
    raw: Optional[Dict[str, Any]]


# Severity mapping from LLM output to canonical
LLM_SEVERITY_MAP: Dict[str, CanonicalSeverity] = {
    "nit": "info",
    "suggestion": "suggestion",
    "warning": "warning",
    "error": "error",
}

# Severity mapping from CI-only output to canonical
CI_SEVERITY_MAP: Dict[str, CanonicalSeverity] = {
    "none": "info",
    "low": "info",
    "medium": "warning",
    "high": "error",
    "critical": "critical",
}

# Default category when not specified
DEFAULT_CATEGORY: CommentCategory = "other"

# Maximum allowed line range (to detect hallucinated ranges)
MAX_LINE_RANGE = 500


def _normalize_severity(
    severity: Optional[str],
    source: Literal["llm", "ci", "human"] = "llm"
) -> CanonicalSeverity:
    """
    Normalize severity from various sources to canonical format.

    Args:
        severity: Raw severity string from source
        source: Origin of the comment

    Returns:
        Canonical severity level
    """
    if not severity:
        return "info"

    severity_lower = severity.lower().strip()

    if source == "ci":
        return CI_SEVERITY_MAP.get(severity_lower, "warning")
    else:
        # LLM or human - use LLM mapping
        return LLM_SEVERITY_MAP.get(severity_lower, "suggestion")


def _normalize_category(category: Optional[str]) -> CommentCategory:
    """
    Normalize category to allowed values.

    Args:
        category: Raw category string

    Returns:
        Valid category or "other"
    """
    if not category:
        return DEFAULT_CATEGORY

    category_lower = category.lower().strip()
    # Use get_args to keep Literal and set in sync
    valid_categories = set(get_args(CommentCategory))

    if category_lower in valid_categories:
        return category_lower  # type: ignore

    # Map common variations
    category_aliases = {
        "formatting": "style",
        "code style": "style",
        "lint": "style",
        "error": "bug",
        "issue": "bug",
        "perf": "performance",
        "speed": "performance",
        "sec": "security",
        "vulnerability": "security",
        "refactor": "maintainability",
        "cleanup": "maintainability",
        "docs": "documentation",
        "comment": "documentation",
    }

    return category_aliases.get(category_lower, DEFAULT_CATEGORY)


def _parse_line_number(value: Any) -> Optional[int]:
    """
    Parse a line number from various input types.

    Args:
        value: Raw line number (int, str, or None)

    Returns:
        Positive integer line number or None
    """
    if value is None:
        return None

    try:
        line = int(value)
        if line > 0:
            return line
        return None
    except (ValueError, TypeError):
        return None


def validate_line_range(
    start_line: Optional[int],
    end_line: Optional[int],
    max_range: int = MAX_LINE_RANGE
) -> tuple[Optional[int], Optional[int], bool]:
    """
    Validate and normalize a line range.

    Handles edge cases:
    - start_line > end_line: swap them
    - Negative or zero values: set to None
    - Range too large: flag as low confidence

    Args:
        start_line: Starting line number
        end_line: Ending line number
        max_range: Maximum allowed range size

    Returns:
        Tuple of (normalized_start, normalized_end, is_valid)
        is_valid is False if range was invalid or suspicious
    """
    # Parse to ensure valid integers
    start = _parse_line_number(start_line)
    end = _parse_line_number(end_line)

    # If both are None, that's valid (no line info)
    if start is None and end is None:
        return None, None, True

    # If only one is set, use it for both (single line)
    if start is None and end is not None:
        return end, end, True
    if end is None and start is not None:
        return start, start, True

    # Both are set - validate
    assert start is not None and end is not None

    # Swap if reversed
    if start > end:
        logger.warning(
            f"[ReviewCommentSchema] start_line ({start}) > end_line ({end}), swapping"
        )
        start, end = end, start

    # Check range size
    range_size = end - start + 1
    if range_size > max_range:
        logger.warning(
            f"[ReviewCommentSchema] Line range too large ({range_size} lines), "
            f"flagging as low confidence"
        )
        return start, end, False

    return start, end, True


def parse_review_comment(
    raw: Dict[str, Any],
    source: Literal["llm", "ci", "human"] = "llm",
    preserve_raw: bool = False
) -> Optional[ReviewComment]:
    """
    Parse a raw comment dict into canonical ReviewComment format.

    Handles both old format (line) and new format (start_line/end_line).

    Old format:
        {"file": "...", "line": 42, "message": "..."}

    New format:
        {"file": "...", "start_line": 40, "end_line": 45, "message": "..."}

    Args:
        raw: Raw comment dictionary
        source: Origin of the comment
        preserve_raw: Whether to include original dict in output

    Returns:
        Normalized ReviewComment or None if invalid
    """
    if not raw or not isinstance(raw, dict):
        logger.warning("[ReviewCommentSchema] Invalid comment: not a dict")
        return None

    # Message is required
    message = raw.get("message")
    if not message or not isinstance(message, str) or not message.strip():
        logger.warning("[ReviewCommentSchema] Invalid comment: missing or empty message")
        return None

    # Parse line numbers - support both old and new formats
    # New format: start_line/end_line
    # Old format: line (treated as end_line, with start_line = end_line)
    raw_start = raw.get("start_line")
    raw_end = raw.get("end_line") or raw.get("line")

    start_line, end_line, line_valid = validate_line_range(raw_start, raw_end)

    # Build canonical comment
    comment: ReviewComment = {
        "message": message.strip(),
        "severity": _normalize_severity(raw.get("severity"), source),
        "category": _normalize_category(raw.get("category")),
        "source": source,
    }

    # Add file if present
    file_path = raw.get("file") or raw.get("path") or raw.get("file_path")
    if file_path and isinstance(file_path, str):
        comment["file"] = file_path.strip()

    # Add line numbers only if valid
    # When line_valid=False (e.g., range > 500 lines), downgrade to file-level comment
    # This prevents suspicious/hallucinated ranges from being posted as inline comments
    if line_valid:
        if start_line is not None:
            comment["start_line"] = start_line
        if end_line is not None:
            comment["end_line"] = end_line
    else:
        logger.warning(
            f"[ReviewCommentSchema] Downgrading to file-level comment due to "
            f"invalid line range (start={start_line}, end={end_line})"
        )

    # Optionally preserve raw for debugging
    if preserve_raw:
        comment["raw"] = raw

    return comment


def normalize_review_comments(
    raw_comments: List[Dict[str, Any]],
    source: Literal["llm", "ci", "human"] = "llm",
    preserve_raw: bool = False
) -> List[ReviewComment]:
    """
    Normalize a list of raw comments to canonical format.

    Filters out invalid comments and logs warnings.

    Args:
        raw_comments: List of raw comment dicts
        source: Origin of the comments
        preserve_raw: Whether to include original dicts in output

    Returns:
        List of normalized ReviewComment objects
    """
    if not raw_comments:
        return []

    normalized = []
    invalid_count = 0

    for raw in raw_comments:
        comment = parse_review_comment(raw, source, preserve_raw)
        if comment:
            normalized.append(comment)
        else:
            invalid_count += 1

    if invalid_count > 0:
        logger.warning(
            f"[ReviewCommentSchema] Filtered {invalid_count} invalid comments "
            f"out of {len(raw_comments)} total"
        )

    return normalized


def is_inline_comment(comment: ReviewComment) -> bool:
    """
    Check if a comment has enough information for GitHub inline review.

    Requires: file path and at least end_line.

    Args:
        comment: Normalized review comment

    Returns:
        True if comment can be posted as inline review
    """
    return bool(
        comment.get("file") and
        comment.get("end_line") is not None
    )


def to_github_inline_payload(
    comment: ReviewComment,
    commit_id: str,
    side: Literal["LEFT", "RIGHT"] = "RIGHT"
) -> Optional[Dict[str, Any]]:
    """
    Convert a ReviewComment to GitHub Pull Request Review Comment API payload.

    This is a preview of Phase B-3 functionality.

    GitHub API requires:
    - body: Comment text
    - commit_id: SHA of the commit to comment on
    - path: File path
    - line: End line number (required)
    - side: LEFT or RIGHT (default RIGHT for new code)
    - start_line: Start line (optional, for multi-line)
    - start_side: Side for start line (optional)

    Args:
        comment: Normalized review comment
        commit_id: PR head commit SHA
        side: Which side of diff to comment on

    Returns:
        GitHub API payload dict or None if not enough info
    """
    if not is_inline_comment(comment):
        logger.debug(
            "[ReviewCommentSchema] Comment missing file or line info, "
            "cannot create inline payload"
        )
        return None

    if not commit_id:
        logger.warning("[ReviewCommentSchema] Missing commit_id for inline comment")
        return None

    payload: Dict[str, Any] = {
        "body": comment["message"],
        "commit_id": commit_id,
        "path": comment["file"],
        "line": comment["end_line"],
        "side": side,
    }

    # Add start_line for multi-line comments
    start = comment.get("start_line")
    end = comment.get("end_line")
    if start is not None and end is not None and start < end:
        payload["start_line"] = start
        payload["start_side"] = side

    return payload


def merge_review_comments(
    ci_comments: List[Dict[str, Any]],
    llm_comments: List[Dict[str, Any]],
    preserve_raw: bool = False
) -> List[ReviewComment]:
    """
    Merge CI-only and LLM comments into a single normalized list.

    This is useful in reviewer_node where both sources contribute.

    Args:
        ci_comments: Comments from CI-only review
        llm_comments: Comments from LLM review
        preserve_raw: Whether to include original dicts

    Returns:
        Merged and normalized list of comments
    """
    normalized_ci = normalize_review_comments(ci_comments, "ci", preserve_raw)
    normalized_llm = normalize_review_comments(llm_comments, "llm", preserve_raw)

    return normalized_ci + normalized_llm
