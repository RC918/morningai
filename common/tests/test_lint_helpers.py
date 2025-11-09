"""
Unit tests for lint_helpers.py

These tests validate the shared AST scanning logic used across api-backend,
orchestrator, and agents for detecting deprecated module imports.
"""

import tempfile
from pathlib import Path

from common.tests.lint_helpers import (
    check_file_for_deprecated_imports,
    find_python_files,
    format_violations_message
)


class TestCheckFileForDeprecatedImports:
    """Test the check_file_for_deprecated_imports function."""
    
    def test_detects_direct_import(self):
        """Test that direct module imports are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import utils.preauth_token\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert import_stmt == "import utils.preauth_token"
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_detects_aliased_import(self):
        """Test that aliased module imports are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import utils.preauth_token as preauth\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert import_stmt == "import utils.preauth_token as preauth"
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_detects_from_import(self):
        """Test that 'from X import Y' statements are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from utils.preauth_token import generate_preauth_token\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert "from utils.preauth_token import" in import_stmt
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_detects_from_import_with_alias(self):
        """Test that 'from X import Y as Z' statements are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from utils.preauth_token import generate_preauth_token as gen\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert "as gen" in import_stmt
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_detects_submodule_import(self):
        """Test that 'from X import Y' where Y is a submodule is detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from utils import preauth_token\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert "from utils import preauth_token" in import_stmt
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_detects_star_import(self):
        """Test that star imports are detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from utils.preauth_token import *\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 1
            line_no, import_stmt, deprecated = violations[0]
            assert line_no == 1
            assert "*" in import_stmt
            assert deprecated == "utils.preauth_token"
            
            Path(f.name).unlink()
    
    def test_skips_relative_imports(self):
        """Test that relative imports are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from .preauth_token import generate_token\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["preauth_token"]
            )
            
            assert len(violations) == 0
            
            Path(f.name).unlink()
    
    def test_no_false_positives_for_valid_imports(self):
        """Test that valid imports are not flagged."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from utils.pre_auth_token import PreAuthTokenManager\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 0
            
            Path(f.name).unlink()
    
    def test_no_false_positives_for_similar_names(self):
        """Test that similar module names don't trigger false positives."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import utils.preauth_token_tools\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 0
            
            Path(f.name).unlink()
    
    def test_handles_syntax_errors_gracefully(self):
        """Test that syntax errors in files are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import utils.preauth_token\nthis is invalid syntax\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 0
            
            Path(f.name).unlink()
    
    def test_detects_multiple_violations_in_one_file(self):
        """Test that multiple violations in one file are all detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import utils.preauth_token\n")
            f.write("from utils.preauth_token import generate_token\n")
            f.write("from utils import preauth_token\n")
            f.flush()
            
            violations = check_file_for_deprecated_imports(
                Path(f.name),
                ["utils.preauth_token"]
            )
            
            assert len(violations) == 3
            assert violations[0][0] == 1  # Line 1
            assert violations[1][0] == 2  # Line 2
            assert violations[2][0] == 3  # Line 3
            
            Path(f.name).unlink()


class TestFindPythonFiles:
    """Test the find_python_files function."""
    
    def test_finds_python_files(self):
        """Test that Python files are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            (root / "test1.py").touch()
            (root / "test2.py").touch()
            (root / "test.txt").touch()
            
            files = find_python_files(root, "*.py")
            
            assert len(files) == 2
            assert all(f.suffix == ".py" for f in files)
    
    def test_excludes_patterns(self):
        """Test that exclude patterns work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "main.py").touch()
            (root / "tests" / "test_main.py").touch()
            
            files = find_python_files(root, "**/*.py", exclude_patterns=["tests/**"])
            
            assert len(files) == 1
            assert "src" in str(files[0])
            assert "tests" not in str(files[0])
    
    def test_recursive_search(self):
        """Test that recursive search works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            (root / "src" / "utils").mkdir(parents=True)
            (root / "src" / "main.py").touch()
            (root / "src" / "utils" / "helper.py").touch()
            
            files = find_python_files(root, "**/*.py")
            
            assert len(files) == 2


class TestFormatViolationsMessage:
    """Test the format_violations_message function."""
    
    def test_formats_single_violation(self):
        """Test formatting a single violation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            file_path = root / "test.py"
            file_path.touch()
            
            violations = [(file_path, [(10, "import utils.preauth_token", "utils.preauth_token")])]
            
            message = format_violations_message(violations, root)
            
            assert "test.py" in message
            assert "Line 10" in message
            assert "import utils.preauth_token" in message
            assert "utils.preauth_token" in message
    
    def test_formats_multiple_violations(self):
        """Test formatting multiple violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            file1 = root / "test1.py"
            file2 = root / "test2.py"
            file1.touch()
            file2.touch()
            
            violations = [
                (file1, [(10, "import utils.preauth_token", "utils.preauth_token")]),
                (file2, [(20, "from utils import preauth_token", "utils.preauth_token")])
            ]
            
            message = format_violations_message(violations, root)
            
            assert "test1.py" in message
            assert "test2.py" in message
            assert "Line 10" in message
            assert "Line 20" in message
    
    def test_includes_migration_guide(self):
        """Test that migration guide is included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            file_path = root / "test.py"
            file_path.touch()
            
            violations = [(file_path, [(10, "import utils.preauth_token", "utils.preauth_token")])]
            migration_guide = ["Migration Guide:", "- Step 1", "- Step 2"]
            
            message = format_violations_message(violations, root, migration_guide)
            
            assert "Migration Guide:" in message
            assert "- Step 1" in message
            assert "- Step 2" in message


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
