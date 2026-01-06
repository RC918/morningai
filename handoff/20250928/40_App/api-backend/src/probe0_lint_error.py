import unittest

def run_tests() -> None:
    """
    Run unit tests on probe0_lint_error.py to ensure no regression is introduced.
    """
    try:
        # Define the test suite
        suite = unittest.TestLoader().loadTestsFromName('handoff.20250928.40_App.api-backend.tests.probe0_lint_error')
        
        # Run the test suite
        result = unittest.TextTestRunner().run(suite)
        
        # If there was a failure or error, raise an exception
        if len(result.failures) > 0 or len(result.errors) > 0:
            raise Exception('Unit tests failed.')
    except Exception as e:
        print(f'Error occurred while running the tests: {str(e)}')
        return

    print('All tests passed successfully.')

if __name__ == "__main__":
    run_tests()