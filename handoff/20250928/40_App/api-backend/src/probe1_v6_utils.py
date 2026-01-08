"""
Probe 1 v6 - Utility file for EPIC D GeneralCoder check_run annotations extraction validation.

This file intentionally contains lint errors to trigger CI failure.
The goal is to verify that GeneralCoder receives BOTH files via ci_error_file_paths.

DO NOT MERGE - This is a test vehicle only.
"""


def calculate_total(a, b, c):
    """Calculate total with intentional lint error."""
    # Intentional lint error: undefined variable
    result = a + b + c + undefined_value
    return result


def format_output(value):
    """Format output with intentional lint error."""
    # Intentional lint error: undefined variable
    formatted = f"Result: {value}, Extra: {extra_data}"
    
    # Intentional lint error: unused variable
    temp = "unused"
    
    return formatted
