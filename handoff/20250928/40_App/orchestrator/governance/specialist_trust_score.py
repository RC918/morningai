"""
Specialist Trust Score - EPIC I-X RuntimeTrustScore Integration

Blueprint Reference: Section 7 (Adversarial Collaboration) - Feedback loop for agent improvement
Issue: #3925 - RuntimeTrustScore Integration - Reviewer Weight Adjustment

This module implements trust score tracking for Reviewer specialists to enable
the E+F+I closed-loop architecture:
- Detection (E): Safety Governor detects issues
- Recording (I): Track specialist accuracy (accepted vs rejected suggestions)
- Adjustment (F): Planner uses weighted findings based on trust scores

Design Principles:
- Per-specialist accuracy tracking
- Default trust score of 0.7 for new specialists
- Thread-safe singleton pattern for global access
- Integration with MultiSpecialistReviewer for weight adjustment
"""

import logging
import threading
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SpecialistType(str, Enum):
    """Specialist types for trust score tracking.

    Mirrors ReviewSpecialist from multi_specialist_reviewer.py
    """
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"


class FeedbackType(str, Enum):
    """Types of feedback for specialist suggestions."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"  # Partially accepted


@dataclass
class SpecialistFeedback:
    """
    Record of feedback for a specialist suggestion.

    Attributes:
        specialist: The specialist type
        feedback_type: Whether the suggestion was accepted/rejected
        finding_id: Optional ID of the specific finding
        timestamp: When the feedback was recorded
        metadata: Additional context (e.g., PR number, user)
    """
    specialist: SpecialistType
    feedback_type: FeedbackType
    finding_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "specialist": self.specialist.value,
            "feedback_type": self.feedback_type.value,
            "finding_id": self.finding_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SpecialistTrustScore:
    """
    Trust score data for a specialist.

    Attributes:
        specialist: The specialist type
        trust_score: Current trust score (0.0 to 1.0)
        total_suggestions: Total number of suggestions made
        accepted_count: Number of accepted suggestions
        rejected_count: Number of rejected suggestions
        partial_count: Number of partially accepted suggestions
        last_updated: When the score was last updated
    """
    specialist: SpecialistType
    trust_score: float = 0.7  # Default trust score for new specialists
    total_suggestions: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    partial_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "specialist": self.specialist.value,
            "trust_score": self.trust_score,
            "total_suggestions": self.total_suggestions,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "partial_count": self.partial_count,
            "last_updated": self.last_updated.isoformat(),
            "accuracy_rate": self.accuracy_rate,
        }

    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate from feedback history."""
        if self.total_suggestions == 0:
            return 0.7  # Default for no data

        # Partial counts as 0.5 acceptance
        effective_accepted = self.accepted_count + (self.partial_count * 0.5)
        return effective_accepted / self.total_suggestions


class SpecialistTrustScoreTracker:
    """
    Tracker for specialist trust scores.

    This class maintains trust scores for all specialists and provides
    methods for recording feedback and retrieving scores.

    Issue #3925: Implements the "Recording (I)" part of E+F+I closed loop.
    """

    # Default trust score for new specialists
    DEFAULT_TRUST_SCORE = 0.7

    # Minimum number of suggestions before trust score is adjusted
    MIN_SUGGESTIONS_FOR_ADJUSTMENT = 5

    # Weight for exponential moving average (higher = more weight on recent)
    EMA_WEIGHT = 0.3

    def __init__(self):
        """Initialize the tracker with default scores for all specialists."""
        self._scores: Dict[SpecialistType, SpecialistTrustScore] = {}
        self._feedback_history: List[SpecialistFeedback] = []
        self._lock = threading.Lock()

        # Initialize default scores for all specialists
        for specialist in SpecialistType:
            self._scores[specialist] = SpecialistTrustScore(
                specialist=specialist,
                trust_score=self.DEFAULT_TRUST_SCORE,
            )

        logger.info(
            "[SpecialistTrustScoreTracker] Initialized with default scores",
            extra={
                "operation": "trust_score_init",
                "specialists": [s.value for s in SpecialistType],
                "default_score": self.DEFAULT_TRUST_SCORE,
            }
        )

    def record_feedback(
        self,
        specialist: SpecialistType,
        feedback_type: FeedbackType,
        finding_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpecialistTrustScore:
        """
        Record feedback for a specialist suggestion.

        Args:
            specialist: The specialist type
            feedback_type: Whether the suggestion was accepted/rejected
            finding_id: Optional ID of the specific finding
            metadata: Additional context

        Returns:
            Updated SpecialistTrustScore for the specialist
        """
        with self._lock:
            # Record feedback
            feedback = SpecialistFeedback(
                specialist=specialist,
                feedback_type=feedback_type,
                finding_id=finding_id,
                metadata=metadata or {},
            )
            self._feedback_history.append(feedback)

            # Update score
            score = self._scores[specialist]
            score.total_suggestions += 1

            if feedback_type == FeedbackType.ACCEPTED:
                score.accepted_count += 1
            elif feedback_type == FeedbackType.REJECTED:
                score.rejected_count += 1
            elif feedback_type == FeedbackType.PARTIAL:
                score.partial_count += 1

            # Recalculate trust score if we have enough data
            if score.total_suggestions >= self.MIN_SUGGESTIONS_FOR_ADJUSTMENT:
                new_accuracy = score.accuracy_rate
                # Use exponential moving average (EMA) for smooth updates
                # Formula: new_score = EMA_WEIGHT * new_accuracy + (1 - EMA_WEIGHT) * old_score
                # This gives more weight to recent feedback while preserving historical trends
                score.trust_score = (
                    self.EMA_WEIGHT * new_accuracy +
                    (1 - self.EMA_WEIGHT) * score.trust_score
                )

            score.last_updated = datetime.now(timezone.utc)

            logger.info(
                f"[SpecialistTrustScoreTracker] Recorded feedback for {specialist.value}",
                extra={
                    "operation": "record_feedback",
                    "specialist": specialist.value,
                    "feedback_type": feedback_type.value,
                    "new_trust_score": score.trust_score,
                    "total_suggestions": score.total_suggestions,
                }
            )

            return score

    def get_trust_score(self, specialist: SpecialistType) -> float:
        """
        Get the current trust score for a specialist.

        Args:
            specialist: The specialist type

        Returns:
            Trust score (0.0 to 1.0)
        """
        with self._lock:
            return self._scores[specialist].trust_score

    def get_all_trust_scores(self) -> Dict[str, float]:
        """
        Get trust scores for all specialists.

        Returns:
            Dictionary mapping specialist name to trust score
        """
        with self._lock:
            return {
                specialist.value: score.trust_score
                for specialist, score in self._scores.items()
            }

    def get_specialist_stats(self, specialist: SpecialistType) -> SpecialistTrustScore:
        """
        Get full statistics for a specialist.

        Args:
            specialist: The specialist type

        Returns:
            A copy of SpecialistTrustScore with all statistics to ensure thread-safety.
        """
        with self._lock:
            return copy(self._scores[specialist])

    def get_feedback_history(
        self,
        specialist: Optional[SpecialistType] = None,
        limit: int = 100,
    ) -> List[SpecialistFeedback]:
        """
        Get feedback history, optionally filtered by specialist.

        Args:
            specialist: Optional specialist to filter by
            limit: Maximum number of records to return

        Returns:
            A list of copies of SpecialistFeedback records to ensure thread-safety.
        """
        with self._lock:
            if specialist:
                filtered = [
                    f for f in self._feedback_history
                    if f.specialist == specialist
                ]
            else:
                filtered = self._feedback_history

            # Return copies of the most recent items to prevent mutation
            sorted_slice = sorted(
                filtered[-limit:],
                key=lambda f: f.timestamp,
                reverse=True,
            )
            return [copy(f) for f in sorted_slice]

    def reset_specialist(self, specialist: SpecialistType) -> None:
        """
        Reset a specialist's trust score to default.

        Args:
            specialist: The specialist type to reset
        """
        with self._lock:
            self._scores[specialist] = SpecialistTrustScore(
                specialist=specialist,
                trust_score=self.DEFAULT_TRUST_SCORE,
            )
            logger.info(
                f"[SpecialistTrustScoreTracker] Reset {specialist.value} to default",
                extra={
                    "operation": "reset_specialist",
                    "specialist": specialist.value,
                }
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker state to dictionary for serialization."""
        with self._lock:
            return {
                "scores": {
                    s.value: score.to_dict()
                    for s, score in self._scores.items()
                },
                "feedback_count": len(self._feedback_history),
            }


# Global singleton instance
_tracker: Optional[SpecialistTrustScoreTracker] = None
_tracker_lock = threading.Lock()


def get_specialist_trust_tracker() -> SpecialistTrustScoreTracker:
    """
    Get or create the global SpecialistTrustScoreTracker instance (thread-safe).

    Returns:
        Global SpecialistTrustScoreTracker instance
    """
    global _tracker

    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = SpecialistTrustScoreTracker()

    return _tracker


def reset_specialist_trust_tracker() -> None:
    """Reset the global tracker instance (useful for testing)."""
    global _tracker
    with _tracker_lock:
        _tracker = None
