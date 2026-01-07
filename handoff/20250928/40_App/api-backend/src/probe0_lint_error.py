import pylint.lint

try:
    pylint_opts = ['handoff/20250928/40_App/api-backend/src/probe0_lint_error.py']
    pylint.lint.Run(pylint_opts)
except Exception as e:
    print(f"An error occurred: {e}")