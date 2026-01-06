import pylint.lint
import sys

def check_lint_errors(file_path: str) -> None:
    """
    Function to check linting errors in a given python file.
    :param file_path: str: Path to the python file
    :return: None
    """
    try:
        pylint_output = pylint.lint.Run([file_path], do_exit=False)
        print("Pylint completed with exit code: ", pylint_output.linter.msg_status)
    except Exception as e:
        print("An error occurred while running pylint: ", str(e))

if __name__ == "__main__":
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    check_lint_errors(file_path)