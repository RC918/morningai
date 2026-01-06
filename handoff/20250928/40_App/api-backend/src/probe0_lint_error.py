import autopep8
import os

def fix_lint(target_file: str) -> None:
    try:
        with open(target_file, 'r') as file:
            raw_content = file.read()

        fixed_content = autopep8.fix_code(raw_content)

        with open(target_file, 'w') as file:
            file.write(fixed_content)

        print(f"Lint fixed for {target_file}")

    except Exception as e:
        print(f"Error occurred while fixing lint for {target_file}. Error: {e}")


target_file = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

fix_lint(target_file)