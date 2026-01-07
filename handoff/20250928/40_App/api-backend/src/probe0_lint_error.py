import subprocess
import sys

def main() -> None:
    """
    Main function to handle linting errors in probe0_lint_error.py
    """

    # Define the target file
    target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

    # Run the linter locally on the target file
    try:
        output = subprocess.check_output(["pylint", target_file])
    except subprocess.CalledProcessError as e:
        # Catch the exception when there are linting issues
        output = e.output

    # Decode the output from bytes to string
    output = output.decode("utf-8")

    if "Your code has been rated at" in output:
        print("No linting errors found.")
    else:
        print("Linting errors found:")
        print(output)


if __name__ == "__main__":
    main()