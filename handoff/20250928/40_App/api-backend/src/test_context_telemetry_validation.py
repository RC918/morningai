"""
Test file for Context Manager Telemetry validation.
This file intentionally contains a lint error (unused import) to trigger AutoFixer.
The AutoFixer workflow will call LLM Planner which uses get_code_context(),
triggering the new telemetry events: [CONTEXT_FILE_SCAN], [CONTEXT_FILE_SELECT], [CONTEXT_TOKEN_BUDGET]
"""
import sys  # F401: unused import - intentional lint error
import os


def validate_telemetry():
    """Simple function to validate telemetry is working."""
    cwd = os.getcwd()
    return f"Current working directory: {cwd}"


if __name__ == "__main__":
    print(validate_telemetry())
