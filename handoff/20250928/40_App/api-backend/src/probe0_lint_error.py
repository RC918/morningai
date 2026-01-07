import pylint.lint
import sys

def run_linter(target_files: str) -> None:
    """
    Run pylint on the specified python file
    """
    try:
        pylint_score = pylint.lint.Run([target_files], do_exit=False).linter.stats['global_note']
        if pylint_score < 10.0:
            print(f"Linter has found issues in {target_files} that need to be addressed.")
            print(f"Your code has been rated at {pylint_score}/10")
        else:
            print(f"{target_files} has passed the linting check with a score of {pylint_score}/10")
    except Exception as e:
        print(f"An error occurred while linting: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    target_files = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    run_linter(target_files)