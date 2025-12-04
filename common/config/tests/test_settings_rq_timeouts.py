"""
Unit tests for RQ timeout configuration settings (Phase 3 P4 #1817).

Tests verify that the timeout-related settings correctly read from
environment variables and validate timeout hierarchy.
"""
import warnings
from common.config.settings import get_settings, reload_settings


class TestRQTimeoutSettings:
    """Test suite for RQ timeout configuration settings."""

    def test_rq_job_timeout_default(self, monkeypatch):
        """Test that rq_job_timeout defaults to 600 seconds."""
        monkeypatch.delenv("RQ_JOB_TIMEOUT", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.rq_job_timeout == 600, \
            f"Expected default 600 but got {settings.rq_job_timeout}"

    def test_rq_job_timeout_from_env(self, monkeypatch):
        """Test that rq_job_timeout reads from RQ_JOB_TIMEOUT env var."""
        monkeypatch.setenv("RQ_JOB_TIMEOUT", "1200")

        reload_settings()

        settings = get_settings()
        assert settings.rq_job_timeout == 1200, \
            f"Expected 1200 but got {settings.rq_job_timeout}"

    def test_rq_task_ttl_default(self, monkeypatch):
        """Test that rq_task_ttl defaults to 600 seconds."""
        monkeypatch.delenv("RQ_TASK_TTL", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.rq_task_ttl == 600, \
            f"Expected default 600 but got {settings.rq_task_ttl}"

    def test_rq_task_ttl_from_env(self, monkeypatch):
        """Test that rq_task_ttl reads from RQ_TASK_TTL env var."""
        monkeypatch.setenv("RQ_TASK_TTL", "900")

        reload_settings()

        settings = get_settings()
        assert settings.rq_task_ttl == 900, \
            f"Expected 900 but got {settings.rq_task_ttl}"

    def test_rq_result_ttl_default(self, monkeypatch):
        """Test that rq_result_ttl defaults to 86400 seconds (24 hours)."""
        monkeypatch.delenv("RQ_RESULT_TTL", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.rq_result_ttl == 86400, \
            f"Expected default 86400 but got {settings.rq_result_ttl}"

    def test_rq_result_ttl_from_env(self, monkeypatch):
        """Test that rq_result_ttl reads from RQ_RESULT_TTL env var."""
        monkeypatch.setenv("RQ_RESULT_TTL", "172800")

        reload_settings()

        settings = get_settings()
        assert settings.rq_result_ttl == 172800, \
            f"Expected 172800 but got {settings.rq_result_ttl}"

    def test_rq_failure_ttl_default(self, monkeypatch):
        """Test that rq_failure_ttl defaults to 3600 seconds (1 hour)."""
        monkeypatch.delenv("RQ_FAILURE_TTL", raising=False)

        reload_settings()

        settings = get_settings()
        assert settings.rq_failure_ttl == 3600, \
            f"Expected default 3600 but got {settings.rq_failure_ttl}"

    def test_rq_failure_ttl_from_env(self, monkeypatch):
        """Test that rq_failure_ttl reads from RQ_FAILURE_TTL env var."""
        monkeypatch.setenv("RQ_FAILURE_TTL", "7200")

        reload_settings()

        settings = get_settings()
        assert settings.rq_failure_ttl == 7200, \
            f"Expected 7200 but got {settings.rq_failure_ttl}"


class TestTimeoutHierarchyValidation:
    """Test suite for timeout hierarchy validation."""

    def test_valid_timeout_hierarchy_no_warning(self, monkeypatch):
        """Test that valid timeout hierarchy does not emit warning."""
        monkeypatch.setenv("RQ_JOB_TIMEOUT", "600")
        monkeypatch.setenv("PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS", "300")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            reload_settings()

            timeout_warnings = [
                warning for warning in w
                if "RQ_JOB_TIMEOUT" in str(warning.message)
                and "PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS" in str(warning.message)
            ]
            assert len(timeout_warnings) == 0, \
                "Should not emit warning when job timeout > agent timeout"

    def test_invalid_timeout_hierarchy_emits_warning(self, monkeypatch):
        """Test that invalid timeout hierarchy emits warning."""
        monkeypatch.setenv("RQ_JOB_TIMEOUT", "300")
        monkeypatch.setenv("PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS", "600")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            reload_settings()

            timeout_warnings = [
                warning for warning in w
                if "RQ_JOB_TIMEOUT" in str(warning.message)
                and "PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS" in str(warning.message)
            ]
            assert len(timeout_warnings) >= 1, \
                "Should emit warning when job timeout <= agent timeout"

    def test_equal_timeouts_emits_warning(self, monkeypatch):
        """Test that equal timeouts emit warning."""
        monkeypatch.setenv("RQ_JOB_TIMEOUT", "300")
        monkeypatch.setenv("PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS", "300")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            reload_settings()

            timeout_warnings = [
                warning for warning in w
                if "RQ_JOB_TIMEOUT" in str(warning.message)
                and "PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS" in str(warning.message)
            ]
            assert len(timeout_warnings) >= 1, \
                "Should emit warning when job timeout == agent timeout"

    def test_default_timeouts_are_valid(self, monkeypatch):
        """Test that default timeout values form a valid hierarchy."""
        monkeypatch.delenv("RQ_JOB_TIMEOUT", raising=False)
        monkeypatch.delenv("PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS", raising=False)

        reload_settings()
        settings = get_settings()

        assert settings.rq_job_timeout > settings.project_engineer_task_timeout_seconds, \
            f"Default RQ_JOB_TIMEOUT ({settings.rq_job_timeout}) should be > " \
            f"PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS ({settings.project_engineer_task_timeout_seconds})"
