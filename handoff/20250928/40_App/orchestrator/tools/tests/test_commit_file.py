"""Tests for commit_file error handling and retry logic.

Issue #3216: Commit Conflict Handling and Retry Logic for SimpleCoder

Tests cover:
- 409 Conflict errors (SHA mismatch) - fail fast, no retry
- 403 Permission denied errors - fail fast, no retry
- 5xx/429 Transient errors - retry with exponential backoff
- Successful file updates and creates
- CommitResult class behavior
"""
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.github_api import (
    commit_file,
    CommitResult,
    _classify_github_error,
    _is_transient_error,
    _is_rate_limit_error,
    _extract_commit_sha,
)
from github import GithubException


class TestCommitResult:
    """Tests for CommitResult class"""

    def test_success_status(self):
        """Test CommitResult with success status"""
        result = CommitResult(CommitResult.SUCCESS, "Updated file", "abc123")
        assert result.success is True
        assert result.status == "success"
        assert result.message == "Updated file"
        assert result.sha == "abc123"

    def test_conflict_status(self):
        """Test CommitResult with conflict status"""
        result = CommitResult(CommitResult.CONFLICT, "SHA mismatch")
        assert result.success is False
        assert result.status == "conflict"
        assert result.message == "SHA mismatch"

    def test_permission_denied_status(self):
        """Test CommitResult with permission denied status"""
        result = CommitResult(CommitResult.PERMISSION_DENIED, "Branch protected")
        assert result.success is False
        assert result.status == "permission_denied"

    def test_transient_error_status(self):
        """Test CommitResult with transient error status"""
        result = CommitResult(CommitResult.TRANSIENT_ERROR, "Server error")
        assert result.success is False
        assert result.status == "transient_error"

    def test_repr(self):
        """Test CommitResult string representation"""
        result = CommitResult(CommitResult.SUCCESS, "test message")
        assert "success" in repr(result)
        assert "test message" in repr(result)


class TestIsTransientError:
    """Tests for _is_transient_error helper"""

    def test_500_is_transient(self):
        assert _is_transient_error(500) is True

    def test_502_is_transient(self):
        assert _is_transient_error(502) is True

    def test_503_is_transient(self):
        assert _is_transient_error(503) is True

    def test_429_is_transient(self):
        assert _is_transient_error(429) is True

    def test_409_is_not_transient(self):
        assert _is_transient_error(409) is False

    def test_403_is_not_transient(self):
        assert _is_transient_error(403) is False

    def test_404_is_not_transient(self):
        assert _is_transient_error(404) is False

    def test_200_is_not_transient(self):
        assert _is_transient_error(200) is False

    def test_408_is_transient(self):
        """Test 408 Request Timeout is transient (Issue #3230)"""
        assert _is_transient_error(408) is True

    def test_401_is_not_transient(self):
        """Test 401 Unauthorized is not transient (Issue #3230)"""
        assert _is_transient_error(401) is False

    def test_422_is_not_transient(self):
        """Test 422 Unprocessable Entity is not transient (Issue #3230)"""
        assert _is_transient_error(422) is False


class TestIsRateLimitError:
    """Tests for _is_rate_limit_error helper (Issue #3230)"""

    def test_rate_limit_in_message(self):
        """Test detection of rate limit in error message"""
        assert _is_rate_limit_error("API rate limit exceeded", {}) is True

    def test_secondary_rate_limit_in_message(self):
        """Test detection of secondary rate limit in error message"""
        assert _is_rate_limit_error("You have exceeded a secondary rate limit", {}) is True

    def test_rate_limit_case_insensitive(self):
        """Test rate limit detection is case insensitive"""
        assert _is_rate_limit_error("RATE LIMIT exceeded", {}) is True

    def test_rate_limit_from_headers(self):
        """Test detection of rate limit from x-ratelimit-remaining header"""
        headers = {"x-ratelimit-remaining": "0"}
        assert _is_rate_limit_error("Some error", headers) is True

    def test_not_rate_limit_with_remaining_quota(self):
        """Test non-rate-limit error with remaining quota"""
        headers = {"x-ratelimit-remaining": "100"}
        assert _is_rate_limit_error("Permission denied", headers) is False

    def test_not_rate_limit_no_headers(self):
        """Test non-rate-limit error without headers"""
        assert _is_rate_limit_error("Permission denied", {}) is False

    def test_not_rate_limit_none_headers(self):
        """Test non-rate-limit error with None headers"""
        assert _is_rate_limit_error("Permission denied", None) is False


class TestExtractCommitSha:
    """Tests for _extract_commit_sha helper - handles both PyGithub objects and dicts"""

    def test_extract_sha_from_pygithub_commit_object(self):
        """Test extracting SHA from PyGithub Commit object (has .sha attribute)"""
        mock_commit = MagicMock()
        mock_commit.sha = "abc123def456"
        result = {"commit": mock_commit}
        assert _extract_commit_sha(result) == "abc123def456"

    def test_extract_sha_from_dict_commit(self):
        """Test extracting SHA from dict-based commit (has ['sha'] key)"""
        result = {"commit": {"sha": "xyz789"}}
        assert _extract_commit_sha(result) == "xyz789"

    def test_extract_sha_returns_empty_for_none_result(self):
        """Test that None result returns empty string"""
        assert _extract_commit_sha(None) == ""

    def test_extract_sha_returns_empty_for_non_dict_result(self):
        """Test that non-dict result returns empty string"""
        assert _extract_commit_sha("not a dict") == ""
        assert _extract_commit_sha(123) == ""
        assert _extract_commit_sha([]) == ""

    def test_extract_sha_returns_empty_for_missing_commit_key(self):
        """Test that missing 'commit' key returns empty string"""
        assert _extract_commit_sha({}) == ""
        assert _extract_commit_sha({"other": "value"}) == ""

    def test_extract_sha_returns_empty_for_none_commit(self):
        """Test that None commit value returns empty string"""
        assert _extract_commit_sha({"commit": None}) == ""

    def test_extract_sha_prefers_attribute_over_dict(self):
        """Test that .sha attribute is preferred over dict access"""
        mock_commit = MagicMock()
        mock_commit.sha = "from_attribute"
        # Even if it has dict-like behavior, attribute should be used
        result = {"commit": mock_commit}
        assert _extract_commit_sha(result) == "from_attribute"

    def test_extract_sha_fallback_to_dict_when_no_attribute(self):
        """Test fallback to dict access when no .sha attribute"""
        # Create a dict that doesn't have .sha attribute
        result = {"commit": {"sha": "from_dict_key"}}
        assert _extract_commit_sha(result) == "from_dict_key"


class TestClassifyGithubError:
    """Tests for _classify_github_error helper"""

    def test_classify_409_conflict(self):
        """Test classification of 409 Conflict error"""
        exc = GithubException(409, {"message": "SHA mismatch"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.CONFLICT
        assert "conflict" in error_msg.lower() or "sha" in error_msg.lower()

    def test_classify_403_permission_denied(self):
        """Test classification of 403 Permission Denied error"""
        exc = GithubException(403, {"message": "Resource not accessible"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower() or "denied" in error_msg.lower()

    def test_classify_403_protected_branch(self):
        """Test classification of 403 Protected Branch error"""
        exc = GithubException(403, {"message": "Protected branch rules"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.PERMISSION_DENIED
        assert "protected branch" in error_msg.lower() or "permission" in error_msg.lower()

    def test_classify_404_not_found(self):
        """Test classification of 404 Not Found error"""
        exc = GithubException(404, {"message": "Not Found"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.NOT_FOUND

    def test_classify_500_transient(self):
        """Test classification of 500 Server Error"""
        exc = GithubException(500, {"message": "Internal Server Error"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR
        assert "500" in error_msg

    def test_classify_502_transient(self):
        """Test classification of 502 Bad Gateway"""
        exc = GithubException(502, {"message": "Bad Gateway"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR

    def test_classify_429_rate_limit(self):
        """Test classification of 429 Rate Limit"""
        exc = GithubException(429, {"message": "Rate limit exceeded"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR

    def test_classify_unknown_error(self):
        """Test classification of unknown error"""
        exc = Exception("Unknown error")
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.UNKNOWN_ERROR

    def test_classify_401_unauthorized(self):
        """Test classification of 401 Unauthorized error (Issue #3230)"""
        exc = GithubException(401, {"message": "Bad credentials"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.PERMISSION_DENIED
        assert "unauthorized" in error_msg.lower() or "credentials" in error_msg.lower()

    def test_classify_422_validation_error(self):
        """Test classification of 422 Unprocessable Entity error (Issue #3230)"""
        exc = GithubException(422, {"message": "Invalid request"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.UNKNOWN_ERROR
        assert "422" in error_msg or "validation" in error_msg.lower()

    def test_classify_408_request_timeout(self):
        """Test classification of 408 Request Timeout error (Issue #3230)"""
        exc = GithubException(408, {"message": "Request Timeout"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR
        assert "408" in error_msg

    def test_classify_403_rate_limit_message(self):
        """Test classification of 403 with rate limit message (Issue #3230)"""
        exc = GithubException(403, {"message": "API rate limit exceeded"}, None)
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR
        assert "rate limit" in error_msg.lower()

    def test_classify_403_secondary_rate_limit(self):
        """Test classification of 403 with secondary rate limit (Issue #3230)"""
        exc = GithubException(
            403,
            {"message": "You have exceeded a secondary rate limit"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR

    def test_classify_403_rate_limit_headers(self):
        """Test classification of 403 with rate limit headers (Issue #3230)"""
        exc = GithubException(
            403,
            {"message": "Forbidden"},
            {"x-ratelimit-remaining": "0"}
        )
        error_type, error_msg = _classify_github_error(exc)
        assert error_type == CommitResult.TRANSIENT_ERROR


class TestCommitFileSuccess:
    """Tests for successful commit_file operations"""

    def test_update_existing_file(self):
        """Test successful update of existing file"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.return_value = {"commit": MagicMock(sha="new_sha")}

        result = commit_file(mock_repo, "main", "test.py", "content", "message")

        assert result.success is True
        assert result.status == CommitResult.SUCCESS
        mock_repo.update_file.assert_called_once()

    def test_create_new_file(self):
        """Test successful creation of new file when file doesn't exist"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_repo.get_contents.side_effect = GithubException(404, {"message": "Not Found"}, None)
        mock_repo.create_file.return_value = {"commit": MagicMock(sha="new_sha")}

        result = commit_file(mock_repo, "main", "new_file.py", "content", "message")

        assert result.success is True
        mock_repo.create_file.assert_called_once()

    def test_repo_none_returns_not_found(self):
        """Test that None repo returns NOT_FOUND result"""
        result = commit_file(None, "main", "test.py", "content", "message")

        assert result.success is False
        assert result.status == CommitResult.NOT_FOUND
        assert "not available" in result.message.lower()


class TestCommitFileConflict:
    """Tests for 409 Conflict error handling"""

    def test_409_conflict_fails_fast(self):
        """Test that 409 Conflict error fails immediately without retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(409, {"message": "SHA mismatch"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=3)

        assert result.success is False
        assert result.status == CommitResult.CONFLICT
        assert mock_repo.update_file.call_count == 1

    def test_409_conflict_message_includes_context(self):
        """Test that 409 Conflict error message includes helpful context"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(409, {"message": "SHA mismatch"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message")

        assert "conflict" in result.message.lower() or "sha" in result.message.lower()


class TestCommitFilePermissionDenied:
    """Tests for 403 Permission Denied error handling"""

    def test_403_permission_denied_fails_fast(self):
        """Test that 403 Permission Denied error fails immediately without retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(403, {"message": "Permission denied"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=3)

        assert result.success is False
        assert result.status == CommitResult.PERMISSION_DENIED
        assert mock_repo.update_file.call_count == 1

    def test_403_protected_branch_fails_fast(self):
        """Test that 403 Protected Branch error fails immediately without retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(
            403, {"message": "Protected branch rules prevent this"}, None
        )

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=3)

        assert result.success is False
        assert result.status == CommitResult.PERMISSION_DENIED
        assert mock_repo.update_file.call_count == 1


class TestCommitFileTransientErrors:
    """Tests for transient error handling with retry"""

    @patch("tools.github_api.time.sleep")
    def test_500_error_retries(self, mock_sleep):
        """Test that 500 Server Error triggers retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(500, {"message": "Server Error"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=2)

        assert result.success is False
        assert result.status == CommitResult.TRANSIENT_ERROR
        assert mock_repo.update_file.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("tools.github_api.time.sleep")
    def test_502_error_retries(self, mock_sleep):
        """Test that 502 Bad Gateway triggers retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(502, {"message": "Bad Gateway"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=1)

        assert result.success is False
        assert result.status == CommitResult.TRANSIENT_ERROR
        assert mock_repo.update_file.call_count == 2

    @patch("tools.github_api.time.sleep")
    def test_429_rate_limit_retries(self, mock_sleep):
        """Test that 429 Rate Limit triggers retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(429, {"message": "Rate limit"}, None)

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=1)

        assert result.success is False
        assert result.status == CommitResult.TRANSIENT_ERROR
        assert mock_repo.update_file.call_count == 2

    @patch("tools.github_api.time.sleep")
    def test_transient_error_succeeds_on_retry(self, mock_sleep):
        """Test that transient error can succeed on retry"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = [
            GithubException(500, {"message": "Server Error"}, None),
            {"commit": MagicMock(sha="new_sha")},
        ]

        result = commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=2)

        assert result.success is True
        assert mock_repo.update_file.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("tools.github_api.time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        """Test that retry uses exponential backoff"""
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(500, {"message": "Server Error"}, None)

        commit_file(mock_repo, "main", "test.py", "content", "message", max_retries=2)

        assert mock_sleep.call_count == 2
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 2.0
        assert delays[1] == 4.0


class TestCommitFileLogging:
    """Tests for logging behavior"""

    def test_success_logs_info(self, caplog):
        """Test that successful commit logs INFO level"""
        import logging
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.return_value = {"commit": MagicMock(sha="new_sha")}

        with caplog.at_level(logging.INFO):
            result = commit_file(mock_repo, "main", "test.py", "content", "message")

        assert result.success is True
        assert any("COMMIT_FILE_SUCCESS" in record.message for record in caplog.records)

    def test_conflict_logs_error(self, caplog):
        """Test that conflict error logs ERROR level"""
        import logging
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(409, {"message": "SHA mismatch"}, None)

        with caplog.at_level(logging.ERROR):
            result = commit_file(mock_repo, "main", "test.py", "content", "message")

        assert result.success is False
        assert any("COMMIT_FILE_CONFLICT" in record.message for record in caplog.records)

    def test_permission_denied_logs_error(self, caplog):
        """Test that permission denied error logs ERROR level"""
        import logging
        mock_repo = MagicMock()
        mock_repo.full_name = "test/repo"
        mock_file = MagicMock()
        mock_file.sha = "old_sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file.side_effect = GithubException(403, {"message": "Permission denied"}, None)

        with caplog.at_level(logging.ERROR):
            result = commit_file(mock_repo, "main", "test.py", "content", "message")

        assert result.success is False
        assert any("COMMIT_FILE_PERMISSION_DENIED" in record.message for record in caplog.records)
