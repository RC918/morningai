import pylint
from pylint import epylint as lint

def lint_and_fix_errors(file_path: str) -> None:
    try:
        (pylint_stdout, pylint_stderr) = lint.py_run(file_path, return_std=True)
        
        if pylint_stdout.getvalue():
            print(f"Pylint stdout:\n{pylint_stdout.getvalue()}")
        if pylint_stderr.getvalue():
            print(f"Pylint stderr:\n{pylint_stderr.getvalue()}")
            
    except Exception as e:
        print(f"An error occurred while linting file: {e}")
        

if __name__ == "__main__":
    file_path = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    lint_and_fix_errors(file_path)