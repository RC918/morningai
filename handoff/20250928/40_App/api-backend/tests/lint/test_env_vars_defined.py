"""
Lint check: Ensure all environment variables used in src/** are defined in config/env.schema.yaml

This test scans all Python files in src/** for os.getenv() and os.environ[] calls,
and validates that the variable names are defined in config/env.schema.yaml.

Usage:
    pytest tests/lint/test_env_vars_defined.py -v
"""

import ast
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple
import difflib

import yaml


def load_schema_vars() -> Set[str]:
    """Load environment variable names from config/env.schema.yaml."""
    repo_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    schema_path = repo_root / 'config' / 'env.schema.yaml'
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return set(schema.get('fields', {}).keys())


class EnvVarVisitor(ast.NodeVisitor):
    """AST visitor to find all environment variable accesses."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []  # (line_number, var_name)
        self.dynamic_usages: List[int] = []  # line numbers with dynamic keys
        
        self.os_names: Set[str] = set()  # Names bound to 'os' module
        self.getenv_names: Set[str] = set()  # Names bound to 'os.getenv'
        self.environ_names: Set[str] = set()  # Names bound to 'os.environ'
    
    def visit_Import(self, node: ast.Import):
        """Track 'import os' and 'import os as alias'."""
        for alias in node.names:
            if alias.name == 'os':
                self.os_names.add(alias.asname if alias.asname else 'os')
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track 'from os import getenv/environ' with optional aliases."""
        if node.module == 'os':
            for alias in node.names:
                if alias.name == 'getenv':
                    self.getenv_names.add(alias.asname if alias.asname else 'getenv')
                elif alias.name == 'environ':
                    self.environ_names.add(alias.asname if alias.asname else 'environ')
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Find os.getenv() and os.environ.get() calls."""
        var_name = None
        
        if isinstance(node.func, ast.Name) and node.func.id in self.getenv_names:
            var_name = self._extract_string_arg(node, 0)
        
        elif isinstance(node.func, ast.Attribute):
            if (node.func.attr == 'getenv' and 
                isinstance(node.func.value, ast.Name) and 
                node.func.value.id in self.os_names):
                var_name = self._extract_string_arg(node, 0)
            
            elif node.func.attr == 'get':
                if self._is_environ_access(node.func.value):
                    var_name = self._extract_string_arg(node, 0)
        
        if var_name is not None:
            if var_name:  # Non-empty string
                self.violations.append((node.lineno, var_name))
            else:  # Dynamic key (not a string literal)
                self.dynamic_usages.append(node.lineno)
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript):
        """Find os.environ["VAR"] accesses."""
        if self._is_environ_access(node.value):
            var_name = self._extract_subscript_key(node)
            if var_name is not None:
                if var_name:  # Non-empty string
                    self.violations.append((node.lineno, var_name))
                else:  # Dynamic key
                    self.dynamic_usages.append(node.lineno)
        
        self.generic_visit(node)
    
    def _is_environ_access(self, node: ast.AST) -> bool:
        """Check if node represents os.environ or environ alias."""
        if isinstance(node, ast.Name) and node.id in self.environ_names:
            return True
        
        if isinstance(node, ast.Attribute):
            if (node.attr == 'environ' and 
                isinstance(node.value, ast.Name) and 
                node.value.id in self.os_names):
                return True
        
        return False
    
    def _extract_string_arg(self, call_node: ast.Call, arg_index: int) -> str | None:
        """Extract string literal from call argument. Returns None if not found, empty string if dynamic."""
        if len(call_node.args) > arg_index:
            arg = call_node.args[arg_index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            else:
                return ""  # Dynamic key
        return None
    
    def _extract_subscript_key(self, subscript_node: ast.Subscript) -> str | None:
        """Extract string literal from subscript. Returns None if not found, empty string if dynamic."""
        if isinstance(subscript_node.slice, ast.Constant) and isinstance(subscript_node.slice.value, str):
            return subscript_node.slice.value
        else:
            return ""  # Dynamic key


def scan_file(filepath: Path, schema_vars: Set[str]) -> Tuple[List[Tuple[int, str]], List[int]]:
    """
    Scan a Python file for undefined environment variable accesses.
    
    Returns:
        (violations, dynamic_usages) where violations is [(line, var_name), ...]
        and dynamic_usages is [line, ...] for dynamic keys
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(filepath))
        visitor = EnvVarVisitor(str(filepath))
        visitor.visit(tree)
        
        undefined = [(line, var) for line, var in visitor.violations if var not in schema_vars]
        
        return undefined, visitor.dynamic_usages
    
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}:{e.lineno}: {e.msg}", file=sys.stderr)
        return [], []
    except Exception as e:
        print(f"⚠️  Error parsing {filepath}: {e}", file=sys.stderr)
        return [], []


def get_suggestions(var_name: str, schema_vars: Set[str], n: int = 3) -> List[str]:
    """Get close matches for a variable name from schema."""
    return difflib.get_close_matches(var_name, schema_vars, n=n, cutoff=0.6)


def test_env_vars_defined():
    """Test that all environment variables used in src/** are defined in config/env.schema.yaml."""
    
    schema_vars = load_schema_vars()
    print(f"\n✓ Loaded {len(schema_vars)} variables from config/env.schema.yaml")
    
    api_backend_dir = Path(__file__).parent.parent.parent
    src_dir = api_backend_dir / 'src'
    repo_root = api_backend_dir.parent.parent.parent.parent
    
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")
    
    python_files = list(src_dir.rglob('*.py'))
    print(f"✓ Scanning {len(python_files)} Python files in {src_dir.relative_to(repo_root)}")
    
    all_violations: Dict[str, List[Tuple[int, str]]] = {}
    total_dynamic = 0
    
    for filepath in python_files:
        violations, dynamic_usages = scan_file(filepath, schema_vars)
        if violations:
            rel_path = filepath.relative_to(repo_root)
            all_violations[str(rel_path)] = violations
        total_dynamic += len(dynamic_usages)
    
    if total_dynamic > 0:
        print(f"\nℹ️  Skipped {total_dynamic} dynamic environment variable accesses (non-literal keys)")
    
    if all_violations:
        print("\n" + "=" * 80)
        print("❌ UNDEFINED ENVIRONMENT VARIABLES DETECTED")
        print("=" * 80)
        
        var_locations: Dict[str, List[str]] = {}
        for filepath, violations in all_violations.items():
            for line, var_name in violations:
                location = f"{filepath}:{line}"
                if var_name not in var_locations:
                    var_locations[var_name] = []
                var_locations[var_name].append(location)
        
        for var_name in sorted(var_locations.keys()):
            locations = var_locations[var_name]
            print(f"\n📍 Variable: {var_name}")
            print(f"   Used in {len(locations)} location(s):")
            for loc in locations[:5]:  # Show first 5 locations
                print(f"     - {loc}")
            if len(locations) > 5:
                print(f"     ... and {len(locations) - 5} more")
            
            suggestions = get_suggestions(var_name, schema_vars)
            if suggestions:
                print(f"   💡 Did you mean: {', '.join(suggestions)}?")
        
        print("\n" + "=" * 80)
        print("🔧 HOW TO FIX:")
        print("=" * 80)
        print("1. Add missing variables to config/env.schema.yaml with:")
        print("   - type: (string|integer|boolean|url|secret)")
        print("   - description: Clear description of the variable")
        print("   - category: (Authentication|Security|Database|etc.)")
        print("   - required: (true|false)")
        print("   - default: Default value (if optional)")
        print("")
        print("2. Or rename the variable to match an existing schema entry")
        print("")
        print("3. Run: python scripts/generate-env-examples.py")
        print("   to update .env.example files after schema changes")
        print("=" * 80)
        
        assert False, f"Found {len(var_locations)} undefined environment variables. See output above for details."
    
    print(f"\n✅ All environment variables are defined in config/env.schema.yaml")
