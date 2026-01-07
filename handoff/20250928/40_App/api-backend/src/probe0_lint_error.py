import pylint.lint
import sys

def lint_file(file_path: str) -> None:
    """
    Lint a Python file and print the report.

    :param file_path: Path to the file to lint.
    """
    pylint_opts = [file_path]
    linter = pylint.lint.Run(pylint_opts, do_exit=False)

    if linter.linter.msg_status > 0:
        print(f"Linting errors found in {file_path}. Please fix them.")
        sys.exit(1)
    else:
        print(f"No linting errors found in {file_path}. The file is clean.")

if __name__ == "__main__":
    try:
        file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
        lint_file(file_path)
    except Exception as e:
        print(f"Error: {str(e)}")