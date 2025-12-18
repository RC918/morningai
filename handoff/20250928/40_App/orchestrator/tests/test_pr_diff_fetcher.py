#!/usr/bin/env python3
"""
Unit tests for PR Diff Fetcher - EPIC B Phase B-1
Issue #2595: Diff-Aware Review Plumbing

Tests for get_pr_diff() function in tools/github_api.py
"""
import sys
import os
from unittest.mock import MagicMock, patch

# Add orchestrator directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from tools.github_api import (  # noqa: E402
    get_pr_diff,
    DIFF_MAX_FILES,
    DIFF_MAX_LINES,
    DIFF_MAX_SIZE_BYTES,
    DIFF_PRIORITY_EXTENSIONS,
    DIFF_MIN_REMAINING_LINES_FOR_PARTIAL
)


class TestDiffConfiguration:
    """Test suite for diff configuration constants"""

    def test_max_files_default(self):
        """Test default max files limit"""
        assert DIFF_MAX_FILES == 20

    def test_max_lines_default(self):
        """Test default max lines limit"""
        assert DIFF_MAX_LINES == 1000

    def test_max_size_default(self):
        """Test default max size limit (100KB)"""
        assert DIFF_MAX_SIZE_BYTES == 100 * 1024

    def test_priority_extensions(self):
        """Test priority file extensions"""
        assert '.py' in DIFF_PRIORITY_EXTENSIONS
        assert '.ts' in DIFF_PRIORITY_EXTENSIONS
        assert '.tsx' in DIFF_PRIORITY_EXTENSIONS
        assert '.js' in DIFF_PRIORITY_EXTENSIONS
        assert '.jsx' in DIFF_PRIORITY_EXTENSIONS


class TestGetPrDiff:
    """Test suite for get_pr_diff function"""

    def test_repo_none_returns_error(self):
        """Test that None repo returns error"""
        result = get_pr_diff(None, 123)

        assert result["error"] == "Repository not available"
        assert result["diff"] == ""
        assert result["files"] == []
        assert result["truncated"] is False

    def test_empty_pr_returns_empty_diff(self):
        """Test PR with no changed files"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_pr.get_files.return_value = []
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        assert result["error"] is None
        assert result["diff"] == ""
        assert result["files"] == []
        assert result["truncated"] is False

    def test_single_file_diff(self):
        """Test PR with single file change"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.status = "modified"
        mock_file.additions = 5
        mock_file.deletions = 2
        mock_file.changes = 7
        mock_file.patch = "@@ -1,5 +1,8 @@\n+new line\n old line"

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        assert result["error"] is None
        assert "test.py" in result["diff"]
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "test.py"
        assert result["truncated"] is False

    def test_priority_file_ordering(self):
        """Test that priority files (.py, .ts) come before others"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create files in non-priority order
        mock_file_md = MagicMock()
        mock_file_md.filename = "README.md"
        mock_file_md.status = "modified"
        mock_file_md.additions = 1
        mock_file_md.deletions = 0
        mock_file_md.changes = 1
        mock_file_md.patch = "+doc"

        mock_file_py = MagicMock()
        mock_file_py.filename = "main.py"
        mock_file_py.status = "modified"
        mock_file_py.additions = 10
        mock_file_py.deletions = 5
        mock_file_py.changes = 15
        mock_file_py.patch = "+code"

        mock_file_ts = MagicMock()
        mock_file_ts.filename = "app.ts"
        mock_file_ts.status = "modified"
        mock_file_ts.additions = 8
        mock_file_ts.deletions = 3
        mock_file_ts.changes = 11
        mock_file_ts.patch = "+typescript"

        # Return in non-priority order
        mock_pr.get_files.return_value = [mock_file_md, mock_file_py, mock_file_ts]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        # Priority files should come first
        assert result["files"][0]["filename"] in ["main.py", "app.ts"]
        assert result["files"][-1]["filename"] == "README.md"

    def test_file_count_truncation(self):
        """Test truncation when file count exceeds limit"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create more files than the limit
        files = []
        for i in range(25):
            mock_file = MagicMock()
            mock_file.filename = f"file{i}.py"
            mock_file.status = "modified"
            mock_file.additions = 1
            mock_file.deletions = 0
            mock_file.changes = 1
            mock_file.patch = f"+line{i}"
            files.append(mock_file)

        mock_pr.get_files.return_value = files
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123, max_files=20)

        assert result["truncated"] is True
        assert len(result["files"]) == 20
        assert "file_count_exceeded" in result["truncation_info"]["truncation_reasons"]
        assert result["truncation_info"]["original_file_count"] == 25
        assert result["truncation_info"]["included_file_count"] == 20

    def test_line_count_truncation(self):
        """Test truncation when line count exceeds limit"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create a file with many lines
        mock_file = MagicMock()
        mock_file.filename = "large.py"
        mock_file.status = "modified"
        mock_file.additions = 2000
        mock_file.deletions = 0
        mock_file.changes = 2000
        mock_file.patch = "\n".join([f"+line{i}" for i in range(2000)])

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123, max_lines=100)

        assert result["truncated"] is True
        assert "line_count_exceeded" in result["truncation_info"]["truncation_reasons"]

    def test_size_truncation(self):
        """Test truncation when size exceeds limit"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create a file with large content
        mock_file = MagicMock()
        mock_file.filename = "large.py"
        mock_file.status = "modified"
        mock_file.additions = 1000
        mock_file.deletions = 0
        mock_file.changes = 1000
        mock_file.patch = "x" * 200000  # 200KB

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123, max_size_bytes=1024)

        assert result["truncated"] is True
        assert "size_exceeded" in result["truncation_info"]["truncation_reasons"]

    def test_custom_limits(self):
        """Test with custom truncation limits"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        files = []
        for i in range(10):
            mock_file = MagicMock()
            mock_file.filename = f"file{i}.py"
            mock_file.status = "modified"
            mock_file.additions = 1
            mock_file.deletions = 0
            mock_file.changes = 1
            mock_file.patch = f"+line{i}"
            files.append(mock_file)

        mock_pr.get_files.return_value = files
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123, max_files=5)

        assert len(result["files"]) == 5
        assert result["truncated"] is True

    def test_file_metadata_captured(self):
        """Test that file metadata is correctly captured"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.status = "added"
        mock_file.additions = 50
        mock_file.deletions = 0
        mock_file.changes = 50
        mock_file.patch = "+new content"

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        assert len(result["files"]) == 1
        file_info = result["files"][0]
        assert file_info["filename"] == "test.py"
        assert file_info["status"] == "added"
        assert file_info["additions"] == 50
        assert file_info["deletions"] == 0
        assert file_info["changes"] == 50

    def test_null_patch_handled(self):
        """Test that files with null patch are handled"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        mock_file = MagicMock()
        mock_file.filename = "binary.png"
        mock_file.status = "added"
        mock_file.additions = 0
        mock_file.deletions = 0
        mock_file.changes = 0
        mock_file.patch = None  # Binary files have no patch

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        assert result["error"] is None
        assert len(result["files"]) == 1

    @patch('tools.github_api.logger')
    def test_pr_not_found_error(self, mock_logger):
        """Test handling of PR not found error"""
        from github import UnknownObjectException

        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = UnknownObjectException(404, "Not Found", None)

        result = get_pr_diff(mock_repo, 999)

        assert result["error"] is not None
        assert "not found" in result["error"].lower()

    @patch('tools.github_api.logger')
    def test_rate_limit_error(self, mock_logger):
        """Test handling of rate limit error"""
        from github import RateLimitExceededException

        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = RateLimitExceededException(403, "Rate limit", None)

        result = get_pr_diff(mock_repo, 123)

        assert result["error"] is not None
        assert "rate limit" in result["error"].lower()

    @patch('tools.github_api.logger')
    def test_generic_exception_handled(self, mock_logger):
        """Test handling of generic exceptions"""
        mock_repo = MagicMock()
        mock_repo.get_pull.side_effect = Exception("Network error")

        result = get_pr_diff(mock_repo, 123)

        assert result["error"] is not None
        assert "Failed to get PR diff" in result["error"]

    def test_truncation_info_structure(self):
        """Test that truncation_info has correct structure"""
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        mock_file = MagicMock()
        mock_file.filename = "test.py"
        mock_file.status = "modified"
        mock_file.additions = 5
        mock_file.deletions = 2
        mock_file.changes = 7
        mock_file.patch = "+new line"

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        result = get_pr_diff(mock_repo, 123)

        info = result["truncation_info"]
        assert "original_file_count" in info
        assert "included_file_count" in info
        assert "original_line_count" in info
        assert "included_line_count" in info
        assert "original_size_bytes" in info
        assert "included_size_bytes" in info
        assert "truncation_reasons" in info
        assert isinstance(info["truncation_reasons"], list)

    def test_original_totals_correct_with_partial_truncation(self):
        """
        Regression test: original_line_count and original_size_bytes
        should reflect the TRUE original totals, not truncated values.

        Bug fixed: When a file was partially truncated (line limit hit mid-file),
        the truncated line count was incorrectly added to original_line_count.
        """
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create a file with 100 lines (will be truncated to 50)
        original_lines = [f"+line{i}" for i in range(100)]
        original_patch = "\n".join(original_lines)
        original_line_count = original_patch.count('\n') + 1  # 100 lines
        original_size = len(original_patch.encode('utf-8'))

        mock_file = MagicMock()
        mock_file.filename = "large.py"
        mock_file.status = "modified"
        mock_file.additions = 100
        mock_file.deletions = 0
        mock_file.changes = 100
        mock_file.patch = original_patch

        mock_pr.get_files.return_value = [mock_file]
        mock_repo.get_pull.return_value = mock_pr

        # Truncate to 50 lines
        result = get_pr_diff(mock_repo, 123, max_lines=50)

        info = result["truncation_info"]

        # Original totals should be the TRUE original values
        assert info["original_line_count"] == original_line_count
        assert info["original_size_bytes"] == original_size

        # Included totals should be truncated
        assert info["included_line_count"] <= 50
        assert result["truncated"] is True
        assert "line_count_exceeded" in info["truncation_reasons"]

    def test_original_totals_correct_with_file_count_truncation(self):
        """
        Regression test: original totals should include ALL files,
        not just included files, when file count limit is hit.
        """
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # Create 5 files, but only include 2
        files = []
        total_original_lines = 0
        total_original_size = 0

        for i in range(5):
            patch = f"+content{i}\n+more{i}"
            total_original_lines += patch.count('\n') + 1
            total_original_size += len(patch.encode('utf-8'))

            mock_file = MagicMock()
            mock_file.filename = f"file{i}.py"
            mock_file.status = "modified"
            mock_file.additions = 2
            mock_file.deletions = 0
            mock_file.changes = 2
            mock_file.patch = patch
            files.append(mock_file)

        mock_pr.get_files.return_value = files
        mock_repo.get_pull.return_value = mock_pr

        # Only include 2 files
        result = get_pr_diff(mock_repo, 123, max_files=2)

        info = result["truncation_info"]

        # Original totals should include ALL 5 files
        assert info["original_file_count"] == 5
        assert info["original_line_count"] == total_original_lines
        assert info["original_size_bytes"] == total_original_size

        # Included totals should only have 2 files
        assert info["included_file_count"] == 2
        assert result["truncated"] is True

    def test_min_remaining_lines_constant(self):
        """Test that DIFF_MIN_REMAINING_LINES_FOR_PARTIAL constant is used"""
        assert DIFF_MIN_REMAINING_LINES_FOR_PARTIAL == 10

    def test_partial_patch_not_included_when_remaining_too_small(self):
        """
        Test that partial patch is NOT included when remaining lines
        is less than or equal to DIFF_MIN_REMAINING_LINES_FOR_PARTIAL.
        """
        mock_repo = MagicMock()
        mock_pr = MagicMock()

        # First file uses up most of the budget
        mock_file1 = MagicMock()
        mock_file1.filename = "first.py"
        mock_file1.status = "modified"
        mock_file1.additions = 95
        mock_file1.deletions = 0
        mock_file1.changes = 95
        mock_file1.patch = "\n".join([f"+line{i}" for i in range(95)])

        # Second file has 20 lines but only 5 lines remain in budget
        mock_file2 = MagicMock()
        mock_file2.filename = "second.py"
        mock_file2.status = "modified"
        mock_file2.additions = 20
        mock_file2.deletions = 0
        mock_file2.changes = 20
        mock_file2.patch = "\n".join([f"+extra{i}" for i in range(20)])

        mock_pr.get_files.return_value = [mock_file1, mock_file2]
        mock_repo.get_pull.return_value = mock_pr

        # Budget is 100 lines, first file uses 95, leaving only 5
        # Since 5 <= DIFF_MIN_REMAINING_LINES_FOR_PARTIAL (10), second file should NOT be included
        result = get_pr_diff(mock_repo, 123, max_lines=100)

        # Only first file should be included
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "first.py"
        assert result["truncated"] is True


class TestDiffAwareReviewIntegration:
    """Test suite for diff-aware review integration"""

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_with_diff(self, mock_get_client):
        """Test review generation with diff content"""
        from llm_reviewer_adapter import LLMReviewerAdapter
        import json

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Code changes look good",
            "quality_score": 85,
            "severity": "low",
            "decision": "approve",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 200}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none",
            diff="--- a/test.py\n+++ b/test.py\n+new line",
            diff_truncated=False,
            diff_files=[{"filename": "test.py", "additions": 1, "deletions": 0}]
        )

        assert result["llm_used"] is True
        assert result["diff_aware"] is True

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_without_diff(self, mock_get_client):
        """Test review generation without diff (metadata-only)"""
        from llm_reviewer_adapter import LLMReviewerAdapter
        import json

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Risk assessment based on metadata",
            "quality_score": 70,
            "severity": "medium",
            "decision": "needs_changes",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 150}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none",
            diff=None,
            diff_truncated=False,
            diff_files=None
        )

        assert result["llm_used"] is True
        assert result["diff_aware"] is False

    @patch('llm_reviewer_adapter.get_client_for_component')
    def test_generate_review_empty_diff(self, mock_get_client):
        """Test review generation with empty diff string"""
        from llm_reviewer_adapter import LLMReviewerAdapter
        import json

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.provider_name = "openai"
        mock_get_client.return_value = mock_client

        valid_review = {
            "summary": "Risk assessment",
            "quality_score": 75,
            "severity": "low",
            "decision": "approve",
            "comments": []
        }

        mock_response = MagicMock()
        mock_response.content = json.dumps(valid_review)
        mock_response.provider = "openai"
        mock_response.model = "gpt-4-turbo-preview"
        mock_response.usage = {"total_tokens": 100}
        mock_client.generate.return_value = mock_response

        adapter = LLMReviewerAdapter(trace_id="test-trace")
        result = adapter.generate_review(
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add new feature",
            repo="owner/repo",
            base_quality_score=80,
            base_severity="none",
            diff="",  # Empty diff
            diff_truncated=False,
            diff_files=[]
        )

        assert result["diff_aware"] is False

    def test_fallback_result_includes_diff_aware(self):
        """Test that fallback result includes diff_aware field"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        result = adapter._get_fallback_result(80, "none")

        assert "diff_aware" in result
        assert result["diff_aware"] is False


class TestPromptGeneration:
    """Test suite for prompt generation methods"""

    def test_diff_aware_system_prompt_content(self):
        """Test diff-aware system prompt contains expected content"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        prompt = adapter._get_diff_aware_system_prompt()

        assert "actual code diff" in prompt.lower()
        assert "json" in prompt.lower()
        assert "quality_score" in prompt
        assert "severity" in prompt

    def test_metadata_only_system_prompt_content(self):
        """Test metadata-only system prompt contains expected content"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        prompt = adapter._get_metadata_only_system_prompt()

        assert "do NOT see the actual code diff" in prompt
        assert "json" in prompt.lower()
        assert "quality_score" in prompt

    def test_diff_aware_user_prompt_includes_diff(self):
        """Test diff-aware user prompt includes diff content"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        diff_content = "--- a/test.py\n+++ b/test.py\n+new line"
        prompt = adapter._build_diff_aware_user_prompt(
            repo="owner/repo",
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add feature",
            diff=diff_content,
            diff_truncated=False,
            diff_files=[{"filename": "test.py", "additions": 1, "deletions": 0}]
        )

        assert diff_content in prompt
        assert "test.py" in prompt
        assert "owner/repo" in prompt

    def test_diff_aware_user_prompt_truncation_warning(self):
        """Test diff-aware user prompt shows truncation warning"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        prompt = adapter._build_diff_aware_user_prompt(
            repo="owner/repo",
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add feature",
            diff="some diff",
            diff_truncated=True,
            diff_files=[]
        )

        assert "truncated" in prompt.lower()

    def test_metadata_only_user_prompt_no_diff(self):
        """Test metadata-only user prompt does not include diff"""
        from llm_reviewer_adapter import LLMReviewerAdapter

        adapter = LLMReviewerAdapter.__new__(LLMReviewerAdapter)
        adapter.trace_id = "test"
        adapter.llm_client = None

        prompt = adapter._build_metadata_only_user_prompt(
            repo="owner/repo",
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            ci_state="success",
            goal="Add feature"
        )

        assert "cannot see the actual code changes" in prompt.lower()
        assert "```diff" not in prompt
