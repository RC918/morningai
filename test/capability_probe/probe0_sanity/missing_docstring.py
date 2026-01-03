"""
Probe 0: Sanity Check - Single File AutoFixer Test

This file intentionally has a function missing a docstring.
When CI runs flake8 with D100/D103 rules, it should fail.
SimpleCoder should be able to add the missing docstring.

Expected outcome:
- CI fails with "missing docstring" error
- SimpleCoder adds docstring
- Commit succeeds

Log keywords to search:
- [Fixer]
- [CODER_PATCH]
"""


def calculate_sum(a: int, b: int) -> int:
    return a + b


def calculate_product(a: int, b: int) -> int:
    return a * b
