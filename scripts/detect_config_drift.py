#!/usr/bin/env python3
"""
Configuration Drift Detection Script

This script detects drift between IaC defaults (render.yaml) and schema definitions
(env.schema.yaml). It identifies discrepancies in default values, types, and
configuration coverage.

Issue #4186: Implement configuration drift detection
Blueprint Alignment: Section 4.3 Model Governance Framework v2 - Drift Monitoring

Usage:
    python scripts/detect_config_drift.py [--render-file PATH] [--schema-file PATH]
    python scripts/detect_config_drift.py --severity critical  # Only show critical drift

Exit codes:
    0: No drift detected (or only informational drift)
    1: Drift detected (warnings or errors)
    2: Configuration/file errors (missing files, parse errors)
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


# Default file paths
DEFAULT_RENDER_FILE = Path(__file__).parent.parent / "render.yaml"
DEFAULT_SCHEMA_FILE = Path(__file__).parent.parent / "config" / "env.schema.yaml"

# Severity levels for drift
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"

# Exit codes
EXIT_SUCCESS = 0
EXIT_DRIFT_DETECTED = 1
EXIT_CONFIG_ERROR = 2


def parse_render_yaml(file_path: Path) -> dict[str, dict[str, Any]]:
    """
    Parse render.yaml and extract all environment variable definitions.

    Args:
        file_path: Path to the render.yaml file

    Returns:
        Dictionary mapping variable names to their render.yaml definitions
        Each definition includes: value, sync, generateValue, service_name
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Render config file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        render_config = yaml.safe_load(f)

    if not render_config or "services" not in render_config:
        raise ValueError(f"Invalid render.yaml format: missing 'services' key in {file_path}")

    env_vars: dict[str, dict[str, Any]] = {}

    for service in render_config.get("services", []) or []:
        if service is None:
            continue
        service_name = service.get("name", "unknown")
        service_type = service.get("type", "unknown")

        for env_var in service.get("envVars", []) or []:
            if env_var is None:
                continue
            key = env_var.get("key")
            if not key:
                continue

            # Extract value, sync status, and generateValue
            var_info: dict[str, Any] = {
                "service_name": service_name,
                "service_type": service_type,
                "sync": env_var.get("sync", True),  # Default is sync=true
                "generateValue": env_var.get("generateValue", False),
            }

            if "value" in env_var:
                var_info["value"] = env_var["value"]
            elif env_var.get("generateValue"):
                var_info["value"] = "<generated>"
            elif env_var.get("sync") is False:
                var_info["value"] = "<manual>"

            # Track all services that define this variable
            if key in env_vars:
                # Variable defined in multiple services
                if "services" not in env_vars[key]:
                    env_vars[key]["services"] = [env_vars[key]["service_name"]]
                env_vars[key]["services"].append(service_name)
            else:
                env_vars[key] = var_info

    return env_vars


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


def normalize_value(value: Any) -> str:
    """Normalize a value for comparison."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).lower().strip()


def detect_value_drift(
    var_name: str,
    render_value: Any,
    schema_default: Any,
) -> tuple[bool, str, str]:
    """
    Detect if there's a drift between render.yaml value and schema default.

    Returns:
        Tuple of (has_drift, severity, message)
    """
    # Skip comparison for manual/generated values
    if render_value in ("<manual>", "<generated>"):
        return False, SEVERITY_INFO, ""

    # Normalize values for comparison
    render_normalized = normalize_value(render_value)
    schema_normalized = normalize_value(schema_default)

    if render_normalized != schema_normalized:
        # Determine severity based on the type of drift
        severity = SEVERITY_MEDIUM

        # Critical drift: security-related settings
        security_keywords = ["secret", "key", "password", "token", "auth"]
        if any(kw in var_name.lower() for kw in security_keywords):
            severity = SEVERITY_HIGH

        # High drift: feature flags that differ
        if var_name.startswith(("ENABLE_", "USE_", "FEATURE_")):
            severity = SEVERITY_HIGH

        message = f"Value drift: render.yaml='{render_value}' vs schema default='{schema_default}'"
        return True, severity, message

    return False, SEVERITY_INFO, ""


def detect_drift(
    render_vars: dict[str, dict[str, Any]],
    schema: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Detect all configuration drift between render.yaml and schema.

    Args:
        render_vars: Environment variables from render.yaml
        schema: Schema definitions from env.schema.yaml

    Returns:
        List of drift items with severity, variable name, and details
    """
    drift_items: list[dict[str, Any]] = []

    render_keys = set(render_vars.keys())
    schema_keys = set(schema.keys())

    # 1. Variables in render.yaml but not in schema (UNDEFINED)
    undefined_vars = render_keys - schema_keys
    for var in sorted(undefined_vars):
        drift_items.append({
            "severity": SEVERITY_MEDIUM,
            "variable": var,
            "type": "UNDEFINED_IN_SCHEMA",
            "message": "Defined in render.yaml but not in schema",
            "service": render_vars[var].get("service_name", "unknown"),
        })

    # 2. Required variables in schema but not in render.yaml
    for var_name, var_schema in schema.items():
        if var_schema is None:
            continue

        is_required = var_schema.get("required", False)
        is_secret = var_schema.get("type") == "secret"

        if var_name not in render_keys:
            if is_required and not is_secret:
                drift_items.append({
                    "severity": SEVERITY_HIGH,
                    "variable": var_name,
                    "type": "MISSING_IN_RENDER",
                    "message": "Required variable not defined in render.yaml",
                })
            elif is_required and is_secret:
                # Secrets might be configured manually in Dashboard
                drift_items.append({
                    "severity": SEVERITY_INFO,
                    "variable": var_name,
                    "type": "MISSING_SECRET",
                    "message": "Required secret not in render.yaml (may be in Dashboard)",
                })

    # 3. Value drift between render.yaml and schema defaults
    for var_name in sorted(render_keys & schema_keys):
        render_info = render_vars[var_name]
        var_schema = schema.get(var_name)

        if var_schema is None:
            continue

        render_value = render_info.get("value")
        schema_default = var_schema.get("default")

        # Skip if no default in schema or no value in render
        if schema_default is None or render_value is None:
            continue

        has_drift, severity, message = detect_value_drift(
            var_name, render_value, schema_default
        )

        if has_drift:
            drift_items.append({
                "severity": severity,
                "variable": var_name,
                "type": "VALUE_DRIFT",
                "message": message,
                "render_value": render_value,
                "schema_default": schema_default,
                "service": render_info.get("service_name", "unknown"),
            })

    # 4. Check for type mismatches
    for var_name in sorted(render_keys & schema_keys):
        render_info = render_vars[var_name]
        var_schema = schema.get(var_name)

        if var_schema is None:
            continue

        render_value = render_info.get("value")
        schema_type = var_schema.get("type", "string")

        # Skip manual/generated values
        if render_value in ("<manual>", "<generated>", None):
            continue

        # Check type consistency
        type_error = None
        if schema_type == "boolean":
            valid_bools = ("true", "false", "yes", "no", "1", "0")
            if str(render_value).lower() not in valid_bools:
                type_error = f"Expected boolean, got '{render_value}'"
        elif schema_type == "integer":
            try:
                int(render_value)
            except (ValueError, TypeError):
                type_error = f"Expected integer, got '{render_value}'"

        if type_error:
            drift_items.append({
                "severity": SEVERITY_HIGH,
                "variable": var_name,
                "type": "TYPE_MISMATCH",
                "message": type_error,
                "service": render_info.get("service_name", "unknown"),
            })

    # 5. Check for choices validation
    for var_name in sorted(render_keys & schema_keys):
        render_info = render_vars[var_name]
        var_schema = schema.get(var_name)

        if var_schema is None:
            continue

        render_value = render_info.get("value")
        choices = var_schema.get("choices")

        if choices and render_value not in ("<manual>", "<generated>", None):
            normalized_value = str(render_value).lower()
            normalized_choices = [str(c).lower() for c in choices]

            if normalized_value not in normalized_choices:
                drift_items.append({
                    "severity": SEVERITY_HIGH,
                    "variable": var_name,
                    "type": "INVALID_CHOICE",
                    "message": f"Value '{render_value}' not in allowed choices: {choices}",
                    "service": render_info.get("service_name", "unknown"),
                })

    return drift_items


def print_report(
    drift_items: list[dict[str, Any]],
    render_count: int,
    schema_count: int,
    min_severity: str = SEVERITY_INFO,
) -> None:
    """Print a formatted drift detection report."""
    severity_order = [SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO]
    min_severity_idx = severity_order.index(min_severity) if min_severity in severity_order else 4

    # Filter by minimum severity
    filtered_items = [
        item for item in drift_items
        if severity_order.index(item["severity"]) <= min_severity_idx
    ]

    print("=" * 70)
    print("CONFIGURATION DRIFT DETECTION REPORT")
    print("=" * 70)
    print()

    print(f"Render.yaml variables: {render_count}")
    print(f"Schema defined variables: {schema_count}")
    print()

    if not filtered_items:
        print("No drift detected!")
        print()
        return

    # Group by severity
    for severity in severity_order:
        severity_items = [item for item in filtered_items if item["severity"] == severity]
        if not severity_items:
            continue

        severity_label = severity.upper()
        print(f"{severity_label} ({len(severity_items)} items):", file=sys.stderr if severity in [SEVERITY_CRITICAL, SEVERITY_HIGH] else sys.stdout)
        print("-" * 50, file=sys.stderr if severity in [SEVERITY_CRITICAL, SEVERITY_HIGH] else sys.stdout)

        for item in severity_items:
            var = item["variable"]
            msg = item["message"]
            drift_type = item["type"]
            service = item.get("service", "")

            output = sys.stderr if severity in [SEVERITY_CRITICAL, SEVERITY_HIGH] else sys.stdout
            if service:
                print(f"  [{drift_type}] {var} ({service}): {msg}", file=output)
            else:
                print(f"  [{drift_type}] {var}: {msg}", file=output)

        print(file=sys.stderr if severity in [SEVERITY_CRITICAL, SEVERITY_HIGH] else sys.stdout)

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for severity in severity_order:
        count = len([item for item in filtered_items if item["severity"] == severity])
        if count > 0:
            print(f"  {severity.upper()}: {count}")

    print()

    # Determine result
    critical_count = len([item for item in filtered_items if item["severity"] == SEVERITY_CRITICAL])
    high_count = len([item for item in filtered_items if item["severity"] == SEVERITY_HIGH])

    if critical_count > 0:
        print("RESULT: FAIL - Critical drift detected (merge blocked)", file=sys.stderr)
    elif high_count > 0:
        print("RESULT: WARNING - High severity drift detected", file=sys.stderr)
    else:
        print("RESULT: PASS (with informational drift)")


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = drift detected, 2 = config errors)
    """
    parser = argparse.ArgumentParser(
        description="Detect configuration drift between render.yaml and env.schema.yaml"
    )
    parser.add_argument(
        "--render-file",
        type=Path,
        default=DEFAULT_RENDER_FILE,
        help="Path to render.yaml file",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Path to env.schema.yaml file",
    )
    parser.add_argument(
        "--severity",
        choices=[SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO],
        default=SEVERITY_INFO,
        help="Minimum severity level to report (default: info)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat high severity drift as errors (exit code 1)",
    )
    parser.add_argument(
        "--block-on-critical",
        action="store_true",
        help="Only block merge on critical drift (exit code 1)",
    )

    args = parser.parse_args()

    try:
        # Parse files
        render_vars = parse_render_yaml(args.render_file)
        schema = parse_schema(args.schema_file)

        # Detect drift
        drift_items = detect_drift(render_vars, schema)

        # Print report
        print_report(
            drift_items,
            len(render_vars),
            len(schema),
            min_severity=args.severity,
        )

        # Determine exit code based on severity counts
        critical_count = len([item for item in drift_items if item["severity"] == SEVERITY_CRITICAL])
        high_count = len([item for item in drift_items if item["severity"] == SEVERITY_HIGH])

        # Always block on critical drift
        if critical_count > 0:
            return EXIT_DRIFT_DETECTED

        # --strict blocks on HIGH severity (unless --block-on-critical overrides)
        if args.strict and high_count > 0 and not args.block_on_critical:
            return EXIT_DRIFT_DETECTED

        return EXIT_SUCCESS

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    except (yaml.YAMLError, ValueError) as e:
        print(f"ERROR: Failed to parse configuration: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR


if __name__ == "__main__":
    sys.exit(main())
