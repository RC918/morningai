import os
import time
import logging
import uuid
import threading
from functools import wraps
from flask import request, jsonify, make_response, g
from redis import ConnectionError as RedisConnectionError
from common.config.settings import settings

logger = logging.getLogger(__name__)

redis_state_lock = threading.Lock()
redis_client = None
redis_connecting = False
retry_attempts = 0
next_retry_deadline = 0.0
REDIS_MAX_RETRIES = settings.rate_limit_redis_max_retries or 3
REDIS_RETRY_DELAY = settings.rate_limit_redis_retry_delay or 1.0
REDIS_LONG_COOLDOWN = 60.0

def get_rate_limit_redis():
    """
    Get Redis client with lazy initialization and non-blocking retry mechanism.
    
    This function initializes Redis on first request rather than at module import time,
    avoiding timing issues where Redis might not be available during app initialization.
    
    If redis_client is already set (e.g., by tests), returns it immediately.
    
    Implements non-blocking retry with exponential backoff. Only one thread attempts
    reconnection at a time; others proceed without rate limiting during backoff window.
    
    Returns:
        Redis client or None if unavailable or in backoff window
    """
    global redis_client, redis_connecting, retry_attempts, next_retry_deadline
    
    if redis_client is not None:
        return redis_client
    
    now = time.monotonic()
    
    with redis_state_lock:
        if redis_client is not None:
            return redis_client
        if redis_connecting:
            return None
        if now < next_retry_deadline:
            return None
        redis_connecting = True
    
    client = None
    error_msg = None
    try:
        from src.utils.redis_client import get_redis_client
        client = get_redis_client()
    except Exception as e:
        error_msg = str(e)
    
    now_after = time.monotonic()
    
    with redis_state_lock:
        redis_connecting = False
        if client:
            redis_client = client
            retry_attempts = 0
            next_retry_deadline = 0.0
            logger.info("✅ Rate limit Redis connection established")
        else:
            retry_attempts += 1
            if retry_attempts < REDIS_MAX_RETRIES:
                delay = REDIS_RETRY_DELAY * retry_attempts
                next_retry_deadline = now_after + delay
                logger.warning(f"⚠️ Rate limit Redis connection failed (attempt {retry_attempts}/{REDIS_MAX_RETRIES}), will retry in {delay}s: {error_msg}")
            else:
                next_retry_deadline = now_after + REDIS_LONG_COOLDOWN
                logger.warning(f"⚠️ Rate limit Redis unavailable after {REDIS_MAX_RETRIES} retries, will retry in {REDIS_LONG_COOLDOWN}s: {error_msg}")
    
    return redis_client

def get_rate_limit_requests():
    """Get rate limit requests dynamically from app.config, env, or settings"""
    try:
        from flask import current_app
        if current_app:
            v = current_app.config.get("RATE_LIMIT_REQUESTS")
            if v is not None:
                return int(v)
    except Exception:
        pass
    env_v = os.getenv("RATE_LIMIT_REQUESTS")
    if env_v is not None:
        return int(env_v)
    return settings.rate_limit_requests or 60

RATE_LIMIT_WINDOW = settings.rate_limit_window or 60
RATE_LIMIT_BY_USER = settings.rate_limit_by_user or False

def _extract_user_id():
    """Extract user ID from request context with fallbacks"""
    uid = getattr(request, 'user_id', None)
    if uid:
        return str(uid)
    
    cu = getattr(request, 'current_user', None)
    if isinstance(cu, dict) and cu.get('user_id'):
        return str(cu['user_id'])
    
    uid = getattr(g, 'user_id', None)
    if uid:
        return str(uid)
    
    return None

def rate_limit(f):
    """Rate limiting decorator with IP and optional user-based limiting
    
    Uses Redis sliding window algorithm for accurate rate limiting.
    Falls back to no limiting if Redis is unavailable.
    Adds X-RateLimit-* headers for observability.
    
    Rate limiting can be configured to use:
    - IP-based (default): Limits requests per IP address
    - User-based (RATE_LIMIT_BY_USER=true): Limits requests per authenticated user
    - Hybrid: Both IP and user limits (most restrictive applies)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client = get_rate_limit_redis()
        
        if not client:
            response = f(*args, **kwargs)
            return response
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        user_id = None
        if RATE_LIMIT_BY_USER:
            user_id = _extract_user_id()
        
        if user_id:
            rate_limit_key = f"rate_limit:user:{user_id}"
            identifier = f"user {user_id}"
        else:
            rate_limit_key = f"rate_limit:ip:{client_ip}"
            identifier = f"IP {client_ip}"
        
        try:
            current_time = time.time()
            window_start = current_time - RATE_LIMIT_WINDOW
            
            unique_member = f"{time.time_ns()}-{uuid.uuid4()}"
            
            rate_limit_requests = get_rate_limit_requests()
            
            pipe = client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {unique_member: current_time})
            pipe.expire(rate_limit_key, RATE_LIMIT_WINDOW + 10)
            results = pipe.execute()
            
            pre_count = results[1]
            remaining = max(0, rate_limit_requests - pre_count - 1)
            reset_time = int(current_time + RATE_LIMIT_WINDOW)
            
            if pre_count >= rate_limit_requests:
                logger.warning(f"Rate limit exceeded for {identifier}: {pre_count} requests")
                
                try:
                    if hasattr(g, 'metrics'):
                        g.metrics['rate_limit_exceeded'] = True
                        g.metrics['rate_limit_identifier'] = identifier
                except Exception:
                    pass  # Don't fail request if metrics tracking fails
                
                response = jsonify({
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {rate_limit_requests} requests per {RATE_LIMIT_WINDOW} seconds."
                    }
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(rate_limit_requests)
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(reset_time)
                return response
            
            try:
                if hasattr(g, 'metrics'):
                    g.metrics['rate_limit_remaining'] = remaining
                    g.metrics['rate_limit_identifier'] = identifier
            except Exception:
                pass  # Don't fail request if metrics tracking fails
            
            result = f(*args, **kwargs)
            
            if isinstance(result, tuple):
                response_obj = make_response(result[0])
                status_code = result[1] if len(result) > 1 else 200
                response_obj.status_code = status_code
                response_obj.headers['X-RateLimit-Limit'] = str(rate_limit_requests)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(reset_time)
                return response_obj
            else:
                response_obj = make_response(result)
                response_obj.headers['X-RateLimit-Limit'] = str(rate_limit_requests)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(reset_time)
                return response_obj
            
        except RedisConnectionError as e:
            logger.warning(f"Rate limit Redis error, allowing request: {e}")
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return f(*args, **kwargs)
    
    return decorated_function


def __getattr__(name):
    """
    Provide backward compatibility for deprecated module-level constants.
    
    This allows existing code to import RATE_LIMIT_REQUESTS, but the value
    is dynamically resolved at access time rather than module import time.
    """
    if name == "RATE_LIMIT_REQUESTS":
        import warnings
        warnings.warn(
            "Importing RATE_LIMIT_REQUESTS as a constant is deprecated. "
            "Use get_rate_limit_requests() for dynamic resolution.",
            DeprecationWarning,
            stacklevel=2
        )
        return get_rate_limit_requests()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
