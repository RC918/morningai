"""
Redis Configuration Helper

Provides secure Redis URL configuration with TLS enforcement.
"""
import os
import logging

logger = logging.getLogger(__name__)


def get_secure_redis_url(allow_local: bool = False) -> str:
    """
    Get Redis URL with TLS enforcement for production.
    
    Args:
        allow_local: If True, allows redis://localhost for local development.
                    If False (default), requires TLS for all connections.
    
    Returns:
        str: Redis URL (Upstash HTTPS or rediss:// with TLS)
    
    Raises:
        ValueError: If no secure Redis configuration found
    
    Examples:
        redis_url = get_secure_redis_url()
        
        redis_url = get_secure_redis_url(allow_local=True)
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    if upstash_url:
        logger.info("✅ Using Upstash Redis (HTTPS)")
        return upstash_url
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        if redis_url.startswith("rediss://"):
            logger.info("✅ Using Redis with TLS (rediss://)")
            return redis_url
        
        if redis_url.startswith("redis://localhost") and allow_local:
            logger.warning("⚠️ Using local Redis without TLS (development only)")
            return redis_url
        
        if not redis_url.startswith("rediss://"):
            raise ValueError(
                "❌ REDIS_URL must use TLS (rediss://) for production. "
                "Current URL does not use TLS. "
                "For local development, use get_secure_redis_url(allow_local=True). "
                f"Got: {redis_url[:20]}..."
            )
    
    raise ValueError(
        "❌ No Redis configuration found. "
        "Set UPSTASH_REDIS_REST_URL (recommended) or REDIS_URL environment variable. "
        "For production, REDIS_URL must use TLS (rediss://)."
    )


def is_redis_tls_enabled() -> bool:
    """
    Check if Redis TLS is enabled.
    
    Returns:
        bool: True if using Upstash (HTTPS) or rediss:// (TLS)
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    if upstash_url:
        return True
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis_url.startswith("rediss://"):
        return True
    
    return False


def get_redis_connection_info() -> dict:
    """
    Get Redis connection information for health checks and monitoring.
    
    Returns:
        dict: Connection information including type, protocol, and TLS status
    """
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    redis_url = os.getenv("REDIS_URL")
    
    if upstash_url:
        return {
            "type": "upstash",
            "protocol": "https",
            "tls_enabled": True,
            "url": upstash_url.split("@")[-1] if "@" in upstash_url else "***",
            "secure": True
        }
    elif redis_url:
        is_tls = redis_url.startswith("rediss://")
        is_local = redis_url.startswith("redis://localhost")
        return {
            "type": "redis",
            "protocol": "rediss" if is_tls else "redis",
            "tls_enabled": is_tls,
            "url": redis_url.split("@")[-1] if "@" in redis_url else "***",
            "secure": is_tls,
            "local_dev": is_local
        }
    else:
        return {
            "type": "none",
            "protocol": "none",
            "tls_enabled": False,
            "url": "not_configured",
            "secure": False
        }
