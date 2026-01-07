import os
import subprocess

def commit_changes(file_path: str, commit_message: str) -> None:
    """
    This function commits changes to the specified file with the given commit message.
    """
    try:
        subprocess.check_call(['git', 'add', file_path])
        subprocess.check_call(['git', 'commit', '-m', commit_message])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while committing changes: {str(e)}")
        raise

def push_changes(remote: str, branch: str) -> None:
    """
    This function pushes changes to the specified remote and branch.
    """
    try:
        subprocess.check_call(['git', 'push', remote, branch])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while pushing changes: {str(e)}")
        raise

def fix_lint(file_path: str) -> None:
    """
    This function fixes linting issues in the specified file and pushes the changes.
    """
    # Run lint fix command
    try:
        subprocess.check_call(['python', '-m', 'autopep8', '--in-place', '--aggressive', '--aggressive', file_path])
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while fixing lint: {str(e)}")
        raise

    # Commit and push changes
    commit_message = "Fix lint errors"
    commit_changes(file_path, commit_message)
    push_changes('origin', 'main')


if __name__ == '__main__':
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    fix_lint(file_path)