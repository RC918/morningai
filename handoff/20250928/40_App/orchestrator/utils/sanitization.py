"""
Sanitization utilities for safe logging and error messages.

This module provides functions to sanitize untrusted data before including
it in log messages or error strings, preventing log injection attacks (CWE-117).

EPIC F Phase F-0: Planner Output Contract
Blueprint Reference: Section 3.2 (Flow Controller v3)
"""


def sanitize_for_log(value: str, max_length: int = 200) -> str:
    """
    Sanitize untrusted data for safe inclusion in log messages.

    Prevents log injection by:
    - Replacing newlines and carriage returns with escaped versions
    - Truncating to max_length to prevent log flooding

    Args:
        value: The untrusted string to sanitize
        max_length: Maximum length of output (default 200)

    Returns:
        Sanitized string safe for logging

    Examples:
        >>> sanitize_for_log("line1\\nline2")
        'line1\\\\nline2'
        >>> sanitize_for_log("a" * 250, max_length=10)
        'aaaaaaaaaa...'
    """
    if not value:
        return ""
    sanitized = value.replace('\n', '\\n').replace('\r', '\\r')
    if len(sanitized) > max_length:
        prefix = sanitized[:max_length]
        # Avoid leaving a dangling backslash if we truncate in the middle of an escape sequence
        if prefix.endswith('\\'):
            prefix = prefix[:-1]
        return prefix + "..."
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
        'task\\\\n123'
    """
    return sanitize_for_log(task_id, max_length=max_length)
