#!/usr/bin/env python3
"""
Standardized Error Handling for Dev_Agent
Phase 1 Week 4: Unified error format with codes and hints
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(Enum):
    """Standard error codes for Dev_Agent operations"""
    UNKNOWN_ERROR = "DEV_000"
    TOOL_EXECUTION_FAILED = "DEV_001"
    INVALID_PATH = "DEV_002"
    PATH_NOT_WHITELISTED = "DEV_003"
    FILE_NOT_FOUND = "DEV_004"
    PERMISSION_DENIED = "DEV_005"
    NETWORK_ERROR = "DEV_006"
    TIMEOUT_ERROR = "DEV_007"
    INVALID_ACTION = "DEV_008"
    STATE_PERSISTENCE_FAILED = "DEV_009"
    SESSION_NOT_FOUND = "DEV_010"
    CONTEXT_WINDOW_FULL = "DEV_011"
    KNOWLEDGE_GRAPH_ERROR = "DEV_012"
    MAX_ITERATIONS_EXCEEDED = "DEV_013"
    CRITICAL_ACTION_FAILED = "DEV_014"
    INVALID_INPUT = "DEV_015"
    INVALID_OUTPUT = "DEV_016"
    DATABASE_ERROR = "DEV_017"
    EXTERNAL_API_ERROR = "DEV_018"
    RATE_LIMIT_EXCEEDED = "DEV_019"
    MISSING_CREDENTIALS = "DEV_020"
    HEALTH_CHECK_FAILED = "DEV_021"


@dataclass
class DevAgentError:
    """Standardized error structure"""
    code: ErrorCode
    message: str
    hint: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'error_code': self.code.value,
            'error_name': self.code.name,
            'message': self.message,
            'hint': self.hint,
            'context': self.context or {}
        }

    def __str__(self) -> str:
        """String representation"""
        msg = f"[{self.code.value}] {self.message}"
        if self.hint:
            msg += f"\nHint: {self.hint}"
        return msg


def create_error(
    code: ErrorCode,
    message: str,
    hint: Optional[str] = None,
    **context
) -> Dict[str, Any]:
    """Helper to create standardized error response"""
    error = DevAgentError(
        code=code,
        message=message,
        hint=hint,
        context=context if context else None
    )
    return {
        'success': False,
        'error': error.to_dict()
    }


def create_success(data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Helper to create standardized success response"""
    result = {'success': True}
    if data:
        result.update(data)
    if kwargs:
        result.update(kwargs)
    return result
