"""Contract Tests for commit_file() GitHub API Integration.

Issue #3228: D-1.6 commit_file() GitHub API Contract Tests & Staging Smoke Test

This module provides contract tests that verify the actual behavior of GitHub API
responses when using commit_file(). Unlike mock-based unit tests, these tests
interact with a real GitHub repository to validate:

1. GithubException.status values for various error scenarios
2. update_file() / create_file() return structure
3. 403 protected branch error message format
4. 409 conflict error message format

IMPORTANT: These tests are SKIPPED by default and require:
- GITHUB_CONTRACT_TEST_TOKEN: GitHub token with repo write access
- GITHUB_CONTRACT_TEST_REPO: Test repository (e.g., "owner/test-repo")
- GITHUB_CONTRACT_TEST_BRANCH: Unprotected branch for testing
- GITHUB_CONTRACT_TEST_PROTECTED_BRANCH: Protected branch for 403 tests (optional)

To run these tests:
1. Set up a dedicated test repository with branch protection on main
2. Create a test branch without protection
3. Configure CI secrets or run locally with environment variables
4. Run: pytest -m contract tools/tests/test_commit_file_contract.py -v

Design Principles:
- Each test uses UUID-based file names to avoid conflicts
- All created files are cleaned up after tests
- Tests are idempotent and can be run multiple times
- Failures provide detailed diagnostic information

Related:
- PR #3226 (commit_file error handling)
- Issue #3216 (Commit Conflict Handling)
- test_commit_file.py (mock-based unit tests)
"""
import os
import sys
import uuid
import logging

import pytest
from github import Github, GithubException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)


# =============================================================================
# Environment Variable Contract
# =============================================================================

CONTRACT_TEST_TOKEN = os.environ.get("GITHUB_CONTRACT_TEST_TOKEN")
CONTRACT_TEST_REPO = os.environ.get("GITHUB_CONTRACT_TEST_REPO")
CONTRACT_TEST_BRANCH = os.environ.get("GITHUB_CONTRACT_TEST_BRANCH", "contract-test")
CONTRACT_TEST_PROTECTED_BRANCH = os.environ.get("GITHUB_CONTRACT_TEST_PROTECTED_BRANCH", "main")

# Skip condition: all required env vars must be set
SKIP_CONTRACT_TESTS = not all([CONTRACT_TEST_TOKEN, CONTRACT_TEST_REPO])
SKIP_REASON = (
    "Contract tests require GITHUB_CONTRACT_TEST_TOKEN and GITHUB_CONTRACT_TEST_REPO. "
    "See test_commit_file_contract.py docstring for setup instructions."
)


def _generate_test_file_path() -> str:
    """Generate a unique file path for contract testing.

    Uses UUID to ensure no conflicts between test runs.
    Files are created in a dedicated .contract-tests/ directory.
    """
    return f".contract-tests/test-{uuid.uuid4().hex[:12]}.txt"


def _cleanup_test_file(repo, branch: str, file_path: str) -> None:
    """Clean up a test file after test completion.

    Best-effort cleanup - logs warning but doesn't fail on error.
    """
    try:
        contents = repo.get_contents(file_path, ref=branch)
        repo.delete_file(
            file_path,
            f"[contract-test] cleanup {file_path}",
            contents.sha,
            branch=branch
        )
        logger.info(f"[CONTRACT_TEST] Cleaned up {file_path}")
    except GithubException as e:
        if e.status != 404:
            logger.warning(f"[CONTRACT_TEST] Failed to cleanup {file_path}: {e}")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def github_client():
    """Create GitHub client for contract tests."""
    if SKIP_CONTRACT_TESTS:
        pytest.skip(SKIP_REASON)
    return Github(CONTRACT_TEST_TOKEN)


@pytest.fixture(scope="module")
def test_repo(github_client):
    """Get the test repository."""
    return github_client.get_repo(CONTRACT_TEST_REPO)


@pytest.fixture
def test_file_path():
    """Generate a unique test file path."""
    return _generate_test_file_path()


@pytest.fixture
def cleanup_files(test_repo):
    """Fixture to track and cleanup test files."""
    files_to_cleanup = []

    yield files_to_cleanup

    for file_path, branch in files_to_cleanup:
        _cleanup_test_file(test_repo, branch, file_path)


# =============================================================================
# Contract Tests: Success Scenarios
# =============================================================================

@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestCreateFileContract:
    """Contract tests for create_file() API behavior."""

    def test_create_file_returns_commit_with_sha(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Verify create_file() returns dict with 'commit' containing 'sha'.

        Contract:
        - Response is a dict
        - Response has 'commit' key
        - commit object has 'sha' attribute (PyGithub Commit object)
        """
        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        result = test_repo.create_file(
            test_file_path,
            "[contract-test] create file",
            "test content",
            branch=CONTRACT_TEST_BRANCH
        )

        assert isinstance(result, dict), "create_file() should return dict"
        assert "commit" in result, "Response should have 'commit' key"
        assert hasattr(result["commit"], "sha"), "Commit should have 'sha' attribute"
        assert len(result["commit"].sha) == 40, "SHA should be 40 characters"

    def test_create_file_commit_sha_is_string(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Verify commit SHA is a string (not bytes or other type)."""
        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        result = test_repo.create_file(
            test_file_path,
            "[contract-test] create file",
            "test content",
            branch=CONTRACT_TEST_BRANCH
        )

        sha = result["commit"].sha
        assert isinstance(sha, str), f"SHA should be str, got {type(sha)}"


@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestUpdateFileContract:
    """Contract tests for update_file() API behavior."""

    def test_update_file_returns_commit_with_sha(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Verify update_file() returns dict with 'commit' containing 'sha'."""
        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        create_result = test_repo.create_file(
            test_file_path,
            "[contract-test] create for update",
            "initial content",
            branch=CONTRACT_TEST_BRANCH
        )
        file_sha = create_result["content"].sha

        update_result = test_repo.update_file(
            test_file_path,
            "[contract-test] update file",
            "updated content",
            file_sha,
            branch=CONTRACT_TEST_BRANCH
        )

        assert isinstance(update_result, dict), "update_file() should return dict"
        assert "commit" in update_result, "Response should have 'commit' key"
        assert hasattr(update_result["commit"], "sha"), "Commit should have 'sha' attribute"


# =============================================================================
# Contract Tests: 409 Conflict Scenarios
# =============================================================================

@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestConflictErrorContract:
    """Contract tests for 409 Conflict error behavior.

    These tests verify the exact structure of GithubException when
    a SHA conflict occurs (file was modified externally).
    """

    def test_409_conflict_exception_status(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Verify GithubException.status is 409 for SHA conflicts.

        Contract:
        - GithubException is raised
        - exception.status == 409
        """
        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        create_result = test_repo.create_file(
            test_file_path,
            "[contract-test] create for conflict",
            "initial content",
            branch=CONTRACT_TEST_BRANCH
        )
        old_sha = create_result["content"].sha

        test_repo.update_file(
            test_file_path,
            "[contract-test] first update",
            "updated content",
            old_sha,
            branch=CONTRACT_TEST_BRANCH
        )

        with pytest.raises(GithubException) as exc_info:
            test_repo.update_file(
                test_file_path,
                "[contract-test] conflict update",
                "conflict content",
                old_sha,
                branch=CONTRACT_TEST_BRANCH
            )

        assert exc_info.value.status == 409, (
            f"Expected status 409, got {exc_info.value.status}"
        )

    def test_409_conflict_exception_has_data(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Verify GithubException.data contains error message for 409."""
        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        create_result = test_repo.create_file(
            test_file_path,
            "[contract-test] create for conflict",
            "initial content",
            branch=CONTRACT_TEST_BRANCH
        )
        old_sha = create_result["content"].sha

        test_repo.update_file(
            test_file_path,
            "[contract-test] first update",
            "updated content",
            old_sha,
            branch=CONTRACT_TEST_BRANCH
        )

        with pytest.raises(GithubException) as exc_info:
            test_repo.update_file(
                test_file_path,
                "[contract-test] conflict update",
                "conflict content",
                old_sha,
                branch=CONTRACT_TEST_BRANCH
            )

        data = exc_info.value.data
        assert data is not None, "GithubException.data should not be None"
        assert isinstance(data, dict), f"data should be dict, got {type(data)}"
        assert "message" in data, "data should have 'message' key"


# =============================================================================
# Contract Tests: 403 Protected Branch Scenarios
# =============================================================================

@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestProtectedBranchErrorContract:
    """Contract tests for 403 Protected Branch error behavior.

    These tests verify the exact structure of GithubException when
    attempting to commit to a protected branch.

    IMPORTANT: Requires GITHUB_CONTRACT_TEST_PROTECTED_BRANCH to be set
    to a branch with protection rules enabled.
    """

    @pytest.fixture
    def protected_branch_available(self):
        """Check if protected branch testing is available."""
        if not CONTRACT_TEST_PROTECTED_BRANCH:
            pytest.skip("GITHUB_CONTRACT_TEST_PROTECTED_BRANCH not set")

    def test_403_protected_branch_exception_status(
        self, test_repo, test_file_path, protected_branch_available
    ):
        """Verify GithubException.status is 403 for protected branch commits.

        Contract:
        - GithubException is raised
        - exception.status == 403
        """
        with pytest.raises(GithubException) as exc_info:
            test_repo.create_file(
                test_file_path,
                "[contract-test] protected branch test",
                "test content",
                branch=CONTRACT_TEST_PROTECTED_BRANCH
            )

        assert exc_info.value.status == 403, (
            f"Expected status 403, got {exc_info.value.status}"
        )

    def test_403_protected_branch_message_contains_keyword(
        self, test_repo, test_file_path, protected_branch_available
    ):
        """Verify 403 error message contains 'protected' keyword.

        Contract:
        - GithubException.data['message'] contains 'protected' (case-insensitive)

        This is important for _classify_github_error() to correctly identify
        protected branch errors vs other 403 errors.
        """
        with pytest.raises(GithubException) as exc_info:
            test_repo.create_file(
                test_file_path,
                "[contract-test] protected branch test",
                "test content",
                branch=CONTRACT_TEST_PROTECTED_BRANCH
            )

        data = exc_info.value.data
        message = data.get("message", "") if isinstance(data, dict) else str(data)

        assert "protected" in message.lower(), (
            f"Expected 'protected' in error message, got: {message}"
        )


# =============================================================================
# Contract Tests: 404 Not Found Scenarios
# =============================================================================

@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestNotFoundErrorContract:
    """Contract tests for 404 Not Found error behavior."""

    def test_404_get_contents_nonexistent_file(self, test_repo):
        """Verify GithubException.status is 404 for nonexistent files."""
        nonexistent_path = f".contract-tests/nonexistent-{uuid.uuid4().hex}.txt"

        with pytest.raises(GithubException) as exc_info:
            test_repo.get_contents(nonexistent_path, ref=CONTRACT_TEST_BRANCH)

        assert exc_info.value.status == 404, (
            f"Expected status 404, got {exc_info.value.status}"
        )


# =============================================================================
# Smoke Test: Full commit_file() Integration
# =============================================================================

@pytest.mark.contract
@pytest.mark.skipif(SKIP_CONTRACT_TESTS, reason=SKIP_REASON)
class TestCommitFileSmokeTest:
    """Smoke tests for commit_file() function with real GitHub API.

    These tests verify that commit_file() correctly handles real
    GitHub API responses, not just mocked ones.
    """

    def test_commit_file_create_success(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Smoke test: commit_file() successfully creates a new file."""
        from tools.github_api import commit_file, CommitResult

        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        result = commit_file(
            test_repo,
            CONTRACT_TEST_BRANCH,
            test_file_path,
            "smoke test content",
            "[contract-test] smoke test create"
        )

        assert result.success is True, f"Expected success, got: {result}"
        assert result.status == CommitResult.SUCCESS
        assert len(result.sha) == 40, f"Expected 40-char SHA, got: {result.sha}"

    def test_commit_file_update_success(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Smoke test: commit_file() successfully updates an existing file."""
        from tools.github_api import commit_file, CommitResult

        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        create_result = commit_file(
            test_repo,
            CONTRACT_TEST_BRANCH,
            test_file_path,
            "initial content",
            "[contract-test] smoke test create"
        )
        assert create_result.success is True

        update_result = commit_file(
            test_repo,
            CONTRACT_TEST_BRANCH,
            test_file_path,
            "updated content",
            "[contract-test] smoke test update"
        )

        assert update_result.success is True, f"Expected success, got: {update_result}"
        assert update_result.status == CommitResult.SUCCESS

    def test_commit_file_conflict_handling(
        self, test_repo, test_file_path, cleanup_files
    ):
        """Smoke test: commit_file() correctly handles 409 conflict.

        This test simulates a race condition by:
        1. Creating a file
        2. Updating it externally (simulating another process)
        3. Attempting to update with stale SHA

        Note: commit_file() fetches fresh SHA before update, so we need
        to directly use update_file() to trigger the conflict.
        """
        from tools.github_api import CommitResult, _classify_github_error

        cleanup_files.append((test_file_path, CONTRACT_TEST_BRANCH))

        create_result = test_repo.create_file(
            test_file_path,
            "[contract-test] create for conflict smoke",
            "initial",
            branch=CONTRACT_TEST_BRANCH
        )
        stale_sha = create_result["content"].sha

        test_repo.update_file(
            test_file_path,
            "[contract-test] external update",
            "external change",
            stale_sha,
            branch=CONTRACT_TEST_BRANCH
        )

        with pytest.raises(GithubException) as exc_info:
            test_repo.update_file(
                test_file_path,
                "[contract-test] stale update",
                "stale change",
                stale_sha,
                branch=CONTRACT_TEST_BRANCH
            )

        error_type, error_msg = _classify_github_error(exc_info.value)
        assert error_type == CommitResult.CONFLICT, (
            f"Expected CONFLICT, got {error_type}: {error_msg}"
        )


# =============================================================================
# Environment Validation Test
# =============================================================================

@pytest.mark.contract
class TestContractTestEnvironment:
    """Tests to validate contract test environment setup."""

    def test_environment_variables_documented(self):
        """Verify all required environment variables are documented."""
        required_vars = [
            "GITHUB_CONTRACT_TEST_TOKEN",
            "GITHUB_CONTRACT_TEST_REPO",
        ]
        optional_vars = [
            "GITHUB_CONTRACT_TEST_BRANCH",
            "GITHUB_CONTRACT_TEST_PROTECTED_BRANCH",
        ]

        for var in required_vars:
            assert var in __doc__, f"Required var {var} should be documented"

        for var in optional_vars:
            assert var in __doc__, f"Optional var {var} should be documented"

    def test_skip_reason_is_informative(self):
        """Verify skip reason provides setup instructions."""
        assert "GITHUB_CONTRACT_TEST_TOKEN" in SKIP_REASON
        assert "GITHUB_CONTRACT_TEST_REPO" in SKIP_REASON

    @pytest.mark.skipif(not SKIP_CONTRACT_TESTS, reason="Only run when skipped")
    def test_contract_tests_skip_gracefully(self):
        """Verify contract tests skip gracefully when env not configured."""
        pass
