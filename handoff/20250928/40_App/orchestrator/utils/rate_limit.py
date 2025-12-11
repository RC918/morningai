"""Rate limiting utilities for Orchestrator PR creation"""
import logging
import redis
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def check_pr_rate_limit(
    trace_id: str,
    max_per_hour: int = 10,
    redis_url: Optional[str] = None
) -> tuple[bool, int]:
    """
    Check if we've created too many PRs recently.
    
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
        
        count = r.incr(key)
        r.expire(key, 3600)
        
        if count > max_per_hour:
            print(f"[Rate Limit] Already created {count} PRs this hour (max: {max_per_hour})")
            return False, count
        
        print(f"[Rate Limit] PR count this hour: {count}/{max_per_hour}")
        return True, count
        
    except redis.ConnectionError as e:
        print(f"[Rate Limit] Redis unavailable, allowing PR creation: {e}")
        return True, 0
    except Exception as e:
        print(f"[Rate Limit] Unexpected error, allowing PR creation: {e}")
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
        
        count = r.incr(key)
        r.expire(key, 120)  # Keep for 2 minutes to handle edge cases
        
        if count > max_per_minute:
            return False, count
        
        return True, count
        
    except redis.ConnectionError:
        # Redis unavailable, allow query (graceful degradation)
        return True, 0
    except Exception:
        # Unexpected error, allow query (graceful degradation)
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

        count = r.incr(key)
        r.expire(key, 120)  # Keep for 2 minutes to handle edge cases

        if count > max_per_minute:
            return False, count

        return True, count

    except redis.ConnectionError:
        # Redis unavailable, allow notification (graceful degradation)
        return True, 0
    except Exception:
        # Unexpected error, allow notification (graceful degradation)
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
