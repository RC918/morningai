# Import required libraries
import os
import pylint.lint

def check_lint_errors(file_path: str) -> None:
    """Check for linting errors in a given Python file.

    Args:
        file_path (str): Path to the Python file.
    """

    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"The file {file_path} does not exist.")
            return

        # Run pylint on the file
        pylint_output = pylint.lint.Run([file_path], do_exit=False)

        # Get the final score (the higher the score, the fewer linting issues)
        final_score = pylint_output.linter.stats['global_note']

        if final_score < 10:
            print(f"The file {file_path} has linting issues.")
            print("Pylint score: ", final_score)
        else:
            print(f"The file {file_path} has no linting issues.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

# Run the function on the target file
check_lint_errors('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')