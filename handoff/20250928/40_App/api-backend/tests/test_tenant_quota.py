"""Tests for Tenant Quota Management

Phase 4: Engineering Optimization (#1820)
"""
from unittest.mock import MagicMock, patch
from src.utils.tenant_quota import (
    TenantQuota,
    TenantUsage,
    QuotaCheckResult,
    TenantQuotaManager,
    PLAN_TIERS,
    check_tenant_quota,
    increment_tenant_usage,
)


class TestTenantQuota:
    """Tests for TenantQuota dataclass"""

    def test_default_values(self):
        """Test default quota values"""
        quota = TenantQuota(tenant_id="test-tenant")

        assert quota.tenant_id == "test-tenant"
        assert quota.api_requests_per_minute == 60
        assert quota.api_requests_per_hour == 1000
        assert quota.api_requests_per_day == 10000
        assert quota.max_concurrent_tasks == 5
        assert quota.max_tasks_per_day == 100
        assert quota.max_storage_bytes == 1073741824  # 1GB
        assert quota.plan_tier == "free"

    def test_custom_values(self):
        """Test custom quota values"""
        quota = TenantQuota(
            tenant_id="enterprise-tenant",
            api_requests_per_minute=300,
            max_concurrent_tasks=50,
            plan_tier="enterprise"
        )

        assert quota.api_requests_per_minute == 300
        assert quota.max_concurrent_tasks == 50
        assert quota.plan_tier == "enterprise"


class TestTenantUsage:
    """Tests for TenantUsage dataclass"""

    def test_default_values(self):
        """Test default usage values"""
        usage = TenantUsage(tenant_id="test-tenant")

        assert usage.tenant_id == "test-tenant"
        assert usage.api_requests_minute == 0
        assert usage.concurrent_tasks == 0
        assert usage.storage_bytes_used == 0


class TestQuotaCheckResult:
    """Tests for QuotaCheckResult dataclass"""

    def test_allowed_result(self):
        """Test allowed quota check result"""
        result = QuotaCheckResult(
            allowed=True,
            current_usage=50,
            quota_limit=100,
            remaining=50,
            resource_type="api_minute"
        )

        assert result.allowed is True
        assert result.remaining == 50

    def test_denied_result(self):
        """Test denied quota check result"""
        result = QuotaCheckResult(
            allowed=False,
            current_usage=100,
            quota_limit=100,
            remaining=0,
            resource_type="api_minute"
        )

        assert result.allowed is False
        assert result.remaining == 0


class TestPlanTiers:
    """Tests for plan tier configurations"""

    def test_free_tier_limits(self):
        """Test free tier has lower limits"""
        free = PLAN_TIERS["free"]
        pro = PLAN_TIERS["pro"]

        assert free["api_requests_per_minute"] < pro["api_requests_per_minute"]
        assert free["max_concurrent_tasks"] < pro["max_concurrent_tasks"]
        assert free["max_llm_tokens_per_day"] < pro["max_llm_tokens_per_day"]

    def test_enterprise_tier_highest(self):
        """Test enterprise tier has highest limits"""
        enterprise = PLAN_TIERS["enterprise"]

        assert enterprise["api_requests_per_minute"] == 300
        assert enterprise["max_concurrent_tasks"] == 50
        assert enterprise["max_llm_tokens_per_day"] == 2000000

    def test_all_tiers_have_required_keys(self):
        """Test all tiers have required configuration keys"""
        required_keys = [
            "api_requests_per_minute",
            "api_requests_per_hour",
            "api_requests_per_day",
            "max_concurrent_tasks",
            "max_tasks_per_day",
            "max_llm_tokens_per_day",
            "max_prs_per_day",
        ]

        for tier_name, tier_config in PLAN_TIERS.items():
            for key in required_keys:
                assert key in tier_config, f"Missing {key} in {tier_name} tier"


class TestTenantQuotaManager:
    """Tests for TenantQuotaManager"""

    def test_init_without_clients(self):
        """Test manager initialization without clients"""
        manager = TenantQuotaManager()

        assert manager._redis is None
        assert manager._supabase is None

    def test_init_with_clients(self):
        """Test manager initialization with clients"""
        mock_redis = MagicMock()
        mock_supabase = MagicMock()

        manager = TenantQuotaManager(
            redis_client=mock_redis,
            supabase_client=mock_supabase
        )

        assert manager._redis is mock_redis
        assert manager._supabase is mock_supabase

    def test_get_tenant_quota_default(self):
        """Test getting default quota when no DB record exists"""
        manager = TenantQuotaManager()

        quota = manager.get_tenant_quota("test-tenant")

        assert quota.tenant_id == "test-tenant"
        assert quota.api_requests_per_minute == 60
        assert quota.plan_tier == "free"

    def test_check_quota_redis(self):
        """Test quota check using Redis"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"50"

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.check_quota("test-tenant", "api_minute")

        assert result.allowed is True
        assert result.current_usage == 50
        assert result.quota_limit == 60  # Default free tier
        assert result.remaining == 9  # 60 - 50 - 1

    def test_check_quota_exceeds_limit(self):
        """Test quota check when limit is exceeded"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"60"

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.check_quota("test-tenant", "api_minute")

        assert result.allowed is False
        assert result.current_usage == 60
        assert result.remaining == 0

    def test_check_quota_no_usage(self):
        """Test quota check with no prior usage"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.check_quota("test-tenant", "api_minute")

        assert result.allowed is True
        assert result.current_usage == 0
        assert result.remaining == 59  # 60 - 0 - 1

    def test_increment_usage_redis(self):
        """Test incrementing usage in Redis"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.increment_usage("test-tenant", "api_minute")

        assert result is True
        mock_pipe.incrby.assert_called_once()
        mock_pipe.expire.assert_called_once()
        mock_pipe.execute.assert_called_once()

    def test_increment_usage_custom_increment(self):
        """Test incrementing usage with custom increment"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.increment_usage("test-tenant", "llm_tokens", 1000)

        assert result is True
        mock_pipe.incrby.assert_called_with(
            "tenant_quota:test-tenant:llm_tokens",
            1000
        )

    def test_get_usage_summary(self):
        """Test getting usage summary"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"10"

        manager = TenantQuotaManager(redis_client=mock_redis)

        summary = manager.get_usage_summary("test-tenant")

        assert summary["tenant_id"] == "test-tenant"
        assert summary["plan_tier"] == "free"
        assert "quotas" in summary
        assert "usage" in summary
        assert "remaining" in summary

    def test_check_quota_fallback_on_error(self):
        """Test quota check falls back to allowing on error"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")

        manager = TenantQuotaManager(redis_client=mock_redis)

        result = manager.check_quota("test-tenant", "api_minute")

        assert result.allowed is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    @patch('src.utils.tenant_quota.get_quota_manager')
    def test_check_tenant_quota(self, mock_get_manager):
        """Test check_tenant_quota convenience function"""
        mock_manager = MagicMock()
        mock_manager.check_quota.return_value = QuotaCheckResult(
            allowed=True,
            current_usage=10,
            quota_limit=100,
            remaining=90,
            resource_type="api_minute"
        )
        mock_get_manager.return_value = mock_manager

        result = check_tenant_quota("test-tenant", "api_minute")

        assert result.allowed is True
        mock_manager.check_quota.assert_called_once_with(
            "test-tenant", "api_minute", 1
        )

    @patch('src.utils.tenant_quota.get_quota_manager')
    def test_increment_tenant_usage(self, mock_get_manager):
        """Test increment_tenant_usage convenience function"""
        mock_manager = MagicMock()
        mock_manager.increment_usage.return_value = True
        mock_get_manager.return_value = mock_manager

        result = increment_tenant_usage("test-tenant", "api_minute", 5)

        assert result is True
        mock_manager.increment_usage.assert_called_once_with(
            "test-tenant", "api_minute", 5
        )


class TestResourceTypes:
    """Tests for different resource types"""

    def test_api_minute_ttl(self):
        """Test API minute has 60 second TTL"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        manager = TenantQuotaManager(redis_client=mock_redis)
        manager._increment_usage_redis("test-tenant", "api_minute", 1)

        # Check expire was called with 60 seconds
        mock_pipe.expire.assert_called_with(
            "tenant_quota:test-tenant:api_minute",
            60
        )

    def test_api_day_ttl(self):
        """Test API day has 86400 second TTL"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        manager = TenantQuotaManager(redis_client=mock_redis)
        manager._increment_usage_redis("test-tenant", "api_day", 1)

        # Check expire was called with 86400 seconds (1 day)
        mock_pipe.expire.assert_called_with(
            "tenant_quota:test-tenant:api_day",
            86400
        )
