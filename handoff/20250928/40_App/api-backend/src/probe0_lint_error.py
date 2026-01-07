import os
from typing import Any, Optional

def read_write_file(file_path: str, data: Optional[Any] = None) -> Optional[str]:
    """
    Function to read and write data to a file

    Args:
        file_path (str): Path to the file
        data (Optional[Any], optional): Data to write to the file. Defaults to None.

    Returns:
        Optional[str]: Data read from the file if data param is None, else None
    """
    try:
        if data is not None:
            with open(file_path, 'w') as file:
                file.write(data)
        else:
            with open(file_path, 'r') as file:
                return file.read()
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Assuming we have the fixes for the lint errors in 'fixed_code_str'
# We write the fixed code to the file
fixed_code_str = ""
file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
read_write_file(file_path, fixed_code_str)