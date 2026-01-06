import pylint
from pylint import epylint as lint

def lint_errors(file_path: str) -> None:
    """
    Function to run pylint on a python file and print the linting errors
    """
    (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)

    if pylint_stdout.getvalue():
        print("Pylint stdout:")
        print(pylint_stdout.getvalue())

    if pylint_stderr.getvalue():
        print("Pylint stderr:")
        print(pylint_stderr.getvalue())

if __name__ == "__main__":
    lint_errors('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')