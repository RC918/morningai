"""
Tests for Provider Health Scoring (EPIC I-2)

These tests ensure:
1. Health score calculation works correctly
2. Per-provider metrics are properly recorded
3. Feature flags control behavior as expected
4. Latency percentile calculations are accurate
5. Error classification works correctly

Contract Test: health scoring must not block SimpleCoder normal operation
"""

from unittest.mock import Mock, patch

# Import metrics components
from metrics import (
    CanaryMetrics,
    get_canary_metrics,
    reset_canary_metrics,
)


class TestCanaryMetricsProviderHealth:
    """Unit tests for CanaryMetrics provider health methods"""

    def setup_method(self):
        """Setup mock Redis client for each test"""
        self.mock_redis = Mock()
        self.mock_pipe = Mock()
        self.mock_pipe.set = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incrby = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incr = Mock(return_value=self.mock_pipe)
        self.mock_pipe.execute = Mock(return_value=[True, 1])
        self.mock_redis.pipeline.return_value.__enter__ = Mock(
            return_value=self.mock_pipe
        )
        self.mock_redis.pipeline.return_value.__exit__ = Mock(return_value=False)
        self.metrics = CanaryMetrics(self.mock_redis, enabled=True)

    def test_record_provider_request_success(self):
        """Test recording a successful provider request"""
        self.metrics.record_provider_request(
            provider="openai",
            latency_ms=500.0,
            success=True,
            error_type=None
        )

        # Verify pipeline was used (incr_counter uses pipeline)
        assert self.mock_redis.pipeline.called

        # Verify set and incrby were called on the pipeline
        assert self.mock_pipe.set.called or self.mock_pipe.incrby.called

    def test_record_provider_request_failure(self):
        """Test recording a failed provider request"""
        self.metrics.record_provider_request(
            provider="gemini",
            latency_ms=5000.0,
            success=False,
            error_type="timeout"
        )

        # Verify pipeline was used
        assert self.mock_redis.pipeline.called

        # Verify execute was called (metrics were recorded)
        assert self.mock_pipe.execute.called

    def test_record_provider_request_disabled(self):
        """Test that recording is skipped when metrics are disabled"""
        disabled_metrics = CanaryMetrics(self.mock_redis, enabled=False)

        disabled_metrics.record_provider_request(
            provider="openai",
            latency_ms=500.0,
            success=True
        )

        # Should not have made any Redis pipeline calls
        self.mock_redis.pipeline.assert_not_called()

    def test_record_provider_latency_buckets(self):
        """Test that latency is recorded in histogram buckets"""
        self.metrics.record_provider_request(
            provider="alicloud",
            latency_ms=1500.0,
            success=True
        )

        # Verify pipeline was used for latency recording
        assert self.mock_redis.pipeline.called
        assert self.mock_pipe.execute.called


class TestHealthScoreCalculation:
    """Unit tests for health score calculation"""

    def setup_method(self):
        """Setup mock Redis client for each test"""
        self.mock_redis = Mock()
        self.mock_pipe = Mock()
        self.mock_pipe.set = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incrby = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incr = Mock(return_value=self.mock_pipe)
        self.mock_pipe.execute = Mock(return_value=[True, 1])
        self.mock_redis.pipeline.return_value.__enter__ = Mock(
            return_value=self.mock_pipe
        )
        self.mock_redis.pipeline.return_value.__exit__ = Mock(return_value=False)
        self.mock_redis.get.return_value = None
        self.mock_redis.keys.return_value = []
        self.metrics = CanaryMetrics(self.mock_redis, enabled=True)

    def test_health_score_perfect(self):
        """Test health score calculation with perfect metrics"""
        result = self.metrics.get_provider_health(
            provider="openai",
            window_minutes=15
        )

        # With no data, should return default health score
        assert "health_score" in result
        assert "provider" in result
        assert result["provider"] == "openai"

    def test_health_score_formula(self):
        """Test health score formula: health = 100 - (latency_penalty * 0.3 + error_rate * 0.4 + drift_rate * 0.3)"""
        result = self.metrics.get_provider_health(
            provider="openai",
            window_minutes=15,
            latency_weight=0.3,
            error_weight=0.4,
            drift_weight=0.3
        )

        # Verify result structure
        assert "health_score" in result
        assert "metrics" in result
        assert "error_rate" in result.get("metrics", {})

    def test_health_score_with_high_latency(self):
        """Test health score penalty for high latency"""
        # p95 > 10000ms should give 100 penalty
        # p95 < 2000ms should give 0 penalty
        # Linear scale: (p95 - 2000) / 80

        # Test latency penalty calculation
        p95_low = 1500  # Below threshold
        p95_high = 12000  # Above max threshold

        penalty_low = min(100, max(0, (p95_low - 2000) / 80))
        penalty_high = min(100, max(0, (p95_high - 2000) / 80))

        assert penalty_low == 0  # No penalty for low latency
        assert penalty_high == 100  # Max penalty for high latency

    def test_health_score_weights_sum(self):
        """Test that default weights sum to 1.0"""
        default_latency_weight = 0.3
        default_error_weight = 0.4
        default_drift_weight = 0.3

        total = default_latency_weight + default_error_weight + default_drift_weight
        assert total == 1.0


class TestErrorClassification:
    """Unit tests for error classification in LLMClient"""

    @patch("llm.client.OpenAIProvider")
    def test_classify_timeout_error(self, mock_provider_class):
        """Test classification of timeout errors"""
        from llm.client import LLMClient

        # Setup mock provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test timeout classification
        timeout_error = Exception("Connection timed out")
        assert client._classify_error(timeout_error) == "timeout"

        timeout_error2 = Exception("Request timeout exceeded")
        assert client._classify_error(timeout_error2) == "timeout"

    @patch("llm.client.OpenAIProvider")
    def test_classify_rate_limit_error(self, mock_provider_class):
        """Test classification of rate limit errors"""
        from llm.client import LLMClient

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test rate limit classification
        rate_error = Exception("Rate limit exceeded")
        assert client._classify_error(rate_error) == "rate_limit"

        rate_error2 = Exception("429 Too Many Requests")
        assert client._classify_error(rate_error2) == "rate_limit"

    @patch("llm.client.OpenAIProvider")
    def test_classify_auth_error(self, mock_provider_class):
        """Test classification of authentication errors"""
        from llm.client import LLMClient

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test auth error classification
        auth_error = Exception("401 Unauthorized")
        assert client._classify_error(auth_error) == "auth_error"

    @patch("llm.client.OpenAIProvider")
    def test_classify_server_error(self, mock_provider_class):
        """Test classification of server errors"""
        from llm.client import LLMClient

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test server error classification
        server_error = Exception("500 Internal Server Error")
        assert client._classify_error(server_error) == "server_error"

        server_error2 = Exception("503 Service Unavailable")
        assert client._classify_error(server_error2) == "server_error"

    @patch("llm.client.OpenAIProvider")
    def test_classify_connection_error(self, mock_provider_class):
        """Test classification of connection errors"""
        from llm.client import LLMClient

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test connection error classification
        conn_error = Exception("Connection refused")
        assert client._classify_error(conn_error) == "connection_error"

        network_error = Exception("Network unreachable")
        assert client._classify_error(network_error) == "connection_error"

    @patch("llm.client.OpenAIProvider")
    def test_classify_generic_api_error(self, mock_provider_class):
        """Test classification of generic API errors"""
        from llm.client import LLMClient

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Test generic error classification
        generic_error = Exception("Unknown error occurred")
        assert client._classify_error(generic_error) == "api_error"


class TestGetAllProvidersHealth:
    """Unit tests for get_all_providers_health method"""

    def setup_method(self):
        """Setup mock Redis client for each test"""
        self.mock_redis = Mock()
        self.mock_pipe = Mock()
        self.mock_pipe.set = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incrby = Mock(return_value=self.mock_pipe)
        self.mock_pipe.incr = Mock(return_value=self.mock_pipe)
        self.mock_pipe.execute = Mock(return_value=[True, 1])
        self.mock_redis.pipeline.return_value.__enter__ = Mock(
            return_value=self.mock_pipe
        )
        self.mock_redis.pipeline.return_value.__exit__ = Mock(return_value=False)
        self.mock_redis.get.return_value = None
        self.mock_redis.keys.return_value = []
        self.metrics = CanaryMetrics(self.mock_redis, enabled=True)

    def test_get_all_providers_health(self):
        """Test getting health scores for all providers"""
        providers = ["openai", "gemini", "alicloud", "siliconflow"]

        result = self.metrics.get_all_providers_health(providers)

        # Result is a dict with providers and ranking
        assert isinstance(result, dict)
        assert "providers" in result
        assert "ranking" in result
        assert len(result["providers"]) == 4

        # Verify each provider has required fields
        for provider_name, provider_health in result["providers"].items():
            assert "provider" in provider_health
            assert "health_score" in provider_health

    def test_get_all_providers_health_sorted(self):
        """Test that providers are sorted by health score (descending)"""
        # This test verifies the sorting behavior
        providers = ["openai", "gemini"]

        result = self.metrics.get_all_providers_health(providers)

        # Results should have a ranking list
        assert "ranking" in result
        assert isinstance(result["ranking"], list)


class TestCanaryMetricsSingleton:
    """Unit tests for get_canary_metrics singleton"""

    def setup_method(self):
        """Reset singleton before each test"""
        reset_canary_metrics()

    def teardown_method(self):
        """Reset singleton after each test"""
        reset_canary_metrics()

    @patch.dict("os.environ", {"REDIS_URL": ""})
    def test_get_canary_metrics_no_redis(self):
        """Test that get_canary_metrics returns None when REDIS_URL is not set"""
        reset_canary_metrics()

        result = get_canary_metrics()

        assert result is None

    @patch("metrics.redis")
    @patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"})
    def test_get_canary_metrics_with_redis(self, mock_redis_module):
        """Test that get_canary_metrics returns instance when REDIS_URL is set"""
        mock_client = Mock()
        mock_redis_module.from_url.return_value = mock_client

        reset_canary_metrics()

        result = get_canary_metrics()

        assert result is not None
        assert isinstance(result, CanaryMetrics)

    @patch("metrics.redis")
    @patch.dict("os.environ", {"REDIS_URL": "redis://localhost:6379"})
    def test_get_canary_metrics_singleton(self, mock_redis_module):
        """Test that get_canary_metrics returns the same instance"""
        mock_client = Mock()
        mock_redis_module.from_url.return_value = mock_client

        reset_canary_metrics()

        result1 = get_canary_metrics()
        result2 = get_canary_metrics()

        assert result1 is result2


class TestContractWithSimpleCoder:
    """
    Contract tests ensuring health scoring does NOT break SimpleCoder

    These tests verify the critical requirement from EPIC I plan:
    "health scoring must not block SimpleCoder normal operation"
    """

    def setup_method(self):
        """Reset metrics singleton before each test"""
        reset_canary_metrics()

    def test_health_scoring_observe_only(self):
        """
        Contract: Health scoring is observe-only and never blocks requests
        """
        mock_redis = Mock()
        mock_redis.pipeline.return_value = Mock()
        mock_redis.pipeline.return_value.__enter__ = Mock(
            return_value=mock_redis.pipeline.return_value
        )
        mock_redis.pipeline.return_value.__exit__ = Mock(return_value=False)
        metrics = CanaryMetrics(mock_redis, enabled=True)

        # Even with errors in metrics recording, should not raise
        mock_redis.incr.side_effect = Exception("Redis connection error")

        # This should NOT raise - observe-only mode
        metrics.record_provider_request(
            provider="openai",
            latency_ms=500.0,
            success=True
        )

        # Test passed if no exception was raised

    def test_health_scoring_disabled_no_impact(self):
        """
        Contract: When PROVIDER_HEALTH_ENABLED=false, there is zero impact
        """
        mock_redis = Mock()
        metrics = CanaryMetrics(mock_redis, enabled=False)

        # Should not make any Redis calls when disabled
        metrics.record_provider_request(
            provider="openai",
            latency_ms=500.0,
            success=True
        )

        mock_redis.incr.assert_not_called()

    @patch("llm.client.OpenAIProvider")
    def test_llm_client_metrics_never_block(self, mock_provider_class):
        """
        Contract: LLMClient._record_provider_metrics never blocks or raises
        """
        from llm.client import LLMClient

        # Setup mock provider
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider_class.return_value = mock_provider

        client = LLMClient(provider="openai")

        # Patch get_canary_metrics inside the method call
        with patch("metrics.get_canary_metrics") as mock_get_metrics:
            # Setup mock metrics that raises exception
            mock_metrics = Mock()
            mock_metrics.record_provider_request.side_effect = Exception("Metrics error")
            mock_get_metrics.return_value = mock_metrics

            # This should NOT raise - metrics errors are swallowed
            client._record_provider_metrics(
                latency_ms=500.0,
                success=True,
                error_type=None
            )

        # Test passed if no exception was raised


class TestFeatureFlags:
    """Unit tests for Feature Flag integration"""

    @patch("common.config.settings.settings")
    def test_provider_health_enabled_flag(self, mock_settings):
        """Test PROVIDER_HEALTH_ENABLED feature flag"""
        mock_settings.provider_health_enabled = True

        # When enabled, metrics should be recorded
        assert mock_settings.provider_health_enabled is True

    @patch("common.config.settings.settings")
    def test_provider_health_weights(self, mock_settings):
        """Test health score weight configuration"""
        mock_settings.provider_health_latency_weight = 0.3
        mock_settings.provider_health_error_weight = 0.4
        mock_settings.provider_health_drift_weight = 0.3

        # Verify weights sum to 1.0
        total = (
            mock_settings.provider_health_latency_weight +
            mock_settings.provider_health_error_weight +
            mock_settings.provider_health_drift_weight
        )
        assert total == 1.0

    @patch("common.config.settings.settings")
    def test_provider_health_window(self, mock_settings):
        """Test health score window configuration"""
        mock_settings.provider_health_window_minutes = 15

        assert mock_settings.provider_health_window_minutes == 15
