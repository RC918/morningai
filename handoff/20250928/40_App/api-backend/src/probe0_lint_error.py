import os
import subprocess

def commit_and_push_changes(file_path: str, commit_message: str):
    try:
        # Add the file to git
        subprocess.check_call(['git', 'add', file_path])

        # Commit the changes
        subprocess.check_call(['git', 'commit', '-m', commit_message])

        # Push the changes
        subprocess.check_call(['git', 'push'])

        print("Changes committed and pushed successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to commit and push changes.")
        print("Error: ", str(e))

if __name__ == "__main__":
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    commit_message = "Fixed lint errors in probe0_lint_error.py"
    commit_and_push_changes(file_path, commit_message)