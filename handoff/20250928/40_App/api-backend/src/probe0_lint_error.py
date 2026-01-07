import subprocess
import sys
from typing import Tuple

def git_add_commit_push(target_files: str, commit_message: str = "Fix lint errors") -> None:
    try:
        # Stage the changes
        subprocess.check_call(['git', 'add', target_files], stderr=subprocess.STDOUT)

        # Commit the changes
        subprocess.check_call(['git', 'commit', '-m', commit_message], stderr=subprocess.STDOUT)

        # Push the changes
        subprocess.check_call(['git', 'push', 'origin', 'HEAD'], stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to add, commit, or push. Details: {e.output}")
        sys.exit(1)

def trigger_ci_pipeline() -> Tuple[bool, str]:
    try:
        # Here we are assuming you have a command to trigger your CI pipeline
        # Replace with your actual command
        output = subprocess.check_output(['trigger', 'ci', 'pipeline'], stderr=subprocess.STDOUT)

        # Assuming a successful pipeline run outputs "Success"
        if "Success" in output:
            return True, output
        else:
            return False, output

    except subprocess.CalledProcessError as e:
        return False, e.output

def main() -> None:
    target_files = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    git_add_commit_push(target_files)

    success, output = trigger_ci_pipeline()

    if not success:
        print("CI pipeline failed with the following output:")
        print(output)
        sys.exit(1)

if __name__ == "__main__":
    main()