#!/usr/bin/env python3
"""
Unified Task Schema for Multi-Agent Orchestration
Defines the standard format for inter-agent communication
"""
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for different agent responsibilities"""
    FAQ = "faq"
    BUGFIX = "bugfix"
    DEPLOY = "deploy"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    ALERT = "alert"
    REFACTOR = "refactor"
    FEATURE = "feature"
    KB_UPDATE = "kb_update"


class TaskPriority(Enum):
    """Task priority levels"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TaskSource(Enum):
    """Task source (which agent or user created it)"""
    FAQ = "faq"
    OPS = "ops"
    DEV = "dev"
    USER = "user"
    SYSTEM = "system"
    WEBHOOK = "webhook"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class SLAConfig:
    """SLA configuration for task"""
    target: str
    deadline: str
    alert_threshold: Optional[int] = None


@dataclass
class UnifiedTask:
    """
    Unified Task Schema for inter-agent communication
    
    This is the contract that all agents (FAQ, Dev, Ops) use to communicate
    through the Orchestrator's event bus and task queue.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: Union[TaskType, str] = TaskType.FAQ
    priority: Union[TaskPriority, str] = TaskPriority.P2
    source: Union[TaskSource, str] = TaskSource.USER
    status: Union[TaskStatus, str] = TaskStatus.PENDING
    
    payload: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    sla: Optional[SLAConfig] = None
    
    assigned_to: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        result = asdict(self)
        result['type'] = self.type.value if isinstance(self.type, TaskType) else self.type
        result['priority'] = self.priority.value if isinstance(self.priority, TaskPriority) else self.priority
        result['source'] = self.source.value if isinstance(self.source, TaskSource) else self.source
        result['status'] = self.status.value if isinstance(self.status, TaskStatus) else self.status
        
        if self.sla:
            result['sla'] = {
                'target': self.sla.target,
                'deadline': self.sla.deadline,
                'alert_threshold': self.sla.alert_threshold
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedTask':
        """Create task from dictionary"""
        sla_data = data.pop('sla', None)
        sla = SLAConfig(**sla_data) if sla_data else None
        
        try:
            data['type'] = TaskType(data['type'])
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid type value '{data.get('type')}', keeping as string: {e}")
            pass
        
        try:
            data['priority'] = TaskPriority(data['priority'])
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid priority value '{data.get('priority')}', keeping as string: {e}")
            pass
        
        try:
            data['source'] = TaskSource(data['source'])
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid source value '{data.get('source')}', keeping as string: {e}")
            pass
        
        try:
            data['status'] = TaskStatus(data['status'])
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid status value '{data.get('status')}', keeping as string: {e}")
            pass
        
        data['sla'] = sla
        
        return cls(**data)
    
    def mark_assigned(self, agent: str):
        """Mark task as assigned to agent"""
        self.assigned_to = agent
        self.status = TaskStatus.ASSIGNED
    
    def mark_in_progress(self):
        """Mark task as in progress"""
        self.status = TaskStatus.IN_PROGRESS
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()
    
    def mark_completed(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
    
    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc).isoformat()
    
    def is_sla_violated(self) -> bool:
        """Check if SLA deadline is violated"""
        if not self.sla or not self.sla.deadline:
            return False
        
        deadline = datetime.fromisoformat(self.sla.deadline.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        return now > deadline and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]


def create_task(
    task_type: str,
    payload: Dict[str, Any],
    priority: str = "P2",
    source: str = "user",
    sla_target: Optional[str] = None,
    sla_deadline: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> UnifiedTask:
    """
    Factory function to create a UnifiedTask
    
    Args:
        task_type: Type of task (faq, bugfix, deploy, etc.)
        payload: Task-specific payload data
        priority: Task priority (P0, P1, P2, P3)
        source: Task source (faq, ops, dev, user, etc.)
        sla_target: SLA target description
        sla_deadline: SLA deadline in ISO8601 format
        parent_task_id: Parent task ID if this is a subtask
        metadata: Additional metadata
    
    Returns:
        UnifiedTask instance
    """
    sla = None
    if sla_target and sla_deadline:
        sla = SLAConfig(target=sla_target, deadline=sla_deadline)
    
    return UnifiedTask(
        type=TaskType(task_type),
        priority=TaskPriority(priority),
        source=TaskSource(source),
        payload=payload,
        sla=sla,
        parent_task_id=parent_task_id,
        metadata=metadata or {}
    )
