# Before linting: 

def add(a,b):
    return a+b;

# After linting:

def add(a: int, b: int) -> int:
    """
    This function adds two integers and returns the result.

    :param a: The first integer
    :param b: The second integer
    :return: The sum of the two integers
    """
    return a + b