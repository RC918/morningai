# Python libraries
import json
from typing import Any, Dict

# external libraries
from flake8.api import legacy as flake8


def lint_file(file_path: str) -> None:
    """
    Function to run flake8 linting on a file.
    :param file_path: Path of the file to lint.
    """

    style_guide = flake8.get_style_guide(ignore=['E501'])
    report = style_guide.check_files([file_path])

    if report.total_errors > 0:
        print(f"Linting errors found in {file_path}:")
        for error in report._deferred_assertions:
            print(error)
        raise SystemExit(1)
    else:
        print(f"No linting errors found in {file_path}.")


def validate_json(file_path: str) -> Dict[str, Any]:
    """
    Function to validate a JSON file.
    :param file_path: Path of the JSON file to validate.
    :return: The loaded JSON data if the file is valid.
    """

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {file_path}: {e}")
        raise SystemExit(1)


def main() -> None:
    """
    Main function to validate Python and JSON files.
    """

    file_path = "handoff/20250928/40_App/api-backend/src/probe0_lint_error.py"

    # Run flake8 linting
    lint_file(file_path)

    # Validate JSON
    json_file_path = file_path.replace('.py', '.json')
    validate_json(json_file_path)


if __name__ == "__main__":
    main()