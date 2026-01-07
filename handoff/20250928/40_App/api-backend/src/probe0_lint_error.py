import subprocess
import sys
from typing import Tuple

def execute_command(command: str) -> Tuple[int, str]:
    """Execute a command and return its output"""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return 0, output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode('utf-8')

def commit_and_push_changes() -> None:
    """Commit the changes and push them to the remote repository"""
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    commit_message = "Fix lint issues"

    # Add the file to staging
    return_code, output = execute_command(f"git add {file_path}")
    if return_code != 0:
        print(f"Failed to add file {file_path} to staging. Error: {output}")
        sys.exit(1)
    
    # Commit the changes
    return_code, output = execute_command(f'git commit -m "{commit_message}"')
    if return_code != 0:
        print(f"Failed to commit changes. Error: {output}")
        sys.exit(1)

    # Push the changes
    return_code, output = execute_command("git push")
    if return_code != 0:
        print(f"Failed to push changes. Error: {output}")
        sys.exit(1)

    print("Changes pushed successfully")

if __name__ == "__main__":
    commit_and_push_changes()