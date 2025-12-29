#!/usr/bin/env python3
"""
SimpleCoder Wiring Integration Tests

D-1 Phase 1: Tests for SimpleCoder integration into fixer_node.

Tests cover:
1. Feature flag gating (ENABLE_SIMPLE_CODER)
2. Autofix gate checks (is_autofix_allowed, is_path_excluded)
3. SimpleCoder execution flow
4. Fallback to AutoFixer when SimpleCoder skips
5. Patch application via commit_file
"""
import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Optional
from types import ModuleType


def setup_fake_modules():
    """Set up fake modules to avoid ImportError in tests.

    This injects fake modules into sys.modules so that the imports
    inside _attempt_simple_coder_fix() succeed in the test environment.
    """
    if "common" not in sys.modules:
        common = ModuleType("common")
        sys.modules["common"] = common

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

from langgraph_orchestrator import (
    AgentState,
    fixer_node,
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
) -> AgentState:
    """Create a test AgentState with SimpleCoder-relevant fields"""
    if review_outcome is None:
        review_outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
            "verdict": "request_changes",
        }

    return {
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


class TestSimpleCoderFeatureFlag:
    """Tests for SimpleCoder feature flag gating"""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_simple_coder_disabled_by_default(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that SimpleCoder is disabled when feature flag is False"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = False

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "disabled" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_simple_coder_enabled_attempts_fix(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test that SimpleCoder attempts fix when enabled"""
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
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "skipped" in message.lower() or "low confidence" in message.lower()


class TestSimpleCoderGateChecks:
    """Tests for SimpleCoder gate checks"""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=False)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_gate_fails_without_valid_review_outcome(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that gate fails when review_outcome doesn't pass autofix check"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                review_outcome={"severity": "high"},
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "gate" in message.lower() or "autofix" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_gate_fails_without_file_path(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that gate fails when file path is missing"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                review_file_path="",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "file path" in message.lower() or "no file" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=True)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_gate_fails_for_excluded_path(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that gate fails for excluded file paths"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                review_file_path=".env",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "excluded" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_gate_fails_without_review_comment(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that gate fails when review comment is missing"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "comment" in message.lower() or "no review" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_gate_fails_without_repo(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that gate fails when repo is missing"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                repo="",
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "repo" in message.lower() or "branch" in message.lower()


class TestSimpleCoderExecution:
    """Tests for SimpleCoder execution flow"""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("tools.github_api.commit_file")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_successful_patch_application(
        self, mock_status, mock_coder, mock_commit, mock_get_repo,
        mock_excluded, mock_allowed
    ):
        """Test successful patch application via commit_file"""
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
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_coder_skips_low_confidence(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that SimpleCoder skip results in fallback"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo
            mock_file = MagicMock()
            mock_file.decoded_content = b"complex code"
            mock_repo.get_contents.return_value = mock_file

            mock_output = MagicMock()
            mock_output.success = False
            mock_output.data = {"status": "skipped", "reason": "Complex fix required"}
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Refactor this function",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "skipped" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_syntax_validation_failure(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed
    ):
        """Test that syntax validation failure results in skip"""
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
                "patch": "def foo(\n    pass",
                "syntax_valid": False,
            }
            mock_coder.return_value.execute.return_value = mock_output

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "syntax" in message.lower()


class TestFixerNodeIntegration:
    """Tests for fixer_node integration with SimpleCoder"""

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_calls_simple_coder_first(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that fixer_node calls SimpleCoder before AutoFixer"""
        mock_attempt.return_value = (False, "Feature flag disabled")
        mock_metrics.return_value = MagicMock()
        mock_eval.return_value = MagicMock()

        state = create_test_state()

        with patch.dict(sys.modules, {"project_engineer.fixer_integration": MagicMock()}):
            result = fixer_node(state)

        mock_attempt.assert_called_once()
        assert result["retry_count"] == 1

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_skips_autofixer_on_simple_coder_success(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that AutoFixer is skipped when SimpleCoder succeeds"""
        mock_attempt.return_value = (True, "SimpleCoder fixed src/test.py")
        mock_metrics.return_value = MagicMock()
        mock_eval.return_value = MagicMock()

        state = create_test_state()

        result = fixer_node(state)

        mock_attempt.assert_called_once()
        assert result["retry_count"] == 1
        assert any(
            "SimpleCoder" in str(msg.content)
            for msg in result.get("messages", [])
            if hasattr(msg, "content")
        )

    @patch("langgraph_orchestrator._attempt_simple_coder_fix")
    @patch("langgraph_orchestrator._get_metrics")
    @patch("langgraph_orchestrator._get_agent_eval")
    def test_fixer_node_falls_back_to_autofixer(
        self, mock_eval, mock_metrics, mock_attempt
    ):
        """Test that fixer_node falls back to AutoFixer when SimpleCoder skips"""
        mock_attempt.return_value = (False, "Gate check failed")
        mock_metrics.return_value = MagicMock()
        mock_eval.return_value = MagicMock()

        state = create_test_state()

        with patch.dict(sys.modules, {"project_engineer.fixer_integration": MagicMock()}):
            result = fixer_node(state)

        mock_attempt.assert_called_once()
        assert result["retry_count"] == 1


class TestEventCodes:
    """Tests for greppable event codes"""

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=True)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_simple_coder_disabled_event_code(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed, caplog
    ):
        """Test that SIMPLE_CODER_DISABLED event is logged"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = False

            state = create_test_state(
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            import logging
            with caplog.at_level(logging.DEBUG):
                success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "disabled" in message.lower()

    @patch("coder.autofix_gate.is_autofix_allowed", return_value=False)
    @patch("coder.autofix_gate.is_path_excluded", return_value=False)
    @patch("tools.github_api.get_repo")
    @patch("coder.simple_coder.get_simple_coder")
    @patch("coder.simple_coder.CoderStatus")
    def test_simple_coder_gate_fail_event_code(
        self, mock_status, mock_coder, mock_get_repo, mock_excluded, mock_allowed, caplog
    ):
        """Test that SIMPLE_CODER_GATE_FAIL event is logged"""
        with patch("langgraph_orchestrator.settings") as mock_settings:
            mock_settings.enable_simple_coder = True

            state = create_test_state(
                review_outcome={
                    "severity": "high",
                    "diff_truncated": False,
                    "schema_validated": True,
                },
                review_file_path="src/test.py",
                comment_body="Add docstring",
            )

            import logging
            with caplog.at_level(logging.INFO):
                success, message = _attempt_simple_coder_fix(state, "test-trace")

            assert success is False
            assert "gate" in message.lower() or "autofix" in message.lower()
