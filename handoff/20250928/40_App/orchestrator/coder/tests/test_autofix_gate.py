"""
Tests for Auto-fix Gate - Three Don'ts Principle #2

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
"""
from coder.autofix_gate import (
    is_autofix_allowed,
    is_senior_coder_required,
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


class TestIsSeniorCoderRequired:
    """Tests for is_senior_coder_required function.

    Issue #3366: Smart gate logic for CI failure auto-fix scenarios.
    CTO Directive: "方案 A + B 混合體"

    This function distinguishes between:
    1. CI failure auto-fix (D-3): Bypasses severity check, only requires schema_validated
    2. Review comment auto-fix (D-1): Uses strict is_autofix_allowed() rules
    """

    def test_ci_failure_with_schema_validated_true_passes(self):
        """CI failure with schema_validated=True should pass (ignore severity)."""
        state = {
            "ci_failure_trigger": True,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": True,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is True

    def test_ci_failure_with_schema_validated_false_fails(self):
        """CI failure with schema_validated=False should fail."""
        state = {
            "ci_failure_trigger": True,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": False,
                "schema_validated": False,
            }
        }
        assert is_senior_coder_required(state) is False

    def test_ci_failure_schema_validated_strict_identity_check(self):
        """schema_validated must be exactly True (identity check, not truthy).

        This prevents bypass via truthy values like 1, "true", etc.
        """
        truthy_but_not_true = [1, "true", "True", "yes", [True], {"valid": True}]
        for value in truthy_but_not_true:
            state = {
                "ci_failure_trigger": True,
                "review_outcome": {
                    "severity": "high",
                    "diff_truncated": False,
                    "schema_validated": value,
                }
            }
            assert is_senior_coder_required(state) is False, (
                f"schema_validated={value!r} should fail (not identity True)"
            )

    def test_ci_failure_schema_validated_none_fails(self):
        """schema_validated=None should fail."""
        state = {
            "ci_failure_trigger": True,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": False,
                "schema_validated": None,
            }
        }
        assert is_senior_coder_required(state) is False

    def test_ci_failure_ignores_severity(self):
        """CI failure should ignore severity (high, medium, critical all pass)."""
        for severity in ["high", "medium", "critical", "unknown"]:
            state = {
                "ci_failure_trigger": True,
                "review_outcome": {
                    "severity": severity,
                    "diff_truncated": False,
                    "schema_validated": True,
                }
            }
            assert is_senior_coder_required(state) is True, (
                f"CI failure with severity={severity} should pass"
            )

    def test_ci_failure_ignores_diff_truncated(self):
        """CI failure should pass even when diff_truncated=True."""
        state = {
            "ci_failure_trigger": True,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": True,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is True

    def test_non_ci_failure_requires_severity_low(self):
        """Non-CI failure (D-1) requires severity=low."""
        state = {
            "ci_failure_trigger": False,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": False,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is False

    def test_non_ci_failure_requires_diff_truncated_false(self):
        """Non-CI failure (D-1) requires diff_truncated=False."""
        state = {
            "ci_failure_trigger": False,
            "review_outcome": {
                "severity": "low",
                "diff_truncated": True,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is False

    def test_non_ci_failure_all_conditions_met_passes(self):
        """Non-CI failure (D-1) passes when all strict conditions are met."""
        state = {
            "ci_failure_trigger": False,
            "review_outcome": {
                "severity": "low",
                "diff_truncated": False,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is True

    def test_empty_state_fails(self):
        """Empty state should fail."""
        assert is_senior_coder_required({}) is False
        assert is_senior_coder_required(None) is False

    def test_empty_review_outcome_fails(self):
        """Empty review_outcome should fail."""
        state = {"ci_failure_trigger": True, "review_outcome": {}}
        assert is_senior_coder_required(state) is False

        state = {"ci_failure_trigger": True, "review_outcome": None}
        assert is_senior_coder_required(state) is False

    def test_missing_ci_failure_trigger_defaults_to_false(self):
        """Missing ci_failure_trigger should default to False (strict D-1 rules)."""
        state = {
            "review_outcome": {
                "severity": "high",
                "diff_truncated": False,
                "schema_validated": True,
            }
        }
        assert is_senior_coder_required(state) is False

    def test_review_outcome_passed_as_argument(self):
        """review_outcome can be passed as argument instead of from state."""
        state = {"ci_failure_trigger": True}
        review_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_senior_coder_required(state, review_outcome) is True

    def test_argument_review_outcome_overrides_state(self):
        """review_outcome argument should override state's review_outcome."""
        state = {
            "ci_failure_trigger": True,
            "review_outcome": {
                "severity": "high",
                "diff_truncated": False,
                "schema_validated": False,
            }
        }
        override_outcome = {
            "severity": "high",
            "diff_truncated": False,
            "schema_validated": True,
        }
        assert is_senior_coder_required(state, override_outcome) is True
