import pylint.lint
from typing import NoReturn

def run_linter_on_file(file_path: str) -> NoReturn:
    """
    Run the pylint linter on the specified file.

    Args:
        file_path (str): The path to the file to lint.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    try:
        pylint_opts = [file_path]
        pylint.lint.Run(pylint_opts)
    except FileNotFoundError as e:
        print(f"Error: {file_path} does not exist.")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    run_linter_on_file('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')