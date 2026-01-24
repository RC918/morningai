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
        verdict="approve",
        severity="low",
        summary="Code looks good",
        review_comments=[],
        file_paths=["src/main.py"],
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
class NegativePattern:
    """
    A past rejected review suggestion (negative example) from Memory v2.

    EPIC B-18.3: Negative Pattern Retrieval
    These patterns represent suggestions that were rejected by humans,
    helping the reviewer avoid repeating false positives.

    Attributes:
        similarity: Similarity score to current code (0.0 to 1.0)
        suggestion_text: The original suggestion that was rejected
        comment_path: File path where the suggestion was made
        comment_line: Line number where the suggestion was made
        confidence: Confidence of the rejection classification
        importance: Importance score for retrieval priority
        ai_source: AI reviewer that made the suggestion
        repo: Repository where rejection occurred
        pr_number: PR number where rejection occurred
        recorded_at: Unix timestamp when rejection was recorded
    """
    similarity: float
    suggestion_text: str
    comment_path: Optional[str] = None
    comment_line: Optional[int] = None
    confidence: float = 0.0
    importance: float = 0.0
    ai_source: Optional[str] = None
    repo: Optional[str] = None
    pr_number: Optional[int] = None
    recorded_at: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "similarity": self.similarity,
            "suggestion_text": self.suggestion_text,
            "comment_path": self.comment_path,
            "comment_line": self.comment_line,
            "confidence": self.confidence,
            "importance": self.importance,
            "ai_source": self.ai_source,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NegativePattern":
        """Create NegativePattern from dictionary"""
        return cls(
            similarity=data.get("similarity", 0.0),
            suggestion_text=data.get("suggestion_text", ""),
            comment_path=data.get("comment_path"),
            comment_line=data.get("comment_line"),
            confidence=data.get("confidence", 0.0),
            importance=data.get("importance", 0.0),
            ai_source=data.get("ai_source"),
            repo=data.get("repo"),
            pr_number=data.get("pr_number"),
            recorded_at=data.get("recorded_at"),
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
        memory_v2_enabled = settings.enable_memory_v2
        feedback_loop_enabled = settings.enable_review_feedback_loop
        is_enabled = memory_v2_enabled and feedback_loop_enabled

        if not is_enabled:
            logger.info(
                "[ReviewFeedbackLoop] Feature flags check: ENABLE_MEMORY_V2=%s, ENABLE_REVIEW_FEEDBACK_LOOP=%s",
                memory_v2_enabled,
                feedback_loop_enabled,
                extra={
                    "operation": "check_enabled",
                    "enable_memory_v2": memory_v2_enabled,
                    "enable_review_feedback_loop": feedback_loop_enabled,
                    "trace_id": self.trace_id,
                }
            )

        return is_enabled

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

    def get_negative_patterns(
        self,
        diff_snippet: str,
        file_paths: Optional[List[str]] = None,
        limit: Optional[int] = None,
        min_similarity: Optional[float] = None,
    ) -> List[NegativePattern]:
        """
        Retrieve past rejected suggestions (negative patterns) similar to current code.

        EPIC B-18.3: Negative Pattern Retrieval
        These patterns help the reviewer avoid repeating false positives.

        Args:
            diff_snippet: Code diff snippet to search for similar patterns
            file_paths: Optional list of file paths to filter by
            limit: Maximum number of patterns to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of NegativePattern objects sorted by similarity
        """
        if not self._enabled:
            logger.debug("[ReviewFeedbackLoop] Feedback loop disabled")
            return []

        if not settings.enable_negative_pattern_retrieval:
            logger.debug("[ReviewFeedbackLoop] Negative pattern retrieval disabled")
            return []

        try:
            from memory.memory_integration import search_negative_patterns

            results = search_negative_patterns(
                query=diff_snippet,
                file_paths=file_paths,
                limit=limit,
                min_similarity=min_similarity,
                trace_id=self.trace_id,
            )

            patterns = [NegativePattern.from_dict(r) for r in results]

            if patterns:
                logger.info(
                    "[ReviewFeedbackLoop] Retrieved %d negative patterns",
                    len(patterns),
                    extra={
                        "negative_pattern_count": len(patterns),
                        "trace_id": self.trace_id,
                        "operation": "get_negative_patterns",
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
                "[ReviewFeedbackLoop] Failed to retrieve negative patterns: %s",
                e,
                extra={
                    "trace_id": self.trace_id,
                    "operation": "get_negative_patterns",
                }
            )
            return []

    def enhance_review_context(
        self,
        diff_snippet: str,
        file_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Enhance review context with past patterns (positive and negative).

        EPIC B-13: Retrieves positive patterns from past reviews.
        EPIC B-18.3: Also retrieves negative patterns (rejected suggestions).

        This method retrieves relevant past patterns and formats them
        for inclusion in the review prompt.

        Args:
            diff_snippet: Code diff snippet to search for similar patterns
            file_paths: Optional list of file paths to filter by

        Returns:
            Dict with:
            - has_patterns: Whether any patterns were found
            - pattern_count: Number of positive patterns found
            - patterns: List of positive pattern summaries
            - has_negative_patterns: Whether any negative patterns were found
            - negative_pattern_count: Number of negative patterns found
            - negative_patterns: List of negative pattern summaries
            - context_text: Formatted text for inclusion in prompt
        """
        # Retrieve positive patterns (B-13)
        patterns = self.get_relevant_patterns(
            diff_snippet=diff_snippet,
            file_paths=file_paths,
        )

        # Retrieve negative patterns (B-18.3)
        negative_patterns = self.get_negative_patterns(
            diff_snippet=diff_snippet,
            file_paths=file_paths,
        )

        if not patterns and not negative_patterns:
            return {
                "has_patterns": False,
                "pattern_count": 0,
                "patterns": [],
                "has_negative_patterns": False,
                "negative_pattern_count": 0,
                "negative_patterns": [],
                "context_text": "",
            }

        context_lines = []

        # Format positive patterns (B-13)
        pattern_summaries = []
        if patterns:
            for p in patterns:
                pattern_summaries.append({
                    "similarity": p.similarity,
                    "verdict": p.verdict,
                    "severity": p.severity,
                    "summary": p.summary,
                    "blocker_count": p.blocker_count,
                })

            context_lines.extend([
                "## Past Review Patterns (B-13 Feedback Loop)",
                "",
                f"Found {len(patterns)} similar past reviews:",
                "",
            ])

            for i, p in enumerate(patterns, 1):
                context_lines.append(
                    f"{i}. [{p.verdict.upper()}] (similarity: {p.similarity:.2f}) "
                    f"{p.summary}"
                )
                if p.blocker_count > 0:
                    context_lines.append(f"   - {p.blocker_count} blocking issues found")

            context_lines.extend([
                "",
                "Consider these past patterns when reviewing similar code.",
                "",
            ])

        # Format negative patterns (B-18.3)
        negative_pattern_summaries = []
        if negative_patterns:
            for np in negative_patterns:
                negative_pattern_summaries.append({
                    "similarity": np.similarity,
                    "suggestion_text": np.suggestion_text,
                    "comment_path": np.comment_path,
                    "confidence": np.confidence,
                    "ai_source": np.ai_source,
                })

            context_lines.extend([
                "## Patterns to AVOID (B-18 Past False Positives)",
                "",
                "IMPORTANT: The following suggestions have been REJECTED by humans in the past.",
                "DO NOT repeat these suggestions for similar code patterns:",
                "",
            ])

            for i, np in enumerate(negative_patterns, 1):
                # Truncate suggestion text for prompt
                suggestion_preview = np.suggestion_text[:200] if np.suggestion_text else "N/A"
                if len(np.suggestion_text) > 200:
                    suggestion_preview += "..."

                context_lines.append(
                    f"{i}. [REJECTED] (similarity: {np.similarity:.2f})"
                )
                context_lines.append(f"   Suggestion: \"{suggestion_preview}\"")
                if np.comment_path:
                    context_lines.append(f"   File: {np.comment_path}")
                if np.ai_source:
                    context_lines.append(f"   Source: {np.ai_source}")
                context_lines.append("")

            context_lines.append(
                "Avoid making similar suggestions - they were marked as false positives."
            )

        return {
            "has_patterns": len(patterns) > 0,
            "pattern_count": len(patterns),
            "patterns": pattern_summaries,
            "has_negative_patterns": len(negative_patterns) > 0,
            "negative_pattern_count": len(negative_patterns),
            "negative_patterns": negative_pattern_summaries,
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
