"""
Test file to trigger Slow Path verification in Hybrid Router.

This file contains intentional issues designed to trigger:
- verdict: request_changes
- severity: medium or higher

DO NOT MERGE - This is a test file for Slow Path verification only.
Delete after verification is complete.
"""
import os
import logging

logger = logging.getLogger(__name__)


def unsafe_file_operation(user_input: str) -> str:
    """
    INTENTIONAL BUG: This function has path traversal vulnerability.
    User input is directly used in file path without sanitization.

    This should trigger medium+ severity from the reviewer.
    """
    # BUG: No input validation - allows path traversal
    file_path = f"/data/{user_input}"

    # BUG: Silently swallowing exceptions hides errors
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception:
        pass  # BUG: Silent exception swallowing

    return ""


def process_user_data(data: dict) -> dict:
    """
    INTENTIONAL BUG: Missing input validation and error handling.
    """
    # BUG: No type checking or validation
    result = data["value"] * 2  # Will crash if "value" missing

    # BUG: Modifying input dict directly (side effect)
    data["processed"] = True

    return {"result": result}


def execute_command(cmd: str) -> None:
    """
    INTENTIONAL BUG: Command injection vulnerability.
    """
    # BUG: Direct shell command execution without sanitization
    os.system(f"echo {cmd}")  # Command injection risk


class DataProcessor:
    """Processor with intentional architectural issues."""

    def __init__(self):
        # BUG: Hardcoded configuration that should be configurable
        self.max_retries = 3
        self.timeout = 30

    def process(self, items: list) -> list:
        """
        INTENTIONAL BUG: Inefficient algorithm and missing error handling.
        """
        results = []
        # BUG: O(n^2) complexity when O(n) is possible
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j:
                    results.append(items[i])

        return results
