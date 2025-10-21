#!/usr/bin/env python3
"""
Rate Limiting Middleware for Orchestrator API
Uses Redis for distributed rate limiting
"""
import logging
import time
from typing import Optional, Callable
from datetime import datetime, timezone

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration"""
    DEFAULT_RATE_LIMIT = 60
    
    BURST_LIMIT = 10
    
    WINDOW_SIZE = 60
    
    ENDPOINT_LIMITS = {
        "/tasks": 30,
        "/events/publish": 100,
        "/health": 300,
    }


class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client for distributed rate limiting
        """
        self.redis = redis_client
        self.local_cache = {}  # Fallback for when Redis is unavailable
    
    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int = RateLimitConfig.WINDOW_SIZE
    ) -> tuple[bool, int]:
        """
        Check if request should be rate limited
        
        Uses sliding window algorithm with Redis
        
        Args:
            key: Rate limit key (e.g., "ip:192.168.1.1")
            limit: Max requests allowed in window
            window: Time window in seconds
        
        Returns:
            tuple[bool, int]: (is_limited, remaining_requests)
        """
        if self.redis:
            return await self._check_redis(key, limit, window)
        else:
            return await self._check_local(key, limit, window)
    
    async def _check_redis(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check rate limit using Redis"""
        try:
            now = time.time()
            window_start = now - window
            
            redis_key = f"rate_limit:{key}"
            
            pipe = self.redis.pipeline()
            
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            pipe.zcard(redis_key)
            
            pipe.zadd(redis_key, {str(now): now})
            
            pipe.expire(redis_key, window + 1)
            
            results = await pipe.execute()
            
            current_count = results[1]
            
            is_limited = current_count >= limit
            remaining = max(0, limit - current_count - 1)
            
            if is_limited:
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
            
            return is_limited, remaining
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}, falling back to local")
            return await self._check_local(key, limit, window)
    
    async def _check_local(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check rate limit using local memory (fallback)"""
        now = time.time()
        
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        self.local_cache[key] = [
            timestamp for timestamp in self.local_cache[key]
            if now - timestamp < window
        ]
        
        current_count = len(self.local_cache[key])
        
        is_limited = current_count >= limit
        remaining = max(0, limit - current_count - 1)
        
        if not is_limited:
            self.local_cache[key].append(now)
        
        return is_limited, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, redis_client_getter: Optional[Callable] = None):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            redis_client_getter: Callable that returns Redis client (for lazy initialization)
        """
        super().__init__(app)
        self.redis_client_getter = redis_client_getter
        self.rate_limiter = None
    
    def _get_rate_limiter(self) -> RateLimiter:
        """Get or create rate limiter with current Redis client"""
        redis_client = None
        if self.redis_client_getter:
            redis_client = self.redis_client_getter()
        
        if not self.rate_limiter or (redis_client and not self.rate_limiter.redis):
            self.rate_limiter = RateLimiter(redis_client)
        
        return self.rate_limiter
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""
        if request.url.path == "/health":
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        limit = self._get_endpoint_limit(request.url.path)
        
        rate_limiter = self._get_rate_limiter()
        
        rate_limit_key = f"ip:{client_ip}:{request.url.path}"
        is_limited, remaining = await rate_limiter.is_rate_limited(
            rate_limit_key,
            limit
        )
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + RateLimitConfig.WINDOW_SIZE)),
                    "Retry-After": str(RateLimitConfig.WINDOW_SIZE)
                }
            )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + RateLimitConfig.WINDOW_SIZE))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit for specific endpoint"""
        if path in RateLimitConfig.ENDPOINT_LIMITS:
            return RateLimitConfig.ENDPOINT_LIMITS[path]
        
        for endpoint_path, limit in RateLimitConfig.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_path):
                return limit
        
        return RateLimitConfig.DEFAULT_RATE_LIMIT
