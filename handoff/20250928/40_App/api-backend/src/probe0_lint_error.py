import pylint.lint

def review_lint_errors(file_path: str):
    try:
        linter = pylint.lint.Run([file_path], do_exit=False)
        if linter.linter.msg_status > 0:
            print(f'Linter found {linter.linter.msg_status} issues in {file_path}')
        else:
            print(f'No issues found in {file_path}')
    except Exception as e:
        print(f'An error occurred while linting: {e}')

review_lint_errors('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')