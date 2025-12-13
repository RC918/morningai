"""
Task Repository for Review Follow-up Tasks

Issue #2259: Migrate ReviewFollowUpService task storage to Redis/DB

This module provides a repository abstraction layer for storing and retrieving
ReviewFollowUpTask instances. It supports multiple backends:
- InMemory: For testing and backward compatibility
- Redis: For production use with TTL-based expiration

Design decisions:
1. Deterministic Task ID: pr{pr_number}_comment{comment_id} for idempotency
2. 30-day TTL (configurable) for Redis storage
3. Repository interface allows easy backend switching via feature flag
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .review_follow_up import ReviewFollowUpTask

logger = logging.getLogger(__name__)


def generate_task_id(pr_number: int, comment_id: str) -> str:
    """
    Generate a deterministic task ID for idempotency.

    Issue #2259: Changed from random UUID to deterministic ID to support
    idempotent task creation and avoid duplicate tasks.

    Args:
        pr_number: Pull request number
        comment_id: Comment ID from the review comment

    Returns:
        Deterministic task ID in format: pr{pr_number}_comment{comment_id}
    """
    return f"pr{pr_number}_comment{comment_id}"


class ReviewFollowUpTaskRepository(ABC):
    """
    Abstract base class for ReviewFollowUpTask storage.

    This interface defines the contract for task storage backends.
    Implementations must handle serialization/deserialization of tasks.
    """

    @abstractmethod
    def save(self, task: "ReviewFollowUpTask") -> bool:
        """
        Save a task to the repository.

        Args:
            task: ReviewFollowUpTask instance to save

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get(self, task_id: str) -> Optional["ReviewFollowUpTask"]:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            ReviewFollowUpTask if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_all(self) -> List["ReviewFollowUpTask"]:
        """
        List all tasks in the repository.

        Returns:
            List of all ReviewFollowUpTask instances
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of tasks.

        Returns:
            Number of tasks in the repository
        """
        pass

    @abstractmethod
    def exists(self, task_id: str) -> bool:
        """
        Check if a task exists.

        Args:
            task_id: Task identifier

        Returns:
            True if task exists, False otherwise
        """
        pass


class InMemoryTaskRepository(ReviewFollowUpTaskRepository):
    """
    In-memory implementation of task repository.

    This is the default backend for backward compatibility and testing.
    Tasks are stored in a dictionary and lost on service restart.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, "ReviewFollowUpTask"] = {}
        logger.info("[InMemoryTaskRepository] Initialized")

    def save(self, task: "ReviewFollowUpTask") -> bool:
        """Save task to in-memory dictionary."""
        try:
            self._tasks[task.task_id] = task
            logger.debug(
                "[InMemoryTaskRepository] Saved task: id=%s",
                task.task_id,
            )
            return True
        except Exception as e:
            logger.error(
                "[InMemoryTaskRepository] Failed to save task %s: %s",
                task.task_id,
                e,
            )
            return False

    def get(self, task_id: str) -> Optional["ReviewFollowUpTask"]:
        """Retrieve task from in-memory dictionary."""
        return self._tasks.get(task_id)

    def delete(self, task_id: str) -> bool:
        """Delete task from in-memory dictionary."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug(
                "[InMemoryTaskRepository] Deleted task: id=%s",
                task_id,
            )
            return True
        return False

    def list_all(self) -> List["ReviewFollowUpTask"]:
        """List all tasks from in-memory dictionary."""
        return list(self._tasks.values())

    def count(self) -> int:
        """Count tasks in in-memory dictionary."""
        return len(self._tasks)

    def exists(self, task_id: str) -> bool:
        """Check if task exists in in-memory dictionary."""
        return task_id in self._tasks


class RedisTaskRepository(ReviewFollowUpTaskRepository):
    """
    Redis-based implementation of task repository.

    Issue #2259: Production backend for multi-worker consistency
    and service restart durability.

    Features:
    - 30-day TTL (configurable via REVIEW_FOLLOW_UP_TASK_TTL)
    - JSON serialization for task data
    - Key prefix: review_follow_up:task:{task_id}
    """

    KEY_PREFIX = "review_follow_up:task:"
    DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

    def __init__(
        self,
        redis_client: Any = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Initialize Redis task repository.

        Args:
            redis_client: Redis client instance (optional, will create if not provided)
            ttl_seconds: TTL for task entries in seconds (default: 30 days)
        """
        self._client = redis_client
        self._ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS
        self._initialized = False

        if self._client is not None:
            self._initialized = True
            logger.info(
                "[RedisTaskRepository] Initialized with TTL=%d seconds (%d days)",
                self._ttl,
                self._ttl // (24 * 60 * 60),
            )

    def _ensure_client(self) -> bool:
        """Ensure Redis client is available."""
        if self._initialized and self._client is not None:
            return True

        try:
            from common.config.settings import settings

            # Try Upstash first, then standard Redis
            upstash_url = settings.upstash_redis_rest_url
            if upstash_url:
                try:
                    from upstash_redis import Redis
                    self._client = Redis(
                        url=upstash_url,
                        token=settings.upstash_redis_rest_token,
                    )
                    self._initialized = True
                    logger.info("[RedisTaskRepository] Connected to Upstash Redis")
                    return True
                except ImportError:
                    logger.warning(
                        "[RedisTaskRepository] upstash-redis not installed"
                    )

            # Fallback to standard Redis
            redis_url = settings.redis_url
            if redis_url:
                import redis
                self._client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self._initialized = True
                logger.info("[RedisTaskRepository] Connected to Redis")
                return True

            logger.warning(
                "[RedisTaskRepository] No Redis configuration found"
            )
            return False

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to initialize Redis client: %s",
                e,
            )
            return False

    def _get_key(self, task_id: str) -> str:
        """Generate Redis key for task."""
        return f"{self.KEY_PREFIX}{task_id}"

    def _serialize_task(self, task: "ReviewFollowUpTask") -> str:
        """Serialize task to JSON string."""
        return json.dumps(task.to_dict(), default=str)

    def _deserialize_task(self, data: str) -> Optional["ReviewFollowUpTask"]:
        """Deserialize task from JSON string."""
        try:
            from .review_follow_up import (
                ReviewFollowUpTask,
                ReviewFollowUpStatus,
                ReviewFollowUpAction,
                PRContext,
            )
            from .comment_triage import CommentTriageResult

            task_dict = json.loads(data)

            # Reconstruct status and action enums
            status = ReviewFollowUpStatus(task_dict.get("status", "pending"))
            action = ReviewFollowUpAction(task_dict.get("action", "manual_review"))

            # Reconstruct PRContext if present
            pr_context = None
            if task_dict.get("pr_context"):
                pr_ctx_dict = task_dict["pr_context"]
                pr_context = PRContext(
                    pr_number=pr_ctx_dict.get("pr_number", 0),
                    repo=pr_ctx_dict.get("repo", ""),
                    branch=pr_ctx_dict.get("branch", ""),
                    base_branch=pr_ctx_dict.get("base_branch", "main"),
                    title=pr_ctx_dict.get("title", ""),
                    description=pr_ctx_dict.get("description", ""),
                    author=pr_ctx_dict.get("author", ""),
                    diff="",  # diff_length is stored, not full diff
                    files_changed=pr_ctx_dict.get("files_changed", []),
                    labels=pr_ctx_dict.get("labels", []),
                    ci_status=pr_ctx_dict.get("ci_status", "unknown"),
                    metadata=pr_ctx_dict.get("metadata", {}),
                )

            # Reconstruct triage result if present
            triage_result = None
            if task_dict.get("triage_result"):
                triage_result = CommentTriageResult.from_dict(
                    task_dict["triage_result"]
                )

            # Parse datetime strings
            created_at = datetime.fromisoformat(task_dict.get("created_at", datetime.now(timezone.utc).isoformat()))
            updated_at = datetime.fromisoformat(task_dict.get("updated_at", datetime.now(timezone.utc).isoformat()))

            return ReviewFollowUpTask(
                task_id=task_dict["task_id"],
                task_type=task_dict.get("task_type", "review_follow_up"),
                original_pr_number=task_dict.get("original_pr_number", 0),
                repo=task_dict.get("repo", ""),
                branch=task_dict.get("branch", ""),
                comment_url=task_dict.get("comment_url", ""),
                comment_body=task_dict.get("comment_body", ""),
                file_path=task_dict.get("file_path", ""),
                line_number=task_dict.get("line_number", 0),
                triage_result=triage_result,
                pr_context=pr_context,
                status=status,
                action=action,
                created_at=created_at,
                updated_at=updated_at,
                result=task_dict.get("result"),
                error=task_dict.get("error"),
                metadata=task_dict.get("metadata", {}),
            )

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to deserialize task: %s",
                e,
                exc_info=True,
            )
            return None

    def save(self, task: "ReviewFollowUpTask") -> bool:
        """Save task to Redis with TTL."""
        if not self._ensure_client():
            logger.warning(
                "[RedisTaskRepository] Cannot save task %s: Redis unavailable",
                task.task_id,
            )
            return False

        try:
            key = self._get_key(task.task_id)
            data = self._serialize_task(task)

            # Use SETEX for atomic set with TTL
            self._client.setex(key, self._ttl, data)

            logger.info(
                "[RedisTaskRepository] Saved task: id=%s, ttl=%d",
                task.task_id,
                self._ttl,
            )
            return True

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to save task %s: %s",
                task.task_id,
                e,
            )
            return False

    def get(self, task_id: str) -> Optional["ReviewFollowUpTask"]:
        """Retrieve task from Redis."""
        if not self._ensure_client():
            return None

        try:
            key = self._get_key(task_id)
            data = self._client.get(key)

            if data is None:
                return None

            return self._deserialize_task(data)

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to get task %s: %s",
                task_id,
                e,
            )
            return None

    def delete(self, task_id: str) -> bool:
        """Delete task from Redis."""
        if not self._ensure_client():
            return False

        try:
            key = self._get_key(task_id)
            result = self._client.delete(key)
            deleted = result > 0

            if deleted:
                logger.debug(
                    "[RedisTaskRepository] Deleted task: id=%s",
                    task_id,
                )

            return deleted

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to delete task %s: %s",
                task_id,
                e,
            )
            return False

    def list_all(self) -> List["ReviewFollowUpTask"]:
        """List all tasks from Redis using SCAN."""
        if not self._ensure_client():
            return []

        try:
            tasks = []
            pattern = f"{self.KEY_PREFIX}*"

            # Use scan_iter if available (redis-py), otherwise use scan
            if hasattr(self._client, "scan_iter"):
                for key in self._client.scan_iter(match=pattern):
                    data = self._client.get(key)
                    if data:
                        task = self._deserialize_task(data)
                        if task:
                            tasks.append(task)
            else:
                # Upstash Redis fallback
                cursor = 0
                while True:
                    result = self._client.scan(cursor=cursor, match=pattern, count=100)
                    if isinstance(result, (list, tuple)) and len(result) >= 2:
                        cursor = result[0]
                        keys = result[1]
                        for key in keys:
                            data = self._client.get(key)
                            if data:
                                task = self._deserialize_task(data)
                                if task:
                                    tasks.append(task)
                        if cursor in (0, "0", b"0"):
                            break
                    else:
                        break

            logger.debug(
                "[RedisTaskRepository] Listed %d tasks",
                len(tasks),
            )
            return tasks

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to list tasks: %s",
                e,
            )
            return []

    def count(self) -> int:
        """Count tasks in Redis."""
        if not self._ensure_client():
            return 0

        try:
            pattern = f"{self.KEY_PREFIX}*"
            count = 0

            # Use scan to count keys
            if hasattr(self._client, "scan_iter"):
                for _ in self._client.scan_iter(match=pattern):
                    count += 1
            else:
                cursor = 0
                while True:
                    result = self._client.scan(cursor=cursor, match=pattern, count=100)
                    if isinstance(result, (list, tuple)) and len(result) >= 2:
                        cursor = result[0]
                        keys = result[1]
                        count += len(keys)
                        if cursor in (0, "0", b"0"):
                            break
                    else:
                        break

            return count

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to count tasks: %s",
                e,
            )
            return 0

    def exists(self, task_id: str) -> bool:
        """Check if task exists in Redis."""
        if not self._ensure_client():
            return False

        try:
            key = self._get_key(task_id)
            return bool(self._client.exists(key))

        except Exception as e:
            logger.error(
                "[RedisTaskRepository] Failed to check task existence %s: %s",
                task_id,
                e,
            )
            return False


def get_task_repository(
    backend: Optional[str] = None,
    redis_client: Any = None,
    ttl_seconds: Optional[int] = None,
) -> ReviewFollowUpTaskRepository:
    """
    Factory function to get the appropriate task repository.

    Issue #2259: Feature flag controlled backend selection.

    Args:
        backend: Backend type ("in_memory", "redis"). If None, reads from
                 REVIEW_FOLLOW_UP_STORE_BACKEND environment variable.
        redis_client: Optional Redis client for Redis backend
        ttl_seconds: Optional TTL for Redis backend

    Returns:
        ReviewFollowUpTaskRepository instance
    """
    import os

    if backend is None:
        backend = os.getenv("REVIEW_FOLLOW_UP_STORE_BACKEND", "in_memory")

    backend = backend.lower()

    if backend == "redis":
        # Get TTL from settings if not provided
        if ttl_seconds is None:
            ttl_seconds = int(os.getenv(
                "REVIEW_FOLLOW_UP_TASK_TTL",
                str(RedisTaskRepository.DEFAULT_TTL_SECONDS)
            ))

        repo = RedisTaskRepository(
            redis_client=redis_client,
            ttl_seconds=ttl_seconds,
        )
        logger.info(
            "[TaskRepository] Using Redis backend with TTL=%d seconds",
            ttl_seconds,
        )
        return repo

    # Default to in-memory
    logger.info("[TaskRepository] Using in-memory backend")
    return InMemoryTaskRepository()
