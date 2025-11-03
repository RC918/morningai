#!/usr/bin/env python3
"""
Check for drift between config/env.schema.yaml and .env.example files

This script ensures that all .env.example files are in sync with the
canonical environment schema. It should be run in CI to prevent drift.

Usage:
    python scripts/check-env-drift.py

Exit codes:
    0: No drift detected
    1: Drift detected or error occurred
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Set


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the environment schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def extract_vars_from_env_example(env_path: Path) -> Set[str]:
    """Extract variable names from .env.example file."""
    if not env_path.exists():
        return set()
    
    vars_found = set()
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                var_name = line.split('=')[0].strip()
                vars_found.add(var_name)
    
    return vars_found


def check_env_file(schema: Dict[str, Any], env_path: Path, expected_categories: Set[str]) -> bool:
    """Check if .env.example file matches schema for expected categories."""
    if not env_path.exists():
        print(f"❌ File not found: {env_path}")
        return False
    
    expected_vars = set()
    fields = schema.get('fields', {})
    for var_name, var_config in fields.items():
        category = var_config.get('category', 'Other')
        if category in expected_categories:
            expected_vars.add(var_name)
    
    actual_vars = extract_vars_from_env_example(env_path)
    
    missing_vars = expected_vars - actual_vars
    extra_vars = actual_vars - expected_vars
    
    has_drift = bool(missing_vars or extra_vars)
    
    if has_drift:
        print(f"❌ Drift detected in: {env_path}")
        if missing_vars:
            print(f"   Missing variables: {', '.join(sorted(missing_vars))}")
        if extra_vars:
            print(f"   Extra variables: {', '.join(sorted(extra_vars))}")
        print(f"   Run: python scripts/generate-env-examples.py")
        print("")
    else:
        print(f"✅ No drift: {env_path}")
    
    return not has_drift


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / 'config' / 'env.schema.yaml'
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    print("🔍 Checking for environment configuration drift...")
    print("")
    
    schema = load_schema(schema_path)
    
    backend_categories = {
        'Authentication', 'Security', 'Database', 'Cloud Services',
        'Infrastructure', 'Monitoring', 'Integration', 'Worker',
        'Application', 'Feature Flags', 'Testing'
    }
    
    frontend_categories = {'Frontend', 'Application', 'Feature Flags'}
    
    orchestrator_categories = {'Database', 'Application', 'Integration', 'Worker', 'Feature Flags'}
    
    all_ok = True
    
    all_ok &= check_env_file(
        schema,
        repo_root / '.env.example',
        backend_categories
    )
    
    all_ok &= check_env_file(
        schema,
        repo_root / 'handoff' / '20250928' / '40_App' / 'api-backend' / '.env.example',
        backend_categories
    )
    
    all_ok &= check_env_file(
        schema,
        repo_root / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / '.env.example',
        frontend_categories
    )
    
    all_ok &= check_env_file(
        schema,
        repo_root / 'handoff' / '20250928' / '40_App' / 'owner-console' / '.env.example',
        frontend_categories
    )
    
    all_ok &= check_env_file(
        schema,
        repo_root / 'orchestrator' / '.env.example',
        orchestrator_categories
    )
    
    print("")
    if all_ok:
        print("✅ All .env.example files are in sync with config/env.schema.yaml")
        sys.exit(0)
    else:
        print("❌ Drift detected! Run: python scripts/generate-env-examples.py")
        sys.exit(1)


if __name__ == '__main__':
    main()
