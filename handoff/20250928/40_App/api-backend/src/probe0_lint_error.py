import pylint.lint

def lint_check(file_path: str) -> None:
    try:
        # Run Pylint on the specified file
        pylint_output = pylint.lint.Run([file_path], do_exit=False)

        # Check if there are any messages recorded by Pylint
        if pylint_output.linter.msg_status > 0:
            print(f'Linting errors found in {file_path}. Please fix them.')
        else:
            print(f'No linting errors found in {file_path}. The file is clean.')

    except Exception as e:
        print(f'An error occurred while linting the file: {e}')

# Specify the path of the target file
target_file = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

# Call the function with the target file
lint_check(target_file)