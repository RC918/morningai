# probe0_lint_error.py

def function_with_linting_error():
    # Hypothetical line with linting issue: over 79 characters.
    print("This is a very long string that will cause a linting issue because it is over 79 characters.")

# Fix the linting issue by breaking the line into multiple lines.
def fixed_function():
    print(
        "This is a very long string that will cause a linting issue" 
        "because it is over 79 characters."
    )