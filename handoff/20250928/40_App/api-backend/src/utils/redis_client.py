import os
import logging
import ssl
from typing import Optional, Dict, Any
from common.config.settings import get_settings

logger = logging.getLogger(__name__)

def create_redis_client(skip_ping: bool = False):
    """
    Creates Redis client with automatic TLS detection
    Supports:
    1. Upstash Redis (HTTPS REST API)
    2. Redis Cloud (TLS TCP)
    3. Local Redis (non-TLS fallback)
    
    Args:
        skip_ping: If True, skip the initial ping check (useful for testing)
    """
    
    upstash_url = get_settings().upstash_redis_rest_url
    if upstash_url:
        try:
            from upstash_redis import Redis
            client = Redis(
                url=upstash_url,
                token=get_settings().upstash_redis_rest_token
            )
            if not skip_ping:
                client.ping()
                logger.info("✅ Connected to Upstash Redis (HTTPS)")
            return client
        except ImportError:
            logger.warning("⚠️ upstash-redis not installed, falling back to standard Redis")
        except Exception as e:
            if not skip_ping:
                logger.error(f"❌ Upstash Redis connection failed: {e}")
                raise
            else:
                logger.debug(f"Upstash Redis client created (ping skipped): {e}")
                raise
    
    redis_url = get_settings().redis_url
    if redis_url:
        try:
            import redis
            
            if not redis_url.startswith("rediss://"):
                logger.warning("⚠️ Redis URL not using TLS (rediss://), recommend upgrading for security")
            
            client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            if not skip_ping:
                client.ping()
                tls_status = "TLS" if redis_url.startswith("rediss://") else "non-TLS"
                logger.info(f"✅ Connected to Redis ({tls_status})")
            
            return client
        except Exception as e:
            if not skip_ping:
                logger.error(f"❌ Redis connection failed: {e}")
                raise
            else:
                logger.debug(f"Redis client created (ping skipped): {e}")
                raise
    
    raise ValueError("❌ No Redis configuration found (UPSTASH_REDIS_REST_URL or REDIS_URL)")

redis_client: Optional[object] = None

def get_redis_client():
    """Get Redis client singleton"""
    global redis_client
    if redis_client is None:
        redis_client = create_redis_client(skip_ping=settings.testing)
    return redis_client

def get_redis_connection_info():
    """Get Redis connection information for health checks"""
    upstash_url = get_settings().upstash_redis_rest_url
    redis_url = get_settings().redis_url
    
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
        
        upstash_url = get_settings().upstash_redis_rest_url
        if upstash_url:
            return {
                "status": "secure",
                "type": "upstash",
                "message": "Using Upstash Redis (cloud-managed, auto-updated)",
                "cve_2025_49844_risk": "low",
                "recommendations": []
            }
        
        redis_url = get_settings().redis_url
        if redis_url:
            info = client.info("server")
            redis_version = info.get("redis_version", "unknown")
            
            try:
                parts = redis_version.split(".")
                
                major = int(parts[0]) if len(parts) > 0 else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                
                if len(parts) > 2:
                    patch_str = parts[2].split("-")[0].split("+")[0]  # Remove suffixes
                    patch = int(patch_str) if patch_str.isdigit() else 0
                else:
                    patch = 0
                
                version_tuple = (major, minor, patch)
            except (ValueError, AttributeError, IndexError) as e:
                logger.warning(f"Failed to parse Redis version '{redis_version}': {e}")
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
