import pylint
from pylint import epylint as lint

def fix_lint(file_path: str) -> None:
    (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)

    if pylint_stderr.getvalue():
        print(f"Error in pylint linting: {pylint_stderr.getvalue()}")
        return

    lint_output = pylint_stdout.getvalue()
    if lint_output:
        print(f"Linting issues found in {file_path}:\n{lint_output}")
    else:
        print(f"No linting issues found in {file_path}")

if __name__ == "__main__":
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    fix_lint(file_path)