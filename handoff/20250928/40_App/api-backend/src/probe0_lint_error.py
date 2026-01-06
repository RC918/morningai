import subprocess
import sys

def run_git_command(command: str) -> None:
    try:
        subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        sys.exit(1)

def commit_and_push_changes(file_path: str) -> None:
    # Stage the file
    run_git_command(f"git add {file_path}")

    # Commit the changes
    run_git_command("git commit -m 'Fix lint errors to trigger CI pipeline'")

    # Push the changes to the remote repository
    run_git_command("git push origin master")

if __name__ == "__main__":
    target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    commit_and_push_changes(target_file)