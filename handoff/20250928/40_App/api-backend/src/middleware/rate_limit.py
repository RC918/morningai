import os
import time
import logging
from functools import wraps
from flask import request, jsonify
from redis import Redis, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    redis_client.ping()
    logger.info("Rate limit Redis connection established")
except Exception as e:
    logger.warning(f"Rate limit Redis unavailable, rate limiting will be disabled: {e}")
    redis_client = None

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

def rate_limit(f):
    """Rate limiting decorator (60 requests per minute per IP by default)
    
    Uses Redis sliding window algorithm for accurate rate limiting.
    Falls back to no limiting if Redis is unavailable.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not redis_client:
            return f(*args, **kwargs)
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        rate_limit_key = f"rate_limit:{client_ip}"
        
        try:
            current_time = int(time.time())
            window_start = current_time - RATE_LIMIT_WINDOW
            
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            pipe.expire(rate_limit_key, RATE_LIMIT_WINDOW + 10)
            results = pipe.execute()
            
            request_count = results[1]
            
            if request_count >= RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for IP {client_ip}: {request_count} requests")
                return jsonify({
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
                    }
                }), 429
            
            return f(*args, **kwargs)
            
        except RedisConnectionError as e:
            logger.warning(f"Rate limit Redis error, allowing request: {e}")
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return f(*args, **kwargs)
    
    return decorated_function
