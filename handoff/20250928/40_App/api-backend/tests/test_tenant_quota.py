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


class TestTenantQuotaManagerDB:
    """Tests for TenantQuotaManager with database operations"""

    def test_get_tenant_quota_from_db(self):
        """Test getting quota from database"""
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{
            "api_requests_per_minute": 120,
            "api_requests_per_hour": 2000,
            "api_requests_per_day": 20000,
            "max_concurrent_tasks": 10,
            "max_tasks_per_day": 200,
            "max_task_duration_seconds": 600,
            "max_storage_bytes": 2147483648,
            "max_documents": 2000,
            "max_embeddings": 20000,
            "max_llm_tokens_per_day": 200000,
            "max_llm_requests_per_hour": 200,
            "max_prs_per_day": 20,
            "max_code_generations_per_hour": 100,
            "plan_tier": "pro",
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        quota = manager.get_tenant_quota("test-tenant")

        assert quota.api_requests_per_minute == 120
        assert quota.plan_tier == "pro"
        mock_supabase.rpc.assert_called_once_with(
            "get_tenant_quota",
            {"p_tenant_id": "test-tenant"}
        )

    def test_get_tenant_quota_db_empty_result(self):
        """Test getting quota when DB returns empty result"""
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        quota = manager.get_tenant_quota("test-tenant")

        assert quota.tenant_id == "test-tenant"
        assert quota.api_requests_per_minute == 60
        assert quota.plan_tier == "free"

    def test_get_tenant_quota_db_exception(self):
        """Test getting quota when DB throws exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.side_effect = Exception("DB error")

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        quota = manager.get_tenant_quota("test-tenant")

        assert quota.tenant_id == "test-tenant"
        assert quota.api_requests_per_minute == 60

    def test_check_quota_db_fallback(self):
        """Test quota check falls back to DB when no Redis"""
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{
            "allowed": True,
            "current_usage": 25,
            "quota_limit": 100,
            "remaining": 75,
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        result = manager._check_quota_db("test-tenant", "api_minute", 1)

        assert result.allowed is True
        assert result.current_usage == 25
        assert result.quota_limit == 100

    def test_check_quota_db_empty_result(self):
        """Test quota check with empty DB result"""
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.rpc.return_value.execute.return_value = mock_result

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        result = manager._check_quota_db("test-tenant", "api_minute", 1)

        assert result.allowed is True
        assert result.current_usage == 0

    def test_increment_usage_with_db(self):
        """Test incrementing usage updates both Redis and DB"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_supabase = MagicMock()

        manager = TenantQuotaManager(
            redis_client=mock_redis,
            supabase_client=mock_supabase
        )
        result = manager.increment_usage("test-tenant", "api_minute", 1)

        assert result is True
        mock_supabase.rpc.assert_called_once_with(
            "increment_tenant_usage",
            {
                "p_tenant_id": "test-tenant",
                "p_resource_type": "api_minute",
                "p_increment": 1
            }
        )

    def test_increment_usage_db_only(self):
        """Test incrementing usage with DB only (no Redis)"""
        mock_supabase = MagicMock()

        manager = TenantQuotaManager(supabase_client=mock_supabase)
        result = manager.increment_usage("test-tenant", "api_minute", 1)

        assert result is True
        mock_supabase.rpc.assert_called_once()

    def test_increment_usage_exception(self):
        """Test incrementing usage handles exceptions"""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis error")

        manager = TenantQuotaManager(redis_client=mock_redis)
        result = manager.increment_usage("test-tenant", "api_minute", 1)

        assert result is False


class TestLazyLoading:
    """Tests for lazy loading of Redis and Supabase clients"""

    def test_redis_lazy_load_with_import_error(self):
        """Test Redis lazy loading handles import errors"""
        manager = TenantQuotaManager()
        manager._redis = None

        with patch(
            'src.utils.tenant_quota.TenantQuotaManager.redis',
            new_callable=lambda: property(lambda self: None)
        ):
            assert manager._redis is None

    def test_supabase_lazy_load_with_import_error(self):
        """Test Supabase lazy loading handles import errors"""
        manager = TenantQuotaManager()
        manager._supabase = None

        with patch(
            'src.utils.tenant_quota.TenantQuotaManager.supabase',
            new_callable=lambda: property(lambda self: None)
        ):
            assert manager._supabase is None


class TestExtractTenantId:
    """Tests for _extract_tenant_id function"""

    def test_extract_from_request_tenant_id(self):
        """Test extracting tenant_id from request attribute"""
        from flask import Flask
        from src.utils.tenant_quota import _extract_tenant_id

        app = Flask(__name__)
        with app.test_request_context():
            with patch('src.utils.tenant_quota.request') as mock_request:
                mock_request.tenant_id = "tenant-123"
                delattr(mock_request, 'current_user')
                result = _extract_tenant_id()
                assert result == "tenant-123"

    def test_extract_from_g_context(self):
        """Test extracting tenant_id from g context"""
        from flask import Flask
        from src.utils.tenant_quota import _extract_tenant_id

        app = Flask(__name__)
        with app.test_request_context():
            with patch('src.utils.tenant_quota.request') as mock_request, \
                 patch('src.utils.tenant_quota.g') as mock_g:
                mock_request.tenant_id = None
                delattr(mock_request, 'current_user')
                mock_g.tenant_id = "tenant-456"
                result = _extract_tenant_id()
                assert result == "tenant-456"

    def test_extract_from_current_user(self):
        """Test extracting tenant_id from current_user dict"""
        from flask import Flask
        from src.utils.tenant_quota import _extract_tenant_id

        app = Flask(__name__)
        with app.test_request_context():
            with patch('src.utils.tenant_quota.request') as mock_request, \
                 patch('src.utils.tenant_quota.g') as mock_g:
                mock_request.tenant_id = None
                mock_g.tenant_id = None
                mock_request.current_user = {"tenant_id": "tenant-789"}
                result = _extract_tenant_id()
                assert result == "tenant-789"

    def test_extract_returns_none(self):
        """Test extracting tenant_id returns None when not found"""
        from flask import Flask
        from src.utils.tenant_quota import _extract_tenant_id

        app = Flask(__name__)
        with app.test_request_context():
            with patch('src.utils.tenant_quota.request') as mock_request, \
                 patch('src.utils.tenant_quota.g') as mock_g:
                mock_request.tenant_id = None
                mock_g.tenant_id = None
                mock_request.current_user = {}
                result = _extract_tenant_id()
                assert result is None


class TestTenantRateLimitDecorator:
    """Tests for tenant_rate_limit decorator"""

    def test_decorator_no_tenant_context_required(self):
        """Test decorator returns 403 when no tenant context and require_tenant=True"""
        from src.utils.tenant_quota import tenant_rate_limit
        from flask import Flask

        app = Flask(__name__)

        @tenant_rate_limit("api_minute", require_tenant=True)
        def test_func():
            return "success"

        with app.app_context(), app.test_request_context():
            with patch('src.utils.tenant_quota._extract_tenant_id') as mock_extract:
                mock_extract.return_value = None
                result = test_func()
                assert result.status_code == 403

    def test_decorator_no_tenant_context_not_required(self):
        """Test decorator passes through when no tenant context and require_tenant=False"""
        from src.utils.tenant_quota import tenant_rate_limit

        @tenant_rate_limit("api_minute", require_tenant=False)
        def test_func():
            return "success"

        with patch('src.utils.tenant_quota._extract_tenant_id') as mock_extract:
            mock_extract.return_value = None
            result = test_func()
            assert result == "success"

    def test_decorator_quota_allowed(self):
        """Test decorator allows request when quota not exceeded"""
        from src.utils.tenant_quota import tenant_rate_limit

        @tenant_rate_limit("api_minute")
        def test_func():
            return "success"

        with patch('src.utils.tenant_quota._extract_tenant_id') as mock_extract, \
             patch('src.utils.tenant_quota.get_quota_manager') as mock_get_manager:
            mock_extract.return_value = "tenant-123"
            mock_manager = MagicMock()
            mock_manager.check_quota.return_value = QuotaCheckResult(
                allowed=True,
                current_usage=10,
                quota_limit=100,
                remaining=90,
                resource_type="api_minute"
            )
            mock_get_manager.return_value = mock_manager

            result = test_func()
            assert result == "success"
            mock_manager.increment_usage.assert_called_once()

    def test_decorator_quota_exceeded(self):
        """Test decorator returns 429 when quota exceeded"""
        from src.utils.tenant_quota import tenant_rate_limit
        from flask import Flask

        app = Flask(__name__)

        @tenant_rate_limit("api_minute")
        def test_func():
            return "success"

        with app.app_context(), app.test_request_context():
            with patch('src.utils.tenant_quota._extract_tenant_id') as mock_extract, \
                 patch('src.utils.tenant_quota.get_quota_manager') as mock_get_manager:
                mock_extract.return_value = "tenant-123"
                mock_manager = MagicMock()
                mock_manager.check_quota.return_value = QuotaCheckResult(
                    allowed=False,
                    current_usage=100,
                    quota_limit=100,
                    remaining=0,
                    resource_type="api_minute"
                )
                mock_get_manager.return_value = mock_manager

                result = test_func()
                assert result.status_code == 429


class TestGetQuotaManager:
    """Tests for get_quota_manager function"""

    def test_get_quota_manager_singleton(self):
        """Test get_quota_manager returns singleton"""
        from src.utils.tenant_quota import get_quota_manager
        import src.utils.tenant_quota as module

        module._quota_manager = None

        manager1 = get_quota_manager()
        manager2 = get_quota_manager()

        assert manager1 is manager2

        module._quota_manager = None
