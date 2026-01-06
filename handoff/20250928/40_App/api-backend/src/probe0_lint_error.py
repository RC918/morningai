import os
import pylint.lint

def run_linter_on_file(file_path: str) -> None:
    """
    Run pylint on the given Python file to check for linting issues.

    Args:
    file_path (str): Path to the Python file to lint.
    """
    # Check if the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Could not find file at path: {file_path}")

    # Run pylint on the file
    try:
        pylint_output = pylint.lint.Run([file_path], exit=False)
        print(pylint_output.linter.msg_status)
    except Exception as e:
        print(f"An error occurred while running pylint: {e}")

# Run the function on the target file
run_linter_on_file('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')