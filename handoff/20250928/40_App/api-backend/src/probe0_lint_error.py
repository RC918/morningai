import autopep8
import pylint.lint
import os
import sys

def lint_and_fix(file_path: str) -> None:
    """
    Lint a Python file and attempt to automatically fix any issues.

    Args:
        file_path (str): Path to the Python file to lint.
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    # Run pylint on the file
    pylint_opts = [file_path]
    linter = pylint.lint.Run(pylint_opts, do_exit=False)
    
    # Print out the pylint score
    print(f"Pylint score for {file_path}: {linter.linter.stats['global_note']}")
    
    # If there are any linting issues, attempt to automatically fix them
    if linter.linter.stats['statement'] > 0:
        with open(file_path, "r") as source_file:
            fixed_source = autopep8.fix_code(source_file.read())
        
        # Write the fixed source code back to the file
        with open(file_path, "w") as source_file:
            source_file.write(fixed_source)
        
        print(f"Fixed linting issues in {file_path}")
    else:
        print(f"No linting issues found in {file_path}")

if __name__ == "__main__":
    # Path to the file to lint
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    
    try:
        lint_and_fix(file_path)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)