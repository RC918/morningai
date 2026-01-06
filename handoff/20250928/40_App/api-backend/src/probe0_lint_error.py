# Import necessary modules
import autopep8
import os

# Specify the target file
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

def fix_lint(file_path: str) -> None:
    """
    Function to fix lint errors in a Python file using autopep8.

    Parameters:
    file_path (str): The path of the Python file to fix.

    Returns:
    None
    """
    try:
        # Check if the file exists
        if os.path.isfile(file_path):
            # Fix the file in-place
            autopep8.fix_file(file_path, options={'aggressive': 1, 'in_place': True})
            print(f'Successfully fixed linting errors in {file_path}')
        else:
            print(f'The file {file_path} does not exist.')
    except Exception as e:
        print(f'An error occurred while trying to fix lint errors in {file_path}: {str(e)}')

# Call the function
fix_lint(file_path)