"""
B-9.6: Comment Validator - False Positive Detection

EPIC B Phase 7 Implementation - Blueprint Section 4.1 "Safe by Design"

This module implements post-processing validation for LLM review comments
to detect and filter false positives before posting to GitHub.

Problem Statement (Issue #3881):
LLM reviewers sometimes claim that function arguments are missing when they
are actually present on subsequent lines of multi-line function calls.
Standard ast.parse() cannot be used because diff fragments are incomplete
Python syntax.

Solution: Fuzzy Parsing (Regex)
Use regex patterns to extract and validate function call arguments from
diff content, without requiring complete Python syntax.

Blueprint Alignment:
- Section 4.1 "Safe by Design" - Post-processing validation prevents false positives
- Section 3.3 "Agent Separation Principle" - Validator only filters, doesn't modify

Usage:
    from review_context.comment_validator import CommentValidator

    validator = CommentValidator(trace_id="abc123")
    validated_comments, filtered_comments, stats = validator.validate_comments(
        comments=review_comments,
        diff_content=diff_content
    )
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# Regex patterns for fuzzy parsing
# Pattern to match keyword arguments (name=value)
KEYWORD_ARG_PATTERN = re.compile(
    r'(\w+)\s*=',      # Argument name followed by =
    re.MULTILINE
)

# Pattern to detect "missing argument" claims in review comments
MISSING_ARG_CLAIM_PATTERNS = [
    re.compile(r'missing\s+(?:required\s+)?(?:argument|parameter)s?\s*[:\-]?\s*[`\'"]*(\w+)', re.IGNORECASE),
    re.compile(r'(?:argument|parameter)s?\s+[`\'"]*(\w+)[`\'"]*\s+(?:is|are)\s+missing', re.IGNORECASE),
    re.compile(r'does\s+not\s+(?:pass|provide|include)\s+[`\'"]*(\w+)', re.IGNORECASE),
    re.compile(r'(?:forgot|omitted|left\s+out)\s+[`\'"]*(\w+)', re.IGNORECASE),
    re.compile(r'[`\'"]*(\w+)[`\'"]*\s+(?:is|was)\s+not\s+(?:passed|provided|included)', re.IGNORECASE),
]


@dataclass
class ValidationResult:
    """
    Result of validating a single comment.

    Attributes:
        is_valid: Whether the comment passed validation
        reason: Reason for filtering (if not valid)
        claimed_missing_args: Arguments the comment claims are missing
        actual_args_found: Arguments actually found in the diff
        confidence: Confidence level of the validation (0.0 to 1.0)
    """
    is_valid: bool
    reason: Optional[str] = None
    claimed_missing_args: List[str] = field(default_factory=list)
    actual_args_found: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class ValidationStats:
    """
    Statistics from comment validation.

    Attributes:
        total_comments: Total number of comments processed
        validated_comments: Number of comments that passed validation
        filtered_false_positives: Number of false positives filtered
        false_positive_rate: Ratio of false positives to total
        filter_reasons: Breakdown of filter reasons
    """
    total_comments: int = 0
    validated_comments: int = 0
    filtered_false_positives: int = 0
    false_positive_rate: float = 0.0
    filter_reasons: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_comments": self.total_comments,
            "validated_comments": self.validated_comments,
            "filtered_false_positives": self.filtered_false_positives,
            "false_positive_rate": self.false_positive_rate,
            "filter_reasons": self.filter_reasons,
        }


class CommentValidator:
    """
    Post-processing validator for LLM review comments.

    Uses fuzzy parsing (regex) to validate LLM claims about missing
    function arguments without requiring complete Python syntax.

    Blueprint Alignment:
    - Section 4.1 "Safe by Design" - Prevents false positives
    - Section 3.3 "Agent Separation Principle" - Only filters, doesn't modify

    Attributes:
        trace_id: Trace ID for logging correlation
    """

    def __init__(self, trace_id: Optional[str] = None):
        """
        Initialize the comment validator.

        Args:
            trace_id: Optional trace ID for logging correlation
        """
        self.trace_id = trace_id or "unknown"

    def validate_comments(
        self,
        comments: List[Dict[str, Any]],
        diff_content: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], ValidationStats]:
        """
        Validate a list of review comments against diff content.

        Args:
            comments: List of review comment dicts
            diff_content: The PR diff content

        Returns:
            Tuple of (validated_comments, filtered_comments, stats)
        """
        stats = ValidationStats(total_comments=len(comments))
        validated = []
        filtered = []

        for comment in comments:
            result = self._validate_single_comment(comment, diff_content)

            if result.is_valid:
                validated.append(comment)
                stats.validated_comments += 1
            else:
                # Add validation metadata to filtered comment
                filtered_comment = comment.copy()
                filtered_comment["_validation_reason"] = result.reason
                filtered_comment["_claimed_missing_args"] = result.claimed_missing_args
                filtered_comment["_actual_args_found"] = result.actual_args_found
                filtered.append(filtered_comment)
                stats.filtered_false_positives += 1

                # Track filter reasons
                reason_key = result.reason or "unknown"
                stats.filter_reasons[reason_key] = stats.filter_reasons.get(reason_key, 0) + 1

        # Calculate false positive rate
        if stats.total_comments > 0:
            stats.false_positive_rate = stats.filtered_false_positives / stats.total_comments

        # Log validation results
        if stats.filtered_false_positives > 0:
            logger.info(
                f"[CommentValidator] Filtered {stats.filtered_false_positives} false positives "
                f"out of {stats.total_comments} comments (rate: {stats.false_positive_rate:.2%})",
                extra={
                    "operation": "comment_validator",
                    "trace_id": self.trace_id,
                    "total_comments": stats.total_comments,
                    "validated_comments": stats.validated_comments,
                    "filtered_false_positives": stats.filtered_false_positives,
                    "false_positive_rate": stats.false_positive_rate,
                    "filter_reasons": stats.filter_reasons,
                }
            )

        return validated, filtered, stats

    def _validate_single_comment(
        self,
        comment: Dict[str, Any],
        diff_content: str
    ) -> ValidationResult:
        """
        Validate a single review comment.

        Currently validates:
        - Claims about missing function arguments

        Args:
            comment: Review comment dict
            diff_content: The PR diff content

        Returns:
            ValidationResult indicating if comment is valid
        """
        message = comment.get("message", "")
        file_path = comment.get("file")

        # Extract claimed missing arguments from the comment
        claimed_missing = self._extract_claimed_missing_args(message)

        if not claimed_missing:
            # No claims about missing arguments - pass through
            return ValidationResult(is_valid=True)

        # Extract file-specific diff content if file_path is available
        file_diff = self._extract_file_diff(diff_content, file_path) if file_path else diff_content

        # Find all arguments actually present in the diff
        actual_args = self._extract_arguments_from_diff(file_diff)

        # Check if any claimed missing arguments are actually present
        actual_args_lower = {arg.lower() for arg in actual_args}
        false_positive_args = []
        for claimed_arg in claimed_missing:
            if claimed_arg.lower() in actual_args_lower:
                false_positive_args.append(claimed_arg)

        if false_positive_args:
            # This is a false positive - the claimed missing args are present
            return ValidationResult(
                is_valid=False,
                reason="missing_arg_false_positive",
                claimed_missing_args=claimed_missing,
                actual_args_found=list(actual_args),
                confidence=0.9  # High confidence when we find the args
            )

        # Comment appears valid
        return ValidationResult(
            is_valid=True,
            claimed_missing_args=claimed_missing,
            actual_args_found=list(actual_args)
        )

    def _extract_claimed_missing_args(self, message: str) -> List[str]:
        """
        Extract argument names that the comment claims are missing.

        Args:
            message: The review comment message

        Returns:
            List of argument names claimed to be missing
        """
        claimed_args = []

        for pattern in MISSING_ARG_CLAIM_PATTERNS:
            matches = pattern.findall(message)
            claimed_args.extend(matches)

        # Deduplicate while preserving order
        seen = set()
        unique_args = []
        for arg in claimed_args:
            if arg.lower() not in seen:
                seen.add(arg.lower())
                unique_args.append(arg)

        return unique_args

    def _extract_file_diff(self, diff_content: str, file_path: str) -> str:
        """
        Extract the diff section for a specific file.

        Args:
            diff_content: Full diff content
            file_path: Path to the file

        Returns:
            Diff content for the specific file, or full diff if not found
        """
        # Pattern to match file header in unified diff
        # Handles both "--- a/path" and "+++ b/path" formats
        file_pattern = re.compile(
            rf'(?:^|\n)(?:---\s+a/|diff\s+--git\s+a/){re.escape(file_path)}.*?'
            rf'(?=\n(?:diff\s+--git|$))',
            re.DOTALL
        )

        match = file_pattern.search(diff_content)
        if match:
            return match.group(0)

        # Fallback: try simpler pattern
        simple_pattern = re.compile(
            rf'{re.escape(file_path)}.*?(?=\ndiff\s+--git|\Z)',
            re.DOTALL
        )
        match = simple_pattern.search(diff_content)
        if match:
            return match.group(0)

        return diff_content

    def _extract_arguments_from_diff(self, diff_content: str) -> Set[str]:
        """
        Extract all argument names from function calls in the diff.

        Uses fuzzy parsing (regex) to handle incomplete Python syntax.

        Args:
            diff_content: Diff content to parse

        Returns:
            Set of argument names found
        """
        args_found = set()

        # Extract keyword arguments from the diff
        # This handles multi-line function calls
        for match in KEYWORD_ARG_PATTERN.finditer(diff_content):
            arg_name = match.group(1)
            # Filter out common false positives (Python keywords, etc.)
            if arg_name not in {
                'False', 'None', 'True', 'and', 'as', 'assert', 'async',
                'await', 'break', 'class', 'continue', 'def', 'del', 'elif',
                'else', 'except', 'finally', 'for', 'from', 'global', 'if',
                'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
                'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
                'self', 'cls'
            }:
                args_found.add(arg_name)

        return args_found


def validate_review_comments(
    comments: List[Dict[str, Any]],
    diff_content: str,
    trace_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], ValidationStats]:
    """
    Convenience function to validate review comments.

    Args:
        comments: List of review comment dicts
        diff_content: The PR diff content
        trace_id: Optional trace ID for logging

    Returns:
        Tuple of (validated_comments, filtered_comments, stats)
    """
    validator = CommentValidator(trace_id=trace_id)
    return validator.validate_comments(comments, diff_content)
