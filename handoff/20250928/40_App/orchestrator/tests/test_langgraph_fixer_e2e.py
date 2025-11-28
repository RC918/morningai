#!/usr/bin/env python3
"""
LangGraph Fixer Node E2E Integration Tests

Phase 2 Step C Enhancement: Tests for fixer_node integration with AutoFixer
in the actual LangGraph orchestrator workflow.

Tests cover:
1. Fixer node routing in orchestrator graph
2. AutoFixer canary rollout behavior
3. MAX_FIXER_RETRIES limit enforcement
4. State transitions through fixer_node
5. Error handling and recovery paths
"""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Optional

from langgraph_orchestrator import (
    AgentState,
    fixer_node,
    should_continue_execution,
    should_retry_or_finish,
    create_orchestrator_graph,
    MAX_FIXER_RETRIES
)


@dataclass
class MockSettings:
    """Mock settings for testing AutoFixer behavior"""
    enable_project_engineer_fixer: bool = False
    project_engineer_fixer_percent: int = 0
    enable_project_engineer_codegen: bool = False
    workspace_path: str = "."
    openai_api_key: str = "test-key"
    github_repo: str = "RC918/morningai"


def create_test_state(
    trace_id: str = "test-trace-123",
    retry_count: int = 0,
    error: Optional[str] = None,
    ci_state: str = "failure",
    pr_number: int = 123
) -> AgentState:
    """Create a test AgentState with common defaults"""
    return {
        "messages": [],
        "goal": "Fix CI failures",
        "trace_id": trace_id,
        "repo": "RC918/morningai",
        "branch": "test-branch",
        "plan": ["Step 1", "Step 2"],
        "current_step": 2,
        "pr_url": f"https://github.com/RC918/morningai/pull/{pr_number}",
        "pr_number": pr_number,
        "ci_state": ci_state,
        "ci_checks": {"lint": "failure"},
        "error": error,
        "retry_count": retry_count,
        "final_result": {}
    }


class TestFixerNodeRouting:
    """Tests for fixer_node routing in the orchestrator graph"""

    def test_graph_contains_fixer_node(self):
        """Test that orchestrator graph contains fixer node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]

        assert any("fixer" in node_id for node_id in node_ids), \
            "Fixer node not found in orchestrator graph"

    def test_should_continue_execution_routes_to_fix_on_error(self):
        """Test that errors route to fixer node when retries available"""
        state = create_test_state(error="CI failed", retry_count=0)
        result = should_continue_execution(state)
        assert result == "fix"

    def test_should_continue_execution_routes_to_finalize_on_max_retries(self):
        """Test that max retries routes to finalizer"""
        state = create_test_state(error="CI failed", retry_count=MAX_FIXER_RETRIES)
        result = should_continue_execution(state)
        assert result == "finalize"

    def test_should_retry_or_finish_routes_to_fix_on_ci_failure(self):
        """Test that CI failure routes to fixer node"""
        state = create_test_state(ci_state="failure", retry_count=0)
        result = should_retry_or_finish(state)
        assert result == "fix"

    def test_should_retry_or_finish_routes_to_finalize_on_success(self):
        """Test that CI success routes to finalizer"""
        state = create_test_state(ci_state="success", error=None)
        result = should_retry_or_finish(state)
        assert result == "finalize"

    def test_should_retry_or_finish_routes_to_finalize_on_max_retries(self):
        """Test that max retries routes to finalizer even on failure"""
        state = create_test_state(
            ci_state="failure",
            retry_count=MAX_FIXER_RETRIES
        )
        result = should_retry_or_finish(state)
        assert result == "finalize"


class TestFixerNodeBehavior:
    """Tests for fixer_node behavior with AutoFixer"""

    def test_fixer_node_increments_retry_count(self):
        """Test that fixer_node increments retry_count"""
        state = create_test_state(retry_count=0)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            assert result["retry_count"] == 1

    def test_fixer_node_respects_max_retries(self):
        """Test that fixer_node stops at MAX_FIXER_RETRIES"""
        state = create_test_state(retry_count=MAX_FIXER_RETRIES)

        result = fixer_node(state)

        assert "Max retries" in (result.get("error") or "")
        assert result["retry_count"] == MAX_FIXER_RETRIES

    def test_fixer_node_calls_autofixer_when_enabled(self):
        """Test that fixer_node calls AutoFixer when should_run_for_task returns True"""
        state = create_test_state(retry_count=0)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = True
            mock_fixer.run_auto_fix_sync.return_value = state
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            fixer_node(state)

            mock_fixer.should_run_for_task.assert_called_once()
            mock_fixer.run_auto_fix_sync.assert_called_once()

    def test_fixer_node_skips_autofixer_when_disabled(self):
        """Test that fixer_node skips AutoFixer when should_run_for_task returns False"""
        state = create_test_state(retry_count=0)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            mock_fixer.should_run_for_task.assert_called_once()
            mock_fixer.run_auto_fix_sync.assert_not_called()
            assert result["retry_count"] == 1

    def test_fixer_node_handles_autofixer_import_error(self):
        """Test that fixer_node handles AutoFixer import error gracefully"""
        state = create_test_state(retry_count=0)

        with patch.dict("sys.modules", {"project_engineer.fixer_integration": None}):
            with patch("project_engineer.fixer_integration.AutoFixer", side_effect=ImportError("Module not found")):
                result = fixer_node(state)

                assert result["retry_count"] == 1
                assert len(result["messages"]) > 0

    def test_fixer_node_handles_autofixer_exception(self):
        """Test that fixer_node handles AutoFixer exceptions gracefully"""
        state = create_test_state(retry_count=0)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = True
            mock_fixer.run_auto_fix_sync.side_effect = Exception("AutoFixer crashed")
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            assert "AutoFixer" in (result.get("error") or "")
            assert result["retry_count"] == 1


class TestAutoFixerCanaryRollout:
    """Tests for AutoFixer canary rollout behavior"""

    def test_autofixer_disabled_by_flag(self):
        """Test AutoFixer is disabled when ENABLE_PROJECT_ENGINEER_FIXER=false"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=False,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        assert fixer.should_run_for_task(state) is False

    def test_autofixer_disabled_by_zero_percent(self):
        """Test AutoFixer is disabled when PROJECT_ENGINEER_FIXER_PERCENT=0"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=0
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        assert fixer.should_run_for_task(state) is False

    def test_autofixer_enabled_at_100_percent(self):
        """Test AutoFixer is enabled for all tasks when percent=100"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        assert fixer.should_run_for_task(state) is True

    def test_autofixer_canary_is_deterministic(self):
        """Test that canary bucket is deterministic for same trace_id"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=50
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state(trace_id="deterministic-test-id")

        results = [fixer.should_run_for_task(state) for _ in range(5)]

        assert all(r == results[0] for r in results), \
            "Canary routing should be deterministic"

    @patch("project_engineer.fixer_integration.hashlib.md5")
    def test_autofixer_uses_pr_number_for_canary(self, mock_md5):
        """Test that canary uses pr_number when available, falling back to trace_id"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=50
        )
        fixer = AutoFixer(settings=settings)

        # Setup mock to return a valid hash object
        mock_hash_obj = MagicMock()
        mock_hash_obj.hexdigest.return_value = '0' * 32
        mock_md5.return_value = mock_hash_obj

        # Test with pr_number - should use pr_number as key
        state_with_pr = create_test_state(pr_number=456, trace_id="should-be-ignored")
        fixer.should_run_for_task(state_with_pr)
        mock_md5.assert_called_once_with(b'456')
        mock_md5.reset_mock()

        # Test without pr_number - should fall back to trace_id
        state_without_pr = create_test_state(trace_id="should-be-used")
        state_without_pr["pr_number"] = None
        fixer.should_run_for_task(state_without_pr)
        mock_md5.assert_called_once_with(b'should-be-used')


class TestMaxRetriesEnforcement:
    """Tests for MAX_FIXER_RETRIES enforcement"""

    def test_max_retries_constant_is_valid(self):
        """Test that MAX_FIXER_RETRIES constant is a positive integer"""
        assert isinstance(MAX_FIXER_RETRIES, int)
        assert MAX_FIXER_RETRIES > 0

    def test_fixer_node_uses_max_retries_constant(self):
        """Test that fixer_node uses MAX_FIXER_RETRIES constant"""
        # Test at boundary
        state_at_limit = create_test_state(retry_count=MAX_FIXER_RETRIES)
        result = fixer_node(state_at_limit)
        assert "Max retries" in (result.get("error") or "")

        # Test below boundary
        state_below_limit = create_test_state(retry_count=MAX_FIXER_RETRIES - 1)
        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state_below_limit)
            assert result["retry_count"] == MAX_FIXER_RETRIES

    def test_conditional_edges_use_max_retries_constant(self):
        """Test that conditional edge functions use MAX_FIXER_RETRIES"""
        # At max retries, should route to finalize
        state_at_max = create_test_state(
            error="Some error",
            retry_count=MAX_FIXER_RETRIES
        )
        assert should_continue_execution(state_at_max) == "finalize"

        # Below max retries, should route to fix
        state_below_max = create_test_state(
            error="Some error",
            retry_count=MAX_FIXER_RETRIES - 1
        )
        assert should_continue_execution(state_below_max) == "fix"


class TestStateTransitions:
    """Tests for state transitions through fixer_node"""

    def test_fixer_node_preserves_trace_id(self):
        """Test that fixer_node preserves trace_id"""
        trace_id = "preserve-trace-123"
        state = create_test_state(trace_id=trace_id)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            assert result["trace_id"] == trace_id

    def test_fixer_node_adds_message(self):
        """Test that fixer_node adds a message to state"""
        state = create_test_state()
        initial_message_count = len(state["messages"])

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            assert len(result["messages"]) > initial_message_count

    def test_fixer_node_updates_pr_info_on_success(self):
        """Test that fixer_node updates PR info when AutoFixer succeeds"""
        state = create_test_state()
        new_pr_number = 999
        new_pr_url = "https://github.com/RC918/morningai/pull/999"

        updated_state = state.copy()
        updated_state["pr_number"] = new_pr_number
        updated_state["pr_url"] = new_pr_url
        updated_state["error"] = None

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = True
            mock_fixer.run_auto_fix_sync.return_value = updated_state
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            assert result["pr_number"] == new_pr_number
            assert result["pr_url"] == new_pr_url


class TestOrchestratorWorkflowPaths:
    """Tests for complete orchestrator workflow paths involving fixer_node"""

    def test_workflow_path_success_no_fixer(self):
        """Test workflow path: planner -> executor -> ci_monitor -> finalizer (success)"""
        state = create_test_state(ci_state="success", error=None)

        # CI success should route to finalizer
        result = should_retry_or_finish(state)
        assert result == "finalize"

    def test_workflow_path_failure_to_fixer(self):
        """Test workflow path: ci_monitor -> fixer on CI failure"""
        state = create_test_state(ci_state="failure", retry_count=0)

        result = should_retry_or_finish(state)
        assert result == "fix"

    def test_workflow_path_fixer_to_executor(self):
        """Test that fixer_node routes back to executor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        # Find edge from fixer to executor
        fixer_edges = [e for e in edges if "fixer" in str(e.get("source", ""))]
        assert len(fixer_edges) > 0, "Fixer node should have outgoing edges"

    def test_workflow_path_max_retries_to_finalize(self):
        """Test workflow path: fixer -> finalizer on max retries"""
        state = create_test_state(
            ci_state="failure",
            error="Persistent failure",
            retry_count=MAX_FIXER_RETRIES
        )

        # At max retries, should route to finalize
        result = should_retry_or_finish(state)
        assert result == "finalize"


class TestErrorRecovery:
    """Tests for error recovery paths"""

    def test_fixer_node_recovers_from_autofixer_error(self):
        """Test that fixer_node recovers from AutoFixer errors"""
        state = create_test_state(retry_count=0)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = True
            mock_fixer.run_auto_fix_sync.side_effect = RuntimeError("Unexpected error")
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            result = fixer_node(state)

            # Should still increment retry count
            assert result["retry_count"] == 1
            # Should set error
            assert result.get("error") is not None
            # Should add message
            assert len(result["messages"]) > 0

    def test_fixer_node_handles_missing_settings(self):
        """Test that fixer_node handles missing settings gracefully"""
        state = create_test_state(retry_count=0)

        with patch("common.config.settings.settings", None):
            # Should not crash even with missing settings
            result = fixer_node(state)
            assert result["retry_count"] == 1


class TestLoggingAndObservability:
    """Tests for logging and observability"""

    def test_fixer_node_logs_retry_count(self):
        """Test that fixer_node logs retry count"""
        state = create_test_state(retry_count=1)

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer
            MockAutoFixer.MAX_FIX_RETRIES = MAX_FIXER_RETRIES

            with patch("langgraph_orchestrator.logger") as mock_logger:
                fixer_node(state)

                # Verify logging was called
                assert mock_logger.info.called or mock_logger.warning.called

    def test_autofixer_logs_disabled_reason(self):
        """Test that AutoFixer logs disabled reason"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=False,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        with patch("project_engineer.fixer_integration.logger") as mock_logger:
            fixer.should_run_for_task(state)

            # Verify debug log was called with disabled reason
            assert mock_logger.debug.called or mock_logger.info.called

    def test_fixer_node_logs_max_retries_reached(self):
        """Test that fixer_node logs autofixer_max_retries_reached when max retries exceeded"""
        state = create_test_state(retry_count=MAX_FIXER_RETRIES, error="Previous error")

        with patch("langgraph_orchestrator.logger") as mock_logger:
            result = fixer_node(state)

            # Verify warning log was called
            assert mock_logger.warning.called

            # Check that the log message contains max_retries_reached indicator
            call_args = mock_logger.warning.call_args
            log_message = call_args[0][0] if call_args[0] else ""
            assert "Max retries reached" in log_message
            assert "autofixer_max_retries_reached=true" in log_message

            # Verify extra contains autofixer_max_retries_reached
            extra = call_args[1].get("extra", {}) if call_args[1] else {}
            assert extra.get("autofixer_max_retries_reached") is True

            # Verify state has error and message
            assert result.get("error") is not None
            assert len(result.get("messages", [])) > 0

    def test_fixer_node_max_retries_message_includes_last_error(self):
        """Test that max retries message includes the last error"""
        last_error = "CI check failed: lint errors"
        state = create_test_state(retry_count=MAX_FIXER_RETRIES, error=last_error)

        result = fixer_node(state)

        # Verify the error is preserved
        assert result.get("error") == last_error

        # Verify message includes last error
        messages = result.get("messages", [])
        assert len(messages) > 0
        last_message = messages[-1].content if messages else ""
        assert last_error in last_message or "gave up" in last_message


class TestSafetyRulesEnforcement:
    """Tests for Phase 2 Step B safety rules enforcement in AutoFixer"""

    def test_autofixer_logs_whitelist_enforcement_when_enabled(self):
        """Test that AutoFixer logs whitelist enforcement and runs the agent when codegen is enabled"""
        import asyncio
        from unittest.mock import MagicMock
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=True
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        # Create mock for ProjectEngineerAgent
        mock_agent_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.pr_number = 123
        mock_result.pr_url = "http://example.com/pr/123"

        async def mock_run_task(*args, **kwargs):
            return [mock_result]

        mock_agent_instance.run_task = mock_run_task

        with patch("project_engineer.fixer_integration.logger") as mock_logger, \
             patch("project_engineer.agent.ProjectEngineerAgent", return_value=mock_agent_instance), \
             patch.object(fixer, "_create_dev_agent", return_value=MagicMock()):

            result = asyncio.run(fixer._run_project_engineer("Fix lint", "RC918/morningai", state))

            # Verify info log for whitelist enforcement was called
            info_calls = mock_logger.info.call_args_list
            whitelist_log_found = any(
                "autofixer_safety_check=whitelist_enforced" in str(call)
                for call in info_calls
            )
            assert whitelist_log_found, "Expected whitelist enforcement log not found"

            # Verify result indicates success
            assert result.get("success") is True
            assert result.get("pr_number") == 123

    def test_autofixer_logs_safety_check_when_codegen_disabled(self):
        """Test that AutoFixer logs safety check when codegen is disabled"""
        import asyncio
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=False
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        with patch("project_engineer.fixer_integration.logger") as mock_logger:
            # Call _run_project_engineer directly
            result = asyncio.run(fixer._run_project_engineer("Fix lint", "RC918/morningai", state))

            # Verify warning log was called
            assert mock_logger.warning.called

            # Check that the log contains safety check indicator
            call_args = mock_logger.warning.call_args
            log_message = call_args[0][0] if call_args[0] else ""
            assert "autofixer_safety_check=codegen_disabled" in log_message

            # Verify result indicates failure due to codegen disabled
            assert result.get("success") is False
            assert "Code generation disabled" in result.get("error", "")

    def test_safe_tasks_whitelist_exists(self):
        """Test that safe_tasks whitelist is properly defined"""
        from project_engineer.safe_tasks import SAFE_TASK_TYPES, is_safe_task

        # Verify whitelist exists and has expected tasks
        assert len(SAFE_TASK_TYPES) > 0
        assert "fix_lint" in SAFE_TASK_TYPES
        assert "documentation_update" in SAFE_TASK_TYPES
        assert "test_generation" in SAFE_TASK_TYPES

        # Verify is_safe_task function works
        assert is_safe_task("fix_lint") is True
        assert is_safe_task("database_migration") is False

    def test_autofixer_respects_codegen_flag(self):
        """Test that AutoFixer respects ENABLE_PROJECT_ENGINEER_CODEGEN flag"""
        import asyncio
        from project_engineer.fixer_integration import AutoFixer

        # Test with codegen disabled
        settings_disabled = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=False
        )
        fixer_disabled = AutoFixer(settings=settings_disabled)
        state = create_test_state()

        result = asyncio.run(fixer_disabled._run_project_engineer("Fix lint", "RC918/morningai", state))
        assert result.get("success") is False
        assert "Code generation disabled" in result.get("error", "")


class TestAsyncWrapperOptimization:
    """Tests for PR-C: Async wrapper optimization in run_auto_fix_sync"""

    def test_run_auto_fix_sync_uses_direct_path_when_no_loop(self):
        """Test that run_auto_fix_sync uses asyncio.run when no event loop is running"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=False
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        with patch("project_engineer.fixer_integration.logger") as mock_logger:
            # Call run_auto_fix_sync from outside any event loop
            # This should use the "direct" path (asyncio.run)
            fixer.run_auto_fix_sync(state)

            # Verify debug log for direct path was called
            debug_calls = mock_logger.debug.call_args_list
            direct_log_found = any(
                "autofixer_async_bridge=direct" in str(call)
                for call in debug_calls
            )
            assert direct_log_found, "Expected direct path log not found"

    def test_run_auto_fix_sync_uses_thread_path_when_in_loop(self):
        """Test that run_auto_fix_sync uses background thread when called from running loop"""
        import asyncio
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=False
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        async def call_from_async_context():
            with patch("project_engineer.fixer_integration.logger") as mock_logger:
                # Call run_auto_fix_sync from within a running event loop
                # This should use the "thread" path
                result = fixer.run_auto_fix_sync(state)

                # Verify info log for thread path was called
                info_calls = mock_logger.info.call_args_list
                thread_log_found = any(
                    "autofixer_async_bridge=thread" in str(call)
                    for call in info_calls
                )
                return thread_log_found, result

        thread_log_found, result = asyncio.run(call_from_async_context())
        assert thread_log_found, "Expected thread path log not found"

    def test_get_autofixer_executor_reuses_executor(self):
        """Test that _get_autofixer_executor returns the same executor instance"""
        from project_engineer.fixer_integration import _get_autofixer_executor

        executor1 = _get_autofixer_executor()
        executor2 = _get_autofixer_executor()

        # Should return the same instance (reused)
        assert executor1 is executor2

    def test_run_auto_fix_sync_returns_state(self):
        """Test that run_auto_fix_sync returns updated state correctly"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=False
        )
        fixer = AutoFixer(settings=settings)
        state = create_test_state()

        result = fixer.run_auto_fix_sync(state)

        # Should return a dict (the state)
        assert isinstance(result, dict)
        # Should have trace_id preserved
        assert result.get("trace_id") == state.get("trace_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
