# Step 1: Import necessary modules
import subprocess
import sys

# Step 2: Define the target file
target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

# Step 3: Define a function to execute pylint and capture the output
def run_pylint(target_file: str) -> str:
    try:
        lint_output = subprocess.check_output(["pylint", target_file])
        return lint_output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running pylint: {str(e)}", file=sys.stderr)
        sys.exit(1)

# Step 4: Run the function and print the output
if __name__ == "__main__":
    lint_output = run_pylint(target_file)
    print(lint_output)