# Before Fix
def some_function(a,b):
  sum=a+b
  print("Sum is",sum)

# After Fix
def some_function(a: int, b: int) -> None:
    """
    This function prints the sum of two numbers
    Args:
    a : int : first number
    b : int : second number

    Returns:
    None
    """
    sum_value = a + b
    print("Sum is", sum_value)