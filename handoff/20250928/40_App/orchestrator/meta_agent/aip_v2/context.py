"""
AIP v2 Context Passing

Blueprint Reference: Section 4.5 - Context Passing
"跨 Agent 的上下文傳遞規範"
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .message import AgentMessage, MessageType, MessagePriority


# =============================================================================
# Context Frame
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


# =============================================================================
# Agent Context
# =============================================================================


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
