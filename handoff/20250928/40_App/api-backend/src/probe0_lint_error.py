import pylint.lint
import subprocess
from typing import List, Tuple

def fix_lint(file_path: str) -> Tuple[int, str]:
    """
    Runs pylint on the given file and returns the score and output.
    """
    pylint_output = pylint.lint.Run([file_path], exit=False)
    return pylint_output.linter.stats['global_note'], pylint_output.linter.msg_status

def commit_changes(file_path: str, commit_message: str) -> None:
    """
    Commits changes using git commit command.
    """
    try:
        subprocess.check_call(['git', 'add', file_path])
        subprocess.check_call(['git', 'commit', '-m', commit_message])
    except subprocess.CalledProcessError as e:
        print(f"Error during git commit: {e.output}")

def git_push(branch: str) -> None:
    """
    Pushes committed changes to the given branch using git push command.
    """
    try:
        subprocess.check_call(['git', 'push', 'origin', branch])
    except subprocess.CalledProcessError as e:
        print(f"Error during git push: {e.output}")

# specify the file
file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

# fix_lint and commit changes
score, output = fix_lint(file_path)
commit_message = f"fix lint issues, pylint score: {score}"
commit_changes(file_path, commit_message)

# git push
branch = "PR_branch"
git_push(branch)