import subprocess
from typing import NoReturn

def commit_and_push_changes(file_path: str) -> NoReturn:
    """
    This function adds the fixed file to the staging area, commits the changes and then pushes the changes to the PR branch.
    
    Parameters:
    file_path (str): The file path to the file that has been fixed.
    
    Returns:
    NoReturn
    """

    try:
        # Adding the fixed file to the staging area
        subprocess.check_call(['git', 'add', file_path])
        print(f"Added {file_path} to the staging area.")
        
        # Committing the changes
        commit_message = "Fixed lint errors"
        subprocess.check_call(['git', 'commit', '-m', commit_message])
        print(f"Committed changes with message: '{commit_message}'")
        
        # Pushing the changes to the PR branch
        subprocess.check_call(['git', 'push'])
        print("Pushed changes to the PR branch successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to commit and push changes: {e}")
        return

# Call the function with the file path
commit_and_push_changes("handoff/20250928/40_App/api-backend/src/probe0_lint_error.py")