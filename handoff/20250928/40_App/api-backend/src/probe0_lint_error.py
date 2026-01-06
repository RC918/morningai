import pylint.lint
import pylint.epylint as lint
import ast
from typing import Tuple

def lint_error(filename: str) -> Tuple[int, int, str]:
    """
    Function to lint the python file and return the results.

    Args:
    filename (str): The python file to lint.

    Returns:
    Tuple[int, int, str]: The number of errors, the number of warnings and the report of the lint.
    """
    (pylint_stdout, pylint_stderr) = lint.py_run(filename, return_std=True)
    lint_report = pylint_stdout.getvalue()

    # Parse the report to get the number of errors and warnings
    num_errors = sum(1 for line in lint_report.split("\n") if "E:" in line)
    num_warnings = sum(1 for line in lint_report.split("\n") if "W:" in line)

    return num_errors, num_warnings, lint_report

def fix_lint() -> None:
    """
    Function to fix the linting errors of the python file.
    """
    filename = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    try:
        with open(filename, 'r') as file:
            try:
                # Check if the file is a valid python file
                ast.parse(file.read())
            except SyntaxError as e:
                print(f"SyntaxError: {e}")
                return

        # Lint the file
        num_errors, num_warnings, lint_report = lint_error(filename)

        # Print the lint report
        print(lint_report)

        # If there are errors or warnings, manually fix them
        if num_errors > 0 or num_warnings > 0:
            print(f"The file {filename} has {num_errors} errors and {num_warnings} warnings. Please fix them manually.")
    except FileNotFoundError:
        print(f"The file {filename} does not exist.")

if __name__ == "__main__":
    fix_lint()