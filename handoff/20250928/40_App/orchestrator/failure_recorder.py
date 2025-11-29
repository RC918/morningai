#!/usr/bin/env python3
"""
Failure Recorder Module - Phase 5 PR-1

Records workflow failures for analysis, replay, and knowledge base building.

Captures failures when:
- Workflow completes with status=error
- Fixer exhausts all retries (MAX_FIXER_RETRIES reached)
- Unexpected exceptions occur during orchestration

All operations are wrapped in try/except to never break the job path.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

FAILURE_KEY_PREFIX = "orchestrator:failures"
FAILURE_LIST_KEY = f"{FAILURE_KEY_PREFIX}:list"
FAILURE_TTL_SECONDS = 86400 * 30


@dataclass
class FailureRecord:
    """
    Schema for recording workflow failures

    Core fields (from roadmap):
    - trace_id: Unique workflow identifier
    - task_type: Type of task (from planner/semantic rules)
    - goal: Human-readable goal description
    - error_type: Categorized error type
    - fixer_retries: Number of fix attempts made
    - merge_decision: Final merge decision if applicable
    - pr_url: Pull request URL if created

    Additional fields for debugging and future PRs:
    - id: Unique failure record identifier
    - error_message: Detailed error message
    - status: Final workflow status
    - created_at: Timestamp when failure was recorded
    - env: Environment (staging/production)
    - pipeline: Pipeline name (e.g., "5-agent-advisory")
    - metadata: Additional context for future extensions
    """
    trace_id: str
    goal: str
    error_type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: Optional[str] = None
    error_message: Optional[str] = None
    fixer_retries: int = 0
    merge_decision: Optional[str] = None
    pr_url: Optional[str] = None
    status: str = "error"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    env: str = "production"
    pipeline: str = "5-agent-advisory"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureRecord":
        """Create FailureRecord from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class FailureRecorder:
    """
    Records and retrieves workflow failures

    Uses Redis for storage with:
    - Per-record keys: orchestrator:failures:<failure_id>
    - List key: orchestrator:failures:list (newest first)
    """

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        enabled: bool = True,
        ttl_seconds: int = FAILURE_TTL_SECONDS,
        key_prefix: str = FAILURE_KEY_PREFIX
    ):
        """
        Initialize failure recorder

        Args:
            redis_client: Redis client instance (optional, disabled if None)
            enabled: Whether failure recording is enabled
            ttl_seconds: TTL for failure records (default: 30 days)
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis_client
        self.enabled = enabled and redis_client is not None
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.list_key = f"{key_prefix}:list"

    def _get_record_key(self, failure_id: str) -> str:
        """Generate Redis key for a failure record"""
        return f"{self.key_prefix}:{failure_id}"

    def record_failure(self, failure: FailureRecord) -> Optional[str]:
        """
        Record a workflow failure

        Args:
            failure: FailureRecord instance to store

        Returns:
            Failure ID if recorded successfully, None otherwise
        """
        if not self.enabled:
            logger.debug("[FailureRecorder] Recording disabled, skipping")
            return None

        try:
            record_key = self._get_record_key(failure.id)
            record_data = json.dumps(failure.to_dict())

            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(record_key, record_data, ex=self.ttl_seconds)
                pipe.lpush(self.list_key, failure.id)
                pipe.ltrim(self.list_key, 0, 9999)
                pipe.execute()

            logger.info(f"[FailureRecorder] Recorded failure: {failure.id}", extra={
                "operation": "record_failure",
                "failure_id": failure.id,
                "trace_id": failure.trace_id,
                "error_type": failure.error_type,
                "fixer_retries": failure.fixer_retries
            })

            return failure.id

        except Exception as e:
            logger.warning(f"[FailureRecorder] Failed to record failure: {e}", extra={
                "operation": "record_failure",
                "trace_id": failure.trace_id,
                "error": str(e)
            })
            return None

    def record_failure_from_state(
        self,
        state: Dict[str, Any],
        error_type: str,
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Record a failure from orchestrator state

        Args:
            state: AgentState dictionary from orchestrator
            error_type: Categorized error type
            error_message: Optional detailed error message

        Returns:
            Failure ID if recorded successfully, None otherwise
        """
        try:
            from common.config.settings import settings
            env = "staging" if settings.environment == "staging" else "production"
        except Exception:
            env = "production"

        failure = FailureRecord(
            trace_id=state.get("trace_id", "unknown"),
            goal=state.get("goal", "")[:500],
            error_type=error_type,
            task_type=state.get("task_type"),
            error_message=error_message or state.get("error"),
            fixer_retries=state.get("retry_count", 0),
            merge_decision=state.get("merge_decision"),
            pr_url=state.get("pr_url"),
            status=state.get("final_result", {}).get("status", "error"),
            env=env,
            metadata={
                "planner_type": state.get("planner_type"),
                "security_risk": state.get("security_risk"),
                "governance_risk": state.get("governance_risk"),
                "ci_state": state.get("ci_state"),
                "code_quality_score": state.get("code_quality_score"),
            }
        )

        return self.record_failure(failure)

    def get_failure(self, failure_id: str) -> Optional[FailureRecord]:
        """
        Get a specific failure record by ID

        Args:
            failure_id: Unique failure identifier

        Returns:
            FailureRecord if found, None otherwise
        """
        if not self.enabled:
            return None

        try:
            record_key = self._get_record_key(failure_id)
            record_data = self.redis.get(record_key)

            if record_data:
                data = json.loads(record_data)
                return FailureRecord.from_dict(data)

            return None

        except Exception as e:
            logger.warning(f"[FailureRecorder] Failed to get failure: {e}", extra={
                "operation": "get_failure",
                "failure_id": failure_id,
                "error": str(e)
            })
            return None

    def list_failures(
        self,
        limit: int = 50,
        offset: int = 0,
        trace_id: Optional[str] = None,
        error_type: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[FailureRecord]:
        """
        List failure records with optional filtering

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            trace_id: Filter by trace_id
            error_type: Filter by error_type
            task_type: Filter by task_type

        Returns:
            List of FailureRecord instances
        """
        if not self.enabled:
            return []

        try:
            failure_ids = self.redis.lrange(self.list_key, offset, offset + limit * 2 - 1)

            failures = []
            for failure_id in failure_ids:
                if isinstance(failure_id, bytes):
                    failure_id = failure_id.decode('utf-8')

                failure = self.get_failure(failure_id)
                if failure is None:
                    continue

                if trace_id and failure.trace_id != trace_id:
                    continue
                if error_type and failure.error_type != error_type:
                    continue
                if task_type and failure.task_type != task_type:
                    continue

                failures.append(failure)

                if len(failures) >= limit:
                    break

            return failures

        except Exception as e:
            logger.warning(f"[FailureRecorder] Failed to list failures: {e}", extra={
                "operation": "list_failures",
                "error": str(e)
            })
            return []

    def get_failure_count(self) -> int:
        """Get total number of recorded failures"""
        if not self.enabled:
            return 0

        try:
            return self.redis.llen(self.list_key)
        except Exception as e:
            logger.warning(f"[FailureRecorder] Failed to get count: {e}")
            return 0

    def get_failure_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of failures

        Returns:
            Dictionary with failure statistics
        """
        if not self.enabled:
            return {"enabled": False, "total": 0}

        try:
            failures = self.list_failures(limit=100)

            error_types: Dict[str, int] = {}
            task_types: Dict[str, int] = {}
            retry_distribution: Dict[int, int] = {}

            for failure in failures:
                error_types[failure.error_type] = error_types.get(failure.error_type, 0) + 1

                if failure.task_type:
                    task_types[failure.task_type] = task_types.get(failure.task_type, 0) + 1

                retry_distribution[failure.fixer_retries] = retry_distribution.get(failure.fixer_retries, 0) + 1

            return {
                "enabled": True,
                "total": self.get_failure_count(),
                "recent_count": len(failures),
                "error_types": error_types,
                "task_types": task_types,
                "retry_distribution": retry_distribution
            }

        except Exception as e:
            logger.warning(f"[FailureRecorder] Failed to get summary: {e}")
            return {"enabled": True, "total": 0, "error": str(e)}


_failure_recorder: Optional[FailureRecorder] = None


def get_failure_recorder(
    redis_client: Optional["redis.Redis"] = None,
    enabled: bool = True
) -> FailureRecorder:
    """
    Get or create the global failure recorder instance

    Args:
        redis_client: Redis client (uses existing if not provided)
        enabled: Whether recording is enabled

    Returns:
        FailureRecorder instance
    """
    global _failure_recorder

    if _failure_recorder is None:
        _failure_recorder = FailureRecorder(
            redis_client=redis_client,
            enabled=enabled
        )

    return _failure_recorder


def create_failure_recorder(
    redis_client: Optional["redis.Redis"] = None,
    enabled: bool = True
) -> FailureRecorder:
    """
    Create a new failure recorder instance (for testing)

    Args:
        redis_client: Redis client
        enabled: Whether recording is enabled

    Returns:
        New FailureRecorder instance
    """
    return FailureRecorder(
        redis_client=redis_client,
        enabled=enabled
    )
