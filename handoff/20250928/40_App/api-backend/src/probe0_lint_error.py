# import necessary libraries
import pylint.lint

# target file
target_files = ["handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"]

# run pylint on target file
pylint.lint.Run(target_files)