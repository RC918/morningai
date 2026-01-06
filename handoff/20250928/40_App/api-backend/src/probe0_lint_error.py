import pylint.lint

def lint_file(file_path: str) -> None:
    try:
        pylint_output = pylint.lint.Run([file_path], do_exit=False)
        for message in pylint_output.linter.reporter.messages:
            print(f"Line {message.line}: {message.msg}")
    except Exception as e:
        print(f"An error occurred while linting: {e}")

if __name__ == "__main__":
    lint_file('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')