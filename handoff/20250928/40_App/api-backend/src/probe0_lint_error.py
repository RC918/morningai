import pylint.lint
import sys

def lint_file(file_path: str) -> None:
    try:
        # Run PyLint on the file
        pylint_opts = [file_path]
        pylint.lint.Run(pylint_opts)
    except Exception as e:
        print(f"An error occurred during linting: {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    file_to_lint = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    lint_file(file_to_lint)

if __name__ == "__main__":
    main()