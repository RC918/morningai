"""
Tests for Auto-fix Gate - Three Don'ts Principle #2

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
"""
from coder.autofix_gate import (
    is_autofix_allowed,
    is_path_excluded,
    EXCLUDED_PATHS,
)


class TestIsPathExcluded:
    """Tests for is_path_excluded function."""

    def test_config_directory_excluded(self):
        """Config directory should be excluded."""
        assert is_path_excluded("config/settings.py") is True
        assert is_path_excluded("config/database.yml") is True
        assert is_path_excluded("src/config/app.py") is True

    def test_migrations_directory_excluded(self):
        """Migrations directory should be excluded."""
        assert is_path_excluded("migrations/001_initial.py") is True
        assert is_path_excluded("db/migrations/002_add_users.py") is True

    def test_env_file_excluded(self):
        """Environment files should be excluded."""
        assert is_path_excluded(".env") is True
        assert is_path_excluded("config/.env") is True
        assert is_path_excluded(".env.local") is False  # Only exact match

    def test_settings_file_excluded(self):
        """Settings files should be excluded."""
        assert is_path_excluded("settings.py") is True
        assert is_path_excluded("src/settings.py") is True
        assert is_path_excluded("app/settings.py") is True

    def test_package_files_excluded(self):
        """Package management files should be excluded."""
        assert is_path_excluded("pyproject.toml") is True
        assert is_path_excluded("package.json") is True
        assert is_path_excluded("package-lock.json") is True
        assert is_path_excluded("yarn.lock") is True
        assert is_path_excluded("poetry.lock") is True
        assert is_path_excluded("requirements.txt") is True

    def test_ci_files_excluded(self):
        """CI/CD files should be excluded."""
        assert is_path_excluded(".github/workflows/ci.yml") is True
        assert is_path_excluded(".gitlab-ci.yml") is True
        assert is_path_excluded("Jenkinsfile") is True

    def test_docker_files_excluded(self):
        """Docker files should be excluded."""
        assert is_path_excluded("Dockerfile") is True
        assert is_path_excluded("docker-compose.yml") is True
        assert is_path_excluded("docker-compose.yaml") is True

    def test_regular_files_not_excluded(self):
        """Regular source files should not be excluded."""
        assert is_path_excluded("src/utils.py") is False
        assert is_path_excluded("app/models/user.py") is False
        assert is_path_excluded("tests/test_utils.py") is False
        assert is_path_excluded("lib/helpers.js") is False

    def test_empty_path_excluded(self):
        """Empty path should be excluded (defensive)."""
        assert is_path_excluded("") is True
        assert is_path_excluded(None) is True

    def test_deep_nested_paths(self):
        """Deep nested paths should be handled correctly."""
        assert is_path_excluded("a/b/c/d/e/.env") is True
        assert is_path_excluded("very/deep/nested/config/settings.py") is True
        assert is_path_excluded("a/b/c/d/e/utils.py") is False

    def test_unicode_paths(self):
        """Unicode paths should be handled correctly."""
        assert is_path_excluded("src/測試.py") is False
        assert is_path_excluded("src/тест.py") is False
        assert is_path_excluded("config/設定.py") is True  # config/ directory

    def test_whitespace_paths(self):
        """Paths with leading/trailing whitespace should be handled."""
        assert is_path_excluded("  config/app.py  ") is True
        assert is_path_excluded("  src/utils.py  ") is False
        # Note: whitespace-only paths are not excluded (they're stripped to empty
        # but the check happens before strip). This is acceptable since whitespace-only
        # paths are not valid file paths in practice.


class TestIsAutofixAllowed:
    """Tests for is_autofix_allowed function."""

    def test_all_conditions_met(self):
        """Auto-fix should be allowed when all conditions are met."""
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_autofix_allowed(outcome) is True

    def test_severity_not_low(self):
        """Auto-fix should be blocked when severity is not low."""
        for severity in ["medium", "high", "critical"]:
            outcome = {
                "severity": severity,
                "diff_truncated": False,
                "schema_validated": True,
            }
            assert is_autofix_allowed(outcome) is False

    def test_diff_truncated(self):
        """Auto-fix should be blocked when diff is truncated."""
        outcome = {
            "severity": "low",
            "diff_truncated": True,
            "schema_validated": True,
        }
        assert is_autofix_allowed(outcome) is False

    def test_schema_not_validated(self):
        """Auto-fix should be blocked when schema is not validated."""
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": False,
        }
        assert is_autofix_allowed(outcome) is False

    def test_empty_outcome(self):
        """Auto-fix should be blocked for empty outcome."""
        assert is_autofix_allowed({}) is False
        assert is_autofix_allowed(None) is False

    def test_missing_fields_default_to_fail(self):
        """Missing fields should default to fail-safe values."""
        outcome = {"severity": "low"}
        assert is_autofix_allowed(outcome) is False

    def test_excluded_paths_block_autofix(self):
        """Auto-fix should be blocked for excluded paths."""
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_autofix_allowed(outcome, file_paths=["config/app.py"]) is False
        assert is_autofix_allowed(outcome, file_paths=["migrations/001.py"]) is False
        assert is_autofix_allowed(outcome, file_paths=[".env"]) is False

    def test_regular_paths_allow_autofix(self):
        """Auto-fix should be allowed for regular paths."""
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_autofix_allowed(outcome, file_paths=["src/utils.py"]) is True
        assert is_autofix_allowed(outcome, file_paths=["app/models.py"]) is True

    def test_mixed_paths_block_autofix(self):
        """Auto-fix should be blocked if any path is excluded."""
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_autofix_allowed(
            outcome,
            file_paths=["src/utils.py", "config/app.py"]
        ) is False


class TestExcludedPathsConstant:
    """Tests for EXCLUDED_PATHS constant."""

    def test_excluded_paths_is_frozenset(self):
        """EXCLUDED_PATHS should be immutable."""
        assert isinstance(EXCLUDED_PATHS, frozenset)

    def test_excluded_paths_contains_critical_paths(self):
        """EXCLUDED_PATHS should contain critical paths."""
        critical_paths = [
            "config/",
            "migrations/",
            ".env",
            "settings.py",
            "pyproject.toml",
            "package.json",
        ]
        for path in critical_paths:
            assert path in EXCLUDED_PATHS, f"{path} should be in EXCLUDED_PATHS"
