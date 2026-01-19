#!/usr/bin/env python3
"""
Configuration Coverage Validation Script

This script validates that production configuration values (prod.md) match
the environment variable schema definitions (env.schema.yaml).

Issue #4185: Create configuration validation script
Blueprint Alignment: Section 4.6 Evidence Ledger - Configuration Audit Trail

Usage:
    python scripts/validate_config_coverage.py [--prod-file PATH] [--schema-file PATH]

Exit codes:
    0: All validations passed
    1: Validation errors found (missing definitions, type mismatches, etc.)
    2: Configuration/file errors (missing files, parse errors)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# Default file paths
DEFAULT_PROD_FILE = Path(__file__).parent.parent / "attachments" / "prod.md"
DEFAULT_SCHEMA_FILE = Path(__file__).parent.parent / "config" / "env.schema.yaml"


def _is_int(value: str) -> bool:
    """Check if a string represents an integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    """Check if a string represents a float."""
    try:
        float(value)
        return True
    except ValueError:
        return False


# Type mapping for validation
TYPE_VALIDATORS = {
    "string": lambda v: isinstance(v, str),
    "integer": _is_int,
    "boolean": lambda v: v.upper() in ("TRUE", "FALSE", "YES", "NO", "1", "0"),
    "url": lambda v: v.startswith(("http://", "https://", "redis://", "rediss://", "postgresql://")),
    "secret": lambda v: isinstance(v, str),  # Secrets are just strings
    "float": _is_float,
}


def parse_prod_md(file_path: Path) -> dict[str, str]:
    """
    Parse prod.md file and extract environment variable values.

    The file format is expected to be:
        VARIABLE_NAME<tab>value

    Args:
        file_path: Path to the prod.md file

    Returns:
        Dictionary mapping variable names to their values
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Production config file not found: {file_path}")

    config = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Split by tab or whitespace
            parts = re.split(r"\t+|\s{2,}", line, maxsplit=1)
            if len(parts) == 2:
                var_name, value = parts
                config[var_name.strip()] = value.strip()
            elif len(parts) == 1 and parts[0]:
                # Variable with no value (might be intentional)
                config[parts[0].strip()] = ""

    return config


def parse_schema(file_path: Path) -> dict[str, dict[str, Any]]:
    """
    Parse env.schema.yaml and extract field definitions.

    Args:
        file_path: Path to the env.schema.yaml file

    Returns:
        Dictionary mapping variable names to their schema definitions
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Schema file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    if not schema or "fields" not in schema:
        raise ValueError(f"Invalid schema format: missing 'fields' key in {file_path}")

    fields = schema.get("fields")
    if fields is None:
        raise ValueError(f"Invalid schema format: 'fields' is null in {file_path}")
    if not isinstance(fields, dict):
        raise ValueError(f"Invalid schema format: 'fields' must be a dict in {file_path}")

    return fields


def validate_type(var_name: str, value: str, schema_type: str) -> tuple[bool, str]:
    """
    Validate that a value matches the expected type.

    Args:
        var_name: Variable name (for error messages)
        value: The value to validate
        schema_type: Expected type from schema

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = TYPE_VALIDATORS.get(schema_type)
    if validator is None:
        # Unknown type, skip validation
        return True, ""

    if not validator(value):
        return False, f"Type mismatch for {var_name}: expected {schema_type}, got '{value}'"

    return True, ""


def validate_choices(var_name: str, value: str, choices: list[Any]) -> tuple[bool, str]:
    """
    Validate that a value is in the allowed choices.

    Args:
        var_name: Variable name (for error messages)
        value: The value to validate
        choices: List of allowed values (may contain non-string types from YAML)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Normalize for case-insensitive comparison
    # Convert choices to strings first (YAML may parse as bool/int)
    normalized_value = value.lower()
    normalized_choices = [str(c).lower() for c in choices]

    if normalized_value not in normalized_choices:
        return False, f"Invalid choice for {var_name}: '{value}' not in {choices}"

    return True, ""


def validate_config(
    prod_config: dict[str, str],
    schema: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    """
    Validate production config against schema.

    Args:
        prod_config: Production configuration from prod.md
        schema: Schema definitions from env.schema.yaml

    Returns:
        Tuple of (errors, warnings, info_messages)
    """
    errors = []
    warnings = []
    info = []

    # Track which schema variables are covered
    schema_vars = set(schema.keys())
    prod_vars = set(prod_config.keys())

    # 1. Check for variables in prod.md but not in schema
    undefined_vars = prod_vars - schema_vars
    for var in sorted(undefined_vars):
        errors.append(f"UNDEFINED: {var} is in prod.md but not defined in schema")

    # 2. Check for required variables missing from prod.md
    for var_name, var_schema in schema.items():
        # Skip null field definitions (malformed schema entries)
        if var_schema is None:
            warnings.append(f"MALFORMED_SCHEMA: {var_name} has null definition in schema")
            continue
        if var_schema.get("required", False) and var_name not in prod_vars:
            # Check if it's a secret (secrets might be intentionally omitted)
            if var_schema.get("type") == "secret":
                info.append(f"MISSING_SECRET: {var_name} (required secret, may be set via secure channel)")
            else:
                warnings.append(f"MISSING_REQUIRED: {var_name} is required but not in prod.md")

    # 3. Validate types and choices for variables in both
    for var_name in sorted(prod_vars & schema_vars):
        value = prod_config[var_name]
        var_schema = schema[var_name]

        # Skip null field definitions (malformed schema entries)
        if var_schema is None:
            continue

        # Type validation
        schema_type = var_schema.get("type", "string")
        is_valid, error_msg = validate_type(var_name, value, schema_type)
        if not is_valid:
            errors.append(error_msg)

        # Choices validation
        choices = var_schema.get("choices")
        if choices:
            is_valid, error_msg = validate_choices(var_name, value, choices)
            if not is_valid:
                errors.append(error_msg)

        # Default value comparison (informational)
        default = var_schema.get("default")
        if default is not None:
            default_str = str(default).lower()
            value_str = value.lower()
            if default_str != value_str:
                info.append(f"CUSTOM_VALUE: {var_name} = '{value}' (default: '{default}')")

    return errors, warnings, info


def print_report(
    errors: list[str],
    warnings: list[str],
    info: list[str],
    prod_count: int,
    schema_count: int,
) -> None:
    """Print a formatted validation report."""
    print("=" * 70)
    print("CONFIGURATION COVERAGE VALIDATION REPORT")
    print("=" * 70)
    print()

    print(f"Production config variables: {prod_count}")
    print(f"Schema defined variables: {schema_count}")
    print()

    if errors:
        print("ERRORS (must fix):", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        for error in errors:
            print(f"  [ERROR] {error}", file=sys.stderr)
        print(file=sys.stderr)

    if warnings:
        print("WARNINGS (should review):", file=sys.stderr)
        print("-" * 50, file=sys.stderr)
        for warning in warnings:
            print(f"  [WARN] {warning}", file=sys.stderr)
        print(file=sys.stderr)

    if info:
        print("INFO (for reference):")
        print("-" * 50)
        for item in info:
            print(f"  [INFO] {item}")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Info: {len(info)}")
    print()

    if errors:
        print("RESULT: FAIL - Configuration validation errors found")
    elif warnings:
        print("RESULT: PASS (with warnings)")
    else:
        print("RESULT: PASS")


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = validation errors, 2 = config errors)
    """
    parser = argparse.ArgumentParser(
        description="Validate production config against environment schema"
    )
    parser.add_argument(
        "--prod-file",
        type=Path,
        default=DEFAULT_PROD_FILE,
        help="Path to prod.md file",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to env.schema.yaml file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    try:
        # Parse files
        prod_config = parse_prod_md(args.prod_file)
        schema = parse_schema(args.schema_file)

        # Validate
        errors, warnings, info = validate_config(prod_config, schema)

        # Print report
        print_report(errors, warnings, info, len(prod_config), len(schema))

        # Determine exit code
        if errors:
            return 1
        if args.strict and warnings:
            return 1
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except (yaml.YAMLError, ValueError) as e:
        print(f"ERROR: Failed to parse configuration: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
