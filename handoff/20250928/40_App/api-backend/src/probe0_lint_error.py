import subprocess
from typing import NoReturn

def run_linter_on_file(file_path: str) -> NoReturn:
    """
    Function to run linting tool on the specified file
    Args:
    file_path (str): Path to the file where linting needs to be performed

    Returns:
    NoReturn: Just prints the output of the linting process
    """
    try:
        # Assuming pylint is the linting tool
        # subprocess.check_output function runs the command and returns its output.
        lint_output = subprocess.check_output(f"pylint {file_path}", shell=True)
        lint_output = lint_output.decode("utf-8")
        
        if lint_output:
            print(f"Linting output for {file_path}:\n{lint_output}")
        else:
            print(f"No linting issues found in {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Linting failed for {file_path} with error:\n{str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Running the function on the target file
run_linter_on_file("handoff/20250928/40_App/api-backend/src/probe0_lint_error.py")