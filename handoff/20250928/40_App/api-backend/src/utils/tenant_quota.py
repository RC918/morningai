"""Tenant Quota Management for Multi-Tenant Resource Isolation

Phase 4: Engineering Optimization (#1820)

This module provides tenant-level resource quota management including:
- Quota checking and enforcement
- Usage tracking and monitoring
- Rate limiting per tenant
"""
import logging
from dataclasses import dataclass
from typing import Optional
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)


@dataclass
class TenantQuota:
    """Tenant quota configuration"""
    tenant_id: str
    api_requests_per_minute: int = 60
    api_requests_per_hour: int = 1000
    api_requests_per_day: int = 10000
    max_concurrent_tasks: int = 5
    max_tasks_per_day: int = 100
    max_task_duration_seconds: int = 300
    max_storage_bytes: int = 1073741824  # 1GB
    max_documents: int = 1000
    max_embeddings: int = 10000
    max_llm_tokens_per_day: int = 100000
    max_llm_requests_per_hour: int = 100
    max_prs_per_day: int = 10
    max_code_generations_per_hour: int = 50
    plan_tier: str = "free"


@dataclass
class TenantUsage:
    """Current tenant usage"""
    tenant_id: str
    api_requests_minute: int = 0
    api_requests_hour: int = 0
    api_requests_day: int = 0
    concurrent_tasks: int = 0
    tasks_today: int = 0
    storage_bytes_used: int = 0
    documents_count: int = 0
    embeddings_count: int = 0
    llm_tokens_today: int = 0
    llm_requests_hour: int = 0
    prs_today: int = 0
    code_generations_hour: int = 0


@dataclass
class QuotaCheckResult:
    """Result of quota check"""
    allowed: bool
    current_usage: int
    quota_limit: int
    remaining: int
    resource_type: str


# Plan tier configurations
PLAN_TIERS = {
    "free": {
        "api_requests_per_minute": 30,
        "api_requests_per_hour": 500,
        "api_requests_per_day": 5000,
        "max_concurrent_tasks": 2,
        "max_tasks_per_day": 50,
        "max_llm_tokens_per_day": 50000,
        "max_prs_per_day": 5,
    },
    "starter": {
        "api_requests_per_minute": 60,
        "api_requests_per_hour": 1000,
        "api_requests_per_day": 10000,
        "max_concurrent_tasks": 5,
        "max_tasks_per_day": 100,
        "max_llm_tokens_per_day": 100000,
        "max_prs_per_day": 10,
    },
    "pro": {
        "api_requests_per_minute": 120,
        "api_requests_per_hour": 3000,
        "api_requests_per_day": 30000,
        "max_concurrent_tasks": 10,
        "max_tasks_per_day": 500,
        "max_llm_tokens_per_day": 500000,
        "max_prs_per_day": 50,
    },
    "enterprise": {
        "api_requests_per_minute": 300,
        "api_requests_per_hour": 10000,
        "api_requests_per_day": 100000,
        "max_concurrent_tasks": 50,
        "max_tasks_per_day": 2000,
        "max_llm_tokens_per_day": 2000000,
        "max_prs_per_day": 200,
    },
}


class TenantQuotaManager:
    """Manager for tenant quota operations"""

    def __init__(self, redis_client=None, supabase_client=None):
        self._redis = redis_client
        self._supabase = supabase_client

    @property
    def redis(self):
        """Lazy load Redis client"""
        if self._redis is None:
            try:
                from src.utils.redis_client import get_redis_client
                self._redis = get_redis_client()
            except Exception as e:
                logger.warning("Redis unavailable for tenant quota: %s", e)
        return self._redis

    @property
    def supabase(self):
        """Lazy load Supabase client"""
        if self._supabase is None:
            try:
                from src.db.supabase_client import get_supabase_client
                self._supabase = get_supabase_client()
            except Exception as e:
                logger.warning("Supabase unavailable for tenant quota: %s", e)
        return self._supabase

    def get_tenant_quota(self, tenant_id: str) -> TenantQuota:
        """Get quota configuration for a tenant"""
        try:
            if self.supabase:
                result = self.supabase.rpc(
                    "get_tenant_quota",
                    {"p_tenant_id": tenant_id}
                ).execute()

                if result.data and len(result.data) > 0:
                    row = result.data[0]
                    return TenantQuota(
                        tenant_id=tenant_id,
                        api_requests_per_minute=row.get("api_requests_per_minute", 60),
                        api_requests_per_hour=row.get("api_requests_per_hour", 1000),
                        api_requests_per_day=row.get("api_requests_per_day", 10000),
                        max_concurrent_tasks=row.get("max_concurrent_tasks", 5),
                        max_tasks_per_day=row.get("max_tasks_per_day", 100),
                        max_task_duration_seconds=row.get("max_task_duration_seconds", 300),
                        max_storage_bytes=row.get("max_storage_bytes", 1073741824),
                        max_documents=row.get("max_documents", 1000),
                        max_embeddings=row.get("max_embeddings", 10000),
                        max_llm_tokens_per_day=row.get("max_llm_tokens_per_day", 100000),
                        max_llm_requests_per_hour=row.get("max_llm_requests_per_hour", 100),
                        max_prs_per_day=row.get("max_prs_per_day", 10),
                        max_code_generations_per_hour=row.get("max_code_generations_per_hour", 50),
                        plan_tier=row.get("plan_tier", "free"),
                    )
        except Exception as e:
            logger.warning("Failed to get tenant quota from DB: %s", e)

        return TenantQuota(tenant_id=tenant_id)

    def check_quota(
        self,
        tenant_id: str,
        resource_type: str,
        increment: int = 1
    ) -> QuotaCheckResult:
        """Check if tenant is within quota for a resource type

        Args:
            tenant_id: Tenant UUID
            resource_type: Type of resource (api_minute, api_hour, tasks_day, etc.)
            increment: Amount to check against quota

        Returns:
            QuotaCheckResult with allowed status and usage info
        """
        try:
            # Try Redis first for fast path
            if self.redis:
                return self._check_quota_redis(tenant_id, resource_type, increment)

            # Fall back to database
            if self.supabase:
                return self._check_quota_db(tenant_id, resource_type, increment)

        except Exception as e:
            logger.warning("Quota check failed, allowing request: %s", e)

        # Default to allowing if quota check fails
        return QuotaCheckResult(
            allowed=True,
            current_usage=0,
            quota_limit=0,
            remaining=0,
            resource_type=resource_type
        )

    def _check_quota_redis(
        self,
        tenant_id: str,
        resource_type: str,
        increment: int
    ) -> QuotaCheckResult:
        """Check quota using Redis for fast path"""
        quota = self.get_tenant_quota(tenant_id)

        # Map resource type to quota limit
        limit_map = {
            "api_minute": quota.api_requests_per_minute,
            "api_hour": quota.api_requests_per_hour,
            "api_day": quota.api_requests_per_day,
            "tasks_day": quota.max_tasks_per_day,
            "concurrent_tasks": quota.max_concurrent_tasks,
            "llm_tokens_day": quota.max_llm_tokens_per_day,
            "llm_requests_hour": quota.max_llm_requests_per_hour,
            "prs_day": quota.max_prs_per_day,
            "code_generations_hour": quota.max_code_generations_per_hour,
        }

        quota_limit = limit_map.get(resource_type, 1000)
        key = f"tenant_quota:{tenant_id}:{resource_type}"

        # Get current usage
        current = self.redis.get(key)
        current_usage = int(current) if current else 0

        allowed = (current_usage + increment) <= quota_limit
        remaining = max(0, quota_limit - current_usage - increment)

        return QuotaCheckResult(
            allowed=allowed,
            current_usage=current_usage,
            quota_limit=quota_limit,
            remaining=remaining,
            resource_type=resource_type
        )

    def _check_quota_db(
        self,
        tenant_id: str,
        resource_type: str,
        increment: int
    ) -> QuotaCheckResult:
        """Check quota using database"""
        result = self.supabase.rpc(
            "check_tenant_quota",
            {
                "p_tenant_id": tenant_id,
                "p_resource_type": resource_type,
                "p_increment": increment
            }
        ).execute()

        if result.data and len(result.data) > 0:
            row = result.data[0]
            return QuotaCheckResult(
                allowed=row.get("allowed", True),
                current_usage=row.get("current_usage", 0),
                quota_limit=row.get("quota_limit", 0),
                remaining=row.get("remaining", 0),
                resource_type=resource_type
            )

        return QuotaCheckResult(
            allowed=True,
            current_usage=0,
            quota_limit=0,
            remaining=0,
            resource_type=resource_type
        )

    def increment_usage(
        self,
        tenant_id: str,
        resource_type: str,
        increment: int = 1
    ) -> bool:
        """Increment usage counter for a tenant

        Args:
            tenant_id: Tenant UUID
            resource_type: Type of resource
            increment: Amount to increment

        Returns:
            True if successful
        """
        try:
            # Update Redis for fast path
            if self.redis:
                self._increment_usage_redis(tenant_id, resource_type, increment)

            # Update database for persistence
            if self.supabase:
                self.supabase.rpc(
                    "increment_tenant_usage",
                    {
                        "p_tenant_id": tenant_id,
                        "p_resource_type": resource_type,
                        "p_increment": increment
                    }
                ).execute()

            return True

        except Exception as e:
            logger.warning("Failed to increment tenant usage: %s", e)
            return False

    def _increment_usage_redis(
        self,
        tenant_id: str,
        resource_type: str,
        increment: int
    ):
        """Increment usage in Redis"""
        ttl_map = {
            "api_minute": 60,
            "api_hour": 3600,
            "api_day": 86400,
            "tasks_day": 86400,
            "concurrent_tasks": 3600,
            "llm_tokens_day": 86400,
            "llm_requests_hour": 3600,
            "prs_day": 86400,
            "code_generations_hour": 3600,
        }

        key = f"tenant_quota:{tenant_id}:{resource_type}"
        ttl = ttl_map.get(resource_type, 3600)

        pipe = self.redis.pipeline()
        pipe.incrby(key, increment)
        pipe.expire(key, ttl)
        pipe.execute()

    def get_usage_summary(self, tenant_id: str) -> dict:
        """Get usage summary for a tenant"""
        quota = self.get_tenant_quota(tenant_id)

        summary = {
            "tenant_id": tenant_id,
            "plan_tier": quota.plan_tier,
            "quotas": {},
            "usage": {},
            "remaining": {},
        }

        resource_types = [
            "api_minute", "api_hour", "api_day",
            "tasks_day", "llm_tokens_day", "prs_day"
        ]

        for resource_type in resource_types:
            result = self.check_quota(tenant_id, resource_type, 0)
            summary["quotas"][resource_type] = result.quota_limit
            summary["usage"][resource_type] = result.current_usage
            summary["remaining"][resource_type] = result.remaining

        return summary


# Global manager instance
_quota_manager: Optional[TenantQuotaManager] = None


def get_quota_manager() -> TenantQuotaManager:
    """Get or create the global quota manager"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = TenantQuotaManager()
    return _quota_manager


def _extract_tenant_id() -> Optional[str]:
    """Extract tenant ID from request context"""
    # Try request attributes
    tenant_id = getattr(request, 'tenant_id', None)
    if tenant_id:
        return str(tenant_id)

    # Try g context
    tenant_id = getattr(g, 'tenant_id', None)
    if tenant_id:
        return str(tenant_id)

    # Try current_user
    current_user = getattr(request, 'current_user', None)
    if isinstance(current_user, dict) and current_user.get('tenant_id'):
        return str(current_user['tenant_id'])

    return None


def tenant_rate_limit(resource_type: str = "api_minute"):
    """Decorator for tenant-level rate limiting

    Args:
        resource_type: Type of resource to rate limit

    Usage:
        @tenant_rate_limit("api_minute")
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = _extract_tenant_id()

            if not tenant_id:
                # No tenant context, fall back to IP-based limiting
                return f(*args, **kwargs)

            manager = get_quota_manager()
            result = manager.check_quota(tenant_id, resource_type)

            if not result.allowed:
                logger.warning(
                    "Tenant quota exceeded: tenant=%s resource=%s usage=%d/%d",
                    tenant_id, resource_type, result.current_usage, result.quota_limit
                )

                response = jsonify({
                    "error": {
                        "code": "tenant_quota_exceeded",
                        "message": "Tenant quota exceeded for %s" % resource_type,
                        "details": {
                            "resource_type": resource_type,
                            "current_usage": result.current_usage,
                            "quota_limit": result.quota_limit,
                            "remaining": result.remaining,
                        }
                    }
                })
                response.status_code = 429
                response.headers['X-Tenant-Quota-Limit'] = str(result.quota_limit)
                response.headers['X-Tenant-Quota-Remaining'] = str(result.remaining)
                return response

            # Increment usage
            manager.increment_usage(tenant_id, resource_type)

            # Add quota headers to response
            result = f(*args, **kwargs)

            # Try to add headers if response is a Flask response
            try:
                if hasattr(result, 'headers'):
                    check_result = manager.check_quota(tenant_id, resource_type, 0)
                    result.headers['X-Tenant-Quota-Limit'] = str(check_result.quota_limit)
                    result.headers['X-Tenant-Quota-Remaining'] = str(check_result.remaining)
            except Exception:
                pass

            return result

        return decorated_function
    return decorator


def check_tenant_quota(tenant_id: str, resource_type: str, increment: int = 1) -> QuotaCheckResult:
    """Convenience function to check tenant quota"""
    return get_quota_manager().check_quota(tenant_id, resource_type, increment)


def increment_tenant_usage(tenant_id: str, resource_type: str, increment: int = 1) -> bool:
    """Convenience function to increment tenant usage"""
    return get_quota_manager().increment_usage(tenant_id, resource_type, increment)
