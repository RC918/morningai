"""
Probe 0: CI Failure Path Validation - SimpleCoder Sanity Check

This file intentionally has a lint error (undefined variable).
When CI runs Ruff linter, it should fail with F821 (undefined name 'reuslt').
The CI failure webhook should trigger AutoFixer via the CI failure path.
SimpleCoder should be able to fix the undefined variable.

Expected flow:
1. CI fails with F821 (undefined name 'reuslt')
2. check_suite.completed webhook sent with conclusion="failure"
3. _handle_ci_check_completed() sets ci_failure_trigger=True
4. AutoFixer enters CI failure mode (not ReviewerAgent mode)
5. SimpleCoder fixes the typo (reuslt -> result)

DO NOT FIX THIS ERROR MANUALLY - it is intentional for testing.
"""


def calculate_sum(a: int, b: int) -> int:
    """
    Calculate the sum of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        The sum of a and b
    """
    result = a + b
    return reuslt  # Intentional typo: should be 'result'
