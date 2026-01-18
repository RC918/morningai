"""
Tests for Specialist Trust Score - EPIC I-X RuntimeTrustScore Integration

Issue #3925: RuntimeTrustScore Integration - Reviewer Weight Adjustment
"""

from datetime import datetime

from governance.specialist_trust_score import (
    SpecialistType,
    FeedbackType,
    SpecialistFeedback,
    SpecialistTrustScore,
    SpecialistTrustScoreTracker,
    get_specialist_trust_tracker,
    reset_specialist_trust_tracker,
)


class TestSpecialistType:
    """Tests for SpecialistType enum."""

    def test_specialist_types_exist(self):
        """Test that all expected specialist types exist."""
        assert SpecialistType.SECURITY.value == "security"
        assert SpecialistType.PERFORMANCE.value == "performance"
        assert SpecialistType.ARCHITECTURE.value == "architecture"

    def test_specialist_type_is_string_enum(self):
        """Test that SpecialistType is a string enum."""
        assert isinstance(SpecialistType.SECURITY, str)
        assert SpecialistType.SECURITY == "security"


class TestFeedbackType:
    """Tests for FeedbackType enum."""

    def test_feedback_types_exist(self):
        """Test that all expected feedback types exist."""
        assert FeedbackType.ACCEPTED.value == "accepted"
        assert FeedbackType.REJECTED.value == "rejected"
        assert FeedbackType.PARTIAL.value == "partial"


class TestSpecialistFeedback:
    """Tests for SpecialistFeedback dataclass."""

    def test_create_feedback(self):
        """Test creating a feedback record."""
        feedback = SpecialistFeedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
            finding_id="finding-123",
        )
        assert feedback.specialist == SpecialistType.SECURITY
        assert feedback.feedback_type == FeedbackType.ACCEPTED
        assert feedback.finding_id == "finding-123"
        assert isinstance(feedback.timestamp, datetime)

    def test_feedback_to_dict(self):
        """Test converting feedback to dictionary."""
        feedback = SpecialistFeedback(
            specialist=SpecialistType.PERFORMANCE,
            feedback_type=FeedbackType.REJECTED,
            metadata={"pr_number": 123},
        )
        result = feedback.to_dict()
        assert result["specialist"] == "performance"
        assert result["feedback_type"] == "rejected"
        assert result["metadata"] == {"pr_number": 123}


class TestSpecialistTrustScore:
    """Tests for SpecialistTrustScore dataclass."""

    def test_default_trust_score(self):
        """Test default trust score is 0.7."""
        score = SpecialistTrustScore(specialist=SpecialistType.SECURITY)
        assert score.trust_score == 0.7
        assert score.total_suggestions == 0
        assert score.accepted_count == 0
        assert score.rejected_count == 0

    def test_accuracy_rate_no_data(self):
        """Test accuracy rate returns default when no data."""
        score = SpecialistTrustScore(specialist=SpecialistType.SECURITY)
        assert score.accuracy_rate == 0.7

    def test_accuracy_rate_with_data(self):
        """Test accuracy rate calculation."""
        score = SpecialistTrustScore(
            specialist=SpecialistType.SECURITY,
            total_suggestions=10,
            accepted_count=8,
            rejected_count=2,
        )
        assert score.accuracy_rate == 0.8

    def test_accuracy_rate_with_partial(self):
        """Test accuracy rate with partial acceptances."""
        score = SpecialistTrustScore(
            specialist=SpecialistType.SECURITY,
            total_suggestions=10,
            accepted_count=6,
            rejected_count=2,
            partial_count=2,  # Counts as 0.5 each = 1.0
        )
        # (6 + 2*0.5) / 10 = 7/10 = 0.7
        assert score.accuracy_rate == 0.7

    def test_to_dict(self):
        """Test converting score to dictionary."""
        score = SpecialistTrustScore(
            specialist=SpecialistType.ARCHITECTURE,
            trust_score=0.85,
            total_suggestions=20,
            accepted_count=17,
        )
        result = score.to_dict()
        assert result["specialist"] == "architecture"
        assert result["trust_score"] == 0.85
        assert result["total_suggestions"] == 20
        assert "accuracy_rate" in result


class TestSpecialistTrustScoreTracker:
    """Tests for SpecialistTrustScoreTracker."""

    def setup_method(self):
        """Reset global tracker before each test."""
        reset_specialist_trust_tracker()

    def test_initialization(self):
        """Test tracker initializes with default scores."""
        tracker = SpecialistTrustScoreTracker()
        scores = tracker.get_all_trust_scores()

        # PR #4209: Added CORRECTNESS specialist, now 4 core specialists
        assert len(scores) == 4
        assert scores["security"] == 0.7
        assert scores["performance"] == 0.7
        assert scores["architecture"] == 0.7
        assert scores["correctness"] == 0.7

    def test_record_accepted_feedback(self):
        """Test recording accepted feedback."""
        tracker = SpecialistTrustScoreTracker()

        result = tracker.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
        )

        assert result.total_suggestions == 1
        assert result.accepted_count == 1
        assert result.rejected_count == 0

    def test_record_rejected_feedback(self):
        """Test recording rejected feedback."""
        tracker = SpecialistTrustScoreTracker()

        result = tracker.record_feedback(
            specialist=SpecialistType.PERFORMANCE,
            feedback_type=FeedbackType.REJECTED,
        )

        assert result.total_suggestions == 1
        assert result.accepted_count == 0
        assert result.rejected_count == 1

    def test_trust_score_adjustment_after_min_suggestions(self):
        """Test trust score adjusts after minimum suggestions."""
        tracker = SpecialistTrustScoreTracker()

        # Record 5 accepted feedbacks (minimum for adjustment)
        for _ in range(5):
            tracker.record_feedback(
                specialist=SpecialistType.SECURITY,
                feedback_type=FeedbackType.ACCEPTED,
            )

        score = tracker.get_trust_score(SpecialistType.SECURITY)
        # With 100% accuracy, score should increase from 0.7
        # EMA: 0.3 * 1.0 + 0.7 * 0.7 = 0.3 + 0.49 = 0.79
        assert score > 0.7

    def test_trust_score_decreases_with_rejections(self):
        """Test trust score decreases with rejections."""
        tracker = SpecialistTrustScoreTracker()

        # Record 5 rejected feedbacks
        for _ in range(5):
            tracker.record_feedback(
                specialist=SpecialistType.ARCHITECTURE,
                feedback_type=FeedbackType.REJECTED,
            )

        score = tracker.get_trust_score(SpecialistType.ARCHITECTURE)
        # With 0% accuracy, score should decrease from 0.7
        # EMA: 0.3 * 0.0 + 0.7 * 0.7 = 0.49
        assert score < 0.7

    def test_get_specialist_stats(self):
        """Test getting full statistics for a specialist."""
        tracker = SpecialistTrustScoreTracker()

        tracker.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
        )
        tracker.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.REJECTED,
        )

        stats = tracker.get_specialist_stats(SpecialistType.SECURITY)
        assert stats.total_suggestions == 2
        assert stats.accepted_count == 1
        assert stats.rejected_count == 1

    def test_get_feedback_history(self):
        """Test getting feedback history."""
        tracker = SpecialistTrustScoreTracker()

        tracker.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
            finding_id="finding-1",
        )
        tracker.record_feedback(
            specialist=SpecialistType.PERFORMANCE,
            feedback_type=FeedbackType.REJECTED,
            finding_id="finding-2",
        )

        # Get all history
        history = tracker.get_feedback_history()
        assert len(history) == 2

        # Get filtered history
        security_history = tracker.get_feedback_history(
            specialist=SpecialistType.SECURITY
        )
        assert len(security_history) == 1
        assert security_history[0].finding_id == "finding-1"

    def test_reset_specialist(self):
        """Test resetting a specialist's score."""
        tracker = SpecialistTrustScoreTracker()

        # Record some feedback
        for _ in range(5):
            tracker.record_feedback(
                specialist=SpecialistType.SECURITY,
                feedback_type=FeedbackType.ACCEPTED,
            )

        # Score should have changed
        assert tracker.get_trust_score(SpecialistType.SECURITY) != 0.7

        # Reset
        tracker.reset_specialist(SpecialistType.SECURITY)

        # Score should be back to default
        assert tracker.get_trust_score(SpecialistType.SECURITY) == 0.7

    def test_to_dict(self):
        """Test converting tracker state to dictionary."""
        tracker = SpecialistTrustScoreTracker()

        tracker.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
        )

        result = tracker.to_dict()
        assert "scores" in result
        assert "feedback_count" in result
        assert result["feedback_count"] == 1
        assert "security" in result["scores"]


class TestLRUEviction:
    """Tests for LRU eviction of feedback history - Issue #4076."""

    def setup_method(self):
        """Reset global tracker before each test."""
        reset_specialist_trust_tracker()

    def test_max_feedback_history_constant(self):
        """Test that MAX_FEEDBACK_HISTORY is set to 1000."""
        assert SpecialistTrustScoreTracker.MAX_FEEDBACK_HISTORY == 1000

    def test_feedback_history_bounded(self):
        """Test that feedback history is bounded by MAX_FEEDBACK_HISTORY."""
        tracker = SpecialistTrustScoreTracker()

        # Record more than MAX_FEEDBACK_HISTORY feedbacks
        # Use a smaller number for testing (we'll verify the deque has maxlen)
        for i in range(10):
            tracker.record_feedback(
                specialist=SpecialistType.SECURITY,
                feedback_type=FeedbackType.ACCEPTED,
                finding_id=f"finding-{i}",
            )

        # Verify all 10 are stored
        history = tracker.get_feedback_history(limit=100)
        assert len(history) == 10

        # Verify most recent is first
        assert history[0].finding_id == "finding-9"
        assert history[9].finding_id == "finding-0"

    def test_lru_eviction_removes_oldest(self):
        """Test that LRU eviction removes oldest entries."""
        # Create a tracker with a small maxlen for testing
        # (Gemini Code Assist suggestion: use max_feedback_history parameter)
        tracker = SpecialistTrustScoreTracker(max_feedback_history=5)

        # Record 7 feedbacks
        for i in range(7):
            tracker.record_feedback(
                specialist=SpecialistType.SECURITY,
                feedback_type=FeedbackType.ACCEPTED,
                finding_id=f"finding-{i}",
            )

        # Only last 5 should remain
        history = tracker.get_feedback_history(limit=100)
        assert len(history) == 5

        # Oldest (finding-0, finding-1) should be evicted
        finding_ids = [f.finding_id for f in history]
        assert "finding-0" not in finding_ids
        assert "finding-1" not in finding_ids
        assert "finding-6" in finding_ids  # Most recent

    def test_self_critique_specialist_handling(self):
        """Test that SELF_CRITIQUE specialist is handled without KeyError.

        Issue: Cursor Bugbot identified that SELF_CRITIQUE is not in CORE_SPECIALISTS
        but the unified SpecialistType enum includes it. Methods should handle
        this gracefully without raising KeyError.
        """
        tracker = SpecialistTrustScoreTracker()

        # get_trust_score should return default for uninitialized SELF_CRITIQUE
        score = tracker.get_trust_score(SpecialistType.SELF_CRITIQUE)
        assert score == tracker.DEFAULT_TRUST_SCORE

        # get_specialist_stats should return default stats
        stats = tracker.get_specialist_stats(SpecialistType.SELF_CRITIQUE)
        assert stats.trust_score == tracker.DEFAULT_TRUST_SCORE
        assert stats.total_suggestions == 0

        # record_feedback should lazily initialize SELF_CRITIQUE
        result = tracker.record_feedback(
            specialist=SpecialistType.SELF_CRITIQUE,
            feedback_type=FeedbackType.ACCEPTED,
            finding_id="self-critique-finding-1",
        )
        assert result.total_suggestions == 1

        # Now SELF_CRITIQUE should be in scores
        score_after = tracker.get_trust_score(SpecialistType.SELF_CRITIQUE)
        assert score_after == tracker.DEFAULT_TRUST_SCORE


class TestGlobalTracker:
    """Tests for global tracker singleton."""

    def setup_method(self):
        """Reset global tracker before each test."""
        reset_specialist_trust_tracker()

    def test_get_tracker_returns_same_instance(self):
        """Test that get_specialist_trust_tracker returns singleton."""
        tracker1 = get_specialist_trust_tracker()
        tracker2 = get_specialist_trust_tracker()
        assert tracker1 is tracker2

    def test_reset_creates_new_instance(self):
        """Test that reset creates a new instance."""
        tracker1 = get_specialist_trust_tracker()
        tracker1.record_feedback(
            specialist=SpecialistType.SECURITY,
            feedback_type=FeedbackType.ACCEPTED,
        )

        reset_specialist_trust_tracker()
        tracker2 = get_specialist_trust_tracker()

        # New tracker should have no feedback history
        assert len(tracker2.get_feedback_history()) == 0
