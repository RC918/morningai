"""
EPIC D Probe 0: SimpleCoder Sanity Check - Intentional Lint Error

This file contains an intentional lint error (F821: undefined name 'reuslt')
to validate the CI failure -> AutoFixer -> SimpleCoder pipeline.

DO NOT FIX THIS ERROR MANUALLY - it is used for automated testing.
"""


def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers."""
    reuslt = a + b  # Intentional typo: 'reuslt' instead of 'result' (F821)
    return result  # This references 'result' which is undefined
