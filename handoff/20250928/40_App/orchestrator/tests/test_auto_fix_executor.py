"""
Tests for Auto-Fix Executor Module

Issue #2252: Implement real auto-fix execution
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from utils.auto_fix_executor import (  # noqa: E402
    AutoFixExecutor,
    AutoFixTask,
    AutoFixTaskStatus,
    should_execute_canary,
    create_auto_fix_task,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = MagicMock()
    settings.auto_fix_enabled = True
    settings.auto_fix_categories = "style,documentation"
    settings.auto_fix_repos_allowlist = ""
    settings.auto_fix_max_retries = 3
    settings.auto_fix_per_repo_per_hour = 10
    settings.auto_fix_per_pr_per_hour = 3
    settings.auto_fix_global_per_hour = 100
    settings.auto_fix_canary_percent = 10
    settings.redis_url = None
    settings.github_token = "test-token"
    return settings


@pytest.fixture
def sample_triage_result_dict():
    """Create sample triage result dictionary for testing"""
    return {
        "comment_id": "test-comment-123",
        "source": "codex",
        "category": "style",
        "risk_level": "low",
        "files_affected": ["src/main.py"],
        "lines_affected": 5,
        "should_auto_fix": True,
        "confidence": 0.9,
        "reason": "Simple style fix",
        "keywords_matched": ["formatting"],
        "metadata": {},
    }


@pytest.fixture
def sample_task(sample_triage_result_dict):
    """Create sample AutoFixTask for testing"""
    return AutoFixTask(
        task_id="auto-fix-test123",
        triage_result=sample_triage_result_dict,
        repo="owner/repo",
        pr_number=42,
        pr_id="owner/repo#42",
        comment_url="https://github.com/owner/repo/pull/42#comment-123",
        comment_body="Please fix the formatting",
        file_path="src/main.py",
        line_number=10,
    )


class TestAutoFixTask:
    """Tests for AutoFixTask dataclass"""

    def test_task_creation(self, sample_triage_result_dict):
        """Test creating an AutoFixTask"""
        task = AutoFixTask(
            task_id="test-task-1",
            triage_result=sample_triage_result_dict,
            repo="owner/repo",
            pr_number=42,
            pr_id="owner/repo#42",
            comment_url="https://github.com/owner/repo/pull/42#comment-123",
            comment_body="Fix this",
        )

        assert task.task_id == "test-task-1"
        assert task.repo == "owner/repo"
        assert task.pr_number == 42
        assert task.status == AutoFixTaskStatus.PENDING

    def test_task_to_dict(self, sample_task):
        """Test converting task to dictionary"""
        data = sample_task.to_dict()

        assert data["task_id"] == "auto-fix-test123"
        assert data["repo"] == "owner/repo"
        assert data["pr_number"] == 42
        assert data["status"] == "pending"
        assert "created_at" in data
        assert "updated_at" in data

    def test_task_from_dict(self, sample_triage_result_dict):
        """Test creating task from dictionary"""
        data = {
            "task_id": "test-task-2",
            "triage_result": sample_triage_result_dict,
            "repo": "owner/repo",
            "pr_number": 42,
            "pr_id": "owner/repo#42",
            "comment_url": "https://github.com/owner/repo/pull/42#comment-123",
            "comment_body": "Fix this",
            "status": "executing",
        }

        task = AutoFixTask.from_dict(data)

        assert task.task_id == "test-task-2"
        assert task.status == AutoFixTaskStatus.EXECUTING

    def test_task_from_dict_invalid_status(self, sample_triage_result_dict):
        """Test creating task from dictionary with invalid status"""
        data = {
            "task_id": "test-task-3",
            "triage_result": sample_triage_result_dict,
            "repo": "owner/repo",
            "pr_number": 42,
            "pr_id": "owner/repo#42",
            "comment_url": "",
            "comment_body": "",
            "status": "invalid_status",
        }

        task = AutoFixTask.from_dict(data)

        assert task.status == AutoFixTaskStatus.PENDING


class TestShouldExecuteCanary:
    """Tests for canary rollout decision logic"""

    def test_canary_zero_percent(self):
        """Test canary with 0% always returns False"""
        assert should_execute_canary("task-1", 0) is False
        assert should_execute_canary("task-2", 0) is False

    def test_canary_hundred_percent(self):
        """Test canary with 100% always returns True"""
        assert should_execute_canary("task-1", 100) is True
        assert should_execute_canary("task-2", 100) is True

    def test_canary_deterministic(self):
        """Test canary is deterministic for same task_id"""
        result1 = should_execute_canary("task-abc", 50)
        result2 = should_execute_canary("task-abc", 50)
        assert result1 == result2

    def test_canary_distribution(self):
        """Test canary roughly follows percentage distribution"""
        selected = sum(
            1 for i in range(1000)
            if should_execute_canary(f"task-{i}", 50)
        )
        assert 400 < selected < 600


class TestCreateAutoFixTask:
    """Tests for create_auto_fix_task helper function"""

    def test_create_task_from_triage_result(self):
        """Test creating task from CommentTriageResult"""
        from dataclasses import dataclass, field
        from enum import Enum
        from typing import Any, Dict, List

        class CommentCategory(Enum):
            STYLE = "style"

        class RiskLevel(Enum):
            LOW = "low"

        @dataclass
        class MockTriageResult:
            comment_id: str
            source: str
            category: CommentCategory
            risk_level: RiskLevel
            files_affected: List[str] = field(default_factory=list)
            lines_affected: int = 0
            should_auto_fix: bool = False
            confidence: float = 0.0
            reason: str = ""
            keywords_matched: List[str] = field(default_factory=list)
            metadata: Dict[str, Any] = field(default_factory=dict)

            def to_dict(self):
                return {
                    "comment_id": self.comment_id,
                    "source": self.source,
                    "category": self.category.value,
                    "risk_level": self.risk_level.value,
                    "files_affected": self.files_affected,
                    "lines_affected": self.lines_affected,
                    "should_auto_fix": self.should_auto_fix,
                    "confidence": self.confidence,
                    "reason": self.reason,
                    "keywords_matched": self.keywords_matched,
                    "metadata": self.metadata,
                }

        triage_result = MockTriageResult(
            comment_id="comment-123",
            source="codex",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
        )

        task = create_auto_fix_task(
            triage_result=triage_result,
            repo="owner/repo",
            pr_number=42,
            comment_url="https://github.com/owner/repo/pull/42#comment-123",
            comment_body="Fix formatting",
        )

        assert task.task_id.startswith("auto-fix-")
        assert task.repo == "owner/repo"
        assert task.pr_number == 42
        assert task.pr_id == "owner/repo#42"
        assert task.triage_result["category"] == "style"


class TestAutoFixExecutor:
    """Tests for AutoFixExecutor class"""

    def test_executor_initialization(self, mock_settings):
        """Test executor initialization"""
        executor = AutoFixExecutor(settings=mock_settings)

        assert executor.settings == mock_settings
        assert executor.redis_url is None

    def test_executor_safety_check_blocked(self, mock_settings, sample_task):
        """Test executor blocks when safety check fails"""
        mock_safety_result = MagicMock()
        mock_safety_result.allowed = False
        mock_safety_result.reason = "Auto-fix is disabled"

        with patch.object(
            AutoFixExecutor, '_check_safety', return_value=mock_safety_result
        ):
            executor = AutoFixExecutor(settings=mock_settings)
            result = executor.execute(sample_task)

            assert result.success is False
            assert result.status == AutoFixTaskStatus.BLOCKED
            assert "Safety check failed" in result.message
            assert result.safety_check_passed is False

    def test_executor_canary_skipped(self, mock_settings, sample_task):
        """Test executor skips when canary rollout not selected"""
        mock_settings.auto_fix_canary_percent = 0

        mock_safety_result = MagicMock()
        mock_safety_result.allowed = True
        mock_safety_result.reason = "All checks passed"

        with patch.object(
            AutoFixExecutor, '_check_safety', return_value=mock_safety_result
        ):
            executor = AutoFixExecutor(settings=mock_settings)
            result = executor.execute(sample_task)

            assert result.success is True
            assert result.status == AutoFixTaskStatus.SKIPPED
            assert "canary rollout" in result.message.lower()
            assert result.safety_check_passed is True
            assert result.canary_selected is False

    def test_executor_success(self, mock_settings, sample_task):
        """Test executor succeeds when all checks pass"""
        mock_settings.auto_fix_canary_percent = 100

        mock_safety_result = MagicMock()
        mock_safety_result.allowed = True
        mock_safety_result.reason = "All checks passed"

        mock_execute_result = {
            "status": "prepared",
            "orchestrator_input": {"task_type": "review_follow_up"},
            "follow_up_task_id": "follow-up-123",
            "pr_url": None,
            "commit_sha": None,
        }

        with patch.object(
            AutoFixExecutor, '_check_safety', return_value=mock_safety_result
        ), patch.object(
            AutoFixExecutor, '_execute_fix', return_value=mock_execute_result
        ):
            executor = AutoFixExecutor(settings=mock_settings)
            result = executor.execute(sample_task)

            assert result.success is True
            assert result.status == AutoFixTaskStatus.COMPLETED
            assert result.safety_check_passed is True
            assert result.canary_selected is True

    def test_executor_execution_error(self, mock_settings, sample_task):
        """Test executor handles execution errors"""
        mock_settings.auto_fix_canary_percent = 100

        mock_safety_result = MagicMock()
        mock_safety_result.allowed = True
        mock_safety_result.reason = "All checks passed"

        with patch.object(
            AutoFixExecutor, '_check_safety', return_value=mock_safety_result
        ), patch.object(
            AutoFixExecutor, '_execute_fix', side_effect=Exception("Test error")
        ):
            executor = AutoFixExecutor(settings=mock_settings)
            result = executor.execute(sample_task)

            assert result.success is False
            assert result.status == AutoFixTaskStatus.FAILED
            assert "Test error" in result.message
            assert result.safety_check_passed is True
            assert result.canary_selected is True


class TestAutoFixTaskStatus:
    """Tests for AutoFixTaskStatus enum"""

    def test_all_statuses_exist(self):
        """Test all expected statuses exist"""
        assert AutoFixTaskStatus.PENDING.value == "pending"
        assert AutoFixTaskStatus.SAFETY_CHECK.value == "safety_check"
        assert AutoFixTaskStatus.CANARY_CHECK.value == "canary_check"
        assert AutoFixTaskStatus.EXECUTING.value == "executing"
        assert AutoFixTaskStatus.COMPLETED.value == "completed"
        assert AutoFixTaskStatus.FAILED.value == "failed"
        assert AutoFixTaskStatus.SKIPPED.value == "skipped"
        assert AutoFixTaskStatus.BLOCKED.value == "blocked"
