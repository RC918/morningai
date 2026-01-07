import pylint.lint
import sys

def lint_file(file_path: str) -> None:
    """
    Run pylint on a given file.

    Args:
        file_path: The path of the file to lint.
    """
    try:
        pylint_score = pylint.lint.Run([file_path], do_exit=False).linter.stats['global_note']
        if pylint_score < 10:
            print(f"Linting errors found in {file_path}. Please review and fix.")
        else:
            print(f"No linting errors found in {file_path}.")
    except Exception as e:
        print(f"Error occurred while linting {file_path}: {str(e)}")
        sys.exit(1)

# Target file to lint
target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

lint_file(target_file)