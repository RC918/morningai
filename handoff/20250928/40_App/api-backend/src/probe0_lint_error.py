import subprocess
from typing import NoReturn

def commit_and_push_changes(file_path: str, commit_message: str) -> NoReturn:
    try:
        # Stage the file for commit
        subprocess.check_call(['git', 'add', file_path])

        # Commit the changes
        subprocess.check_call(['git', 'commit', '-m', commit_message])

        # Push the changes to the remote repository
        subprocess.check_call(['git', 'push'])
        
        print("Changes committed and pushed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while committing and pushing changes: {str(e)}")

commit_and_push_changes("handoff/20250928/40_App/api-backend/src/probe0_lint_error.py", "Fix lint errors in probe0_lint_error.py")