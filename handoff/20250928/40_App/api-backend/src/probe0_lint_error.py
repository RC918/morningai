# Importing necessary modules
import sys
import pylint.lint

def check_lint(file_path: str) -> None:
    """
    Function to check lint errors
    :param file_path: str: path to the Python file
    """
    # Run pylint
    pylint_output = pylint.lint.Run([file_path], do_exit=False)

    # If there are any errors
    if pylint_output.linter.stats['global_note'] < 10.0:
        print(f"Lint errors detected in {file_path}. Please fix them.")
        sys.exit(1)
    else:
        print(f"No lint errors detected in {file_path}. File is clean.")


if __name__ == "__main__":
    check_lint('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')