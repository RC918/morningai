"""
AIP v2 Agent Protocol Interface

Blueprint Reference: Section 4.5
"所有 Agent 必須實作 AIP v2 介面才能加入 MorningAI 生態系。"
"""

from typing import List, Protocol, runtime_checkable

from .message import AgentMessage
from .handshake import AgentHandshake, AgentCapability
from .context import AgentContext


# =============================================================================
# AIP v2 Agent Protocol Interface
# =============================================================================


@runtime_checkable
class AIPv2Agent(Protocol):
    """Protocol interface for AIP v2 compliant agents.

    Blueprint Reference: Section 4.5
    "所有 Agent 必須實作 AIP v2 介面才能加入 MorningAI 生態系。"

    All agents in the MorningAI ecosystem must implement this interface.

    Issue #4139 Enhancement: Added lifecycle methods (initialize, shutdown)
    for proper agent lifecycle management.
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

    async def initialize(self) -> None:
        """Initialize the agent.

        Called when the agent is first started. Implementations should
        set up any required resources, connections, or state.

        Issue #4139: Added lifecycle method for proper initialization.
        """
        ...

    async def shutdown(self) -> None:
        """Shutdown the agent gracefully.

        Called when the agent is being stopped. Implementations should
        clean up resources, close connections, and save state if needed.

        Issue #4139: Added lifecycle method for proper cleanup.
        """
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

    def is_healthy(self) -> bool:
        """Check if the agent is healthy and ready to process messages.

        Issue #4139: Added health check method for monitoring.

        Returns:
            True if the agent is healthy, False otherwise.
        """
        ...
