# api-backend/src/probe0_lint_error.py
# Import required modules
from typing import Any

def add_numbers(num1: Any, num2: Any) -> Any:
    """
    A function to add two numbers
    
    Parameters:
    num1 (Any): The first number
    num2 (Any): The second number

    Returns:
    Any: The sum of the two numbers
    """

    # If the inputs are not numbers, throw an error
    if not isinstance(num1, (int, float)) or not isinstance(num2, (int, float)):
        raise ValueError('Both inputs must be numbers')

    # Return the sum of the two numbers
    return num1 + num2

# Test the function
result = add_numbers(3, 5)
print(result)