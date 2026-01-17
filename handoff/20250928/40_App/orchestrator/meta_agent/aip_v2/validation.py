"""
AIP v2 Message Validation

Provides validation for AIP v2 messages and handshakes.
"""

import json
import re
from typing import Optional

from .message import AgentMessage
from .handshake import AgentHandshake


# =============================================================================
# Validation Exceptions
# =============================================================================


class MessageValidationError(Exception):
    """Exception raised when message validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


# =============================================================================
# Message Validator
# =============================================================================


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

        Note: This method is kept for backward compatibility.
        Use HandshakeValidator.validate() for new code.
        """
        return HandshakeValidator.validate(handshake)


# =============================================================================
# Handshake Validator (Issue #4139 - Split validation logic)
# =============================================================================


class HandshakeValidator:
    """Validator for AIP v2 handshakes.

    Separated from MessageValidator per Issue #4139 to improve
    Single Responsibility Principle compliance.
    """

    VALID_AGENT_ID_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_-]*$"

    @classmethod
    def validate(cls, handshake: AgentHandshake) -> bool:
        """Validate an AgentHandshake.

        Raises:
            MessageValidationError: If validation fails.

        Returns:
            True if validation passes.
        """
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
