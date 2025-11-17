"""
Tests for agent_registry models.

Tests cover:
- AgentType, AgentStatus, PermissionLevel, TaskStatus enums
- AgentStatistics model
- Agent model with validation
- AgentRegistrationRequest with validation
- AgentUpdateRequest
- AgentHealthMetrics, AgentHealthError, AgentHealth models
- Task model with validation
- TaskCreationRequest with validation
- TaskUpdateRequest
- Pagination model
- AgentListResponse, TaskListResponse models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestEnums:
    """Test enum classes"""
    
    def test_agent_type_values(self):
        """Should have all agent type values"""
        from models.agent_registry import AgentType
        
        assert AgentType.DEV_AGENT == "dev_agent"
        assert AgentType.OPS_AGENT == "ops_agent"
        assert AgentType.PM_AGENT == "pm_agent"
        assert AgentType.GROWTH_STRATEGIST == "growth_strategist"
        assert AgentType.META_AGENT == "meta_agent"
    
    def test_agent_status_values(self):
        """Should have all agent status values"""
        from models.agent_registry import AgentStatus
        
        assert AgentStatus.ACTIVE == "active"
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.BUSY == "busy"
        assert AgentStatus.OFFLINE == "offline"
        assert AgentStatus.ERROR == "error"
    
    def test_permission_level_values(self):
        """Should have all permission level values"""
        from models.agent_registry import PermissionLevel
        
        assert PermissionLevel.SANDBOX_ONLY == "sandbox_only"
        assert PermissionLevel.STAGING_ACCESS == "staging_access"
        assert PermissionLevel.PROD_LOW_RISK == "prod_low_risk"
        assert PermissionLevel.PROD_FULL_ACCESS == "prod_full_access"
    
    def test_task_status_values(self):
        """Should have all task status values"""
        from models.agent_registry import TaskStatus
        
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.ASSIGNED == "assigned"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"


class TestAgentStatistics:
    """Test AgentStatistics model"""
    
    def test_create_with_defaults(self):
        """Should create with default values"""
        from models.agent_registry import AgentStatistics
        
        stats = AgentStatistics()
        
        assert stats.pr_merged_count == 0
        assert stats.pr_reverted_count == 0
        assert stats.test_pass_count == 0
        assert stats.test_fail_count == 0
        assert stats.test_pass_rate == 0.0
    
    def test_create_with_values(self):
        """Should create with provided values"""
        from models.agent_registry import AgentStatistics
        
        stats = AgentStatistics(
            pr_merged_count=10,
            pr_reverted_count=2,
            test_pass_count=50,
            test_fail_count=5,
            test_pass_rate=0.91
        )
        
        assert stats.pr_merged_count == 10
        assert stats.pr_reverted_count == 2
        assert stats.test_pass_count == 50
        assert stats.test_fail_count == 5
        assert stats.test_pass_rate == 0.91
    
    def test_validates_non_negative_counts(self):
        """Should reject negative counts"""
        from models.agent_registry import AgentStatistics
        
        with pytest.raises(ValidationError):
            AgentStatistics(pr_merged_count=-1)
    
    def test_validates_pass_rate_range(self):
        """Should reject pass rate outside 0-1 range"""
        from models.agent_registry import AgentStatistics
        
        with pytest.raises(ValidationError):
            AgentStatistics(test_pass_rate=1.5)
        
        with pytest.raises(ValidationError):
            AgentStatistics(test_pass_rate=-0.1)


class TestAgent:
    """Test Agent model"""
    
    def test_create_agent(self):
        """Should create agent with required fields"""
        from models.agent_registry import Agent, AgentType, AgentStatus, PermissionLevel
        
        agent = Agent(
            agent_id="test-123",
            agent_type=AgentType.DEV_AGENT,
            status=AgentStatus.ACTIVE,
            permission_level=PermissionLevel.SANDBOX_ONLY,
            reputation_score=100
        )
        
        assert agent.agent_id == "test-123"
        assert agent.agent_type == AgentType.DEV_AGENT
        assert agent.status == AgentStatus.ACTIVE
        assert agent.permission_level == PermissionLevel.SANDBOX_ONLY
        assert agent.reputation_score == 100
        assert agent.capabilities == []
        assert agent.metadata == {}
    
    def test_validates_reputation_score_range(self):
        """Should reject reputation score outside 0-999 range"""
        from models.agent_registry import Agent, AgentType, AgentStatus, PermissionLevel
        
        with pytest.raises(ValidationError):
            Agent(
                agent_id="test-123",
                agent_type=AgentType.DEV_AGENT,
                status=AgentStatus.ACTIVE,
                permission_level=PermissionLevel.SANDBOX_ONLY,
                reputation_score=1000
            )
        
        with pytest.raises(ValidationError):
            Agent(
                agent_id="test-123",
                agent_type=AgentType.DEV_AGENT,
                status=AgentStatus.ACTIVE,
                permission_level=PermissionLevel.SANDBOX_ONLY,
                reputation_score=-1
            )
    
    def test_agent_with_statistics(self):
        """Should create agent with statistics"""
        from models.agent_registry import Agent, AgentType, AgentStatus, PermissionLevel, AgentStatistics
        
        stats = AgentStatistics(pr_merged_count=5, test_pass_rate=0.95)
        agent = Agent(
            agent_id="test-123",
            agent_type=AgentType.DEV_AGENT,
            status=AgentStatus.ACTIVE,
            permission_level=PermissionLevel.SANDBOX_ONLY,
            reputation_score=100,
            statistics=stats
        )
        
        assert agent.statistics.pr_merged_count == 5
        assert agent.statistics.test_pass_rate == 0.95
    
    def test_agent_json_serialization(self):
        """Should serialize to JSON with datetime formatting"""
        from models.agent_registry import Agent, AgentType, AgentStatus, PermissionLevel
        
        agent = Agent(
            agent_id="test-123",
            agent_type=AgentType.DEV_AGENT,
            status=AgentStatus.ACTIVE,
            permission_level=PermissionLevel.SANDBOX_ONLY,
            reputation_score=100
        )
        
        json_data = agent.model_dump()
        
        assert json_data['agent_id'] == "test-123"
        assert isinstance(json_data['created_at'], datetime)


class TestAgentRegistrationRequest:
    """Test AgentRegistrationRequest model"""
    
    def test_create_registration_request(self):
        """Should create registration request"""
        from models.agent_registry import AgentRegistrationRequest, AgentType
        
        request = AgentRegistrationRequest(
            agent_type=AgentType.DEV_AGENT,
            capabilities=["python", "testing"]
        )
        
        assert request.agent_type == AgentType.DEV_AGENT
        assert request.capabilities == ["python", "testing"]
        assert request.metadata == {}
    
    def test_validates_empty_capabilities(self):
        """Should reject empty capabilities list"""
        from models.agent_registry import AgentRegistrationRequest, AgentType
        
        with pytest.raises(ValidationError):
            AgentRegistrationRequest(
                agent_type=AgentType.DEV_AGENT,
                capabilities=[]
            )


class TestAgentUpdateRequest:
    """Test AgentUpdateRequest model"""
    
    def test_create_update_request(self):
        """Should create update request with optional fields"""
        from models.agent_registry import AgentUpdateRequest, AgentStatus
        
        request = AgentUpdateRequest(status=AgentStatus.BUSY)
        
        assert request.status == AgentStatus.BUSY
        assert request.capabilities is None
        assert request.metadata is None
    
    def test_create_empty_update_request(self):
        """Should create update request with no fields"""
        from models.agent_registry import AgentUpdateRequest
        
        request = AgentUpdateRequest()
        
        assert request.status is None
        assert request.capabilities is None
        assert request.metadata is None


class TestAgentHealthModels:
    """Test agent health models"""
    
    def test_agent_health_metrics(self):
        """Should create health metrics"""
        from models.agent_registry import AgentHealthMetrics
        
        metrics = AgentHealthMetrics(
            cpu_usage=45.5,
            memory_usage=60.0,
            active_tasks=3,
            queue_depth=10
        )
        
        assert metrics.cpu_usage == 45.5
        assert metrics.memory_usage == 60.0
        assert metrics.active_tasks == 3
        assert metrics.queue_depth == 10
    
    def test_validates_cpu_usage_range(self):
        """Should reject CPU usage outside 0-100 range"""
        from models.agent_registry import AgentHealthMetrics
        
        with pytest.raises(ValidationError):
            AgentHealthMetrics(cpu_usage=101.0)
    
    def test_agent_health_error(self):
        """Should create health error"""
        from models.agent_registry import AgentHealthError
        
        error = AgentHealthError(
            timestamp=datetime.utcnow(),
            error_type="connection_error",
            message="Failed to connect"
        )
        
        assert error.error_type == "connection_error"
        assert error.message == "Failed to connect"
    
    def test_agent_health(self):
        """Should create agent health status"""
        from models.agent_registry import AgentHealth, AgentStatus
        
        health = AgentHealth(
            agent_id="test-123",
            status=AgentStatus.ACTIVE,
            last_heartbeat=datetime.utcnow()
        )
        
        assert health.agent_id == "test-123"
        assert health.status == AgentStatus.ACTIVE
        assert health.errors == []
    
    def test_agent_health_report(self):
        """Should create health report"""
        from models.agent_registry import AgentHealthReport, AgentStatus, AgentHealthMetrics
        
        metrics = AgentHealthMetrics(cpu_usage=30.0)
        report = AgentHealthReport(
            status=AgentStatus.ACTIVE,
            metrics=metrics
        )
        
        assert report.status == AgentStatus.ACTIVE
        assert report.metrics.cpu_usage == 30.0


class TestTask:
    """Test Task model"""
    
    def test_create_task(self):
        """Should create task with required fields"""
        from models.agent_registry import Task, TaskStatus
        
        task = Task(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            task_type="bug_fix"
        )
        
        assert task.task_id == "task-123"
        assert task.status == TaskStatus.QUEUED
        assert task.task_type == "bug_fix"
        assert task.agent_id is None
        assert task.tenant_id is None
        assert task.payload == {}
    
    def test_task_with_all_fields(self):
        """Should create task with all fields"""
        from models.agent_registry import Task, TaskStatus
        
        now = datetime.utcnow()
        task = Task(
            task_id="task-123",
            status=TaskStatus.COMPLETED,
            agent_id="agent-456",
            tenant_id="tenant-789",
            task_type="deployment",
            payload={"env": "staging"},
            result={"success": True},
            error_message=None,
            created_at=now,
            assigned_at=now,
            started_at=now,
            completed_at=now
        )
        
        assert task.agent_id == "agent-456"
        assert task.tenant_id == "tenant-789"
        assert task.payload == {"env": "staging"}
        assert task.result == {"success": True}
    
    def test_task_json_serialization(self):
        """Should serialize to JSON with datetime formatting"""
        from models.agent_registry import Task, TaskStatus
        
        task = Task(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            task_type="bug_fix"
        )
        
        json_data = task.model_dump()
        
        assert json_data['task_id'] == "task-123"
        assert isinstance(json_data['created_at'], datetime)


class TestTaskCreationRequest:
    """Test TaskCreationRequest model"""
    
    def test_create_task_request(self):
        """Should create task creation request"""
        from models.agent_registry import TaskCreationRequest
        
        request = TaskCreationRequest(
            task_type="bug_fix",
            payload={"issue_id": "123"}
        )
        
        assert request.task_type == "bug_fix"
        assert request.payload == {"issue_id": "123"}
        assert request.tenant_id is None
    
    def test_validates_empty_task_type(self):
        """Should reject empty task type"""
        from models.agent_registry import TaskCreationRequest
        
        with pytest.raises(ValidationError):
            TaskCreationRequest(
                task_type="",
                payload={}
            )
    
    def test_strips_whitespace_from_task_type(self):
        """Should strip whitespace from task type"""
        from models.agent_registry import TaskCreationRequest
        
        request = TaskCreationRequest(
            task_type="  bug_fix  ",
            payload={}
        )
        
        assert request.task_type == "bug_fix"


class TestTaskUpdateRequest:
    """Test TaskUpdateRequest model"""
    
    def test_create_task_update_request(self):
        """Should create task update request"""
        from models.agent_registry import TaskUpdateRequest, TaskStatus
        
        request = TaskUpdateRequest(
            status=TaskStatus.COMPLETED,
            result={"success": True}
        )
        
        assert request.status == TaskStatus.COMPLETED
        assert request.result == {"success": True}
        assert request.error_message is None
    
    def test_create_empty_task_update_request(self):
        """Should create task update request with no fields"""
        from models.agent_registry import TaskUpdateRequest
        
        request = TaskUpdateRequest()
        
        assert request.status is None
        assert request.result is None
        assert request.error_message is None


class TestPagination:
    """Test Pagination model"""
    
    def test_create_pagination(self):
        """Should create pagination metadata"""
        from models.agent_registry import Pagination
        
        pagination = Pagination(
            page=1,
            page_size=20,
            total_items=100,
            total_pages=5
        )
        
        assert pagination.page == 1
        assert pagination.page_size == 20
        assert pagination.total_items == 100
        assert pagination.total_pages == 5
    
    def test_validates_page_minimum(self):
        """Should reject page less than 1"""
        from models.agent_registry import Pagination
        
        with pytest.raises(ValidationError):
            Pagination(
                page=0,
                page_size=20,
                total_items=100,
                total_pages=5
            )
    
    def test_validates_page_size_range(self):
        """Should reject page size outside 1-100 range"""
        from models.agent_registry import Pagination
        
        with pytest.raises(ValidationError):
            Pagination(
                page=1,
                page_size=0,
                total_items=100,
                total_pages=5
            )
        
        with pytest.raises(ValidationError):
            Pagination(
                page=1,
                page_size=101,
                total_items=100,
                total_pages=5
            )


class TestResponseModels:
    """Test response models"""
    
    def test_agent_list_response(self):
        """Should create agent list response"""
        from models.agent_registry import (
            AgentListResponse, Agent, Pagination,
            AgentType, AgentStatus, PermissionLevel
        )
        
        agent = Agent(
            agent_id="test-123",
            agent_type=AgentType.DEV_AGENT,
            status=AgentStatus.ACTIVE,
            permission_level=PermissionLevel.SANDBOX_ONLY,
            reputation_score=100
        )
        pagination = Pagination(
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1
        )
        
        response = AgentListResponse(
            agents=[agent],
            pagination=pagination
        )
        
        assert len(response.agents) == 1
        assert response.agents[0].agent_id == "test-123"
        assert response.pagination.page == 1
    
    def test_task_list_response(self):
        """Should create task list response"""
        from models.agent_registry import (
            TaskListResponse, Task, Pagination, TaskStatus
        )
        
        task = Task(
            task_id="task-123",
            status=TaskStatus.QUEUED,
            task_type="bug_fix"
        )
        pagination = Pagination(
            page=1,
            page_size=20,
            total_items=1,
            total_pages=1
        )
        
        response = TaskListResponse(
            tasks=[task],
            pagination=pagination
        )
        
        assert len(response.tasks) == 1
        assert response.tasks[0].task_id == "task-123"
        assert response.pagination.page == 1
