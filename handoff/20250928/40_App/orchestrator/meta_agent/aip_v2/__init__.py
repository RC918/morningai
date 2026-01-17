"""
AIP v2 (Agent Interaction Protocol v2) Module

This module provides the complete AIP v2 implementation as defined in
MorningAI Ecosystem Blueprint 2025 Final, Section 4.5.

The module is organized into submodules for better maintainability:
- message: Core message types (AgentMessage, MessagePriority, MessageType)
- handshake: Handshake protocol (AgentHandshake, CapabilityDeclaration)
- error: Error handling (AgentError, ErrorPropagationPolicy)
- context: Context passing (ContextFrame, AgentContext)
- validation: Message validation (MessageValidator, MessageValidationError)
- protocol: Agent protocol interface (AIPv2Agent)
- capabilities: Agent type to capability mapping

Blueprint Reference: Section 4.5 - Agent Interaction Protocol v2 (AIP v2)
Issue: #4139 - AIP v2 Architecture Improvements
"""

from .message import (
    AIP_VERSION,
    MessagePriority,
    MessageType,
    AgentMessage,
    AgentTask,
    AgentResult,
)
from .handshake import (
    HandshakeStatus,
    AgentCapability,
    CapabilityDeclaration,
    AgentHandshake,
    HandshakeResponse,
)
from .error import (
    ErrorSeverity,
    AgentError,
    ErrorPropagationPolicy,
    ErrorHandler,
)
from .context import (
    ContextFrame,
    AgentContext,
)
from .validation import (
    MessageValidationError,
    MessageValidator,
    HandshakeValidator,
)
from .protocol import (
    AIPv2Agent,
)
from .capabilities import (
    AGENT_TYPE_CAPABILITIES,
    get_capabilities_for_agent_type,
)

__all__ = [
    # Version
    "AIP_VERSION",
    # Message types
    "MessagePriority",
    "MessageType",
    "AgentMessage",
    "AgentTask",
    "AgentResult",
    # Handshake
    "HandshakeStatus",
    "AgentCapability",
    "CapabilityDeclaration",
    "AgentHandshake",
    "HandshakeResponse",
    # Error handling
    "ErrorSeverity",
    "AgentError",
    "ErrorPropagationPolicy",
    "ErrorHandler",
    # Context
    "ContextFrame",
    "AgentContext",
    # Validation
    "MessageValidationError",
    "MessageValidator",
    "HandshakeValidator",
    # Protocol
    "AIPv2Agent",
    # Capabilities
    "AGENT_TYPE_CAPABILITIES",
    "get_capabilities_for_agent_type",
]
