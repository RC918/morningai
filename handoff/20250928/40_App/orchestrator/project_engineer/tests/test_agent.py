#!/usr/bin/env python3
"""
Unit tests for ProjectEngineerAgent
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

from project_engineer.agent import ProjectEngineerAgent, TaskResult


class TestProjectEngineerAgent:
    """Test suite for ProjectEngineerAgent"""

    def test_init(self):
        """Test ProjectEngineerAgent initialization"""
        agent = ProjectEngineerAgent()

        # Agent should initialize successfully
        assert agent is not None

        # Check that is_safe_task function is available
        assert agent.is_safe_task is not None

    def test_get_status(self):
        """Test get_status method"""
        agent = ProjectEngineerAgent()
        status = agent.get_status()

        assert status["agent_type"] == "ProjectEngineerAgent"
        assert status["version"] == "1.0.0-phase2-step-a"
        assert status["mode"] == "analysis_only"
        assert "features" in status
        assert status["features"]["safe_task_gating"] is True
        assert status["features"]["code_generation"] is False

    def test_run_task_empty_description(self):
        """Test run_task with empty description"""
        agent = ProjectEngineerAgent()

        with pytest.raises(ValueError, match="Task description cannot be empty"):
            agent.run_task("")

    def test_run_task_whitespace_description(self):
        """Test run_task with whitespace-only description"""
        agent = ProjectEngineerAgent()

        with pytest.raises(ValueError, match="Task description cannot be empty"):
            agent.run_task("   ")

    def test_run_task_basic(self):
        """Test run_task with basic description"""
        agent = ProjectEngineerAgent()
        results = agent.run_task("更新 README.md")

        # Should return at least one result
        assert len(results) > 0

        # Each result should be a TaskResult
        for result in results:
            assert isinstance(result, TaskResult)
            assert result.task_id is not None
            assert result.task_type is not None
            assert result.status in ["success", "failed", "skipped"]
            assert isinstance(result.is_safe, bool)
            assert result.details is not None

    def test_run_task_with_safe_task(self):
        """Test run_task with a safe task (documentation update)"""
        agent = ProjectEngineerAgent()
        results = agent.run_task("更新 README.md 添加安裝說明")

        assert len(results) > 0

        # At least one result should be classified as safe
        # (depends on LLM Planner and TaskClassifier behavior)
        # In Phase 2 Step A, all tasks are skipped (analysis only)
        for result in results:
            assert result.status == "skipped"
            assert "analysis only" in result.details.lower()

    def test_run_task_with_unsafe_task(self):
        """Test run_task with an unsafe task (refactor)"""
        agent = ProjectEngineerAgent()
        results = agent.run_task("重構 payment_service.py 的錯誤處理")

        assert len(results) > 0

        # All tasks should be skipped in Phase 2 Step A
        for result in results:
            assert result.status == "skipped"

    def test_run_task_returns_task_results(self):
        """Test that run_task returns properly structured TaskResult objects"""
        agent = ProjectEngineerAgent()
        results = agent.run_task("分析 user_service.py 的性能瓶頸")

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
            assert result.status in ["success", "failed", "skipped"]

            # is_safe should be a boolean
            assert isinstance(result.is_safe, bool)

            # details should be a non-empty string
            assert isinstance(result.details, str)
            assert len(result.details) > 0

    def test_process_step_basic(self):
        """Test _process_step method"""
        agent = ProjectEngineerAgent()

        result = agent._process_step(
            step_text="更新 README.md",
            step_index=0,
            trace_id="test-trace-123"
        )

        assert isinstance(result, TaskResult)
        assert result.task_id == "test-trace-123-step-0"
        assert result.status == "skipped"
        assert result.details is not None

    def test_multiple_tasks(self):
        """Test run_task with multiple tasks in description"""
        agent = ProjectEngineerAgent()
        results = agent.run_task(
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

    def test_run_task_function(self):
        """Test run_task convenience function"""
        from project_engineer.agent import run_task

        results = run_task("更新 README.md")

        assert len(results) > 0
        assert all(isinstance(r, TaskResult) for r in results)

    def test_run_task_function_with_repo(self):
        """Test run_task function with custom repo"""
        from project_engineer.agent import run_task

        results = run_task("更新文檔", repo="test/repo")

        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
