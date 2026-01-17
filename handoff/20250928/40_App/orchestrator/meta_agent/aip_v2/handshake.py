"""
AIP v2 Handshake Protocol

Blueprint Reference: Section 4.5 - Handshake Protocol
"Agent 啟動時的能力宣告與驗證"
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .message import AIP_VERSION, AgentMessage, MessageType, MessagePriority


# =============================================================================
# Handshake Enums
# =============================================================================


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


# =============================================================================
# Capability Declaration
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


# =============================================================================
# Agent Handshake
# =============================================================================


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


# =============================================================================
# Handshake Response
# =============================================================================


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
