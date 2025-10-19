"""Rate limiting utilities for Orchestrator PR creation"""
import redis
import time
from typing import Optional


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
