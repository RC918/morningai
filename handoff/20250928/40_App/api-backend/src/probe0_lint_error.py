import linting_tool

def lint_and_fix_errors(file_path: str):
    try:
        linting_report = linting_tool.lint_file(file_path)
        print(f"Linting report for {file_path}:\n\n{linting_report}")

        if linting_report.has_errors():
            print(f"Fixing linting errors for {file_path}...")
            fixed_code = linting_tool.fix_errors(file_path)
            with open(file_path, 'w') as file:
                file.write(fixed_code)
            print(f"Fixed linting errors for {file_path}.")

        else:
            print(f"No linting errors found in {file_path}.")

    except Exception as e:
        print(f"An error occurred while linting and fixing {file_path}: {e}")


if __name__ == "__main__":
    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"
    lint_and_fix_errors(file_path)