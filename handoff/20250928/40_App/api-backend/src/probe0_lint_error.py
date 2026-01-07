import pylint.lint
import logging

def lint_file(file_path: str) -> None:
    """
    Run pylint on the specified file and print the report

    Args:
        file_path (str): Path to the file to lint
    """

    try:
        linter = pylint.lint.Run([file_path], do_exit=False)
        print(linter.linter.stats['message-line'])
    except Exception as e:
        logging.error(f"Error occurred while running pylint: {e}")

# Run lint on the target file
lint_file('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')