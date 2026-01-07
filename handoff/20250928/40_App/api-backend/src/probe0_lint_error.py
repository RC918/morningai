import pylint.lint

def lint_file(file_path: str) -> None:
    """
    Function to lint a file and print out issues.

    Args:
        file_path (str): The path to the file to lint.
    """
    try:
        pylint_output = pylint.lint.Run([file_path], exit=False)
        if pylint_output.linter.msg_status > 0:
            print(f"Linting issues found in {file_path}. Please review.")
        else:
            print(f"No linting issues found in {file_path}.")
    except Exception as e:
        print(f"An error occurred while linting {file_path}. Error: {str(e)}")

if __name__ == "__main__":
    lint_file('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')