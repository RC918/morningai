#!/usr/bin/env python3
"""
AST-based checker for os.getenv() and os.environ.get() calls.

This script uses Python's AST (Abstract Syntax Tree) to accurately detect
direct environment variable access, avoiding false positives from comments
or string literals that grep-based approaches would catch.

Usage:
    python check_os_getenv.py [--strict]

Exit codes:
    0: No violations found (or warning mode)
    1: Violations found (in strict mode)
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set


class EnvGetenvVisitor(ast.NodeVisitor):
    """AST visitor that detects os.getenv() and os.environ.get() calls"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[Tuple[int, str]] = []
    
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes"""
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and 
                node.func.value.id == 'os' and 
                node.func.attr == 'getenv'):
                self.violations.append((
                    node.lineno,
                    f"os.getenv() call"
                ))
        
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Attribute) and
                isinstance(node.func.value.value, ast.Name) and
                node.func.value.value.id == 'os' and
                node.func.value.attr == 'environ' and
                node.func.attr == 'get'):
                self.violations.append((
                    node.lineno,
                    f"os.environ.get() call"
                ))
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Visit subscript nodes (e.g., os.environ['KEY'])"""
        if isinstance(node.value, ast.Attribute):
            if (isinstance(node.value.value, ast.Name) and
                node.value.value.id == 'os' and
                node.value.attr == 'environ'):
                self.violations.append((
                    node.lineno,
                    f"os.environ[...] subscript access"
                ))
        
        self.generic_visit(node)


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped"""
    skip_patterns = {
        'common/config/settings.py',
        'common/config/test_settings.py',
        '.github/scripts/check_os_getenv.py',
        'handoff/20250928/40_App/api-backend/conftest.py',
        'handoff/20250928/40_App/api-backend/sitecustomize.py',
        'env_schema_validator.py',
        'common/utils/repo_root.py',
    }
    
    skip_dirs = {
        '.venv', '.git', 'node_modules', '__pycache__', '.pytest_cache',
        '_vendor', 'site-packages', 'pip'
    }
    
    skip_path_patterns = {
        'tests/',
        'migrations/',
        'examples/',
        '/60_Design/',
        'scripts/test_',
        'sandbox/',
        '.github/scripts/',
        'docs/',
        'phase6_startup.py',
        'phase7_startup.py',
    }
    
    parts = filepath.parts
    if any(skip_dir in parts for skip_dir in skip_dirs):
        return True
    
    filepath_str = str(filepath)
    
    for pattern in skip_patterns:
        if filepath_str.endswith(pattern):
            return True
    
    for pattern in skip_path_patterns:
        if pattern in filepath_str:
            return True
    
    if filepath.name.startswith('test_') and filepath.parent.name != 'tests':
        return True
    
    return False


def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """Check a single Python file for os.getenv() calls"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        visitor = EnvGetenvVisitor(str(filepath))
        visitor.visit(tree)
        
        return visitor.violations
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"⚠️  Error processing {filepath}: {e}", file=sys.stderr)
        return []


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the repository"""
    python_files = []
    
    for filepath in root_dir.rglob('*.py'):
        if not should_skip_file(filepath):
            python_files.append(filepath)
    
    return python_files


def main():
    """Main entry point"""
    strict_mode = '--strict' in sys.argv
    
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    
    print("🔍 Checking for direct os.getenv() and os.environ.get() calls...")
    print(f"   Repository: {repo_root}")
    print(f"   Mode: {'STRICT (blocking)' if strict_mode else 'WARNING (non-blocking)'}")
    print()
    
    python_files = find_python_files(repo_root)
    print(f"   Found {len(python_files)} Python files to check")
    print()
    
    all_violations = {}
    for filepath in python_files:
        violations = check_file(filepath)
        if violations:
            rel_path = filepath.relative_to(repo_root)
            all_violations[str(rel_path)] = violations
    
    if not all_violations:
        print("✅ No direct os.getenv() or os.environ.get() calls found!")
        print()
        print("All environment variable access is properly centralized in common/config/settings.py")
        return 0
    
    print(f"{'❌ ERROR' if strict_mode else '⚠️  WARNING'}: Found {len(all_violations)} files with direct environment variable access:")
    print()
    
    total_violations = 0
    for filepath, violations in sorted(all_violations.items()):
        print(f"  {filepath}:")
        for lineno, description in violations:
            print(f"    Line {lineno}: {description}")
            total_violations += 1
        print()
    
    print(f"Total: {total_violations} violations in {len(all_violations)} files")
    print()
    
    print("📚 Migration Guide:")
    print()
    print("  Instead of:")
    print("    import os")
    print("    db_url = os.getenv('DATABASE_URL')")
    print()
    print("  Use:")
    print("    from common.config.settings import get_settings")
    print("    db_url = get_settings().database_url")
    print()
    print("  See docs/config/settings.md for complete migration guide")
    print()
    
    if strict_mode:
        print("❌ BLOCKING: This PR cannot be merged until all violations are fixed.")
        print()
        print("To add a new environment variable:")
        print("  1. Add it to config/env.schema.yaml")
        print("  2. Add it to common/config/settings.py with proper type and alias")
        print("  3. Use get_settings().variable_name in your code")
        return 1
    else:
        print("⚠️  WARNING MODE: This check is currently non-blocking.")
        print("   After PR 1c is merged, this will become a blocking check.")
        print()
        print("   Please migrate these calls to use common/config/settings.py")
        return 0


if __name__ == '__main__':
    sys.exit(main())
