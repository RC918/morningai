#!/usr/bin/env python3
"""
Unit tests for ProjectEngineerAgent
Phase 2 Step B: Added tests for code generation mode
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

from project_engineer.agent import ProjectEngineerAgent, TaskResult  # noqa: E402


class TestProjectEngineerAgent:
    """Test suite for ProjectEngineerAgent"""

    def test_init(self):
        """Test ProjectEngineerAgent initialization"""
        agent = ProjectEngineerAgent()

        # Agent should initialize successfully
        assert agent is not None

        # Check that is_safe_task function is available
        assert agent.is_safe_task is not None

    def test_get_status_analysis_mode(self):
        """Test get_status method in analysis mode"""
        agent = ProjectEngineerAgent()
        status = agent.get_status()

        assert status["agent_type"] == "ProjectEngineerAgent"
        assert status["version"] == "1.2.0-phase1-security"
        assert status["mode"] == "analysis_only"
        assert status["workflow_available"] is False
        assert "features" in status
        assert status["features"]["safe_task_gating"] is True
        assert status["features"]["code_generation"] is False

    @pytest.mark.asyncio
    async def test_run_task_empty_description(self):
        """Test run_task with empty description"""
        agent = ProjectEngineerAgent()

        with pytest.raises(ValueError, match="Task description cannot be empty"):
            await agent.run_task("")

    @pytest.mark.asyncio
    async def test_run_task_whitespace_description(self):
        """Test run_task with whitespace-only description"""
        agent = ProjectEngineerAgent()

        with pytest.raises(ValueError, match="Task description cannot be empty"):
            await agent.run_task("   ")

    @pytest.mark.asyncio
    async def test_run_task_basic(self):
        """Test run_task with basic description"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("更新 README.md")

        # Should return at least one result
        assert len(results) > 0

        # Each result should be a TaskResult
        for result in results:
            assert isinstance(result, TaskResult)
            assert result.task_id is not None
            assert result.task_type is not None
            # Status can be success, failed, skipped, or blocked (semantic rules validation)
            assert result.status in ["success", "failed", "skipped", "blocked"]
            assert isinstance(result.is_safe, bool)
            assert result.details is not None

    @pytest.mark.asyncio
    async def test_run_task_with_safe_task(self):
        """Test run_task with a safe task (documentation update)"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("Update README.md with installation instructions")

        assert len(results) > 0

        # In analysis mode, tasks are either skipped (code generation disabled)
        # or blocked (semantic rules validation failed)
        for result in results:
            # Status can be skipped or blocked depending on semantic rules validation
            assert result.status in ["skipped", "blocked"]

    @pytest.mark.asyncio
    async def test_run_task_with_unsafe_task(self):
        """Test run_task with an unsafe task (refactor)"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("重構 payment_service.py 的錯誤處理")

        assert len(results) > 0

        # In analysis mode, tasks are either skipped (code generation disabled)
        # or blocked (semantic rules validation failed)
        for result in results:
            assert result.status in ["skipped", "blocked"]

    @pytest.mark.asyncio
    async def test_run_task_returns_task_results(self):
        """Test that run_task returns properly structured TaskResult objects"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("分析 user_service.py 的性能瓶頸")

        assert len(results) > 0

        for result in results:
            # Check all required fields
            assert hasattr(result, "task_id")
            assert hasattr(result, "task_type")
            assert hasattr(result, "status")
            assert hasattr(result, "is_safe")
            assert hasattr(result, "details")
            assert hasattr(result, "pr_number")
            assert hasattr(result, "pr_url")
            assert hasattr(result, "error")

            # task_id should be a string
            assert isinstance(result.task_id, str)

            # task_type should be a string
            assert isinstance(result.task_type, str)

            # status should be one of the valid values
            # Status can be success, failed, skipped, or blocked (semantic rules validation)
            assert result.status in ["success", "failed", "skipped", "blocked"]

            # is_safe should be a boolean
            assert isinstance(result.is_safe, bool)

            # details should be a non-empty string
            assert isinstance(result.details, str)
            assert len(result.details) > 0

    @pytest.mark.asyncio
    async def test_process_step_basic(self):
        """Test _process_step method"""
        agent = ProjectEngineerAgent()

        result = await agent._process_step(
            step_text="更新 README.md",
            step_index=0,
            trace_id="test-trace-123"
        )

        assert isinstance(result, TaskResult)
        assert result.task_id == "test-trace-123-step-0"
        # Status can be skipped or blocked depending on semantic rules validation
        assert result.status in ["skipped", "blocked"]
        assert result.details is not None

    @pytest.mark.asyncio
    async def test_multiple_tasks(self):
        """Test run_task with multiple tasks in description"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task(
            "1. 更新 README.md\n"
            "2. 添加單元測試\n"
            "3. 修復 lint 錯誤"
        )

        # Should return multiple results (depends on LLM Planner)
        assert len(results) >= 1

        # All should be TaskResult objects
        for result in results:
            assert isinstance(result, TaskResult)


class TestTaskResult:
    """Test suite for TaskResult dataclass"""

    def test_task_result_creation(self):
        """Test TaskResult creation with required fields"""
        result = TaskResult(
            task_id="test-123",
            task_type="documentation_update",
            status="success",
            is_safe=True,
            details="Task completed successfully"
        )

        assert result.task_id == "test-123"
        assert result.task_type == "documentation_update"
        assert result.status == "success"
        assert result.is_safe is True
        assert result.details == "Task completed successfully"
        assert result.pr_number is None
        assert result.pr_url is None
        assert result.error is None

    def test_task_result_with_optional_fields(self):
        """Test TaskResult creation with optional fields"""
        result = TaskResult(
            task_id="test-456",
            task_type="test_generation",
            status="success",
            is_safe=True,
            details="Tests generated",
            pr_number=1234,
            pr_url="https://github.com/org/repo/pull/1234",
            error=None
        )

        assert result.pr_number == 1234
        assert result.pr_url == "https://github.com/org/repo/pull/1234"

    def test_task_result_with_error(self):
        """Test TaskResult creation with error"""
        result = TaskResult(
            task_id="test-789",
            task_type="unknown",
            status="failed",
            is_safe=False,
            details="Task failed",
            error="ImportError: module not found"
        )

        assert result.status == "failed"
        assert result.error == "ImportError: module not found"


class TestRunTaskFunction:
    """Test suite for run_task convenience function"""

    @pytest.mark.asyncio
    async def test_run_task_function(self):
        """Test run_task convenience function"""
        from project_engineer.agent import run_task

        results = await run_task("更新 README.md")

        assert len(results) > 0
        assert all(isinstance(r, TaskResult) for r in results)

    @pytest.mark.asyncio
    async def test_run_task_function_with_repo(self):
        """Test run_task function with custom repo"""
        from project_engineer.agent import run_task

        results = await run_task("更新文檔", repo="test/repo")

        assert len(results) > 0


def _can_import_code_generation_workflow():
    """Check if CodeGenerationWorkflow can be imported"""
    try:
        from agents.dev_agent.workflows import code_generation_workflow  # noqa: F401
        return True
    except ImportError:
        return False


# Skip code generation tests if langgraph is not available
requires_langgraph = pytest.mark.skipif(
    not _can_import_code_generation_workflow(),
    reason="CodeGenerationWorkflow requires langgraph which is not available in test environment"
)


class TestProjectEngineerAgentCodeGeneration:
    """Test suite for code generation mode (Phase 2 Step B)"""

    def test_init_with_code_generation_disabled(self):
        """Test initialization with code generation disabled (default)"""
        agent = ProjectEngineerAgent()

        assert agent.enable_code_generation is False
        assert agent.mode == "analysis_only"
        assert agent.workflow is None

    def test_init_with_code_generation_enabled_no_dev_agent(self):
        """Test initialization fails without dev_agent"""
        with pytest.raises(ValueError, match="dev_agent required"):
            ProjectEngineerAgent(enable_code_generation=True)

    @requires_langgraph
    def test_init_with_code_generation_enabled(self):
        """Test initialization with code generation enabled"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow_instance = MagicMock()
            MockWorkflow.return_value = mock_workflow_instance

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            assert agent.enable_code_generation is True
            assert agent.mode == "execution"
            assert agent.workflow is not None
            MockWorkflow.assert_called_once_with(mock_dev_agent)

    @requires_langgraph
    def test_get_status_execution_mode(self):
        """Test get_status() in execution mode"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            status = agent.get_status()

            assert status["mode"] == "execution"
            assert status["workflow_available"] is True
            assert status["features"]["code_generation"] is True

    @requires_langgraph
    @pytest.mark.asyncio
    async def test_execute_code_generation_success(self):
        """Test successful code generation execution"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow = MagicMock()
            mock_workflow.execute = AsyncMock(return_value={
                "error": None,
                "pr_number": 1234,
                "pr_url": "https://github.com/test/repo/pull/1234"
            })
            MockWorkflow.return_value = mock_workflow

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            result = await agent._execute_code_generation(
                step_text="Add unit tests",
                task_type="test_generation",
                task_id="test-123",
                trace_id="trace-456"
            )

            assert result.status == "success"
            assert result.pr_number == 1234
            assert result.pr_url == "https://github.com/test/repo/pull/1234"
            assert result.is_safe is True

    @requires_langgraph
    @pytest.mark.asyncio
    async def test_execute_code_generation_failure(self):
        """Test code generation execution failure"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow = MagicMock()
            mock_workflow.execute = AsyncMock(return_value={
                "error": "Security validation failed"
            })
            MockWorkflow.return_value = mock_workflow

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            result = await agent._execute_code_generation(
                step_text="Add unit tests",
                task_type="test_generation",
                task_id="test-123",
                trace_id="trace-456"
            )

            assert result.status == "failed"
            assert result.error == "Security validation failed"
            assert result.is_safe is True

    @requires_langgraph
    @pytest.mark.asyncio
    async def test_execute_code_generation_exception(self):
        """Test code generation execution with exception"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow = MagicMock()
            mock_workflow.execute = AsyncMock(side_effect=Exception("Workflow crashed"))
            MockWorkflow.return_value = mock_workflow

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            result = await agent._execute_code_generation(
                step_text="Add unit tests",
                task_type="test_generation",
                task_id="test-123",
                trace_id="trace-456"
            )

            assert result.status == "failed"
            assert "Workflow crashed" in result.error
            assert result.is_safe is True

    @requires_langgraph
    @pytest.mark.asyncio
    async def test_process_step_execution_mode_safe_task(self):
        """Test step processing in execution mode with safe task"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow') as MockWorkflow:
            mock_workflow = MagicMock()
            mock_workflow.execute = AsyncMock(return_value={
                "error": None,
                "pr_number": 5678,
                "pr_url": "https://github.com/test/repo/pull/5678"
            })
            MockWorkflow.return_value = mock_workflow

            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock classifier to return safe task type
            if agent.classifier:
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    from agents.dev_agent.workflows.task_classifier import TaskType
                    mock_classify.return_value = TaskType.TEST_GENERATION

                    result = await agent._process_step(
                        step_text="Add unit tests for utils.py",
                        step_index=0,
                        trace_id="test-trace"
                    )

                    assert result.status == "success"
                    assert result.pr_number == 5678

    @requires_langgraph
    @pytest.mark.asyncio
    async def test_process_step_execution_mode_unsafe_task(self):
        """Test step processing in execution mode with unsafe task"""
        mock_dev_agent = MagicMock()

        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )

            # Mock classifier to return unsafe task type
            if agent.classifier:
                with patch.object(agent.classifier, 'classify') as mock_classify:
                    from agents.dev_agent.workflows.task_classifier import TaskType
                    mock_classify.return_value = TaskType.UNKNOWN

                    result = await agent._process_step(
                        step_text="Refactor entire codebase",
                        step_index=0,
                        trace_id="test-trace"
                    )

                    # Unsafe tasks should be blocked by semantic rules validation
                    assert result.status in ["skipped", "blocked"]
                    assert result.is_safe is False

    @pytest.mark.asyncio
    async def test_process_step_analysis_mode_safe_task(self):
        """Test step processing in analysis mode with safe task"""
        agent = ProjectEngineerAgent()  # analysis mode by default

        # Mock classifier to return safe task type
        if agent.classifier:
            with patch.object(agent.classifier, 'classify') as mock_classify:
                from agents.dev_agent.workflows.task_classifier import TaskType
                mock_classify.return_value = TaskType.DOCUMENTATION_UPDATE

                result = await agent._process_step(
                    step_text="Update README.md",
                    step_index=0,
                    trace_id="test-trace"
                )

                # Safe tasks should be skipped in analysis mode
                assert result.status == "skipped"
                assert result.is_safe is True
                assert "code generation disabled" in result.details.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
