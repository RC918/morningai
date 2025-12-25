"""
PR Deduplication (Memory v2 Short-term Memory) for Publisher Node

Blueprint Alignment:
- Memory v2 (Layer 1 - Short-term): Tracks recent PR creations
- Flow Controller v3: Called before PR creation in Publisher Node
- Safety Governor v2: Prevents duplicate/similar PRs
- Telemetry v2: Structured logging for dedup decisions (可預測性 guarantee)

Purpose:
Before creating a PR, check if a similar PR was recently created.
This prevents the Orchestrator from creating duplicate PRs for:
1. Same changeset (exact duplicate)
2. Similar goal/task (semantic duplicate)
3. Same file paths (path-based duplicate)

Feature Flags:
- ENABLE_PR_DEDUPLICATION: Master switch (default: True)
- PR_DEDUP_WINDOW_SECONDS: Time window for dedup check (default: 3600 = 1 hour)
- PR_DEDUP_SIMILARITY_THRESHOLD: Similarity threshold (default: 0.8)
- PR_DEDUP_DRY_RUN: Log-only mode for testing (default: True)
- PR_DEDUP_LEASE_TTL_SECONDS: Atomic lease TTL for race condition prevention (default: 300 = 5 min)

Issue: Memory v2 Short-term Deduplication (垃圾PR Prevention)
Fix: Atomic SETNX reservation to prevent race condition (Issue #2910)
"""

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional  # Any used for redis_client type hint

logger = logging.getLogger(__name__)

# Fail-open monitoring constants (Issue #2919)
FAIL_OPEN_METRIC_NAME = "pr_lease.fail_open"
# Default values - actual values read from settings (Issue #2933)
DEFAULT_FAIL_OPEN_ALERT_THRESHOLD = 5  # Alert if >5 fail-open events in 5 minutes
DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES = 5

# Default configuration
DEFAULT_DEDUP_WINDOW_SECONDS = 3600  # 1 hour
DEFAULT_SIMILARITY_THRESHOLD = 0.8
DEFAULT_DEDUP_MAX_RECORDS = 100  # Issue #2872: Limit records fetched for performance
DEFAULT_LEASE_TTL_SECONDS = 300  # 5 minutes - lease for atomic reservation
REDIS_KEY_PREFIX = "orchestrator:pr_dedup"
REDIS_LEASE_PREFIX = "orchestrator:pr_lease"


@dataclass
class PRRecord:
    """Record of a PR creation for deduplication"""
    trace_id: str
    goal: str
    changeset_hash: str
    file_paths: List[str]
    pr_url: Optional[str]
    pr_number: Optional[int]
    created_at: float
    repo: str
    branch: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "goal": self.goal,
            "changeset_hash": self.changeset_hash,
            "file_paths": self.file_paths,
            "pr_url": self.pr_url,
            "pr_number": self.pr_number,
            "created_at": self.created_at,
            "repo": self.repo,
            "branch": self.branch
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PRRecord":
        return cls(
            trace_id=data.get("trace_id", ""),
            goal=data.get("goal", ""),
            changeset_hash=data.get("changeset_hash", ""),
            file_paths=data.get("file_paths", []),
            pr_url=data.get("pr_url"),
            pr_number=data.get("pr_number"),
            created_at=data.get("created_at", 0),
            repo=data.get("repo", ""),
            branch=data.get("branch", "")
        )


@dataclass
class DeduplicationResult:
    """Result of PR deduplication check"""
    is_duplicate: bool
    should_create_pr: bool
    duplicate_type: Optional[str] = None  # "exact", "semantic", "path"
    matching_pr: Optional[PRRecord] = None
    similarity_score: float = 0.0
    reasoning: str = ""
    dry_run: bool = False


def _get_redis_client(redis_url: Optional[str] = None):
    """
    Get Redis client for deduplication storage.

    Args:
        redis_url: Optional Redis URL override

    Returns:
        Redis client instance or None if unavailable
    """
    try:
        import redis

        try:
            from common.config.settings import settings
            url = redis_url or getattr(settings, 'redis_url', None)
        except ImportError:
            url = redis_url

        if url:
            return redis.Redis.from_url(url, decode_responses=True)
        else:
            logger.warning("[PRDedup] No Redis URL configured")
            return None
    except Exception as e:
        logger.warning(f"[PRDedup] Failed to connect to Redis: {e}")
        return None


def _get_dedup_key(repo: str) -> str:
    """Get Redis key for PR deduplication records"""
    try:
        from common.config.settings import settings
        prefix = getattr(settings, 'redis_key_prefix', '') or ''
        prefix = prefix.rstrip(':')
    except ImportError:
        prefix = ''

    base_key = f"{REDIS_KEY_PREFIX}:{repo}"
    return f"{prefix}:{base_key}" if prefix else base_key


def _normalize_goal(goal: str) -> str:
    """
    Normalize a goal string for comparison.

    Args:
        goal: Original goal string

    Returns:
        Normalized goal string
    """
    # Lowercase
    normalized = goal.lower()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    # Remove common prefixes
    prefixes = ['fix:', 'feat:', 'docs:', 'refactor:', 'chore:', 'test:']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    return normalized


def _calculate_goal_similarity(goal1: str, goal2: str) -> float:
    """
    Calculate similarity between two goals using Jaccard similarity.

    Args:
        goal1: First goal string
        goal2: Second goal string

    Returns:
        Similarity score between 0 and 1
    """
    # Normalize goals
    norm1 = _normalize_goal(goal1)
    norm2 = _normalize_goal(goal2)

    # Tokenize
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())

    if not tokens1 or not tokens2:
        return 0.0

    # Jaccard similarity
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def _calculate_path_similarity(paths1: List[str], paths2: List[str]) -> float:
    """
    Calculate similarity between two sets of file paths.

    Args:
        paths1: First list of file paths
        paths2: Second list of file paths

    Returns:
        Similarity score between 0 and 1
    """
    if not paths1 or not paths2:
        return 0.0

    set1 = set(paths1)
    set2 = set(paths2)

    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union)


def record_pr_creation(
    trace_id: str,
    goal: str,
    changeset_hash: str,
    file_paths: List[str],
    repo: str,
    branch: str,
    pr_url: Optional[str] = None,
    pr_number: Optional[int] = None,
    redis_url: Optional[str] = None
) -> bool:
    """
    Record a PR creation for future deduplication checks.

    Blueprint Alignment:
    - Memory v2 (Layer 1): Stores short-term PR creation records
    - Telemetry v2: Enables traceability of PR creation decisions

    Args:
        trace_id: Unique trace ID
        goal: Task goal/description
        changeset_hash: Hash of the changeset
        file_paths: List of files in the changeset
        repo: Repository (owner/repo format)
        branch: Branch name
        pr_url: Optional PR URL
        pr_number: Optional PR number
        redis_url: Optional Redis URL override

    Returns:
        True if recorded successfully, False otherwise
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        record = PRRecord(
            trace_id=trace_id,
            goal=goal,
            changeset_hash=changeset_hash,
            file_paths=file_paths,
            pr_url=pr_url,
            pr_number=pr_number,
            created_at=time.time(),
            repo=repo,
            branch=branch
        )

        key = _get_dedup_key(repo)

        # Store as sorted set with timestamp as score
        r.zadd(key, {json.dumps(record.to_dict()): record.created_at})

        # Set TTL on the key (2x the dedup window for safety)
        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        r.expire(key, window * 2)

        logger.info("[PRDedup] Recorded PR creation", extra={
            "operation": "pr_dedup_record",
            "trace_id": trace_id,
            "repo": repo,
            "changeset_hash": changeset_hash,
            "file_count": len(file_paths)
        })

        return True

    except Exception as e:
        logger.warning(f"[PRDedup] Failed to record PR creation: {e}", extra={
            "operation": "pr_dedup_record_error",
            "trace_id": trace_id,
            "error": str(e)
        })
        return False


def check_pr_deduplication(
    goal: str,
    changeset_hash: str,
    file_paths: List[str],
    repo: str,
    trace_id: Optional[str] = None,
    redis_url: Optional[str] = None
) -> DeduplicationResult:
    """
    Check if a similar PR was recently created.

    Blueprint Alignment:
    - Memory v2 (Layer 1): Queries short-term PR creation records
    - Flow Controller v3: Called before PR creation in Publisher Node
    - Safety Governor v2: Part of the governance layer

    Args:
        goal: Task goal/description
        changeset_hash: Hash of the changeset
        file_paths: List of files in the changeset
        repo: Repository (owner/repo format)
        trace_id: Optional trace ID for logging
        redis_url: Optional Redis URL override

    Returns:
        DeduplicationResult with decision
    """
    # Check if deduplication is enabled
    try:
        from common.config.settings import settings
        enabled = getattr(settings, 'enable_pr_deduplication', True)
        dry_run = getattr(settings, 'pr_dedup_dry_run', True)
        window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
        window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        threshold = getattr(settings, 'pr_dedup_similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD)
        threshold = threshold or DEFAULT_SIMILARITY_THRESHOLD
    except ImportError:
        enabled = True
        dry_run = True
        window = DEFAULT_DEDUP_WINDOW_SECONDS
        threshold = DEFAULT_SIMILARITY_THRESHOLD

    if not enabled:
        logger.info("[PRDedup] Feature disabled, allowing PR creation", extra={
            "operation": "pr_dedup",
            "trace_id": trace_id,
            "enabled": False
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning="PR deduplication disabled"
        )

    try:
        r = _get_redis_client(redis_url)
        if not r:
            logger.warning("[PRDedup] Redis unavailable, allowing PR creation", extra={
                "operation": "pr_dedup",
                "trace_id": trace_id
            })
            return DeduplicationResult(
                is_duplicate=False,
                should_create_pr=True,
                reasoning="Redis unavailable, skipping dedup check"
            )

        key = _get_dedup_key(repo)

        # Get recent PR records within the time window
        # Issue #2872: Add LIMIT to zrangebyscore for performance
        min_time = time.time() - window
        try:
            from common.config.settings import settings
            max_records = getattr(settings, 'pr_dedup_max_records', DEFAULT_DEDUP_MAX_RECORDS)
            max_records = max_records or DEFAULT_DEDUP_MAX_RECORDS
        except ImportError:
            max_records = DEFAULT_DEDUP_MAX_RECORDS

        # Use start=0, num=max_records to limit results (most recent first via zrevrangebyscore)
        # This prevents fetching unbounded records which could cause memory issues.
        #
        # TRADE-OFF NOTE (Issue #2872):
        # - By limiting to max_records (default: 100), we prioritize the most recent PRs
        # - In high-volume scenarios where more than max_records PRs exist in the window,
        #   older duplicates may be missed (false negatives)
        # - This is an acceptable trade-off for performance vs. completeness
        # - The order of results does NOT affect correctness since we check for ANY match
        # - Adjust PR_DEDUP_MAX_RECORDS if your repo has very high PR volume
        records_json = r.zrevrangebyscore(key, '+inf', min_time, start=0, num=max_records)

        if not records_json:
            logger.info("[PRDedup] No recent PRs found, allowing creation", extra={
                "operation": "pr_dedup",
                "trace_id": trace_id,
                "repo": repo
            })
            return DeduplicationResult(
                is_duplicate=False,
                should_create_pr=True,
                reasoning="No recent PRs in dedup window"
            )

        # Check for duplicates
        for record_json in records_json:
            try:
                record = PRRecord.from_dict(json.loads(record_json))
            except (json.JSONDecodeError, KeyError):
                continue

            # Check 1: Exact changeset match
            if record.changeset_hash == changeset_hash:
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,  # Allow in dry-run mode
                    duplicate_type="exact",
                    matching_pr=record,
                    similarity_score=1.0,
                    reasoning=f"Exact changeset match with PR #{record.pr_number} (trace: {record.trace_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result

            # Check 2: Semantic similarity (goal)
            goal_similarity = _calculate_goal_similarity(goal, record.goal)
            if goal_similarity >= threshold:
                pr_num = record.pr_number
                tr_id = record.trace_id
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,
                    duplicate_type="semantic",
                    matching_pr=record,
                    similarity_score=goal_similarity,
                    reasoning=f"Semantic match ({goal_similarity:.2f}) with PR #{pr_num} (trace: {tr_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result

            # Check 3: Path similarity
            path_similarity = _calculate_path_similarity(file_paths, record.file_paths)
            if path_similarity >= threshold:
                pr_num = record.pr_number
                tr_id = record.trace_id
                result = DeduplicationResult(
                    is_duplicate=True,
                    should_create_pr=dry_run,
                    duplicate_type="path",
                    matching_pr=record,
                    similarity_score=path_similarity,
                    reasoning=f"Path match ({path_similarity:.2f}) with PR #{pr_num} (trace: {tr_id})",
                    dry_run=dry_run
                )
                _log_dedup_result(result, trace_id)
                return result

        # No duplicates found
        logger.info("[PRDedup] No duplicates found, allowing creation", extra={
            "operation": "pr_dedup",
            "trace_id": trace_id,
            "repo": repo,
            "records_checked": len(records_json)
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning=f"No duplicates found in {len(records_json)} recent PRs"
        )

    except Exception as e:
        logger.warning(f"[PRDedup] Error during dedup check: {e}", extra={
            "operation": "pr_dedup_error",
            "trace_id": trace_id,
            "error": str(e)
        })
        return DeduplicationResult(
            is_duplicate=False,
            should_create_pr=True,
            reasoning=f"Error during dedup check: {e}"
        )


def _log_dedup_result(result: DeduplicationResult, trace_id: Optional[str]) -> None:
    """Log deduplication result"""
    log_extra = {
        "operation": "pr_dedup",
        "trace_id": trace_id,
        "is_duplicate": result.is_duplicate,
        "duplicate_type": result.duplicate_type,
        "similarity_score": result.similarity_score,
        "should_create_pr": result.should_create_pr,
        "dry_run": result.dry_run
    }

    if result.matching_pr:
        log_extra["matching_trace_id"] = result.matching_pr.trace_id
        log_extra["matching_pr_number"] = result.matching_pr.pr_number

    if result.dry_run:
        logger.warning(
            f"[PRDedup][DRY-RUN] Would block duplicate PR: {result.reasoning}",
            extra=log_extra
        )
    else:
        logger.warning(
            f"[PRDedup] Blocking duplicate PR: {result.reasoning}",
            extra=log_extra
        )


def cleanup_old_records(
    repo: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Clean up old PR records outside the dedup window.

    Args:
        repo: Repository (owner/repo format)
        redis_url: Optional Redis URL override

    Returns:
        Number of records removed
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0

        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        key = _get_dedup_key(repo)
        min_time = time.time() - window

        # Remove records older than the window
        removed = r.zremrangebyscore(key, 0, min_time)

        if removed:
            logger.info(f"[PRDedup] Cleaned up {removed} old records", extra={
                "operation": "pr_dedup_cleanup",
                "repo": repo,
                "removed_count": removed
            })

        return removed

    except Exception as e:
        logger.warning(f"[PRDedup] Failed to cleanup old records: {e}")
        return 0


def get_recent_pr_count(
    repo: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Get count of recent PRs in the dedup window.

    Args:
        repo: Repository (owner/repo format)
        redis_url: Optional Redis URL override

    Returns:
        Number of recent PRs
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0

        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        key = _get_dedup_key(repo)
        min_time = time.time() - window

        return r.zcount(key, min_time, '+inf')

    except Exception:
        return 0


def generate_dedup_key(
    repo: str,
    doc_file_path: str,
    source_pr_number: Optional[int] = None,
    event_action: Optional[str] = None
) -> str:
    """
    Generate a deterministic deduplication key.

    Blueprint Alignment:
    - Memory v2 (Layer 1): Deterministic key for short-term dedup
    - 可預測性 (Deterministic): Same input always produces same key

    Args:
        repo: Repository (owner/repo format)
        doc_file_path: Path to the generated doc file
        source_pr_number: Optional source PR number that triggered this
        event_action: Optional event action (opened, merged, etc.)

    Returns:
        Deterministic dedup key string
    """
    components = [repo, doc_file_path]
    if source_pr_number is not None:
        components.append(str(source_pr_number))
    if event_action:
        components.append(event_action)

    key_string = ":".join(components)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

    return f"{repo}:{key_hash}"


def _get_lease_key(dedup_key: str) -> str:
    """Get Redis key for PR creation lease"""
    try:
        from common.config.settings import settings
        prefix = getattr(settings, 'redis_key_prefix', '') or ''
        prefix = prefix.rstrip(':')
    except ImportError:
        prefix = ''

    base_key = f"{REDIS_LEASE_PREFIX}:{dedup_key}"
    return f"{prefix}:{base_key}" if prefix else base_key


@dataclass
class LeaseResult:
    """Result of attempting to acquire a PR creation lease"""
    acquired: bool
    lease_key: str
    holder: Optional[str] = None
    ttl_remaining: Optional[int] = None
    existing_pr_url: Optional[str] = None
    existing_pr_number: Optional[int] = None
    reason: str = ""


def _record_fail_open_event(
    trace_id: str,
    dedup_key: str,
    reason: str,
    error: Optional[str] = None,
    redis_client: Optional[Any] = None
) -> None:
    """
    Record a fail-open event for monitoring and alerting (Issue #2919).

    Blueprint Alignment:
    - Telemetry v2: Full execution trace reconstruction
    - Safety Governor v2: Monitor degraded safety states

    This function:
    1. Adds a Sentry breadcrumb for debugging
    2. Increments a metrics counter for Prometheus/Grafana
    3. Logs structured warning for observability

    Args:
        trace_id: Trace ID for correlation
        dedup_key: The dedup key that triggered fail-open
        reason: Reason for fail-open (e.g., "redis_unavailable", "connection_error")
        error: Optional error message
        redis_client: Optional Redis client for metrics (if available)
    """
    # 1. Add Sentry breadcrumb for debugging
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            category="pr_dedup",
            message=f"PR lease fail-open: {reason}",
            level="warning",
            data={
                "trace_id": trace_id,
                "dedup_key": dedup_key,
                "reason": reason,
                "error": error,
                "fail_open": True,
            }
        )
    except ImportError:
        pass  # Sentry not available
    except Exception as e:
        logger.debug(f"[PRDedup] Failed to add Sentry breadcrumb: {e}")

    # 2. Increment metrics counter (if Redis available)
    # Use INCR + EXPIRE pattern for robustness (ensures TTL is always refreshed)
    if redis_client:
        try:
            from datetime import datetime
            minute_str = datetime.utcnow().strftime("%Y%m%d%H%M")
            metric_key = f"metrics:orchestrator:{FAIL_OPEN_METRIC_NAME}:{minute_str}"

            with redis_client.pipeline(transaction=True) as pipe:
                pipe.incr(metric_key)  # INCR creates key with value 1 if not exists
                pipe.expire(metric_key, 7200)  # Always refresh TTL to 2 hours
                pipe.execute()

            logger.debug(f"[PRDedup] Recorded fail-open metric: {metric_key}")
        except Exception as e:
            logger.debug(f"[PRDedup] Failed to record fail-open metric: {e}")

    # 3. Log structured warning for observability
    logger.warning(f"[PRDedup] FAIL-OPEN: {reason}", extra={
        "operation": "pr_lease_fail_open",
        "trace_id": trace_id,
        "dedup_key": dedup_key,
        "reason": reason,
        "error": error,
        "alert_type": "redis_fail_open",
        "fail_open": True,
    })


def get_fail_open_count(
    window_minutes: Optional[int] = None,
    redis_url: Optional[str] = None
) -> int:
    """
    Get the count of fail-open events in the specified time window.

    Used for alerting when fail-open rate exceeds threshold.

    Args:
        window_minutes: Time window in minutes (default: from settings or 5)
        redis_url: Optional Redis URL override

    Returns:
        Count of fail-open events in the window
    """
    # Issue #2933: Read from settings if not explicitly provided
    if window_minutes is None:
        try:
            from common.config.settings import settings
            window_minutes = getattr(
                settings, 'fail_open_alert_window_minutes',
                DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES
            )
        except ImportError:
            window_minutes = DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES

    try:
        r = _get_redis_client(redis_url)
        if not r:
            return 0

        from datetime import datetime, timedelta
        now = datetime.utcnow()
        total = 0

        for i in range(window_minutes):
            timestamp = now - timedelta(minutes=i)
            minute_str = timestamp.strftime("%Y%m%d%H%M")
            metric_key = f"metrics:orchestrator:{FAIL_OPEN_METRIC_NAME}:{minute_str}"
            value = r.get(metric_key)
            if value:
                total += int(value)

        return total
    except Exception as e:
        logger.debug(f"[PRDedup] Failed to get fail-open count: {e}")
        return 0


def check_fail_open_alert_threshold(
    redis_url: Optional[str] = None
) -> bool:
    """
    Check if fail-open events exceed the alert threshold.

    Issue #2933: Thresholds are now configurable via settings.

    Args:
        redis_url: Optional Redis URL override

    Returns:
        True if threshold exceeded, False otherwise
    """
    # Issue #2933: Read thresholds from settings
    try:
        from common.config.settings import settings
        threshold = getattr(
            settings, 'fail_open_alert_threshold',
            DEFAULT_FAIL_OPEN_ALERT_THRESHOLD
        )
        window_minutes = getattr(
            settings, 'fail_open_alert_window_minutes',
            DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES
        )
    except ImportError:
        threshold = DEFAULT_FAIL_OPEN_ALERT_THRESHOLD
        window_minutes = DEFAULT_FAIL_OPEN_ALERT_WINDOW_MINUTES

    count = get_fail_open_count(window_minutes=window_minutes, redis_url=redis_url)
    exceeded = count > threshold

    if exceeded:
        logger.error(
            f"[PRDedup] ALERT: Fail-open threshold exceeded! "
            f"{count} events in {window_minutes} minutes "
            f"(threshold: {threshold})",
            extra={
                "operation": "pr_lease_fail_open_alert",
                "alert_type": "fail_open_threshold_exceeded",
                "count": count,
                "threshold": threshold,
                "window_minutes": window_minutes,
            }
        )

        # Send Sentry alert
        try:
            import sentry_sdk
            sentry_sdk.capture_message(
                f"[PRDedup] Fail-open threshold exceeded: {count} events in {window_minutes} min",
                level="error",
                tags={
                    "alert_type": "fail_open_threshold_exceeded",
                    "component": "pr_deduplication",
                    "count": str(count),
                    "threshold": str(threshold),
                }
            )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[PRDedup] Failed to send Sentry alert: {e}")

    return exceeded


def acquire_pr_lease(
    dedup_key: str,
    worker_id: str,
    trace_id: str,
    redis_url: Optional[str] = None
) -> LeaseResult:
    """
    Attempt to acquire an atomic lease for PR creation.

    Blueprint Alignment:
    - Memory v2 (Layer 1): Atomic short-term reservation
    - Safety Governor v2: Prevents race condition duplicates
    - Telemetry v2: Structured logging for lease decisions

    This uses Redis SETNX (SET if Not eXists) for atomic reservation.
    If another worker already holds the lease, this will fail fast.

    Args:
        dedup_key: Deterministic dedup key from generate_dedup_key()
        worker_id: ID of the worker attempting to acquire lease
        trace_id: Trace ID for logging
        redis_url: Optional Redis URL override

    Returns:
        LeaseResult with acquisition status
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            # Issue #2919: Record fail-open event for monitoring
            _record_fail_open_event(
                trace_id=trace_id,
                dedup_key=dedup_key,
                reason="redis_unavailable",
                error=None,
                redis_client=None  # Redis not available
            )
            return LeaseResult(
                acquired=True,
                lease_key=dedup_key,
                reason="Redis unavailable, fail-open"
            )

        try:
            from common.config.settings import settings
            ttl = getattr(settings, 'pr_dedup_lease_ttl_seconds', DEFAULT_LEASE_TTL_SECONDS)
            ttl = ttl or DEFAULT_LEASE_TTL_SECONDS
        except ImportError:
            ttl = DEFAULT_LEASE_TTL_SECONDS

        lease_key = _get_lease_key(dedup_key)
        lease_value = json.dumps({
            "worker_id": worker_id,
            "trace_id": trace_id,
            "acquired_at": time.time(),
            "status": "in_progress"
        })

        acquired = r.set(lease_key, lease_value, nx=True, ex=ttl)

        if acquired:
            logger.info("[PRDedup] Lease acquired", extra={
                "operation": "pr_lease_acquire",
                "trace_id": trace_id,
                "dedup_key": dedup_key,
                "worker_id": worker_id,
                "ttl_seconds": ttl,
                "result": "acquired"
            })
            return LeaseResult(
                acquired=True,
                lease_key=lease_key,
                holder=worker_id,
                ttl_remaining=ttl,
                reason="Lease acquired successfully"
            )
        else:
            existing = r.get(lease_key)
            existing_data = json.loads(existing) if existing else {}
            existing_holder = existing_data.get("worker_id", "unknown")
            existing_trace = existing_data.get("trace_id", "unknown")
            existing_status = existing_data.get("status", "unknown")
            existing_pr_url = existing_data.get("pr_url")
            existing_pr_number = existing_data.get("pr_number")
            ttl_remaining = r.ttl(lease_key)

            logger.warning("[PRDedup] Lease already held by another worker", extra={
                "operation": "pr_lease_acquire",
                "trace_id": trace_id,
                "dedup_key": dedup_key,
                "worker_id": worker_id,
                "existing_holder": existing_holder,
                "existing_trace": existing_trace,
                "existing_status": existing_status,
                "ttl_remaining": ttl_remaining,
                "result": "already_held"
            })
            return LeaseResult(
                acquired=False,
                lease_key=lease_key,
                holder=existing_holder,
                ttl_remaining=ttl_remaining,
                existing_pr_url=existing_pr_url,
                existing_pr_number=existing_pr_number,
                reason=f"Lease held by {existing_holder} (trace: {existing_trace}, status: {existing_status})"
            )

    except Exception as e:
        # Issue #2919: Record fail-open event for monitoring
        # Try to get Redis client for metrics (may fail if Redis is the issue)
        try:
            metrics_redis = _get_redis_client(redis_url)
        except Exception:
            metrics_redis = None

        _record_fail_open_event(
            trace_id=trace_id,
            dedup_key=dedup_key,
            reason="connection_error",
            error=str(e),
            redis_client=metrics_redis
        )
        return LeaseResult(
            acquired=True,
            lease_key=dedup_key,
            reason=f"Error acquiring lease: {e}, fail-open"
        )


def release_pr_lease(
    dedup_key: str,
    trace_id: str,
    redis_url: Optional[str] = None
) -> bool:
    """
    Release a PR creation lease (used when PR creation fails).

    Args:
        dedup_key: Deterministic dedup key
        trace_id: Trace ID for logging
        redis_url: Optional Redis URL override

    Returns:
        True if released successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        lease_key = _get_lease_key(dedup_key)
        deleted = r.delete(lease_key)

        logger.info("[PRDedup] Lease released", extra={
            "operation": "pr_lease_release",
            "trace_id": trace_id,
            "dedup_key": dedup_key,
            "deleted": bool(deleted)
        })
        return bool(deleted)

    except Exception as e:
        logger.warning(f"[PRDedup] Error releasing lease: {e}", extra={
            "operation": "pr_lease_release_error",
            "trace_id": trace_id,
            "dedup_key": dedup_key,
            "error": str(e)
        })
        return False


def complete_pr_lease(
    dedup_key: str,
    trace_id: str,
    pr_url: str,
    pr_number: int,
    redis_url: Optional[str] = None
) -> bool:
    """
    Mark a PR creation lease as complete (PR successfully created).

    This updates the lease to "done" status with PR info and extends TTL
    to the full dedup window, preventing duplicate PRs for the same content.

    Args:
        dedup_key: Deterministic dedup key
        trace_id: Trace ID for logging
        pr_url: URL of the created PR
        pr_number: Number of the created PR
        redis_url: Optional Redis URL override

    Returns:
        True if completed successfully
    """
    try:
        r = _get_redis_client(redis_url)
        if not r:
            return False

        try:
            from common.config.settings import settings
            window = getattr(settings, 'pr_dedup_window_seconds', DEFAULT_DEDUP_WINDOW_SECONDS)
            window = window or DEFAULT_DEDUP_WINDOW_SECONDS
        except ImportError:
            window = DEFAULT_DEDUP_WINDOW_SECONDS

        lease_key = _get_lease_key(dedup_key)

        existing = r.get(lease_key)
        existing_data = json.loads(existing) if existing else {}

        completed_value = json.dumps({
            "worker_id": existing_data.get("worker_id", "unknown"),
            "trace_id": trace_id,
            "acquired_at": existing_data.get("acquired_at", time.time()),
            "completed_at": time.time(),
            "status": "done",
            "pr_url": pr_url,
            "pr_number": pr_number
        })

        r.set(lease_key, completed_value, ex=window)

        logger.info("[PRDedup] Lease completed with PR info", extra={
            "operation": "pr_lease_complete",
            "trace_id": trace_id,
            "dedup_key": dedup_key,
            "pr_url": pr_url,
            "pr_number": pr_number,
            "ttl_seconds": window
        })
        return True

    except Exception as e:
        logger.warning(f"[PRDedup] Error completing lease: {e}", extra={
            "operation": "pr_lease_complete_error",
            "trace_id": trace_id,
            "dedup_key": dedup_key,
            "error": str(e)
        })
        return False


def generate_deterministic_branch(
    repo: str,
    doc_file_path: str,
    source_pr_number: Optional[int] = None
) -> str:
    """
    Generate a deterministic branch name for PR creation.

    Blueprint Alignment:
    - 可預測性 (Deterministic): Same input always produces same branch name
    - This prevents multiple branches for the same content

    Args:
        repo: Repository (owner/repo format)
        doc_file_path: Path to the generated doc file
        source_pr_number: Optional source PR number

    Returns:
        Deterministic branch name
    """
    components = [repo, doc_file_path]
    if source_pr_number is not None:
        components.append(str(source_pr_number))

    key_string = ":".join(components)
    branch_hash = hashlib.sha256(key_string.encode()).hexdigest()[:12]

    path_slug = doc_file_path.split("/")[-1].replace(".md", "")[:20]
    path_slug = re.sub(r'[^a-zA-Z0-9-]', '-', path_slug).lower()

    return f"orchestrator/docs-{path_slug}-{branch_hash}"
