# Example of original code with possible lint errors
def example_function(a,b):
    c=a+b
    return c

# Example of fixed code following flake8 rules
def example_function(a: int, b: int) -> int:
    """
    Add two integers and return result.

    Parameters:
        a (int): The first integer
        b (int): The second integer

    Returns:
        int: The sum of the two integers
    """
    c = a + b
    return c