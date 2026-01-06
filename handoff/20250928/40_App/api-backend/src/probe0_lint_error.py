import os
import subprocess
from typing import Tuple
from git import Repo, GitCommandError

def fix_lint(file_path: str) -> Tuple[bool, str]:
    try:
        lint_result = subprocess.check_output(f"flake8 --max-line-length=120 {file_path}", shell=True, stderr=subprocess.STDOUT).decode()
        if lint_result:
            return False, lint_result
        else:
            return True, "No linting issues found"
    except subprocess.CalledProcessError as e:
        return False, str(e.output)

def commit_and_push(repo: Repo, branch_name: str, commit_message: str) -> None:
    try:
        repo.git.checkout(branch_name)
        repo.git.add(update=True)
        repo.git.commit('-m', commit_message)
        origin = repo.remote(name='origin')
        origin.push()
    except GitCommandError as e:
        print(f"Error: {str(e)}")

# Specify the path of the file that needs the lint fix
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

# Fix lint issues 
lint_status, lint_message = fix_lint(file_path)
if lint_status:
    print(lint_message)
else:
    print(f"Error: {lint_message}")
    exit(1)

# Specify the path of your repository and the branch name
repo_path = '<your_repo_path>'
branch_name = '<branch_name>'
repo = Repo(repo_path)

# Commit the fixed file and push the changes to the PR branch
commit_message = 'Fix lint issues and re-trigger CI'
commit_and_push(repo, branch_name, commit_message)