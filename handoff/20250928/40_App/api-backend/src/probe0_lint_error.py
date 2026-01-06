# probe0_lint_error.py
def function_with_linting_errors(param1: int, param2: str) -> bool:
    """
    This function is a sample function with linting errors.
    
    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.
    """
    if param1 > 5:
        print(f"{param2} is greater than 5")
        return True

    print(f"{param2} is not greater than 5")
    return False