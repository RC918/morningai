# updated code in probe0_lint_error.py

def calculate_sum(num1: int, num2: int) -> int:
    """Calculate the sum of two numbers."""
    try:
        total = num1 + num2
    except TypeError as e:
        print(f"An error occurred: {e}")
        return 0
    else:
        return total

if __name__ == "__main__":
    print(calculate_sum(5, 10))