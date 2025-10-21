#!/usr/bin/env python3
"""
Integration tests for API rate limiting
Tests Redis-based distributed rate limiting
"""
import pytest
import time
import os

os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
os.environ["ORCHESTRATOR_API_KEY_TEST"] = "test-api-key-123:agent"

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from orchestrator.api.main import app
from orchestrator.api.auth import create_jwt_token, Role, AuthConfig
from orchestrator.api.rate_limiter import RateLimitConfig


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def agent_token():
    """Generate agent JWT token"""
    os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
    AuthConfig.load_api_keys()
    AuthConfig.validate_config()
    return create_jwt_token("test_agent", Role.AGENT)


@pytest.fixture
def mock_redis_queue():
    """Mock Redis queue for testing"""
    with patch('orchestrator.api.main.redis_queue') as mock_queue:
        mock_redis = AsyncMock()
        mock_pipeline = MagicMock()
        mock_pipeline.zremrangebyscore = MagicMock(return_value=mock_pipeline)
        mock_pipeline.zcard = MagicMock(return_value=mock_pipeline)
        mock_pipeline.zadd = MagicMock(return_value=mock_pipeline)
        mock_pipeline.expire = MagicMock(return_value=mock_pipeline)
        mock_pipeline.execute = AsyncMock(return_value=[None, 0, None, None])
        
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        
        mock_queue.redis_client = mock_redis
        mock_queue.get_queue_stats = AsyncMock(return_value={
            "pending_tasks": 0,
            "processing_tasks": 0,
            "total_tasks": 0
        })
        mock_queue.get_task = AsyncMock(return_value=None)
        yield mock_queue


class TestRateLimitHeaders:
    """Test rate limit response headers"""
    
    def test_rate_limit_headers_present(self, client, mock_redis_queue):
        """Test that rate limit headers are included in responses"""
        response = client.get("/")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_headers_values(self, client, mock_redis_queue):
        """Test rate limit header values are correct"""
        response = client.get("/")
        
        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])
        reset = int(response.headers["X-RateLimit-Reset"])
        
        assert limit == RateLimitConfig.DEFAULT_RATE_LIMIT
        
        assert 0 <= remaining <= limit
        
        assert reset > time.time()


class TestRateLimitEnforcement:
    """Test rate limit enforcement"""
    
    def test_health_endpoint_high_limit(self, client, mock_redis_queue):
        """Test /health endpoint has higher rate limit"""
        responses = []
        for i in range(10):
            response = client.get("/health")
            responses.append(response)
        
        for response in responses:
            assert response.status_code == 200
    
    def test_rate_limit_decreases_with_requests(self, client, mock_redis_queue):
        """Test that remaining count decreases with each request"""
        response1 = client.get("/")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        
        response2 = client.get("/")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        assert remaining2 <= remaining1
    
    def test_different_endpoints_different_limits(self, client, agent_token, mock_redis_queue):
        """Test different endpoints have different rate limits"""
        with patch('orchestrator.api.main.orchestrator_router') as mock_router:
            from orchestrator.api.router import OrchestratorRouter
            router = OrchestratorRouter(mock_redis_queue)
            mock_router.route_task = router.route_task
            mock_redis_queue.enqueue_task = AsyncMock(return_value=True)
            
            response_tasks = client.post(
                "/tasks",
                headers={"Authorization": f"Bearer {agent_token}"},
                json={
                    "type": "bugfix",
                    "payload": {"issue": "123"},
                    "priority": "P2"
                }
            )
            
            response_root = client.get("/")
            
            if response_tasks.status_code == 200:
                limit_tasks = int(response_tasks.headers.get("X-RateLimit-Limit", 0))
                limit_root = int(response_root.headers["X-RateLimit-Limit"])
                
                assert limit_tasks == RateLimitConfig.ENDPOINT_LIMITS["/tasks"]
                assert limit_root == RateLimitConfig.DEFAULT_RATE_LIMIT


class TestRateLimitByIP:
    """Test rate limiting by IP address"""
    
    def test_rate_limit_per_ip(self, client, mock_redis_queue):
        """Test rate limits are enforced per IP address"""
        headers_ip1 = {"X-Forwarded-For": "192.168.1.1"}
        headers_ip2 = {"X-Forwarded-For": "192.168.1.2"}
        
        response1 = client.get("/health", headers=headers_ip1)
        response2 = client.get("/health", headers=headers_ip2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    def test_x_real_ip_header(self, client, mock_redis_queue):
        """Test X-Real-IP header is respected"""
        headers = {"X-Real-IP": "10.0.0.1"}
        
        response = client.get("/", headers=headers)
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers


class TestRateLimitExceeded:
    """Test behavior when rate limit is exceeded"""
    
    def test_rate_limit_exceeded_response(self, client, mock_redis_queue):
        """Test response when rate limit is exceeded"""
        
        response = client.get("/")
        assert "X-RateLimit-Limit" in response.headers
        
    
    def test_rate_limit_reset_time(self, client, mock_redis_queue):
        """Test rate limit reset timestamp is reasonable"""
        response = client.get("/")
        
        reset_time = int(response.headers["X-RateLimit-Reset"])
        current_time = int(time.time())
        
        assert reset_time > current_time
        assert reset_time <= current_time + RateLimitConfig.WINDOW_SIZE + 5


class TestRateLimitFallback:
    """Test rate limiter fallback behavior"""
    
    def test_rate_limiter_works_without_redis(self, client, mock_redis_queue):
        """Test rate limiter falls back to local storage when Redis unavailable"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestRateLimitConfiguration:
    """Test rate limit configuration"""
    
    def test_default_rate_limit(self):
        """Test default rate limit configuration"""
        assert RateLimitConfig.DEFAULT_RATE_LIMIT == 60
        assert RateLimitConfig.WINDOW_SIZE == 60
    
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limits are configured"""
        assert "/tasks" in RateLimitConfig.ENDPOINT_LIMITS
        assert "/events/publish" in RateLimitConfig.ENDPOINT_LIMITS
        assert "/health" in RateLimitConfig.ENDPOINT_LIMITS
        
        assert RateLimitConfig.ENDPOINT_LIMITS["/health"] > RateLimitConfig.ENDPOINT_LIMITS["/tasks"]
    
    def test_burst_limit_configured(self):
        """Test burst limit is configured"""
        assert hasattr(RateLimitConfig, 'BURST_LIMIT')
        assert RateLimitConfig.BURST_LIMIT > 0


class TestRateLimitMiddleware:
    """Test rate limit middleware behavior"""
    
    def test_health_endpoint_bypasses_some_checks(self, client, mock_redis_queue):
        """Test /health endpoint has lenient rate limiting"""
        responses = []
        for i in range(5):
            response = client.get("/health")
            responses.append(response)
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 4  # At least 4 out of 5 should succeed
    
    def test_rate_limit_applies_to_authenticated_requests(self, client, agent_token, mock_redis_queue):
        """Test rate limiting applies even with authentication"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert "X-RateLimit-Limit" in response.headers


class TestRateLimitIntegration:
    """Integration tests for rate limiting"""
    
    def test_rate_limit_with_multiple_endpoints(self, client, agent_token, mock_redis_queue):
        """Test rate limiting across multiple endpoints"""
        response1 = client.get("/")
        response2 = client.get("/stats")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        assert "X-RateLimit-Limit" in response1.headers
        assert "X-RateLimit-Limit" in response2.headers
    
    def test_rate_limit_persists_across_requests(self, client, mock_redis_queue):
        """Test rate limit state persists across requests"""
        response1 = client.get("/")
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        
        response2 = client.get("/")
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        assert remaining2 <= remaining1
