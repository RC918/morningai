# Original code with lint error
def calculate_sum(a,b):
    return a+b

# Fixed code
def calculate_sum(a: int, b: int) -> int:
    return a + b