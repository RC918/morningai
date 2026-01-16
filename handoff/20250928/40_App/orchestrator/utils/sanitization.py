"""
Sanitization utilities for safe logging and error messages.

This module provides functions to sanitize untrusted data before including
it in log messages or error strings, preventing log injection attacks (CWE-117).

Issues: #4016, #3992 - Add input sanitization for log fields to prevent log injection

EPIC F Phase F-0: Planner Output Contract
Blueprint Reference:
- Section 3.2 (Flow Controller v3)
- Section 3.4 (Security-First Design): Defense in depth
- Section 4.1 (Safe by Design): Input validation
- Section 4.7 (Capability-Based Security): Secure logging practices
"""

import re
from typing import Any, Dict, Optional, Union


# Control characters that could be used for log injection
# Includes newlines, carriage returns, and other control chars (ASCII 0-31, 127)
_CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x1f\x7f]')


def sanitize_for_log(value: Optional[Union[str, Any]], max_length: int = 200) -> str:
    """
    Sanitize untrusted data for safe inclusion in log messages.

    Prevents log injection by:
    - Converting non-string values to strings safely
    - Removing/replacing ALL control characters (not just newlines)
    - Truncating to max_length to prevent log flooding

    Args:
        value: The untrusted value to sanitize (string or any type)
        max_length: Maximum length of output (default 200)

    Returns:
        Sanitized string safe for logging

    Examples:
        >>> sanitize_for_log("line1\\nline2")
        'line1 line2'
        >>> sanitize_for_log("a" * 250, max_length=10)
        'aaaaaaaaaa...'
        >>> sanitize_for_log(None)
        ''
        >>> sanitize_for_log(123)
        '123'
    """
    if value is None:
        return ""

    # Convert to string if not already
    if not isinstance(value, str):
        try:
            value = str(value)
        except Exception:
            return "<non-serializable>"

    # Replace ALL control characters with space (more secure than just newlines)
    sanitized = _CONTROL_CHAR_PATTERN.sub(' ', value)

    if len(sanitized) > max_length:
        return sanitized[:max_length] + "..."
    return sanitized


def sanitize_task_id(task_id: str, max_length: int = 100) -> str:
    """
    Sanitize task_id for safe inclusion in error messages.

    This is a convenience wrapper around sanitize_for_log with a default
    max_length of 100, suitable for task identifiers.

    Args:
        task_id: The task_id to sanitize
        max_length: Maximum length of output (default 100)

    Returns:
        Sanitized string safe for error messages

    Examples:
        >>> sanitize_task_id("task-123")
        'task-123'
        >>> sanitize_task_id("task\\n123")
        'task 123'
    """
    return sanitize_for_log(task_id, max_length=max_length)


def sanitize_log_fields(
    fields: Dict[str, Any],
    max_length: int = 200,
    skip_keys: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Sanitize all string fields in a dictionary for safe logging.

    This is useful for sanitizing the 'extra' dict passed to logger calls.
    Non-string values (int, float, bool, None, list, dict) are passed through
    with appropriate handling.

    Args:
        fields: Dictionary of fields to sanitize
        max_length: Maximum length for sanitized strings
        skip_keys: Set of keys to skip sanitization for (e.g., internal fields)

    Returns:
        New dictionary with sanitized string values

    Examples:
        >>> sanitize_log_fields({"repo": "owner/repo\\n", "count": 5})
        {'repo': 'owner/repo ', 'count': 5}
    """
    if not fields:
        return {}

    skip_keys = skip_keys or set()
    sanitized: Dict[str, Any] = {}

    for key, value in fields.items():
        if key in skip_keys:
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = sanitize_for_log(value, max_length)
        elif isinstance(value, (int, float, bool, type(None))):
            # Safe types that don't need sanitization
            sanitized[key] = value
        elif isinstance(value, (list, tuple)):
            # Recursively sanitize list items (including nested dicts)
            sanitized_list = []
            for item in value:
                if isinstance(item, dict):
                    sanitized_list.append(
                        sanitize_log_fields(item, max_length, skip_keys)
                    )
                elif isinstance(item, str):
                    sanitized_list.append(sanitize_for_log(item, max_length))
                elif isinstance(item, (int, float, bool, type(None))):
                    sanitized_list.append(item)
                else:
                    # For other types (including nested lists), convert to string
                    sanitized_list.append(sanitize_for_log(item, max_length))
            sanitized[key] = sanitized_list
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_log_fields(value, max_length, skip_keys)
        else:
            # For other types, convert to string and sanitize
            sanitized[key] = sanitize_for_log(value, max_length)

    return sanitized
