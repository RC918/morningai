# Example of cleaning up code to fix linting errors

def function_with_lint_errors():    # missing docstring and type hints
    a=1    # incorrect spacing
    return a

# Cleaned up version
def cleaned_function() -> int:
    """
    A function that returns 1.
    """
    a = 1
    return a