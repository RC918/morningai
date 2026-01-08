"""
Probe 1: EPIC D GeneralCoder Multi-file Validation - Utility Module

This file is part of a 2-file test to validate GeneralCoder's multi-file capabilities:
- probe1_utils.py (this file): Utility functions
- probe1_main.py: Main module that imports from this file

DO NOT MERGE THIS FILE - it is a test vehicle only.

This test validates:
- D-1b: Multi-file support (<=5 files)
- Import relationship understanding
- Per-file syntax validation
"""


def calculate_total(items: list) -> int:
    """Calculate the total of a list of numbers."""
    total = 0
    for item in items:
        total += item
    return total


def format_result(value: int) -> str:
    """Format a numeric result as a string."""
    return f"Result: {value}"
