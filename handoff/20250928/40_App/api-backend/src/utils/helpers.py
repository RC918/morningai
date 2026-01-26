"""General utility helper functions.

This module contains pure functions with no side effects that can be
safely imported and used throughout the application.

Note: These functions are re-exported from src.main for backward compatibility.
Tests should patch via 'src.main._as_bool' (not 'src.utils.helpers._as_bool').
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md - Patch Canonical Target
"""

# D-4 Test: Intentional lint error for CI failure auto-fix testing
# This unused import will trigger ruff F401 error
import json
unused_test_variable = "This variable is intentionally unused to trigger F841"


def _as_bool(val):
    """Check if a value is truthy (handles bool, None, and string values).

    Args:
        val: The value to check. Can be bool, None, or string.

    Returns:
        bool: True if the value is truthy, False otherwise.

    Examples:
        >>> _as_bool(True)
        True
        >>> _as_bool(False)
        False
        >>> _as_bool(None)
        False
        >>> _as_bool('true')
        True
        >>> _as_bool('1')
        True
        >>> _as_bool('yes')
        True
        >>> _as_bool('on')
        True
        >>> _as_bool('false')
        False
        >>> _as_bool('0')
        False
    """
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "on")
