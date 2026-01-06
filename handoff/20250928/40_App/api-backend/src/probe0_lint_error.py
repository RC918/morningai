import pylint.lint
from typing import List

def fix_lint_errors(file_path: str) -> None:
    """
    Runs Pylint on the given Python file and print out the detected lint errors
    """

    pylint_opts: List[str] = [file_path]
    linter = pylint.lint.Run(pylint_opts, do_exit=False)
    
    if linter.linter.msg_status > 0:
        print(f"Lint errors detected in {file_path}")
    else:
        print(f"No lint errors detected in {file_path}")

if __name__ == "__main__":
    # path to the file with potential lint errors
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    try:
        fix_lint_errors(file_path)
    except Exception as e:
        print(f"An error occurred: {e}")