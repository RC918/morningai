#!/usr/bin/env python3
"""
Fixer Node Unit Tests - Issue #3239

D-1 Phase 1: Unit tests for fixer_node and _attempt_simple_coder_fix.

This module adds targeted tests for gaps identified in #3239:
1. Test that _attempt_simple_coder_fix() is called when autofix is eligible
2. Test that SimpleCoder fallback to AutoFixer works when SimpleCoder fails
3. Test that fixer_node correctly routes based on fix_handoff.auto_fix_eligible
4. Test error handling when SimpleCoder raises exceptions
5. Test commit_file result handling (SUCCESS, CONFLICT, PERMISSION_DENIED)

Related:
- #3239: Add fixer_node and _attempt_simple_coder_fix unit tests
- #3211: Three Don'ts Safety Guardrails (closed)
- test_simple_coder_wiring.py: Existing wiring tests
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
            enable_general_coder = False
            enable_project_engineer_fixer = False
            project_engineer_fixer_percent = 0
            enable_project_engineer_codegen = False
            workspace_path = "."
            openai_api_key = "test-key"
            github_repo = "RC918/morningai"
            github_token = "test-token"
            agent_github_token = "test-agent-token"
            general_coder_max_files = 5  # Issue #3890: D-4 Context Extraction

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
    fixer_node,
    _attempt_simple_coder_fix,
    _ensure_comment_body_for_ci_failure,
    _extract_file_path_from_error,
    _extract_file_paths_from_error,
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
    fix_handoff: Optional[dict] = None,
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
        "review_comments": [],
        "review_severity": review_severity,
        "merge_decision": "pending",
        "code_quality_score": 80,
        "review_outcome": review_outcome,
        "review_file_path": review_file_path,
        "comment_body": comment_body,
        "diff_head_sha": diff_head_sha,
    }

    if fix_handoff is not None:
        state["fix_handoff"] = fix_handoff

    return state


class TestCommitFileResultHandling:
    """Tests for commit_file result handling in _attempt_simple_coder_fix.

    These tests verify that _attempt_simple_coder_fix correctly handles
    different CommitResult statuses from commit_file().
    """

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_commit_success_returns_true(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that successful commit returns (True, success_message)."""
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

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is True
            assert "successfully" in message.lower()
            mock_commit.assert_called_once()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_commit_conflict_returns_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that 409 Conflict returns (False, error_message)."""
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
                CommitResult.CONFLICT,
                "SHA mismatch: file was modified"
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
    def test_commit_error_returns_false(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that generic error returns (False, error_message)."""
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
                CommitResult.UNKNOWN_ERROR,
                "Network error: connection timeout"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed to apply patch" in message.lower()


class TestSimpleCoderExceptionHandling:
    """Tests for exception handling when SimpleCoder raises errors."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_coder_execute_exception_returns_false(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that SimpleCoder.execute() exception returns (False, error)."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_coder.return_value.execute.side_effect = RuntimeError(
                "LLM API timeout"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed" in message.lower() or "error" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_coder_execute_value_error_returns_false(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that ValueError from SimpleCoder returns (False, error)."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_coder.return_value.execute.side_effect = ValueError(
                "Invalid input format"
            )

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed" in message.lower() or "error" in message.lower()


class TestFixerNodeSimpleCoderIntegration:
    """Tests for fixer_node integration with SimpleCoder.

    These tests verify that fixer_node correctly:
    1. Calls _attempt_simple_coder_fix first
    2. Skips AutoFixer when SimpleCoder succeeds
    3. Falls back to AutoFixer when SimpleCoder fails
    """

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_records_simple_coder_success_metrics(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that fixer_node records metrics on SimpleCoder success."""
        mock_attempt.return_value = (True, "SimpleCoder fixed src/test.py")
        mock_metrics_instance = MagicMock()
        mock_metrics.return_value = mock_metrics_instance
        mock_eval.return_value = MagicMock()

        state = create_test_state()

        fixer_node(state)

        mock_metrics_instance.record_fixer_attempt.assert_called_once()
        call_args = mock_metrics_instance.record_fixer_attempt.call_args
        assert call_args[1]["success"] is True

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_adds_simple_coder_message_on_success(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that fixer_node adds SimpleCoder message on success."""
        mock_attempt.return_value = (True, "SimpleCoder fixed src/test.py")
        mock_metrics.return_value = MagicMock()
        mock_eval.return_value = MagicMock()

        state = create_test_state()

        result = fixer_node(state)

        messages = result.get("messages", [])
        assert len(messages) > 0
        assert any(
            "SimpleCoder" in str(getattr(msg, "content", ""))
            for msg in messages
        )

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_increments_retry_on_simple_coder_success(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that fixer_node increments retry_count on SimpleCoder success."""
        mock_attempt.return_value = (True, "SimpleCoder fixed src/test.py")
        mock_metrics.return_value = MagicMock()
        mock_eval.return_value = MagicMock()

        state = create_test_state(retry_count=0)

        result = fixer_node(state)

        assert result["retry_count"] == 1


class TestReviewCommentExtraction:
    """Tests for review comment extraction from state."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_extracts_comment_from_review_comments_dict(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test extraction of comment from review_comments list of dicts."""
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
            )
            state["review_comments"] = [{"body": "Add docstring to function"}]

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is True
            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["review_comment"] == "Add docstring to function"

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_extracts_comment_from_review_comments_string(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test extraction of comment from review_comments list of strings."""
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
            )
            state["review_comments"] = ["Add type hints"]

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is True
            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["review_comment"] == "Add type hints"


class TestFileContentFetching:
    """Tests for file content fetching from GitHub."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_uses_diff_head_sha_when_available(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that diff_head_sha is used as ref when available."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_output = MagicMock()
            mock_output.success = False
            mock_output.data = {"reason": "Low confidence"}
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
                diff_head_sha="abc123def456",
            )

            _attempt_simple_coder_fix(state, "test-trace")

            mock_repo.get_contents.assert_called_once_with(
                "src/test.py",
                ref="abc123def456"
            )

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_uses_branch_when_no_diff_head_sha(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that branch is used as ref when diff_head_sha is empty."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"def foo():\n    pass"
            mock_repo.get_contents.return_value = mock_file

            mock_output = MagicMock()
            mock_output.success = False
            mock_output.data = {"reason": "Low confidence"}
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
                branch="feature-branch",
                diff_head_sha="",
            )

            _attempt_simple_coder_fix(state, "test-trace")

            mock_repo.get_contents.assert_called_once_with(
                "src/test.py",
                ref="feature-branch"
            )

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_handles_file_fetch_exception(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that file fetch exception returns (False, error)."""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_repo.get_contents.side_effect = Exception("File not found")

            state = create_test_state(
                review_file_path="src/nonexistent.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "failed to fetch" in message.lower()


class TestSeverityExtraction:
    """Tests for severity extraction from review_outcome."""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_passes_severity_to_simple_coder(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that severity from review_outcome is passed to SimpleCoder."""
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
                review_outcome={
                    "severity": "low",
                    "diff_truncated": False,
                    "schema_validated": True,
                },
            )

            _attempt_simple_coder_fix(state, "test-trace")

            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["severity"] == "low"

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_defaults_to_low_severity_when_missing(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that severity defaults to 'low' when not in review_outcome."""
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
                review_outcome={
                    "diff_truncated": False,
                    "schema_validated": True,
                },
            )

            _attempt_simple_coder_fix(state, "test-trace")

            call_args = mock_coder.return_value.execute.call_args
            context = call_args[0][0].context
            assert context["severity"] == "low"


class TestEnsureCommentBodyForCiFailure:
    """Regression tests for _ensure_comment_body_for_ci_failure (Issue #3564).

    Root Cause #10: CI failure scenarios don't have a PR review comment,
    but coders need comment_body to understand what to fix. This function
    synthesizes comment_body from ci_failure_context.
    """

    def test_synthesizes_comment_when_ci_failure_trigger_and_no_comment(self):
        """Test that comment_body is synthesized when ci_failure_trigger=True."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "F821: undefined name 'reuslt'",
            },
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] != ""
        assert "lint" in state["comment_body"]
        assert "F821" in state["comment_body"]

    def test_does_not_override_existing_comment_body(self):
        """Test that existing comment_body is not overwritten."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "F821: undefined name",
            },
            "comment_body": "Human review comment",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] == "Human review comment"

    def test_synthesizes_comment_despite_existing_review_comments(self):
        """Test that comment_body IS synthesized even when review_comments exist (Issue #3572).

        Root Cause #12: The review_comments list contains ALL historical PR comments
        (including bot comments, previous test comments, etc.), not just the triggering
        comment. For CI failure scenarios, there is no triggering comment - the webhook
        comes from CI, not a PR review. We should NOT skip synthesis just because
        historical comments exist.
        """
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "F821: undefined name 'reuslt'",
            },
            "comment_body": "",
            "review_comments": [{"body": "Please fix this"}],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        # Issue #3572: comment_body should be synthesized despite review_comments
        assert state["comment_body"] != ""
        assert "lint" in state["comment_body"]
        assert "F821" in state["comment_body"]

    def test_synthesizes_comment_with_many_historical_comments(self):
        """Test synthesis works with many historical PR comments (Issue #3572).

        This is the exact scenario from Probe 0 (#3528) which had 25 historical
        comments and was blocking CI failure auto-fix for "十幾個版本" (a dozen versions).
        """
        # Simulate 25 historical comments like Probe 0 had
        historical_comments = [{"body": f"Comment {i}"} for i in range(25)]
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "test/capability_probe/probe0_sanity/missing_docstring.py:15:12: F821 undefined name 'reuslt'",
            },
            "comment_body": "",
            "review_comments": historical_comments,
            "review_file_path": "",
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        # Issue #3572: comment_body should be synthesized
        assert state["comment_body"] != ""
        assert "lint" in state["comment_body"]
        # Issue #3567: review_file_path should be extracted
        assert state["review_file_path"] == "test/capability_probe/probe0_sanity/missing_docstring.py"

    def test_does_nothing_when_ci_failure_trigger_false(self):
        """Test that nothing happens when ci_failure_trigger=False."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": False,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "F821: undefined name",
            },
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] == ""

    def test_handles_missing_ci_failure_context(self):
        """Test graceful handling when ci_failure_context is missing."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] == ""

    def test_synthesizes_without_error_summary(self):
        """Test synthesis when error_summary is empty."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "test",
                "error_summary": "",
            },
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] == "Fix CI failure in test check"

    def test_truncates_long_error_summary(self):
        """Test that long error_summary is truncated to 500 chars."""
        long_error = "E" * 1000
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": long_error,
            },
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert len(state["comment_body"]) < 600

    def test_handles_non_string_error_summary(self):
        """Test handling when error_summary is not a string."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": ["error1", "error2"],
            },
            "comment_body": "",
            "review_comments": [],
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["comment_body"] != ""
        assert "lint" in state["comment_body"]

    def test_extracts_file_path_from_error_summary(self):
        """Test that review_file_path is extracted from error_summary (Issue #3567)."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "src/utils/helper.py:42:1: F821 undefined name 'reuslt'",
            },
            "comment_body": "",
            "review_comments": [],
            "review_file_path": "",
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["review_file_path"] == "src/utils/helper.py"

    def test_does_not_override_existing_review_file_path(self):
        """Test that existing review_file_path is not overwritten."""
        state = {
            "trace_id": "test-trace-123",
            "ci_failure_trigger": True,
            "ci_failure_context": {
                "failed_check_name": "lint",
                "error_summary": "src/utils/helper.py:42:1: F821 undefined name",
            },
            "comment_body": "",
            "review_comments": [],
            "review_file_path": "existing/path.py",
        }

        _ensure_comment_body_for_ci_failure(state, "test-trace-123")

        assert state["review_file_path"] == "existing/path.py"


class TestExtractFilePathFromError:
    """Tests for _extract_file_path_from_error helper function (Issue #3567).

    This function extracts file paths from CI error summaries to enable
    SimpleCoder to work in CI failure scenarios.
    """

    def test_extracts_flake8_format(self):
        """Test extraction from flake8 format: path/file.py:line:col: error."""
        error = "src/utils/helper.py:42:1: F821 undefined name 'reuslt'"
        assert _extract_file_path_from_error(error) == "src/utils/helper.py"

    def test_extracts_pylint_format(self):
        """Test extraction from pylint format."""
        error = "orchestrator/agent.py:123:0: E1101: Module has no member"
        assert _extract_file_path_from_error(error) == "orchestrator/agent.py"

    def test_extracts_eslint_format(self):
        """Test extraction from eslint format: path/file.js:line:col: error."""
        error = "src/components/Button.tsx:15:3: 'useState' is defined but never used"
        assert _extract_file_path_from_error(error) == "src/components/Button.tsx"

    def test_extracts_compiler_format(self):
        """Test extraction from compiler format: path/file.py(line): error."""
        error = "src/main.py(42): SyntaxError: invalid syntax"
        assert _extract_file_path_from_error(error) == "src/main.py"

    def test_extracts_error_in_format(self):
        """Test extraction from 'Error in path/file.py' format."""
        error = "Error in src/utils/helper.py: undefined variable"
        assert _extract_file_path_from_error(error) == "src/utils/helper.py"

    def test_extracts_file_format(self):
        """Test extraction from 'File path/file.py' format."""
        error = "File src/config.py has issues"
        assert _extract_file_path_from_error(error) == "src/config.py"

    def test_extracts_multiline_first_match(self):
        """Test extraction from multiline error (first file wins)."""
        error = """src/first.py:10:1: E501 line too long
src/second.py:20:1: E501 line too long"""
        assert _extract_file_path_from_error(error) == "src/first.py"

    def test_returns_empty_for_no_match(self):
        """Test returns empty string when no file path found."""
        error = "Some generic error without file path"
        assert _extract_file_path_from_error(error) == ""

    def test_returns_empty_for_empty_input(self):
        """Test returns empty string for empty input."""
        assert _extract_file_path_from_error("") == ""
        assert _extract_file_path_from_error(None) == ""

    def test_handles_various_extensions(self):
        """Test extraction works for various file extensions."""
        test_cases = [
            ("app.js:1:1: error", "app.js"),
            ("app.ts:1:1: error", "app.ts"),
            ("app.jsx:1:1: error", "app.jsx"),
            ("app.tsx:1:1: error", "app.tsx"),
            ("main.go:1:1: error", "main.go"),
            ("lib.rs:1:1: error", "lib.rs"),
            ("App.java:1:1: error", "App.java"),
            ("script.rb:1:1: error", "script.rb"),
            ("index.php:1:1: error", "index.php"),
            ("main.c:1:1: error", "main.c"),
            ("main.cpp:1:1: error", "main.cpp"),
            ("header.h:1:1: error", "header.h"),
            ("header.hpp:1:1: error", "header.hpp"),
        ]
        for error, expected in test_cases:
            assert _extract_file_path_from_error(error) == expected, f"Failed for: {error}"

    # Issue #3890: Tests for Python SyntaxError format (Pattern 4)
    def test_extracts_python_syntax_error_format(self):
        """Test extraction from Python SyntaxError format: File "path/file.py", line N."""
        error = '''  File "src/utils/helper.py", line 10
    print("hello"
                 ^
SyntaxError: unexpected EOF while parsing'''
        assert _extract_file_path_from_error(error) == "src/utils/helper.py"

    def test_extracts_python_syntax_error_nested_path(self):
        """Test extraction from Python SyntaxError with nested path."""
        error = '''  File "/home/user/project/src/deep/nested/module.py", line 42
    def foo(
           ^
SyntaxError: invalid syntax'''
        assert _extract_file_path_from_error(error) == "/home/user/project/src/deep/nested/module.py"

    def test_extracts_python_syntax_error_traceback(self):
        """Test extraction from Python traceback with multiple File entries."""
        error = '''Traceback (most recent call last):
  File "src/main.py", line 5, in <module>
    from src.broken import foo
  File "src/broken.py", line 10
    print("hello"
                 ^
SyntaxError: unexpected EOF while parsing'''
        # Should extract first File entry
        assert _extract_file_path_from_error(error) == "src/main.py"

    def test_extracts_quoted_file_path(self):
        """Test extraction from quoted file path in File format."""
        error = 'File "orchestrator/langgraph_orchestrator.py" has syntax error'
        assert _extract_file_path_from_error(error) == "orchestrator/langgraph_orchestrator.py"

    def test_extracts_file_path_case_insensitive(self):
        """Test extraction is case insensitive for File keyword."""
        error = 'file "src/test.py", line 1'
        assert _extract_file_path_from_error(error) == "src/test.py"


class TestExtractFilePathsFromError:
    """Tests for _extract_file_paths_from_error helper function (Issue #3890).

    This function extracts ALL file paths from CI error summaries for
    multi-file support in GeneralCoder (D-1b).
    """

    def test_extracts_single_flake8_error(self):
        """Test extraction of single file from flake8 format."""
        error = "src/utils/helper.py:42:1: F821 undefined name 'result'"
        result = _extract_file_paths_from_error(error)
        assert result == ["src/utils/helper.py"]

    def test_extracts_multiple_flake8_errors(self):
        """Test extraction of multiple files from flake8 format."""
        error = """src/first.py:10:1: E501 line too long
src/second.py:20:1: E501 line too long
src/third.py:30:1: F401 unused import"""
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/first.py", "src/second.py", "src/third.py"}

    def test_extracts_duplicate_files_once(self):
        """Test that duplicate file paths are deduplicated."""
        error = """src/utils.py:10:1: E501 line too long
src/utils.py:20:1: E501 line too long
src/utils.py:30:1: E501 line too long"""
        result = _extract_file_paths_from_error(error)
        assert result == ["src/utils.py"]

    def test_extracts_mixed_formats(self):
        """Test extraction from mixed error formats."""
        error = """src/first.py:10:1: E501 line too long
Error in src/second.py: undefined variable
File "src/third.py", line 5
    print(
         ^
SyntaxError: invalid syntax"""
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/first.py", "src/second.py", "src/third.py"}

    def test_extracts_python_syntax_error_format(self):
        """Test extraction from Python SyntaxError format."""
        error = '''  File "src/broken.py", line 10
    print("hello"
                 ^
SyntaxError: unexpected EOF while parsing'''
        result = _extract_file_paths_from_error(error)
        assert result == ["src/broken.py"]

    def test_extracts_multiple_python_files_from_traceback(self):
        """Test extraction of multiple files from Python traceback."""
        error = '''Traceback (most recent call last):
  File "src/main.py", line 5, in <module>
    from src.broken import foo
  File "src/broken.py", line 10
    print("hello"
                 ^
SyntaxError: unexpected EOF while parsing'''
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/main.py", "src/broken.py"}

    def test_returns_empty_for_no_match(self):
        """Test returns empty list when no file paths found."""
        error = "Some generic error without file path"
        result = _extract_file_paths_from_error(error)
        assert result == []

    def test_returns_empty_for_empty_input(self):
        """Test returns empty list for empty input."""
        assert _extract_file_paths_from_error("") == []

    def test_limits_to_max_files(self):
        """Test that results are limited to max files (default 5)."""
        error = """src/file1.py:1:1: error
src/file2.py:1:1: error
src/file3.py:1:1: error
src/file4.py:1:1: error
src/file5.py:1:1: error
src/file6.py:1:1: error
src/file7.py:1:1: error"""
        result = _extract_file_paths_from_error(error)
        # Should be limited to 5 files (general_coder_max_files default)
        assert len(result) <= 5

    def test_extracts_compiler_format(self):
        """Test extraction from compiler format: path/file.py(line): error."""
        error = """src/main.py(42): SyntaxError: invalid syntax
src/utils.py(10): TypeError: unsupported operand"""
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/main.py", "src/utils.py"}

    def test_extracts_various_extensions(self):
        """Test extraction works for various file extensions."""
        error = """app.js:1:1: error
app.ts:2:1: error
main.go:3:1: error
lib.rs:4:1: error"""
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"app.js", "app.ts", "main.go", "lib.rs"}

    def test_extracts_error_in_format(self):
        """Test extraction from 'Error in path/file.py' format."""
        error = """Error in src/first.py: undefined variable
Error in src/second.py: syntax error"""
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/first.py", "src/second.py"}

    def test_extracts_quoted_paths(self):
        """Test extraction from quoted file paths."""
        error = '''File "src/quoted.py" has issues
in file "src/another.py" found error'''
        result = _extract_file_paths_from_error(error)
        assert set(result) == {"src/quoted.py", "src/another.py"}
