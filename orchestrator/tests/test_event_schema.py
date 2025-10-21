#!/usr/bin/env python3
"""Tests for event schema"""
import pytest

from orchestrator.schemas.event_schema import (
    AgentEvent, EventType, EventPriority,
    create_task_event, create_deploy_event, create_alert_event
)


class TestAgentEvent:
    """Test AgentEvent"""
    
    def test_create_event(self):
        """Test creating an event"""
        event = AgentEvent(
            event_type=EventType.TASK_CREATED,
            source_agent="dev_agent",
            task_id="task-123",
            payload={"type": "bugfix"}
        )
        
        assert event.event_id is not None
        assert event.event_type == EventType.TASK_CREATED
        assert event.source_agent == "dev_agent"
        assert event.task_id == "task-123"
    
    def test_event_to_dict(self):
        """Test converting event to dict"""
        event = AgentEvent(
            event_type=EventType.DEPLOY_STARTED,
            source_agent="ops_agent",
            payload={"deployment_id": "dep-456"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "deploy.started"
        assert event_dict["source_agent"] == "ops_agent"
        assert event_dict["priority"] == "medium"
    
    def test_event_from_dict(self):
        """Test creating event from dict"""
        data = {
            "event_id": "evt-123",
            "event_type": "alert.triggered",
            "priority": "critical",
            "source_agent": "ops_agent",
            "trace_id": "trace-456",
            "task_id": "task-789",
            "payload": {"severity": "critical"},
            "timestamp": "2025-10-21T10:00:00Z",
            "metadata": {}
        }
        
        event = AgentEvent.from_dict(data)
        
        assert event.event_id == "evt-123"
        assert event.event_type == EventType.ALERT_TRIGGERED
        assert event.priority == EventPriority.CRITICAL


class TestEventFactories:
    """Test event factory functions"""
    
    def test_create_task_event(self):
        """Test creating task event"""
        event = create_task_event(
            event_type="task.created",
            task_id="task-123",
            source_agent="dev_agent",
            payload={"type": "bugfix"}
        )
        
        assert event.event_type == EventType.TASK_CREATED
        assert event.task_id == "task-123"
        assert event.source_agent == "dev_agent"
    
    def test_create_deploy_event(self):
        """Test creating deploy event"""
        event = create_deploy_event(
            event_type="deploy.started",
            deployment_id="dep-123",
            source_agent="ops_agent",
            payload={"env": "production"}
        )
        
        assert event.event_type == EventType.DEPLOY_STARTED
        assert event.payload["deployment_id"] == "dep-123"
        assert event.priority == EventPriority.HIGH
    
    def test_create_alert_event_critical(self):
        """Test creating critical alert event"""
        event = create_alert_event(
            event_type="alert.triggered",
            alert_id="alert-123",
            severity="critical",
            source_agent="ops_agent",
            payload={"message": "System down"}
        )
        
        assert event.event_type == EventType.ALERT_TRIGGERED
        assert event.payload["alert_id"] == "alert-123"
        assert event.priority == EventPriority.CRITICAL
    
    def test_create_alert_event_low(self):
        """Test creating low priority alert event"""
        event = create_alert_event(
            event_type="alert.triggered",
            alert_id="alert-456",
            severity="low",
            source_agent="ops_agent",
            payload={"message": "Minor issue"}
        )
        
        assert event.priority == EventPriority.LOW
