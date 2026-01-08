"""
Probe 1 v5 Test File - Utils Module
Purpose: Validate GitHub Annotations extraction for GeneralCoder (D-1b)

This file contains intentional lint errors (F821: undefined names) to test:
1. Annotations API extraction in _fetch_failed_check_runs()
2. ci_error_file_paths being passed to orchestrator
3. review_files being set for GeneralCoder multi-file support

Expected behavior after PR #3677:
- Annotations should be extracted from lint check_run
- File paths should be extracted: probe1_v5_utils.py, probe1_v5_main.py
- GeneralCoder should receive review_files with both files
"""


def calculate_total(items: list) -> int:
    """Calculate total value from items."""
    # Intentional F821 error: 'sum_values' is not defined
    return sum_values(items)


def format_output(data: dict) -> str:
    """Format data for display."""
    # Intentional F821 error: 'formatter' is not defined
    return formatter.to_string(data)


def validate_input(value: str) -> bool:
    """Validate input string."""
    if not value:
        return False
    return True
