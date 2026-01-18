"""
Webhook Parsers - Infrastructure Layer Adapters

This module provides parsers for converting external webhook payloads
into standardized internal data structures.

D-5: GitHub Comment Parser (Review Feedback Handler Phase 1)

Blueprint Alignment:
- Parsers belong to the Infrastructure Layer (not Intelligence Layer)
- They convert external "dirty" data into clean internal formats
- Coder/Reviewer Agents receive already-parsed data structures

Usage:
    from webhooks.parsers.github_comment_parser import (
        GitHubCommentParser,
        ParsedReviewComment,
        FixTask,
        parse_review_comments,
    )
"""

# Use relative imports to avoid triggering parent webhooks module
from .github_comment_parser import (
    GitHubCommentParser,
    ParsedReviewComment,
    FixTask,
    CommentType,
    CommentSeverity,
    ParserStats,
    parse_review_comments,
    get_github_comment_parser,
)

__all__ = [
    # D-5: GitHub Comment Parser
    "GitHubCommentParser",
    "ParsedReviewComment",
    "FixTask",
    "CommentType",
    "CommentSeverity",
    "ParserStats",
    "parse_review_comments",
    "get_github_comment_parser",
]
