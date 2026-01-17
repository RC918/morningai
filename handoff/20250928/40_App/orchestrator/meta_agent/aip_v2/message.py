"""
AIP v2 Message Schema

Blueprint Reference: Section 4.5 - Message Schema
"統一的 AgentMessage 格式（sender, receiver, payload, trace_id）"
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Optional
import uuid


# =============================================================================
# AIP v2 Protocol Version Constant
# =============================================================================

AIP_VERSION = "2.0"
"""Current AIP (Agent Interaction Protocol) version."""


# =============================================================================
# AIP v2 Core Enums
# =============================================================================


class MessagePriority(str, Enum):
    """Message priority levels as defined in Blueprint Section 4.5.

    Priority determines message processing order and timeout behavior:
    - CRITICAL: Immediate processing, no timeout (e.g., security incidents)
    - HIGH: Priority queue, short timeout (e.g., production issues)
    - NORMAL: Standard queue, normal timeout (e.g., code reviews)
    - LOW: Background queue, extended timeout (e.g., documentation)
    """
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class MessageType(str, Enum):
    """Types of messages in AIP v2 protocol.

    Categories:
    - Task messages: REQUEST, RESPONSE, PROGRESS
    - Control messages: HANDSHAKE, HEARTBEAT, ACK
    - Error messages: ERROR, RETRY
    - Context messages: CONTEXT_PUSH, CONTEXT_POP
    """
    REQUEST = "request"
    RESPONSE = "response"
    PROGRESS = "progress"
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    ERROR = "error"
    RETRY = "retry"
    CONTEXT_PUSH = "context_push"
    CONTEXT_POP = "context_pop"


# =============================================================================
# Task and Result Types
# =============================================================================


@dataclass
class AgentTask:
    """A task to be executed by an agent"""
    task_id: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    requires_approval: bool = False


@dataclass
class AgentResult:
    """Result from an agent task execution"""
    task_id: str
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# =============================================================================
# AIP v2 Message Schema
# =============================================================================


class MessageValidationError(Exception):
    """Exception raised when message validation fails.

    Note: This is duplicated here for use in from_dict validation.
    The canonical version is in validation.py.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


@dataclass
class AgentMessage:
    """Unified message format for all agent communication (AIP v2).

    Blueprint Reference: Section 4.5 - Message Schema
    "統一的 AgentMessage 格式（sender, receiver, payload, trace_id）"

    This is the core message format that all agents must use for communication.
    Every message includes tracing information for observability.

    Example:
        message = AgentMessage(
            sender="planner_agent",
            receiver="coding_agent",
            payload={"task": "implement feature X"},
            priority=MessagePriority.HIGH,
        )
    """
    sender: str
    receiver: str
    payload: Dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary.

        Validates sender/receiver format and handles malformed timestamps safely.

        Raises:
            MessageValidationError: If sender or receiver format is invalid.
        """
        valid_pattern = r"^[a-zA-Z][a-zA-Z0-9_-]*$"

        sender = data["sender"]
        receiver = data["receiver"]

        if not re.match(valid_pattern, sender):
            raise MessageValidationError(
                f"Invalid sender format in from_dict: {sender}", "sender"
            )
        if not re.match(valid_pattern, receiver):
            raise MessageValidationError(
                f"Invalid receiver format in from_dict: {receiver}", "receiver"
            )

        timestamp = datetime.now(timezone.utc)
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            sender=sender,
            receiver=receiver,
            payload=data["payload"],
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            message_type=MessageType(data.get("message_type", "request")),
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=timestamp,
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            ttl_seconds=data.get("ttl_seconds"),
            metadata=data.get("metadata", {}),
        )

    def create_response(
        self,
        payload: Dict[str, Any],
        success: bool = True,
    ) -> "AgentMessage":
        """Create a response message to this message.

        Note: The success parameter takes precedence over any 'success' key
        in the payload dict to ensure explicit intent is honored.
        """
        # Spread payload first, then success to ensure explicit parameter wins
        response_payload = {**payload, "success": success}
        return AgentMessage(
            sender=self.receiver,
            receiver=self.sender,
            payload=response_payload,
            trace_id=self.trace_id,
            message_type=MessageType.RESPONSE,
            priority=self.priority,
            correlation_id=self.trace_id,
            reply_to=self.trace_id,
            metadata=dict(self.metadata),  # Copy to prevent shared reference
        )

    def create_error_response(
        self,
        error_code: str,
        error_message: str,
        severity: Optional[str] = None,
    ) -> "AgentMessage":
        """Create an error response message.

        Args:
            severity: Error severity value (e.g., "error", "fatal").
                      Defaults to "error" if not provided.
        """
        severity_value = severity if severity is not None else "error"
        return AgentMessage(
            sender=self.receiver,
            receiver=self.sender,
            payload={
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
                "severity": severity_value,
            },
            trace_id=self.trace_id,
            message_type=MessageType.ERROR,
            priority=MessagePriority.HIGH,
            correlation_id=self.trace_id,
            reply_to=self.trace_id,
            metadata=dict(self.metadata),  # Copy to prevent shared reference
        )
