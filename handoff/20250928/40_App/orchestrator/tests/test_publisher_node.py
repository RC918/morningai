#!/usr/bin/env python3
"""
Unit tests for publisher_node and post_pr_review - EPIC B Phase B-3

Tests cover:
1. post_pr_review() feature flag behavior
2. post_pr_review() fallback mechanism for 422/404 errors
3. post_pr_review() error handling for other errors
4. post_pr_review() comment processing (validation, truncation)
5. publisher_node no-op behavior
6. publisher_node integration with post_pr_review

Issue #2595: EPIC B - Diff-Aware Review Plumbing
Phase B-3: GitHub Inline Comment Posting
Issue #2706: Add unit tests for publisher_node fallback mechanism
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402
from github import GithubException, UnknownObjectException  # noqa: E402


class MockSettings:
    """Mock settings object for testing"""
    def __init__(
        self,
        enable_github_review_posting=True,
        github_review_posting_dry_run=False,
        github_review_posting_max_comments=10,
        agent_github_token="test-token",
        github_token="test-token",
        github_repo="test/repo"
    ):
        self.enable_github_review_posting = enable_github_review_posting
        self.github_review_posting_dry_run = github_review_posting_dry_run
        self.github_review_posting_max_comments = github_review_posting_max_comments
        self.agent_github_token = agent_github_token
        self.github_token = github_token
        self.github_repo = github_repo


class TestPostPrReviewFeatureFlags:
    """Tests for post_pr_review() feature flag behavior"""

    def test_feature_disabled_returns_error(self):
        """ENABLE_GITHUB_REVIEW_POSTING=False should return success=False, error='Feature disabled'"""
        mock_settings = MockSettings(enable_github_review_posting=False)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=MagicMock(),
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert result["error"] == "Feature disabled"
            assert result["posted_count"] == 0

    def test_dry_run_mode_does_not_call_create_review(self):
        """DRY_RUN=True should return success=True, dry_run=True without calling create_review()"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=True,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is True
            assert result["dry_run"] is True
            assert result["posted_count"] == 1
            mock_pr.create_review.assert_not_called()

    def test_live_mode_calls_create_review(self):
        """DRY_RUN=False should call create_review()"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is True
            assert result["dry_run"] is False
            mock_pr.create_review.assert_called_once()


class TestPostPrReviewFallback:
    """Tests for post_pr_review() fallback mechanism (422/404 errors)"""

    def test_422_error_triggers_fallback(self):
        """GithubException(status=422) should trigger fallback to Review Body Appendix"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        call_count = [0]

        def create_review_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise GithubException(422, {"message": "Validation Failed"}, None)

        mock_pr.create_review.side_effect = create_review_side_effect

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test comment"}]
            )

            assert result["success"] is True
            assert result.get("downgraded") is True
            assert mock_pr.create_review.call_count == 2

    def test_404_error_triggers_fallback(self):
        """GithubException(status=404) should trigger fallback to Review Body Appendix"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        call_count = [0]

        def create_review_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise GithubException(404, {"message": "Not Found"}, None)

        mock_pr.create_review.side_effect = create_review_side_effect

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test comment"}]
            )

            assert result["success"] is True
            assert result.get("downgraded") is True

    def test_fallback_success_returns_downgraded_true(self):
        """Fallback success should return success=True, downgraded=True"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        call_count = [0]

        def create_review_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise GithubException(422, {"message": "Validation Failed"}, None)

        mock_pr.create_review.side_effect = create_review_side_effect

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is True
            assert result["downgraded"] is True
            assert result["posted_count"] == 1

    def test_fallback_also_fails_returns_both_errors(self):
        """When fallback also fails, should return success=False with both error messages"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        mock_pr.create_review.side_effect = [
            GithubException(422, {"message": "Validation Failed"}, None),
            Exception("Fallback also failed")
        ]

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert "Both inline and fallback review failed" in result["error"]
            assert "Validation Failed" in result["error"]
            assert "Fallback also failed" in result["error"]

    def test_fallback_body_contains_comments_as_markdown(self):
        """Fallback should convert comments to markdown in review body"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        call_count = [0]
        captured_body = [None]

        def create_review_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise GithubException(422, {"message": "Validation Failed"}, None)
            captured_body[0] = kwargs.get("body")

        mock_pr.create_review.side_effect = create_review_side_effect

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[
                    {"file": "src/test.py", "end_line": 42, "message": "Fix this bug"},
                    {"file": "src/utils.py", "start_line": 10, "end_line": 15, "message": "Refactor"}
                ]
            )

            assert result["success"] is True
            assert captured_body[0] is not None
            assert "Comments (Fallback Mode)" in captured_body[0]
            assert "src/test.py" in captured_body[0]
            assert "Line 42" in captured_body[0]
            assert "Fix this bug" in captured_body[0]
            assert "src/utils.py" in captured_body[0]
            assert "10-15" in captured_body[0]
            assert "Refactor" in captured_body[0]


class TestPostPrReviewOtherErrors:
    """Tests for post_pr_review() error handling (non-fallback errors)"""

    def test_401_error_does_not_trigger_fallback(self):
        """GithubException(status=401) should NOT trigger fallback"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_review.side_effect = GithubException(401, {"message": "Unauthorized"}, None)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert "GitHub API error" in result["error"]
            assert result.get("downgraded") is not True
            mock_pr.create_review.assert_called_once()

    def test_403_error_does_not_trigger_fallback(self):
        """GithubException(status=403) should NOT trigger fallback"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_pr.create_review.side_effect = GithubException(403, {"message": "Forbidden"}, None)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert "GitHub API error" in result["error"]
            assert result.get("downgraded") is not True

    def test_repo_none_returns_error(self):
        """repo=None should return error='Repository not available'"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False
        )

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=None,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert result["error"] == "Repository not available"

    def test_pr_not_found_returns_error(self):
        """UnknownObjectException should return appropriate error"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = UnknownObjectException(404, {"message": "Not Found"}, None)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=99999,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}]
            )

            assert result["success"] is False
            assert "not found" in result["error"].lower()


class TestPostPrReviewCommentProcessing:
    """Tests for post_pr_review() comment processing"""

    def test_empty_comments_returns_success(self):
        """Empty comments list should return success=True"""
        mock_settings = MockSettings(enable_github_review_posting=True)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=MagicMock(),
                pr_number=123,
                comments=[]
            )

            assert result["success"] is True
            assert result["posted_count"] == 0

    def test_missing_required_fields_skipped(self):
        """Comments missing file/end_line/message should be skipped"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=True,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[
                    {"file": "test.py", "end_line": 10},
                    {"file": "test.py", "message": "No line"},
                    {"end_line": 10, "message": "No file"},
                    {"file": "test.py", "end_line": 10, "message": "Valid"}
                ]
            )

            assert result["success"] is True
            assert result["skipped_count"] == 3
            assert result["posted_count"] == 1

    def test_comments_over_max_truncated(self):
        """Comments over max_comments should be truncated"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=True,
            github_review_posting_max_comments=3
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        comments = [
            {"file": f"test{i}.py", "end_line": i + 1, "message": f"Comment {i}"}
            for i in range(10)
        ]

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=comments
            )

            assert result["success"] is True
            assert result["truncated_count"] == 7
            assert result["posted_count"] == 3

    def test_multiline_comment_sets_start_line(self):
        """Multi-line comments (start_line < end_line) should set start_line and start_side"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        captured_comments = [None]

        def capture_create_review(**kwargs):
            captured_comments[0] = kwargs.get("comments")

        mock_pr.create_review.side_effect = capture_create_review

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "start_line": 10, "end_line": 20, "message": "Multi-line"}]
            )

            assert result["success"] is True
            assert captured_comments[0] is not None
            assert len(captured_comments[0]) == 1
            comment = captured_comments[0][0]
            assert comment["line"] == 20
            assert comment["start_line"] == 10
            assert comment["start_side"] == "RIGHT"

    def test_single_line_comment_no_start_line(self):
        """Single-line comments should not have start_line"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        captured_comments = [None]

        def capture_create_review(**kwargs):
            captured_comments[0] = kwargs.get("comments")

        mock_pr.create_review.side_effect = capture_create_review

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 42, "message": "Single line"}]
            )

            assert result["success"] is True
            assert captured_comments[0] is not None
            comment = captured_comments[0][0]
            assert comment["line"] == 42
            assert "start_line" not in comment


try:
    import langgraph  # noqa: F401
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


@pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="langgraph not installed")
class TestPublisherNodeNoOp:
    """Tests for publisher_node no-op behavior"""

    def test_feature_disabled_is_pure_noop(self):
        """When ENABLE_GITHUB_REVIEW_POSTING=False, publisher_node should be pure no-op"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = False

        mock_metrics = MagicMock()

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"file": "test.py", "end_line": 10, "message": "Test"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo") as mock_get_repo:
                    from langgraph_orchestrator import publisher_node

                    result = publisher_node(state)

                    mock_get_repo.assert_not_called()
                    assert "publish_result" in result
                    assert result["publish_result"]["attempted"] is False

    def test_no_pr_number_skips_publish(self):
        """When pr_number is None, should skip publish"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()

        state = {
            "trace_id": "test-trace",
            "pr_number": None,
            "review_comments": [{"file": "test.py", "end_line": 10, "message": "Test"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo") as mock_get_repo:
                    from langgraph_orchestrator import publisher_node

                    result = publisher_node(state)

                    mock_get_repo.assert_not_called()
                    assert "No PR available" in result["messages"][-1].content

    def test_empty_review_comments_skips_publish(self):
        """When review_comments is empty, should skip publish"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo") as mock_get_repo:
                    from langgraph_orchestrator import publisher_node

                    result = publisher_node(state)

                    mock_get_repo.assert_not_called()
                    assert "No review comments" in result["messages"][-1].content

    def test_no_inline_eligible_comments_skips_publish(self):
        """When no inline-eligible comments, should skip publish"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"message": "General comment"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.is_inline_comment", return_value=False):
                    with patch("langgraph_orchestrator.get_repo") as mock_get_repo:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        mock_get_repo.assert_not_called()
                        assert "No inline-eligible" in result["messages"][-1].content


@pytest.mark.skipif(not LANGGRAPH_AVAILABLE, reason="langgraph not installed")
class TestPublisherNodeIntegration:
    """Tests for publisher_node integration with post_pr_review"""

    def test_success_sets_publish_result(self):
        """When post_pr_review returns success=True, should set publish_result correctly"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 2,
            "skipped_count": 0,
            "truncated_count": 0,
            "dry_run": False,
            "error": None
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [
                {"file": "test.py", "end_line": 10, "message": "Test 1"},
                {"file": "test.py", "end_line": 20, "message": "Test 2"}
            ],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo", return_value=mock_repo):
                    with patch("langgraph_orchestrator.post_pr_review", return_value=mock_post_result):
                        with patch("langgraph_orchestrator.is_inline_comment", return_value=True):
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            assert result["publish_result"]["success"] is True
                            assert result["publish_result"]["posted_count"] == 2
                            assert "Review published" in result["messages"][-1].content

    def test_failure_sets_error_message(self):
        """When post_pr_review returns success=False, should set error message"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": False,
            "posted_count": 0,
            "skipped_count": 0,
            "truncated_count": 0,
            "dry_run": False,
            "error": "GitHub API error"
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"file": "test.py", "end_line": 10, "message": "Test"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo", return_value=mock_repo):
                    with patch("langgraph_orchestrator.post_pr_review", return_value=mock_post_result):
                        with patch("langgraph_orchestrator.is_inline_comment", return_value=True):
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            assert result["publish_result"]["success"] is False
                            assert result["publish_result"]["error"] == "GitHub API error"
                            assert "failed" in result["messages"][-1].content.lower()

    def test_downgraded_shows_fallback_in_message(self):
        """When post_pr_review returns downgraded=True, should show FALLBACK in message"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 1,
            "skipped_count": 0,
            "truncated_count": 0,
            "dry_run": False,
            "downgraded": True,
            "error": None
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"file": "test.py", "end_line": 10, "message": "Test"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo", return_value=mock_repo):
                    with patch("langgraph_orchestrator.post_pr_review", return_value=mock_post_result):
                        with patch("langgraph_orchestrator.is_inline_comment", return_value=True):
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            assert result["publish_result"]["success"] is True
                            assert result["publish_result"]["downgraded"] is True
                            assert "FALLBACK" in result["messages"][-1].content

    def test_dry_run_shows_in_message(self):
        """When post_pr_review returns dry_run=True, should show DRY-RUN in message"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 1,
            "skipped_count": 0,
            "truncated_count": 0,
            "dry_run": True,
            "error": None
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"file": "test.py", "end_line": 10, "message": "Test"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator.metrics", mock_metrics):
                with patch("langgraph_orchestrator.get_repo", return_value=mock_repo):
                    with patch("langgraph_orchestrator.post_pr_review", return_value=mock_post_result):
                        with patch("langgraph_orchestrator.is_inline_comment", return_value=True):
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            assert result["publish_result"]["dry_run"] is True
                            assert "DRY-RUN" in result["messages"][-1].content
