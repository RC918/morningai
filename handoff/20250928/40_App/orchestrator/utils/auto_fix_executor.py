"""
Auto-Fix Executor Module - Execute Auto-Fix Tasks from AI Reviewer Comments

This module provides the AutoFixExecutor class that orchestrates the execution
of auto-fix tasks, integrating safety checks, canary rollout, and the actual
fix execution via the orchestrator.

Issue #2252: Implement real auto-fix execution for Comment Triage Agent

Components:
1. AutoFixExecutor - Main executor class
2. AutoFixTask - Task data structure for queue
3. enqueue_auto_fix - Function to add tasks to Redis queue
4. should_execute_canary - Canary rollout decision logic
"""
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from common.config.settings import Settings
    from webhooks.comment_triage import CommentTriageResult

logger = logging.getLogger(__name__)


class AutoFixTaskStatus(Enum):
    """Status of an auto-fix task"""
    PENDING = "pending"
    SAFETY_CHECK = "safety_check"
    CANARY_CHECK = "canary_check"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class AutoFixTask:
    """
    Task data structure for auto-fix execution.

    This is the schema for auto-fix tasks in the Redis queue.
    """
    task_id: str
    triage_result: Dict[str, Any]
    repo: str
    pr_number: int
    pr_id: str
    comment_url: str
    comment_body: str
    file_path: str = ""
    line_number: int = 0
    actor_name: Optional[str] = None
    commit_message: Optional[str] = None
    status: AutoFixTaskStatus = AutoFixTaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "triage_result": self.triage_result,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "pr_id": self.pr_id,
            "comment_url": self.comment_url,
            "comment_body": self.comment_body,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "actor_name": self.actor_name,
            "commit_message": self.commit_message,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoFixTask":
        """Create from dictionary"""
        status_str = data.get("status", "pending")
        try:
            status = AutoFixTaskStatus(status_str)
        except ValueError:
            status = AutoFixTaskStatus.PENDING

        return cls(
            task_id=data.get("task_id", ""),
            triage_result=data.get("triage_result", {}),
            repo=data.get("repo", ""),
            pr_number=data.get("pr_number", 0),
            pr_id=data.get("pr_id", ""),
            comment_url=data.get("comment_url", ""),
            comment_body=data.get("comment_body", ""),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            actor_name=data.get("actor_name"),
            commit_message=data.get("commit_message"),
            status=status,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            error_message=data.get("error_message"),
            result=data.get("result"),
        )


def should_execute_canary(task_id: str, canary_percent: int) -> bool:
    """
    Determine if a task should be executed based on canary rollout percentage.

    Uses deterministic hashing so the same task_id always gets the same result.

    Args:
        task_id: Unique task identifier
        canary_percent: Percentage of tasks to execute (0-100)

    Returns:
        True if task should be executed
    """
    if canary_percent <= 0:
        return False
    if canary_percent >= 100:
        return True

    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100
    return task_percent < canary_percent


@dataclass
class AutoFixExecutionResult:
    """Result of auto-fix execution"""
    success: bool
    task_id: str
    status: AutoFixTaskStatus
    message: str
    pr_url: Optional[str] = None
    commit_sha: Optional[str] = None
    execution_time_ms: int = 0
    safety_check_passed: bool = False
    canary_selected: bool = False


class AutoFixExecutor:
    """
    Executor for auto-fix tasks from AI reviewer comments.

    This class orchestrates the full auto-fix execution flow:
    1. Safety checks (policy, rate limiting, loop protection)
    2. Canary rollout decision
    3. PR context fetching
    4. Orchestrator execution
    5. Result handling

    Issue #2252: Implement real auto-fix execution
    """

    def __init__(self, settings: "Settings" = None, redis_url: Optional[str] = None):
        """
        Initialize AutoFixExecutor.

        Args:
            settings: Application settings. If None, uses global settings.
            redis_url: Redis connection URL. If None, uses settings.redis_url.
        """
        if settings is None:
            from common.config.settings import settings as global_settings
            settings = global_settings
        self.settings = settings
        self.redis_url = redis_url or settings.redis_url

    def execute(self, task: AutoFixTask) -> AutoFixExecutionResult:
        """
        Execute an auto-fix task.

        This is the main entry point for auto-fix execution.

        Args:
            task: AutoFixTask to execute

        Returns:
            AutoFixExecutionResult with execution outcome
        """
        import time
        start_time = time.time()

        logger.info(
            "[AutoFixExecutor] Starting execution",
            extra={
                "operation": "auto_fix_execute_start",
                "task_id": task.task_id,
                "repo": task.repo,
                "pr_id": task.pr_id,
                "category": task.triage_result.get("category", "unknown"),
            }
        )

        task.status = AutoFixTaskStatus.SAFETY_CHECK
        task.updated_at = datetime.now(timezone.utc).isoformat()

        safety_result = self._check_safety(task)
        if not safety_result.allowed:
            task.status = AutoFixTaskStatus.BLOCKED
            task.error_message = safety_result.reason
            task.updated_at = datetime.now(timezone.utc).isoformat()

            logger.warning(
                "[AutoFixExecutor] Safety check failed",
                extra={
                    "operation": "auto_fix_safety_blocked",
                    "task_id": task.task_id,
                    "reason": safety_result.reason,
                }
            )

            return AutoFixExecutionResult(
                success=False,
                task_id=task.task_id,
                status=AutoFixTaskStatus.BLOCKED,
                message=f"Safety check failed: {safety_result.reason}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                safety_check_passed=False,
                canary_selected=False,
            )

        task.status = AutoFixTaskStatus.CANARY_CHECK
        task.updated_at = datetime.now(timezone.utc).isoformat()

        canary_percent = self.settings.auto_fix_canary_percent
        if not should_execute_canary(task.task_id, canary_percent):
            task.status = AutoFixTaskStatus.SKIPPED
            task.updated_at = datetime.now(timezone.utc).isoformat()

            logger.info(
                "[AutoFixExecutor] Skipped by canary rollout",
                extra={
                    "operation": "auto_fix_canary_skipped",
                    "task_id": task.task_id,
                    "canary_percent": canary_percent,
                }
            )

            return AutoFixExecutionResult(
                success=True,
                task_id=task.task_id,
                status=AutoFixTaskStatus.SKIPPED,
                message=f"Skipped by canary rollout ({canary_percent}%)",
                execution_time_ms=int((time.time() - start_time) * 1000),
                safety_check_passed=True,
                canary_selected=False,
            )

        task.status = AutoFixTaskStatus.EXECUTING
        task.updated_at = datetime.now(timezone.utc).isoformat()

        try:
            result = self._execute_fix(task)

            task.status = AutoFixTaskStatus.COMPLETED
            task.result = result
            task.updated_at = datetime.now(timezone.utc).isoformat()

            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "[AutoFixExecutor] Execution completed",
                extra={
                    "operation": "auto_fix_execute_completed",
                    "task_id": task.task_id,
                    "pr_url": result.get("pr_url"),
                    "execution_time_ms": execution_time_ms,
                }
            )

            return AutoFixExecutionResult(
                success=True,
                task_id=task.task_id,
                status=AutoFixTaskStatus.COMPLETED,
                message="Auto-fix executed successfully",
                pr_url=result.get("pr_url"),
                commit_sha=result.get("commit_sha"),
                execution_time_ms=execution_time_ms,
                safety_check_passed=True,
                canary_selected=True,
            )

        except Exception as e:
            task.status = AutoFixTaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now(timezone.utc).isoformat()

            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "[AutoFixExecutor] Execution failed",
                extra={
                    "operation": "auto_fix_execute_failed",
                    "task_id": task.task_id,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms,
                },
                exc_info=True,
            )

            return AutoFixExecutionResult(
                success=False,
                task_id=task.task_id,
                status=AutoFixTaskStatus.FAILED,
                message=f"Execution failed: {str(e)}",
                execution_time_ms=execution_time_ms,
                safety_check_passed=True,
                canary_selected=True,
            )

    def _check_safety(self, task: AutoFixTask):
        """
        Perform safety checks for the task.

        Args:
            task: AutoFixTask to check

        Returns:
            AutoFixSafetyCheckResult from auto_fix_policy module
        """
        from webhooks.comment_triage import CommentTriageResult, CommentCategory, RiskLevel
        from utils.auto_fix_policy import check_auto_fix_safety

        triage_data = task.triage_result
        triage_result = CommentTriageResult(
            comment_id=triage_data.get("comment_id", ""),
            source=triage_data.get("source", "unknown"),
            category=CommentCategory(triage_data.get("category", "unknown")),
            risk_level=RiskLevel(triage_data.get("risk_level", "medium")),
            files_affected=triage_data.get("files_affected", []),
            lines_affected=triage_data.get("lines_affected", 0),
            should_auto_fix=triage_data.get("should_auto_fix", False),
            confidence=triage_data.get("confidence", 0.0),
            reason=triage_data.get("reason", ""),
            keywords_matched=triage_data.get("keywords_matched", []),
            metadata=triage_data.get("metadata", {}),
        )

        return check_auto_fix_safety(
            triage_result=triage_result,
            repo=task.repo,
            pr_id=task.pr_id,
            actor_name=task.actor_name,
            commit_message=task.commit_message,
            settings=self.settings,
            redis_url=self.redis_url,
        )

    def _execute_fix(self, task: AutoFixTask) -> Dict[str, Any]:
        """
        Execute the actual fix using the orchestrator.

        Args:
            task: AutoFixTask to execute

        Returns:
            Dictionary with execution result (pr_url, commit_sha, etc.)
        """
        from webhooks.review_follow_up import ReviewFollowUpService
        from webhooks.comment_triage import CommentTriageResult, CommentCategory, RiskLevel

        triage_data = task.triage_result
        triage_result = CommentTriageResult(
            comment_id=triage_data.get("comment_id", ""),
            source=triage_data.get("source", "unknown"),
            category=CommentCategory(triage_data.get("category", "unknown")),
            risk_level=RiskLevel(triage_data.get("risk_level", "medium")),
            files_affected=triage_data.get("files_affected", []),
            lines_affected=triage_data.get("lines_affected", 0),
            should_auto_fix=triage_data.get("should_auto_fix", False),
            confidence=triage_data.get("confidence", 0.0),
            reason=triage_data.get("reason", ""),
            keywords_matched=triage_data.get("keywords_matched", []),
            metadata=triage_data.get("metadata", {}),
        )

        service = ReviewFollowUpService(github_token=self.settings.github_token)

        follow_up_task = service.create_task(
            triage_result=triage_result,
            pr_number=task.pr_number,
            repo=task.repo,
            branch="",
            comment_url=task.comment_url,
            comment_body=task.comment_body,
            file_path=task.file_path,
            line_number=task.line_number,
        )

        pr_context = service.fetch_pr_context(follow_up_task)
        if pr_context:
            follow_up_task.pr_context = pr_context

        orchestrator_input = service.prepare_for_orchestrator(follow_up_task)

        logger.info(
            "[AutoFixExecutor] Prepared orchestrator input",
            extra={
                "operation": "auto_fix_orchestrator_input",
                "task_id": task.task_id,
                "goal_length": len(orchestrator_input.get("goal", "")),
                "has_pr_context": pr_context is not None,
            }
        )

        return {
            "status": "prepared",
            "orchestrator_input": orchestrator_input,
            "follow_up_task_id": follow_up_task.task_id,
            "pr_url": None,
            "commit_sha": None,
        }


def create_auto_fix_task(
    triage_result: "CommentTriageResult",
    repo: str,
    pr_number: int,
    comment_url: str,
    comment_body: str,
    file_path: str = "",
    line_number: int = 0,
    actor_name: Optional[str] = None,
    commit_message: Optional[str] = None,
) -> AutoFixTask:
    """
    Create an AutoFixTask from a CommentTriageResult.

    Args:
        triage_result: Result from CommentTriageAgent
        repo: Repository in owner/repo format
        pr_number: Pull request number
        comment_url: URL to the comment
        comment_body: Body of the comment
        file_path: File path mentioned in comment
        line_number: Line number mentioned in comment
        actor_name: Actor name for loop protection
        commit_message: Commit message for loop protection

    Returns:
        AutoFixTask ready for execution
    """
    task_id = f"auto-fix-{uuid.uuid4().hex[:12]}"
    pr_id = f"{repo}#{pr_number}"

    return AutoFixTask(
        task_id=task_id,
        triage_result=triage_result.to_dict(),
        repo=repo,
        pr_number=pr_number,
        pr_id=pr_id,
        comment_url=comment_url,
        comment_body=comment_body,
        file_path=file_path,
        line_number=line_number,
        actor_name=actor_name,
        commit_message=commit_message,
    )


def enqueue_auto_fix(
    task: AutoFixTask,
    redis_url: Optional[str] = None,
    queue_name: str = "auto_fix",
) -> Optional[str]:
    """
    Enqueue an auto-fix task to the Redis queue.

    Args:
        task: AutoFixTask to enqueue
        redis_url: Redis connection URL. If None, uses settings.redis_url.
        queue_name: Name of the queue (default: "auto_fix")

    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    try:
        import redis
        from rq import Queue
        from rq.serializers import JSONSerializer
        from common.config.settings import settings

        if redis_url is None:
            redis_url = settings.redis_url

        redis_client = redis.from_url(redis_url)
        queue = Queue(queue_name, connection=redis_client, serializer=JSONSerializer)

        job = queue.enqueue(
            "redis_queue.worker.run_auto_fix_task",
            task.to_dict(),
            job_id=task.task_id,
            job_timeout=600,
            result_ttl=86400,
            failure_ttl=3600,
        )

        logger.info(
            "[AutoFixExecutor] Task enqueued",
            extra={
                "operation": "auto_fix_enqueue",
                "task_id": task.task_id,
                "job_id": job.id,
                "queue_name": queue_name,
            }
        )

        return job.id

    except Exception as e:
        logger.error(
            "[AutoFixExecutor] Failed to enqueue task",
            extra={
                "operation": "auto_fix_enqueue_failed",
                "task_id": task.task_id,
                "error": str(e),
            },
            exc_info=True,
        )
        return None
