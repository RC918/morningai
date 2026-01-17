"""
AIP v2 Exceptions

Single source of truth for all AIP v2 exceptions.
This module exists to avoid circular imports between message.py and validation.py.
"""

from typing import Optional


class MessageValidationError(Exception):
    """Exception raised when message validation fails.

    This is the canonical definition used throughout the aip_v2 module.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)
