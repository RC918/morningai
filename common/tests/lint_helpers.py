"""
Shared helpers for lint tests across the codebase.

This module provides reusable AST scanning logic for detecting deprecated
module imports in Python files. It's used by lint tests in api-backend,
orchestrator, and agents.
"""

import ast
from pathlib import Path
from typing import List, Tuple


def check_file_for_deprecated_imports(
    file_path: Path,
    deprecated_modules: List[str]
) -> List[Tuple[int, str, str]]:
    """
    Check a Python file for deprecated module imports.
    
    Detects both direct and aliased imports:
    - import utils.preauth_token
    - import utils.preauth_token as preauth  (aliased)
    - from utils.preauth_token import generate_preauth_token
    - from utils.preauth_token import generate_preauth_token as gen_token  (aliased)
    - from utils import preauth_token
    - from utils import preauth_token as pt  (aliased)
    - from utils.preauth_token import *  (star import)
    
    Skips relative imports (e.g., from .module import something) as they are
    internal to packages and not subject to deprecation policies.
    
    Args:
        file_path: Path to Python file to scan
        deprecated_modules: List of deprecated module fully qualified names (FQNs)
    
    Returns:
        List of (line_number, import_statement, deprecated_module) tuples
        
    Example:
        >>> deprecated = ["utils.preauth_token", "src.utils.preauth_token"]
        >>> violations = check_file_for_deprecated_imports(Path("app.py"), deprecated)
        >>> if violations:
        ...     for line_no, import_stmt, deprecated_mod in violations:
        ...         print(f"Line {line_no}: {import_stmt} (deprecated: {deprecated_mod})")
    """
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for deprecated in deprecated_modules:
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
                if node.level > 0:
                    continue
                
                if node.module:
                    for deprecated in deprecated_modules:
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
                        else:
                            for alias in node.names:
                                fqn = f"{node.module}.{alias.name}"
                                if fqn == deprecated:
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


def find_python_files(
    root: Path,
    include_pattern: str = "**/*.py",
    exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Find all Python files matching the pattern.
    
    Args:
        root: Root directory to search from
        include_pattern: Glob pattern for files to include (default: "**/*.py")
        exclude_patterns: List of glob patterns to exclude (e.g., ["tests/**", "migrations/**"])
    
    Returns:
        List of matching Python file paths
        
    Example:
        >>> root = Path("/app")
        >>> # Find all Python files in src/, excluding tests
        >>> files = find_python_files(root, "src/**/*.py", exclude_patterns=["src/tests/**"])
        >>> # Find all Python files, excluding tests and migrations
        >>> files = find_python_files(root, "**/*.py", exclude_patterns=["tests/**", "migrations/**"])
    """
    if exclude_patterns is None:
        exclude_patterns = []
    
    all_files = list(root.glob(include_pattern))
    
    filtered_files = []
    for file_path in all_files:
        relative_path = file_path.relative_to(root)
        
        excluded = False
        for exclude_pattern in exclude_patterns:
            if relative_path.match(exclude_pattern):
                excluded = True
                break
        
        if not excluded:
            filtered_files.append(file_path)
    
    return filtered_files


def format_violations_message(
    all_violations: List[Tuple[Path, List[Tuple[int, str, str]]]],
    root: Path,
    migration_guide: List[str] = None
) -> str:
    """
    Format violations into a human-readable error message.
    
    Args:
        all_violations: List of (file_path, violations) tuples
        root: Root directory for computing relative paths
        migration_guide: Optional list of migration guide lines
    
    Returns:
        Formatted error message string
        
    Example:
        >>> violations = [(Path("/app/src/main.py"), [(10, "import utils.preauth_token", "utils.preauth_token")])]
        >>> message = format_violations_message(violations, Path("/app"))
        >>> print(message)
    """
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
    
    if migration_guide:
        error_message.append("\n")
        error_message.extend(migration_guide)
    
    error_message.append("")
    
    return "\n".join(error_message)
