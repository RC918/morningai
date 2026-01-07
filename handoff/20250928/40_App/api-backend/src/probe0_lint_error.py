import subprocess
import sys

def main():
    """Main function to identify linting errors."""
    target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    try:
        process_output = subprocess.check_output(
            [sys.executable, "-m", "pylint", target_file]
        )
        print(process_output.decode())
    except subprocess.CalledProcessError as e:
        print(f"Pylint check failed: {e.output.decode()}")
    except Exception as e:
        print(f"An error occurred while running pylint: {str(e)}")

if __name__ == "__main__":
    main()