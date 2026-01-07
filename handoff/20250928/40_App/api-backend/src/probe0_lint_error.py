import subprocess
import sys
from typing import List

def git_commit(file: str, commit_message: str) -> None:
    """
    This function stages and commits a file using git.
    Args:
        file (str): The file to commit.
        commit_message (str): The commit message.
    """
    try:
        # Stage the file
        subprocess.check_output(['git', 'add', file])
        # Commit the file
        subprocess.check_output(['git', 'commit', '-m', commit_message])
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while committing the file: {e.output}", file=sys.stderr)

def fix_lint(target_files: List[str]) -> None:
    """
    This function fixes lint issues and commits the changes to the repository.
    Args:
        target_files (List[str]): The list of files to fix and commit.
    """
    for file in target_files:
        try:
            # Fix lint issues
            subprocess.check_output(['autopep8', '--in-place', '--aggressive', file])
            # Commit the changes
            git_commit(file, "Fixed lint errors")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while fixing lint errors in the file: {e.output}", file=sys.stderr)

if __name__ == "__main__":
    target_files = ['handoff/20250928/40_App/api-backend/src/probe0_lint_error.py']
    fix_lint(target_files)