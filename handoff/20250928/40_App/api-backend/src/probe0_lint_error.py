import os
import sys
from pylint import epylint as lint

def main() -> None:
    # Define the file to be linted
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    try:
        # Run pylint on the file
        (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)

        # Print the output
        print(pylint_stdout.getvalue())
        print(pylint_stderr.getvalue())

        if pylint_stdout.getvalue() != '':
            print("Linting errors found. Please fix them.")

        if pylint_stderr.getvalue() != '':
            print("An error occurred while linting. Please check the file.")

    except Exception as err:
        print(f"An unexpected error occurred: {err}")

if __name__ == "__main__":
    main()