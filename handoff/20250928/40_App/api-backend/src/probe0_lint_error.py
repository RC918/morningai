# Importing required module
import pylint.lint

# Linting the target file
try:
    pylint_output = pylint.lint.Run(['handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'], do_exit=False)
    print("Pylint completed without a problem.")
except Exception as e:
    print("There was a problem with Pylint:")
    print(str(e))