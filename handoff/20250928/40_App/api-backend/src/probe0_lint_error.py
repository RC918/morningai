import pylint.lint
from typing import NoReturn

def run_linter_on_file(file_path: str) -> NoReturn:
    try:
        pylint_output = pylint.lint.Run(file_path, do_exit=False)
    except Exception as e:
        raise Exception(f"An error occurred while running pylint: {str(e)}")

    if pylint_output.linter.msg_status > 0:
        raise Exception("Pylint found issues in the code")
    else:
        print("No issues found by pylint")

if __name__ == "__main__":
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    run_linter_on_file(file_path)