"""
GitHub Comment Parser - D-5 Phase 1 Implementation

EPIC D Stage 3: D-5 Review Feedback Handler (General Fixes)
Issue: D-5 Phase 1 - GitHub Comment Parser

This module provides:
1. GitHubCommentParser class for parsing GitHub review comments
2. Extraction of file_path, line_number, and comment_body from inline comments
3. Conversion of review comments to fix tasks for GeneralCoder

Blueprint Alignment:
- This parser belongs to the Infrastructure Layer (webhooks/parsers/)
- It converts external "dirty" GitHub payloads into clean internal formats
- Coder/Reviewer Agents receive already-parsed data structures

Blueprint Reference: EPIC D-5 (Review Feedback Handler)
Dependency: EPIC B (Reviewer Agent), EPIC D-1b (GeneralCoder)

Usage:
    from webhooks.parsers import (
        GitHubCommentParser,
        ParsedReviewComment,
        parse_review_comments,
    )

    parser = GitHubCommentParser(trace_id="abc123")

    # Parse GitHub review comments
    parsed = parser.parse_github_review(review_data)

    # Convert to fix tasks for GeneralCoder
    fix_tasks = parser.to_fix_tasks(parsed)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CommentType(Enum):
    """Type of review comment."""
    INLINE = "inline"  # Comment on specific line(s)
    FILE = "file"  # Comment on entire file
    GENERAL = "general"  # General PR comment (not file-specific)


class CommentSeverity(Enum):
    """Severity level inferred from comment content."""
    BLOCKER = "blocker"  # Must fix before merge
    SUGGESTION = "suggestion"  # Should fix, but not blocking
    NIT = "nit"  # Nice to have, optional
    QUESTION = "question"  # Clarification needed
    PRAISE = "praise"  # Positive feedback (no action needed)


@dataclass
class ParsedReviewComment:
    """
    A parsed review comment with extracted metadata.

    Attributes:
        comment_id: Unique identifier for the comment
        comment_type: Type of comment (inline, file, general)
        file_path: Path to the file (None for general comments)
        line_number: Line number in the file (None for file/general comments)
        line_range: Tuple of (start_line, end_line) for multi-line comments
        body: The comment text
        severity: Inferred severity level
        author: Comment author username
        created_at: When the comment was created
        in_reply_to: ID of parent comment if this is a reply
        suggestion_code: Extracted code suggestion if present
        is_resolved: Whether the comment thread is resolved
    """
    comment_id: str
    comment_type: CommentType
    body: str
    severity: CommentSeverity = CommentSeverity.SUGGESTION
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    line_range: Optional[tuple] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    in_reply_to: Optional[str] = None
    suggestion_code: Optional[str] = None
    is_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "comment_id": self.comment_id,
            "comment_type": self.comment_type.value,
            "body": self.body,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_range": self.line_range,
            "author": self.author,
            "created_at": self.created_at,
            "in_reply_to": self.in_reply_to,
            "suggestion_code": self.suggestion_code,
            "is_resolved": self.is_resolved,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedReviewComment":
        """Create ParsedReviewComment from dictionary."""
        return cls(
            comment_id=data.get("comment_id", ""),
            comment_type=CommentType(data.get("comment_type", "general")),
            body=data.get("body", ""),
            severity=CommentSeverity(data.get("severity", "suggestion")),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            line_range=tuple(data["line_range"]) if data.get("line_range") else None,
            author=data.get("author"),
            created_at=data.get("created_at"),
            in_reply_to=data.get("in_reply_to"),
            suggestion_code=data.get("suggestion_code"),
            is_resolved=data.get("is_resolved", False),
        )


@dataclass
class FixTask:
    """
    A fix task derived from review comments for GeneralCoder.

    Attributes:
        task_id: Unique identifier for the task
        file_path: Path to the file to fix
        review_comment: The review comment describing the issue
        severity: Severity level (maps to GeneralCoder severity)
        line_number: Optional line number for targeted fix
        suggestion_code: Optional suggested code from reviewer
        source_comments: List of comment IDs that contributed to this task
    """
    task_id: str
    file_path: str
    review_comment: str
    severity: str = "low"
    line_number: Optional[int] = None
    suggestion_code: Optional[str] = None
    source_comments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for GeneralCoder input."""
        return {
            "task_id": self.task_id,
            "file_path": self.file_path,
            "review_comment": self.review_comment,
            "severity": self.severity,
            "line_number": self.line_number,
            "suggestion_code": self.suggestion_code,
            "source_comments": self.source_comments,
        }


@dataclass
class ParserStats:
    """Statistics for the parser."""
    total_comments: int = 0
    inline_comments: int = 0
    file_comments: int = 0
    general_comments: int = 0
    actionable_comments: int = 0
    suggestions_extracted: int = 0
    fix_tasks_created: int = 0


class GitHubCommentParser:
    """
    Parses GitHub review comments and converts them to fix tasks.

    EPIC D-5 Phase 1: GitHub Comment Parser
    Blueprint: Infrastructure Layer adapter for GitHub payloads.

    This class provides:
    1. parse_github_review(): Parse raw GitHub review data
    2. parse_inline_comment(): Parse a single inline comment
    3. to_fix_tasks(): Convert parsed comments to fix tasks
    4. infer_severity(): Infer severity from comment content

    The parser enables the Reviewer -> Coder feedback loop by
    extracting actionable information from review comments.
    """

    # Patterns for severity inference
    BLOCKER_PATTERNS = [
        r"\b(must|required|critical|blocker|blocking|security|vulnerability)\b",
        r"\b(do not merge|don't merge|cannot merge)\b",
        r"\b(breaks?|broken|crash|fail)\b",
    ]
    SUGGESTION_PATTERNS = [
        r"\b(should|consider|recommend|suggest|better|improve)\b",
        r"\b(please|could you|would you)\b",
    ]
    NIT_PATTERNS = [
        r"\b(nit|nitpick|minor|optional|style|formatting)\b",
        r"\b(nice to have|low priority)\b",
    ]
    QUESTION_PATTERNS = [
        r"\?$",
        r"\b(why|what|how|when|where|which|who)\b.*\?",
        r"\b(curious|wondering|confused|unclear)\b",
    ]
    PRAISE_PATTERNS = [
        r"\b(good|great|nice|excellent|well done|lgtm|looks good)\b",
        r"\b(thank|thanks|appreciate)\b",
        r"^\s*\+1\s*$",
    ]

    # Pattern for GitHub suggestion blocks
    SUGGESTION_BLOCK_PATTERN = re.compile(
        r"```suggestion\s*\n(.*?)\n```",
        re.DOTALL | re.IGNORECASE
    )

    def __init__(self, trace_id: Optional[str] = None):
        """
        Initialize the GitHubCommentParser.

        Args:
            trace_id: Optional workflow trace ID for correlation
        """
        self.trace_id = trace_id
        self.stats = ParserStats()

    def parse_github_review(
        self,
        review_data: Dict[str, Any],
        include_resolved: bool = False,
    ) -> List[ParsedReviewComment]:
        """
        Parse a GitHub review response into structured comments.

        Args:
            review_data: Raw GitHub review data (from API or webhook)
            include_resolved: Whether to include resolved comment threads

        Returns:
            List of ParsedReviewComment objects

        Event Codes (greppable):
            [GITHUB_COMMENT_PARSE_START] - Starting to parse review
            [GITHUB_COMMENT_PARSE_SUCCESS] - Successfully parsed comments
            [GITHUB_COMMENT_PARSE_FAIL] - Failed to parse review
        """
        logger.info(
            "[GITHUB_COMMENT_PARSE_START] Parsing GitHub review",
            extra={
                "trace_id": self.trace_id,
                "operation": "parse_github_review",
            }
        )

        parsed_comments: List[ParsedReviewComment] = []

        try:
            # Handle different GitHub API response formats
            comments = self._extract_comments_from_review(review_data)

            for comment_data in comments:
                parsed = self.parse_inline_comment(comment_data)
                if parsed:
                    # Skip resolved comments unless requested
                    if parsed.is_resolved and not include_resolved:
                        continue
                    parsed_comments.append(parsed)
                    self.stats.total_comments += 1

                    # Update type-specific stats
                    if parsed.comment_type == CommentType.INLINE:
                        self.stats.inline_comments += 1
                    elif parsed.comment_type == CommentType.FILE:
                        self.stats.file_comments += 1
                    else:
                        self.stats.general_comments += 1

                    # Track actionable comments
                    if parsed.severity not in (CommentSeverity.PRAISE, CommentSeverity.QUESTION):
                        self.stats.actionable_comments += 1

                    if parsed.suggestion_code:
                        self.stats.suggestions_extracted += 1

            logger.info(
                "[GITHUB_COMMENT_PARSE_SUCCESS] Parsed %d comments (%d actionable)",
                len(parsed_comments),
                self.stats.actionable_comments,
                extra={
                    "trace_id": self.trace_id,
                    "operation": "parse_github_review",
                    "total_comments": len(parsed_comments),
                    "actionable_comments": self.stats.actionable_comments,
                }
            )

            return parsed_comments

        except Exception as e:
            logger.error(
                "[GITHUB_COMMENT_PARSE_FAIL] Failed to parse review: %s",
                str(e),
                extra={
                    "trace_id": self.trace_id,
                    "operation": "parse_github_review",
                    "error": str(e),
                },
                exc_info=True,
            )
            return []

    def _extract_comments_from_review(
        self,
        review_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract comment list from various GitHub API response formats.

        Handles:
        - Pull request review comments API response
        - Review event webhook payload
        - Single review with comments array

        Args:
            review_data: Raw GitHub API/webhook data

        Returns:
            List of comment dictionaries
        """
        # Direct comments array
        if isinstance(review_data, list):
            return review_data

        # Review with comments array
        if "comments" in review_data:
            return review_data["comments"]

        # Single comment object
        if "id" in review_data and "body" in review_data:
            return [review_data]

        # Webhook payload with review object
        if "review" in review_data:
            review = review_data["review"]
            if "comments" in review:
                return review["comments"]
            # Single review body (general comment)
            if "body" in review:
                return [{
                    "id": review.get("id"),
                    "body": review.get("body"),
                    "user": review.get("user"),
                    "submitted_at": review.get("submitted_at"),
                }]

        # Pull request review comments endpoint
        if "data" in review_data:
            return review_data["data"]

        logger.warning(
            "[GITHUB_COMMENT_PARSE] Unknown review data format",
            extra={"trace_id": self.trace_id, "keys": list(review_data.keys())}
        )
        return []

    def parse_inline_comment(
        self,
        comment_data: Dict[str, Any]
    ) -> Optional[ParsedReviewComment]:
        """
        Parse a single GitHub inline comment.

        Args:
            comment_data: Raw comment data from GitHub API

        Returns:
            ParsedReviewComment or None if parsing fails
        """
        try:
            comment_id = str(comment_data.get("id", ""))
            body = comment_data.get("body", "")

            if not body:
                return None

            # Determine comment type
            file_path = comment_data.get("path")
            line_number = comment_data.get("line") or comment_data.get("original_line")
            start_line = comment_data.get("start_line")

            if file_path and line_number:
                comment_type = CommentType.INLINE
            elif file_path:
                comment_type = CommentType.FILE
            else:
                comment_type = CommentType.GENERAL

            # Build line range if multi-line
            line_range = None
            if start_line and line_number and start_line != line_number:
                line_range = (start_line, line_number)

            # Extract suggestion code if present
            suggestion_code = self._extract_suggestion_code(body)

            # Infer severity from content
            severity = self.infer_severity(body)

            # Get author info
            user = comment_data.get("user", {})
            author = user.get("login") if isinstance(user, dict) else None

            # Check if resolved (GitHub uses different fields)
            is_resolved = (
                comment_data.get("resolved", False) or
                comment_data.get("state") == "resolved"
            )

            return ParsedReviewComment(
                comment_id=comment_id,
                comment_type=comment_type,
                body=body,
                severity=severity,
                file_path=file_path,
                line_number=line_number,
                line_range=line_range,
                author=author,
                created_at=comment_data.get("created_at") or comment_data.get("submitted_at"),
                in_reply_to=str(comment_data.get("in_reply_to_id", "")) or None,
                suggestion_code=suggestion_code,
                is_resolved=is_resolved,
            )

        except Exception as e:
            logger.warning(
                "[GITHUB_COMMENT_PARSE] Failed to parse comment: %s",
                str(e),
                extra={"trace_id": self.trace_id}
            )
            return None

    def _extract_suggestion_code(self, body: str) -> Optional[str]:
        """
        Extract code from GitHub suggestion blocks.

        GitHub suggestion format:
        ```suggestion
        suggested code here
        ```

        Args:
            body: Comment body text

        Returns:
            Extracted suggestion code or None
        """
        match = self.SUGGESTION_BLOCK_PATTERN.search(body)
        if match:
            return match.group(1).strip()
        return None

    def infer_severity(self, body: str) -> CommentSeverity:
        """
        Infer severity level from comment content.

        Uses pattern matching to categorize comments by severity.
        Order of precedence: blocker > suggestion > nit > question > praise

        Args:
            body: Comment body text

        Returns:
            Inferred CommentSeverity
        """
        body_lower = body.lower()

        # Check patterns in order of precedence
        for pattern in self.BLOCKER_PATTERNS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return CommentSeverity.BLOCKER

        for pattern in self.SUGGESTION_PATTERNS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return CommentSeverity.SUGGESTION

        for pattern in self.NIT_PATTERNS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return CommentSeverity.NIT

        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return CommentSeverity.QUESTION

        for pattern in self.PRAISE_PATTERNS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                return CommentSeverity.PRAISE

        # Default to suggestion
        return CommentSeverity.SUGGESTION

    def to_fix_tasks(
        self,
        comments: List[ParsedReviewComment],
        group_by_file: bool = True,
    ) -> List[FixTask]:
        """
        Convert parsed comments to fix tasks for GeneralCoder.

        Args:
            comments: List of parsed review comments
            group_by_file: Whether to group comments by file into single tasks

        Returns:
            List of FixTask objects

        Event Codes (greppable):
            [FIX_TASK_CREATED] - Created fix task from comments
        """
        fix_tasks: List[FixTask] = []

        # Filter to actionable comments only
        actionable = [
            c for c in comments
            if c.severity not in (CommentSeverity.PRAISE, CommentSeverity.QUESTION)
            and c.file_path  # Must have a file path
            and not c.is_resolved  # Skip resolved
        ]

        if not actionable:
            logger.info(
                "[FIX_TASK_CREATED] No actionable comments to convert",
                extra={"trace_id": self.trace_id}
            )
            return []

        if group_by_file:
            # Group comments by file
            by_file: Dict[str, List[ParsedReviewComment]] = {}
            for comment in actionable:
                file_path = comment.file_path or ""
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(comment)

            # Create one task per file
            for file_path, file_comments in by_file.items():
                task = self._create_fix_task(file_path, file_comments)
                fix_tasks.append(task)
                self.stats.fix_tasks_created += 1
        else:
            # Create one task per comment
            for comment in actionable:
                task = self._create_fix_task(
                    comment.file_path or "",
                    [comment]
                )
                fix_tasks.append(task)
                self.stats.fix_tasks_created += 1

        logger.info(
            "[FIX_TASK_CREATED] Created %d fix tasks from %d comments",
            len(fix_tasks),
            len(actionable),
            extra={
                "trace_id": self.trace_id,
                "operation": "to_fix_tasks",
                "task_count": len(fix_tasks),
                "comment_count": len(actionable),
            }
        )

        return fix_tasks

    def _create_fix_task(
        self,
        file_path: str,
        comments: List[ParsedReviewComment]
    ) -> FixTask:
        """
        Create a single fix task from one or more comments.

        Args:
            file_path: Path to the file
            comments: List of comments for this file

        Returns:
            FixTask object
        """
        # Generate task ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        task_id = f"d5-fix-{timestamp}-{hash(file_path) % 10000:04d}"

        # Combine comment bodies into review_comment
        comment_texts = []
        for c in comments:
            prefix = ""
            if c.line_number:
                prefix = f"[Line {c.line_number}] "
            elif c.line_range:
                prefix = f"[Lines {c.line_range[0]}-{c.line_range[1]}] "
            comment_texts.append(f"{prefix}{c.body}")

        review_comment = "\n\n".join(comment_texts)

        # Determine overall severity (highest wins)
        severity_order = [
            CommentSeverity.BLOCKER,
            CommentSeverity.SUGGESTION,
            CommentSeverity.NIT,
        ]
        overall_severity = CommentSeverity.NIT
        for sev in severity_order:
            if any(c.severity == sev for c in comments):
                overall_severity = sev
                break

        # Map to GeneralCoder severity
        severity_map = {
            CommentSeverity.BLOCKER: "high",
            CommentSeverity.SUGGESTION: "medium",
            CommentSeverity.NIT: "low",
        }
        coder_severity = severity_map.get(overall_severity, "low")

        # Get first line number if available
        line_number = None
        for c in comments:
            if c.line_number:
                line_number = c.line_number
                break

        # Get first suggestion code if available
        suggestion_code = None
        for c in comments:
            if c.suggestion_code:
                suggestion_code = c.suggestion_code
                break

        return FixTask(
            task_id=task_id,
            file_path=file_path,
            review_comment=review_comment,
            severity=coder_severity,
            line_number=line_number,
            suggestion_code=suggestion_code,
            source_comments=[c.comment_id for c in comments],
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics."""
        return {
            "total_comments": self.stats.total_comments,
            "inline_comments": self.stats.inline_comments,
            "file_comments": self.stats.file_comments,
            "general_comments": self.stats.general_comments,
            "actionable_comments": self.stats.actionable_comments,
            "suggestions_extracted": self.stats.suggestions_extracted,
            "fix_tasks_created": self.stats.fix_tasks_created,
        }


def parse_review_comments(
    review_data: Dict[str, Any],
    trace_id: Optional[str] = None,
    include_resolved: bool = False,
) -> List[ParsedReviewComment]:
    """
    Convenience function to parse GitHub review comments.

    Args:
        review_data: Raw GitHub review data
        trace_id: Optional trace ID for correlation
        include_resolved: Whether to include resolved threads

    Returns:
        List of ParsedReviewComment objects
    """
    parser = GitHubCommentParser(trace_id=trace_id)
    return parser.parse_github_review(review_data, include_resolved=include_resolved)


def get_github_comment_parser(trace_id: Optional[str] = None) -> GitHubCommentParser:
    """
    Factory function to get a GitHubCommentParser instance.

    Args:
        trace_id: Optional workflow trace ID

    Returns:
        GitHubCommentParser instance
    """
    return GitHubCommentParser(trace_id=trace_id)


# Backward compatibility aliases (deprecated, use GitHubCommentParser)
ReviewCommentParser = GitHubCommentParser
get_review_comment_parser = get_github_comment_parser
