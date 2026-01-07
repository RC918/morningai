import pylint.lint

def lint_check(file_path: str) -> None:
    """
    Function to run pylint on a given file and print the report
    :param file_path: string, path of the python file to lint
    :return: None
    """
    try:
        pylint_output = pylint.lint.Run([file_path], do_exit=False)
        for message in pylint_output.linter.reporter.messages:
            print(f"Line {message.line}, {message.msg_id}: {message.msg} in {message.obj}")
    except Exception as e:
        print(f"An error occurred while linting: {str(e)}")

# Run the lint check on the target file
lint_check('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')