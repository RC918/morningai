#!/usr/bin/env python3
"""
Check for unused environment variables in the schema.

This script identifies variables defined in config/env.schema.yaml that are
not referenced in the codebase (common/config/settings.py). This helps
identify dead configuration that can be cleaned up.

Usage:
    python scripts/check-unused-env-vars.py

Exit codes:
    0: No issues found (or only warnings)
    1: Error occurred
"""

import yaml
import sys
import re
from pathlib import Path
from typing import Dict, Any, Set, List, Tuple

from repo_root_utils import get_repo_root


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the environment schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def extract_settings_fields(settings_path: Path) -> Set[str]:
    """Extract environment variable names referenced in Settings class.

    Looks for Field(..., alias="VAR_NAME", ...) patterns.
    """
    if not settings_path.exists():
        return set()

    content = settings_path.read_text()

    alias_pattern = re.compile(r'alias\s*=\s*["\']([A-Z_][A-Z0-9_]*)["\']')

    return set(alias_pattern.findall(content))


def categorize_unused_vars(
    schema: Dict[str, Any],
    used_vars: Set[str]
) -> Tuple[List[str], List[str], List[str]]:
    """Categorize unused variables by their status.

    Returns:
        Tuple of (deprecated_unused, optional_unused, required_unused)
    """
    fields = schema.get('fields', {})

    deprecated_unused = []
    optional_unused = []
    required_unused = []

    for var_name, var_config in fields.items():
        if var_name in used_vars:
            continue

        notes = var_config.get('notes', '')
        is_deprecated = 'DEPRECATED' in notes.upper() or 'deprecated' in notes.lower()
        is_required = var_config.get('required', False)

        if is_deprecated:
            deprecated_unused.append(var_name)
        elif is_required:
            required_unused.append(var_name)
        else:
            optional_unused.append(var_name)

    return deprecated_unused, optional_unused, required_unused


def main():
    """Main entry point."""
    repo_root = get_repo_root()
    schema_path = repo_root / 'config' / 'env.schema.yaml'
    settings_path = repo_root / 'common' / 'config' / 'settings.py'

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)

    if not settings_path.exists():
        print(f"Error: Settings file not found: {settings_path}")
        sys.exit(1)

    print("Checking for unused environment variables...")
    print("")

    schema = load_schema(schema_path)
    used_vars = extract_settings_fields(settings_path)

    schema_vars = set(schema.get('fields', {}).keys())

    print(f"Schema defines {len(schema_vars)} variables")
    print(f"Settings references {len(used_vars)} variables")
    print("")

    deprecated_unused, optional_unused, required_unused = categorize_unused_vars(
        schema, used_vars
    )

    if deprecated_unused:
        print(f"Deprecated variables not in Settings ({len(deprecated_unused)}):")
        print("  (These are expected - deprecated vars may be removed from code)")
        for var in sorted(deprecated_unused):
            print(f"    - {var}")
        print("")

    if optional_unused:
        print(f"Optional variables not in Settings ({len(optional_unused)}):")
        print("  (Consider adding to Settings or removing from schema)")
        for var in sorted(optional_unused):
            print(f"    - {var}")
        print("")

    if required_unused:
        print(f"WARNING: Required variables not in Settings ({len(required_unused)}):")
        print("  (These should be added to Settings or marked as optional)")
        for var in sorted(required_unused):
            print(f"    - {var}")
        print("")

    total_unused = len(deprecated_unused) + len(optional_unused) + len(required_unused)

    if total_unused == 0:
        print("All schema variables are referenced in Settings.")
    else:
        print(f"Summary: {total_unused} variables in schema not referenced in Settings")
        print(f"  - {len(deprecated_unused)} deprecated (expected)")
        print(f"  - {len(optional_unused)} optional (review needed)")
        print(f"  - {len(required_unused)} required (action needed)")

    sys.exit(0)


if __name__ == '__main__':
    main()
