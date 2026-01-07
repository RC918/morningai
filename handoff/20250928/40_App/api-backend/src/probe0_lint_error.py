import autopep8
import os
from typing import NoReturn


def fix_lint_errors(file_path: str) -> NoReturn:
    """Fix lint errors in a Python file using autopep8.

    Args:
        file_path (str): Path to the Python file.
    """

    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} does not exist.")
        return

    # Check if file is a Python file
    if not file_path.endswith(".py"):
        print(f"Error: {file_path} is not a Python file.")
        return

    try:
        # Read original file
        with open(file_path, "r") as input_file:
            file_contents = input_file.read()

        # Fix lint errors
        fixed_contents = autopep8.fix_code(file_contents)

        # Write fixed contents back to file
        with open(file_path, "w") as output_file:
            output_file.write(fixed_contents)

        print(f"Lint errors in {file_path} have been fixed.")

    except Exception as e:
        print(f"Error fixing lint errors in {file_path}: {e}")


# Target file path
file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

# Fix lint errors in target file
fix_lint_errors(file_path)