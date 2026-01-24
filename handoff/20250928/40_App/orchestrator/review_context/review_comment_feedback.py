"""
Review Comment Feedback - EPIC B-18 Phase 1 Implementation

EPIC B-18: Review Comment Feedback (Human-in-the-Loop Learning)
Issue: B-18.1 - Feedback Signal Capture

This module provides:
1. FeedbackClassification enum for categorizing human feedback signals
2. classify_feedback() function for signal detection and classification
3. ReviewCommentFeedback dataclass for storing feedback data

Blueprint Alignment:
- This module enables the system to learn from human feedback on AI review comments
- Negative examples are stored in Memory v2 Knowledge Base to prevent repetition
- Supports the "accumulated experience" principle from Blueprint Section 3.3

Signal Detection Rules (from EPIC B-18 spec):
| Signal | Classification | Confidence |
|--------|---------------|------------|
| Comment resolved + code changed | ACCEPTED | High |
| Comment resolved + no code change | DISMISSED | Medium |
| Thumbs down reaction | REJECTED | High |
| Reply contains "false positive" | REJECTED | High |
| Reply contains "good catch" | ACCEPTED | High |
| Reply contains "?" or "what do you mean" | CLARIFIED | Medium |
| No response after 24h | UNKNOWN | Low |

Usage:
    from review_context.review_comment_feedback import (
        FeedbackClassification,
        ReviewCommentFeedback,
        classify_feedback,
        classify_reply_pattern,
    )

    # Classify feedback from a resolved thread
    classification = classify_feedback(
        action="resolved",
        code_changed=True,
        reply_text=None,
    )
    # Returns: (FeedbackClassification.ACCEPTED, 0.9)

    # Classify feedback from a reply
    classification = classify_reply_pattern("This is a false positive")
    # Returns: (FeedbackClassification.REJECTED, 0.85)
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from common.config.settings import settings

logger = logging.getLogger(__name__)


class FeedbackClassification(Enum):
    """
    Classification of human feedback on AI review comments.

    EPIC B-18: These classifications determine how feedback is stored
    and used to improve future reviews.
    """
    ACCEPTED = "accepted"      # Human agreed with the suggestion
    REJECTED = "rejected"      # Human explicitly rejected (false positive)
    DISMISSED = "dismissed"    # Human resolved without acting (ignored)
    CLARIFIED = "clarified"    # Human asked for clarification
    UNKNOWN = "unknown"        # No clear signal detected


@dataclass
class ReviewCommentFeedback:
    """
    Feedback data for a single review comment.

    Attributes:
        comment_id: GitHub comment ID
        thread_id: GitHub thread ID
        pr_number: Pull request number
        repo: Repository in owner/repo format
        classification: Feedback classification
        confidence: Confidence score (0.0 to 1.0)
        signal_source: What triggered the classification (e.g., "resolved", "reply")
        comment_body: Original comment text
        comment_path: File path the comment was on
        comment_line: Line number the comment was on
        is_ai_comment: Whether the comment was from an AI reviewer
        ai_source: AI reviewer source (e.g., "gemini", "copilot")
        reply_text: Human reply text if any
        code_changed: Whether code was changed after the comment
        recorded_at: Unix timestamp when feedback was recorded
    """
    comment_id: int
    thread_id: int
    pr_number: int
    repo: str
    classification: FeedbackClassification
    confidence: float
    signal_source: str
    comment_body: str = ""
    comment_path: Optional[str] = None
    comment_line: Optional[int] = None
    is_ai_comment: bool = False
    ai_source: Optional[str] = None
    reply_text: Optional[str] = None
    code_changed: bool = False
    recorded_at: int = field(default_factory=lambda: int(time.time()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "comment_id": self.comment_id,
            "thread_id": self.thread_id,
            "pr_number": self.pr_number,
            "repo": self.repo,
            "classification": self.classification.value,
            "confidence": self.confidence,
            "signal_source": self.signal_source,
            "comment_body": self.comment_body,
            "comment_path": self.comment_path,
            "comment_line": self.comment_line,
            "is_ai_comment": self.is_ai_comment,
            "ai_source": self.ai_source,
            "reply_text": self.reply_text,
            "code_changed": self.code_changed,
            "recorded_at": self.recorded_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewCommentFeedback":
        """Create ReviewCommentFeedback from dictionary."""
        return cls(
            comment_id=data.get("comment_id", 0),
            thread_id=data.get("thread_id", 0),
            pr_number=data.get("pr_number", 0),
            repo=data.get("repo", ""),
            classification=FeedbackClassification(data.get("classification", "unknown")),
            confidence=data.get("confidence", 0.0),
            signal_source=data.get("signal_source", ""),
            comment_body=data.get("comment_body", ""),
            comment_path=data.get("comment_path"),
            comment_line=data.get("comment_line"),
            is_ai_comment=data.get("is_ai_comment", False),
            ai_source=data.get("ai_source"),
            reply_text=data.get("reply_text"),
            code_changed=data.get("code_changed", False),
            recorded_at=data.get("recorded_at", int(time.time())),
            metadata=data.get("metadata", {}),
        )


# =============================================================================
# Reply Pattern Detection
# =============================================================================
# These patterns are used to classify feedback from human replies to AI comments.
# Patterns are ordered by specificity - more specific patterns should be checked first.

ACCEPTED_PATTERNS: List[Tuple[str, float]] = [
    (r"\b(good\s+catch|nice\s+catch|great\s+catch)\b", 0.9),
    (r"\b(you'?re\s+right|you\s+are\s+right)\b", 0.85),
    (r"\b(fixed|will\s+fix|fixing)\b", 0.8),
    (r"\b(thanks|thank\s+you|thx)\b", 0.7),
    (r"\b(agreed|agree)\b", 0.75),
    (r"\b(done|addressed|applied)\b", 0.8),
]

REJECTED_PATTERNS: List[Tuple[str, float]] = [
    (r"\b(false\s+positive)\b", 0.95),
    (r"\b(not\s+a\s+bug|not\s+an?\s+issue)\b", 0.9),
    (r"\b(intentional|by\s+design|expected\s+behavior)\b", 0.85),
    (r"\b(won'?t\s+fix|wontfix)\b", 0.9),
    (r"\b(incorrect|wrong)\b", 0.8),
    (r"\b(doesn'?t\s+apply|not\s+applicable|n/?a)\b", 0.85),
    (r"\b(already\s+handled|already\s+covered)\b", 0.8),
]

CLARIFIED_PATTERNS: List[Tuple[str, float]] = [
    (r"\?$", 0.6),  # Ends with question mark
    (r"\b(what\s+do\s+you\s+mean)\b", 0.85),
    (r"\b(can\s+you\s+explain|please\s+explain)\b", 0.8),
    (r"\b(not\s+sure\s+I\s+understand|don'?t\s+understand)\b", 0.8),
    (r"\b(could\s+you\s+clarify)\b", 0.85),
    (r"\b(why\s+is\s+this|why\s+would)\b.*\?", 0.7),
]


def classify_reply_pattern(
    reply_text: str,
) -> Tuple[FeedbackClassification, float]:
    """
    Classify feedback based on reply text patterns.

    Args:
        reply_text: The human reply text to analyze

    Returns:
        Tuple of (FeedbackClassification, confidence)

    Event Codes (greppable):
        [FEEDBACK_REPLY_CLASSIFIED] - Reply pattern matched
    """
    if not reply_text:
        return FeedbackClassification.UNKNOWN, 0.0

    reply_lower = reply_text.lower().strip()

    # Check rejected patterns first (highest priority for negative feedback)
    for pattern, confidence in REJECTED_PATTERNS:
        if re.search(pattern, reply_lower, re.IGNORECASE):
            logger.debug(
                "[FEEDBACK_REPLY_CLASSIFIED] Rejected pattern matched: %s",
                pattern,
            )
            return FeedbackClassification.REJECTED, confidence

    # Check accepted patterns
    for pattern, confidence in ACCEPTED_PATTERNS:
        if re.search(pattern, reply_lower, re.IGNORECASE):
            logger.debug(
                "[FEEDBACK_REPLY_CLASSIFIED] Accepted pattern matched: %s",
                pattern,
            )
            return FeedbackClassification.ACCEPTED, confidence

    # Check clarification patterns
    for pattern, confidence in CLARIFIED_PATTERNS:
        if re.search(pattern, reply_lower, re.IGNORECASE):
            logger.debug(
                "[FEEDBACK_REPLY_CLASSIFIED] Clarified pattern matched: %s",
                pattern,
            )
            return FeedbackClassification.CLARIFIED, confidence

    return FeedbackClassification.UNKNOWN, 0.0


def classify_feedback(
    action: str,
    code_changed: bool = False,
    reply_text: Optional[str] = None,
    has_thumbs_down: bool = False,
    has_thumbs_up: bool = False,
) -> Tuple[FeedbackClassification, float]:
    """
    Classify feedback based on multiple signals.

    This function implements the Signal Detection Rules from EPIC B-18 spec.

    Args:
        action: The webhook action (e.g., "resolved", "unresolved")
        code_changed: Whether code was changed after the comment
        reply_text: Human reply text if any
        has_thumbs_down: Whether the comment has a thumbs down reaction
        has_thumbs_up: Whether the comment has a thumbs up reaction

    Returns:
        Tuple of (FeedbackClassification, confidence)

    Event Codes (greppable):
        [FEEDBACK_CLASSIFIED] - Feedback classification completed
    """
    # Priority 1: Explicit rejection signals
    if has_thumbs_down:
        logger.info("[FEEDBACK_CLASSIFIED] Thumbs down reaction detected")
        return FeedbackClassification.REJECTED, 0.9

    # Priority 2: Reply text patterns
    if reply_text:
        classification, confidence = classify_reply_pattern(reply_text)
        if classification != FeedbackClassification.UNKNOWN:
            logger.info(
                "[FEEDBACK_CLASSIFIED] Reply pattern: %s (confidence=%.2f)",
                classification.value,
                confidence,
            )
            return classification, confidence

    # Priority 3: Thread resolution signals
    if action == "resolved":
        if code_changed:
            logger.info("[FEEDBACK_CLASSIFIED] Resolved with code change -> ACCEPTED")
            return FeedbackClassification.ACCEPTED, 0.85
        else:
            logger.info("[FEEDBACK_CLASSIFIED] Resolved without code change -> DISMISSED")
            return FeedbackClassification.DISMISSED, 0.7

    if action == "unresolved":
        logger.info("[FEEDBACK_CLASSIFIED] Thread unresolved -> needs attention")
        return FeedbackClassification.UNKNOWN, 0.3

    # Priority 4: Thumbs up (lower priority than explicit signals)
    if has_thumbs_up:
        logger.info("[FEEDBACK_CLASSIFIED] Thumbs up reaction detected")
        return FeedbackClassification.ACCEPTED, 0.7

    return FeedbackClassification.UNKNOWN, 0.0


def create_feedback_from_webhook(
    event_metadata: Dict[str, Any],
    pr_number: int,
    repo: str,
    action: str,
    code_changed: bool = False,
) -> Optional[ReviewCommentFeedback]:
    """
    Create a ReviewCommentFeedback from webhook event metadata.

    Args:
        event_metadata: Metadata from the parsed webhook event
        pr_number: Pull request number
        repo: Repository in owner/repo format
        action: The webhook action (e.g., "resolved", "unresolved")
        code_changed: Whether code was changed after the comment

    Returns:
        ReviewCommentFeedback or None if feedback cannot be created

    Event Codes (greppable):
        [FEEDBACK_CREATED] - Feedback object created from webhook
        [FEEDBACK_SKIPPED] - Feedback creation skipped (not an AI comment)
    """
    if not settings.enable_review_comment_feedback:
        logger.debug("[FEEDBACK_SKIPPED] Feature flag disabled")
        return None

    comment_id = event_metadata.get("comment_id")
    thread_id = event_metadata.get("thread_id")

    if not comment_id or not thread_id:
        logger.warning(
            "[FEEDBACK_SKIPPED] Missing comment_id or thread_id in metadata"
        )
        return None

    # Only process feedback for AI reviewer comments
    is_ai_comment = event_metadata.get("comment_author_is_ai", False)
    if not is_ai_comment:
        logger.debug(
            "[FEEDBACK_SKIPPED] Comment is not from AI reviewer: comment_id=%s",
            comment_id,
        )
        return None

    # Classify the feedback
    classification, confidence = classify_feedback(
        action=action,
        code_changed=code_changed,
    )

    feedback = ReviewCommentFeedback(
        comment_id=comment_id,
        thread_id=thread_id,
        pr_number=pr_number,
        repo=repo,
        classification=classification,
        confidence=confidence,
        signal_source=f"webhook:{action}",
        comment_body=event_metadata.get("comment_body", ""),
        comment_path=event_metadata.get("comment_path"),
        comment_line=event_metadata.get("comment_line"),
        is_ai_comment=True,
        ai_source=event_metadata.get("comment_ai_source"),
        code_changed=code_changed,
        metadata={
            "thread_node_id": event_metadata.get("thread_node_id"),
            "thread_comment_ids": event_metadata.get("thread_comment_ids", []),
        },
    )

    logger.info(
        "[FEEDBACK_CREATED] Created feedback: comment_id=%s, classification=%s, confidence=%.2f",
        comment_id,
        classification.value,
        confidence,
        extra={
            "comment_id": comment_id,
            "thread_id": thread_id,
            "pr_number": pr_number,
            "repo": repo,
            "classification": classification.value,
            "confidence": confidence,
            "ai_source": feedback.ai_source,
        }
    )

    return feedback


def create_feedback_from_reaction(
    event_metadata: Dict[str, Any],
    pr_number: int,
    repo: str,
    action: str,
) -> Optional[ReviewCommentFeedback]:
    """
    Create a ReviewCommentFeedback from a reaction webhook event.

    B-18.1.2: Reaction events on PR review comments (thumbs up/down)

    Args:
        event_metadata: Metadata from the parsed webhook event
        pr_number: Pull request number
        repo: Repository in owner/repo format
        action: The webhook action ("created" or "deleted")

    Returns:
        ReviewCommentFeedback or None if feedback cannot be created

    Event Codes (greppable):
        [FEEDBACK_REACTION_CREATED] - Feedback object created from reaction
        [FEEDBACK_REACTION_SKIPPED] - Feedback creation skipped
    """
    if not settings.enable_review_comment_feedback:
        logger.debug("[FEEDBACK_REACTION_SKIPPED] Feature flag disabled")
        return None

    comment_id = event_metadata.get("comment_id")
    reaction_content = event_metadata.get("reaction_content", "")
    reaction_sentiment = event_metadata.get("reaction_sentiment", "neutral")

    if not comment_id:
        logger.warning(
            "[FEEDBACK_REACTION_SKIPPED] Missing comment_id in metadata"
        )
        return None

    # Only process feedback for AI reviewer comments
    is_ai_comment = event_metadata.get("comment_author_is_ai", False)
    if not is_ai_comment:
        logger.debug(
            "[FEEDBACK_REACTION_SKIPPED] Comment is not from AI reviewer: comment_id=%s",
            comment_id,
        )
        return None

    # Classify based on reaction sentiment
    # For "created" action: positive reaction = ACCEPTED, negative = REJECTED
    # For "deleted" action: we record but with lower confidence (user changed mind)
    if action == "created":
        if reaction_sentiment == "positive":
            classification = FeedbackClassification.ACCEPTED
            confidence = 0.7  # Lower than explicit "good catch" reply
        elif reaction_sentiment == "negative":
            classification = FeedbackClassification.REJECTED
            confidence = 0.9  # Thumbs down is a strong rejection signal
        else:
            classification = FeedbackClassification.UNKNOWN
            confidence = 0.3
    elif action == "deleted":
        # Reaction was removed - user changed their mind
        # We still record this but with lower confidence
        classification = FeedbackClassification.UNKNOWN
        confidence = 0.2
    else:
        classification = FeedbackClassification.UNKNOWN
        confidence = 0.0

    logger.info(
        "[FEEDBACK_REACTION_CLASSIFIED] Reaction %s: content=%s, sentiment=%s -> %s (confidence=%.2f)",
        action,
        reaction_content,
        reaction_sentiment,
        classification.value,
        confidence,
    )

    feedback = ReviewCommentFeedback(
        comment_id=comment_id,
        thread_id=0,  # Reactions don't have thread context
        pr_number=pr_number,
        repo=repo,
        classification=classification,
        confidence=confidence,
        signal_source=f"reaction:{action}:{reaction_content}",
        comment_body=event_metadata.get("comment_body", ""),
        comment_path=event_metadata.get("comment_path"),
        comment_line=event_metadata.get("comment_line"),
        is_ai_comment=True,
        ai_source=event_metadata.get("comment_ai_source"),
        code_changed=False,
        metadata={
            "reaction_id": event_metadata.get("reaction_id"),
            "reaction_content": reaction_content,
            "reaction_sentiment": reaction_sentiment,
            "reaction_user": event_metadata.get("reaction_user"),
            "comment_node_id": event_metadata.get("comment_node_id"),
        },
    )

    logger.info(
        "[FEEDBACK_REACTION_CREATED] Created feedback from reaction: comment_id=%s, reaction=%s, classification=%s",
        comment_id,
        reaction_content,
        classification.value,
        extra={
            "comment_id": comment_id,
            "pr_number": pr_number,
            "repo": repo,
            "reaction_content": reaction_content,
            "classification": classification.value,
            "confidence": confidence,
            "ai_source": feedback.ai_source,
        }
    )

    return feedback


class ReviewCommentFeedbackCollector:
    """
    Collects and processes review comment feedback.

    EPIC B-18 Phase 1: Feedback Signal Capture

    This class provides:
    1. process_thread_event(): Process thread resolved/unresolved events
    2. process_reaction_event(): Process reaction events (B-18.1.2)
    3. process_reply(): Process reply text for feedback signals
    4. get_stats(): Get collection statistics
    """

    def __init__(self, trace_id: Optional[str] = None):
        """
        Initialize the ReviewCommentFeedbackCollector.

        Args:
            trace_id: Optional workflow trace ID for correlation
        """
        self.trace_id = trace_id
        self._enabled = settings.enable_review_comment_feedback
        self._feedbacks_collected = 0
        self._ai_comments_processed = 0
        self._human_comments_skipped = 0
        self._reactions_processed = 0

    @property
    def is_enabled(self) -> bool:
        """Check if feedback collection is enabled."""
        return self._enabled

    def process_thread_event(
        self,
        event_metadata: Dict[str, Any],
        pr_number: int,
        repo: str,
        action: str,
        code_changed: bool = False,
    ) -> Optional[ReviewCommentFeedback]:
        """
        Process a thread resolved/unresolved event.

        Args:
            event_metadata: Metadata from the parsed webhook event
            pr_number: Pull request number
            repo: Repository in owner/repo format
            action: The webhook action ("resolved" or "unresolved")
            code_changed: Whether code was changed after the comment

        Returns:
            ReviewCommentFeedback or None if not applicable
        """
        if not self._enabled:
            return None

        feedback = create_feedback_from_webhook(
            event_metadata=event_metadata,
            pr_number=pr_number,
            repo=repo,
            action=action,
            code_changed=code_changed,
        )

        if feedback:
            self._feedbacks_collected += 1
            self._ai_comments_processed += 1
        elif event_metadata.get("comment_author_is_ai", False) is False:
            self._human_comments_skipped += 1

        return feedback

    def process_reaction_event(
        self,
        event_metadata: Dict[str, Any],
        pr_number: int,
        repo: str,
        action: str,
    ) -> Optional[ReviewCommentFeedback]:
        """
        Process a reaction event on a review comment.

        B-18.1.2: Reaction events on PR review comments (thumbs up/down)

        Args:
            event_metadata: Metadata from the parsed webhook event
            pr_number: Pull request number
            repo: Repository in owner/repo format
            action: The webhook action ("created" or "deleted")

        Returns:
            ReviewCommentFeedback or None if not applicable
        """
        if not self._enabled:
            return None

        feedback = create_feedback_from_reaction(
            event_metadata=event_metadata,
            pr_number=pr_number,
            repo=repo,
            action=action,
        )

        if feedback:
            self._feedbacks_collected += 1
            self._reactions_processed += 1
            self._ai_comments_processed += 1
        elif event_metadata.get("comment_author_is_ai", False) is False:
            self._human_comments_skipped += 1

        return feedback

    def get_stats(self) -> Dict[str, Any]:
        """Get feedback collection statistics."""
        return {
            "enabled": self._enabled,
            "feedbacks_collected": self._feedbacks_collected,
            "ai_comments_processed": self._ai_comments_processed,
            "human_comments_skipped": self._human_comments_skipped,
            "reactions_processed": self._reactions_processed,
            "trace_id": self.trace_id,
        }


def get_feedback_collector(
    trace_id: Optional[str] = None,
) -> ReviewCommentFeedbackCollector:
    """
    Factory function to get a ReviewCommentFeedbackCollector instance.

    Args:
        trace_id: Optional workflow trace ID

    Returns:
        ReviewCommentFeedbackCollector instance
    """
    return ReviewCommentFeedbackCollector(trace_id=trace_id)


# =============================================================================
# B-18.2: Negative Example Storage
# =============================================================================
# These functions save review comment feedback to Memory v2 Knowledge Base
# for future retrieval during reviews.

# Confidence threshold for storing feedback (from EPIC B-18 spec)
REVIEW_FEEDBACK_CONFIDENCE_THRESHOLD = 0.7


def calculate_feedback_importance(
    feedback: ReviewCommentFeedback,
    pattern_frequency: float = 0.5,
    impact_severity: float = 0.5,
) -> float:
    """
    Calculate importance score for review feedback.

    B-18.2.3: Importance scoring for feedback

    Formula (from EPIC B-18 spec):
    importance_score = (
        rejection_confidence * 0.4 +    # How certain is the rejection?
        pattern_frequency * 0.3 +       # How often does this pattern appear?
        impact_severity * 0.3           # How bad was the false positive?
    )

    Args:
        feedback: The ReviewCommentFeedback to score
        pattern_frequency: How often this code pattern appears (0.0-1.0)
        impact_severity: Based on original suggestion severity (0.0-1.0)

    Returns:
        Importance score (0.0 to 1.0)

    Event Codes (greppable):
        [FEEDBACK_IMPORTANCE_SCORED] - Importance score calculated
    """
    rejection_confidence = feedback.confidence

    importance = (
        rejection_confidence * 0.4 +
        pattern_frequency * 0.3 +
        impact_severity * 0.3
    )

    logger.debug(
        "[FEEDBACK_IMPORTANCE_SCORED] comment_id=%s, importance=%.2f "
        "(confidence=%.2f, frequency=%.2f, severity=%.2f)",
        feedback.comment_id,
        importance,
        rejection_confidence,
        pattern_frequency,
        impact_severity,
    )

    return min(1.0, max(0.0, importance))


def save_review_comment_feedback(
    feedback: ReviewCommentFeedback,
    pattern_frequency: float = 0.5,
    impact_severity: float = 0.5,
) -> bool:
    """
    Save review comment feedback to Memory v2 Knowledge Base.

    B-18.2.2: Implement save_review_comment_feedback()

    This function stores human feedback on AI review comments as either
    positive (REVIEW_ACCEPTED) or negative (REVIEW_REJECTED) examples
    in the Knowledge Base for future retrieval.

    Args:
        feedback: The ReviewCommentFeedback to save
        pattern_frequency: How often this code pattern appears (0.0-1.0)
        impact_severity: Based on original suggestion severity (0.0-1.0)

    Returns:
        True if saved successfully, False otherwise

    Event Codes (greppable):
        [FEEDBACK_SAVED] - Feedback saved to Knowledge Base
        [FEEDBACK_SAVE_SKIPPED] - Feedback not saved (below threshold or disabled)
        [FEEDBACK_SAVE_FAILED] - Failed to save feedback
    """
    if not settings.enable_review_comment_feedback:
        logger.debug("[FEEDBACK_SAVE_SKIPPED] Feature flag disabled")
        return False

    # Only save feedback with sufficient confidence
    threshold = getattr(
        settings,
        'review_feedback_confidence_threshold',
        REVIEW_FEEDBACK_CONFIDENCE_THRESHOLD,
    )
    if feedback.confidence < threshold:
        logger.debug(
            "[FEEDBACK_SAVE_SKIPPED] Confidence %.2f below threshold %.2f",
            feedback.confidence,
            threshold,
        )
        return False

    # Only save ACCEPTED or REJECTED feedback (not UNKNOWN, DISMISSED, CLARIFIED)
    if feedback.classification not in (
        FeedbackClassification.ACCEPTED,
        FeedbackClassification.REJECTED,
    ):
        logger.debug(
            "[FEEDBACK_SAVE_SKIPPED] Classification %s not saveable",
            feedback.classification.value,
        )
        return False

    try:
        from memory.memory_v2 import (
            MemoryEntry,
            MemoryLayer,
            MemoryScope,
            get_memory_v2,
        )
        from memory.memory_consolidation import MemoryType

        memory = get_memory_v2()
        if memory is None:
            logger.warning("[FEEDBACK_SAVE_FAILED] Memory v2 not available")
            return False

        # Determine memory type based on classification
        if feedback.classification == FeedbackClassification.ACCEPTED:
            memory_type = MemoryType.REVIEW_ACCEPTED
        else:
            memory_type = MemoryType.REVIEW_REJECTED

        # Calculate importance score
        importance = calculate_feedback_importance(
            feedback,
            pattern_frequency=pattern_frequency,
            impact_severity=impact_severity,
        )

        # Build memory entry key
        key = f"review_feedback:{feedback.repo}:{feedback.pr_number}:{feedback.comment_id}"

        # Build content as JSON for searchability
        import json
        content = json.dumps({
            "suggestion_text": feedback.comment_body[:500] if feedback.comment_body else "",
            "code_pattern": feedback.comment_path or "",
            "feedback": feedback.classification.value,
            "confidence": feedback.confidence,
            "signal_source": feedback.signal_source,
            "ai_source": feedback.ai_source,
            "recorded_at": feedback.recorded_at,
        })

        # Build metadata for filtering and retrieval
        metadata = {
            "type": memory_type.value,
            "classification": feedback.classification.value,
            "confidence": feedback.confidence,
            "importance": importance,
            "repo": feedback.repo,
            "pr_number": feedback.pr_number,
            "comment_id": feedback.comment_id,
            "comment_path": feedback.comment_path,
            "comment_line": feedback.comment_line,
            "ai_source": feedback.ai_source,
            "signal_source": feedback.signal_source,
            "recorded_at": feedback.recorded_at,
        }

        # Create memory entry
        entry = MemoryEntry(
            key=key,
            content=content,
            layer=MemoryLayer.KNOWLEDGE_BASE,
            scope=MemoryScope.GLOBAL,
            metadata=metadata,
        )

        # Save to Knowledge Base
        success = memory.save(entry)

        if success:
            logger.info(
                "[FEEDBACK_SAVED] Saved %s feedback: key=%s, importance=%.2f",
                feedback.classification.value,
                key,
                importance,
                extra={
                    "key": key,
                    "classification": feedback.classification.value,
                    "confidence": feedback.confidence,
                    "importance": importance,
                    "repo": feedback.repo,
                    "pr_number": feedback.pr_number,
                    "comment_id": feedback.comment_id,
                }
            )
        else:
            logger.warning(
                "[FEEDBACK_SAVE_FAILED] Failed to save feedback: key=%s",
                key,
            )

        return success

    except ImportError as e:
        logger.warning(
            "[FEEDBACK_SAVE_FAILED] Memory v2 import failed: %s",
            str(e),
        )
        return False
    except Exception as e:
        logger.error(
            "[FEEDBACK_SAVE_FAILED] Unexpected error saving feedback: %s",
            str(e),
            exc_info=True,
        )
        return False
