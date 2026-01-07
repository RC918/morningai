import pylint.lint

def run_linter(file_path: str):
    try:
        linter = pylint.lint.Run([file_path], do_exit=False)
        if linter.linter.stats['global_note'] < 7:  # replace 7 with your desired linting score
            print(f"Linting issues detected in {file_path}. Please review and fix.")
        else:
            print(f"No major linting issues detected in {file_path}.")
    except Exception as e:
        print(f"An error occurred while linting: {str(e)}")

if __name__ == "__main__":
    run_linter('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')