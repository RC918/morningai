# Original Code with lint errors
def add(a,b):
    result= a+b 
    print(f'The result is {result}') 
    return result

# Fixed Code
def add(a: int, b: int) -> int:
    """
    This function adds two numbers and prints the result.
    
    Args:
        a (int): The first number to add
        b (int): The second number to add

    Returns:
        int: The sum of a and b
    """
    result = a + b
    print(f'The result is {result}')
    return result