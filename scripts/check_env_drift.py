#!/usr/bin/env python3
"""
Check for drift between config/env.schema.yaml and .env.example files
Ensures .env.example files stay in sync with the schema
"""

import yaml
import sys
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple

def parse_env_example(file_path: Path) -> Set[str]:
    """Parse .env.example file and extract variable names"""
    if not file_path.exists():
        return set()
    
    variables = set()
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(r'^#?\s*([A-Z_][A-Z0-9_]*)=', line)
            if match:
                variables.add(match.group(1))
    
    return variables

def load_schema_variables(schema_path: Path) -> Set[str]:
    """Load variable names from env.schema.yaml"""
    if not schema_path.exists():
        print(f"❌ Schema not found at {schema_path}")
        sys.exit(1)
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return set(schema['fields'].keys())

def check_drift() -> int:
    """Check for drift between schema and .env.example files"""
    
    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / 'config' / 'env.schema.yaml'
    
    schema_vars = load_schema_variables(schema_path)
    
    env_files = [
        repo_root / '.env.example',
        repo_root / 'handoff' / '20250928' / '40_App' / 'frontend-dashboard' / '.env.example',
        repo_root / 'handoff' / '20250928' / '40_App' / 'owner-console' / '.env.example',
        repo_root / 'orchestrator' / '.env.example',
    ]
    
    has_drift = False
    results: List[Tuple[Path, Set[str], Set[str]]] = []
    
    print("🔍 Checking for drift between env.schema.yaml and .env.example files...")
    print(f"   Schema defines {len(schema_vars)} variables\n")
    
    for env_file in env_files:
        if not env_file.exists():
            print(f"⚠️  {env_file.relative_to(repo_root)}: File not found (skipping)")
            continue
        
        env_vars = parse_env_example(env_file)
        
        missing_in_env = schema_vars - env_vars
        extra_in_env = env_vars - schema_vars
        
        if missing_in_env or extra_in_env:
            has_drift = True
            results.append((env_file, missing_in_env, extra_in_env))
        else:
            print(f"✅ {env_file.relative_to(repo_root)}: No drift ({len(env_vars)} variables)")
    
    if has_drift:
        print("\n" + "=" * 80)
        print("❌ DRIFT DETECTED")
        print("=" * 80)
        
        for env_file, missing, extra in results:
            rel_path = env_file.relative_to(repo_root)
            print(f"\n📄 {rel_path}:")
            
            if missing:
                print(f"   ⚠️  Missing {len(missing)} variables from schema:")
                for var in sorted(missing)[:10]:  # Show first 10
                    print(f"      - {var}")
                if len(missing) > 10:
                    print(f"      ... and {len(missing) - 10} more")
            
            if extra:
                print(f"   ⚠️  Extra {len(extra)} variables not in schema:")
                for var in sorted(extra)[:10]:  # Show first 10
                    print(f"      - {var}")
                if len(extra) > 10:
                    print(f"      ... and {len(extra) - 10} more")
        
        print("\n" + "=" * 80)
        print("🔧 To fix drift:")
        print(f"   1. Update config/env.schema.yaml with any missing variables")
        print(f"   2. Run: python scripts/generate_env_example.py")
        print(f"   3. Commit both schema and .env.example changes together")
        print("=" * 80)
        
        return 1
    
    print("\n✅ No drift detected - all .env.example files match schema")
    return 0

if __name__ == '__main__':
    sys.exit(check_drift())
