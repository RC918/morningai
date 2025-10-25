import os
import logging
import ssl
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def create_redis_client():
    """
    Creates Redis client with automatic TLS detection
    Supports:
    1. Upstash Redis (HTTPS REST API)
    2. Redis Cloud (TLS TCP)
    3. Local Redis (non-TLS fallback)
    """
    
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    if upstash_url:
        try:
            from upstash_redis import Redis
            client = Redis(
                url=upstash_url,
                token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
            )
            client.ping()
            logger.info("✅ Connected to Upstash Redis (HTTPS)")
            return client
        except ImportError:
            logger.warning("⚠️ upstash-redis not installed, falling back to standard Redis")
        except Exception as e:
            logger.error(f"❌ Upstash Redis connection failed: {e}")
            raise
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            
            if not redis_url.startswith("rediss://"):
                logger.warning("⚠️ Redis URL not using TLS (rediss://), recommend upgrading for security")
            
            ssl_cert_reqs = ssl.CERT_REQUIRED if redis_url.startswith("rediss://") else None
            
            client = redis.from_url(
                redis_url,
                ssl_cert_reqs=ssl_cert_reqs,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            client.ping()
            
            tls_status = "TLS" if redis_url.startswith("rediss://") else "non-TLS"
            logger.info(f"✅ Connected to Redis ({tls_status})")
            return client
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    raise ValueError("❌ No Redis configuration found (UPSTASH_REDIS_REST_URL or REDIS_URL)")

redis_client: Optional[object] = None

def get_redis_client():
    """Get Redis client singleton"""
    global redis_client
    if redis_client is None:
        redis_client = create_redis_client()
    return redis_client

def get_redis_connection_info():
    """Get Redis connection information for health checks"""
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    redis_url = os.getenv("REDIS_URL")
    
    if upstash_url:
        return {
            "type": "upstash",
            "protocol": "https",
            "tls_enabled": True,
            "url": upstash_url.split("@")[-1] if "@" in upstash_url else "***"
        }
    elif redis_url:
        is_tls = redis_url.startswith("rediss://")
        return {
            "type": "redis",
            "protocol": "rediss" if is_tls else "redis",
            "tls_enabled": is_tls,
            "url": redis_url.split("@")[-1] if "@" in redis_url else "***"
        }
    else:
        return {
            "type": "none",
            "protocol": "none",
            "tls_enabled": False,
            "url": "not_configured"
        }

def check_redis_security() -> Dict[str, Any]:
    """
    Check Redis security status and version
    
    Returns:
        Dict containing security status and recommendations
    """
    try:
        client = get_redis_client()
        
        upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
        if upstash_url:
            return {
                "status": "secure",
                "type": "upstash",
                "message": "Using Upstash Redis (cloud-managed, auto-updated)",
                "cve_2025_49844_risk": "low",
                "recommendations": []
            }
        
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            info = client.info("server")
            redis_version = info.get("redis_version", "unknown")
            
            try:
                major, minor, patch = map(int, redis_version.split(".")[:3])
                version_tuple = (major, minor, patch)
            except (ValueError, AttributeError):
                version_tuple = (0, 0, 0)
            
            is_vulnerable = version_tuple < (8, 2, 2)
            
            is_tls = redis_url.startswith("rediss://")
            
            recommendations = []
            if is_vulnerable:
                recommendations.append("⚠️ CRITICAL: Upgrade Redis to 8.2.2+ to fix CVE-2025-49844 (RediShell)")
                recommendations.append("Temporary mitigation: Disable Lua scripts via ACL")
            if not is_tls:
                recommendations.append("⚠️ Enable TLS encryption (use rediss:// instead of redis://)")
            
            return {
                "status": "vulnerable" if is_vulnerable else "secure",
                "type": "redis",
                "version": redis_version,
                "tls_enabled": is_tls,
                "cve_2025_49844_risk": "high" if is_vulnerable else "low",
                "message": f"Redis {redis_version} - {'VULNERABLE' if is_vulnerable else 'Secure'}",
                "recommendations": recommendations
            }
        
        return {
            "status": "unknown",
            "type": "none",
            "message": "No Redis configuration found",
            "cve_2025_49844_risk": "unknown",
            "recommendations": ["Configure Redis connection"]
        }
        
    except Exception as e:
        logger.error(f"Failed to check Redis security: {e}")
        return {
            "status": "error",
            "type": "unknown",
            "message": f"Failed to check Redis security: {str(e)}",
            "cve_2025_49844_risk": "unknown",
            "recommendations": ["Check Redis connection"]
        }
