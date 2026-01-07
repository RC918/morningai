import subprocess
import pylint
from pylint import epylint as lint

def lint_and_fix(file_path: str):
    """Lint and fix a python file."""
    (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)
    
    if pylint_stderr.getvalue():
        print(f"Error while linting {file_path}:")
        print(pylint_stderr.getvalue())
        return False
    
    lint_output = pylint_stdout.getvalue()
    if lint_output:
        print(f"Lint issues found in {file_path}:")
        print(lint_output)
        return False
    
    return True

def git_task(branch_name: str, file_path: str):
    """Commit the fixes to a new branch and create a follow-up PR."""
    try:
        # Create a new branch
        subprocess.check_call(["git", "checkout", "-b", branch_name])

        # Add the fixed file
        subprocess.check_call(["git", "add", file_path])

        # Commit the changes
        subprocess.check_call(["git", "commit", "-m", "fix lint issues"])

        # Push the branch to the remote repository
        subprocess.check_call(["git", "push", "origin", branch_name])

        print(f"Changes pushed to new branch {branch_name}. Please create a PR for validation.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the git task: {e.output}")

def main():
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    branch_name = 'fix-lint-issues'

    if not lint_and_fix(file_path):
        print("Failed to lint and fix the file. Exiting.")
        return

    git_task(branch_name, file_path)

if __name__ == "__main__":
    main()