#!/usr/bin/env python3
"""Tests for task schema"""
import pytest
from datetime import datetime, timezone, timedelta

from orchestrator.schemas.task_schema import (
    UnifiedTask, TaskType, TaskPriority, TaskSource, TaskStatus,
    SLAConfig, create_task
)


class TestUnifiedTask:
    """Test UnifiedTask"""
    
    def test_create_task(self):
        """Test creating a task"""
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            priority=TaskPriority.P1,
            source=TaskSource.OPS,
            payload={"issue_id": "123"}
        )
        
        assert task.task_id is not None
        assert task.type == TaskType.BUGFIX
        assert task.priority == TaskPriority.P1
        assert task.source == TaskSource.OPS
        assert task.status == TaskStatus.PENDING
        assert task.payload == {"issue_id": "123"}
    
    def test_task_to_dict(self):
        """Test converting task to dict"""
        task = UnifiedTask(
            type=TaskType.DEPLOY,
            payload={"env": "production"}
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == task.task_id
        assert task_dict["type"] == "deploy"
        assert task_dict["priority"] == "P2"
        assert task_dict["payload"] == {"env": "production"}
    
    def test_task_from_dict(self):
        """Test creating task from dict"""
        data = {
            "task_id": "test-123",
            "type": "faq",
            "priority": "P0",
            "source": "user",
            "status": "pending",
            "payload": {"question": "How to deploy?"},
            "trace_id": "trace-456",
            "created_at": "2025-10-21T10:00:00Z"
        }
        
        task = UnifiedTask.from_dict(data)
        
        assert task.task_id == "test-123"
        assert task.type == TaskType.FAQ
        assert task.priority == TaskPriority.P0
        assert task.payload == {"question": "How to deploy?"}
    
    def test_mark_assigned(self):
        """Test marking task as assigned"""
        task = UnifiedTask(type=TaskType.BUGFIX)
        task.mark_assigned("dev_agent")
        
        assert task.assigned_to == "dev_agent"
        assert task.status == TaskStatus.ASSIGNED
    
    def test_mark_in_progress(self):
        """Test marking task as in progress"""
        task = UnifiedTask(type=TaskType.BUGFIX)
        task.mark_in_progress()
        
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
    
    def test_mark_completed(self):
        """Test marking task as completed"""
        task = UnifiedTask(type=TaskType.BUGFIX)
        task.mark_completed()
        
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_mark_failed(self):
        """Test marking task as failed"""
        task = UnifiedTask(type=TaskType.BUGFIX)
        task.mark_failed("Connection error")
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Connection error"
        assert task.completed_at is not None
    
    def test_sla_violation(self):
        """Test SLA violation check"""
        past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            sla=SLAConfig(target="P1 SLA", deadline=past_deadline)
        )
        
        assert task.is_sla_violated()
    
    def test_sla_not_violated(self):
        """Test SLA not violated"""
        future_deadline = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            sla=SLAConfig(target="P1 SLA", deadline=future_deadline)
        )
        
        assert not task.is_sla_violated()
    
    def test_sla_not_violated_when_completed(self):
        """Test SLA not violated when task is completed"""
        past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        task = UnifiedTask(
            type=TaskType.BUGFIX,
            sla=SLAConfig(target="P1 SLA", deadline=past_deadline)
        )
        task.mark_completed()
        
        assert not task.is_sla_violated()


class TestCreateTask:
    """Test create_task factory function"""
    
    def test_create_simple_task(self):
        """Test creating a simple task"""
        task = create_task(
            task_type="faq",
            payload={"question": "What is this?"},
            priority="P1"
        )
        
        assert task.type == TaskType.FAQ
        assert task.priority == TaskPriority.P1
        assert task.payload == {"question": "What is this?"}
    
    def test_create_task_with_sla(self):
        """Test creating task with SLA"""
        deadline = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        
        task = create_task(
            task_type="deploy",
            payload={"env": "production"},
            sla_target="Deploy SLA",
            sla_deadline=deadline
        )
        
        assert task.sla is not None
        assert task.sla.target == "Deploy SLA"
        assert task.sla.deadline == deadline
    
    def test_create_task_with_metadata(self):
        """Test creating task with metadata"""
        task = create_task(
            task_type="bugfix",
            payload={"bug_id": "456"},
            metadata={"repo": "morningai", "branch": "main"}
        )
        
        assert task.metadata == {"repo": "morningai", "branch": "main"}
