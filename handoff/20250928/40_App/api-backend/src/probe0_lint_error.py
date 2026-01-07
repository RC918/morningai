import os
import subprocess

def fix_lint_and_run_tests(file_path: str) -> None:
    """
    Function to run linter and tests on a python file.
    """
    
    # Running lint check
    try:
        print("Running lint check...")
        lint_output = subprocess.check_output(['flake8', file_path], stderr=subprocess.STDOUT)
        print(lint_output.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print("Lint check failed with errors:")
        print(e.output.decode('utf-8'))
        return

    print("Lint check passed successfully.")
    
    # Running tests
    try:
        print("Running tests...")
        test_output = subprocess.check_output(['pytest', file_path], stderr=subprocess.STDOUT)
        print(test_output.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print("Tests failed with errors:")
        print(e.output.decode('utf-8'))
        return
    
    print("Tests passed successfully.")
    
    print("All checks passed. Safe to push changes.")

# Target file path
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

# Run lint and tests on the target file
fix_lint_and_run_tests(file_path)