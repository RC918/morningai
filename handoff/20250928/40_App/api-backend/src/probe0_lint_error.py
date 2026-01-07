# File: probe0_lint_error.py

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("Both arguments should be integers.")

    return a + b

try:
    print(calculate_sum(5, "5"))
except ValueError as err:
    print(f"Error: {err}")