"""
Test to ensure deprecated modules are not imported in production code.

This test scans src/** for imports of deprecated modules and fails CI if found.
Tests are excluded to allow backward compatibility testing.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple

from src.utils.repo_root import get_api_backend_root as _get_api_backend_root


DEPRECATED_MODULES = [
    "utils.preauth_token",
    "src.utils.preauth_token",
]

ALLOWLIST = [
]


def get_api_backend_root() -> Path:
    """Get the api-backend root directory."""
    return _get_api_backend_root()


def find_python_files(root: Path, include_pattern: str = "src/**/*.py") -> List[Path]:
    """Find all Python files matching the pattern."""
    return list(root.glob(include_pattern))


def check_file_for_deprecated_imports(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Check a Python file for deprecated module imports.
    
    Detects both direct and aliased imports:
    - import utils.preauth_token
    - import utils.preauth_token as preauth  (aliased)
    - from utils.preauth_token import generate_preauth_token
    - from utils.preauth_token import generate_preauth_token as gen_token  (aliased)
    
    Returns:
        List of (line_number, import_statement, deprecated_module) tuples
    """
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for deprecated in DEPRECATED_MODULES:
                        if alias.name == deprecated or alias.name.endswith(f".{deprecated}"):
                            import_stmt = f"import {alias.name}"
                            if alias.asname:
                                import_stmt += f" as {alias.asname}"
                            violations.append((
                                node.lineno,
                                import_stmt,
                                deprecated
                            ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for deprecated in DEPRECATED_MODULES:
                        if node.module == deprecated or node.module.endswith(f".{deprecated}"):
                            names_list = []
                            for alias in node.names:
                                if alias.asname:
                                    names_list.append(f"{alias.name} as {alias.asname}")
                                else:
                                    names_list.append(alias.name)
                            import_stmt = f"from {node.module} import {', '.join(names_list)}"
                            violations.append((
                                node.lineno,
                                import_stmt,
                                deprecated
                            ))
                        elif deprecated.endswith(f".{node.module}"):
                            for alias in node.names:
                                if alias.name == deprecated.split('.')[-1]:
                                    import_stmt = f"from {node.module} import {alias.name}"
                                    if alias.asname:
                                        import_stmt += f" as {alias.asname}"
                                    violations.append((
                                        node.lineno,
                                        import_stmt,
                                        deprecated
                                    ))
    
    except SyntaxError:
        pass
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
    
    return violations


def test_no_deprecated_imports_in_src():
    """
    Test that deprecated modules are not imported in src/** code.
    
    This enforces the deprecation policy by failing CI if production code
    imports deprecated modules. Tests are excluded to allow backward
    compatibility testing.
    """
    root = get_api_backend_root()
    python_files = find_python_files(root, "src/**/*.py")
    
    all_violations = []
    
    for file_path in python_files:
        relative_path = file_path.relative_to(root)
        if str(relative_path) in ALLOWLIST:
            continue
        
        violations = check_file_for_deprecated_imports(file_path)
        if violations:
            all_violations.append((file_path, violations))
    
    if all_violations:
        error_message = [
            "\n❌ Deprecated module imports found in production code!\n",
            "The following files import deprecated modules:\n"
        ]
        
        for file_path, violations in all_violations:
            relative_path = file_path.relative_to(root)
            error_message.append(f"\n📄 {relative_path}:")
            for line_no, import_stmt, deprecated_module in violations:
                error_message.append(f"  Line {line_no}: {import_stmt}")
                error_message.append(f"    ❌ Deprecated: {deprecated_module}")
        
        error_message.extend([
            "\n",
            "🔧 Migration Guide:",
            "  - Replace 'utils.preauth_token' with 'utils.pre_auth_token'",
            "  - Use PreAuthTokenManager class instead of standalone functions:",
            "    • generate_preauth_token() → PreAuthTokenManager.generate_token()",
            "    • validate_and_consume_preauth_token() → PreAuthTokenManager.verify_token() + consume_token_atomic()",
            "    • revoke_preauth_tokens_for_user() → PreAuthTokenManager.revoke_token()",
            "\n",
            "📚 See: handoff/20250928/40_App/api-backend/src/utils/pre_auth_token.py",
            ""
        ])
        
        raise AssertionError("\n".join(error_message))


if __name__ == "__main__":
    test_no_deprecated_imports_in_src()
    print("✅ No deprecated imports found in src/**")


def test_aliased_import_detection():
    """
    Test that aliased imports of deprecated modules are detected.
    
    This verifies Task 7: Extend lint checks to cover aliased imports.
    """
    import tempfile
    
    test_cases = [
        # (code, should_detect, description)
        ("import utils.preauth_token", True, "Direct module import"),
        ("import utils.preauth_token as preauth", True, "Module import with alias"),
        ("from utils.preauth_token import generate_preauth_token", True, "Direct function import"),
        ("from utils.preauth_token import generate_preauth_token as gen_token", True, "Function import with alias"),
        ("from utils.preauth_token import generate_preauth_token as gen, validate_and_consume_preauth_token as validate", True, "Multiple imports with aliases"),
        ("from utils.preauth_token import generate_preauth_token, validate_and_consume_preauth_token as validate", True, "Mixed imports (some aliased)"),
        ("from utils.pre_auth_token import PreAuthTokenManager", False, "Valid import (not deprecated)"),
        ("import utils.pre_auth_token", False, "Valid module import (not deprecated)"),
        ("from utils.pre_auth_token import PreAuthTokenManager as Manager", False, "Valid aliased import (not deprecated)"),
    ]
    
    for code, should_detect, description in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(Path(f.name))
            
            if should_detect:
                assert len(violations) > 0, f"Failed to detect: {description}\n  Code: {code}"
                line_no, import_stmt, deprecated = violations[0]
                assert deprecated in DEPRECATED_MODULES, f"Wrong deprecated module for: {description}"
            else:
                assert len(violations) == 0, f"False positive for: {description}\n  Code: {code}\n  Violations: {violations}"
            
            Path(f.name).unlink()


if __name__ == "__main__":
    test_no_deprecated_imports_in_src()
    print("✅ No deprecated imports found in src/**")
    test_aliased_import_detection()
    print("✅ Aliased import detection working correctly")
