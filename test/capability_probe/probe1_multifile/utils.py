"""
Probe 1: D-1 Multi-file Refactor Test - Utils Module

This file contains a function that is imported by main.py.
The function name `calculate_total` will be renamed to `compute_total`
but the caller in main.py will NOT be updated, causing an import error.

GeneralCoder should detect the import relationship and update both files.

Expected outcome:
- CI fails with import error or undefined name
- GeneralCoder identifies both files need updating
- Both files are modified atomically

Log keywords to search:
- [GENERAL_CODER_ATTEMPT]
- [GENERAL_CODER_PATCH]
"""


def compute_total(items: list[float]) -> float:
    """Calculate the total sum of items.

    Args:
        items: List of numeric values to sum.

    Returns:
        The sum of all items.
    """
    return sum(items)


def calculate_average(items: list[float]) -> float:
    """Calculate the average of items.

    Args:
        items: List of numeric values.

    Returns:
        The average value.
    """
    if not items:
        return 0.0
    return sum(items) / len(items)
