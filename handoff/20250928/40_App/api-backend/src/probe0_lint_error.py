# Import necessary libraries
import sys
import pylint.lint

# Define the path of the file to lint
file_to_lint = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

def lint_and_fix_errors(file_to_lint: str) -> None:
    """
    This function will run pylint on the given file and print out any linting errors.
    """
    try:
        # Run pylint on the file
        pylint_output = pylint.lint.Run([file_to_lint], exit=False)
        
        # If there are any linting errors, print them out
        if pylint_output.linter.msg_status > 0:
            print(f"Pylint found linting errors in {file_to_lint}")
        
    except Exception as e:
        print(f"An error occurred while linting {file_to_lint}: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    lint_and_fix_errors(file_to_lint)