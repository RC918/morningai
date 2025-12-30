#!/usr/bin/env python3
"""
Edge Case Tests for _attempt_simple_coder_fix - Issue #3246

D-1 Phase 1: Edge case tests for boundary conditions in _attempt_simple_coder_fix.

These tests cover edge cases identified in #3246 that have distinct branching
behavior in production code. Each test verifies a specific code path that
wasn't covered by existing tests.

Edge cases covered:
1. get_repo() returns None
2. File content without decoded_content attribute
3. SimpleCoder output.data is None
4. SimpleCoder returns empty patch content
5. CommitResult.NOT_FOUND status
6. CommitResult.TRANSIENT_ERROR status
7. Non-Python file with syntax_valid=False (should NOT skip)
8. review_comments as list of strings (not dicts)

Related:
- #3246: Edge case tests for _attempt_simple_coder_fix
- #3243: fixer_node and _attempt_simple_coder_fix unit tests
- test_fixer_node_unit.py: Main unit tests
- test_simple_coder_wiring.py: Wiring integration tests
"""
import sys
from unittest.mock import MagicMock, patch
from typing import Optional
from types import ModuleType


def setup_fake_modules():
    """Set up fake modules to avoid ImportError in tests.

    This injects fake modules into sys.modules so that the imports
    inside langgraph_orchestrator and _attempt_simple_coder_fix() succeed
    in the test environment.
    """
    if "common" not in sys.modules:
        common = ModuleType("common")
        sys.modules["common"] = common

    if "common.config" not in sys.modules:
        common_config = ModuleType("common.config")
        sys.modules["common.config"] = common_config
        sys.modules["common"].config = common_config

    if "common.config.settings" not in sys.modules:
        settings_module = ModuleType("common.config.settings")

        class FakeSettings:
            enable_simple_coder = False
            enable_project_engineer_fixer = False
            project_engineer_fixer_percent = 0
            enable_project_engineer_codegen = False
            workspace_path = "."
            openai_api_key = "test-key"
            github_repo = "RC918/morningai"

        settings_module.settings = FakeSettings()
        sys.modules["common.config.settings"] = settings_module
        sys.modules["common.config"].settings = settings_module

    if "common.agents" not in sys.modules:
        common_agents = ModuleType("common.agents")
        sys.modules["common.agents"] = common_agents
        sys.modules["common"].agents = common_agents

    if "common.agents.base_agent" not in sys.modules:
        base_agent = ModuleType("common.agents.base_agent")

        class FakeAgentInput:
            def __init__(self, task_id="", prompt="", context=None):
                self.task_id = task_id
                self.prompt = prompt
                self.context = context or {}

        base_agent.AgentInput = FakeAgentInput
        sys.modules["common.agents.base_agent"] = base_agent
        sys.modules["common.agents"].base_agent = base_agent


setup_fake_modules()

from langgraph_orchestrator import (  # noqa: E402
    AgentState,
    _attempt_simple_coder_fix,
)


def create_test_state(
    trace_id: str = "test-trace-123",
    retry_count: int = 0,
    error: Optional[str] = None,
    ci_state: str = "failure",
    pr_number: int = 123,
    review_severity: str = "low",
    review_outcome: Optional[dict] = None,
    review_file_path: str = "",
    comment_body: str = "",
    repo: str = "RC918/morningai",
    branch: str = "test-branch",
    diff_head_sha: str = "",
    review_comments: Optional[list] = None,
) -> AgentState:
    """Create a test AgentState with SimpleCoder-relevant fields."""
    if review_outcome is None:
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
            "verdict": "request_changes",
        }

    state = {
        "messages": [],
        "goal": "Fix code issue",
        "trace_id": trace_id,
        "repo": repo,
        "branch": branch,
        "plan": ["Step 1", "Step 2"],
        "current_step": 2,
        "pr_url": f"https://github.com/{repo}/pull/{pr_number}",
        "pr_number": pr_number,
        "ci_state": ci_state,
        "ci_checks": {"lint": "failure"},
        "error": error,
        "retry_count": retry_count,
        "final_result": {},
        "review_result": {},
        "review_comments": review_comments or [],
        "review_severity": review_severity,
        "merge_decision": "pending",
        "code_quality_score": 80,
        "review_outcome": review_outcome,
        "review_file_path": review_file_path,
        "comment_body": comment_body,
        "diff_head_sha": diff_head_sha,
    }

    return state


class TestGetRepoEdgeCases:
    """Tests for get_repo() edge cases in _attempt_simple_coder_fix."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_get_repo_returns_none(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that get_repo() returning None is handled gracefully.

        This edge case occurs when the GitHub API fails to retrieve the
        repository object (e.g., network error, invalid repo name).
        """
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_get_repo.return_value = None

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "could not access repository" in message.lower()
            mock_coder.assert_not_called()


class TestFileContentEdgeCases:
    """Tests for file content fetching edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_file_without_decoded_content_attribute(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test handling of file object without decoded_content attribute.

        This edge case can occur with certain GitHub API responses where
        the file object doesn't have the expected decoded_content attribute
        (e.g., binary files, large files, or API edge cases).
        """
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo

            mock_file = MagicMock(spec=[])
            del mock_file.decoded_content
            mock_repo.get_contents.return_value = mock_file

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "could not decode file content" in message.lower()
            mock_coder.assert_not_called()


class TestSimpleCoderOutputEdgeCases:
    """Tests for SimpleCoder output edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_output_data_is_none(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test handling when output.data is None.

        This edge case can occur if SimpleCoder returns success=False
        with data=None (e.g., internal error before data is populated).
        """
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_output = MagicMock()
            mock_output.success = False
            mock_output.data = None
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "skipped" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_empty_patch_content(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test handling when SimpleCoder returns empty patch content.

        This edge case occurs when SimpleCoder returns status=patch but
        the patch content is empty string. This should be treated as a skip.
        """
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": "",
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "empty patch" in message.lower()


class TestCommitResultEdgeCases:
    """Tests for CommitResult status edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_commit_not_found_returns_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that NOT_FOUND status returns (False, error_message).

        This edge case occurs when the branch or file path doesn't exist
        at commit time (e.g., branch was deleted between fetch and commit).
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.NOT_FOUND,
                "Branch not found: test-branch"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed to apply patch" in message.lower()
            mock_commit.assert_called_once()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_commit_transient_error_returns_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that TRANSIENT_ERROR status returns (False, error_message).

        This edge case occurs when GitHub returns a transient error
        (e.g., 5xx, 429) that exhausted all retries.
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.TRANSIENT_ERROR,
                "Server error (HTTP 503): Service temporarily unavailable"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed to apply patch" in message.lower()
            mock_commit.assert_called_once()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_commit_permission_denied_returns_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that PERMISSION_DENIED status returns (False, error_message).

        This edge case occurs when the token lacks write permission or
        branch protection rules prevent the commit.
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.PERMISSION_DENIED,
                "Branch protection prevents commit: main is protected"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed to apply patch" in message.lower()
            mock_commit.assert_called_once()


class TestSyntaxValidationEdgeCases:
    """Tests for syntax validation edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_non_python_file_ignores_syntax_valid_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that non-Python files ignore syntax_valid=False.

        The syntax validation check only applies to .py files. For other
        file types (e.g., .js, .ts, .json), syntax_valid=False should NOT
        cause the fix to be skipped.
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"function foo() { return 1; }"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": "function foo() { return 42; }",
                "syntax_valid": False,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.SUCCESS,
                "Commit successful",
                sha="abc123"
            )

            state = create_test_state(
                review_file_path="src/test.js",
                comment_body="Change return value",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is True
            assert "successfully" in message.lower()
            mock_commit.assert_called_once()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_python_file_with_syntax_valid_none(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that Python files with syntax_valid=None proceed to commit.

        If syntax_valid is None (not explicitly False), the check should
        pass and proceed to commit. Only explicit False triggers skip.
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": None,
            }
            mock_coder.return_value.execute.return_value = mock_output

            with patch("tools.github_api.commit_file") as mock_commit:
                mock_commit.return_value = CommitResult(
                    CommitResult.SUCCESS,
                    "Commit successful",
                    sha="abc123"
                )

                state = create_test_state(
                    review_file_path="src/test.py",
                    comment_body="Add docstring",
                )

                success, message = _attempt_simple_coder_fix(state, "test-trace")

                assert success is True
                mock_commit.assert_called_once()


class TestReviewCommentExtractionEdgeCases:
    """Tests for review comment extraction edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_review_comments_as_list_of_strings(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test extraction of comment from review_comments list of strings.

        The production code handles both list of dicts (with 'body' key)
        and list of strings. This tests the string case.
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.SUCCESS,
                "Commit successful",
                sha="abc123"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="",
                review_comments=["Add docstring to function"],
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is True
            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["review_comment"] == "Add docstring to function"

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_empty_review_comments_list(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that empty review_comments list with empty comment_body fails gate.

        When both comment_body is empty and review_comments is an empty list,
        the function should return (False, "No review comment available").
        """
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="",
                review_comments=[],
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "comment" in message.lower() or "no review" in message.lower()
            mock_coder.assert_not_called()


class TestSeverityExtractionEdgeCases:
    """Tests for severity extraction edge cases."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_review_outcome_not_dict(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test handling when review_outcome is not a dict.

        If review_outcome is a non-dict value (e.g., string, None),
        severity should default to "low".
        """
        from tools.github_api import CommitResult

        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_status.PATCH.value = "patch"

            mock_output = MagicMock()
            mock_output.success = True
            mock_output.data = {
                "status": "patch",
                "patch": 'def foo():\n    """Docstring."""\n    pass',
                "syntax_valid": True,
            }
            mock_coder.return_value.execute.return_value = mock_output

            mock_commit.return_value = CommitResult(
                CommitResult.SUCCESS,
                "Commit successful",
                sha="abc123"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )
            state["review_outcome"] = "not_a_dict"

            with patch("coder.autofix_gate.is_autofix_allowed", return_value=True):
                success, message = _attempt_simple_coder_fix(state, "test-trace")

            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["severity"] == "low"
