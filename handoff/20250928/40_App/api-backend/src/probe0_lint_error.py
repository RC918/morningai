"""
Probe 0: SimpleCoder Sanity Check - Intentional Lint Error

This file contains an intentional lint error (F821: undefined name 'result')
to test the CI failure -> AutoFixer -> SimpleCoder pipeline.

The typo 'reuslt' should trigger:
1. CI lint check failure (F821 undefined name)
2. AutoFixer detection
3. SimpleCoder minimal fix: reuslt -> result

DO NOT manually fix this file - it's for automated testing.
"""


def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two integers."""
    reuslt = a + b  # Intentional typo: should be 'result'
    return result  # F821: undefined name 'result'
