import pycodestyle

def check_lint(file_path: str) -> None:
    """Check a file for PEP 8 compliance."""
    style_guide = pycodestyle.StyleGuide()
    result = style_guide.check_files([file_path])

    print(f"Total errors in {file_path}: {result.total_errors}")

check_lint('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')