"""
Test to ensure deprecated modules are not imported in production code.

This test scans src/** for imports of deprecated modules and fails CI if found.
Tests are excluded to allow backward compatibility testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

from common.tests.lint_helpers import (
    check_file_for_deprecated_imports,
    find_python_files,
    format_violations_message
)
from common.tests.test_config import (
    API_BACKEND_DEPRECATED_MODULES,
    PREAUTH_TOKEN_MIGRATION_GUIDE
)
from src.utils.repo_root import get_api_backend_root as _get_api_backend_root


DEPRECATED_MODULES = API_BACKEND_DEPRECATED_MODULES

ALLOWLIST = [
]


def get_api_backend_root() -> Path:
    """Get the api-backend root directory."""
    return _get_api_backend_root()


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
        
        violations = check_file_for_deprecated_imports(file_path, DEPRECATED_MODULES)
        if violations:
            all_violations.append((file_path, violations))
    
    if all_violations:
        error_message = format_violations_message(
            all_violations,
            root,
            PREAUTH_TOKEN_MIGRATION_GUIDE
        )
        raise AssertionError(error_message)


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
        ("import utils.preauth_token", True, "Direct module import"),
        ("import utils.preauth_token as preauth", True, "Module import with alias"),
        ("from utils.preauth_token import generate_preauth_token", True, "Direct function import"),
        ("from utils.preauth_token import generate_preauth_token as gen_token", True, "Function import with alias"),
        ("from utils.preauth_token import generate_preauth_token as gen, validate_and_consume_preauth_token as validate", True, "Multiple imports with aliases"),
        ("from utils.preauth_token import generate_preauth_token, validate_and_consume_preauth_token as validate", True, "Mixed imports (some aliased)"),
        ("from utils import preauth_token", True, "Import submodule from parent"),
        ("from utils import preauth_token as pt", True, "Import submodule from parent with alias"),
        ("from utils.preauth_token import *", True, "Star import"),
        ("from utils.preauth_token import (\n    generate_preauth_token as gen\n)", True, "Multi-line import with parentheses"),
        ("from utils.pre_auth_token import PreAuthTokenManager", False, "Valid import (not deprecated)"),
        ("import utils.pre_auth_token", False, "Valid module import (not deprecated)"),
        ("from utils.pre_auth_token import PreAuthTokenManager as Manager", False, "Valid aliased import (not deprecated)"),
        ("import utils.preauth_token_tools", False, "Similar name should not trigger"),
        ("from utils import preauth_token_tools", False, "Similar submodule name should not trigger"),
    ]
    
    for code, should_detect, description in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(Path(f.name), DEPRECATED_MODULES)
            
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
