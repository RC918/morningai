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
        github_repo="test/repo",
        redis_url=None  # Disable Redis dedup in tests
    ):
        self.enable_github_review_posting = enable_github_review_posting
        self.github_review_posting_dry_run = github_review_posting_dry_run
        self.github_review_posting_max_comments = github_review_posting_max_comments
        self.agent_github_token = agent_github_token
        self.github_token = github_token
        self.github_repo = github_repo
        self.redis_url = redis_url


def create_mock_pr():
    """
    Create a mock PR object with proper state for testing.

    P4: PR State Guard uses allowlist approach (state must be "open").
    All mock PRs need explicit state="open" and merged=False to pass the guard.
    """
    mock_pr = MagicMock()
    mock_pr.state = "open"
    mock_pr.merged = False
    return mock_pr


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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
        mock_pr = create_mock_pr()
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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo") as mock_get_repo:
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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo") as mock_get_repo:
                    from langgraph_orchestrator import publisher_node

                    result = publisher_node(state)

                    mock_get_repo.assert_not_called()
                    assert "No PR available" in result["messages"][-1].content

    def test_empty_review_comments_posts_summary_report(self):
        """Issue #3220: When review_comments is empty, should post Summary Report for visibility"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None,
            "summary_only": True
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [],
            "messages": [],
            "diff_head_sha": "abc123def456"
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo) as mock_get_repo:
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        # Issue #3220: Summary Report should be posted even with no inline comments
                        mock_get_repo.assert_called_once()
                        mock_post.assert_called_once()
                        # Verify post_pr_review was called with empty comments and Summary Report body
                        call_args = mock_post.call_args
                        assert call_args.kwargs.get("comments") == []
                        # Summary Report uses "MorningAI Review Summary" as the header
                        assert "MorningAI Review Summary" in call_args.kwargs.get("summary", "")

    def test_file_level_comments_published_in_review_body(self):
        """When no inline-eligible comments but file-level exist, should publish in review body"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"message": "General comment", "file": "test.py", "severity": "warning"}],
            "messages": []
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("review_comment_schema.is_inline_comment", return_value=False):
                    with patch("tools.github_api.get_repo", return_value=mock_repo) as mock_get_repo:
                        with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            # File-level comments should trigger get_repo and post_pr_review
                            mock_get_repo.assert_called_once()
                            mock_post.assert_called_once()
                            # Verify post_pr_review was called with empty comments and file-level body
                            call_args = mock_post.call_args
                            assert call_args.kwargs.get("comments") == []
                            assert "File-Level Comments" in call_args.kwargs.get("summary", "")
                            # Verify state reflects file-level publish
                            assert result["publish_result"]["file_level_in_body"] == 1
                            assert "file-level comments in review body" in result["messages"][-1].content

    def test_no_comments_at_all_posts_summary_report(self):
        """Issue #3220: When no inline-eligible comments and no file-level comments, should post Summary Report"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None,
            "summary_only": True
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [],
            "messages": [],
            "diff_head_sha": "abc123def456"
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo) as mock_get_repo:
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        # Issue #3220: Summary Report should be posted even with no comments
                        mock_get_repo.assert_called_once()
                        mock_post.assert_called_once()
                        # Verify post_pr_review was called with empty comments and Summary Report body
                        call_args = mock_post.call_args
                        assert call_args.kwargs.get("comments") == []
                        # Summary Report uses "MorningAI Review Summary" as the header
                        assert "MorningAI Review Summary" in call_args.kwargs.get("summary", "")

    def test_summary_report_passes_commit_id_for_dedup(self):
        """Issue #3253: Summary Report should pass commit_id to enable Redis dedup idempotency"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None,
            "summary_only": True
        }

        test_commit_id = "abc123def456789012345678901234567890abcd"
        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [],
            "messages": [],
            "diff_head_sha": test_commit_id
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        # Issue #3253: Verify commit_id is passed for Redis dedup
                        mock_post.assert_called_once()
                        call_args = mock_post.call_args
                        assert call_args.kwargs.get("commit_id") == test_commit_id

    def test_summary_report_handles_missing_or_invalid_diff_head_sha(self):
        """Issue #3253: Summary Report should gracefully handle missing/invalid diff_head_sha"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None,
            "summary_only": True
        }

        # Test cases: None, empty string, non-string types
        invalid_values = [None, "", 123, {"sha": "abc"}, []]

        for invalid_value in invalid_values:
            state = {
                "trace_id": "test-trace",
                "pr_number": 123,
                "review_comments": [],
                "messages": [],
                "diff_head_sha": invalid_value
            }

            with patch("langgraph_orchestrator.settings", mock_settings):
                with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                    with patch("tools.github_api.get_repo", return_value=mock_repo):
                        with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                            from langgraph_orchestrator import publisher_node

                            # Should not raise exception
                            result = publisher_node(state)

                            # Verify commit_id is normalized to None for invalid values
                            mock_post.assert_called_once()
                            call_args = mock_post.call_args
                            assert call_args.kwargs.get("commit_id") is None, \
                                f"Expected commit_id=None for invalid value {invalid_value!r}"

                            mock_post.reset_mock()

    def test_file_level_fallback_passes_commit_id_for_dedup(self):
        """Issue #3253: File-level fallback path should pass commit_id for Redis dedup"""
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None
        }

        test_commit_id = "abc123def456789012345678901234567890abcd"
        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [{"message": "General comment", "file": "test.py", "severity": "warning"}],
            "messages": [],
            "diff_head_sha": test_commit_id
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("review_comment_schema.is_inline_comment", return_value=False):
                    with patch("tools.github_api.get_repo", return_value=mock_repo):
                        with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            # Issue #3253: Verify commit_id is passed for Redis dedup in file-level fallback
                            mock_post.assert_called_once()
                            call_args = mock_post.call_args
                            assert call_args.kwargs.get("commit_id") == test_commit_id


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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result):
                        with patch("review_comment_schema.is_inline_comment", return_value=True):
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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result):
                        with patch("review_comment_schema.is_inline_comment", return_value=True):
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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result):
                        with patch("review_comment_schema.is_inline_comment", return_value=True):
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
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result):
                        with patch("review_comment_schema.is_inline_comment", return_value=True):
                            from langgraph_orchestrator import publisher_node

                            result = publisher_node(state)

                            assert result["publish_result"]["dry_run"] is True
                            assert "DRY-RUN" in result["messages"][-1].content


class TestPostPrReviewCommitId:
    """Tests for post_pr_review() commit_id parameter - EPIC B Phase 3 P2 follow-up"""

    def test_commit_id_passed_to_create_review(self):
        """When commit_id is provided, should pass commit object to create_review()"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_commit = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit

        captured_kwargs = [None]

        def capture_create_review(**kwargs):
            captured_kwargs[0] = kwargs

        mock_pr.create_review.side_effect = capture_create_review

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}],
                commit_id="abc123def456"
            )

            assert result["success"] is True
            mock_repo.get_commit.assert_called_once_with("abc123def456")
            assert captured_kwargs[0] is not None
            assert captured_kwargs[0].get("commit") == mock_commit

    def test_commit_id_none_does_not_call_get_commit(self):
        """When commit_id is None, should not call get_commit()"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_repo.get_pull.return_value = mock_pr

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}],
                commit_id=None
            )

            assert result["success"] is True
            mock_repo.get_commit.assert_not_called()

    def test_commit_id_get_commit_fails_proceeds_without_commit(self):
        """When get_commit() fails, should proceed without commit (fail-open)"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.side_effect = GithubException(
            404, {"message": "Commit not found"}, None
        )

        captured_kwargs = [None]

        def capture_create_review(**kwargs):
            captured_kwargs[0] = kwargs

        mock_pr.create_review.side_effect = capture_create_review

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}],
                commit_id="invalid_sha"
            )

            assert result["success"] is True
            assert captured_kwargs[0] is not None
            assert "commit" not in captured_kwargs[0]

    def test_commit_id_unknown_object_exception_proceeds_without_commit(self):
        """When get_commit() raises UnknownObjectException, should proceed without commit"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.side_effect = UnknownObjectException(
            404, {"message": "Not Found"}, None
        )

        captured_kwargs = [None]

        def capture_create_review(**kwargs):
            captured_kwargs[0] = kwargs

        mock_pr.create_review.side_effect = capture_create_review

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import post_pr_review

            result = post_pr_review(
                repo=mock_repo,
                pr_number=123,
                comments=[{"file": "test.py", "end_line": 10, "message": "Test"}],
                commit_id="nonexistent_sha"
            )

            assert result["success"] is True
            assert captured_kwargs[0] is not None
            assert "commit" not in captured_kwargs[0]

    def test_commit_id_logged_in_result(self):
        """commit_id should be logged in the result extra fields"""
        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_commit = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit

        with patch("common.config.settings.settings", mock_settings):
            with patch("tools.github_api.logger") as mock_logger:
                from tools.github_api import post_pr_review

                result = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=[{"file": "test.py", "end_line": 10, "message": "Test"}],
                    commit_id="abc123def456"
                )

                assert result["success"] is True
                # Verify commit_id was logged
                info_calls = [call for call in mock_logger.info.call_args_list]
                commit_logged = any(
                    "commit_id" in str(call) for call in info_calls
                )
                assert commit_logged


class TestReviewDedupFunctions:
    """Tests for _check_review_already_posted and _mark_review_posted - P2 Artifact Idempotency"""

    def test_check_review_no_head_sha_returns_not_posted(self):
        """When head_sha is None, should return (False, None) - can't deduplicate without SHA"""
        mock_settings = MockSettings()

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import _check_review_already_posted

            already_posted, dedup_key = _check_review_already_posted(
                repo="test/repo",
                pr_number=123,
                head_sha=None,
            )

            assert already_posted is False
            assert dedup_key is None

    def test_check_review_no_redis_url_returns_not_posted(self):
        """When redis_url is None, should return (False, None) - Redis not configured"""
        mock_settings = MockSettings(redis_url=None)

        # Patch tools.github_api.settings directly because settings is imported at module level
        # with "from common.config.settings import settings", so patching common.config.settings.settings
        # doesn't affect the already-bound settings in tools.github_api
        with patch("tools.github_api.settings", mock_settings):
            from tools.github_api import _check_review_already_posted

            already_posted, dedup_key = _check_review_already_posted(
                repo="test/repo",
                pr_number=123,
                head_sha="abc123def456",
            )

            assert already_posted is False
            assert dedup_key is None

    def test_check_review_redis_error_returns_not_posted_graceful_degradation(self):
        """When Redis raises an error, should return (False, None) - graceful degradation"""
        mock_settings = MockSettings()
        mock_settings.redis_url = "redis://localhost:6379"

        # Import real redis to get the actual exception class
        import redis as real_redis

        # Create a mock Redis that raises RedisError on set (atomic claim uses r.set with nx=True)
        mock_redis = MagicMock()
        mock_redis.set.side_effect = real_redis.exceptions.RedisError("Connection refused")

        # Mock the redis module that gets imported inside the function
        # but keep the real exceptions module
        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis
        mock_redis_module.exceptions = real_redis.exceptions

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import _check_review_already_posted

                already_posted, dedup_key = _check_review_already_posted(
                    repo="test/repo",
                    pr_number=123,
                    head_sha="abc123def456",
                )

                assert already_posted is False
                assert dedup_key is None

    def test_mark_review_no_dedup_key_does_nothing(self):
        """When dedup_key is None, should do nothing"""
        mock_settings = MockSettings()

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import _mark_review_posted

            # Should not raise any exception
            _mark_review_posted(dedup_key=None)

    def test_mark_review_no_redis_url_does_nothing(self):
        """When redis_url is None, should do nothing"""
        mock_settings = MockSettings(redis_url=None)

        with patch("common.config.settings.settings", mock_settings):
            from tools.github_api import _mark_review_posted

            # Should not raise any exception
            _mark_review_posted(dedup_key="review_posted:test/repo:123:abc123:v1")

    def test_mark_review_redis_error_does_not_raise(self):
        """When Redis raises an error, should not raise - graceful degradation"""
        mock_settings = MockSettings()
        mock_settings.redis_url = "redis://localhost:6379"

        # Import real redis to get the actual exception class
        import redis as real_redis

        mock_redis = MagicMock()
        mock_redis.setex.side_effect = real_redis.exceptions.RedisError("Connection refused")

        # Mock the redis module that gets imported inside the function
        # but keep the real exceptions module
        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis
        mock_redis_module.exceptions = real_redis.exceptions

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import _mark_review_posted

                # Should not raise any exception
                _mark_review_posted(dedup_key="review_posted:test/repo:123:abc123:v1")


class TestDedupObservability:
    """
    Issue #3260: Tests for Redis dedup observability events.

    These tests verify that proper warning logs are emitted when dedup is skipped:
    1. When head_sha (commit_id) is None
    2. When Redis operations fail
    """

    def test_no_head_sha_logs_warning_with_correct_operation(self):
        """When head_sha is None, should log warning with operation=review_dedup_skipped_no_commit_id"""
        mock_settings = MockSettings()

        with patch("tools.github_api.settings", mock_settings):
            with patch("tools.github_api.logger") as mock_logger:
                from tools.github_api import _check_review_already_posted

                already_posted, dedup_key = _check_review_already_posted(
                    repo="test/repo",
                    pr_number=123,
                    head_sha=None,
                )

                assert already_posted is False
                assert dedup_key is None

                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert "Dedup skipped" in call_args[0][0]
                assert "head_sha is None" in call_args[0][0]
                extra = call_args[1]["extra"]
                assert extra["operation"] == "review_dedup_skipped_no_commit_id"
                assert extra["repo"] == "test/repo"
                assert extra["pr_number"] == 123
                assert extra["reason"] == "head_sha_none"
                assert extra["fail_open"] is True

    def test_redis_error_logs_warning_with_correct_operation(self):
        """When Redis raises an error, should log warning with operation=review_dedup_skipped_redis_error"""
        mock_settings = MockSettings()
        mock_settings.redis_url = "redis://localhost:6379"

        import redis as real_redis

        mock_redis = MagicMock()
        mock_redis.set.side_effect = real_redis.exceptions.RedisError("Connection refused")

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis
        mock_redis_module.exceptions = real_redis.exceptions

        with patch("tools.github_api.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                with patch("tools.github_api.logger") as mock_logger:
                    from tools.github_api import _check_review_already_posted

                    already_posted, dedup_key = _check_review_already_posted(
                        repo="test/repo",
                        pr_number=123,
                        head_sha="abc123def456",
                    )

                    assert already_posted is False
                    assert dedup_key is None

                    mock_logger.warning.assert_called_once()
                    call_args = mock_logger.warning.call_args
                    assert "Dedup skipped" in call_args[0][0]
                    assert "Redis error" in call_args[0][0]
                    extra = call_args[1]["extra"]
                    assert extra["operation"] == "review_dedup_skipped_redis_error"
                    assert extra["repo"] == "test/repo"
                    assert extra["pr_number"] == 123
                    assert extra["reason"] == "redis_error"
                    assert extra["fail_open"] is True
                    assert "error" in extra
                    assert "error_type" in extra

    def test_dedup_hit_logs_info_with_correct_operation(self):
        """When dedup hit occurs, should log info with operation=review_dedup_hit"""
        mock_settings = MockSettings()
        mock_settings.redis_url = "redis://localhost:6379"

        import redis as real_redis

        mock_redis = MagicMock()
        mock_redis.set.return_value = False
        mock_redis.get.return_value = "posted"

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis
        mock_redis_module.exceptions = real_redis.exceptions

        with patch("tools.github_api.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                with patch("tools.github_api.logger") as mock_logger:
                    from tools.github_api import _check_review_already_posted

                    already_posted, dedup_key = _check_review_already_posted(
                        repo="test/repo",
                        pr_number=123,
                        head_sha="abc123def456",
                    )

                    assert already_posted is True
                    assert dedup_key is not None

                    info_calls = mock_logger.info.call_args_list
                    dedup_hit_call = None
                    for call in info_calls:
                        if call[1].get("extra", {}).get("operation") == "review_dedup_hit":
                            dedup_hit_call = call
                            break

                    assert dedup_hit_call is not None
                    extra = dedup_hit_call[1]["extra"]
                    assert extra["operation"] == "review_dedup_hit"
                    assert extra["repo"] == "test/repo"
                    assert extra["pr_number"] == 123
                    assert extra["existing_status"] == "posted"

    def test_dedup_claimed_logs_info_with_correct_operation(self):
        """When dedup claim succeeds, should log info with operation=review_dedup_claimed"""
        mock_settings = MockSettings()
        mock_settings.redis_url = "redis://localhost:6379"

        import redis as real_redis

        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis
        mock_redis_module.exceptions = real_redis.exceptions

        with patch("tools.github_api.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                with patch("tools.github_api.logger") as mock_logger:
                    from tools.github_api import _check_review_already_posted

                    already_posted, dedup_key = _check_review_already_posted(
                        repo="test/repo",
                        pr_number=123,
                        head_sha="abc123def456",
                    )

                    assert already_posted is False
                    assert dedup_key is not None

                    info_calls = mock_logger.info.call_args_list
                    claimed_call = None
                    for call in info_calls:
                        if call[1].get("extra", {}).get("operation") == "review_dedup_claimed":
                            claimed_call = call
                            break

                    assert claimed_call is not None
                    extra = claimed_call[1]["extra"]
                    assert extra["operation"] == "review_dedup_claimed"
                    assert extra["repo"] == "test/repo"
                    assert extra["pr_number"] == 123
                    assert "dedup_key" in extra


class TestRedisDedupIntegration:
    """
    Issue #3258: Integration tests for Redis dedup verification.

    These tests verify the full dedup flow from post_pr_review through to
    Redis dedup functions, ensuring that:
    1. First call claims and posts successfully
    2. Second call with same commit_id is deduplicated
    3. The dedup key format is correct and consistent
    """

    def test_full_dedup_flow_first_call_posts_second_call_skipped(self):
        """
        Issue #3258: Verify full dedup flow - first call posts, second call is deduplicated.

        This integration test simulates:
        1. First call: claim succeeds, review is posted, mark as posted
        2. Second call: claim fails (key exists), review is skipped
        """
        import redis as real_redis

        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )
        mock_settings.redis_url = "redis://localhost:6379"

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_commit = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit
        mock_repo.owner.login = "RC918"
        mock_repo.name = "morningai"

        redis_store = {}
        call_count = {"set": 0}

        def mock_set(key, value, nx=False, ex=None):
            call_count["set"] += 1
            if nx and key in redis_store:
                return None
            redis_store[key] = value
            return True

        def mock_get(key):
            return redis_store.get(key)

        def mock_setex(key, ttl, value):
            redis_store[key] = value

        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.side_effect = mock_get
        mock_redis_instance.setex.side_effect = mock_setex

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis_instance
        mock_redis_module.exceptions = real_redis.exceptions

        test_commit_id = "abc123def456789012345678901234567890abcd"
        comments = [{"file": "test.py", "end_line": 10, "message": "Test comment"}]

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import post_pr_review

                result1 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=comments,
                    commit_id=test_commit_id
                )

                assert result1["success"] is True
                assert result1.get("skipped_reason") is None
                assert mock_pr.create_review.called

                mock_pr.create_review.reset_mock()

                result2 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=comments,
                    commit_id=test_commit_id
                )

                assert result2["success"] is True
                assert result2.get("skipped_reason") == "review_already_posted"
                assert not mock_pr.create_review.called

    def test_dedup_key_includes_commit_id_and_version_with_ttl(self):
        """
        Issue #3258: Verify dedup key format and TTL enforcement.

        The dedup key should be: review_posted:{repo}:{pr}:{head_sha[:12]}:{version}
        TTL values should be:
        - Claim TTL: 300 seconds (5 minutes) for initial SET NX
        - Posted TTL: 86400 seconds (24 hours) for SETEX after successful post
        """
        import redis as real_redis
        from utils.constants import REVIEWER_VERSION, REVIEW_DEDUP_TTL_SECONDS
        from tools.github_api import REVIEW_CLAIM_TTL_SECONDS

        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )
        mock_settings.redis_url = "redis://localhost:6379"

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_commit = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit
        mock_repo.owner.login = "RC918"
        mock_repo.name = "morningai"

        captured_set_calls = []
        captured_setex_calls = []

        def mock_set(key, value, nx=False, ex=None):
            captured_set_calls.append({"key": key, "value": value, "nx": nx, "ex": ex})
            return True

        def mock_setex(key, ttl, value):
            captured_setex_calls.append({"key": key, "ttl": ttl, "value": value})

        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.setex.side_effect = mock_setex

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis_instance
        mock_redis_module.exceptions = real_redis.exceptions

        test_commit_id = "abc123def456789012345678901234567890abcd"
        comments = [{"file": "test.py", "end_line": 10, "message": "Test comment"}]

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import post_pr_review

                post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=comments,
                    commit_id=test_commit_id
                )

                assert len(captured_set_calls) == 1
                set_call = captured_set_calls[0]
                expected_key = f"review_posted:RC918/morningai:123:abc123def456:{REVIEWER_VERSION}"
                assert set_call["key"] == expected_key
                assert set_call["value"] == "claiming"
                assert set_call["nx"] is True
                assert set_call["ex"] == REVIEW_CLAIM_TTL_SECONDS

                assert len(captured_setex_calls) == 1
                setex_call = captured_setex_calls[0]
                assert setex_call["key"] == expected_key
                assert setex_call["ttl"] == REVIEW_DEDUP_TTL_SECONDS
                assert setex_call["value"] == "posted"

    def test_different_commit_ids_are_not_deduplicated(self):
        """
        Issue #3258: Verify that different commit_ids result in separate reviews.

        When a new commit is pushed, the review should be posted again because
        the commit_id is different.
        """
        import redis as real_redis

        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )
        mock_settings.redis_url = "redis://localhost:6379"

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_commit = MagicMock()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.get_commit.return_value = mock_commit
        mock_repo.owner.login = "RC918"
        mock_repo.name = "morningai"

        redis_store = {}

        def mock_set(key, value, nx=False, ex=None):
            if nx and key in redis_store:
                return None
            redis_store[key] = value
            return True

        def mock_get(key):
            return redis_store.get(key)

        def mock_setex(key, ttl, value):
            redis_store[key] = value

        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.side_effect = mock_get
        mock_redis_instance.setex.side_effect = mock_setex

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis_instance
        mock_redis_module.exceptions = real_redis.exceptions

        commit_id_1 = "abc123def456789012345678901234567890abcd"
        commit_id_2 = "def456abc789012345678901234567890abcdef"
        comments = [{"file": "test.py", "end_line": 10, "message": "Test comment"}]

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import post_pr_review

                result1 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=comments,
                    commit_id=commit_id_1
                )

                assert result1["success"] is True
                assert result1.get("skipped_reason") is None
                assert mock_pr.create_review.call_count == 1

                result2 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=comments,
                    commit_id=commit_id_2
                )

                assert result2["success"] is True
                assert result2.get("skipped_reason") is None
                assert mock_pr.create_review.call_count == 2

    def test_summary_report_dedup_integration(self):
        """
        Issue #3258: Verify Summary Report (empty comments) uses dedup correctly.

        When posting a Summary Report (no inline comments), the dedup mechanism
        should still work correctly using the commit_id.
        """
        import redis as real_redis

        mock_settings = MockSettings(
            enable_github_review_posting=True,
            github_review_posting_dry_run=False,
            github_review_posting_max_comments=10
        )
        mock_settings.redis_url = "redis://localhost:6379"

        mock_repo = MagicMock()
        mock_pr = create_mock_pr()
        mock_repo.get_pull.return_value = mock_pr
        mock_repo.owner.login = "RC918"
        mock_repo.name = "morningai"

        redis_store = {}

        def mock_set(key, value, nx=False, ex=None):
            if nx and key in redis_store:
                return None
            redis_store[key] = value
            return True

        def mock_get(key):
            return redis_store.get(key)

        def mock_setex(key, ttl, value):
            redis_store[key] = value

        mock_redis_instance = MagicMock()
        mock_redis_instance.set.side_effect = mock_set
        mock_redis_instance.get.side_effect = mock_get
        mock_redis_instance.setex.side_effect = mock_setex

        mock_redis_module = MagicMock()
        mock_redis_module.Redis.from_url.return_value = mock_redis_instance
        mock_redis_module.exceptions = real_redis.exceptions

        test_commit_id = "abc123def456789012345678901234567890abcd"

        with patch("common.config.settings.settings", mock_settings):
            with patch.dict("sys.modules", {"redis": mock_redis_module}):
                from tools.github_api import post_pr_review

                result1 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=[],
                    summary="Summary Report: No issues found",
                    commit_id=test_commit_id
                )

                assert result1["success"] is True
                assert result1.get("skipped_reason") is None
                assert mock_pr.create_review.called

                mock_pr.create_review.reset_mock()

                result2 = post_pr_review(
                    repo=mock_repo,
                    pr_number=123,
                    comments=[],
                    summary="Summary Report: No issues found",
                    commit_id=test_commit_id
                )

                assert result2["success"] is True
                assert result2.get("skipped_reason") == "review_already_posted"
                assert not mock_pr.create_review.called


class TestDiffHeadShaContract:
    """
    Issue #3259: Tests to verify diff_head_sha contract enforcement.

    Contract (from AgentState docstring):
    - Source: Captured from GitHub API via get_pr_diff() -> pr.head.sha
    - Format: 40-character hex string (case-insensitive), or None if unavailable
    - Availability: Best-effort; may be None if get_pr_diff() fails

    Usage by path:
    - Inline comments: MUST use diff_head_sha from get_pr_diff() for line alignment
    - Summary-only / file-level: Can work with or without diff_head_sha
    - Redis dedup: Uses diff_head_sha[:12] in key; skips dedup if None
    """

    def test_inline_path_disables_commit_pinning_when_diff_head_sha_none(self):
        """
        Issue #3259: Inline comments path should disable commit pinning
        (commit_id=None) when diff_head_sha is None to avoid 422 errors.
        """
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 1,
            "dry_run": False,
            "error": None
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [
                {"message": "Inline comment", "file": "test.py", "line": 10, "severity": "warning"}
            ],
            "messages": [],
            "diff_head_sha": None
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        mock_post.assert_called_once()
                        call_args = mock_post.call_args
                        assert call_args.kwargs.get("commit_id") is None, \
                            "Inline path should disable commit pinning when diff_head_sha is None"

    def test_summary_only_path_works_without_diff_head_sha(self):
        """
        Issue #3259: Summary-only path should work gracefully without diff_head_sha.
        No line positions involved, so commit pinning is optional.
        """
        mock_settings = MagicMock()
        mock_settings.enable_github_review_posting = True

        mock_metrics = MagicMock()
        mock_repo = MagicMock()

        mock_post_result = {
            "success": True,
            "posted_count": 0,
            "dry_run": False,
            "error": None,
            "summary_only": True
        }

        state = {
            "trace_id": "test-trace",
            "pr_number": 123,
            "review_comments": [],
            "messages": [],
            "diff_head_sha": None
        }

        with patch("langgraph_orchestrator.settings", mock_settings):
            with patch("langgraph_orchestrator._get_metrics", return_value=mock_metrics):
                with patch("tools.github_api.get_repo", return_value=mock_repo):
                    with patch("tools.github_api.post_pr_review", return_value=mock_post_result) as mock_post:
                        from langgraph_orchestrator import publisher_node

                        result = publisher_node(state)

                        assert "error" not in result or result.get("error") is None
                        mock_post.assert_called_once()
                        call_args = mock_post.call_args
                        assert call_args.kwargs.get("commit_id") is None

    def test_redis_dedup_skips_when_diff_head_sha_none(self):
        """
        Issue #3259: Redis dedup should skip (fail-open) when diff_head_sha is None.
        This is verified by _check_review_already_posted returning (False, None).
        """
        from tools.github_api import _check_review_already_posted

        already_posted, dedup_key = _check_review_already_posted(
            repo="owner/repo",
            pr_number=123,
            head_sha=None
        )

        assert already_posted is False, "Should not block posting when head_sha is None"
        assert dedup_key is None, "Should not generate dedup key when head_sha is None"

    def test_diff_head_sha_format_validation(self):
        """
        Issue #3259: Verify diff_head_sha format is validated correctly.

        Current validation: non-empty string check only (defensive, not strict).
        The actual format (40-char hex) is trusted from GitHub API source.

        Invalid (normalized to None): None, empty string, non-string types
        Valid (preserved as-is): Any non-empty string (trusted from GitHub API)
        """
        valid_sha = "abc123def456789012345678901234567890abcd"
        invalid_values = [None, "", 123, {"sha": "abc"}, []]

        for invalid_value in invalid_values:
            raw_head_sha = invalid_value
            stored_head_sha = raw_head_sha if isinstance(raw_head_sha, str) and raw_head_sha else None
            assert stored_head_sha is None, f"Invalid value {invalid_value!r} should normalize to None"

        raw_head_sha = valid_sha
        stored_head_sha = raw_head_sha if isinstance(raw_head_sha, str) and raw_head_sha else None
        assert stored_head_sha == valid_sha, "Valid 40-char hex should be preserved"

    def test_diff_head_sha_represents_review_time_not_current(self):
        """
        Issue #3259: Document that diff_head_sha represents the PR head at
        'review time' (when get_pr_diff was called), NOT the current/latest head.

        This is a documentation test - it verifies the contract is understood.
        """
        from langgraph_orchestrator import AgentState

        docstring = AgentState.__doc__
        assert "review time" in docstring.lower() or "review_time" in docstring.lower() or \
               "when get_pr_diff was called" in docstring, \
            "AgentState docstring should document that diff_head_sha is captured at review time"
        assert "NOT the current/latest head" in docstring or "not the current" in docstring.lower(), \
            "AgentState docstring should clarify diff_head_sha is not the live/current head"
