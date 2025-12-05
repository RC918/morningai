"""
Audit Log - Structured Event Logging for Meta Agent

This module provides structured audit logging for tracking who approved what,
when, and what operations were performed during autonomous execution.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"

    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    TASK_RETRIED = "task_retried"

    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_TIMEOUT = "approval_timeout"

    POLICY_VIOLATION = "policy_violation"
    SAFETY_LIMIT_REACHED = "safety_limit_reached"

    HIGH_RISK_OPERATION = "high_risk_operation"
    OPERATION_BLOCKED = "operation_blocked"


@dataclass
class AuditEvent:
    """A single audit event"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    execution_id: str
    task_id: Optional[str] = None
    actor: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Structured audit logger for Meta Agent operations.

    Provides methods for logging various events with consistent structure,
    and supports multiple output handlers (console, file, external service).
    """

    def __init__(
        self,
        execution_id: str,
        actor: Optional[str] = None,
        handlers: Optional[List[Callable[[AuditEvent], None]]] = None,
    ):
        """
        Initialize the AuditLogger.

        Args:
            execution_id: The execution ID to associate with all events
            actor: Default actor (user/system) for events
            handlers: Optional list of event handlers for custom processing
        """
        self.execution_id = execution_id
        self.actor = actor or "system"
        self.handlers = handlers or []
        self.events: List[AuditEvent] = []
        self._event_counter = 0

        logger.info(
            "[AuditLogger] Initialized for execution %s (actor: %s)",
            execution_id, self.actor)

    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        self._event_counter += 1
        return f"{self.execution_id}-evt-{self._event_counter:04d}"

    def _emit_event(self, event: AuditEvent) -> None:
        """Emit an event to all handlers"""
        self.events.append(event)

        # Log to standard logger
        logger.info(
            "[AUDIT] %s | %s | task=%s | actor=%s | action=%s",
            event.event_type.value,
            event.execution_id,
            event.task_id or "N/A",
            event.actor or "N/A",
            event.action or "N/A",
        )

        # Call custom handlers
        for handler in self.handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("[AuditLogger] Handler failed: %s", e)

    def log_execution_started(
        self,
        goal_text: str,
        plan_id: str,
        task_count: int,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log execution start event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.EXECUTION_STARTED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            actor=self.actor,
            action="start_execution",
            details={
                "goal_text": goal_text[:200],
                "plan_id": plan_id,
                "task_count": task_count,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_execution_completed(
        self,
        status: str,
        tasks_completed: int,
        tasks_failed: int,
        duration_seconds: float,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log execution completion event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.EXECUTION_COMPLETED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            actor=self.actor,
            action="complete_execution",
            details={
                "status": status,
                "tasks_completed": tasks_completed,
                "tasks_failed": tasks_failed,
                "duration_seconds": duration_seconds,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_execution_failed(
        self,
        error: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log execution failure event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.EXECUTION_FAILED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            actor=self.actor,
            action="fail_execution",
            details={
                "error": error[:500],
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_task_started(
        self,
        task_id: str,
        task_type: str,
        description: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log task start event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.TASK_STARTED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=self.actor,
            action="start_task",
            details={
                "task_type": task_type,
                "description": description[:200],
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_task_completed(
        self,
        task_id: str,
        duration_seconds: float,
        outputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log task completion event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.TASK_COMPLETED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=self.actor,
            action="complete_task",
            details={
                "duration_seconds": duration_seconds,
                "outputs_keys": list((outputs or {}).keys()),
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_task_failed(
        self,
        task_id: str,
        error: str,
        attempt: int,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log task failure event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.TASK_FAILED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=self.actor,
            action="fail_task",
            details={
                "error": error[:500],
                "attempt": attempt,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_approval_requested(
        self,
        task_id: str,
        operation: str,
        resource: str,
        reason: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log approval request event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.APPROVAL_REQUESTED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=self.actor,
            action="request_approval",
            resource=resource,
            details={
                "operation": operation,
                "reason": reason,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_approval_granted(
        self,
        task_id: str,
        approver: str,
        operation: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log approval granted event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.APPROVAL_GRANTED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=approver,
            action="grant_approval",
            details={
                "operation": operation,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_approval_denied(
        self,
        task_id: str,
        denier: str,
        operation: str,
        reason: Optional[str] = None,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log approval denied event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.APPROVAL_DENIED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=denier,
            action="deny_approval",
            details={
                "operation": operation,
                "reason": reason,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_policy_violation(
        self,
        violation_type: str,
        details: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log policy violation event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.POLICY_VIOLATION,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            actor=self.actor,
            action="policy_violation",
            details={
                "violation_type": violation_type,
                "details": details,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_safety_limit_reached(
        self,
        limit_type: str,
        limit_value: Any,
        current_value: Any,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log safety limit reached event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SAFETY_LIMIT_REACHED,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            actor=self.actor,
            action="safety_limit_reached",
            details={
                "limit_type": limit_type,
                "limit_value": limit_value,
                "current_value": current_value,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def log_high_risk_operation(
        self,
        task_id: str,
        operation: str,
        resource: str,
        risk_level: str,
        **kwargs: Any,
    ) -> AuditEvent:
        """Log high-risk operation event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.HIGH_RISK_OPERATION,
            timestamp=datetime.now(),
            execution_id=self.execution_id,
            task_id=task_id,
            actor=self.actor,
            action="high_risk_operation",
            resource=resource,
            details={
                "operation": operation,
                "risk_level": risk_level,
                **kwargs,
            },
        )
        self._emit_event(event)
        return event

    def get_events(
        self,
        event_type: Optional[AuditEventType] = None,
        task_id: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Get filtered events"""
        events = self.events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if task_id:
            events = [e for e in events if e.task_id == task_id]

        return events

    def export_events(self) -> List[Dict[str, Any]]:
        """Export all events as dictionaries"""
        return [e.to_dict() for e in self.events]

    def export_json(self) -> str:
        """Export all events as JSON"""
        return json.dumps(self.export_events(), default=str, indent=2)
