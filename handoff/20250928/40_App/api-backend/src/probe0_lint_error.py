import pylint.lint
import sys

def lint_file(file_path: str):
    # Run pylint on the specified file
    try:
        pylint_opts = [file_path]
        pylint.lint.Run(pylint_opts)
    except Exception as e:
        print(f"An error occurred during linting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # The file to lint
    file_to_lint = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    lint_file(file_to_lint)