import subprocess
import os

def commit_and_push_changes(file_path: str, commit_message: str = "fix lint errors") -> None:
    try:
        # Stage the file
        subprocess.check_output(['git', 'add', file_path])
        
        # Commit the changes
        subprocess.check_output(['git', 'commit', '-m', commit_message])
        
        # Push the changes
        subprocess.check_output(['git', 'push'])
        print("Changes committed and pushed successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to commit and push changes.")
        print("Error:", e.output)

# Specify the target file
target_file = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

# Commit and push the changes
commit_and_push_changes(target_file)