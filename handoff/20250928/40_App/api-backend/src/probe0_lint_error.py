import pylint.lint
import sys

def fix_lint(file_path: str) -> None:
    """Fix linting errors in a Python file using pylint."""
    try:
        # Run pylint on the file
        pylint_output = pylint.lint.Run([file_path], do_exit=False)

        # If there were any linting errors, print them and exit
        if pylint_output.linter.msg_status > 0:
            print(f"Linting errors found in {file_path}. Please fix them.")
            sys.exit(1)

    except Exception as e:
        print(f"An error occurred while linting {file_path}: {str(e)}")
        sys.exit(1)

    print(f"No linting errors found in {file_path}.")

# Run the function on the target file
fix_lint('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')