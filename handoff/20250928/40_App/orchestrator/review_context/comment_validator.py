"""
B-9.6: Comment Validator - False Positive Detection + Deduplication

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

Issue #4063: Enhanced Verification Step
Added validation for more types of false positives:
- Missing argument claims (original)
- Undefined variable claims
- Import statement claims
- Type annotation claims

Issue #4064: Comment Deduplication
Added deduplication to filter duplicate comments:
- Same file + same line = duplicate
- Similar message content (>80% similarity) = duplicate

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
from difflib import SequenceMatcher
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

# Issue #4063: Additional false positive detection patterns
# Pattern to detect "undefined variable" claims
UNDEFINED_VAR_CLAIM_PATTERNS = [
    re.compile(r'(?:undefined|undeclared)\s+(?:variable|name|identifier)\s*[:\-]?\s*[`\'"]*(\w+)', re.IGNORECASE),
    re.compile(r'[`\'"]*(\w+)[`\'"]*\s+(?:is|was)\s+(?:not\s+defined|undefined)', re.IGNORECASE),
    re.compile(r'(?:name|variable)\s+[`\'"]*(\w+)[`\'"]*\s+(?:is|was)\s+not\s+(?:defined|declared)', re.IGNORECASE),
]

# Pattern to detect "missing import" claims
MISSING_IMPORT_CLAIM_PATTERNS = [
    re.compile(r'missing\s+import\s+(?:for\s+)?[`\'"]*(\w+)', re.IGNORECASE),
    re.compile(r'[`\'"]*(\w+)[`\'"]*\s+(?:is|was)\s+not\s+imported', re.IGNORECASE),
    re.compile(r'(?:need|should)\s+(?:to\s+)?import\s+[`\'"]*(\w+)', re.IGNORECASE),
]

# Pattern to extract import statements from diff
IMPORT_PATTERN = re.compile(
    r'(?:^|\n)\+?\s*(?:from\s+[\w.]+\s+)?import\s+(.+?)(?:\s+as\s+\w+)?(?:\s*#.*)?$',
    re.MULTILINE
)

# Pattern to extract variable definitions from diff
VARIABLE_DEF_PATTERN = re.compile(
    r'(?:^|\n)\+?\s*(\w+)\s*(?::\s*[\w\[\],\s]+)?\s*=',
    re.MULTILINE
)

# Issue #4064: Deduplication similarity threshold
DEDUP_SIMILARITY_THRESHOLD = 0.80  # 80% similarity = duplicate


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

        Issue #4063: Enhanced validation for multiple false positive types:
        - Claims about missing function arguments
        - Claims about undefined variables
        - Claims about missing imports

        Args:
            comment: Review comment dict
            diff_content: The PR diff content

        Returns:
            ValidationResult indicating if comment is valid
        """
        message = comment.get("message", "")
        file_path = comment.get("file")

        # Extract file-specific diff content if file_path is available
        file_diff = self._extract_file_diff(diff_content, file_path) if file_path else diff_content

        # 1. Validate missing argument claims (original)
        claimed_missing_args = self._extract_claimed_missing_args(message)
        if claimed_missing_args:
            actual_args = self._extract_arguments_from_diff(file_diff)
            actual_args_lower = {arg.lower() for arg in actual_args}
            false_positive_args = [
                arg for arg in claimed_missing_args
                if arg.lower() in actual_args_lower
            ]
            if false_positive_args:
                return ValidationResult(
                    is_valid=False,
                    reason="missing_arg_false_positive",
                    claimed_missing_args=claimed_missing_args,
                    actual_args_found=list(actual_args),
                    confidence=0.9
                )

        # 2. Validate undefined variable claims (Issue #4063)
        claimed_undefined_vars = self._extract_claimed_undefined_vars(message)
        if claimed_undefined_vars:
            defined_vars = self._extract_defined_variables(file_diff)
            defined_vars_lower = {var.lower() for var in defined_vars}
            false_positive_vars = [
                var for var in claimed_undefined_vars
                if var.lower() in defined_vars_lower
            ]
            if false_positive_vars:
                return ValidationResult(
                    is_valid=False,
                    reason="undefined_var_false_positive",
                    claimed_missing_args=claimed_undefined_vars,
                    actual_args_found=list(defined_vars),
                    confidence=0.85
                )

        # 3. Validate missing import claims (Issue #4063)
        claimed_missing_imports = self._extract_claimed_missing_imports(message)
        if claimed_missing_imports:
            actual_imports = self._extract_imports_from_diff(file_diff)
            actual_imports_lower = {imp.lower() for imp in actual_imports}
            false_positive_imports = [
                imp for imp in claimed_missing_imports
                if imp.lower() in actual_imports_lower
            ]
            if false_positive_imports:
                return ValidationResult(
                    is_valid=False,
                    reason="missing_import_false_positive",
                    claimed_missing_args=claimed_missing_imports,
                    actual_args_found=list(actual_imports),
                    confidence=0.85
                )

        # Comment appears valid
        return ValidationResult(is_valid=True)

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
        seen: Set[str] = set()
        unique_args = []
        for arg in claimed_args:
            if arg.lower() not in seen:
                seen.add(arg.lower())
                unique_args.append(arg)

        return unique_args

    def _extract_claimed_undefined_vars(self, message: str) -> List[str]:
        """
        Issue #4063: Extract variable names that the comment claims are undefined.

        Args:
            message: The review comment message

        Returns:
            List of variable names claimed to be undefined
        """
        claimed_vars = []

        for pattern in UNDEFINED_VAR_CLAIM_PATTERNS:
            matches = pattern.findall(message)
            claimed_vars.extend(matches)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_vars = []
        for var in claimed_vars:
            if var.lower() not in seen:
                seen.add(var.lower())
                unique_vars.append(var)

        return unique_vars

    def _extract_claimed_missing_imports(self, message: str) -> List[str]:
        """
        Issue #4063: Extract import names that the comment claims are missing.

        Args:
            message: The review comment message

        Returns:
            List of import names claimed to be missing
        """
        claimed_imports = []

        for pattern in MISSING_IMPORT_CLAIM_PATTERNS:
            matches = pattern.findall(message)
            claimed_imports.extend(matches)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_imports = []
        for imp in claimed_imports:
            if imp.lower() not in seen:
                seen.add(imp.lower())
                unique_imports.append(imp)

        return unique_imports

    def _extract_defined_variables(self, diff_content: str) -> Set[str]:
        """
        Issue #4063: Extract all variable definitions from the diff.

        Args:
            diff_content: Diff content to parse

        Returns:
            Set of variable names defined in the diff
        """
        vars_found: Set[str] = set()

        for match in VARIABLE_DEF_PATTERN.finditer(diff_content):
            var_name = match.group(1)
            # Filter out Python keywords
            if var_name not in {
                'False', 'None', 'True', 'and', 'as', 'assert', 'async',
                'await', 'break', 'class', 'continue', 'def', 'del', 'elif',
                'else', 'except', 'finally', 'for', 'from', 'global', 'if',
                'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
                'pass', 'raise', 'return', 'try', 'while', 'with', 'yield',
            }:
                vars_found.add(var_name)

        return vars_found

    def _extract_imports_from_diff(self, diff_content: str) -> Set[str]:
        """
        Issue #4063: Extract all imported names from the diff.

        Args:
            diff_content: Diff content to parse

        Returns:
            Set of imported names found in the diff
        """
        imports_found: Set[str] = set()

        for match in IMPORT_PATTERN.finditer(diff_content):
            import_str = match.group(1)
            # Handle multiple imports: "import a, b, c" or "from x import a, b, c"
            for part in import_str.split(','):
                # Handle "name as alias" format
                name = part.strip().split()[0] if part.strip() else ""
                if name and name not in {'(', ')'}:
                    imports_found.add(name)

        return imports_found

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


# =============================================================================
# Issue #4064: Comment Deduplication
# =============================================================================


@dataclass
class DeduplicationStats:
    """
    Statistics from comment deduplication.

    Attributes:
        total_comments: Total number of comments before deduplication
        unique_comments: Number of unique comments after deduplication
        duplicates_removed: Number of duplicate comments removed
        duplicate_rate: Ratio of duplicates to total
        duplicate_groups: Number of groups of duplicate comments found
    """
    total_comments: int = 0
    unique_comments: int = 0
    duplicates_removed: int = 0
    duplicate_rate: float = 0.0
    duplicate_groups: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_comments": self.total_comments,
            "unique_comments": self.unique_comments,
            "duplicates_removed": self.duplicates_removed,
            "duplicate_rate": self.duplicate_rate,
            "duplicate_groups": self.duplicate_groups,
        }


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity ratio between two text strings.

    Uses SequenceMatcher for efficient string comparison.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def deduplicate_comments(
    comments: List[Dict[str, Any]],
    similarity_threshold: float = DEDUP_SIMILARITY_THRESHOLD,
    trace_id: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], DeduplicationStats]:
    """
    Issue #4064: Deduplicate review comments to reduce noise.

    Deduplication criteria:
    1. Same file + same line = exact duplicate (keep first)
    2. Similar message content (>80% similarity) = semantic duplicate (keep first)

    Blueprint Alignment:
    - NOISE BUDGET: "Maximum 5 comments per review" - deduplication helps stay within budget
    - Section 4.1 "Safe by Design" - Reduces noise and improves signal-to-noise ratio

    Args:
        comments: List of review comment dicts
        similarity_threshold: Minimum similarity ratio to consider as duplicate (default: 0.80)
        trace_id: Optional trace ID for logging

    Returns:
        Tuple of (unique_comments, duplicate_comments, stats)
    """
    trace_id = trace_id or "unknown"
    stats = DeduplicationStats(total_comments=len(comments))

    if not comments:
        return [], [], stats

    unique: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []
    seen_locations: Set[Tuple[Optional[str], Optional[int]]] = set()
    duplicate_group_count = 0

    for comment in comments:
        file_path = comment.get("file")
        line_number = comment.get("line")
        message = comment.get("message", "")

        # 1. Check for exact location duplicate (same file + same line)
        location_key = (file_path, line_number)
        if file_path and line_number and location_key in seen_locations:
            dup_comment = comment.copy()
            dup_comment["_dedup_reason"] = "exact_location_duplicate"
            duplicates.append(dup_comment)
            continue

        # 2. Check for semantic duplicate (similar message content)
        is_semantic_dup = False
        for existing in unique:
            existing_message = existing.get("message", "")
            similarity = _calculate_similarity(message, existing_message)
            if similarity >= similarity_threshold:
                dup_comment = comment.copy()
                dup_comment["_dedup_reason"] = "semantic_duplicate"
                dup_comment["_similarity"] = similarity
                duplicates.append(dup_comment)
                is_semantic_dup = True
                duplicate_group_count += 1
                break

        if is_semantic_dup:
            continue

        # Not a duplicate - add to unique list
        unique.append(comment)
        if file_path and line_number:
            seen_locations.add(location_key)

    # Calculate stats
    stats.unique_comments = len(unique)
    stats.duplicates_removed = len(duplicates)
    stats.duplicate_groups = duplicate_group_count
    if stats.total_comments > 0:
        stats.duplicate_rate = stats.duplicates_removed / stats.total_comments

    # Log deduplication results
    if stats.duplicates_removed > 0:
        logger.info(
            f"[CommentDedup] Removed {stats.duplicates_removed} duplicates "
            f"out of {stats.total_comments} comments (rate: {stats.duplicate_rate:.2%})",
            extra={
                "operation": "comment_dedup",
                "trace_id": trace_id,
                "total_comments": stats.total_comments,
                "unique_comments": stats.unique_comments,
                "duplicates_removed": stats.duplicates_removed,
                "duplicate_rate": stats.duplicate_rate,
                "duplicate_groups": stats.duplicate_groups,
            }
        )

    return unique, duplicates, stats


def validate_and_deduplicate_comments(
    comments: List[Dict[str, Any]],
    diff_content: str,
    trace_id: Optional[str] = None,
    similarity_threshold: float = DEDUP_SIMILARITY_THRESHOLD
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Issue #4063 + #4064: Combined validation and deduplication pipeline.

    This is the recommended entry point for comment post-processing.
    It first validates comments to filter false positives, then deduplicates
    the remaining comments to reduce noise.

    Blueprint Alignment:
    - Section 4.1 "Safe by Design" - Multi-stage filtering
    - NOISE BUDGET: Helps stay within "Maximum 5 comments per review"

    Args:
        comments: List of review comment dicts
        diff_content: The PR diff content
        trace_id: Optional trace ID for logging
        similarity_threshold: Minimum similarity ratio for deduplication

    Returns:
        Tuple of (final_comments, combined_stats_dict)
    """
    trace_id = trace_id or "unknown"

    # Stage 1: Validate comments (filter false positives)
    validated, filtered_fp, validation_stats = validate_review_comments(
        comments=comments,
        diff_content=diff_content,
        trace_id=trace_id
    )

    # Stage 2: Deduplicate validated comments
    unique, duplicates, dedup_stats = deduplicate_comments(
        comments=validated,
        similarity_threshold=similarity_threshold,
        trace_id=trace_id
    )

    # Combine stats
    combined_stats = {
        "validation": validation_stats.to_dict(),
        "deduplication": dedup_stats.to_dict(),
        "pipeline": {
            "input_comments": len(comments),
            "after_validation": len(validated),
            "after_deduplication": len(unique),
            "total_filtered": len(comments) - len(unique),
            "false_positives_filtered": validation_stats.filtered_false_positives,
            "duplicates_removed": dedup_stats.duplicates_removed,
        }
    }

    logger.info(
        f"[CommentPipeline] Processed {len(comments)} -> {len(unique)} comments "
        f"(FP: {validation_stats.filtered_false_positives}, Dup: {dedup_stats.duplicates_removed})",
        extra={
            "operation": "comment_pipeline",
            "trace_id": trace_id,
            **combined_stats["pipeline"],
        }
    )

    return unique, combined_stats
