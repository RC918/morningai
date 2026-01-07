import pylint.lint

try:
    # Path to the file to lint
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py" 

    # Run the linter on the file
    pylint_output = pylint.lint.Run([file_path], do_exit=False)

    # Get the final score after linting
    final_score = pylint_output.linter.stats['global_note']

    print(f'Final lint score for the file is: {final_score}')

except Exception as e:
    print(f'An error occurred during linting: {e}')