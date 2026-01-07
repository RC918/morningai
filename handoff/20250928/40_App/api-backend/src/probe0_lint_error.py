# handoff/20250928/40_App/api-backend/src/probe0_lint_error.py

def add_numbers(num1: int, num2: int) -> int:
    """
    Function to add two numbers
    :param num1: First number
    :param num2: Second number
    :return: The sum of the two numbers
    """
    try:
        result = num1 + num2
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None