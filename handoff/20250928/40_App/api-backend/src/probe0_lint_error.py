# api-backend/src/probe0_lint_error.py

def calculate_sum(a: int, b: int) -> int:
    """
    Function to calculate the sum of two numbers
    """
    # Check if the inputs are integers
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("Both inputs must be integers")
    # Return the sum
    return a + b

def main() -> None:
    """
    Main function to run the script
    """
    try:
        result = calculate_sum(5, 6)
        print(f"The result is {result}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()