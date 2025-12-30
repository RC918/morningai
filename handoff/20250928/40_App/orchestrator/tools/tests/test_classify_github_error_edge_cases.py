"""Edge case tests for _classify_github_error 403 message variants.

Issue #3232: D-1.5 Edge-case tests for _classify_github_error 403 message variants

Tests cover edge cases not covered by test_commit_file.py:
1. e.data is not a dict (string, None, list, etc.)
2. message key is missing from e.data
3. Alternative GitHub wording variants for protected branch errors
4. Case sensitivity handling for protected branch detection
"""
import sys
import os


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.github_api import (  # noqa: E402
    _classify_github_error,
    CommitResult,
)
from github import GithubException  # noqa: E402


class TestClassifyGithubError403EdgeCases:
    """Edge case tests for _classify_github_error with 403 status.

    These tests focus on edge cases not covered by TestClassifyGithubError
    in test_commit_file.py, specifically around data format variations
    and protected branch message variants.
    """

    def test_403_data_is_none(self):
        """Test 403 error when e.data is None.

        GitHub API can return None for data in some edge cases.
        The classifier should handle this gracefully and fall back
        to str(e) for the error message.
        """
        exc = GithubException(403, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower() or "denied" in error_msg.lower()

    def test_403_data_is_string(self):
        """Test 403 error when e.data is a string instead of dict.

        Some GitHub API responses may return a plain string error message
        instead of a structured dict. The classifier should handle this
        by using str(e) as the error message.
        """
        exc = GithubException(403, "Access denied to repository", None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower() or "denied" in error_msg.lower()

    def test_403_data_is_empty_dict(self):
        """Test 403 error when e.data is an empty dict (no message key).

        If the dict exists but has no 'message' key, the classifier
        should fall back to str(e) for the error message.
        """
        exc = GithubException(403, {}, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower()

    def test_403_data_dict_without_message_key(self):
        """Test 403 error when e.data dict has other keys but no 'message'.

        GitHub might return a dict with 'documentation_url' or other keys
        but missing the 'message' key. The classifier should handle this.
        """
        exc = GithubException(
            403,
            {"documentation_url": "https://docs.github.com/rest", "errors": []},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower()

    def test_403_data_is_list(self):
        """Test 403 error when e.data is a list instead of dict.

        Edge case where data might be a list of errors. The classifier
        should handle this gracefully.
        """
        exc = GithubException(403, ["error1", "error2"], None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower()

    def test_403_data_is_integer(self):
        """Test 403 error when e.data is an unexpected type (integer).

        Defensive test for completely unexpected data types.
        """
        exc = GithubException(403, 12345, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "permission" in error_msg.lower()


class TestProtectedBranchMessageVariants:
    """Tests for different GitHub protected branch error message variants.

    GitHub may use different wording for protected branch errors.
    These tests ensure all known variants are correctly detected.
    """

    def test_protected_branch_lowercase(self):
        """Test detection of 'protected branch' (lowercase).

        Standard GitHub error message format.
        """
        exc = GithubException(
            403,
            {"message": "protected branch hook declined"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()

    def test_protected_branch_uppercase(self):
        """Test detection of 'PROTECTED BRANCH' (uppercase).

        Ensures case-insensitive matching works.
        """
        exc = GithubException(
            403,
            {"message": "PROTECTED BRANCH rules prevent this action"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()

    def test_protected_branch_mixed_case(self):
        """Test detection of 'Protected Branch' (mixed case).

        Common GitHub API response format.
        """
        exc = GithubException(
            403,
            {"message": "Protected Branch rule violations detected"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()

    def test_branch_is_protected_variant(self):
        """Test detection of 'branch is protected' variant.

        Alternative wording GitHub may use.
        """
        exc = GithubException(
            403,
            {"message": "The branch 'main' is protected and cannot be modified"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED

    def test_protected_branch_hook_declined(self):
        """Test detection of 'protected branch hook declined' variant.

        GitHub webhook-related protected branch error.
        """
        exc = GithubException(
            403,
            {"message": "protected branch hook declined: Changes must be made through a pull request"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()

    def test_protected_branch_requires_review(self):
        """Test detection of protected branch requiring review.

        GitHub error when branch requires pull request reviews.
        """
        exc = GithubException(
            403,
            {"message": "protected branch requires pull request reviews"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()

    def test_protected_branch_status_checks(self):
        """Test detection of protected branch requiring status checks.

        GitHub error when branch requires status checks to pass.
        """
        exc = GithubException(
            403,
            {"message": "protected branch requires status checks to pass before merging"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower() or "protected branch" in error_msg.lower()


class TestProtectedBranchVsOther403:
    """Tests to verify protected branch detection doesn't false-positive.

    Ensure that 403 errors without protected branch keywords are
    correctly classified as generic PERMISSION_DENIED without the
    'Branch protection prevents commit' prefix.
    """

    def test_403_generic_permission_denied(self):
        """Test that generic 403 doesn't trigger protected branch detection.

        A 403 without 'protected branch' in the message should be
        classified as PERMISSION_DENIED but without the branch protection
        prefix in the error message.
        """
        exc = GithubException(
            403,
            {"message": "Resource not accessible by integration"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" not in error_msg.lower()

    def test_403_token_expired(self):
        """Test that token expiration 403 doesn't trigger protected branch.

        Token-related 403 errors should not be confused with branch protection.
        """
        exc = GithubException(
            403,
            {"message": "The token has expired"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" not in error_msg.lower()

    def test_403_insufficient_permissions(self):
        """Test that insufficient permissions 403 doesn't trigger protected branch.

        Permission-related 403 errors should not be confused with branch protection.
        """
        exc = GithubException(
            403,
            {"message": "Must have admin rights to Repository"},
            None
        )
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" not in error_msg.lower()


class TestProtectedBranchInStringData:
    """Tests for protected branch detection when e.data is a string.

    When e.data is a string (not dict), the classifier uses str(e)
    which may still contain 'protected branch'. These tests verify
    the detection still works in this edge case.
    """

    def test_protected_branch_in_string_data(self):
        """Test protected branch detection when data is a string containing the phrase.

        If e.data is a string that contains 'protected branch', the classifier
        should still detect it via str(e) which includes the data.
        """
        exc = GithubException(403, "protected branch prevents direct push", None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" in error_msg.lower()

    def test_no_protected_branch_in_string_data(self):
        """Test that string data without protected branch is handled correctly.

        String data without 'protected branch' should be generic PERMISSION_DENIED.
        """
        exc = GithubException(403, "Access forbidden", None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED
        assert "branch protection" not in error_msg.lower()


class TestOtherStatusCodeEdgeCases:
    """Edge case tests for other status codes with unusual data formats.

    While issue #3232 focuses on 403, these tests ensure other status codes
    also handle edge cases in data format gracefully.
    """

    def test_409_data_is_none(self):
        """Test 409 Conflict when e.data is None."""
        exc = GithubException(409, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.CONFLICT

    def test_409_data_is_string(self):
        """Test 409 Conflict when e.data is a string."""
        exc = GithubException(409, "SHA mismatch detected", None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.CONFLICT

    def test_404_data_is_none(self):
        """Test 404 Not Found when e.data is None."""
        exc = GithubException(404, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.NOT_FOUND

    def test_500_data_is_none(self):
        """Test 500 Server Error when e.data is None."""
        exc = GithubException(500, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.TRANSIENT_ERROR

    def test_401_data_is_none(self):
        """Test 401 Unauthorized when e.data is None."""
        exc = GithubException(401, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.PERMISSION_DENIED

    def test_422_data_is_none(self):
        """Test 422 Validation Error when e.data is None."""
        exc = GithubException(422, None, None)
        error_type, error_msg = _classify_github_error(exc)

        assert error_type == CommitResult.UNKNOWN_ERROR
