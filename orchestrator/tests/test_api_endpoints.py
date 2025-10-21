#!/usr/bin/env python3
"""
Integration tests for API endpoints
Tests all FastAPI endpoints with proper authentication and mocking
"""
import pytest
import os

os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
os.environ["ORCHESTRATOR_API_KEY_TEST"] = "test-api-key-123:agent"

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from orchestrator.api.main import app
from orchestrator.api.auth import create_jwt_token, Role, AuthConfig
from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority, TaskStatus


@pytest.fixture(autouse=True)
def setup_env():
    """Setup environment variables for testing"""
    os.environ["ORCHESTRATOR_JWT_SECRET"] = "test-secret-key-for-testing-only-min-32-chars"
    AuthConfig.load_api_keys()
    AuthConfig.validate_config()
    yield


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


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


@pytest.fixture
def mock_redis_queue():
    """Mock Redis queue for testing"""
    with patch('orchestrator.api.main.redis_queue') as mock_queue:
        mock_queue.redis_client = AsyncMock()
        yield mock_queue


@pytest.fixture
def mock_orchestrator_router():
    """Mock orchestrator router"""
    with patch('orchestrator.api.main.orchestrator_router') as mock_router:
        from orchestrator.api.router import OrchestratorRouter
        real_router = OrchestratorRouter(MagicMock())
        mock_router.route_task = real_router.route_task
        yield mock_router


@pytest.fixture
def mock_hitl_gate():
    """Mock HITL gate"""
    with patch('orchestrator.api.main.hitl_gate') as mock_gate:
        yield mock_gate


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_service_info(self, client):
        """Test root endpoint returns service information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "MorningAI Orchestrator"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_root_no_authentication_required(self, client):
        """Test root endpoint doesn't require authentication"""
        response = client.get("/")
        assert response.status_code == 200


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client, mock_redis_queue):
        """Test health check returns healthy status"""
        mock_redis_queue.get_queue_stats = AsyncMock(return_value={
            "pending_tasks": 5,
            "processing_tasks": 3,
            "total_tasks": 8
        })
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis"] == "connected"
        assert "queue_stats" in data
        assert data["queue_stats"]["pending_tasks"] == 5
    
    def test_health_check_redis_failure(self, client, mock_redis_queue):
        """Test health check handles Redis failure"""
        mock_redis_queue.get_queue_stats = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        response = client.get("/health")
        
        assert response.status_code == 503


class TestTaskEndpoints:
    """Test task-related endpoints"""
    
    def test_create_task_success(self, client, agent_token, mock_redis_queue, mock_orchestrator_router):
        """Test creating a task successfully"""
        mock_redis_queue.enqueue_task = AsyncMock(return_value=True)
        
        response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "type": "bugfix",
                "payload": {"issue_id": "123", "description": "Fix bug"},
                "priority": "P1",
                "source": "user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
        assert "task" in data
        assert data["task"]["type"] == "bugfix"
    
    def test_create_task_requires_agent_role(self, client, user_token, mock_redis_queue):
        """Test creating task requires agent role"""
        response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "type": "bugfix",
                "payload": {"issue": "123"},
                "priority": "P2"
            }
        )
        
        assert response.status_code == 403
    
    def test_create_task_invalid_type(self, client, agent_token, mock_redis_queue, mock_orchestrator_router):
        """Test creating task with invalid type"""
        response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "type": "invalid_type",
                "payload": {"issue": "123"},
                "priority": "P2"
            }
        )
        
        assert response.status_code == 400
    
    def test_create_task_enqueue_failure(self, client, agent_token, mock_redis_queue, mock_orchestrator_router):
        """Test task creation when enqueue fails"""
        mock_redis_queue.enqueue_task = AsyncMock(return_value=False)
        
        response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "type": "bugfix",
                "payload": {"issue": "123"},
                "priority": "P2"
            }
        )
        
        assert response.status_code == 500
    
    def test_get_task_success(self, client, user_token, mock_redis_queue):
        """Test getting task by ID"""
        mock_task = UnifiedTask(
            task_id="test-123",
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1,
            payload={"issue": "123"}
        )
        mock_redis_queue.get_task = AsyncMock(return_value=mock_task)
        
        response = client.get(
            "/tasks/test-123",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["task_id"] == "test-123"
        assert data["task"]["type"] == "bugfix"
    
    def test_get_task_not_found(self, client, user_token, mock_redis_queue):
        """Test getting non-existent task"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.get(
            "/tasks/nonexistent",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404
    
    def test_get_task_requires_authentication(self, client, mock_redis_queue):
        """Test getting task requires authentication"""
        response = client.get("/tasks/test-123")
        assert response.status_code == 403
    
    def test_update_task_status_success(self, client, agent_token, mock_redis_queue):
        """Test updating task status"""
        mock_task = UnifiedTask(
            task_id="test-123",
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1,
            payload={"issue": "123"}
        )
        mock_redis_queue.get_task = AsyncMock(return_value=mock_task)
        mock_redis_queue.update_task = AsyncMock(return_value=True)
        mock_redis_queue.publish_event = AsyncMock(return_value=True)
        
        response = client.patch(
            "/tasks/test-123/status?status=completed",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "completed"
    
    def test_update_task_status_requires_agent(self, client, user_token, mock_redis_queue):
        """Test updating task status requires agent role"""
        response = client.patch(
            "/tasks/test-123/status?status=completed",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_update_task_status_not_found(self, client, agent_token, mock_redis_queue):
        """Test updating status of non-existent task"""
        mock_redis_queue.get_task = AsyncMock(return_value=None)
        
        response = client.patch(
            "/tasks/nonexistent/status?status=completed",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert response.status_code == 404


class TestEventEndpoints:
    """Test event-related endpoints"""
    
    def test_publish_event_success(self, client, agent_token, mock_redis_queue):
        """Test publishing an event"""
        mock_redis_queue.publish_event = AsyncMock(return_value=True)
        
        response = client.post(
            "/events/publish",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "event_type": "task.created",
                "source_agent": "dev_agent",
                "payload": {"task_id": "123"},
                "priority": "medium"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_type"] == "task.created"
    
    def test_publish_event_requires_agent(self, client, user_token, mock_redis_queue):
        """Test publishing event requires agent role"""
        response = client.post(
            "/events/publish",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "event_type": "task.created",
                "source_agent": "dev_agent",
                "payload": {"task_id": "123"}
            }
        )
        
        assert response.status_code == 403
    
    def test_publish_event_failure(self, client, agent_token, mock_redis_queue):
        """Test event publishing failure"""
        mock_redis_queue.publish_event = AsyncMock(return_value=False)
        
        response = client.post(
            "/events/publish",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "event_type": "task.created",
                "source_agent": "dev_agent",
                "payload": {"task_id": "123"}
            }
        )
        
        assert response.status_code == 500


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_stats_success(self, client, mock_redis_queue):
        """Test getting orchestrator statistics"""
        mock_redis_queue.get_queue_stats = AsyncMock(return_value={
            "pending_tasks": 10,
            "processing_tasks": 5,
            "total_tasks": 15
        })
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "queue" in data
        assert data["queue"]["pending_tasks"] == 10
        assert "timestamp" in data


class TestApprovalEndpoints:
    """Test HITL approval endpoints"""
    
    def test_get_pending_approvals(self, client, user_token, mock_hitl_gate):
        """Test getting pending approvals"""
        mock_hitl_gate.get_pending_approvals = AsyncMock(return_value=[
            {"approval_id": "app-1", "status": "pending"},
            {"approval_id": "app-2", "status": "pending"}
        ])
        
        response = client.get(
            "/approvals/pending",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["approvals"]) == 2
    
    def test_get_pending_approvals_requires_auth(self, client):
        """Test getting pending approvals requires authentication"""
        response = client.get("/approvals/pending")
        assert response.status_code == 403
    
    def test_get_approval_status(self, client, user_token, mock_hitl_gate):
        """Test getting approval status by ID"""
        mock_hitl_gate.get_approval_status = AsyncMock(return_value={
            "approval_id": "app-123",
            "status": "pending",
            "task_id": "task-456"
        })
        
        response = client.get(
            "/approvals/app-123",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["approval"]["approval_id"] == "app-123"
    
    def test_get_approval_status_not_found(self, client, user_token, mock_hitl_gate):
        """Test getting non-existent approval"""
        mock_hitl_gate.get_approval_status = AsyncMock(return_value=None)
        
        response = client.get(
            "/approvals/nonexistent",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 404
    
    def test_approve_request(self, client, agent_token, mock_hitl_gate):
        """Test approving a request"""
        mock_hitl_gate.approve = AsyncMock(return_value=True)
        
        response = client.post(
            "/approvals/app-123/approve",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["approval_id"] == "app-123"
    
    def test_approve_requires_agent(self, client, user_token, mock_hitl_gate):
        """Test approving requires agent role"""
        response = client.post(
            "/approvals/app-123/approve",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_approve_not_found(self, client, agent_token, mock_hitl_gate):
        """Test approving non-existent request"""
        mock_hitl_gate.approve = AsyncMock(return_value=False)
        
        response = client.post(
            "/approvals/nonexistent/approve",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert response.status_code == 404
    
    def test_reject_request(self, client, agent_token, mock_hitl_gate):
        """Test rejecting a request"""
        mock_hitl_gate.reject = AsyncMock(return_value=True)
        
        response = client.post(
            "/approvals/app-123/reject?reason=Not+ready",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["approval_id"] == "app-123"
    
    def test_reject_requires_agent(self, client, user_token, mock_hitl_gate):
        """Test rejecting requires agent role"""
        response = client.post(
            "/approvals/app-123/reject",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403
    
    def test_get_approval_history(self, client, user_token, mock_hitl_gate):
        """Test getting approval history"""
        mock_hitl_gate.get_approval_history = AsyncMock(return_value=[
            {"approval_id": "app-1", "status": "approved"},
            {"approval_id": "app-2", "status": "rejected"}
        ])
        
        response = client.get(
            "/approvals/history?limit=50",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["history"]) == 2


class TestEndpointIntegration:
    """Integration tests across multiple endpoints"""
    
    def test_task_lifecycle(self, client, agent_token, mock_redis_queue, mock_orchestrator_router):
        """Test complete task lifecycle"""
        mock_redis_queue.enqueue_task = AsyncMock(return_value=True)
        create_response = client.post(
            "/tasks",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "type": "bugfix",
                "payload": {"issue": "123"},
                "priority": "P2"
            }
        )
        assert create_response.status_code == 200
        task_id = create_response.json()["task_id"]
        
        mock_task = UnifiedTask(
            task_id=task_id,
            type=TaskType.BUGFIX,
            priority=TaskPriority.P2,
            payload={"issue": "123"}
        )
        mock_redis_queue.get_task = AsyncMock(return_value=mock_task)
        get_response = client.get(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert get_response.status_code == 200
        
        mock_redis_queue.update_task = AsyncMock(return_value=True)
        mock_redis_queue.publish_event = AsyncMock(return_value=True)
        update_response = client.patch(
            f"/tasks/{task_id}/status?status=completed",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        assert update_response.status_code == 200
    
    def test_authentication_across_endpoints(self, client, agent_token, mock_redis_queue):
        """Test authentication works across all endpoints"""
        endpoints = [
            ("/tasks/test-123", "get"),
            ("/stats", "get"),
            ("/approvals/pending", "get")
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {agent_token}"}
                )
            
            assert response.status_code != 401
            assert response.status_code != 403 or endpoint == "/approvals/pending"  # Some may return 404 or other codes
