#!/usr/bin/env python3
"""
Failure Recorder Module - Phase 5 PR-1

Records workflow failures for analysis, replay, and knowledge base building.

Captures failures when:
- Workflow completes with status=error
- Fixer exhausts all retries (MAX_FIXER_RETRIES reached)
- Unexpected exceptions occur during orchestration

All operations are wrapped in try/except to never break the job path.

Slack Alerting (Issue #3517):
- Sends Slack webhook notifications when failures are recorded
- Rate limited to max 10 alerts/minute to prevent spam
- Graceful degradation if Slack webhook fails
"""

import logging
import json
import os
import time
import uuid
from collections import deque
from typing import Dict, List, Optional, Any, Deque
from datetime import datetime
from dataclasses import dataclass, asdict, field

try:
    import redis
except ImportError:
    redis = None

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)

# Slack alerting constants (Issue #3517)
SLACK_RATE_LIMIT_MAX_ALERTS = 10  # Max alerts per window
SLACK_RATE_LIMIT_WINDOW_SECONDS = 60  # Window size in seconds
SLACK_REQUEST_TIMEOUT_SECONDS = 5  # Timeout for Slack webhook requests

FAILURE_KEY_PREFIX = "orchestrator:failures"
FAILURE_LIST_KEY = f"{FAILURE_KEY_PREFIX}:list"
FAILURE_TTL_SECONDS = 86400 * 30
DEFAULT_REPLAY_REPO = "RC918/morningai"


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


@dataclass
class ReplayResult:
    """
    Result of a replay operation

    Attributes:
        success: Whether the replay was successfully enqueued
        failure_id: ID of the original failure record
        new_trace_id: New trace ID for the replayed workflow
        job_id: RQ job ID if successfully enqueued
        error: Error message if replay failed
    """
    success: bool
    failure_id: str
    new_trace_id: Optional[str] = None
    job_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class FailureRecorder:
    """
    Records and retrieves workflow failures

    Uses Redis for storage with:
    - Per-record keys: orchestrator:failures:<failure_id>
    - List key: orchestrator:failures:list (newest first)

    Slack Alerting (Issue #3517):
    - Sends Slack webhook notifications when failures are recorded
    - Rate limited to max 10 alerts/minute to prevent spam
    - Graceful degradation if Slack webhook fails
    """

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        enabled: bool = True,
        ttl_seconds: int = FAILURE_TTL_SECONDS,
        key_prefix: str = FAILURE_KEY_PREFIX,
        slack_webhook_url: Optional[str] = None,
    ):
        """
        Initialize failure recorder

        Args:
            redis_client: Redis client instance (optional, disabled if None)
            enabled: Whether failure recording is enabled
            ttl_seconds: TTL for failure records (default: 30 days)
            key_prefix: Prefix for all Redis keys
            slack_webhook_url: Slack webhook URL for alerting (optional)
        """
        self.redis = redis_client
        self.enabled = enabled and redis_client is not None
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.list_key = f"{key_prefix}:list"

        # Slack alerting configuration (Issue #3517)
        self.slack_webhook_url = slack_webhook_url or os.environ.get(
            "SLACK_WEBHOOK_URL"
        )
        self.slack_enabled = bool(self.slack_webhook_url) and httpx is not None
        # Rate limiting: track timestamps of recent alerts
        self._alert_timestamps: Deque[float] = deque(
            maxlen=SLACK_RATE_LIMIT_MAX_ALERTS
        )

    def _get_record_key(self, failure_id: str) -> str:
        """Generate Redis key for a failure record"""
        return f"{self.key_prefix}:{failure_id}"

    def _is_rate_limited(self) -> bool:
        """
        Check if Slack alerting is rate limited (Issue #3517).

        Uses a sliding window algorithm to enforce max 10 alerts per minute.
        Uses time.monotonic() to avoid issues with clock adjustments (NTP, etc).

        Returns:
            True if rate limited (should skip alert), False otherwise
        """
        now = time.monotonic()
        window_start = now - SLACK_RATE_LIMIT_WINDOW_SECONDS

        # Remove timestamps outside the window
        while self._alert_timestamps and self._alert_timestamps[0] < window_start:
            self._alert_timestamps.popleft()

        # Check if we've hit the limit
        if len(self._alert_timestamps) >= SLACK_RATE_LIMIT_MAX_ALERTS:
            return True

        return False

    def _send_slack_alert(self, failure: FailureRecord) -> bool:
        """
        Send Slack webhook notification for a failure (Issue #3517).

        This is a best-effort operation - failures here should not break
        the main recording flow. Rate limited to max 10 alerts/minute.

        Args:
            failure: FailureRecord instance to alert about

        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.slack_enabled:
            logger.debug(
                "[FailureRecorder] Slack alerting disabled, skipping",
                extra={"failure_id": failure.id}
            )
            return False

        if self._is_rate_limited():
            logger.warning(
                "[FailureRecorder] Slack alert rate limited, skipping",
                extra={
                    "operation": "send_slack_alert",
                    "failure_id": failure.id,
                    "rate_limit": f"{SLACK_RATE_LIMIT_MAX_ALERTS}/{SLACK_RATE_LIMIT_WINDOW_SECONDS}s"
                }
            )
            return False

        try:
            # Build Slack message payload
            goal_truncated = (
                failure.goal[:200] + "..." if len(failure.goal) > 200 else failure.goal
            )

            # Format created_at with explicit UTC suffix for clarity
            created_at_display = f"{failure.created_at} UTC"

            # Build dashboard link (only if FAILURE_DASHBOARD_URL is configured)
            dashboard_url = os.environ.get("FAILURE_DASHBOARD_URL")

            payload = {
                "text": ":warning: Workflow Failure Recorded",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":warning: Workflow Failure Recorded",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Error Type:*\n`{failure.error_type}`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Trace ID:*\n`{failure.trace_id}`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Environment:*\n{failure.env}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Fixer Retries:*\n{failure.fixer_retries}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Goal:*\n{goal_truncated}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Failure ID: `{failure.id}` | Recorded at: {created_at_display}"
                            }
                        ]
                    }
                ]
            }

            # Add dashboard link button only if FAILURE_DASHBOARD_URL is configured
            if dashboard_url:
                failure_link = f"{dashboard_url}/failures/{failure.id}"
                payload["blocks"].insert(3, {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Failure Details",
                                "emoji": True
                            },
                            "url": failure_link,
                            "action_id": "view_failure"
                        }
                    ]
                })

            # Add PR URL if available
            if failure.pr_url:
                insert_index = 4 if dashboard_url else 3
                payload["blocks"].insert(insert_index, {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*PR:* <{failure.pr_url}|View Pull Request>"
                    }
                })

            # Send webhook request
            with httpx.Client(timeout=SLACK_REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(
                    self.slack_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

            # Record timestamp for rate limiting (using monotonic time)
            self._alert_timestamps.append(time.monotonic())

            logger.info(
                "[FailureRecorder] Slack alert sent successfully",
                extra={
                    "operation": "send_slack_alert",
                    "failure_id": failure.id,
                    "trace_id": failure.trace_id
                }
            )
            return True

        except httpx.TimeoutException:
            logger.warning(
                "[FailureRecorder] Slack alert timed out",
                extra={
                    "operation": "send_slack_alert",
                    "failure_id": failure.id,
                    "timeout": SLACK_REQUEST_TIMEOUT_SECONDS
                }
            )
            return False
        except httpx.HTTPStatusError as e:
            logger.warning(
                "[FailureRecorder] Slack alert HTTP error",
                extra={
                    "operation": "send_slack_alert",
                    "failure_id": failure.id,
                    "status_code": e.response.status_code,
                    "error": str(e)
                }
            )
            return False
        except Exception as e:
            # Never break the main flow - just log the error
            logger.warning(
                "[FailureRecorder] Failed to send Slack alert",
                extra={
                    "operation": "send_slack_alert",
                    "failure_id": failure.id,
                    "error": str(e)
                }
            )
            return False

    def _save_to_failure_memory(self, failure: FailureRecord) -> None:
        """
        Save failure to long-term memory (Supabase) for knowledge base

        This is a best-effort operation - failures here should not break
        the main recording flow. The failure_memory module handles graceful
        degradation when Supabase is not available.

        Args:
            failure: FailureRecord instance to persist
        """
        try:
            from failure_memory import save_failure_to_memory

            memory_key = save_failure_to_memory(failure)
            if memory_key:
                logger.info(
                    f"[FailureRecorder] Saved to failure memory: {memory_key}",
                    extra={
                        "operation": "save_to_failure_memory",
                        "failure_id": failure.id,
                        "memory_key": memory_key
                    }
                )
            else:
                logger.debug(
                    "[FailureRecorder] Failure memory not available, skipping",
                    extra={"failure_id": failure.id}
                )
        except ImportError:
            logger.debug(
                "[FailureRecorder] failure_memory module not available",
                extra={"failure_id": failure.id}
            )
        except Exception as e:
            # Never break the main flow - just log the error
            # Use static message for log aggregation (error details in extra)
            logger.warning(
                "[FailureRecorder] Failed to save to failure memory",
                extra={
                    "operation": "save_to_failure_memory",
                    "failure_id": failure.id,
                    "error": str(e)
                }
            )

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

            # Also save to long-term failure memory (Supabase) for knowledge base
            # This is wrapped in try/except to never break the main recording flow
            self._save_to_failure_memory(failure)

            # Send Slack alert (Issue #3517)
            # This is wrapped in try/except to never break the main recording flow
            try:
                self._send_slack_alert(failure)
            except Exception as slack_error:
                logger.warning(
                    "[FailureRecorder] Failed to send Slack alert",
                    extra={
                        "operation": "send_slack_alert",
                        "failure_id": failure.id,
                        "error": str(slack_error)
                    }
                )

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
        except (ImportError, AttributeError):
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
        Get summary statistics over the last 100 failures

        Returns:
            Dictionary with failure statistics including:
            - enabled: Whether the recorder is enabled
            - total: Total number of recorded failures
            - recent_count: Number of failures in the sample (up to 100)
            - error_types: Count by error type
            - task_types: Count by task type
            - retry_distribution: Count by number of fixer retries
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

    def replay_failure(self, failure_id: str, repo: Optional[str] = None) -> ReplayResult:
        """
        Replay a failed workflow by re-enqueuing it to the job queue

        This method retrieves the original failure record and creates a new
        orchestrator task with the same goal but a new trace_id.

        Args:
            failure_id: ID of the failure record to replay
            repo: Optional override for the repository (uses original if not provided)

        Returns:
            ReplayResult with success status, new trace_id, and job_id
        """
        if not self.enabled:
            return ReplayResult(
                success=False,
                failure_id=failure_id,
                error="Failure recorder is disabled"
            )

        try:
            failure = self.get_failure(failure_id)
            if failure is None:
                return ReplayResult(
                    success=False,
                    failure_id=failure_id,
                    error=f"Failure record not found: {failure_id}"
                )

            new_trace_id = f"replay-{failure_id[:8]}-{uuid.uuid4()}"

            target_repo = repo or failure.metadata.get("repo") or DEFAULT_REPLAY_REPO

            try:
                from rq import Queue
                from rq.serializers import JSONSerializer

                try:
                    from common.config.settings import settings
                    redis_url = getattr(settings, "redis_url", None)
                except (ImportError, AttributeError):
                    redis_url = None

                if not redis_url:
                    import os
                    redis_url = os.environ.get("REDIS_URL")

                if not redis_url or redis is None:
                    return ReplayResult(
                        success=False,
                        failure_id=failure_id,
                        error="Redis URL not configured for replay"
                    )

                redis_client_rq = redis.from_url(redis_url, decode_responses=False)

                q = Queue(
                    "orchestrator",
                    connection=redis_client_rq,
                    serializer=JSONSerializer()
                )

                job = q.enqueue(
                    "redis_queue.worker.run_orchestrator_task",
                    new_trace_id,
                    failure.goal,
                    target_repo,
                    job_timeout=600,
                    result_ttl=86400,
                    failure_ttl=3600
                )

                logger.info(f"[FailureRecorder] Replayed failure: {failure_id}", extra={
                    "operation": "replay_failure",
                    "failure_id": failure_id,
                    "new_trace_id": new_trace_id,
                    "job_id": job.id,
                    "original_trace_id": failure.trace_id,
                    "goal": failure.goal[:50]
                })

                return ReplayResult(
                    success=True,
                    failure_id=failure_id,
                    new_trace_id=new_trace_id,
                    job_id=job.id
                )

            except ImportError as e:
                logger.warning(f"[FailureRecorder] RQ not available for replay: {e}")
                return ReplayResult(
                    success=False,
                    failure_id=failure_id,
                    error=f"RQ not available: {e}"
                )

        except Exception as e:
            logger.error(f"[FailureRecorder] Failed to replay failure: {e}", extra={
                "operation": "replay_failure",
                "failure_id": failure_id,
                "error": str(e)
            })
            return ReplayResult(
                success=False,
                failure_id=failure_id,
                error=str(e)
            )


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


def init_failure_recorder_from_env() -> FailureRecorder:
    """
    Initialize failure recorder from environment variables

    This is a shared utility function that can be used by both
    the orchestrator and API routes to avoid code duplication.

    Returns:
        FailureRecorder instance configured from REDIS_URL env var
    """
    import os
    try:
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis is not None:
            redis_client = redis.from_url(redis_url)
            return get_failure_recorder(redis_client=redis_client, enabled=True)
        return get_failure_recorder(redis_client=None, enabled=False)
    except Exception as e:
        logger.warning(f"Failed to initialize failure recorder: {e}")
        return get_failure_recorder(redis_client=None, enabled=False)
