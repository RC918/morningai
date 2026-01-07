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
    """Process data using utility functions."""
    # Intentional typo: should be 'calculate_total'
    total = calcualte_total(data)
    return format_result(total, "Total")


def main() -> None:
    """Main function to demonstrate the processing."""
    sample_data = [10, 20, 30, 40]
    result = process_data(sample_data)
    print(result)


if __name__ == "__main__":
    main()
