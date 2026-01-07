import subprocess
import os
from typing import NoReturn

def fix_lint(file_path: str) -> NoReturn:
    """
    Fix linting errors in the file using autopep8
    """
    try:
        subprocess.check_call(['autopep8', '--in-place', '--aggressive', '--aggressive', file_path])
        print(f"Linting errors in {file_path} have been fixed.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fixing linting errors in {file_path}: {str(e)}")

def commit_changes(file_path: str) -> NoReturn:
    """
    Commit the corrected file
    """
    try:
        subprocess.check_call(['git', 'add', file_path])
        subprocess.check_call(['git', 'commit', '-m', 'Fix linting errors'])
        print(f"Changes in {file_path} have been committed.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while committing the changes in {file_path}: {str(e)}")

def push_changes(branch_name: str) -> NoReturn:
    """
    Push the changes to the branch
    """
    try:
        subprocess.check_call(['git', 'push', 'origin', branch_name])
        print(f"Changes have been pushed to the branch {branch_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while pushing the changes to the branch {branch_name}: {str(e)}")

def main() -> NoReturn:
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    branch_name = "feature/fix-lint-errors" # Assuming the branch name
    fix_lint(file_path)
    commit_changes(file_path)
    push_changes(branch_name)

if __name__ == "__main__":
    main()