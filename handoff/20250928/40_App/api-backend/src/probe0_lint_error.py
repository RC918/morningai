# Required Libraries
import subprocess
import sys

def run_test_suite(test_file: str, test_class: str) -> None:
    """
    This function runs the test suite locally focusing on a specific test class.

    Args:
        test_file (str): The python file with the tests.
        test_class (str): The class with the tests to be focused on.

    Returns:
        None
    """

    try:
        # Running the full test suite locally
        subprocess.check_call(["pytest", test_file])

        # Focusing on 'TestDashboard503Integration' tests
        subprocess.check_call(["pytest", f"{test_file}::{test_class}"])

    except subprocess.CalledProcessError as err:
        # If a non-zero exit status was returned, print the error and exit
        print(f'Error: {err}')
        sys.exit(1)

    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run_test_suite('test_dashboard.py', 'TestDashboard503Integration')