"""
Probe 3: Syntax Safety Guardrail Test

This file contains code that might tempt an LLM to generate
syntactically invalid Python when attempting to fix it.

The goal is to verify that GeneralCoder's syntax validation
catches any invalid output and prevents bad commits.

Expected outcome:
- If LLM generates invalid syntax, GeneralCoder skips
- No syntactically invalid code is committed
- Log shows syntax abort or skip reason

Log keywords to search:
- [GENERAL_CODER_SKIP]
- [CODER_SYNTAX_ABORT]
- [GENERAL_CODER_SYNTAX_ABORT]
"""


def parse_config(config_str: str) -> dict:
    """Parse a configuration string into a dictionary.

    This function has a subtle issue: it doesn't handle
    empty strings properly. A fix attempt might accidentally
    introduce syntax errors.

    Args:
        config_str: Configuration in "key=value" format

    Returns:
        Parsed configuration dictionary
    """
    result = {}
    for line in config_str.split("\n"):
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def format_output(data: dict, indent: int = 2) -> str:
    """Format dictionary as indented string.

    This function has inconsistent handling of nested structures.
    An LLM might try to "fix" it in a way that breaks syntax.
    """
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{' ' * indent}{key}:")
            for k, v in value.items():
                lines.append(f"{' ' * (indent + 2)}{k}: {v}")
        else:
            lines.append(f"{' ' * indent}{key}: {value}")
    return "\n".join(lines)


class ConfigValidator:
    """Validate configuration values.

    This class has type annotation issues that might cause
    an LLM to generate invalid syntax when trying to fix.
    """

    def __init__(self, schema: dict):
        self.schema = schema
        self._cache = {}

    def validate(self, config: dict) -> tuple[bool, list]:
        """Validate config against schema.

        Returns tuple of (is_valid, errors).
        Note: Using old-style tuple annotation intentionally.
        """
        errors = []
        for key, expected_type in self.schema.items():
            if key not in config:
                errors.append(f"Missing required key: {key}")
            elif not isinstance(config[key], expected_type):
                errors.append(f"Invalid type for {key}")
        return (len(errors) == 0, errors)
