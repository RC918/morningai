# Import required modules
import pylint.lint

# Specify the file to lint
file_to_lint = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

# Run the linter
pylint_output = pylint.lint.Run([file_to_lint], do_exit=False)

# Extract and print any errors
for msg in pylint_output.linter.reporter.messages:
    print(f'Line {msg.line}, Col {msg.column}: {msg.msg} ({msg.symbol})')