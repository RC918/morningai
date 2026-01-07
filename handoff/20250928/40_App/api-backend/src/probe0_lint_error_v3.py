"""
Probe 0 v3: EPIC D CI Failure Path Validation - Post Embedding Migration

This file contains an INTENTIONAL lint error to validate the CI failure path:
- CI should fail with F821 (undefined name 'reuslt')
- AutoFixer should detect the failure and trigger SimpleCoder
- SimpleCoder should fix 'reuslt' -> 'result'

DO NOT MERGE THIS FILE - it is a test vehicle only.

This test validates the complete SimpleCoder pipeline after:
- PR #3660: EmbeddingClient dimension fix (alicloud -> 1024)
- PR #3661: Database migration (vector columns -> 1024)
- PR #3659: P5/P6 prompt strengthening and dialogue detection
"""


def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers."""
    result = a + b
    return reuslt  # Intentional typo: should be 'result'


def main() -> None:
    """Main function to demonstrate the calculation."""
    x = 10
    y = 20
    total = calculate_sum(x, y)
    print(f"The sum of {x} and {y} is {total}")


if __name__ == "__main__":
    main()
