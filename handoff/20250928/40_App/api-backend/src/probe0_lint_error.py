# Python Code

# Importing required modules
from typing import Any

def example_function(arg1: int, arg2: str) -> Any:
    """
    This is an example function to show how to fix common lint errors
    """
    try:
        # Your code here
        print(arg1, arg2)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Or use proper logging
        # logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    example_function(1, "test")