"""
Tests for Review Feedback Loop - EPIC B Phase B-13

This module validates the B-13 Review Feedback Loop implementation:
1. ReviewFeedbackLoop class functionality
2. Integration with Memory v2 for storing review outcomes
3. Pattern retrieval for informing future reviews

Blueprint Reference: EPIC B-13 (Real-time Feedback Loop)
Issue: #4105 - Validate and Enable Pattern Retrieval
"""

from unittest.mock import patch, MagicMock

from review_context.review_feedback_loop import (
    ReviewFeedbackLoop,
    ReviewPattern,
    FeedbackLoopStats,
    get_feedback_loop,
)


class TestReviewPattern:
    """Tests for ReviewPattern dataclass."""

    def test_review_pattern_creation(self):
        """Test ReviewPattern can be created with all fields."""
        pattern = ReviewPattern(
            similarity=0.85,
            verdict="approve",
            severity="low",
            summary="Code looks good",
            comments=[{"body": "LGTM"}],
            file_paths=["src/main.py"],
            pr_number=123,
            repo="owner/repo",
            blocker_count=0,
            saved_at="2024-01-01T00:00:00Z",
        )

        assert pattern.similarity == 0.85
        assert pattern.verdict == "approve"
        assert pattern.severity == "low"
        assert pattern.summary == "Code looks good"
        assert len(pattern.comments) == 1
        assert pattern.file_paths == ["src/main.py"]
        assert pattern.pr_number == 123
        assert pattern.repo == "owner/repo"
        assert pattern.blocker_count == 0

    def test_review_pattern_to_dict(self):
        """Test ReviewPattern serialization to dictionary."""
        pattern = ReviewPattern(
            similarity=0.9,
            verdict="request_changes",
            severity="high",
            summary="Security issue found",
            blocker_count=2,
        )

        result = pattern.to_dict()

        assert result["similarity"] == 0.9
        assert result["verdict"] == "request_changes"
        assert result["severity"] == "high"
        assert result["summary"] == "Security issue found"
        assert result["blocker_count"] == 2
        assert result["comments"] == []
        assert result["file_paths"] == []

    def test_review_pattern_from_dict(self):
        """Test ReviewPattern deserialization from dictionary."""
        data = {
            "similarity": 0.75,
            "verdict": "comment",
            "severity": "medium",
            "summary": "Minor suggestions",
            "comments": [{"body": "Consider refactoring"}],
            "file_paths": ["src/utils.py"],
            "pr_number": 456,
            "repo": "test/repo",
            "blocker_count": 1,
            "saved_at": "2024-01-15T12:00:00Z",
        }

        pattern = ReviewPattern.from_dict(data)

        assert pattern.similarity == 0.75
        assert pattern.verdict == "comment"
        assert pattern.severity == "medium"
        assert pattern.summary == "Minor suggestions"
        assert len(pattern.comments) == 1
        assert pattern.pr_number == 456

    def test_review_pattern_from_dict_with_defaults(self):
        """Test ReviewPattern deserialization with missing fields uses defaults."""
        data = {}

        pattern = ReviewPattern.from_dict(data)

        assert pattern.similarity == 0.0
        assert pattern.verdict == "unknown"
        assert pattern.severity == "low"
        assert pattern.summary == ""
        assert pattern.comments == []
        assert pattern.file_paths == []
        assert pattern.pr_number is None
        assert pattern.repo is None
        assert pattern.blocker_count == 0


class TestFeedbackLoopStats:
    """Tests for FeedbackLoopStats dataclass."""

    def test_feedback_loop_stats_defaults(self):
        """Test FeedbackLoopStats has correct default values."""
        stats = FeedbackLoopStats()

        assert stats.patterns_retrieved == 0
        assert stats.feedbacks_saved == 0
        assert stats.avg_similarity == 0.0
        assert stats.last_save_at is None
        assert stats.last_retrieval_at is None


class TestReviewFeedbackLoopInit:
    """Tests for ReviewFeedbackLoop initialization."""

    @patch("review_context.review_feedback_loop.settings")
    def test_init_with_trace_id(self, mock_settings):
        """Test ReviewFeedbackLoop initialization with trace_id."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        loop = ReviewFeedbackLoop(trace_id="test-trace-123")

        assert loop.trace_id == "test-trace-123"
        assert loop.is_enabled is True

    @patch("review_context.review_feedback_loop.settings")
    def test_init_disabled_when_memory_v2_off(self, mock_settings):
        """Test ReviewFeedbackLoop is disabled when ENABLE_MEMORY_V2=false."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = True

        loop = ReviewFeedbackLoop()

        assert loop.is_enabled is False

    @patch("review_context.review_feedback_loop.settings")
    def test_init_disabled_when_feedback_loop_off(self, mock_settings):
        """Test ReviewFeedbackLoop is disabled when ENABLE_REVIEW_FEEDBACK_LOOP=false."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = False

        loop = ReviewFeedbackLoop()

        assert loop.is_enabled is False


class TestSaveFeedback:
    """Tests for ReviewFeedbackLoop.save_feedback method."""

    @patch("review_context.review_feedback_loop.settings")
    def test_save_feedback_disabled_returns_false(self, mock_settings):
        """Test save_feedback returns False when disabled."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = False

        loop = ReviewFeedbackLoop()
        result = loop.save_feedback(
            pr_number=123,
            repo="owner/repo",
            verdict="approve",
            severity="low",
            summary="LGTM",
            review_comments=[],
            file_paths=["src/main.py"],
        )

        assert result is False

    @patch("review_context.review_feedback_loop.settings")
    def test_save_feedback_enabled_calls_memory_integration(self, mock_settings):
        """Test save_feedback calls memory integration when enabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        mock_save = MagicMock(return_value=True)
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(save_review_feedback=mock_save)},
        ):
            loop = ReviewFeedbackLoop(trace_id="test-trace")
            result = loop.save_feedback(
                pr_number=123,
                repo="owner/repo",
                verdict="approve",
                severity="low",
                summary="LGTM",
                review_comments=[{"body": "Looks good"}],
                file_paths=["src/main.py"],
                diff_snippet="+ new code",
                blocker_count=0,
            )

            assert result is True

    @patch("review_context.review_feedback_loop.settings")
    def test_save_feedback_updates_stats(self, mock_settings):
        """Test save_feedback updates statistics on success."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        mock_save = MagicMock(return_value=True)
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(save_review_feedback=mock_save)},
        ):
            loop = ReviewFeedbackLoop()
            loop.save_feedback(
                pr_number=123,
                repo="owner/repo",
                verdict="approve",
                severity="low",
                summary="LGTM",
                review_comments=[],
                file_paths=[],
            )

            assert loop.stats.feedbacks_saved == 1
            assert loop.stats.last_save_at is not None

    @patch("review_context.review_feedback_loop.settings")
    def test_save_feedback_handles_import_error(self, mock_settings):
        """Test save_feedback handles ImportError gracefully."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        loop = ReviewFeedbackLoop()
        with patch.dict("sys.modules", {"memory.memory_integration": None}):
            result = loop.save_feedback(
                pr_number=123,
                repo="owner/repo",
                verdict="approve",
                severity="low",
                summary="LGTM",
                review_comments=[],
                file_paths=[],
            )

            assert result is False


class TestGetRelevantPatterns:
    """Tests for ReviewFeedbackLoop.get_relevant_patterns method."""

    @patch("review_context.review_feedback_loop.settings")
    def test_get_patterns_disabled_returns_empty(self, mock_settings):
        """Test get_relevant_patterns returns empty when disabled."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = False
        mock_settings.enable_review_pattern_retrieval = False

        loop = ReviewFeedbackLoop()
        result = loop.get_relevant_patterns(diff_snippet="some code")

        assert result == []

    @patch("review_context.review_feedback_loop.settings")
    def test_get_patterns_pattern_retrieval_disabled(self, mock_settings):
        """Test get_relevant_patterns returns empty when pattern retrieval disabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = False

        loop = ReviewFeedbackLoop()
        result = loop.get_relevant_patterns(diff_snippet="some code")

        assert result == []

    @patch("review_context.review_feedback_loop.settings")
    def test_get_patterns_enabled_calls_memory_integration(self, mock_settings):
        """Test get_relevant_patterns calls memory integration when enabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        mock_results = [
            {
                "similarity": 0.9,
                "verdict": "approve",
                "severity": "low",
                "summary": "Similar code approved",
            }
        ]

        mock_search = MagicMock(return_value=mock_results)
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(search_review_patterns=mock_search)},
        ):
            loop = ReviewFeedbackLoop(trace_id="test-trace")
            result = loop.get_relevant_patterns(
                diff_snippet="def hello(): pass",
                file_paths=["src/main.py"],
                limit=5,
                min_similarity=0.7,
            )

            assert len(result) == 1
            assert result[0].similarity == 0.9
            assert result[0].verdict == "approve"

    @patch("review_context.review_feedback_loop.settings")
    def test_get_patterns_updates_stats(self, mock_settings):
        """Test get_relevant_patterns updates statistics."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        mock_results = [
            {"similarity": 0.9, "verdict": "approve", "severity": "low", "summary": "A"},
            {"similarity": 0.8, "verdict": "comment", "severity": "medium", "summary": "B"},
        ]

        mock_search = MagicMock(return_value=mock_results)
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(search_review_patterns=mock_search)},
        ):
            loop = ReviewFeedbackLoop()
            loop.get_relevant_patterns(diff_snippet="code")

            assert loop.stats.patterns_retrieved == 2
            assert abs(loop.stats.avg_similarity - 0.85) < 0.001
            assert loop.stats.last_retrieval_at is not None


class TestEnhanceReviewContext:
    """Tests for ReviewFeedbackLoop.enhance_review_context method."""

    @patch("review_context.review_feedback_loop.settings")
    def test_enhance_context_no_patterns(self, mock_settings):
        """Test enhance_review_context with no patterns found."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        mock_search = MagicMock(return_value=[])
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(search_review_patterns=mock_search)},
        ):
            loop = ReviewFeedbackLoop()
            result = loop.enhance_review_context(diff_snippet="code")

            assert result["has_patterns"] is False
            assert result["pattern_count"] == 0
            assert result["patterns"] == []
            assert result["context_text"] == ""

    @patch("review_context.review_feedback_loop.settings")
    def test_enhance_context_with_patterns(self, mock_settings):
        """Test enhance_review_context formats patterns correctly."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        mock_results = [
            {
                "similarity": 0.9,
                "verdict": "approve",
                "severity": "low",
                "summary": "Code looks good",
                "blocker_count": 0,
            },
            {
                "similarity": 0.8,
                "verdict": "request_changes",
                "severity": "high",
                "summary": "Security issue",
                "blocker_count": 2,
            },
        ]

        mock_search = MagicMock(return_value=mock_results)
        with patch.dict(
            "sys.modules",
            {"memory.memory_integration": MagicMock(search_review_patterns=mock_search)},
        ):
            loop = ReviewFeedbackLoop()
            result = loop.enhance_review_context(diff_snippet="code")

            assert result["has_patterns"] is True
            assert result["pattern_count"] == 2
            assert len(result["patterns"]) == 2
            assert "Past Review Patterns" in result["context_text"]
            assert "APPROVE" in result["context_text"]
            assert "REQUEST_CHANGES" in result["context_text"]
            assert "2 blocking issues" in result["context_text"]


class TestGetStats:
    """Tests for ReviewFeedbackLoop.get_stats method."""

    @patch("review_context.review_feedback_loop.settings")
    def test_get_stats_returns_all_fields(self, mock_settings):
        """Test get_stats returns all statistics fields."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        loop = ReviewFeedbackLoop()
        stats = loop.get_stats()

        assert "enabled" in stats
        assert "patterns_retrieved" in stats
        assert "feedbacks_saved" in stats
        assert "avg_similarity" in stats
        assert "last_save_at" in stats
        assert "last_retrieval_at" in stats


class TestGetFeedbackLoop:
    """Tests for get_feedback_loop factory function."""

    @patch("review_context.review_feedback_loop.settings")
    def test_get_feedback_loop_creates_instance(self, mock_settings):
        """Test get_feedback_loop creates ReviewFeedbackLoop instance."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        loop = get_feedback_loop(trace_id="test-trace")

        assert isinstance(loop, ReviewFeedbackLoop)
        assert loop.trace_id == "test-trace"

    @patch("review_context.review_feedback_loop.settings")
    def test_get_feedback_loop_without_trace_id(self, mock_settings):
        """Test get_feedback_loop works without trace_id."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        loop = get_feedback_loop()

        assert isinstance(loop, ReviewFeedbackLoop)
        assert loop.trace_id is None
