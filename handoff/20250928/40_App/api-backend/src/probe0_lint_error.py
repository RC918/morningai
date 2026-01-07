import pytest
import pylint
import subprocess
import sys
from typing import Tuple

def run_lint_and_tests(filepath: str) -> Tuple[int, int]:
    """
    Function to run lint check and tests on a python script.

    Parameters:
    filepath (str): path to the python script

    Returns:
    Tuple[int, int]: returns a tuple, first element is the lint score, second is the test result
    """
    
    # Run pylint on the specified file
    lint_score = pylint.lint.Run([filepath], exit=False).linter.stats['global_note']

    # Run pytest on the specified file
    test_result = pytest.main([filepath])

    return lint_score, test_result

if __name__ == "__main__":
    # Path to the python script
    filepath = 'handoff/20250928/40_App/api-backend/src/probe0_lint_error.py'

    try:
        lint_score, test_result = run_lint_and_tests(filepath)
        print(f"Lint score: {lint_score}")
        print(f"Test result: {test_result}")

        if lint_score < 10.0 or test_result != 0:
            print("Script failed either lint check or tests, check the above scores for more details.")
            sys.exit(1)

    except Exception as e:
        print("An error occurred while running lint check or tests.")
        print(str(e))
        sys.exit(1)