"""
Probe 1: EPIC D GeneralCoder Multi-file Validation - Main Module

This file is part of a 2-file test to validate GeneralCoder's multi-file capabilities:
- probe1_utils.py: Utility functions
- probe1_main.py (this file): Main module that imports from probe1_utils

DO NOT MERGE THIS FILE - it is a test vehicle only.

Expected CI failure: F821 (undefined name 'calcualte_total')
GeneralCoder should:
1. Detect the typo in the import usage
2. Understand the relationship between the two files
3. Fix 'calcualte_total' -> 'calculate_total'
"""
from probe1_utils import calculate_total, format_result


def process_data(data: list) -> str:
    """Process a list of data and return formatted result."""
    # INTENTIONAL TYPO: 'calcualte_total' instead of 'calculate_total'
    # This should trigger F821 (undefined name) lint error
    # GeneralCoder should detect this and fix it
    total = calcualte_total(data)  # noqa: F821 - intentional typo for testing
    return format_result(total)


def main():
    """Main entry point."""
    sample_data = [1, 2, 3, 4, 5]
    result = process_data(sample_data)
    print(result)


if __name__ == "__main__":
    main()
