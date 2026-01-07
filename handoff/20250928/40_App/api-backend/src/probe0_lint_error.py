# probe0_lint_error.py

from typing import Any

def example_function(param1: Any, param2: Any) -> None:
    """
    This is an example function that does nothing.
    
    Args:
        param1 (Any): The first parameter.
        param2 (Any): The second parameter.
    """
    pass

try:
    example_function('param1', 'param2')
except Exception as e:
    print(f"An error occurred: {e}")