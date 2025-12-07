"""
Tests for DeepWiki integration in AutonomousExecutor.

Issue #1824: DeepWiki 知識庫與 Session Insights
"""

from unittest.mock import Mock, patch
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meta_agent.autonomous_executor import (
    AutonomousExecutor,
    ExecutionResult,
    ExecutionStatus,
)
from meta_agent.task_planner import TaskPlan, SubTaskStatus


class TestGenerateSessionInsights:
    """Tests for _generate_session_insights method."""

    def _create_mock_plan(self) -> TaskPlan:
        """Create a mock TaskPlan for testing."""
        plan = Mock(spec=TaskPlan)
        plan.plan_id = "test-plan-123"
        plan.subtasks = [
            Mock(
                task_id="task-1",
                description="Test task 1",
                status=SubTaskStatus.COMPLETED,
            ),
            Mock(
                task_id="task-2",
                description="Test task 2",
                status=SubTaskStatus.FAILED,
            ),
        ]
        return plan

    def _create_executor_with_execution(self) -> AutonomousExecutor:
        """Create an executor with a mock execution result."""
        executor = AutonomousExecutor()
        executor.current_execution = ExecutionResult(
            execution_id="exec-123",
            plan_id="test-plan-123",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
            tasks_completed=1,
            tasks_failed=2,
            tasks_skipped=0,
            total_duration_seconds=10.5,
            errors=["Task task-2: Test error 1", "Task task-3: Test error 2"],
        )
        return executor

    def test_generate_session_insights_disabled(self):
        """Test insights are skipped when DeepWiki is disabled."""
        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        with patch("meta_agent.autonomous_executor.settings") as mock_settings:
            mock_settings.enable_deepwiki = False

            executor._generate_session_insights(plan)

            # Should not have deepwiki_insights in metadata
            assert "deepwiki_insights" not in executor.current_execution.metadata

    def test_generate_session_insights_no_settings(self):
        """Test insights are skipped when settings is None."""
        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        with patch("meta_agent.autonomous_executor.settings", None):
            executor._generate_session_insights(plan)

            # Should not have deepwiki_insights in metadata
            assert "deepwiki_insights" not in executor.current_execution.metadata

    @patch("meta_agent.autonomous_executor.settings")
    def test_generate_session_insights_enabled(self, mock_settings):
        """Test insights are generated when DeepWiki is enabled."""
        mock_settings.enable_deepwiki = True

        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        mock_insight = Mock()
        mock_insight.session_id = "exec-123"
        mock_insight.insight_type = "execution_analysis"
        mock_insight.summary = "Execution completed with 1 failure"
        mock_insight.recommendations = ["Review failed task"]
        mock_insight.metrics = {"tasks_completed": 1, "tasks_failed": 1}

        mock_deepwiki = Mock()
        mock_deepwiki.get_session_insights.return_value = mock_insight

        # Patch the import inside the method by patching the module that gets imported
        with patch.dict(
            "sys.modules",
            {"deepwiki.service": Mock(get_deepwiki_service=Mock(return_value=mock_deepwiki))},
        ):
            executor._generate_session_insights(plan)

            # Should have deepwiki_insights in metadata
            assert "deepwiki_insights" in executor.current_execution.metadata
            insights = executor.current_execution.metadata["deepwiki_insights"]
            assert insights["session_id"] == "exec-123"
            assert insights["insight_type"] == "execution_analysis"
            assert insights["summary"] == "Execution completed with 1 failure"
            assert insights["recommendations"] == ["Review failed task"]

    @patch("meta_agent.autonomous_executor.settings")
    def test_generate_session_insights_import_error(self, mock_settings):
        """Test insights handle ImportError gracefully."""
        mock_settings.enable_deepwiki = True

        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        # Simulate ImportError by making the import fail
        mock_module = Mock()
        mock_module.get_deepwiki_service = Mock(side_effect=ImportError("deepwiki not available"))

        with patch.dict("sys.modules", {"deepwiki.service": mock_module}):
            # Should not raise exception
            executor._generate_session_insights(plan)

            # Should not have deepwiki_insights in metadata
            assert "deepwiki_insights" not in executor.current_execution.metadata

    @patch("meta_agent.autonomous_executor.settings")
    def test_generate_session_insights_exception(self, mock_settings):
        """Test insights handle exceptions gracefully."""
        mock_settings.enable_deepwiki = True

        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        mock_deepwiki = Mock()
        mock_deepwiki.get_session_insights.side_effect = Exception("Service error")

        mock_module = Mock()
        mock_module.get_deepwiki_service = Mock(return_value=mock_deepwiki)

        with patch.dict("sys.modules", {"deepwiki.service": mock_module}):
            # Should not raise exception
            executor._generate_session_insights(plan)

            # Should not have deepwiki_insights in metadata
            assert "deepwiki_insights" not in executor.current_execution.metadata

    @patch("meta_agent.autonomous_executor.settings")
    def test_generate_session_insights_passes_correct_data(self, mock_settings):
        """Test insights passes correct execution data to DeepWiki."""
        mock_settings.enable_deepwiki = True

        executor = self._create_executor_with_execution()
        plan = self._create_mock_plan()

        mock_insight = Mock()
        mock_insight.session_id = "exec-123"
        mock_insight.insight_type = "execution_analysis"
        mock_insight.summary = "Test summary"
        mock_insight.recommendations = []
        mock_insight.metrics = {}

        mock_deepwiki = Mock()
        mock_deepwiki.get_session_insights.return_value = mock_insight

        mock_module = Mock()
        mock_module.get_deepwiki_service = Mock(return_value=mock_deepwiki)

        with patch.dict("sys.modules", {"deepwiki.service": mock_module}):
            executor._generate_session_insights(plan)

            # Verify get_session_insights was called with correct arguments
            mock_deepwiki.get_session_insights.assert_called_once()
            call_args = mock_deepwiki.get_session_insights.call_args

            assert call_args.kwargs["session_id"] == "exec-123"

            execution_result = call_args.kwargs["execution_result"]
            assert execution_result["status"] == "completed"
            assert execution_result["tasks_completed"] == 1
            assert execution_result["tasks_failed"] == 2
            # Verify all errors are passed (not just the first one)
            assert execution_result["errors"] == [
                "Task task-2: Test error 1",
                "Task task-3: Test error 2",
            ]

            task_plan = call_args.kwargs["task_plan"]
            assert task_plan["plan_id"] == "test-plan-123"
            assert len(task_plan["steps"]) == 2


class TestFinalizeExecutionWithDeepWiki:
    """Tests for _finalize_execution calling _generate_session_insights."""

    def test_finalize_execution_calls_generate_insights(self):
        """Test _finalize_execution calls _generate_session_insights."""
        executor = AutonomousExecutor()
        executor.current_execution = ExecutionResult(
            execution_id="exec-123",
            plan_id="test-plan-123",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )

        plan = Mock(spec=TaskPlan)
        plan.plan_id = "test-plan-123"
        plan.subtasks = []
        plan.get_progress.return_value = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "in_progress": 0,
        }

        with patch.object(
            executor, "_generate_session_insights"
        ) as mock_generate_insights:
            executor._finalize_execution(plan)

            mock_generate_insights.assert_called_once_with(plan)
