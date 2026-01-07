import pylint.lint

def lint_file(file_path: str) -> None:
    try:
        pylint_opts = [file_path]
        pylint.lint.Run(pylint_opts)
    except Exception as e:
        print(f"An error occurred during linting: {e}")

# specify the file path
file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

lint_file(file_path)