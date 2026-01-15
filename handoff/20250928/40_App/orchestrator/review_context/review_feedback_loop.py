"""
Review Feedback Loop - EPIC B Phase B-13 Implementation

Real-time Feedback Loop for Reviewer Agent.

This module provides:
1. ReviewFeedbackLoop class for orchestrating feedback collection and retrieval
2. Integration with Memory v2 for storing review outcomes
3. Pattern retrieval for informing future reviews

Blueprint Reference: EPIC B-13 (Real-time Feedback Loop)
Dependency: EPIC G Memory v2 (completed)

Usage:
    from review_context.review_feedback_loop import ReviewFeedbackLoop

    loop = ReviewFeedbackLoop(trace_id="abc123")

    # After review: save feedback
    loop.save_feedback(
        pr_number=123,
        repo="owner/repo",
        review_outcome=outcome,
        diff_snippet=diff
    )

    # Before review: retrieve patterns
    patterns = loop.get_relevant_patterns(
        diff_snippet=diff,
        file_paths=["src/main.py"]
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from common.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ReviewPattern:
    """
    A past review pattern retrieved from Memory v2.

    Attributes:
        similarity: Similarity score (0.0 to 1.0)
        verdict: Past review verdict
        severity: Past review severity
        summary: Past review summary
        comments: Past review comments
        file_paths: Files that were reviewed
        pr_number: Original PR number
        repo: Original repository
    """
    similarity: float
    verdict: str
    severity: str
    summary: str
    comments: List[Dict[str, Any]] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    pr_number: Optional[int] = None
    repo: Optional[str] = None
    blocker_count: int = 0
    saved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "similarity": self.similarity,
            "verdict": self.verdict,
            "severity": self.severity,
            "summary": self.summary,
            "comments": self.comments,
            "file_paths": self.file_paths,
            "pr_number": self.pr_number,
            "repo": self.repo,
            "blocker_count": self.blocker_count,
            "saved_at": self.saved_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewPattern":
        """Create ReviewPattern from dictionary"""
        return cls(
            similarity=data.get("similarity", 0.0),
            verdict=data.get("verdict", "unknown"),
            severity=data.get("severity", "low"),
            summary=data.get("summary", ""),
            comments=data.get("comments", []),
            file_paths=data.get("file_paths", []),
            pr_number=data.get("pr_number"),
            repo=data.get("repo"),
            blocker_count=data.get("blocker_count", 0),
            saved_at=data.get("saved_at"),
        )


@dataclass
class FeedbackLoopStats:
    """Statistics for the feedback loop"""
    patterns_retrieved: int = 0
    feedbacks_saved: int = 0
    avg_similarity: float = 0.0
    last_save_at: Optional[str] = None
    last_retrieval_at: Optional[str] = None


class ReviewFeedbackLoop:
    """
    Orchestrates the real-time feedback loop for the Reviewer Agent.

    EPIC B Phase B-13: Real-time Feedback Loop
    Blueprint: Reviewer feedback stored in Memory v2 for accumulated experience.

    This class provides:
    1. save_feedback(): Store review outcomes in Knowledge Base
    2. get_relevant_patterns(): Retrieve past patterns for current review
    3. enhance_review_context(): Add past patterns to review context

    The feedback loop enables the system to learn from past reviews
    and provide more consistent and informed suggestions.
    """

    def __init__(self, trace_id: Optional[str] = None):
        """
        Initialize the ReviewFeedbackLoop.

        Args:
            trace_id: Optional workflow trace ID for correlation
        """
        self.trace_id = trace_id
        self.stats = FeedbackLoopStats()
        self._enabled = self._check_enabled()

    def _check_enabled(self) -> bool:
        """Check if the feedback loop is enabled via feature flags."""
        return (
            settings.enable_memory_v2 and
            settings.enable_review_feedback_loop
        )

    @property
    def is_enabled(self) -> bool:
        """Check if the feedback loop is enabled."""
        return self._enabled

    def save_feedback(
        self,
        pr_number: int,
        repo: str,
        verdict: str,
        severity: str,
        summary: str,
        review_comments: List[Dict[str, Any]],
        file_paths: List[str],
        diff_snippet: Optional[str] = None,
        blocker_count: int = 0,
    ) -> bool:
        """
        Save review feedback to Memory v2 Knowledge Base.

        Args:
            pr_number: Pull request number
            repo: Repository name (owner/repo format)
            verdict: Review verdict (approve, request_changes, comment, blocked, unknown)
            severity: Review severity (low, medium, high, critical)
            summary: One-line review summary
            review_comments: List of review comment dicts
            file_paths: List of files reviewed
            diff_snippet: Optional code diff snippet for similarity search
            blocker_count: Number of blocking issues found

        Returns:
            True if saved successfully, False otherwise
        """
        if not self._enabled:
            logger.debug("[ReviewFeedbackLoop] Feedback loop disabled")
            return False

        try:
            from memory.memory_integration import save_review_feedback

            success = save_review_feedback(
                pr_number=pr_number,
                repo=repo,
                verdict=verdict,
                severity=severity,
                summary=summary,
                review_comments=review_comments,
                file_paths=file_paths,
                trace_id=self.trace_id,
                diff_snippet=diff_snippet,
                blocker_count=blocker_count,
            )

            if success:
                self.stats.feedbacks_saved += 1
                self.stats.last_save_at = datetime.now(timezone.utc).isoformat()
                logger.info(
                    "[ReviewFeedbackLoop] Saved feedback for PR #%d",
                    pr_number,
                    extra={
                        "pr_number": pr_number,
                        "repo": repo,
                        "verdict": verdict,
                        "trace_id": self.trace_id,
                        "operation": "save_feedback",
                    }
                )

            return success

        except ImportError as e:
            logger.warning(
                "[ReviewFeedbackLoop] Memory integration not available: %s",
                e
            )
            return False
        except Exception as e:
            logger.warning(
                "[ReviewFeedbackLoop] Failed to save feedback: %s",
                e,
                extra={
                    "pr_number": pr_number,
                    "repo": repo,
                    "trace_id": self.trace_id,
                    "operation": "save_feedback",
                }
            )
            return False

    def get_relevant_patterns(
        self,
        diff_snippet: str,
        file_paths: Optional[List[str]] = None,
        limit: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> List[ReviewPattern]:
        """
        Retrieve past review patterns similar to the current code.

        Args:
            diff_snippet: Code diff snippet to search for similar patterns
            file_paths: Optional list of file paths to filter by
            limit: Maximum number of patterns to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of ReviewPattern objects sorted by similarity
        """
        if not self._enabled:
            logger.debug("[ReviewFeedbackLoop] Feedback loop disabled")
            return []

        if not settings.enable_review_pattern_retrieval:
            logger.debug("[ReviewFeedbackLoop] Pattern retrieval disabled")
            return []

        try:
            from memory.memory_integration import search_review_patterns

            results = search_review_patterns(
                query=diff_snippet,
                file_paths=file_paths,
                limit=limit,
                min_similarity=min_similarity,
                trace_id=self.trace_id,
            )

            patterns = [ReviewPattern.from_dict(r) for r in results]

            if patterns:
                self.stats.patterns_retrieved += len(patterns)
                self.stats.last_retrieval_at = datetime.now(timezone.utc).isoformat()
                self.stats.avg_similarity = sum(
                    p.similarity for p in patterns
                ) / len(patterns)

                logger.info(
                    "[ReviewFeedbackLoop] Retrieved %d patterns (avg similarity: %.2f)",
                    len(patterns),
                    self.stats.avg_similarity,
                    extra={
                        "pattern_count": len(patterns),
                        "avg_similarity": self.stats.avg_similarity,
                        "trace_id": self.trace_id,
                        "operation": "get_relevant_patterns",
                    }
                )

            return patterns

        except ImportError as e:
            logger.warning(
                "[ReviewFeedbackLoop] Memory integration not available: %s",
                e
            )
            return []
        except Exception as e:
            logger.warning(
                "[ReviewFeedbackLoop] Failed to retrieve patterns: %s",
                e,
                extra={
                    "trace_id": self.trace_id,
                    "operation": "get_relevant_patterns",
                }
            )
            return []

    def enhance_review_context(
        self,
        diff_snippet: str,
        file_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Enhance review context with past patterns.

        This method retrieves relevant past patterns and formats them
        for inclusion in the review prompt.

        Args:
            diff_snippet: Code diff snippet to search for similar patterns
            file_paths: Optional list of file paths to filter by

        Returns:
            Dict with:
            - has_patterns: Whether any patterns were found
            - pattern_count: Number of patterns found
            - patterns: List of pattern summaries
            - context_text: Formatted text for inclusion in prompt
        """
        patterns = self.get_relevant_patterns(
            diff_snippet=diff_snippet,
            file_paths=file_paths,
        )

        if not patterns:
            return {
                "has_patterns": False,
                "pattern_count": 0,
                "patterns": [],
                "context_text": "",
            }

        pattern_summaries = []
        for p in patterns:
            pattern_summaries.append({
                "similarity": p.similarity,
                "verdict": p.verdict,
                "severity": p.severity,
                "summary": p.summary,
                "blocker_count": p.blocker_count,
            })

        context_lines = [
            "## Past Review Patterns (B-13 Feedback Loop)",
            "",
            f"Found {len(patterns)} similar past reviews:",
            "",
        ]

        for i, p in enumerate(patterns, 1):
            context_lines.append(
                f"{i}. [{p.verdict.upper()}] (similarity: {p.similarity:.2f}) "
                f"{p.summary}"
            )
            if p.blocker_count > 0:
                context_lines.append(f"   - {p.blocker_count} blocking issues found")

        context_lines.append("")
        context_lines.append(
            "Consider these past patterns when reviewing similar code."
        )

        return {
            "has_patterns": True,
            "pattern_count": len(patterns),
            "patterns": pattern_summaries,
            "context_text": "\n".join(context_lines),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback loop statistics."""
        return {
            "enabled": self._enabled,
            "patterns_retrieved": self.stats.patterns_retrieved,
            "feedbacks_saved": self.stats.feedbacks_saved,
            "avg_similarity": self.stats.avg_similarity,
            "last_save_at": self.stats.last_save_at,
            "last_retrieval_at": self.stats.last_retrieval_at,
        }


def get_feedback_loop(trace_id: Optional[str] = None) -> ReviewFeedbackLoop:
    """
    Factory function to get a ReviewFeedbackLoop instance.

    Args:
        trace_id: Optional workflow trace ID

    Returns:
        ReviewFeedbackLoop instance
    """
    return ReviewFeedbackLoop(trace_id=trace_id)
