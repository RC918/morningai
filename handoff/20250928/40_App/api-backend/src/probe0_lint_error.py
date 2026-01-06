import subprocess
from typing import Tuple

def run_linter(file: str) -> Tuple[int, str]:
    """
    Run linter on the given file and return the exit code and output.

    :param file: The file to run the linter on.
    :return: A tuple containing the exit code and output.
    """
    try:
        output = subprocess.check_output(["pylint", file])
        return 0, output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8")

def main() -> None:
    """
    Main function to run the linter on the target file and print the result.
    """
    target_file = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    exit_code, output = run_linter(target_file)

    if exit_code == 0:
        print("No linting errors found.")
    else:
        print(f"Linting errors found in {target_file}:\n{output}")

if __name__ == "__main__":
    main()