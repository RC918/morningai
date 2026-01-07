import pylint.lint
import sys

def run_linter_on_file(file_path: str) -> None:
    """
    Runs pylint on the specified file and prints out any linting errors

    Parameters:
    file_path(str): Path to the file to lint
    """
    try:
        pylint_output = pylint.lint.Run([file_path], do_exit=False)
        linting_errors = pylint_output.linter.msg_status
        if linting_errors:
            print(f"Linting errors found in {file_path}. Please fix the errors and try again.")
        else:
            print(f"No linting errors found in {file_path}. File is ready for production.")
    except Exception as e:
        print(f"An error occurred while trying to lint the file at {file_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_linter_on_file("handoff/20250928/40_App/api-backend/src/probe0_lint_error.py")