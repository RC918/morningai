"""
Probe 1: D-1 Multi-file Refactor Test - Main Module

This file imports `calculate_total` from utils.py, but the function
was renamed to `compute_total`. This creates an import error.

GeneralCoder should:
1. Detect the import relationship
2. Update this file to use the correct function name

Expected outcome:
- CI fails with ImportError or NameError
- GeneralCoder updates the import statement
- Both files work together after fix

Log keywords to search:
- [GENERAL_CODER_ATTEMPT]
- [GENERAL_CODER_PATCH]
"""
from test.capability_probe.probe1_multifile.utils import calculate_total


def process_order(prices: list[float]) -> dict:
    """Process an order and return summary.

    Args:
        prices: List of item prices.

    Returns:
        Dictionary with order summary.
    """
    total = calculate_total(prices)
    return {
        "item_count": len(prices),
        "total": total,
        "status": "processed"
    }


if __name__ == "__main__":
    sample_prices = [10.99, 25.50, 8.75]
    result = process_order(sample_prices)
    print(f"Order processed: {result}")
