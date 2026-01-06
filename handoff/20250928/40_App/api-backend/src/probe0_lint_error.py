# probe0_lint_error.py

def add_numbers(num1: int, num2: int) -> int:
    """
    Add two integers and return the result

    :param num1: First integer
    :param num2: Second integer
    :return: Sum of num1 and num2
    """
    try:
        result = num1 + num2
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    print(add_numbers(5, 10))