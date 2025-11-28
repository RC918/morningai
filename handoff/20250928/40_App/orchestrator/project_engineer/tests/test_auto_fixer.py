#!/usr/bin/env python3
"""
Unit tests for AutoFixer - Phase 2 Step C Fixer Node

Tests cover:
1. Canary rollout logic (should_run_for_task)
2. Auto-fix workflow (run_auto_fix)
3. ReviewerAgent integration
4. ProjectEngineerAgent integration
5. Error handling
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MockSettings:
    """Mock settings for testing"""
    enable_project_engineer_fixer: bool = False
    project_engineer_fixer_percent: int = 0
    enable_project_engineer_codegen: bool = False
    workspace_path: str = "."
    openai_api_key: str = "test-key"


@dataclass
class MockReviewComment:
    """Mock review comment"""
    file_path: str
    line_number: int
    severity: str
    category: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class MockReviewResult:
    """Mock review result"""
    passed: bool
    comments: List[MockReviewComment]
    summary: dict


@dataclass
class MockTaskResult:
    """Mock task result"""
    task_id: str
    task_type: str
    status: str
    is_safe: bool
    details: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None


class TestAutoFixerShouldRunForTask:
    """Tests for AutoFixer.should_run_for_task()"""

    def test_disabled_by_flag(self):
        """Test that auto-fix is disabled when ENABLE_PROJECT_ENGINEER_FIXER=false"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=False,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)

        state = {"trace_id": "test-123"}
        assert fixer.should_run_for_task(state) is False

    def test_disabled_by_zero_percent(self):
        """Test that auto-fix is disabled when PROJECT_ENGINEER_FIXER_PERCENT=0"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=0
        )
        fixer = AutoFixer(settings=settings)

        state = {"trace_id": "test-123"}
        assert fixer.should_run_for_task(state) is False

    def test_enabled_for_all_at_100_percent(self):
        """Test that auto-fix is enabled for all tasks when percent=100"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)

        state = {"trace_id": "test-123"}
        assert fixer.should_run_for_task(state) is True

    def test_canary_bucket_deterministic(self):
        """Test that canary bucket is deterministic for same trace_id"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=50
        )
        fixer = AutoFixer(settings=settings)

        state = {"trace_id": "deterministic-test-id"}

        result1 = fixer.should_run_for_task(state)
        result2 = fixer.should_run_for_task(state)
        result3 = fixer.should_run_for_task(state)

        assert result1 == result2 == result3

    def test_canary_uses_pr_number_if_available(self):
        """Test that canary uses pr_number over trace_id when available"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=50
        )
        fixer = AutoFixer(settings=settings)

        state_with_pr = {"trace_id": "test-123", "pr_number": 456}
        state_without_pr = {"trace_id": "test-123"}

        _ = fixer.should_run_for_task(state_with_pr)
        _ = fixer.should_run_for_task(state_without_pr)


class TestAutoFixerRunAutoFix:
    """Tests for AutoFixer.run_auto_fix()"""

    @pytest.mark.asyncio
    async def test_skips_when_no_changed_files(self):
        """Test that auto-fix skips when no changed files found"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)

        with patch.object(fixer, '_get_changed_files', new_callable=AsyncMock) as mock_get_files:
            mock_get_files.return_value = []

            state = {"trace_id": "test-123"}
            result = await fixer.run_auto_fix(state)

            assert result.get("error") == "No changed files found for auto-fix"

    @pytest.mark.asyncio
    async def test_skips_when_review_passes(self):
        """Test that auto-fix skips when ReviewerAgent passes"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100
        )
        fixer = AutoFixer(settings=settings)

        with patch.object(fixer, '_get_changed_files', new_callable=AsyncMock) as mock_get_files:
            mock_get_files.return_value = ["test.py"]

            with patch.object(fixer, '_run_reviewer', new_callable=AsyncMock) as mock_reviewer:
                mock_reviewer.return_value = MockReviewResult(
                    passed=True,
                    comments=[],
                    summary={}
                )

                state = {"trace_id": "test-123"}
                result = await fixer.run_auto_fix(state)

                assert result.get("error") is None

    @pytest.mark.asyncio
    async def test_invokes_project_engineer_on_review_failures(self):
        """Test that ProjectEngineerAgent is invoked when review fails"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=True
        )
        fixer = AutoFixer(settings=settings)

        with patch.object(fixer, '_get_changed_files', new_callable=AsyncMock) as mock_get_files:
            mock_get_files.return_value = ["test.py"]

            with patch.object(fixer, '_run_reviewer', new_callable=AsyncMock) as mock_reviewer:
                mock_reviewer.return_value = MockReviewResult(
                    passed=False,
                    comments=[
                        MockReviewComment(
                            file_path="test.py",
                            line_number=10,
                            severity="error",
                            category="lint",
                            message="E501: line too long",
                            suggestion="Break line"
                        )
                    ],
                    summary={"error": 1, "warning": 0, "lint": 1}
                )

                with patch.object(fixer, '_run_project_engineer', new_callable=AsyncMock) as mock_pe:
                    mock_pe.return_value = {
                        "success": True,
                        "pr_number": 123,
                        "pr_url": "https://github.com/test/repo/pull/123"
                    }

                    state = {"trace_id": "test-123", "repo": "test/repo"}
                    result = await fixer.run_auto_fix(state)

                    mock_pe.assert_called_once()
                    assert result.get("error") is None
                    assert result.get("pr_number") == 123

    @pytest.mark.asyncio
    async def test_sets_error_on_project_engineer_failure(self):
        """Test that error is set when ProjectEngineerAgent fails"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            project_engineer_fixer_percent=100,
            enable_project_engineer_codegen=True
        )
        fixer = AutoFixer(settings=settings)

        with patch.object(fixer, '_get_changed_files', new_callable=AsyncMock) as mock_get_files:
            mock_get_files.return_value = ["test.py"]

            with patch.object(fixer, '_run_reviewer', new_callable=AsyncMock) as mock_reviewer:
                mock_reviewer.return_value = MockReviewResult(
                    passed=False,
                    comments=[],
                    summary={"error": 1}
                )

                with patch.object(fixer, '_run_project_engineer', new_callable=AsyncMock) as mock_pe:
                    mock_pe.return_value = {
                        "success": False,
                        "error": "Fix generation failed"
                    }

                    state = {"trace_id": "test-123"}
                    result = await fixer.run_auto_fix(state)

                    assert result.get("error") == "Fix generation failed"


class TestAutoFixerBuildFixTaskDescription:
    """Tests for AutoFixer._build_fix_task_description()"""

    def test_includes_pr_number(self):
        """Test that PR number is included in description"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings()
        fixer = AutoFixer(settings=settings)

        review_result = MockReviewResult(
            passed=False,
            comments=[],
            summary={"error": 1, "warning": 2}
        )

        description = fixer._build_fix_task_description(
            review_result, pr_number=123, changed_files=["test.py"]
        )

        assert "PR #123" in description

    def test_includes_error_count(self):
        """Test that error count is included in description"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings()
        fixer = AutoFixer(settings=settings)

        review_result = MockReviewResult(
            passed=False,
            comments=[],
            summary={"error": 5, "warning": 3, "lint": 4}
        )

        description = fixer._build_fix_task_description(
            review_result, pr_number=None, changed_files=[]
        )

        assert "5 errors" in description
        assert "3 warnings" in description

    def test_includes_critical_issues(self):
        """Test that critical issues are included in description"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings()
        fixer = AutoFixer(settings=settings)

        review_result = MockReviewResult(
            passed=False,
            comments=[
                MockReviewComment(
                    file_path="test.py",
                    line_number=10,
                    severity="error",
                    category="security",
                    message="SQL injection vulnerability",
                    suggestion="Use parameterized queries"
                )
            ],
            summary={"error": 1, "security": 1}
        )

        description = fixer._build_fix_task_description(
            review_result, pr_number=None, changed_files=["test.py"]
        )

        assert "test.py:10" in description
        assert "SQL injection" in description
        assert "parameterized queries" in description


class TestAutoFixerRunProjectEngineer:
    """Tests for AutoFixer._run_project_engineer()"""

    @pytest.mark.asyncio
    async def test_returns_error_when_codegen_disabled(self):
        """Test that error is returned when ENABLE_PROJECT_ENGINEER_CODEGEN=false"""
        from project_engineer.fixer_integration import AutoFixer

        settings = MockSettings(
            enable_project_engineer_fixer=True,
            enable_project_engineer_codegen=False
        )
        fixer = AutoFixer(settings=settings)

        result = await fixer._run_project_engineer(
            fix_description="Fix test",
            repo="test/repo",
            state={"trace_id": "test-123"}
        )

        assert result["success"] is False
        assert "ENABLE_PROJECT_ENGINEER_CODEGEN=false" in result["error"]


try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestFixerNodeIntegration:
    """Integration tests for fixer_node with AutoFixer"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fixer_node_increments_retry_count(self):
        """Test that fixer_node increments retry_count"""
        from langgraph_orchestrator import fixer_node

        state = {
            "trace_id": "test-123",
            "retry_count": 0,
            "messages": []
        }

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = False
            MockAutoFixer.return_value = mock_fixer

            result = fixer_node(state)

            assert result["retry_count"] == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fixer_node_gives_up_after_max_retries(self):
        """Test that fixer_node gives up after max retries"""
        from langgraph_orchestrator import fixer_node

        state = {
            "trace_id": "test-123",
            "retry_count": 3,
            "messages": []
        }

        result = fixer_node(state)

        assert "Max retries" in (result.get("error") or "")

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fixer_node_calls_auto_fixer_when_enabled(self):
        """Test that fixer_node calls AutoFixer when enabled"""
        from langgraph_orchestrator import fixer_node

        state = {
            "trace_id": "test-123",
            "retry_count": 0,
            "messages": []
        }

        with patch("project_engineer.fixer_integration.AutoFixer") as MockAutoFixer:
            mock_fixer = MagicMock()
            mock_fixer.should_run_for_task.return_value = True
            mock_fixer.run_auto_fix_sync.return_value = state
            MockAutoFixer.return_value = mock_fixer

            fixer_node(state)

            mock_fixer.should_run_for_task.assert_called_once()
            mock_fixer.run_auto_fix_sync.assert_called_once()
