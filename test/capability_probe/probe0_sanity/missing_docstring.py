"""
Probe 0: Sanity Check - Single File AutoFixer Test

This file intentionally has a lint error (undefined variable).
When CI runs flake8, it should fail with F821 (undefined name).
SimpleCoder should be able to fix the undefined variable.

Expected outcome:
- CI fails with "undefined name" error
- SimpleCoder fixes the undefined variable
- Commit succeeds

Log keywords to search:
- [Fixer]
- [CODER_PATCH]
"""


def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers."""
    return a + b


def calculate_product(a: int, b: int) -> int:
    """Calculate the product of two integers."""
    result = a * b
    return reuslt  # Intentional typo: should be 'result'
