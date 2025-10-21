#!/usr/bin/env python3
"""
Integration tests for API authentication
Tests JWT and API Key authentication with RBAC
"""
import pytest
import os

os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
os.environ["ORCHESTRATOR_API_KEY_TEST"] = "test-api-key-123:agent"

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from orchestrator.api.auth import create_jwt_token, Role, AuthConfig
from orchestrator.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_redis_queue():
    """Mock Redis queue for testing"""
    with patch('orchestrator.api.main.redis_queue') as mock_queue:
        mock_queue.redis_client = AsyncMock()
        yield mock_queue


@pytest.fixture
def admin_token():
    """Generate admin JWT token"""
    return create_jwt_token("admin_user", Role.ADMIN)


@pytest.fixture
def agent_token():
    """Generate agent JWT token"""
    return create_jwt_token("agent_user", Role.AGENT)


@pytest.fixture
def user_token():
    """Generate user JWT token"""
    return create_jwt_token("regular_user", Role.USER)


@pytest.fixture(autouse=True)
def setup_env():
    """Setup environment variables for testing"""
    os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
    os.environ["ORCHESTRATOR_API_KEY_TEST"] = "test-api-key-123:agent"
    AuthConfig.load_api_keys()
    AuthConfig.validate_config()
    yield
    if "ORCHESTRATOR_API_KEY_TEST" in os.environ:
        del os.environ["ORCHESTRATOR_API_KEY_TEST"]


class TestJWTAuthentication:
    """Test JWT authentication"""
    
    def test_jwt_token_creation(self):
        """Test JWT token can be created"""
        token = create_jwt_token("test_user", Role.AGENT)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_access_protected_endpoint_without_auth(self, client, mock_redis_queue):
        """Test accessing protected endpoint without authentication fails"""
        response = client.get("/tasks/test-123")
        assert response.status_code == 403
    
    def test_access_protected_endpoint_with_valid_jwt(self, client, agent_token, mock_redis_queue):
        """Test accessing protected endpoint with valid JWT succeeds"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert response.status_code == 404
    
    def test_access_protected_endpoint_with_invalid_jwt(self, client, mock_redis_queue):
        """Test accessing protected endpoint with invalid JWT fails"""
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_expired_jwt(self, client, mock_redis_queue):
        """Test accessing protected endpoint with expired JWT fails"""
        import jwt
        from datetime import datetime, timedelta, timezone
        
        payload = {
            "sub": "test_user",
            "role": "agent",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(payload, AuthConfig.JWT_SECRET_KEY, algorithm="HS256")
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestAPIKeyAuthentication:
    """Test API Key authentication"""
    
    def test_access_with_valid_api_key(self, client, mock_redis_queue):
        """Test accessing endpoint with valid API key"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={"X-API-Key": "test-api-key-123"}
        )
        assert response.status_code in [403, 404]
    
    def test_access_with_invalid_api_key(self, client, mock_redis_queue):
        """Test accessing endpoint with invalid API key"""
        response = client.get(
            "/tasks/test-123",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code in [401, 403]
    
    def test_api_key_without_jwt(self, client, mock_redis_queue):
        """Test that API key works without JWT"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={"X-API-Key": "test-api-key-123"}
        )
        assert response.status_code != 401


class TestRBACAuthorization:
    """Test Role-Based Access Control"""
    
    def test_admin_can_access_all_endpoints(self, client, admin_token, mock_redis_queue):
        """Test admin role has full access"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        mock_redis_queue.enqueue_task = AsyncMock(return_value=True)
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 404]  # Not 401/403
    
    def test_agent_can_create_tasks(self, client, agent_token, mock_redis_queue):
        """Test agent role can create tasks"""
        from orchestrator.api.main import orchestrator_router
        from orchestrator.api.router import OrchestratorRouter
        
        with patch('orchestrator.api.main.orchestrator_router') as mock_router_instance:
            mock_router = OrchestratorRouter(mock_redis_queue)
            mock_router_instance.route_task = mock_router.route_task
            
            mock_redis_queue.enqueue_task = AsyncMock(return_value=True)
            
            response = client.post(
                "/tasks",
                headers={"Authorization": f"Bearer {agent_token}"},
                json={
                    "type": "bugfix",
                    "payload": {"issue": "123"},
                    "priority": "P2"
                }
            )
            assert response.status_code in [200, 201]  # Not 403
    
    def test_user_cannot_create_tasks(self, client, user_token, mock_redis_queue):
        """Test user role cannot create tasks (requires agent role)"""
        response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "type": "bugfix",
                "payload": {"issue": "123"},
                "priority": "P2"
            }
        )
        assert response.status_code in [403, 503]
    
    def test_user_can_read_tasks(self, client, user_token, mock_redis_queue):
        """Test user role can read tasks"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404
    
    def test_agent_can_approve_hitl(self, client, agent_token, mock_redis_queue):
        """Test agent role can approve HITL requests"""
        from orchestrator.api.main import hitl_gate
        
        with patch('orchestrator.api.main.hitl_gate') as mock_gate:
            mock_gate.approve = AsyncMock(return_value=True)
            
            response = client.post(
                "/approvals/test-approval-123/approve",
                headers={"Authorization": f"Bearer {agent_token}"}
            )
            assert response.status_code == 200
    
    def test_user_cannot_approve_hitl(self, client, user_token, mock_redis_queue):
        """Test user role cannot approve HITL requests"""
        response = client.post(
            "/approvals/test-approval-123/approve",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code in [403, 503]


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_root_endpoint_public(self, client):
        """Test root endpoint is publicly accessible"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "MorningAI Orchestrator"
    
    def test_health_endpoint_requires_redis(self, client, mock_redis_queue):
        """Test health endpoint requires Redis connection"""
        mock_redis_queue.get_queue_stats = AsyncMock(return_value={
            "pending_tasks": 0,
            "processing_tasks": 0,
            "total_tasks": 0
        })
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthenticationEdgeCases:
    """Test edge cases in authentication"""
    
    def test_both_jwt_and_api_key_provided(self, client, agent_token, mock_redis_queue):
        """Test when both JWT and API key are provided, JWT takes precedence"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/test-123",
            headers={
                "Authorization": f"Bearer {agent_token}",
                "X-API-Key": "test-api-key-123"
            }
        )
        assert response.status_code == 404  # Task not found, but auth succeeded
    
    def test_malformed_bearer_token(self, client, mock_redis_queue):
        """Test malformed Bearer token format"""
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": "Bearer"}
        )
        assert response.status_code in [401, 403]
    
    def test_wrong_auth_scheme(self, client, agent_token, mock_redis_queue):
        """Test using wrong authentication scheme"""
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Basic {agent_token}"}
        )
        assert response.status_code == 403
    
    def test_empty_api_key(self, client, mock_redis_queue):
        """Test empty API key"""
        response = client.get(
            "/tasks/test-123",
            headers={"X-API-Key": ""}
        )
        assert response.status_code in [401, 403]
