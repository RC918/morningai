#!/usr/bin/env python3
"""
Review Comment Schema - EPIC B Phase B-2 Implementation
Canonical schema definition for review comments with backward compatibility

This module provides:
1. Canonical ReviewComment schema with start_line/end_line support
2. Parser that handles both old (line) and new (start_line/end_line) formats
3. Validation and normalization logic for edge cases
4. Severity mapping between different taxonomies
5. Unified diff parser for extracting valid RIGHT-side line ranges (Phase B-3.1)
6. Inline comment validator to gate comments against allowed line ranges (Phase B-3.1)
7. Telemetry fields for Phase B-B staging verification

Issue #2595: EPIC B - Diff-Aware Review Plumbing
Phase B-2: Review Comment Schema Definition
Phase B-3.1: Line Number Validation & Truncation Handling
Phase B-B: Staging Verification (Dry-run)

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

    # Parse diff and validate inline comments (Phase B-3.1)
    from review_comment_schema import parse_diff_allowed_lines, validate_inline_comments
    allowed_lines = parse_diff_allowed_lines(diff_content)
    valid, invalid, downgrade_reasons = validate_inline_comments(comments, allowed_lines)
    # downgrade_reasons: Dict with keys file_not_in_diff, line_not_in_diff,
    #                    missing_end_line, strict_truncated, other
"""
import logging
import re
from typing import Any, Dict, List, Optional, TypedDict, Literal, get_args, Set, Tuple

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
        schema_version: Schema version (e.g., "1.0")
        raw: Original unparsed comment dict (for debugging)
    """
    message: str
    file: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    severity: CanonicalSeverity
    category: CommentCategory
    source: Literal["llm", "ci", "human"]
    schema_version: str
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

# Current schema version (semantic versioning: major.minor)
# - v1.0: Initial schema with start_line/end_line support
SCHEMA_VERSION = "1.0"

# Valid categories as frozenset for efficient lookup (extracted from Literal)
VALID_CATEGORIES: frozenset[str] = frozenset(get_args(CommentCategory))


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

    # Use module-level VALID_CATEGORIES frozenset for efficient lookup
    if category_lower in VALID_CATEGORIES:
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
        logger.debug(
            f"[ReviewCommentSchema] start_line ({start}) > end_line ({end}), swapping"
        )
        start, end = end, start

    # Check range size
    range_size = end - start + 1
    if range_size > max_range:
        logger.debug(
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
        "schema_version": SCHEMA_VERSION,
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
        # WARNING: This indicates Agent failed to locate code precisely.
        # This is a quality degradation that we need to be aware of, not hide.
        # If warnings are too frequent, fix the prompt/model, not the log level.
        logger.warning(
            f"[ReviewCommentSchema] Downgrading to file-level comment due to "
            f"invalid line range (start={start_line}, end={end_line})"
        )
        # TODO (#2695): Add metrics counter here
        # metrics.increment("review.schema.downgrade_to_file_level")

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


# =============================================================================
# Phase B-3.1: Unified Diff Parser and Inline Comment Validator
# =============================================================================
# These functions address three high-risk items:
# 1. Line number semantics: Clarify that line numbers are RIGHT-side file lines
# 2. Truncated diff handling: Validate comments against visible diff hunks
# 3. Partial patch detection: Detect and handle truncated patches per file
# =============================================================================

# Regex patterns for unified diff parsing
DIFF_FILE_HEADER_PATTERN = re.compile(r'^--- a/(.+)$', re.MULTILINE)
DIFF_NEW_FILE_HEADER_PATTERN = re.compile(r'^\+\+\+ b/(.+)$', re.MULTILINE)
DIFF_HUNK_HEADER_PATTERN = re.compile(
    r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',
    re.MULTILINE
)
# Sentinel for truncated patches (from get_pr_diff)
TRUNCATION_SENTINEL = "... (truncated"


class DiffFileInfo(TypedDict):
    """Information about a file in the diff."""
    filename: str
    allowed_lines: Set[int]  # RIGHT-side line numbers that appear in diff
    patch_truncated: bool  # Whether the patch was truncated mid-file


def parse_diff_allowed_lines(diff_content: str) -> Dict[str, DiffFileInfo]:
    """
    Parse unified diff to extract valid RIGHT-side line numbers per file.

    Phase B-3.1: Line Number Validation
    Issue #2595: EPIC B - Diff-Aware Review Plumbing

    This function parses the unified diff that was sent to the LLM and extracts
    the set of RIGHT-side (new file) line numbers that appear in each file's
    diff hunks. This is used to validate inline comments before posting to GitHub.

    GitHub's inline comment API requires that the line number exists in the
    PR's diff context. Comments referencing lines outside the diff will fail
    with 422 errors.

    Algorithm:
    1. Split diff by file sections (--- a/... and +++ b/...)
    2. For each file, parse hunk headers (@@ -old,len +new,len @@)
    3. Walk hunk body lines and track RIGHT-side line numbers:
       - ' ' (context): allow this line, increment both counters
       - '+' (addition): allow this line, increment new counter only
       - '-' (deletion): increment old counter only, don't allow
    4. Detect truncation sentinel to mark patch_truncated=True

    Args:
        diff_content: Unified diff string (from get_pr_diff)

    Returns:
        Dict mapping filename to DiffFileInfo with allowed_lines set
    """
    if not diff_content:
        return {}

    result: Dict[str, DiffFileInfo] = {}

    # Split by file sections
    # Each file section starts with "--- a/filename" and "+++ b/filename"
    lines = diff_content.split('\n')
    current_file: Optional[str] = None
    current_allowed: Set[int] = set()
    current_truncated = False
    new_line_counter = 0
    in_hunk = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for new file header
        if line.startswith('+++ b/'):
            # Save previous file if exists
            if current_file is not None:
                result[current_file] = {
                    "filename": current_file,
                    "allowed_lines": current_allowed,
                    "patch_truncated": current_truncated
                }

            # Extract filename (handle +++ b/dev/null for deleted files)
            if line == '+++ b/dev/null' or line.startswith('+++ /dev/null'):
                # Deleted file - no RIGHT-side lines allowed
                current_file = None
            else:
                # Remove "+++ b/" prefix and handle quoted paths
                # Git may quote paths with spaces or special chars: +++ b/"path with spaces.txt"
                raw_path = line[6:]
                if raw_path.startswith('"') and raw_path.endswith('"'):
                    raw_path = raw_path[1:-1]  # Strip surrounding quotes
                current_file = raw_path
                current_allowed = set()
                current_truncated = False
            in_hunk = False
            i += 1
            continue

        # Check for hunk header
        hunk_match = DIFF_HUNK_HEADER_PATTERN.match(line)
        if hunk_match and current_file is not None:
            # Parse hunk header: @@ -old_start,old_len +new_start,new_len @@
            new_start = int(hunk_match.group(3))
            new_line_counter = new_start
            in_hunk = True
            i += 1
            continue

        # Check for truncation sentinel
        if TRUNCATION_SENTINEL in line:
            if current_file is not None:
                current_truncated = True
            in_hunk = False
            i += 1
            continue

        # Process hunk body lines
        if in_hunk and current_file is not None and line:
            first_char = line[0] if line else ''

            if first_char == ' ':
                # Context line: appears on both sides
                current_allowed.add(new_line_counter)
                new_line_counter += 1
            elif first_char == '+':
                # Addition: only on RIGHT side
                current_allowed.add(new_line_counter)
                new_line_counter += 1
            elif first_char == '-':
                # Deletion: only on LEFT side, don't add to allowed
                pass
            elif first_char == '\\':
                # "\ No newline at end of file" - ignore
                pass
            else:
                # Unknown line or end of hunk
                # Could be start of new hunk or file
                pass

        i += 1

    # Save last file
    if current_file is not None:
        result[current_file] = {
            "filename": current_file,
            "allowed_lines": current_allowed,
            "patch_truncated": current_truncated
        }

    logger.debug(
        f"[ReviewCommentSchema] Parsed diff: {len(result)} files, "
        f"truncated files: {sum(1 for f in result.values() if f['patch_truncated'])}"
    )

    return result


def is_line_in_diff(
    file_path: str,
    start_line: Optional[int],
    end_line: Optional[int],
    allowed_lines_map: Dict[str, DiffFileInfo]
) -> Tuple[bool, str]:
    """
    Check if a comment's line range is valid within the diff.

    Phase B-3.1: Inline Comment Validation

    Args:
        file_path: File path from the comment
        start_line: Start line number (1-indexed)
        end_line: End line number (1-indexed)
        allowed_lines_map: Result from parse_diff_allowed_lines

    Returns:
        Tuple of (is_valid, reason)
        - is_valid: True if the line range is fully contained in the diff
        - reason: Human-readable reason if invalid
    """
    if not file_path:
        return False, "missing_file_path"

    if file_path not in allowed_lines_map:
        return False, "file_not_in_diff"

    file_info = allowed_lines_map[file_path]

    # Note: Truncated patch handling is done in validate_inline_comments()
    # with strict_truncated flag. Here we just check if lines are visible.

    if end_line is None:
        return False, "missing_end_line"

    # Check if all lines in range are allowed
    start = start_line if start_line is not None else end_line
    allowed = file_info["allowed_lines"]

    for line_num in range(start, end_line + 1):
        if line_num not in allowed:
            return False, f"line_{line_num}_not_in_diff"

    return True, "valid"


def _bucket_downgrade_reason(reason: str) -> str:
    """
    Bucket raw downgrade reasons into canonical categories for telemetry.

    Phase B-B Telemetry: Downgrade reason bucketing

    Categories:
    - file_not_in_diff: File path not found in diff
    - line_not_in_diff: Line number(s) not visible in diff hunk
    - missing_end_line: Comment missing required end_line
    - strict_truncated: Truncated patch forced inline rejection

    Args:
        reason: Raw reason string from validation

    Returns:
        Canonical bucket name
    """
    if reason == "file_not_in_diff" or reason == "missing_file_path":
        return "file_not_in_diff"
    elif reason == "missing_end_line":
        return "missing_end_line"
    elif reason == "patch_truncated":
        return "strict_truncated"
    elif "not_in_diff" in reason:
        # Matches "line_N_not_in_diff" patterns
        return "line_not_in_diff"
    else:
        # Fallback for any unexpected reasons
        return "other"


def validate_inline_comments(
    comments: List[ReviewComment],
    allowed_lines_map: Dict[str, DiffFileInfo],
    strict_truncated: bool = True
) -> Tuple[List[ReviewComment], List[ReviewComment], Dict[str, int]]:
    """
    Validate inline comments against the diff and split into valid/invalid.

    Phase B-3.1: Inline Comment Validation
    Issue #2595: EPIC B - Diff-Aware Review Plumbing

    This function gates inline comments through a deterministic validator
    that checks if each comment's target lines exist in the diff that was
    shown to the LLM. Invalid comments are downgraded to file-level.

    Args:
        comments: List of normalized ReviewComment objects
        allowed_lines_map: Result from parse_diff_allowed_lines
        strict_truncated: If True, reject all inline comments for files
                         with truncated patches (safer but loses some value)

    Returns:
        Tuple of (valid_inline_comments, invalid_comments, downgrade_reasons)
        - valid_inline_comments: Comments that can be posted as inline
        - invalid_comments: Comments that failed validation (downgraded)
        - downgrade_reasons: Dict mapping reason bucket to count
          (Phase B-B Telemetry)
    """
    valid: List[ReviewComment] = []
    invalid: List[ReviewComment] = []
    # Phase B-B Telemetry: Track downgrade reasons by bucket
    downgrade_reasons: Dict[str, int] = {
        "file_not_in_diff": 0,
        "line_not_in_diff": 0,
        "missing_end_line": 0,
        "strict_truncated": 0,
        "other": 0
    }

    for comment in comments:
        # Skip non-inline comments (no file or line info)
        if not is_inline_comment(comment):
            # Already file-level, pass through as valid
            valid.append(comment)
            continue

        file_path = comment.get("file")
        start_line = comment.get("start_line")
        end_line = comment.get("end_line")

        # Check if file has truncated patch
        if strict_truncated and file_path in allowed_lines_map:
            file_info = allowed_lines_map[file_path]
            if file_info["patch_truncated"]:
                # Downgrade: strip line info
                downgraded = _downgrade_to_file_level(
                    comment, "patch_truncated"
                )
                invalid.append(downgraded)
                downgrade_reasons["strict_truncated"] += 1
                continue

        # Validate line range
        is_valid, reason = is_line_in_diff(
            file_path, start_line, end_line, allowed_lines_map
        )

        if is_valid:
            valid.append(comment)
        else:
            # Downgrade: strip line info
            downgraded = _downgrade_to_file_level(comment, reason)
            invalid.append(downgraded)
            # Phase B-B Telemetry: Bucket the reason
            bucket = _bucket_downgrade_reason(reason)
            downgrade_reasons[bucket] += 1

    if invalid:
        logger.warning(
            f"[ReviewCommentSchema] Downgraded {len(invalid)} comments "
            f"to file-level due to line validation failures",
            extra={
                "operation": "validate_inline_comments",
                "valid_count": len(valid),
                "invalid_count": len(invalid),
                # Phase B-B Telemetry: Include reason breakdown
                "downgrade_reasons": downgrade_reasons
            }
        )

    return valid, invalid, downgrade_reasons


def _downgrade_to_file_level(
    comment: ReviewComment,
    reason: str
) -> ReviewComment:
    """
    Downgrade an inline comment to file-level by stripping line info.

    Args:
        comment: Original comment with line info
        reason: Reason for downgrade (for logging/debugging)

    Returns:
        New comment dict without line info
    """
    downgraded: ReviewComment = {
        "message": comment["message"],
        "severity": comment.get("severity", "info"),
        "category": comment.get("category", "other"),
        "source": comment.get("source", "llm"),
        "schema_version": comment.get("schema_version", SCHEMA_VERSION),
    }

    # Keep file path for file-level comment
    if comment.get("file"):
        downgraded["file"] = comment["file"]

    # Add downgrade reason to message for transparency
    downgraded["message"] = (
        f"[Line info removed: {reason}] {comment['message']}"
    )

    logger.debug(
        f"[ReviewCommentSchema] Downgraded comment for {comment.get('file')}: "
        f"lines {comment.get('start_line')}-{comment.get('end_line')} -> "
        f"file-level (reason: {reason})"
    )

    return downgraded


def get_diff_coverage_info(
    allowed_lines_map: Dict[str, DiffFileInfo]
) -> Dict[str, Any]:
    """
    Get summary information about diff coverage for logging/debugging.

    Args:
        allowed_lines_map: Result from parse_diff_allowed_lines

    Returns:
        Dict with coverage statistics
    """
    total_files = len(allowed_lines_map)
    truncated_files = sum(
        1 for f in allowed_lines_map.values() if f["patch_truncated"]
    )
    total_lines = sum(
        len(f["allowed_lines"]) for f in allowed_lines_map.values()
    )

    return {
        "total_files": total_files,
        "truncated_files": truncated_files,
        "total_allowed_lines": total_lines,
        "files": list(allowed_lines_map.keys()),
        # Phase B-B: Add coverage percentage for telemetry
        "truncation_rate": truncated_files / total_files if total_files > 0 else 0.0
    }
