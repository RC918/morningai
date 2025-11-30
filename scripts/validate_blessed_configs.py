#!/usr/bin/env python3
"""
Validate render.yaml against blessed_configs.yaml

This script ensures that render.yaml service configurations match the
approved configurations defined in config/blessed_configs.yaml.

Usage:
    python scripts/validate_blessed_configs.py [--env production|staging]

Exit codes:
    0 - All validations passed
    1 - Validation errors found
    2 - File not found or parse error
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(2)

    with open(path, "r") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse {path}: {e}")
            sys.exit(2)


def get_service_env_vars(service: dict[str, Any]) -> dict[str, str]:
    """Extract environment variables from a render.yaml service definition."""
    env_vars = {}
    for env_var in service.get("envVars", []):
        key = env_var.get("key")
        value = env_var.get("value")
        if key and value is not None:
            env_vars[key] = str(value)
    return env_vars


def parse_config_string(config: str) -> tuple[str, str]:
    """Parse a config string like 'KEY=value' into (key, value)."""
    if "=" not in config:
        return config, ""
    key, value = config.split("=", 1)
    return key, value


def normalize_value(value: str) -> str:
    """Normalize a value for comparison (handle booleans, etc.)."""
    lower = value.lower()
    if lower in ("true", "false"):
        return lower
    return value


def validate_service_configs(
    service_name: str,
    render_env_vars: dict[str, str],
    blessed_configs: list[str],
) -> list[str]:
    """Validate a service's env vars against blessed configs."""
    errors = []

    for config in blessed_configs:
        key, expected_value = parse_config_string(config)
        actual_value = render_env_vars.get(key)

        if actual_value is None:
            errors.append(
                f"  - {key}: MISSING (expected '{expected_value}')"
            )
        elif normalize_value(actual_value) != normalize_value(expected_value):
            errors.append(
                f"  - {key}: MISMATCH (expected '{expected_value}', got '{actual_value}')"
            )

    return errors


def validate_critical_rules(
    render_services: list[dict[str, Any]],
    blessed_config: dict[str, Any],
) -> list[str]:
    """Validate critical cross-service rules."""
    errors = []
    validation_rules = blessed_config.get("validation_rules", [])

    for rule in validation_rules:
        severity = rule.get("severity", "")
        if severity != "critical":
            continue

        rule_name = rule.get("name", "unknown")
        rule_desc = rule.get("description", "")

        if rule_name == "mock_users_production_disabled":
            for service in render_services:
                env_vars = get_service_env_vars(service)
                if env_vars.get("ENABLE_MOCK_USERS", "").lower() == "true":
                    errors.append(
                        f"CRITICAL: {rule_desc} - "
                        f"Service '{service.get('name')}' has ENABLE_MOCK_USERS=true"
                    )

        elif rule_name == "demo_mode_production_disabled":
            for service in render_services:
                env_vars = get_service_env_vars(service)
                if env_vars.get("DEMO_MODE", "").lower() == "true":
                    errors.append(
                        f"CRITICAL: {rule_desc} - "
                        f"Service '{service.get('name')}' has DEMO_MODE=true"
                    )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate render.yaml against blessed_configs.yaml"
    )
    parser.add_argument(
        "--env",
        choices=["production", "staging"],
        default="production",
        help="Environment to validate against (default: production)",
    )
    parser.add_argument(
        "--render-yaml",
        type=Path,
        default=Path("render.yaml"),
        help="Path to render.yaml (default: render.yaml)",
    )
    parser.add_argument(
        "--blessed-configs",
        type=Path,
        default=Path("config/blessed_configs.yaml"),
        help="Path to blessed_configs.yaml (default: config/blessed_configs.yaml)",
    )
    args = parser.parse_args()

    print(f"Validating render.yaml against blessed configs for '{args.env}' environment...")
    print()

    render_config = load_yaml_file(args.render_yaml)
    blessed_config = load_yaml_file(args.blessed_configs)

    render_services = render_config.get("services", [])
    blessed_services = blessed_config.get("services", {}).get(args.env, [])

    all_errors: list[str] = []
    services_checked = 0
    configs_checked = 0

    render_services_by_name = {s.get("name"): s for s in render_services}

    for blessed_service in blessed_services:
        service_name = blessed_service.get("name")
        blessed_configs_list = blessed_service.get("configs", [])

        if not blessed_configs_list:
            print(f"[SKIP] {service_name}: No configs to validate")
            continue

        render_service = render_services_by_name.get(service_name)

        if render_service is None:
            all_errors.append(f"Service '{service_name}': NOT FOUND in render.yaml")
            continue

        render_env_vars = get_service_env_vars(render_service)
        service_errors = validate_service_configs(
            service_name, render_env_vars, blessed_configs_list
        )

        services_checked += 1
        configs_checked += len(blessed_configs_list)

        if service_errors:
            all_errors.append(f"Service '{service_name}':")
            all_errors.extend(service_errors)
            print(f"[FAIL] {service_name}: {len(service_errors)} error(s)")
        else:
            print(f"[PASS] {service_name}: {len(blessed_configs_list)} config(s) validated")

    critical_errors = validate_critical_rules(render_services, blessed_config)
    all_errors.extend(critical_errors)

    print()
    print(f"Summary: {services_checked} services, {configs_checked} configs checked")

    if all_errors:
        print()
        print("=" * 60)
        print("VALIDATION ERRORS:")
        print("=" * 60)
        for error in all_errors:
            print(error)
        print()
        print(f"Total errors: {len(all_errors)}")
        return 1
    else:
        print()
        print("All validations passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
