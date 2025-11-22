#!/usr/bin/env python3
"""
CI script to audit Pydantic aliases in settings.py against env.schema.yaml.

This script ensures that all environment variables defined in config/env.schema.yaml
have corresponding Pydantic aliases in common/config/settings.py.

Exit codes:
  0: All required aliases are present
  1: Missing aliases detected or script error
"""
import ast
import sys
from pathlib import Path
from typing import Set, Dict, List

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_env_schema(schema_path: Path) -> Set[str]:
    """Load environment variable names from env.schema.yaml."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        env_vars = set(schema.get('fields', {}).keys())
        print(f"✓ Loaded {len(env_vars)} environment variables from schema")
        return env_vars
    except Exception as e:
        print(f"ERROR: Failed to load env.schema.yaml: {e}")
        sys.exit(1)


def extract_aliases_from_settings(settings_path: Path) -> Dict[str, List[str]]:
    """
    Extract Pydantic field aliases from settings.py using AST parsing.
    
    Returns:
        Dict with 'aliases' (set of alias strings) and 'fields_without_alias' (list of field names)
    """
    try:
        with open(settings_path, 'r') as f:
            tree = ast.parse(f.read(), filename=str(settings_path))
    except Exception as e:
        print(f"ERROR: Failed to parse settings.py: {e}")
        sys.exit(1)
    
    aliases = set()
    fields_without_alias = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Settings':
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    
                    if isinstance(item.value, ast.Call):
                        func = item.value.func
                        if isinstance(func, ast.Name) and func.id == 'Field':
                            alias_found = False
                            for keyword in item.value.keywords:
                                if keyword.arg == 'alias':
                                    if isinstance(keyword.value, ast.Constant):
                                        alias_value = keyword.value.value
                                        aliases.add(alias_value)
                                        alias_found = True
                            
                            if not alias_found:
                                fields_without_alias.append(field_name)
    
    print(f"✓ Found {len(aliases)} fields with aliases in settings.py")
    print(f"✓ Found {len(fields_without_alias)} fields without aliases")
    
    return {
        'aliases': aliases,
        'fields_without_alias': fields_without_alias
    }


def get_exclusions() -> Set[str]:
    """
    Get environment variables that are allowed to not have aliases.
    
    These are typically:
    - Variables not consumed by Settings class
    - Frontend-only variables (VITE_*)
    - CI/build-time variables
    """
    return {
        'VITE_API_BASE_URL',
        'VITE_FEATURES',
        'VITE_SENTRY_DSN',
        'VITE_USE_MOCK',
        'VITE_TRACE_VIEWER_URL',
        'VITE_FEATURE_OWNER_CONSOLE_API',
        'VITE_E2E',
        
        'SECRET_KEY',  # Use FLASK_SECRET_KEY
        'MASTER_KEY',  # Use ENCRYPTION_MASTER_KEY
        'STRIPE_WEBHOOK_SECRET',  # Use STRIPE_WEBHOOK_SECRET_KEY
        'Mailtrap_API_TOKEN',  # Use MAILTRAP_API_TOKEN
    }


def main():
    """Main audit function."""
    print("=" * 80)
    print("🔍 Auditing Pydantic Aliases in settings.py")
    print("=" * 80)
    print()
    
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    
    schema_path = repo_root / 'config' / 'env.schema.yaml'
    settings_path = repo_root / 'common' / 'config' / 'settings.py'
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)
    
    if not settings_path.exists():
        print(f"ERROR: Settings file not found: {settings_path}")
        sys.exit(1)
    
    print(f"📄 Schema: {schema_path.relative_to(repo_root)}")
    print(f"📄 Settings: {settings_path.relative_to(repo_root)}")
    print()
    
    env_vars = load_env_schema(schema_path)
    result = extract_aliases_from_settings(settings_path)
    aliases = result['aliases']
    fields_without_alias = result['fields_without_alias']
    
    exclusions = get_exclusions()
    print(f"✓ Excluding {len(exclusions)} variables (frontend-only, deprecated, etc.)")
    print()
    
    required_vars = env_vars - exclusions
    missing = sorted(required_vars - aliases)
    
    if not missing:
        print("=" * 80)
        print("✅ SUCCESS: All required environment variables have Pydantic aliases!")
        print("=" * 80)
        print()
        print(f"  Total env vars in schema: {len(env_vars)}")
        print(f"  Excluded vars: {len(exclusions)}")
        print(f"  Required vars: {len(required_vars)}")
        print(f"  Aliases found: {len(aliases)}")
        print()
        return 0
    
    print("=" * 80)
    print(f"❌ FAILURE: {len(missing)} environment variables missing Pydantic aliases")
    print("=" * 80)
    print()
    print("Missing aliases for the following environment variables:")
    print()
    
    for var in missing:
        field_name = var.lower()
        print(f"  • {var}")
        print(f"    Suggested fix in settings.py:")
        print(f"    {field_name}: ... = Field(..., alias=\"{var}\", ...)")
        print()
    
    print("=" * 80)
    print("📝 How to fix:")
    print("=" * 80)
    print()
    print("1. Open common/config/settings.py")
    print("2. Find each field listed above")
    print("3. Add alias=\"UPPERCASE_NAME\" to the Field() definition")
    print()
    print("Example:")
    print("  # Before:")
    print("  rq_queue_name: str = Field(default=\"orchestrator\", description=\"...\")")
    print()
    print("  # After:")
    print("  rq_queue_name: str = Field(")
    print("      default=\"orchestrator\",")
    print("      alias=\"RQ_QUEUE_NAME\",  # ← Add this line")
    print("      description=\"...\"")
    print("  )")
    print()
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
