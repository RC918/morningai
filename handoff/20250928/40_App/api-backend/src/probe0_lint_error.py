import os
import subprocess
from typing import Tuple

def commit_and_push(file_path: str, branch_name: str, commit_message: str) -> Tuple[bool, str]:
    """
    Commit and push changes to a given file on a specific branch with a specific commit message.

    :param file_path: The path to the file that has been changed.
    :param branch_name: The name of the branch on which changes should be pushed.
    :param commit_message: The commit message to use.
    :return: A tuple where the first element is a boolean indicating success and the second element is an error message in case of failure.
    """
    try:
        # Stage the file for commit
        subprocess.check_call(['git', 'add', file_path])

        # Commit the changes
        subprocess.check_call(['git', 'commit', '-m', commit_message])

        # Push the changes to the branch
        subprocess.check_call(['git', 'push', 'origin', branch_name])

        return True, ""

    except subprocess.CalledProcessError as e:
        return False, str(e)

def main():
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    branch_name = 'PR-3627'
    commit_message = 'Fix lint errors to trigger CI pipeline'

    success, error_message = commit_and_push(file_path, branch_name, commit_message)

    if not success:
        print(f"An error occurred while committing and pushing changes: {error_message}")
        os._exit(1)  # Exit with an error code

if __name__ == "__main__":
    main()