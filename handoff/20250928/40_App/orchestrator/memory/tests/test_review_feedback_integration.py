"""
Tests for B-13 Review Feedback Memory Integration

This module validates the memory_integration functions for B-13:
1. save_review_feedback - stores review outcomes in Knowledge Base
2. search_review_patterns - retrieves past patterns for current reviews

Blueprint Reference: EPIC B-13 (Real-time Feedback Loop)
Issue: #4105 - Validate and Enable Pattern Retrieval
"""

from unittest.mock import patch

from memory.memory_integration import (
    save_review_feedback,
    search_review_patterns,
    _is_review_feedback_enabled,
    _is_review_pattern_retrieval_enabled,
    _sanitize_diff_for_storage,
)


class TestFeatureFlagChecks:
    """Tests for B-13 feature flag checks."""

    @patch("memory.memory_integration.settings")
    def test_review_feedback_enabled_when_both_flags_true(self, mock_settings):
        """Test _is_review_feedback_enabled returns True when both flags enabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True

        assert _is_review_feedback_enabled() is True

    @patch("memory.memory_integration.settings")
    def test_review_feedback_disabled_when_memory_v2_off(self, mock_settings):
        """Test _is_review_feedback_enabled returns False when ENABLE_MEMORY_V2=false."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = True

        assert _is_review_feedback_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_review_feedback_disabled_when_feedback_loop_off(self, mock_settings):
        """Test _is_review_feedback_enabled returns False when ENABLE_REVIEW_FEEDBACK_LOOP=false."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = False

        assert _is_review_feedback_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_pattern_retrieval_enabled_when_all_flags_true(self, mock_settings):
        """Test _is_review_pattern_retrieval_enabled returns True when all flags enabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        assert _is_review_pattern_retrieval_enabled() is True

    @patch("memory.memory_integration.settings")
    def test_pattern_retrieval_disabled_when_feedback_loop_off(self, mock_settings):
        """Test _is_review_pattern_retrieval_enabled returns False when feedback loop disabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = False
        mock_settings.enable_review_pattern_retrieval = True

        assert _is_review_pattern_retrieval_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_pattern_retrieval_disabled_when_retrieval_off(self, mock_settings):
        """Test _is_review_pattern_retrieval_enabled returns False when ENABLE_REVIEW_PATTERN_RETRIEVAL=false."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = False

        assert _is_review_pattern_retrieval_enabled() is False


class TestSanitizeDiffForStorage:
    """Tests for _sanitize_diff_for_storage function."""

    def test_sanitize_none_diff(self):
        """Test sanitizing None diff returns None and 0 count."""
        result, count = _sanitize_diff_for_storage(None)
        assert result is None
        assert count == 0

    def test_sanitize_empty_diff(self):
        """Test sanitizing empty diff returns empty and 0 count."""
        result, count = _sanitize_diff_for_storage("")
        assert result == ""
        assert count == 0

    def test_sanitize_clean_diff(self):
        """Test sanitizing clean diff returns unchanged."""
        diff = "+ def hello():\n+     return 'world'"
        result, count = _sanitize_diff_for_storage(diff)
        assert result == diff
        assert count == 0

    def test_sanitize_diff_with_api_key(self):
        """Test sanitizing diff with API key pattern."""
        diff = "+ API_KEY = 'sk-1234567890abcdef'"
        result, count = _sanitize_diff_for_storage(diff)
        assert "sk-1234567890abcdef" not in result
        assert count >= 1

    def test_sanitize_diff_with_password(self):
        """Test sanitizing diff with password pattern."""
        diff = "+ password = 'super_secret_123'"
        result, count = _sanitize_diff_for_storage(diff)
        assert "super_secret_123" not in result
        assert count >= 1


class TestSaveReviewFeedbackDisabled:
    """Tests for save_review_feedback when disabled."""

    @patch("memory.memory_integration.settings")
    def test_save_feedback_disabled_returns_false(self, mock_settings):
        """Test save_review_feedback returns False when disabled."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = False

        result = save_review_feedback(
            pr_number=123,
            repo="owner/repo",
            verdict="approve",
            severity="low",
            summary="LGTM",
            review_comments=[],
            file_paths=["src/main.py"],
        )

        assert result is False

    @patch("memory.memory_integration._get_memory_v2")
    @patch("memory.memory_integration.settings")
    def test_save_feedback_no_memory_instance(self, mock_settings, mock_get_memory):
        """Test save_review_feedback returns False when Memory v2 unavailable."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_get_memory.return_value = None

        result = save_review_feedback(
            pr_number=123,
            repo="owner/repo",
            verdict="approve",
            severity="low",
            summary="LGTM",
            review_comments=[],
            file_paths=["src/main.py"],
        )

        assert result is False


class TestSearchReviewPatternsDisabled:
    """Tests for search_review_patterns when disabled."""

    @patch("memory.memory_integration.settings")
    def test_search_patterns_disabled_returns_empty(self, mock_settings):
        """Test search_review_patterns returns empty when disabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = False

        result = search_review_patterns(query="def hello():")

        assert result == []

    @patch("memory.memory_integration._get_memory_v2")
    @patch("memory.memory_integration.settings")
    def test_search_patterns_no_memory_instance(self, mock_settings, mock_get_memory):
        """Test search_review_patterns returns empty when Memory v2 unavailable."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True
        mock_get_memory.return_value = None

        result = search_review_patterns(query="def hello():")

        assert result == []


class TestB13FeatureFlagCombinations:
    """Tests for various B-13 feature flag combinations."""

    @patch("memory.memory_integration.settings")
    def test_all_flags_disabled(self, mock_settings):
        """Test all B-13 features disabled."""
        mock_settings.enable_memory_v2 = False
        mock_settings.enable_review_feedback_loop = False
        mock_settings.enable_review_pattern_retrieval = False

        assert _is_review_feedback_enabled() is False
        assert _is_review_pattern_retrieval_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_only_memory_v2_enabled(self, mock_settings):
        """Test only ENABLE_MEMORY_V2=true."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = False
        mock_settings.enable_review_pattern_retrieval = False

        assert _is_review_feedback_enabled() is False
        assert _is_review_pattern_retrieval_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_feedback_loop_enabled_pattern_retrieval_disabled(self, mock_settings):
        """Test feedback loop enabled but pattern retrieval disabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = False

        assert _is_review_feedback_enabled() is True
        assert _is_review_pattern_retrieval_enabled() is False

    @patch("memory.memory_integration.settings")
    def test_all_flags_enabled(self, mock_settings):
        """Test all B-13 features enabled."""
        mock_settings.enable_memory_v2 = True
        mock_settings.enable_review_feedback_loop = True
        mock_settings.enable_review_pattern_retrieval = True

        assert _is_review_feedback_enabled() is True
        assert _is_review_pattern_retrieval_enabled() is True
