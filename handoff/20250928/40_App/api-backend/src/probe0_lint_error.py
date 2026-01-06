import os
import subprocess
import sys
from typing import NoReturn

def run_tests_and_lint() -> NoReturn:
    """
    This function runs the local test suite for 'TestDashboard503Integration' and runs pylint on the target file.
    """
    target_files = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'
    test_suite = 'TestDashboard503Integration'

    # Run the test suite
    try:
        subprocess.check_call(['pytest', '-k', test_suite])
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}. Test suite {test_suite} failed.")
        sys.exit(1)

    # Run pylint on the target file
    try:
        subprocess.check_call(['pylint', target_files])
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}. Pylint check failed for {target_files}")
        sys.exit(1)

    print("All tests passed and no lint errors found.")

if __name__ == "__main__":
    run_tests_and_lint()