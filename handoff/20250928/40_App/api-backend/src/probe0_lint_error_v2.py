"""
Probe 0 v2: EPIC D CI Failure Path Validation - SimpleCoder Sanity Check

This file contains an INTENTIONAL lint error to validate the CI failure path:
- CI should fail with F821 (undefined name 'reuslt')
- AutoFixer should detect the failure and trigger SimpleCoder
- SimpleCoder should fix 'reuslt' -> 'result'

DO NOT MERGE THIS FILE - it is a test vehicle only.

Previous test (PR #3627) was polluted by AutoFixer loops generating invalid content.
This is a clean restart to validate the P3 fix (check_run conclusion detection).
"""


def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers."""
    result = a + b
    # INTENTIONAL ERROR: 'reuslt' is undefined (should be 'result')
    # This should trigger F821: undefined name 'reuslt'
    return reuslt  # INTENTIONAL: F821 error to trigger SimpleCoder


def main():
    """Main function to demonstrate the lint error."""
    value = calculate_sum(10, 20)
    print(f"The sum is: {value}")


if __name__ == "__main__":
    main()
