"""
Unit tests for Review Follow-up Mode

Issue #2211: Orchestrator Review Follow-up Mode

Tests cover:
1. ReviewFollowUpTask schema and creation
2. ReviewFollowUpService functionality
3. PR context fetching
4. HITL approval determination
5. Goal text building
"""

import json
from unittest.mock import MagicMock

import pytest

from webhooks.review_follow_up import (
    ReviewFollowUpStatus,
    ReviewFollowUpAction,
    PRContext,
    ReviewFollowUpTask,
    ReviewFollowUpService,
    determine_hitl_requirement,
    SENSITIVE_FILE_PATTERNS,
)
from webhooks.comment_triage import (
    CommentTriageResult,
    CommentCategory,
    RiskLevel,
)
from webhooks.task_repository import (
    generate_task_id,
    InMemoryTaskRepository,
    RedisTaskRepository,
    get_task_repository,
)


class TestReviewFollowUpStatus:
    """Tests for ReviewFollowUpStatus enum"""

    def test_status_values(self):
        """Test all status values exist"""
        assert ReviewFollowUpStatus.PENDING.value == "pending"
        assert ReviewFollowUpStatus.FETCHING_CONTEXT.value == "fetching_context"
        assert ReviewFollowUpStatus.PLANNING.value == "planning"
        assert ReviewFollowUpStatus.EXECUTING.value == "executing"
        assert ReviewFollowUpStatus.AWAITING_APPROVAL.value == "awaiting_approval"
        assert ReviewFollowUpStatus.COMPLETED.value == "completed"
        assert ReviewFollowUpStatus.FAILED.value == "failed"
        assert ReviewFollowUpStatus.SKIPPED.value == "skipped"


class TestReviewFollowUpAction:
    """Tests for ReviewFollowUpAction enum"""

    def test_action_values(self):
        """Test all action values exist"""
        assert ReviewFollowUpAction.AUTO_FIX.value == "auto_fix"
        assert ReviewFollowUpAction.MANUAL_REVIEW.value == "manual_review"
        assert ReviewFollowUpAction.SKIP.value == "skip"
        assert ReviewFollowUpAction.ESCALATE.value == "escalate"


class TestPRContext:
    """Tests for PRContext dataclass"""

    def test_pr_context_creation(self):
        """Test PRContext creation with all fields"""
        context = PRContext(
            pr_number=123,
            repo="RC918/morningai",
            branch="feature/test",
            base_branch="main",
            title="Test PR",
            description="Test description",
            author="testuser",
            diff="diff content",
            files_changed=["file1.py", "file2.py"],
            comments=[{"id": 1, "body": "comment"}],
            reviews=[{"id": 1, "state": "approved"}],
            labels=["bug", "enhancement"],
            ci_status="success",
            metadata={"key": "value"},
        )

        assert context.pr_number == 123
        assert context.repo == "RC918/morningai"
        assert context.branch == "feature/test"
        assert context.base_branch == "main"
        assert context.title == "Test PR"
        assert context.description == "Test description"
        assert context.author == "testuser"
        assert context.diff == "diff content"
        assert len(context.files_changed) == 2
        assert len(context.comments) == 1
        assert len(context.reviews) == 1
        assert len(context.labels) == 2
        assert context.ci_status == "success"

    def test_pr_context_to_dict(self):
        """Test PRContext serialization"""
        context = PRContext(
            pr_number=123,
            repo="RC918/morningai",
            branch="feature/test",
            base_branch="main",
            title="Test PR",
            description="Test description",
            author="testuser",
            diff="diff content",
            files_changed=["file1.py"],
        )

        result = context.to_dict()

        assert result["pr_number"] == 123
        assert result["repo"] == "RC918/morningai"
        assert result["diff_length"] == len("diff content")
        assert result["files_changed"] == ["file1.py"]
        assert result["comments_count"] == 0
        assert result["reviews_count"] == 0

    def test_pr_context_defaults(self):
        """Test PRContext default values"""
        context = PRContext(
            pr_number=1,
            repo="test/repo",
            branch="main",
            base_branch="main",
            title="Test",
            description="",
            author="user",
            diff="",
        )

        assert context.files_changed == []
        assert context.comments == []
        assert context.reviews == []
        assert context.labels == []
        assert context.ci_status == "unknown"
        assert context.metadata == {}


class TestReviewFollowUpTask:
    """Tests for ReviewFollowUpTask dataclass"""

    def test_task_creation(self):
        """Test ReviewFollowUpTask creation"""
        task = ReviewFollowUpTask(
            task_id="test-task-123",
            original_pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/RC918/morningai/pull/456#comment-789",
            comment_body="Consider using a more descriptive variable name",
            file_path="src/auth.py",
            line_number=42,
        )

        assert task.task_id == "test-task-123"
        assert task.task_type == "review_follow_up"
        assert task.original_pr_number == 456
        assert task.repo == "RC918/morningai"
        assert task.branch == "feature/test"
        assert task.file_path == "src/auth.py"
        assert task.line_number == 42
        assert task.status == ReviewFollowUpStatus.PENDING
        assert task.action == ReviewFollowUpAction.MANUAL_REVIEW

    def test_task_to_dict(self):
        """Test ReviewFollowUpTask serialization"""
        task = ReviewFollowUpTask(
            task_id="test-task-123",
            original_pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/RC918/morningai/pull/456#comment-789",
            comment_body="Test comment",
            file_path="src/auth.py",
            line_number=42,
        )

        result = task.to_dict()

        assert result["task_id"] == "test-task-123"
        assert result["task_type"] == "review_follow_up"
        assert result["original_pr_number"] == 456
        assert result["status"] == "pending"
        assert result["action"] == "manual_review"
        assert "created_at" in result
        assert "updated_at" in result

    def test_task_from_triage_result_auto_fix(self):
        """Test task creation from triage result with auto-fix"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
            reason="Style issue with high confidence",
            files_affected=["src/utils.py"],
            lines_affected=5,
        )

        task = ReviewFollowUpTask.from_triage_result(
            task_id="test-task-123",
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use consistent naming",
        )

        assert task.action == ReviewFollowUpAction.AUTO_FIX
        assert task.triage_result == triage_result
        assert task.file_path == "src/utils.py"

    def test_task_from_triage_result_escalate_security(self):
        """Test task creation from triage result with security escalation"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.SECURITY,
            risk_level=RiskLevel.HIGH,
            should_auto_fix=False,
            confidence=0.85,
            reason="Security vulnerability detected",
            files_affected=["src/auth.py"],
            lines_affected=10,
        )

        task = ReviewFollowUpTask.from_triage_result(
            task_id="test-task-123",
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="SQL injection vulnerability",
        )

        assert task.action == ReviewFollowUpAction.ESCALATE

    def test_task_from_triage_result_skip_unknown(self):
        """Test task creation from triage result with unknown category"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="unknown",
            category=CommentCategory.UNKNOWN,
            risk_level=RiskLevel.LOW,
            should_auto_fix=False,
            confidence=0.2,
            reason="Unable to classify",
            files_affected=[],
            lines_affected=0,
        )

        task = ReviewFollowUpTask.from_triage_result(
            task_id="test-task-123",
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Some comment",
        )

        assert task.action == ReviewFollowUpAction.SKIP


class TestReviewFollowUpService:
    """Tests for ReviewFollowUpService"""

    def test_service_initialization(self):
        """Test service initialization with default repository"""
        service = ReviewFollowUpService()
        # Issue #2259: Now uses repository instead of _tasks dict
        from webhooks.task_repository import InMemoryTaskRepository
        assert isinstance(service._repository, InMemoryTaskRepository)

    def test_service_initialization_with_token(self):
        """Test service initialization with GitHub token"""
        service = ReviewFollowUpService(github_token="test-token")
        assert service._github_token == "test-token"

    def test_create_task(self):
        """Test task creation through service"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
            reason="Style issue",
            files_affected=["src/utils.py"],
            lines_affected=5,
        )

        task = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use consistent naming",
        )

        # Issue #2259: Task ID is now deterministic (pr{pr_number}_comment{comment_id})
        assert task.task_id == "pr456_commentcomment-123"
        assert task.original_pr_number == 456
        assert task.action == ReviewFollowUpAction.AUTO_FIX

        # Task should be stored in repository
        assert service.get_task(task.task_id) == task

    def test_get_task_not_found(self):
        """Test getting non-existent task"""
        service = ReviewFollowUpService()
        assert service.get_task("non-existent") is None

    def test_prepare_for_orchestrator(self):
        """Test preparing task for orchestrator"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.BUG_FIX,
            risk_level=RiskLevel.MEDIUM,
            should_auto_fix=True,
            confidence=0.85,
            reason="Bug fix needed",
            files_affected=["src/utils.py"],
            lines_affected=10,
        )

        task = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Fix the null pointer exception",
            file_path="src/utils.py",
            line_number=42,
        )

        result = service.prepare_for_orchestrator(task)

        assert result["task_type"] == "review_follow_up"
        assert result["goal"].startswith("[Review Follow-up:")
        assert result["repo"] == "RC918/morningai"
        assert result["branch"] == "feature/test"
        assert result["original_pr_number"] == 456
        assert result["file_path"] == "src/utils.py"
        assert result["line_number"] == 42
        assert "triage_result" in result

    def test_prepare_for_orchestrator_requires_approval_high_risk(self):
        """Test that high-risk tasks require approval"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.SECURITY,
            risk_level=RiskLevel.HIGH,
            should_auto_fix=False,
            confidence=0.9,
            reason="Security issue",
            files_affected=["src/auth.py"],
            lines_affected=20,
        )

        task = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Security vulnerability",
        )

        result = service.prepare_for_orchestrator(task)

        assert result["requires_approval"] is True

    def test_prepare_for_orchestrator_no_approval_auto_fix(self):
        """Test that auto-fix with high confidence doesn't require approval"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.95,
            reason="Style fix",
            files_affected=["src/utils.py"],
            lines_affected=2,
        )

        task = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use snake_case",
        )

        result = service.prepare_for_orchestrator(task)

        assert result["requires_approval"] is False

    def test_get_stats(self):
        """Test service statistics"""
        service = ReviewFollowUpService()

        # Create multiple tasks
        for i in range(3):
            triage_result = CommentTriageResult(
                comment_id=f"comment-{i}",
                source="gemini-code-assist",
                category=CommentCategory.STYLE,
                risk_level=RiskLevel.LOW,
                should_auto_fix=True,
                confidence=0.9,
                reason="Style issue",
                files_affected=[f"file{i}.py"],
                lines_affected=5,
            )
            service.create_task(
                triage_result=triage_result,
                pr_number=100 + i,
                repo="RC918/morningai",
                branch="feature/test",
                comment_url=f"https://github.com/.../{i}",
                comment_body=f"Comment {i}",
            )

        stats = service.get_stats()

        assert stats["total_tasks"] == 3
        assert "status_counts" in stats
        assert "action_counts" in stats
        assert stats["status_counts"].get("pending", 0) == 3
        assert stats["action_counts"].get("auto_fix", 0) == 3

    @pytest.mark.xfail(reason="Pre-existing legacy debt #3251 - get_repo() signature mismatch")
    def test_fetch_pr_context_stub(self):
        """Test PR context fetching with stub (no GitHub API)"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
            reason="Style issue",
            files_affected=["src/utils.py"],
            lines_affected=5,
        )

        task = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use consistent naming",
        )

        # This should return stub context since GitHub API is not available
        context = service.fetch_pr_context(task)

        assert context is not None
        assert context.pr_number == 456
        assert context.repo == "RC918/morningai"
        # Stub context should have stub=True in metadata
        assert context.metadata.get("stub") is True


class TestDetermineAction:
    """Tests for action determination logic"""

    def test_auto_fix_action(self):
        """Test auto-fix action determination"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
            reason="Style issue",
            files_affected=["src/utils.py"],
            lines_affected=5,
        )

        action = ReviewFollowUpTask._determine_action(triage_result)
        assert action == ReviewFollowUpAction.AUTO_FIX

    def test_escalate_action_security_high_risk(self):
        """Test escalate action for high-risk security issues"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.SECURITY,
            risk_level=RiskLevel.HIGH,
            should_auto_fix=False,
            confidence=0.85,
            reason="Security vulnerability",
            files_affected=["src/auth.py"],
            lines_affected=10,
        )

        action = ReviewFollowUpTask._determine_action(triage_result)
        assert action == ReviewFollowUpAction.ESCALATE

    def test_skip_action_unknown_low_confidence(self):
        """Test skip action for unknown category with low confidence"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="unknown",
            category=CommentCategory.UNKNOWN,
            risk_level=RiskLevel.LOW,
            should_auto_fix=False,
            confidence=0.2,
            reason="Unable to classify",
            files_affected=[],
            lines_affected=0,
        )

        action = ReviewFollowUpTask._determine_action(triage_result)
        assert action == ReviewFollowUpAction.SKIP

    def test_manual_review_action_default(self):
        """Test manual review as default action"""
        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.REFACTOR,
            risk_level=RiskLevel.MEDIUM,
            should_auto_fix=False,
            confidence=0.7,
            reason="Refactoring suggestion",
            files_affected=["src/utils.py"],
            lines_affected=50,
        )

        action = ReviewFollowUpTask._determine_action(triage_result)
        assert action == ReviewFollowUpAction.MANUAL_REVIEW


class TestDetermineHitlRequirement:
    """
    Tests for unified determine_hitl_requirement() function.

    Issue #2258: Single source of truth for HITL approval decisions.
    """

    def test_none_triage_result_requires_approval(self):
        """Test that None triage_result requires approval"""
        assert determine_hitl_requirement(None) is True

    def test_high_risk_requires_approval(self):
        """Test that high risk level requires approval"""
        triage_result = {"risk_level": "high", "category": "style"}
        assert determine_hitl_requirement(triage_result) is True

    def test_security_category_requires_approval(self):
        """Test that security category requires approval"""
        triage_result = {"risk_level": "low", "category": "security"}
        assert determine_hitl_requirement(triage_result) is True

    def test_escalate_action_requires_approval(self):
        """Test that escalate action requires approval"""
        triage_result = {"risk_level": "low", "category": "style"}
        assert determine_hitl_requirement(triage_result, action="escalate") is True

    @pytest.mark.parametrize("pattern", SENSITIVE_FILE_PATTERNS)
    def test_sensitive_file_patterns_require_approval(self, pattern):
        """Test that sensitive file patterns require approval"""
        triage_result = {"risk_level": "low", "category": "style"}
        file_path = f"src/{pattern}_module.py"
        assert determine_hitl_requirement(triage_result, file_path=file_path) is True

    def test_sensitive_file_case_insensitive(self):
        """Test that sensitive file pattern matching is case insensitive"""
        triage_result = {"risk_level": "low", "category": "style"}
        assert determine_hitl_requirement(
            triage_result, file_path="src/AUTH_SERVICE.py"
        ) is True
        assert determine_hitl_requirement(
            triage_result, file_path="src/Config.py"
        ) is True

    def test_auto_fix_high_confidence_no_approval(self):
        """Test that auto-fix with high confidence doesn't require approval"""
        triage_result = {
            "risk_level": "low",
            "category": "style",
            "should_auto_fix": True,
            "confidence": 0.85,
        }
        assert determine_hitl_requirement(triage_result, file_path="src/utils.py") is False

    def test_auto_fix_low_confidence_requires_approval(self):
        """Test that auto-fix with low confidence requires approval"""
        triage_result = {
            "risk_level": "low",
            "category": "style",
            "should_auto_fix": True,
            "confidence": 0.7,
        }
        assert determine_hitl_requirement(triage_result) is True

    def test_default_requires_approval(self):
        """Test that default case requires approval"""
        triage_result = {
            "risk_level": "low",
            "category": "refactor",
            "should_auto_fix": False,
            "confidence": 0.5,
        }
        assert determine_hitl_requirement(triage_result) is True

    def test_empty_file_path_no_sensitive_check(self):
        """Test that empty file path skips sensitive file check"""
        triage_result = {
            "risk_level": "low",
            "category": "style",
            "should_auto_fix": True,
            "confidence": 0.9,
        }
        assert determine_hitl_requirement(triage_result, file_path="") is False

    def test_priority_high_risk_over_auto_fix(self):
        """Test that high risk takes priority over auto-fix"""
        triage_result = {
            "risk_level": "high",
            "category": "style",
            "should_auto_fix": True,
            "confidence": 0.95,
        }
        assert determine_hitl_requirement(triage_result) is True

    def test_priority_security_over_auto_fix(self):
        """Test that security category takes priority over auto-fix"""
        triage_result = {
            "risk_level": "low",
            "category": "security",
            "should_auto_fix": True,
            "confidence": 0.95,
        }
        assert determine_hitl_requirement(triage_result) is True

    def test_priority_sensitive_file_over_auto_fix(self):
        """Test that sensitive file takes priority over auto-fix"""
        triage_result = {
            "risk_level": "low",
            "category": "style",
            "should_auto_fix": True,
            "confidence": 0.95,
        }
        assert determine_hitl_requirement(
            triage_result, file_path="src/auth.py"
        ) is True


class TestTaskRepository:
    """
    Tests for Task Repository abstraction layer.

    Issue #2259: Task Storage Migration to Redis/DB
    """

    def test_generate_task_id(self):
        """Test deterministic task ID generation"""
        task_id = generate_task_id(123, "comment-456")
        assert task_id == "pr123_commentcomment-456"

        task_id2 = generate_task_id(123, "comment-456")
        assert task_id == task_id2

    def test_in_memory_repository_save_and_get(self):
        """Test InMemoryTaskRepository save and get operations"""
        repo = InMemoryTaskRepository()

        task = ReviewFollowUpTask(
            task_id="test-task-123",
            original_pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Test comment",
        )

        assert repo.save(task) is True
        retrieved = repo.get("test-task-123")
        assert retrieved is not None
        assert retrieved.task_id == "test-task-123"
        assert retrieved.original_pr_number == 456

    def test_in_memory_repository_delete(self):
        """Test InMemoryTaskRepository delete operation"""
        repo = InMemoryTaskRepository()

        task = ReviewFollowUpTask(
            task_id="test-task-123",
            original_pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Test comment",
        )

        repo.save(task)
        assert repo.exists("test-task-123") is True

        assert repo.delete("test-task-123") is True
        assert repo.exists("test-task-123") is False
        assert repo.get("test-task-123") is None

    def test_in_memory_repository_list_all(self):
        """Test InMemoryTaskRepository list_all operation"""
        repo = InMemoryTaskRepository()

        for i in range(3):
            task = ReviewFollowUpTask(
                task_id=f"test-task-{i}",
                original_pr_number=100 + i,
                repo="RC918/morningai",
                branch="feature/test",
                comment_url=f"https://github.com/.../{i}",
                comment_body=f"Test comment {i}",
            )
            repo.save(task)

        all_tasks = repo.list_all()
        assert len(all_tasks) == 3
        assert repo.count() == 3

    def test_in_memory_repository_get_nonexistent(self):
        """Test InMemoryTaskRepository get for non-existent task"""
        repo = InMemoryTaskRepository()
        assert repo.get("nonexistent") is None

    def test_in_memory_repository_delete_nonexistent(self):
        """Test InMemoryTaskRepository delete for non-existent task"""
        repo = InMemoryTaskRepository()
        assert repo.delete("nonexistent") is False

    def test_get_task_repository_default(self):
        """Test get_task_repository factory with default backend"""
        repo = get_task_repository()
        assert isinstance(repo, InMemoryTaskRepository)

    def test_get_task_repository_in_memory_explicit(self):
        """Test get_task_repository factory with explicit in_memory backend"""
        repo = get_task_repository(backend="in_memory")
        assert isinstance(repo, InMemoryTaskRepository)

    def test_service_with_custom_repository(self):
        """Test ReviewFollowUpService with custom repository"""
        custom_repo = InMemoryTaskRepository()
        service = ReviewFollowUpService(repository=custom_repo)

        assert service._repository is custom_repo

    def test_service_idempotent_task_creation(self):
        """Test that creating the same task twice returns existing task"""
        service = ReviewFollowUpService()

        triage_result = CommentTriageResult(
            comment_id="comment-123",
            source="gemini-code-assist",
            category=CommentCategory.STYLE,
            risk_level=RiskLevel.LOW,
            should_auto_fix=True,
            confidence=0.9,
            reason="Style issue",
            files_affected=["src/utils.py"],
            lines_affected=5,
        )

        task1 = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use consistent naming",
        )

        task2 = service.create_task(
            triage_result=triage_result,
            pr_number=456,
            repo="RC918/morningai",
            branch="feature/test",
            comment_url="https://github.com/...",
            comment_body="Use consistent naming",
        )

        assert task1.task_id == task2.task_id
        assert service._repository.count() == 1


FIXED_DATETIME_STR = "2025-01-15T10:30:00"


class TestRedisTaskRepository:
    """
    Tests for Redis Task Repository with mocked Redis client.

    Issue #2259: Phase B - Redis Integration with Feature Flag Control
    """

    def test_redis_repository_save_and_get(self):
        """Test RedisTaskRepository save and get with mock client"""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=86400)

        task = ReviewFollowUpTask(
            task_id="test-task-redis",
            original_pr_number=789,
            repo="RC918/morningai",
            branch="feature/redis",
            comment_url="https://github.com/...",
            comment_body="Redis test comment",
        )

        result = repo.save(task)
        assert result is True
        mock_client.setex.assert_called_once()

    def test_redis_repository_get_existing(self):
        """Test RedisTaskRepository get for existing task"""
        mock_client = MagicMock()
        task_data = {
            "task_id": "test-task-redis",
            "task_type": "review_follow_up",
            "original_pr_number": 789,
            "repo": "RC918/morningai",
            "branch": "feature/redis",
            "comment_url": "https://github.com/...",
            "comment_body": "Redis test comment",
            "file_path": "",
            "line_number": 0,
            "triage_result": None,
            "pr_context": None,
            "status": "pending",
            "action": "manual_review",
            "created_at": FIXED_DATETIME_STR,
            "updated_at": FIXED_DATETIME_STR,
            "result": None,
            "error": None,
            "metadata": {},
        }
        mock_client.get.return_value = json.dumps(task_data)

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=86400)
        retrieved = repo.get("test-task-redis")

        assert retrieved is not None
        assert retrieved.task_id == "test-task-redis"
        assert retrieved.original_pr_number == 789

    def test_redis_repository_delete(self):
        """Test RedisTaskRepository delete operation"""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=86400)
        result = repo.delete("test-task-redis")

        assert result is True
        mock_client.delete.assert_called_once()

    def test_redis_repository_exists(self):
        """Test RedisTaskRepository exists operation"""
        mock_client = MagicMock()
        mock_client.exists.return_value = 1

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=86400)
        result = repo.exists("test-task-redis")

        assert result is True
        mock_client.exists.assert_called_once()

    def test_redis_repository_ttl_configuration(self):
        """Test RedisTaskRepository TTL configuration"""
        mock_client = MagicMock()
        custom_ttl = 7 * 24 * 60 * 60  # 7 days

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=custom_ttl)
        assert repo._ttl == custom_ttl

    def test_redis_repository_default_ttl(self):
        """Test RedisTaskRepository default TTL (30 days)"""
        mock_client = MagicMock()
        repo = RedisTaskRepository(redis_client=mock_client)

        expected_ttl = 30 * 24 * 60 * 60  # 30 days
        assert repo._ttl == expected_ttl

    def test_get_task_repository_redis_backend(self):
        """Test get_task_repository factory with redis backend"""
        mock_client = MagicMock()
        repo = get_task_repository(backend="redis", redis_client=mock_client)

        assert isinstance(repo, RedisTaskRepository)

    def test_redis_repository_key_prefix(self):
        """Test RedisTaskRepository uses correct key prefix"""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        repo = RedisTaskRepository(redis_client=mock_client, ttl_seconds=86400)
        repo.get("test-task-123")

        expected_key = "review_follow_up:task:test-task-123"
        mock_client.get.assert_called_with(expected_key)

    def test_redis_repository_connection_failure_graceful(self):
        """Test RedisTaskRepository handles connection failure gracefully"""
        repo = RedisTaskRepository(redis_client=None, ttl_seconds=86400)

        assert repo.get("test-task") is None
        assert repo.delete("test-task") is False
        assert repo.exists("test-task") is False
        assert repo.count() == 0
        assert repo.list_all() == []
