# Python
import os
from typing import NoReturn

def fix_lint(file_path: str) -> NoReturn:
    """
    Function to fix common lint errors
    """
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        with open(file_path, 'w') as file:
            for line in lines:
                # remove trailing whitespaces
                line = line.rstrip() 
                # make sure there are spaces around operators
                line = ' '.join(line.split())
                file.write(line)

    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    fix_lint(file_path)

if __name__ == "__main__":
    main()