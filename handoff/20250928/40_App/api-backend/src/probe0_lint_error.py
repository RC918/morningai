import subprocess
import sys

def fix_lint_error(file_path: str, commit_message: str, branch_name: str):
    try:
        # Add the updated file to the Git staging area
        subprocess.check_call(['git', 'add', file_path])

        # Commit the changes
        subprocess.check_call(['git', 'commit', '-m', commit_message])

        # Push the changes to the PR branch
        subprocess.check_call(['git', 'push', 'origin', branch_name])

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing changes: {e}", file=sys.stderr)
        sys.exit(1)

# Use the function
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
commit_message = 'Fix lint error in probe0_lint_error.py'
branch_name = '<pr-branch-name>'  # Replace with your PR branch name
fix_lint_error(file_path, commit_message, branch_name)