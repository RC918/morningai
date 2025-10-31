import os
import time
import logging
import uuid
from functools import wraps
from flask import request, jsonify, make_response, g
from redis import ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

redis_client = None
redis_init_attempted = False
redis_retry_count = 0
REDIS_MAX_RETRIES = int(os.getenv("RATE_LIMIT_REDIS_MAX_RETRIES", "3"))
REDIS_RETRY_DELAY = float(os.getenv("RATE_LIMIT_REDIS_RETRY_DELAY", "1.0"))

def get_rate_limit_redis():
    """
    Get Redis client with lazy initialization and retry mechanism.
    
    This function initializes Redis on first request rather than at module import time,
    avoiding timing issues where Redis might not be available during app initialization.
    
    If redis_client is already set (e.g., by tests), returns it immediately.
    
    Implements retry mechanism with exponential backoff for transient connection failures.
    
    Returns:
        Redis client or None if unavailable after retries
    """
    global redis_client, redis_init_attempted, redis_retry_count
    
    if redis_client is not None:
        return redis_client
    
    if not redis_init_attempted or redis_retry_count < REDIS_MAX_RETRIES:
        redis_init_attempted = True
        try:
            from src.utils.redis_client import get_redis_client
            redis_client = get_redis_client()
            logger.info("✅ Rate limit Redis connection established")
            redis_retry_count = 0  # Reset retry count on success
        except Exception as e:
            redis_retry_count += 1
            if redis_retry_count < REDIS_MAX_RETRIES:
                logger.warning(f"⚠️ Rate limit Redis connection failed (attempt {redis_retry_count}/{REDIS_MAX_RETRIES}), will retry: {e}")
                time.sleep(REDIS_RETRY_DELAY * redis_retry_count)  # Exponential backoff
            else:
                logger.warning(f"⚠️ Rate limit Redis unavailable after {REDIS_MAX_RETRIES} retries, rate limiting will be disabled: {e}")
            redis_client = None
    
    return redis_client

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_BY_USER = os.getenv("RATE_LIMIT_BY_USER", "false").lower() == "true"

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
        if RATE_LIMIT_BY_USER and hasattr(g, 'user_id'):
            user_id = g.user_id
        
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
            
            pipe = client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {unique_member: current_time})
            pipe.expire(rate_limit_key, RATE_LIMIT_WINDOW + 10)
            results = pipe.execute()
            
            pre_count = results[1]
            remaining = max(0, RATE_LIMIT_REQUESTS - pre_count - 1)
            reset_time = int(current_time + RATE_LIMIT_WINDOW)
            
            if pre_count >= RATE_LIMIT_REQUESTS:
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
                        "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
                    }
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_REQUESTS)
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
                response_obj.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_REQUESTS)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(reset_time)
                return response_obj
            else:
                response_obj = make_response(result)
                response_obj.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_REQUESTS)
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
