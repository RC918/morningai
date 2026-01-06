# python
import os
from pylint import epylint as lint

def fix_lint(file_path: str) -> None:
    """
    This function runs pylint on the provided python file and prints the lint errors

    Args:
    file_path (str): Path to the file to lint

    Returns:
    None
    """
    (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)

    if pylint_stdout.getvalue() != "":
        print(f"Pylint stdout for file {file_path}:")
        print(pylint_stdout.getvalue())

    if pylint_stderr.getvalue() != "":
        print(f"Pylint stderr for file {file_path}:")
        print(pylint_stderr.getvalue())

# replace with the exact path of your python file
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py' 

# check if the file exists
if os.path.exists(file_path):
    fix_lint(file_path)
else:
    print(f"File {file_path} does not exist.\nPlease check the file path.")