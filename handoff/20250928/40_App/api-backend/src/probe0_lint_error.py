# Here is a general way of cleaning up a python file

# Import necessary libraries
import pep8
from autopep8 import fix_code

# Open the file
with open('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py', 'r+') as file:
    # Read the content
    content = file.read()

    # Fix the code
    fixed_content = fix_code(content)

    # Clear the file content
    file.seek(0)
    file.truncate()

    # Write the fixed content back to file
    file.write(fixed_content)

# Now, create a checker and check if there are still issues
checker = pep8.Checker('handoff/20250928/40_App/api-backend/src/probe0_lint_error.py')
errors = checker.check_all()

# If there are still issues, print them out
if errors > 0:
    print(f"There are still {errors} PEP8 issues.")
else:
    print("No PEP8 issues found.")