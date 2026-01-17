"""
Agent Protocol - AIP v2 (Agent Interaction Protocol v2) Implementation

This module implements the complete AIP v2 specification as defined in
MorningAI Ecosystem Blueprint 2025 Final, Section 4.5.

AIP v2 Components:
- Message Schema: Unified AgentMessage format (sender, receiver, payload, trace_id)
- Handshake Protocol: Agent startup capability declaration and verification
- Error Propagation: Standardized error passing and recovery mechanism
- Context Passing: Cross-agent context passing specification
- Priority Levels: Message priority (CRITICAL, HIGH, NORMAL, LOW)

All agents must implement AIP v2 interface to join the MorningAI ecosystem.

Blueprint Reference: Section 4.5 - Agent Interaction Protocol v2 (AIP v2)
Issue: #4098 - EPIC K P3: AIP v2 Complete Message Schema
Original Issue: #1821 - Meta Agent 自主任務規劃與執行

Note: Issue #4139 introduced a modular structure in the `aip_v2/` subpackage.
New code can import from `meta_agent.aip_v2` for cleaner organization:
    from meta_agent.aip_v2 import AgentMessage, AIPv2Agent, MessageValidator
This file is kept for backward compatibility with existing imports.
"""

from abc import abstractmethod  # noqa: F401 - kept for future use in base classes
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import uuid


# =============================================================================
# AIP v2 Protocol Version Constant
# =============================================================================

AIP_VERSION = "2.0"
"""Current AIP (Agent Interaction Protocol) version."""


# =============================================================================
# AIP v2 Core Enums (Blueprint Section 4.5)
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


class ErrorSeverity(str, Enum):
    """Error severity levels for error propagation.

    Determines how errors are handled and escalated:
    - FATAL: Unrecoverable, requires human intervention
    - ERROR: Recoverable with retry or fallback
    - WARNING: Non-blocking, logged for monitoring
    - INFO: Informational, no action required
    """
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class HandshakeStatus(str, Enum):
    """Status of agent handshake process."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class AgentCapability(Enum):
    """Capabilities that agents can have.

    Blueprint Reference: Section 3.3 - Agent Catalog V2
    These capabilities map to the 13 agent types defined in the Blueprint.
    """
    CODE_ANALYSIS = "code_analysis"
    CODE_WRITING = "code_writing"
    CODE_REVIEW = "code_review"
    TEST_WRITING = "test_writing"
    TEST_EXECUTION = "test_execution"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    DATABASE_OPERATIONS = "database_operations"
    UI_ANALYSIS = "ui_analysis"
    UX_EVALUATION = "ux_evaluation"
    RISK_ASSESSMENT = "risk_assessment"
    GOVERNANCE = "governance"


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
# AIP v2 Message Schema (Blueprint Section 4.5)
# =============================================================================


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
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> "AgentMessage":
        """Create an error response message."""
        return AgentMessage(
            sender=self.receiver,
            receiver=self.sender,
            payload={
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
                "severity": severity.value,
            },
            trace_id=self.trace_id,
            message_type=MessageType.ERROR,
            priority=MessagePriority.HIGH,
            correlation_id=self.trace_id,
            reply_to=self.trace_id,
            metadata=dict(self.metadata),  # Copy to prevent shared reference
        )


# =============================================================================
# AIP v2 Handshake Protocol (Blueprint Section 4.5)
# =============================================================================


@dataclass
class CapabilityDeclaration:
    """Declaration of agent capabilities during handshake.

    Blueprint Reference: Section 4.5 - Handshake Protocol
    "Agent 啟動時的能力宣告與驗證"
    """
    capability: AgentCapability
    version: str = "1.0"
    constraints: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert capability declaration to dictionary."""
        return {
            "capability": self.capability.value,
            "version": self.version,
            "constraints": self.constraints,
            "rate_limit": self.rate_limit,
        }


@dataclass
class AgentHandshake:
    """Handshake message for agent registration and capability declaration.

    Blueprint Reference: Section 4.5 - Handshake Protocol
    When an agent starts up, it must declare its capabilities and be verified
    before it can participate in the MorningAI ecosystem.

    Example:
        handshake = AgentHandshake(
            agent_id="coding_agent_001",
            agent_type="coding",
            capabilities=[
                CapabilityDeclaration(AgentCapability.CODE_WRITING),
                CapabilityDeclaration(AgentCapability.CODE_ANALYSIS),
            ],
        )
    """
    agent_id: str
    agent_type: str
    capabilities: List[CapabilityDeclaration]
    protocol_version: str = AIP_VERSION
    status: HandshakeStatus = HandshakeStatus.PENDING
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    supported_message_types: List[MessageType] = field(
        default_factory=lambda: [MessageType.REQUEST, MessageType.RESPONSE]
    )

    def to_message(self, orchestrator_id: str = "orchestrator") -> AgentMessage:
        """Convert handshake to AgentMessage for transmission."""
        return AgentMessage(
            sender=self.agent_id,
            receiver=orchestrator_id,
            payload={
                "agent_type": self.agent_type,
                "capabilities": [cap.to_dict() for cap in self.capabilities],
                "protocol_version": self.protocol_version,
                "supported_message_types": [mt.value for mt in self.supported_message_types],
            },
            message_type=MessageType.HANDSHAKE,
            priority=MessagePriority.HIGH,
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert handshake to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "protocol_version": self.protocol_version,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "supported_message_types": [mt.value for mt in self.supported_message_types],
        }


@dataclass
class HandshakeResponse:
    """Response to agent handshake request."""
    agent_id: str
    status: HandshakeStatus
    assigned_queue: Optional[str] = None
    rate_limits: Dict[str, int] = field(default_factory=dict)
    rejection_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_message(self, orchestrator_id: str = "orchestrator") -> AgentMessage:
        """Convert response to AgentMessage."""
        return AgentMessage(
            sender=orchestrator_id,
            receiver=self.agent_id,
            payload={
                "status": self.status.value,
                "assigned_queue": self.assigned_queue,
                "rate_limits": self.rate_limits,
                "rejection_reason": self.rejection_reason,
            },
            message_type=MessageType.HANDSHAKE_ACK,
            priority=MessagePriority.HIGH,
        )


# =============================================================================
# AIP v2 Error Propagation (Blueprint Section 4.5)
# =============================================================================


@dataclass
class AgentError:
    """Standardized error format for error propagation.

    Blueprint Reference: Section 4.5 - Error Propagation
    "標準化的錯誤傳遞與回復機制"

    Example:
        error = AgentError(
            error_code="TASK_TIMEOUT",
            message="Task execution exceeded timeout",
            severity=ErrorSeverity.ERROR,
            source_agent="coding_agent",
            recoverable=True,
            retry_after_seconds=30,
        )
    """
    error_code: str
    message: str
    severity: ErrorSeverity
    source_agent: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recoverable: bool = True
    retry_after_seconds: Optional[int] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    caused_by: Optional["AgentError"] = None

    def to_dict(self, max_depth: int = 10) -> Dict[str, Any]:
        """Convert error to dictionary with depth limiting.

        Args:
            max_depth: Maximum recursion depth for caused_by chain (default: 10).
                       Prevents stack overflow on deeply nested error chains.
        """
        caused_by_dict = None
        if self.caused_by and max_depth > 0:
            caused_by_dict = self.caused_by.to_dict(max_depth=max_depth - 1)
        elif self.caused_by and max_depth <= 0:
            caused_by_dict = {
                "error_code": self.caused_by.error_code,
                "message": "[truncated: max depth exceeded]",
            }

        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "source_agent": self.source_agent,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "retry_after_seconds": self.retry_after_seconds,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "caused_by": caused_by_dict,
        }

    def to_message(self, receiver: str) -> AgentMessage:
        """Convert error to AgentMessage for transmission."""
        return AgentMessage(
            sender=self.source_agent,
            receiver=receiver,
            payload=self.to_dict(),
            trace_id=self.trace_id,
            message_type=MessageType.ERROR,
            priority=MessagePriority.HIGH if self.severity == ErrorSeverity.FATAL
            else MessagePriority.NORMAL,
        )


class ErrorPropagationPolicy(str, Enum):
    """Policies for error propagation between agents."""
    PROPAGATE = "propagate"
    ABSORB = "absorb"
    RETRY = "retry"
    ESCALATE = "escalate"


@dataclass
class ErrorHandler:
    """Configuration for handling specific error types."""
    error_codes: List[str]
    policy: ErrorPropagationPolicy
    max_retries: int = 3
    retry_delay_seconds: int = 5
    escalation_target: Optional[str] = None
    fallback_action: Optional[str] = None


# =============================================================================
# AIP v2 Context Passing (Blueprint Section 4.5)
# =============================================================================


@dataclass
class ContextFrame:
    """A frame of context to be passed between agents.

    Blueprint Reference: Section 4.5 - Context Passing
    "跨 Agent 的上下文傳遞規範"

    Context frames allow agents to share relevant information without
    coupling their implementations.

    Example:
        context = ContextFrame(
            frame_id="ctx_001",
            source_agent="planner_agent",
            data={"task_plan": [...], "constraints": [...]},
            scope="task",
        )
    """
    frame_id: str
    source_agent: str
    data: Dict[str, Any]
    scope: str = "task"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    parent_frame_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context frame to dictionary."""
        return {
            "frame_id": self.frame_id,
            "source_agent": self.source_agent,
            "data": self.data,
            "scope": self.scope,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "parent_frame_id": self.parent_frame_id,
            "metadata": self.metadata,
        }

    def is_expired(self) -> bool:
        """Check if context frame has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_message(self, receiver: str) -> AgentMessage:
        """Convert context frame to AgentMessage for transmission.

        Provides consistency with AgentHandshake and AgentError which also
        have to_message() methods.
        """
        return AgentMessage(
            sender=self.source_agent,
            receiver=receiver,
            payload=self.to_dict(),
            message_type=MessageType.CONTEXT_PUSH,
            priority=MessagePriority.NORMAL,
            metadata=self.metadata,
        )


@dataclass
class AgentContext:
    """Complete context for an agent interaction.

    This aggregates multiple context frames and provides methods for
    context management during agent communication.
    """
    trace_id: str
    frames: List[ContextFrame] = field(default_factory=list)
    global_data: Dict[str, Any] = field(default_factory=dict)

    def push_frame(self, frame: ContextFrame) -> None:
        """Add a new context frame."""
        self.frames.append(frame)

    def pop_frame(self) -> Optional[ContextFrame]:
        """Remove and return the most recent context frame."""
        if self.frames:
            return self.frames.pop()
        return None

    def get_frame(self, frame_id: str) -> Optional[ContextFrame]:
        """Get a specific context frame by ID."""
        for frame in self.frames:
            if frame.frame_id == frame_id:
                return frame
        return None

    def get_active_frames(self) -> List[ContextFrame]:
        """Get all non-expired context frames."""
        return [f for f in self.frames if not f.is_expired()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "trace_id": self.trace_id,
            "frames": [f.to_dict() for f in self.frames],
            "global_data": self.global_data,
        }

    def to_message(
        self,
        sender: str,
        receiver: str,
        push: bool = True,
    ) -> AgentMessage:
        """Convert context to AgentMessage for transmission."""
        return AgentMessage(
            sender=sender,
            receiver=receiver,
            payload=self.to_dict(),
            trace_id=self.trace_id,
            message_type=MessageType.CONTEXT_PUSH if push else MessageType.CONTEXT_POP,
            priority=MessagePriority.NORMAL,
        )


# =============================================================================
# AIP v2 Message Validation
# =============================================================================


class MessageValidationError(Exception):
    """Exception raised when message validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class MessageValidator:
    """Validator for AIP v2 messages.

    Ensures messages conform to the AIP v2 specification before transmission.
    """

    REQUIRED_FIELDS = ["sender", "receiver", "payload", "trace_id"]
    MAX_PAYLOAD_SIZE = 1024 * 1024
    VALID_AGENT_ID_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]*$"

    @classmethod
    def validate(cls, message: AgentMessage) -> bool:
        """Validate an AgentMessage.

        Raises:
            MessageValidationError: If validation fails.

        Returns:
            True if validation passes.
        """
        import re
        import json

        if not message.sender:
            raise MessageValidationError("sender is required", "sender")

        if not message.receiver:
            raise MessageValidationError("receiver is required", "receiver")

        if not message.trace_id:
            raise MessageValidationError("trace_id is required", "trace_id")

        if not re.match(cls.VALID_AGENT_ID_PATTERN, message.sender):
            raise MessageValidationError(
                f"Invalid sender format: {message.sender}", "sender"
            )

        if not re.match(cls.VALID_AGENT_ID_PATTERN, message.receiver):
            raise MessageValidationError(
                f"Invalid receiver format: {message.receiver}", "receiver"
            )

        try:
            payload_size = len(json.dumps(message.payload))
            if payload_size > cls.MAX_PAYLOAD_SIZE:
                raise MessageValidationError(
                    f"Payload size {payload_size} exceeds maximum {cls.MAX_PAYLOAD_SIZE}",
                    "payload",
                )
        except (TypeError, ValueError) as e:
            raise MessageValidationError(
                f"Payload is not JSON serializable: {e}", "payload"
            )

        if message.ttl_seconds is not None and message.ttl_seconds <= 0:
            raise MessageValidationError(
                "ttl_seconds must be positive", "ttl_seconds"
            )

        return True

    @classmethod
    def validate_handshake(cls, handshake: AgentHandshake) -> bool:
        """Validate an AgentHandshake.

        Raises:
            MessageValidationError: If validation fails.

        Returns:
            True if validation passes.
        """
        import re

        if not handshake.agent_id:
            raise MessageValidationError("agent_id is required", "agent_id")

        if not re.match(cls.VALID_AGENT_ID_PATTERN, handshake.agent_id):
            raise MessageValidationError(
                f"Invalid agent_id format: {handshake.agent_id}", "agent_id"
            )

        if not handshake.agent_type:
            raise MessageValidationError("agent_type is required", "agent_type")

        if not handshake.capabilities:
            raise MessageValidationError(
                "At least one capability must be declared", "capabilities"
            )

        return True


# =============================================================================
# AIP v2 Agent Protocol Interface
# =============================================================================


@runtime_checkable
class AIPv2Agent(Protocol):
    """Protocol interface for AIP v2 compliant agents.

    Blueprint Reference: Section 4.5
    "所有 Agent 必須實作 AIP v2 介面才能加入 MorningAI 生態系。"

    All agents in the MorningAI ecosystem must implement this interface.
    """

    @property
    def agent_id(self) -> str:
        """Unique identifier for this agent."""
        ...

    @property
    def agent_type(self) -> str:
        """Type of agent (maps to AgentType enum)."""
        ...

    @property
    def capabilities(self) -> List[AgentCapability]:
        """List of capabilities this agent provides."""
        ...

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        """Handle an incoming AIP v2 message.

        Args:
            message: The incoming AgentMessage.

        Returns:
            Response AgentMessage.
        """
        ...

    async def perform_handshake(self, orchestrator_id: str) -> AgentHandshake:
        """Perform handshake with orchestrator.

        Args:
            orchestrator_id: ID of the orchestrator to handshake with.

        Returns:
            AgentHandshake with capability declarations.
        """
        ...

    def get_context(self) -> AgentContext:
        """Get current agent context."""
        ...


# =============================================================================
# Agent Type to Capability Mapping (Blueprint Section 3.3 Integration)
# =============================================================================


AGENT_TYPE_CAPABILITIES: Dict[str, List[AgentCapability]] = {
    "planner": [AgentCapability.CODE_ANALYSIS],
    "coding": [AgentCapability.CODE_WRITING, AgentCapability.CODE_ANALYSIS],
    "reviewer": [AgentCapability.CODE_REVIEW, AgentCapability.CODE_ANALYSIS],
    "test": [AgentCapability.TEST_WRITING, AgentCapability.TEST_EXECUTION],
    "debugger": [AgentCapability.CODE_ANALYSIS, AgentCapability.CODE_WRITING],
    "ui_consistency": [AgentCapability.UI_ANALYSIS],
    "ux_heuristic": [AgentCapability.UX_EVALUATION],
    "visual_regression": [AgentCapability.UI_ANALYSIS],
    "design_token_governance": [AgentCapability.UI_ANALYSIS, AgentCapability.GOVERNANCE],
    "judge": [AgentCapability.GOVERNANCE],
    "debate_left": [AgentCapability.CODE_ANALYSIS],
    "debate_right": [AgentCapability.CODE_ANALYSIS],
    "risk_analyzer": [AgentCapability.RISK_ASSESSMENT, AgentCapability.GOVERNANCE],
    "dev_agent": [
        AgentCapability.CODE_ANALYSIS,
        AgentCapability.CODE_WRITING,
        AgentCapability.CODE_REVIEW,
        AgentCapability.TEST_WRITING,
        AgentCapability.TEST_EXECUTION,
    ],
    "ops_agent": [
        AgentCapability.DEPLOYMENT,
        AgentCapability.MONITORING,
        AgentCapability.INCIDENT_RESPONSE,
    ],
    "pm_agent": [AgentCapability.DOCUMENTATION],
    "growth_strategist": [AgentCapability.DOCUMENTATION],
    "meta_agent": [AgentCapability.GOVERNANCE],
}


def get_capabilities_for_agent_type(agent_type: str) -> List[AgentCapability]:
    """Get the default capabilities for a given agent type.

    Args:
        agent_type: The agent type string (from AgentType enum).

    Returns:
        List of AgentCapability for the agent type (a copy to prevent mutation).
    """
    # Return a copy to prevent callers from mutating the module constant
    return list(AGENT_TYPE_CAPABILITIES.get(agent_type, []))


# =============================================================================
# Legacy Protocol Interfaces (Backward Compatibility)
# =============================================================================


@runtime_checkable
class DevAgentProtocol(Protocol):
    """
    Protocol for Development Agent implementations.

    Dev agents handle code-related tasks including analysis, writing,
    testing, and review.
    """

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        ...

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        ...

    async def analyze_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Analyze code structure and identify issues.

        Args:
            task: The analysis task with inputs containing:
                - repo: Repository path or URL
                - files: Optional list of files to analyze
                - analysis_type: Type of analysis (structure, security, performance)

        Returns:
            AgentResult with analysis findings
        """
        ...

    async def write_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Write or modify code based on requirements.

        Args:
            task: The code writing task with inputs containing:
                - description: What code to write
                - target_files: Files to create or modify
                - constraints: Any constraints or requirements

        Returns:
            AgentResult with files modified and changes made
        """
        ...

    async def write_test(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Write tests for existing code.

        Args:
            task: The test writing task with inputs containing:
                - target_files: Files to write tests for
                - test_type: Type of tests (unit, integration, e2e)
                - coverage_target: Target coverage percentage

        Returns:
            AgentResult with test files created
        """
        ...

    async def run_test(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Execute tests and return results.

        Args:
            task: The test execution task with inputs containing:
                - test_files: Optional specific test files to run
                - test_command: Optional custom test command

        Returns:
            AgentResult with test results and coverage
        """
        ...

    async def review_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Review code changes and provide feedback.

        Args:
            task: The code review task with inputs containing:
                - changes: Diff or list of changed files
                - review_criteria: What to look for

        Returns:
            AgentResult with review comments and suggestions
        """
        ...


@runtime_checkable
class OpsAgentProtocol(Protocol):
    """
    Protocol for Operations Agent implementations.

    Ops agents handle deployment, monitoring, and operational tasks.
    """

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        ...

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        ...

    async def deploy(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Deploy application to target environment.

        Args:
            task: The deployment task with inputs containing:
                - environment: Target environment (staging, production)
                - version: Version or commit to deploy
                - rollback_on_failure: Whether to auto-rollback

        Returns:
            AgentResult with deployment status and URL
        """
        ...

    async def monitor(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Monitor application health and metrics.

        Args:
            task: The monitoring task with inputs containing:
                - metrics: List of metrics to check
                - duration: How long to monitor
                - thresholds: Alert thresholds

        Returns:
            AgentResult with monitoring data
        """
        ...

    async def rollback(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Rollback to a previous deployment.

        Args:
            task: The rollback task with inputs containing:
                - environment: Target environment
                - target_version: Version to rollback to

        Returns:
            AgentResult with rollback status
        """
        ...

    async def scale(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Scale application resources.

        Args:
            task: The scaling task with inputs containing:
                - environment: Target environment
                - replicas: Target number of replicas
                - resources: Resource limits

        Returns:
            AgentResult with scaling status
        """
        ...


class BaseDevAgent:
    """Base implementation for DevAgent with common functionality"""

    def __init__(self) -> None:
        self._capabilities = [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CODE_WRITING,
            AgentCapability.CODE_REVIEW,
            AgentCapability.TEST_WRITING,
            AgentCapability.TEST_EXECUTION,
        ]
        self._available = True

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    @property
    def is_available(self) -> bool:
        return self._available

    async def analyze_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement analyze_code")

    async def write_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement write_code")

    async def write_test(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement write_test")

    async def run_test(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement run_test")

    async def review_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement review_code")


class BaseOpsAgent:
    """Base implementation for OpsAgent with common functionality"""

    def __init__(self) -> None:
        self._capabilities = [
            AgentCapability.DEPLOYMENT,
            AgentCapability.MONITORING,
            AgentCapability.INCIDENT_RESPONSE,
        ]
        self._available = True

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    @property
    def is_available(self) -> bool:
        return self._available

    async def deploy(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement deploy")

    async def monitor(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement monitor")

    async def rollback(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement rollback")

    async def scale(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement scale")


def validate_dev_agent(agent: Any) -> bool:
    """Validate that an object implements DevAgentProtocol"""
    return isinstance(agent, DevAgentProtocol)


def validate_ops_agent(agent: Any) -> bool:
    """Validate that an object implements OpsAgentProtocol"""
    return isinstance(agent, OpsAgentProtocol)
