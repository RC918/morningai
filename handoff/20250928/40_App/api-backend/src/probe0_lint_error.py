# Bad code
def some_function(some_arg1,some_arg2):
    result=some_arg1+some_arg2;return result

# Good code
def some_function(some_arg1: int, some_arg2: int) -> int:
    """Add two numbers."""
    result = some_arg1 + some_arg2
    return result