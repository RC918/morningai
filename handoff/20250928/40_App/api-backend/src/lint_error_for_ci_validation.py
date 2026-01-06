import yaml
from typing import Any

def check_yaml_syntax(file_path: str) -> Any:
    """
    Check for syntax errors in a YAML file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Parsed YAML file content if no error, else None.
    """
    try:
        with open(file_path, 'r') as file:
            content = yaml.safe_load(file)
            print(f"No syntax errors found in {file_path}.\nFile content:\n{content}")
            return content
    except yaml.YAMLError as exc:
        print(f"Error in {file_path}")
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            print("Error position: (%s:%s)" % (mark.line+1, mark.column+1))
        return None

check_yaml_syntax('.github/workflows/openapi-verify.yml')