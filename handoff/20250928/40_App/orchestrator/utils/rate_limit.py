"""Rate limiting utilities for Orchestrator PR creation

Issue #2943: North Star alignment improvements:
- Atomic rate limiting using Redis Lua script
- Telemetry integration for structured event logging
- Auto-recovery mechanism with monitoring/alerting
"""
import json
import logging
import redis
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Atomic Rate Limiting with Redis Lua Script (Issue #2943)
# =============================================================================

# Lua script for atomic check-and-increment rate limiting
# This ensures no race condition can cause the limit to be exceeded
# Returns: {allowed (0 or 1), current_count}
RATE_LIMIT_LUA_SCRIPT = """
local key = KEYS[1]
local max_limit = tonumber(ARGV[1])
local expiry_seconds = tonumber(ARGV[2])

-- Get current count (0 if key doesn't exist)
local current = tonumber(redis.call('GET', key) or '0')

-- Check if already at or over limit
if current >= max_limit then
    return {0, current}  -- blocked
end

-- Increment and set expiry atomically
local new_count = redis.call('INCR', key)
redis.call('EXPIRE', key, expiry_seconds)

return {1, new_count}  -- allowed
"""


@dataclass
class RateLimitResult:
    """Result of atomic rate limit check (Issue #2943)"""
    allowed: bool
    current_count: int
    key: str
    max_limit: int
    decision: str  # 'allowed' or 'blocked'
    trace_id: Optional[str] = None
    context_id: Optional[str] = None  # pr_id, query_type, source, etc.


def _emit_rate_limit_telemetry(
    result: RateLimitResult,
    operation: str,
    extra_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emit structured telemetry event for rate limit decision (Issue #2943).

    Args:
        result: The rate limit result
        operation: Operation name (e.g., 'pr_rate_limit', 'deepwiki_rate_limit')
        extra_context: Additional context to include in telemetry
    """
    telemetry_data = {
        "operation": operation,
        "key": result.key,
        "current_count": result.current_count,
        "max_limit": result.max_limit,
        "decision": result.decision,
        "trace_id": result.trace_id,
        "context_id": result.context_id,
    }
    if extra_context:
        telemetry_data.update(extra_context)

    if result.allowed:
        logger.debug(
            f"[RateLimit] {operation}: allowed ({result.current_count}/{result.max_limit})",
            extra=telemetry_data
        )
    else:
        logger.warning(
            f"[RateLimit] {operation}: blocked ({result.current_count}/{result.max_limit})",
            extra=telemetry_data
        )


def _atomic_rate_limit_check(
    r: redis.Redis,
    key: str,
    max_limit: int,
    expiry_seconds: int,
    trace_id: Optional[str] = None,
    context_id: Optional[str] = None,
    operation: str = "rate_limit"
) -> RateLimitResult:
    """
    Perform atomic rate limit check using Redis Lua script (Issue #2943).

    This function provides true atomicity - no race condition can cause
    the limit to be exceeded, even under high concurrency.

    Args:
        r: Redis client instance
        key: Redis key for the rate limit counter
        max_limit: Maximum allowed count
        expiry_seconds: TTL for the key
        trace_id: Optional trace ID for telemetry
        context_id: Optional context ID (pr_id, query_type, etc.)
        operation: Operation name for telemetry

    Returns:
        RateLimitResult with allowed status and details
    """
    # Execute Lua script atomically
    result = r.eval(RATE_LIMIT_LUA_SCRIPT, 1, key, max_limit, expiry_seconds)

    allowed = bool(result[0])
    current_count = int(result[1])
    decision = "allowed" if allowed else "blocked"

    rate_limit_result = RateLimitResult(
        allowed=allowed,
        current_count=current_count,
        key=key,
        max_limit=max_limit,
        decision=decision,
        trace_id=trace_id,
        context_id=context_id,
    )

    # Emit telemetry
    _emit_rate_limit_telemetry(rate_limit_result, operation)

    return rate_limit_result


# Auto-recovery: Track consecutive rate limit hits for alerting
RATE_LIMIT_ALERT_THRESHOLD = 10  # Alert after 10 consecutive blocks
RATE_LIMIT_ALERT_KEY_PREFIX = "rate_limit:alert_count"


def _check_and_alert_rate_limit_pattern(
    r: redis.Redis,
    key: str,
    was_blocked: bool,
    operation: str
) -> None:
    """
    Monitor rate limit patterns and emit alerts (Issue #2943 Auto-Recovery).

    Tracks consecutive rate limit blocks and emits warning when threshold
    is exceeded, indicating potential need for intervention.

    Args:
        r: Redis client instance
        key: Original rate limit key
        was_blocked: Whether the request was blocked
        operation: Operation name for logging
    """
    alert_key = f"{RATE_LIMIT_ALERT_KEY_PREFIX}:{key}"

    if was_blocked:
        # Increment consecutive block counter
        consecutive_blocks = r.incr(alert_key)
        r.expire(alert_key, 3600)  # Reset after 1 hour of no blocks

        if consecutive_blocks >= RATE_LIMIT_ALERT_THRESHOLD:
            logger.warning(
                f"[RateLimit:Alert] {operation}: {consecutive_blocks} consecutive blocks detected",
                extra={
                    "operation": f"{operation}_alert",
                    "alert_type": "consecutive_blocks",
                    "consecutive_blocks": consecutive_blocks,
                    "threshold": RATE_LIMIT_ALERT_THRESHOLD,
                    "key": key,
                    "recommendation": "Consider increasing rate limit or investigating traffic pattern",
                }
            )
    else:
        # Reset consecutive block counter on successful request
        r.delete(alert_key)


def _get_redis_key_prefix() -> str:
    """
    Get the Redis key prefix from settings, normalized to not have trailing colon.

    Returns empty string if settings import fails (legacy behavior fallback).
    Normalizes prefix to ensure no double-colon issues (e.g., "stg:" -> "stg").
    """
    try:
        from common.config.settings import settings
        prefix = getattr(settings, 'redis_key_prefix', None) or ""
        # Normalize: remove trailing colon if present (we add it in key construction)
        return prefix.rstrip(":")
    except ImportError:
        return ""


def _get_pr_updated_keys(repo: str, pr_number: int) -> Tuple[str, str]:
    """
    Get both prefixed and legacy PR key base names.

    Returns:
        Tuple of (prefixed_pr_key, legacy_pr_key)
        - prefixed_pr_key: Key with REDIS_KEY_PREFIX (e.g., "morningai:pr_updated:owner/repo:123")
        - legacy_pr_key: Key without prefix (e.g., "pr_updated:owner/repo:123")

    The prefixed key is used for new writes; legacy key is checked for backward compatibility
    to avoid breaking in-flight jobs during deployment.
    """
    prefix = _get_redis_key_prefix()
    legacy_pr_key = f"pr_updated:{repo}:{pr_number}"
    if prefix:
        prefixed_pr_key = f"{prefix}:{legacy_pr_key}"
    else:
        prefixed_pr_key = legacy_pr_key
    return prefixed_pr_key, legacy_pr_key


def _get_with_legacy_fallback(r, prefixed_key: str, legacy_key: str) -> Optional[str]:
    """
    Get a value from Redis, checking prefixed key first, then legacy key.

    This helper reduces code duplication for the "prefixed-first, legacy-fallback"
    pattern used throughout the PR_UPDATED debounce functions.

    Args:
        r: Redis client instance
        prefixed_key: The prefixed key to check first
        legacy_key: The legacy key to check as fallback

    Returns:
        The value from Redis, or None if not found in either key
    """
    value = r.get(prefixed_key)
    # Fallback to legacy key if prefixed key is not found and they are different
    if value is None and prefixed_key != legacy_key:
        value = r.get(legacy_key)
    return value


def check_pr_rate_limit(
    trace_id: str,
    max_per_hour: int = 10,
    redis_url: Optional[str] = None
) -> tuple[bool, int]:
    """
    Check if we've created too many PRs recently.

    Issue #2937: Fixed counter leak bug where INCR was called before checking
    the limit, causing the counter to increment even when rate limited.
    Issue #2943: Upgraded to atomic Lua script for true atomicity under concurrency.

    Args:
        trace_id: Unique trace ID for this operation
        max_per_hour: Maximum PRs allowed per hour (default: 10)
        redis_url: Redis connection URL (optional, uses localhost if None)

    Returns:
        Tuple of (allowed: bool, current_count: int)
        - allowed: True if PR creation should proceed, False if rate limited
        - current_count: Current number of PRs created this hour
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_hour = int(time.time() / 3600)
        key = f"orchestrator:pr_count:{current_hour}"

        # Issue #2943: Use atomic Lua script for true atomicity
        # This prevents race conditions where two concurrent requests could both pass
        result = _atomic_rate_limit_check(
            r=r,
            key=key,
            max_limit=max_per_hour,
            expiry_seconds=3600,
            trace_id=trace_id,
            context_id=f"pr_rate_limit:{current_hour}",
            operation="pr_rate_limit"
        )

        # Issue #2943: Auto-recovery monitoring
        _check_and_alert_rate_limit_pattern(r, key, not result.allowed, "pr_rate_limit")

        # Maintain backward-compatible print statements for existing log parsing
        if result.allowed:
            print(f"[Rate Limit] PR count this hour: {result.current_count}/{max_per_hour}")
        else:
            print(f"[Rate Limit] Already created {result.current_count} PRs this hour (max: {max_per_hour})")

        return result.allowed, result.current_count

    except redis.ConnectionError as e:
        print(f"[Rate Limit] Redis unavailable, allowing PR creation: {e}")
        logger.warning(
            "[RateLimit] Redis unavailable, fail-open allowing PR creation",
            extra={
                "operation": "pr_rate_limit_redis_error",
                "error": str(e),
                "trace_id": trace_id,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0
    except Exception as e:
        print(f"[Rate Limit] Unexpected error, allowing PR creation: {e}")
        logger.warning(
            "[RateLimit] Unexpected error, fail-open allowing PR creation",
            extra={
                "operation": "pr_rate_limit_error",
                "error": str(e),
                "trace_id": trace_id,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0


def get_pr_count_last_hour(redis_url: Optional[str] = None) -> int:
    """
    Get the current PR creation count for this hour.

    Args:
        redis_url: Redis connection URL (optional)

    Returns:
        Number of PRs created in the current hour, or 0 if unavailable
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_hour = int(time.time() / 3600)
        key = f"orchestrator:pr_count:{current_hour}"

        count = r.get(key)
        return int(count) if count else 0

    except Exception:
        return 0


def check_deepwiki_rate_limit(
    query_type: str,
    max_per_minute: int = 60,
    redis_url: Optional[str] = None
) -> tuple[bool, int]:
    """
    Check if DeepWiki queries are rate limited.

    Issue #2153: Rate limiting for DeepWiki API calls.
    Issue #2937: Fixed counter leak bug - now uses check-then-increment pattern.
    Issue #2943: Upgraded to atomic Lua script for true atomicity under concurrency.

    Args:
        query_type: Type of query (e.g., 'code_question', 'error_lookup')
        max_per_minute: Maximum queries allowed per minute (default: 60)
        redis_url: Redis connection URL (optional, uses localhost if None)

    Returns:
        Tuple of (allowed: bool, current_count: int)
        - allowed: True if query should proceed, False if rate limited
        - current_count: Current number of queries this minute
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_minute = int(time.time() / 60)
        key = f"deepwiki:query_count:{query_type}:{current_minute}"

        # Issue #2943: Use atomic Lua script for true atomicity
        result = _atomic_rate_limit_check(
            r=r,
            key=key,
            max_limit=max_per_minute,
            expiry_seconds=120,  # Keep for 2 minutes to handle edge cases
            trace_id=None,
            context_id=query_type,
            operation="deepwiki_rate_limit"
        )

        # Issue #2943: Auto-recovery monitoring
        _check_and_alert_rate_limit_pattern(r, key, not result.allowed, "deepwiki_rate_limit")

        return result.allowed, result.current_count

    except redis.ConnectionError as e:
        # Redis unavailable, allow query (graceful degradation)
        logger.warning(
            "[RateLimit] Redis unavailable, fail-open allowing DeepWiki query",
            extra={
                "operation": "deepwiki_rate_limit_redis_error",
                "error": str(e),
                "query_type": query_type,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0
    except Exception as e:
        # Unexpected error, allow query (graceful degradation)
        logger.warning(
            "[RateLimit] Unexpected error, fail-open allowing DeepWiki query",
            extra={
                "operation": "deepwiki_rate_limit_error",
                "error": str(e),
                "query_type": query_type,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0


def get_deepwiki_query_count(
    query_type: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Get the current DeepWiki query count for this minute.

    Args:
        query_type: Type of query (e.g., 'code_question', 'error_lookup')
        redis_url: Redis connection URL (optional)

    Returns:
        Number of queries in the current minute, or 0 if unavailable
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_minute = int(time.time() / 60)
        key = f"deepwiki:query_count:{query_type}:{current_minute}"

        count = r.get(key)
        return int(count) if count else 0

    except Exception:
        return 0


def check_notification_rate_limit(
    source: str,
    max_per_minute: int = 30,
    redis_url: Optional[str] = None
) -> tuple[bool, int]:
    """
    Check if outbound notifications are rate limited.

    Issue #2153: Rate limiting for OutboundNotifier to avoid triggering API limits.
    Issue #2937: Fixed counter leak bug - now uses check-then-increment pattern.
    Issue #2943: Upgraded to atomic Lua script for true atomicity under concurrency.

    Different services have different rate limits:
    - GitHub: 5000 requests/hour for authenticated requests
    - Jira: Varies by plan, typically 100-1000 requests/minute
    - Slack: 1 message per second per channel (burst allowed)

    This function provides a conservative default of 30/minute per source.

    Args:
        source: Notification source (e.g., 'github', 'jira', 'slack')
        max_per_minute: Maximum notifications allowed per minute (default: 30)
        redis_url: Redis connection URL (optional, uses localhost if None)

    Returns:
        Tuple of (allowed: bool, current_count: int)
        - allowed: True if notification should proceed, False if rate limited
        - current_count: Current number of notifications this minute
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_minute = int(time.time() / 60)
        key = f"outbound_notifier:rate_limit:{source}:{current_minute}"

        # Issue #2943: Use atomic Lua script for true atomicity
        result = _atomic_rate_limit_check(
            r=r,
            key=key,
            max_limit=max_per_minute,
            expiry_seconds=120,  # Keep for 2 minutes to handle edge cases
            trace_id=None,
            context_id=source,
            operation="notification_rate_limit"
        )

        # Issue #2943: Auto-recovery monitoring
        _check_and_alert_rate_limit_pattern(r, key, not result.allowed, "notification_rate_limit")

        return result.allowed, result.current_count

    except redis.ConnectionError as e:
        # Redis unavailable, allow notification (graceful degradation)
        logger.warning(
            "[RateLimit] Redis unavailable, fail-open allowing notification",
            extra={
                "operation": "notification_rate_limit_redis_error",
                "error": str(e),
                "source": source,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0
    except Exception as e:
        # Unexpected error, allow notification (graceful degradation)
        logger.warning(
            "[RateLimit] Unexpected error, fail-open allowing notification",
            extra={
                "operation": "notification_rate_limit_error",
                "error": str(e),
                "source": source,
                "decision": "allowed_fail_open",
            }
        )
        return True, 0


def get_notification_count(
    source: str,
    redis_url: Optional[str] = None
) -> int:
    """
    Get the current notification count for this minute.

    Issue #2153: Helper function for OutboundNotifier rate limiting.

    Args:
        source: Notification source (e.g., 'github', 'jira', 'slack')
        redis_url: Redis connection URL (optional)

    Returns:
        Number of notifications in the current minute, or 0 if unavailable
    """
    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_minute = int(time.time() / 60)
        key = f"outbound_notifier:rate_limit:{source}:{current_minute}"

        count = r.get(key)
        return int(count) if count else 0

    except Exception:
        return 0


# Default rate limits per source (requests per minute)
DEFAULT_NOTIFICATION_RATE_LIMITS = {
    "github": 60,   # GitHub has generous limits for authenticated requests
    "jira": 30,     # Jira has stricter limits
    "slack": 30,    # Slack has per-channel limits, be conservative
}


# =============================================================================
# AI Reviewer Rate Limiting (Issue #2253)
# =============================================================================

# Default rate limits for AI reviewer comments
AI_REVIEWER_RATE_LIMITS = {
    'per_pr_per_hour': 20,      # Each PR can receive max 20 AI comments/hour
    'per_repo_per_hour': 100,   # Each repo can receive max 100 AI comments/hour
    'per_bot_per_hour': 50,     # Each bot can send max 50 comments/hour
}

# Rate limit window in seconds (1 hour)
AI_REVIEWER_RATE_LIMIT_WINDOW = 3600


@dataclass
class AIReviewerRateLimitResult:
    """Result of AI reviewer rate limit check"""
    allowed: bool
    exceeded_dimension: Optional[str] = None  # 'pr', 'repo', or 'bot'
    current_count: int = 0
    limit: int = 0
    pr_id: Optional[str] = None
    repo: Optional[str] = None
    bot_name: Optional[str] = None


def check_ai_reviewer_rate_limit(
    pr_id: str,
    repo: str,
    bot_name: str,
    limits: Optional[Dict[str, int]] = None,
    redis_url: Optional[str] = None
) -> AIReviewerRateLimitResult:
    """
    Check if AI reviewer comment processing is rate limited.

    Uses Redis ZSET sliding window algorithm for accurate rate limiting
    across three dimensions: per-PR, per-repo, and per-bot.

    Issue #2253: Rate limiting for AI reviewer comments.

    Args:
        pr_id: Pull request identifier (e.g., "owner/repo#123")
        repo: Repository identifier (e.g., "owner/repo")
        bot_name: Bot name (e.g., "copilot", "gemini", "coderabbit")
        limits: Optional custom limits dict, defaults to AI_REVIEWER_RATE_LIMITS
        redis_url: Redis connection URL (optional, uses localhost if None)

    Returns:
        AIReviewerRateLimitResult with allowed status and details
    """
    if limits is None:
        limits = AI_REVIEWER_RATE_LIMITS

    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_time = time.time()
        window_start = current_time - AI_REVIEWER_RATE_LIMIT_WINDOW

        # Define rate limit dimensions
        # Use AI_REVIEWER_RATE_LIMITS as fallback for partial limits dict
        pr_limit = limits.get('per_pr_per_hour', AI_REVIEWER_RATE_LIMITS['per_pr_per_hour'])
        repo_limit = limits.get('per_repo_per_hour', AI_REVIEWER_RATE_LIMITS['per_repo_per_hour'])
        bot_limit = limits.get('per_bot_per_hour', AI_REVIEWER_RATE_LIMITS['per_bot_per_hour'])

        dimensions = [
            ('pr', f"ai_reviewer:rate:{pr_id}", pr_limit),
            ('repo', f"ai_reviewer:rate:repo:{repo}", repo_limit),
            ('bot', f"ai_reviewer:rate:bot:{bot_name}", bot_limit),
        ]

        # Check all dimensions first (before incrementing)
        for dimension, key, limit in dimensions:
            # Clean old entries and get current count
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()
            current_count = results[1]

            if current_count >= limit:
                logger.warning(
                    "[AIReviewerRateLimit] Rate limit exceeded",
                    extra={
                        "operation": "ai_reviewer_rate_limit_exceeded",
                        "dimension": dimension,
                        "key": key,
                        "current_count": current_count,
                        "limit": limit,
                        "pr_id": pr_id,
                        "repo": repo,
                        "bot_name": bot_name,
                    }
                )
                return AIReviewerRateLimitResult(
                    allowed=False,
                    exceeded_dimension=dimension,
                    current_count=current_count,
                    limit=limit,
                    pr_id=pr_id,
                    repo=repo,
                    bot_name=bot_name,
                )

        # All checks passed, increment all counters atomically
        unique_member = f"{time.time_ns()}-{uuid.uuid4()}"
        pipe = r.pipeline()
        for _, key, _ in dimensions:
            pipe.zadd(key, {unique_member: current_time})
            pipe.expire(key, AI_REVIEWER_RATE_LIMIT_WINDOW + 60)
        pipe.execute()

        logger.debug(
            "[AIReviewerRateLimit] Rate limit check passed",
            extra={
                "operation": "ai_reviewer_rate_limit_passed",
                "pr_id": pr_id,
                "repo": repo,
                "bot_name": bot_name,
            }
        )

        return AIReviewerRateLimitResult(
            allowed=True,
            pr_id=pr_id,
            repo=repo,
            bot_name=bot_name,
        )

    except redis.ConnectionError as e:
        logger.warning(
            "[AIReviewerRateLimit] Redis unavailable, allowing request",
            extra={
                "operation": "ai_reviewer_rate_limit_redis_error",
                "error": str(e),
                "pr_id": pr_id,
                "repo": repo,
                "bot_name": bot_name,
            }
        )
        return AIReviewerRateLimitResult(
            allowed=True,
            pr_id=pr_id,
            repo=repo,
            bot_name=bot_name,
        )
    except Exception as e:
        logger.warning(
            "[AIReviewerRateLimit] Unexpected error, allowing request",
            extra={
                "operation": "ai_reviewer_rate_limit_error",
                "error": str(e),
                "pr_id": pr_id,
                "repo": repo,
                "bot_name": bot_name,
            }
        )
        return AIReviewerRateLimitResult(
            allowed=True,
            pr_id=pr_id,
            repo=repo,
            bot_name=bot_name,
        )


PR_UPDATED_PENDING_KEY_TTL_BUFFER = 10
PR_UPDATED_THROTTLE_KEY_TTL_BUFFER = 60
PR_UPDATED_JOB_SCHEDULED_TTL_BUFFER = 120

# P2 Robustness: Maximum number of times a single job can reschedule itself
# Prevents infinite loops in extreme scenarios (e.g., continuous rapid pushes)
PR_UPDATED_MAX_RESCHEDULE_COUNT = 10


@dataclass
class PRUpdatedDebounceResult:
    """Result of PR_UPDATED debounce check"""
    should_process: bool
    reason: str
    pr_key: str
    job_token: Optional[str] = None
    should_schedule_job: bool = False
    last_processed_at: Optional[float] = None
    pending_since: Optional[float] = None


def _get_redis_client(redis_url: Optional[str] = None):
    """
    Get Redis client using settings.redis_url or provided URL.

    Args:
        redis_url: Optional Redis URL override

    Returns:
        Redis client instance

    Raises:
        redis.ConnectionError: If Redis is unavailable
    """
    try:
        from common.config.settings import settings
        url = redis_url or getattr(settings, 'redis_url', None)
    except ImportError:
        url = redis_url

    if url:
        return redis.Redis.from_url(url, decode_responses=True)
    else:
        raise redis.ConnectionError("No Redis URL configured (settings.redis_url is None)")


def check_pr_updated_debounce(
    repo: str,
    pr_number: int,
    debounce_seconds: int = 30,
    throttle_seconds: int = 600,
    job_timeout: int = 600,
    redis_url: Optional[str] = None
) -> PRUpdatedDebounceResult:
    """
    Check if a PR_UPDATED event should trigger a delayed review job.

    Phase B-B: PR_UPDATED Event Support with Debounce/Throttle

    Uses "sleep inside job" debounce pattern:
    1. First event: Schedule a delayed job (sleep + process), set job_scheduled key
    2. Subsequent events: Update latest_payload, don't schedule new job
    3. When job wakes up: Read latest payload, process review
    4. Throttle: Ensure minimum time between actual reviews

    CRITICAL FIX: Single push now triggers review after debounce window.
    Previous implementation required a second event to trigger processing.

    Environment Isolation: Uses REDIS_KEY_PREFIX to separate production/staging keys.
    Backward Compatibility: Checks both prefixed and legacy keys to avoid breaking
    in-flight jobs during deployment.

    Args:
        repo: Repository identifier (e.g., "owner/repo")
        pr_number: Pull request number
        debounce_seconds: Debounce window in seconds (default: 30)
        throttle_seconds: Minimum time between reviews (default: 600 = 10 min)
        job_timeout: RQ job timeout for TTL calculation (default: 600)
        redis_url: Redis connection URL (uses settings.redis_url if None)

    Returns:
        PRUpdatedDebounceResult with:
        - should_process: Always False (processing happens in delayed job)
        - should_schedule_job: True if caller should enqueue a delayed job
        - job_token: Token to pass to delayed job for verification
        - reason: Human-readable explanation
    """
    pr_key, legacy_pr_key = _get_pr_updated_keys(repo, pr_number)
    job_scheduled_key = f"{pr_key}:job_scheduled"
    last_processed_key = f"{pr_key}:last_processed"
    latest_payload_key = f"{pr_key}:latest_payload"
    legacy_job_scheduled_key = f"{legacy_pr_key}:job_scheduled"
    legacy_last_processed_key = f"{legacy_pr_key}:last_processed"
    legacy_latest_payload_key = f"{legacy_pr_key}:latest_payload"

    try:
        r = _get_redis_client(redis_url)
        current_time = time.time()

        # Check throttle: prefixed first, then legacy fallback
        last_processed = _get_with_legacy_fallback(r, last_processed_key, legacy_last_processed_key)
        if last_processed:
            last_processed_time = float(last_processed)
            time_since_last = current_time - last_processed_time
            if time_since_last < throttle_seconds:
                logger.info(
                    "[PRUpdatedDebounce] Throttled - PR was reviewed recently",
                    extra={
                        "operation": "pr_updated_debounce_throttled",
                        "repo": repo,
                        "pr_number": pr_number,
                        "time_since_last": time_since_last,
                        "throttle_seconds": throttle_seconds,
                    }
                )
                return PRUpdatedDebounceResult(
                    should_process=False,
                    should_schedule_job=False,
                    reason=f"throttled: last review {int(time_since_last)}s ago",
                    pr_key=pr_key,
                    last_processed_at=last_processed_time,
                )

        job_ttl = debounce_seconds + job_timeout + PR_UPDATED_JOB_SCHEDULED_TTL_BUFFER
        job_token = str(uuid.uuid4())

        # Check if legacy job exists (backward compatibility during deployment)
        # If legacy job exists, don't schedule new prefixed job to avoid duplicates
        legacy_job_exists = False
        if pr_key != legacy_pr_key:
            legacy_job_exists = r.exists(legacy_job_scheduled_key) > 0

        if legacy_job_exists:
            # Legacy job in progress - update legacy payload and extend TTL
            existing_payload = r.get(legacy_latest_payload_key)
            event_count = 1
            if existing_payload:
                try:
                    existing_data = json.loads(existing_payload)
                    event_count = existing_data.get("event_count", 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            payload_data = {
                "repo": repo,
                "pr_number": pr_number,
                "updated_at": current_time,
                "event_count": event_count,
            }
            r.set(
                legacy_latest_payload_key,
                json.dumps(payload_data),
                ex=job_ttl + PR_UPDATED_PENDING_KEY_TTL_BUFFER
            )
            r.expire(legacy_job_scheduled_key, job_ttl)

            logger.debug(
                "[PRUpdatedDebounce] Legacy job in progress - updating legacy payload",
                extra={
                    "operation": "pr_updated_debounce_legacy_update",
                    "repo": repo,
                    "pr_number": pr_number,
                    "event_count": event_count,
                    "legacy_key": legacy_pr_key,
                }
            )
            return PRUpdatedDebounceResult(
                should_process=False,
                should_schedule_job=False,
                reason=f"debounced: legacy job in progress (event #{event_count})",
                pr_key=pr_key,
            )

        # Try to set prefixed job_scheduled key
        was_set = r.set(job_scheduled_key, job_token, nx=True, ex=job_ttl)

        payload_data = {
            "repo": repo,
            "pr_number": pr_number,
            "updated_at": current_time,
            "event_count": 1,
        }

        if was_set:
            r.set(
                latest_payload_key,
                json.dumps(payload_data),
                ex=job_ttl + PR_UPDATED_PENDING_KEY_TTL_BUFFER
            )
            logger.info(
                "[PRUpdatedDebounce] First event - scheduling delayed job",
                extra={
                    "operation": "pr_updated_debounce_schedule_job",
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                    "debounce_seconds": debounce_seconds,
                    "pr_key": pr_key,
                }
            )
            return PRUpdatedDebounceResult(
                should_process=False,
                should_schedule_job=True,
                job_token=job_token,
                reason="first_event: job scheduled",
                pr_key=pr_key,
                pending_since=current_time,
            )
        else:
            existing_payload = r.get(latest_payload_key)
            event_count = 1
            if existing_payload:
                try:
                    existing_data = json.loads(existing_payload)
                    event_count = existing_data.get("event_count", 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

            payload_data["event_count"] = event_count
            r.set(
                latest_payload_key,
                json.dumps(payload_data),
                ex=job_ttl + PR_UPDATED_PENDING_KEY_TTL_BUFFER
            )

            # P2 Robustness: Extend job_scheduled_key TTL on subsequent pushes
            # This prevents token expiration during long push sequences
            r.expire(job_scheduled_key, job_ttl)

            logger.debug(
                "[PRUpdatedDebounce] Subsequent event - updating payload and extending TTL",
                extra={
                    "operation": "pr_updated_debounce_update_payload",
                    "repo": repo,
                    "pr_number": pr_number,
                    "event_count": event_count,
                    "extended_ttl": job_ttl,
                }
            )
            return PRUpdatedDebounceResult(
                should_process=False,
                should_schedule_job=False,
                reason=f"debounced: job already scheduled (event #{event_count})",
                pr_key=pr_key,
            )

    except redis.ConnectionError as e:
        logger.warning(
            "[PRUpdatedDebounce] Redis unavailable - SKIPPING PR_UPDATED (fail-closed)",
            extra={
                "operation": "pr_updated_debounce_redis_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        pr_key_fallback, _ = _get_pr_updated_keys(repo, pr_number)
        return PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=False,
            reason="redis_unavailable: skipped (fail-closed)",
            pr_key=pr_key_fallback,
        )
    except Exception as e:
        logger.warning(
            "[PRUpdatedDebounce] Unexpected error - SKIPPING PR_UPDATED (fail-closed)",
            extra={
                "operation": "pr_updated_debounce_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        pr_key_fallback, _ = _get_pr_updated_keys(repo, pr_number)
        return PRUpdatedDebounceResult(
            should_process=False,
            should_schedule_job=False,
            reason="error: skipped (fail-closed)",
            pr_key=pr_key_fallback,
        )


def verify_pr_updated_job_token(
    repo: str,
    pr_number: int,
    job_token: str,
    redis_url: Optional[str] = None
) -> bool:
    """
    Verify that a delayed job is still the active job for this PR.

    Call this at the start of the delayed job to prevent stale jobs
    from processing if a newer job was scheduled.

    Environment Isolation: Uses REDIS_KEY_PREFIX to separate production/staging keys.
    Backward Compatibility: Checks both prefixed and legacy keys.

    Args:
        repo: Repository identifier
        pr_number: Pull request number
        job_token: Token that was returned when job was scheduled
        redis_url: Redis connection URL (uses settings.redis_url if None)

    Returns:
        True if this job should proceed, False if it should exit
    """
    pr_key, legacy_pr_key = _get_pr_updated_keys(repo, pr_number)
    job_scheduled_key = f"{pr_key}:job_scheduled"
    legacy_job_scheduled_key = f"{legacy_pr_key}:job_scheduled"

    try:
        r = _get_redis_client(redis_url)

        # Check prefixed key first, then legacy fallback
        current_token = _get_with_legacy_fallback(r, job_scheduled_key, legacy_job_scheduled_key)

        if current_token is None:
            logger.warning(
                "[PRUpdatedDebounce] Job token expired or cleared",
                extra={
                    "operation": "pr_updated_verify_token_expired",
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                }
            )
            return False

        if current_token != job_token:
            logger.info(
                "[PRUpdatedDebounce] Job token mismatch - newer job exists",
                extra={
                    "operation": "pr_updated_verify_token_mismatch",
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                    "current_token": current_token,
                }
            )
            return False

        return True

    except Exception as e:
        logger.warning(
            "[PRUpdatedDebounce] Failed to verify token - proceeding anyway",
            extra={
                "operation": "pr_updated_verify_token_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        return True


def get_pr_updated_latest_payload(
    repo: str,
    pr_number: int,
    redis_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the latest payload for a PR_UPDATED event.

    Call this in the delayed job after sleep to get the most recent event data.

    Environment Isolation: Uses REDIS_KEY_PREFIX to separate production/staging keys.
    Backward Compatibility: Checks both prefixed and legacy keys.

    Args:
        repo: Repository identifier
        pr_number: Pull request number
        redis_url: Redis connection URL (uses settings.redis_url if None)

    Returns:
        Dict with latest payload data, or None if not found
    """
    pr_key, legacy_pr_key = _get_pr_updated_keys(repo, pr_number)
    latest_payload_key = f"{pr_key}:latest_payload"
    legacy_latest_payload_key = f"{legacy_pr_key}:latest_payload"

    try:
        r = _get_redis_client(redis_url)

        # Check prefixed key first, then legacy fallback
        payload_str = _get_with_legacy_fallback(r, latest_payload_key, legacy_latest_payload_key)

        if payload_str:
            return json.loads(payload_str)
        return None

    except Exception as e:
        logger.warning(
            "[PRUpdatedDebounce] Failed to get latest payload",
            extra={
                "operation": "pr_updated_get_payload_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        return None


def mark_pr_updated_processed(
    repo: str,
    pr_number: int,
    throttle_seconds: int = 600,
    redis_url: Optional[str] = None
) -> None:
    """
    Mark a PR_UPDATED event as processed (for throttle tracking).

    Call this after successfully processing a PR_UPDATED review.
    Clears the job_scheduled key and sets last_processed timestamp.

    Environment Isolation: Uses REDIS_KEY_PREFIX to separate production/staging keys.
    Backward Compatibility: Cleans up both prefixed and legacy keys.

    Args:
        repo: Repository identifier
        pr_number: Pull request number
        throttle_seconds: Throttle window for TTL
        redis_url: Redis connection URL (uses settings.redis_url if None)
    """
    pr_key, legacy_pr_key = _get_pr_updated_keys(repo, pr_number)
    last_processed_key = f"{pr_key}:last_processed"
    job_scheduled_key = f"{pr_key}:job_scheduled"
    latest_payload_key = f"{pr_key}:latest_payload"
    legacy_job_scheduled_key = f"{legacy_pr_key}:job_scheduled"
    legacy_latest_payload_key = f"{legacy_pr_key}:latest_payload"

    try:
        r = _get_redis_client(redis_url)
        current_time = time.time()

        pipeline = r.pipeline()
        pipeline.set(
            last_processed_key,
            str(current_time),
            ex=throttle_seconds + PR_UPDATED_THROTTLE_KEY_TTL_BUFFER
        )
        # Clean up prefixed keys
        pipeline.delete(job_scheduled_key)
        pipeline.delete(latest_payload_key)
        # Also clean up legacy keys (backward compatibility)
        if pr_key != legacy_pr_key:
            pipeline.delete(legacy_job_scheduled_key)
            pipeline.delete(legacy_latest_payload_key)
        pipeline.execute()

        logger.info(
            "[PRUpdatedDebounce] Marked as processed",
            extra={
                "operation": "pr_updated_mark_processed",
                "repo": repo,
                "pr_number": pr_number,
                "pr_key": pr_key,
            }
        )
    except Exception as e:
        logger.warning(
            "[PRUpdatedDebounce] Failed to mark as processed",
            extra={
                "operation": "pr_updated_mark_processed_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )


def get_ai_reviewer_rate_limit_counts(
    pr_id: Optional[str] = None,
    repo: Optional[str] = None,
    bot_name: Optional[str] = None,
    redis_url: Optional[str] = None
) -> Dict[str, int]:
    """
    Get current AI reviewer rate limit counts for monitoring.

    Issue #2253: Helper function for AI reviewer rate limit monitoring.

    Args:
        pr_id: Optional PR identifier to check
        repo: Optional repo identifier to check
        bot_name: Optional bot name to check
        redis_url: Redis connection URL (optional)

    Returns:
        Dict with counts for each specified dimension
    """
    counts: Dict[str, int] = {}

    try:
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        current_time = time.time()
        window_start = current_time - AI_REVIEWER_RATE_LIMIT_WINDOW

        if pr_id:
            key = f"ai_reviewer:rate:{pr_id}"
            r.zremrangebyscore(key, 0, window_start)
            counts['pr'] = r.zcard(key)

        if repo:
            key = f"ai_reviewer:rate:repo:{repo}"
            r.zremrangebyscore(key, 0, window_start)
            counts['repo'] = r.zcard(key)

        if bot_name:
            key = f"ai_reviewer:rate:bot:{bot_name}"
            r.zremrangebyscore(key, 0, window_start)
            counts['bot'] = r.zcard(key)

    except Exception as exc:
        logger.warning(
            "[AIReviewerRateLimit] Failed to get rate limit counts",
            extra={
                "operation": "ai_reviewer_rate_limit_counts_failed",
                "pr_id": pr_id,
                "repo": repo,
                "bot_name": bot_name,
                "error_type": type(exc).__name__,
            }
        )

    return counts


def increment_reschedule_count(
    repo: str,
    pr_number: int,
    job_token: str,
    ttl_seconds: int = 3600,
    redis_url: Optional[str] = None
) -> tuple[int, bool]:
    """
    Increment and check the reschedule count for a PR_UPDATED job.

    P2 Robustness: Prevents infinite reschedule loops by limiting
    the number of times a single job can reschedule itself.

    Environment Isolation: Uses REDIS_KEY_PREFIX to separate production/staging keys.

    Args:
        repo: Repository identifier
        pr_number: Pull request number
        job_token: Token identifying the job chain
        ttl_seconds: TTL for the counter key (default: 1 hour)
        redis_url: Redis connection URL (uses settings.redis_url if None)

    Returns:
        Tuple of (current_count, exceeded_limit):
        - current_count: Current reschedule count after increment
        - exceeded_limit: True if count exceeds PR_UPDATED_MAX_RESCHEDULE_COUNT
    """
    pr_key, _ = _get_pr_updated_keys(repo, pr_number)
    reschedule_count_key = f"{pr_key}:reschedule_count:{job_token}"

    try:
        r = _get_redis_client(redis_url)
        count = r.incr(reschedule_count_key)
        r.expire(reschedule_count_key, ttl_seconds)

        exceeded = count > PR_UPDATED_MAX_RESCHEDULE_COUNT

        if exceeded:
            logger.warning(
                "[PRUpdatedDebounce] Reschedule limit exceeded",
                extra={
                    "operation": "pr_updated_reschedule_limit_exceeded",
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                    "reschedule_count": count,
                    "max_reschedule_count": PR_UPDATED_MAX_RESCHEDULE_COUNT,
                }
            )
        else:
            logger.debug(
                "[PRUpdatedDebounce] Reschedule count incremented",
                extra={
                    "operation": "pr_updated_reschedule_count",
                    "repo": repo,
                    "pr_number": pr_number,
                    "job_token": job_token,
                    "reschedule_count": count,
                    "max_reschedule_count": PR_UPDATED_MAX_RESCHEDULE_COUNT,
                }
            )

        return count, exceeded

    except Exception as e:
        logger.warning(
            "[PRUpdatedDebounce] Failed to check reschedule count - allowing reschedule",
            extra={
                "operation": "pr_updated_reschedule_count_error",
                "error": str(e),
                "repo": repo,
                "pr_number": pr_number,
            }
        )
        return 0, False


def check_rq_scheduler_health(redis_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if RQ Scheduler is running and healthy.

    P2 Robustness: Healthcheck to ensure the scheduler is running,
    which is required for enqueue_in() delayed jobs to execute.

    Args:
        redis_url: Redis connection URL (uses settings.redis_url if None)

    Returns:
        Dict with health status:
        - healthy: True if scheduler appears to be running (scheduler_key_exists=True)
        - scheduler_key_exists: True if scheduler registry key exists
        - scheduled_jobs_count: Number of jobs in scheduled queue
        - queue_name: The queue name used for health check
        - error: Error message if check failed
    """
    try:
        from common.config.settings import settings
        queue_name = getattr(settings, 'rq_queue_name', None) or 'orchestrator'
    except ImportError:
        queue_name = 'orchestrator'

    result: Dict[str, Any] = {
        "healthy": False,
        "scheduler_key_exists": False,
        "scheduled_jobs_count": 0,
        "queue_name": queue_name,
        "error": None,
    }

    try:
        r = _get_redis_client(redis_url)

        scheduler_key = f"rq:scheduler:{queue_name}"
        result["scheduler_key_exists"] = r.exists(scheduler_key) > 0

        scheduled_registry_key = f"rq:scheduled:{queue_name}"
        result["scheduled_jobs_count"] = r.zcard(scheduled_registry_key)

        # healthy=True only if scheduler key exists (scheduler is running)
        result["healthy"] = result["scheduler_key_exists"]

        logger.info(
            "[RQSchedulerHealth] Health check completed",
            extra={
                "operation": "rq_scheduler_health_check",
                "healthy": result["healthy"],
                "scheduler_key_exists": result["scheduler_key_exists"],
                "scheduled_jobs_count": result["scheduled_jobs_count"],
                "queue_name": queue_name,
            }
        )

    except Exception as e:
        result["error"] = str(e)
        logger.warning(
            "[RQSchedulerHealth] Health check failed",
            extra={
                "operation": "rq_scheduler_health_check_error",
                "error": str(e),
                "queue_name": queue_name,
            }
        )

    return result
