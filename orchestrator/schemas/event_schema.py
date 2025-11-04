#!/usr/bin/env python3
"""
Event Schema for Multi-Agent Event Bus
Defines events that agents publish and subscribe to
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import uuid


class EventType(Enum):
    """Event types published by agents"""
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    
    ISSUE_CREATED = "issue.created"
    ISSUE_UPDATED = "issue.updated"
    ISSUE_CLOSED = "issue.closed"
    
    PR_OPENED = "pr.opened"
    PR_MERGED = "pr.merged"
    PR_CLOSED = "pr.closed"
    PR_REVIEW_REQUESTED = "pr.review_requested"
    
    DEPLOY_STARTED = "deploy.started"
    DEPLOY_SUCCEEDED = "deploy.succeeded"
    DEPLOY_FAILED = "deploy.failed"
    DEPLOY_ROLLED_BACK = "deploy.rolled_back"
    
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_ACKNOWLEDGED = "alert.ack"
    ALERT_RESOLVED = "alert.resolved"
    
    KB_UPDATED = "kb.updated"
    KB_GAP_DETECTED = "kb.gap_detected"
    
    SLA_VIOLATION = "sla.violation"
    SLA_WARNING = "sla.warning"
    
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"
    
    CI_STARTED = "ci.started"
    CI_PASSED = "ci.passed"
    CI_FAILED = "ci.failed"


class EventPriority(Enum):
    """Event priority for routing and processing"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentEvent:
    """
    Standard event format for the event bus
    
    All agents publish events in this format, which other agents
    can subscribe to via the Orchestrator's event bus (Redis Pub/Sub).
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TASK_CREATED
    priority: EventPriority = EventPriority.MEDIUM
    
    source_agent: str = ""
    
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    
    payload: Dict[str, Any] = field(default_factory=dict)
    
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['priority'] = self.priority.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentEvent':
        """Create event from dictionary"""
        data['event_type'] = EventType(data['event_type'])
        data['priority'] = EventPriority(data['priority'])
        return cls(**data)


def create_task_event(
    event_type: str,
    task_id: str,
    source_agent: str,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
    priority: str = "medium"
) -> AgentEvent:
    """Create a task-related event"""
    return AgentEvent(
        event_type=EventType(event_type),
        source_agent=source_agent,
        task_id=task_id,
        trace_id=trace_id or str(uuid.uuid4()),
        payload=payload,
        priority=EventPriority(priority)
    )


def create_deploy_event(
    event_type: str,
    deployment_id: str,
    source_agent: str,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None
) -> AgentEvent:
    """Create a deployment-related event"""
    return AgentEvent(
        event_type=EventType(event_type),
        source_agent=source_agent,
        trace_id=trace_id or str(uuid.uuid4()),
        payload={
            "deployment_id": deployment_id,
            **payload
        },
        priority=EventPriority.HIGH
    )


def create_alert_event(
    event_type: str,
    alert_id: str,
    severity: str,
    source_agent: str,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None
) -> AgentEvent:
    """Create an alert-related event"""
    priority_map = {
        "critical": EventPriority.CRITICAL,
        "high": EventPriority.HIGH,
        "medium": EventPriority.MEDIUM,
        "low": EventPriority.LOW
    }
    
    return AgentEvent(
        event_type=EventType(event_type),
        source_agent=source_agent,
        trace_id=trace_id or str(uuid.uuid4()),
        payload={
            "alert_id": alert_id,
            "severity": severity,
            **payload
        },
        priority=priority_map.get(severity.lower(), EventPriority.MEDIUM)
    )
