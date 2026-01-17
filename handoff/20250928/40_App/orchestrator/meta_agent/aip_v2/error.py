"""
AIP v2 Error Propagation

Blueprint Reference: Section 4.5 - Error Propagation
"標準化的錯誤傳遞與回復機制"
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from .message import AgentMessage, MessageType, MessagePriority


# =============================================================================
# Error Enums
# =============================================================================


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


class ErrorPropagationPolicy(str, Enum):
    """Policies for error propagation between agents."""
    PROPAGATE = "propagate"
    ABSORB = "absorb"
    RETRY = "retry"
    ESCALATE = "escalate"


# =============================================================================
# Agent Error
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


# =============================================================================
# Error Handler Configuration
# =============================================================================


@dataclass
class ErrorHandler:
    """Configuration for handling specific error types."""
    error_codes: List[str]
    policy: ErrorPropagationPolicy
    max_retries: int = 3
    retry_delay_seconds: int = 5
    escalation_target: Optional[str] = None
    fallback_action: Optional[str] = None
