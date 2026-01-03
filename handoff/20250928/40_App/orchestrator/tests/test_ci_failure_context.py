"""
Tests for CiFailureContext contract hardening and regression (Issue #3512).

This module tests the CiFailureContext dataclass introduced in PR #3511:
1. Fallback behavior when ci_failure_trigger=True but ci_failure_context is missing
2. JSON serialization/deserialization roundtrip (RQ queue path)
3. Optional fields (logs_url, error_summary, check_run_id) can be None
4. _build_ci_fix_description handles None optional fields gracefully

Blueprint Alignment:
- Flow Controller v3: "Deterministic" - tests prove deterministic behavior
- Telemetry v2: "Reproducible" - serialization tests ensure reproducibility
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.flow.schema import CiFailureContext


class TestCiFailureContextSerialization:
    """Test CiFailureContext JSON serialization for RQ queue path."""

    def test_json_serialization_roundtrip_full(self):
        """CiFailureContext survives JSON serialization with all fields populated."""
        original = CiFailureContext(
            failed_check_name="lint",
            conclusion="failure",
            pr_number=123,
            head_sha="abc123def456",
            head_branch="feature/test",
            version=1,
            logs_url="https://github.com/test/repo/actions/runs/123",
            error_summary="F401: unused import 'os'",
            check_run_id=456789,
        )

        serialized = json.dumps(original.to_dict())
        deserialized_dict = json.loads(serialized)
        restored = CiFailureContext.from_dict(deserialized_dict)

        assert restored.failed_check_name == original.failed_check_name
        assert restored.conclusion == original.conclusion
        assert restored.pr_number == original.pr_number
        assert restored.head_sha == original.head_sha
        assert restored.head_branch == original.head_branch
        assert restored.version == original.version
        assert restored.logs_url == original.logs_url
        assert restored.error_summary == original.error_summary
        assert restored.check_run_id == original.check_run_id

    def test_json_serialization_roundtrip_minimal(self):
        """CiFailureContext survives JSON serialization with only required fields."""
        original = CiFailureContext(
            failed_check_name="test",
            conclusion="timed_out",
            pr_number=456,
            head_sha="def789",
            head_branch="main",
        )

        serialized = json.dumps(original.to_dict())
        deserialized_dict = json.loads(serialized)
        restored = CiFailureContext.from_dict(deserialized_dict)

        assert restored.failed_check_name == original.failed_check_name
        assert restored.conclusion == original.conclusion
        assert restored.pr_number == original.pr_number
        assert restored.head_sha == original.head_sha
        assert restored.head_branch == original.head_branch
        assert restored.version == 1
        assert restored.logs_url is None
        assert restored.error_summary is None
        assert restored.check_run_id is None

    def test_to_dict_returns_json_serializable(self):
        """to_dict() returns a dict that can be serialized to JSON."""
        context = CiFailureContext(
            failed_check_name="build",
            conclusion="cancelled",
            pr_number=789,
            head_sha="xyz123",
            head_branch="develop",
        )

        result = context.to_dict()

        assert isinstance(result, dict)
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_from_dict_handles_missing_optional_fields(self):
        """from_dict() handles missing optional fields gracefully."""
        minimal_dict = {
            "failed_check_name": "security",
            "conclusion": "failure",
            "pr_number": 100,
            "head_sha": "sha123",
            "head_branch": "fix/security",
        }

        restored = CiFailureContext.from_dict(minimal_dict)

        assert restored.failed_check_name == "security"
        assert restored.conclusion == "failure"
        assert restored.pr_number == 100
        assert restored.head_sha == "sha123"
        assert restored.head_branch == "fix/security"
        assert restored.version == 1
        assert restored.logs_url is None
        assert restored.error_summary is None
        assert restored.check_run_id is None


class TestCiFailureContextOptionalFields:
    """Test that optional fields (logs_url, error_summary, check_run_id) can be None."""

    def test_optional_fields_none_safe(self):
        """Optional fields can be None without errors."""
        context = CiFailureContext(
            failed_check_name="lint",
            conclusion="failure",
            pr_number=123,
            head_sha="abc123",
            head_branch="main",
            logs_url=None,
            error_summary=None,
            check_run_id=None,
        )

        assert context.logs_url is None
        assert context.error_summary is None
        assert context.check_run_id is None
        assert context.failed_check_name == "lint"

    def test_optional_fields_default_to_none(self):
        """Optional fields default to None when not provided."""
        context = CiFailureContext(
            failed_check_name="test",
            conclusion="failure",
            pr_number=456,
            head_sha="def456",
            head_branch="feature",
        )

        assert context.logs_url is None
        assert context.error_summary is None
        assert context.check_run_id is None

    def test_partial_optional_fields(self):
        """Some optional fields can be set while others remain None."""
        context = CiFailureContext(
            failed_check_name="build",
            conclusion="failure",
            pr_number=789,
            head_sha="ghi789",
            head_branch="develop",
            logs_url="https://example.com/logs",
            error_summary=None,
            check_run_id=12345,
        )

        assert context.logs_url == "https://example.com/logs"
        assert context.error_summary is None
        assert context.check_run_id == 12345


class TestBuildCiFixDescriptionWithNoneFields:
    """Test _build_ci_fix_description handles None optional fields gracefully."""

    def test_build_description_with_error_summary(self):
        """_build_ci_fix_description uses error_summary when available."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()

            context = CiFailureContext(
                failed_check_name="lint",
                conclusion="failure",
                pr_number=123,
                head_sha="abc123",
                head_branch="main",
                error_summary="F401: unused import 'os'",
                logs_url="https://example.com/logs",
            )

            result = fixer._build_ci_fix_description(
                context, pr_number=123, changed_files=["src/main.py"]
            )

            assert "Fix CI failures for PR #123" in result
            assert "lint" in result
            assert "failure" in result
            assert "F401: unused import 'os'" in result
            assert "src/main.py" in result

    def test_build_description_with_logs_url_only(self):
        """_build_ci_fix_description uses logs_url when error_summary is None."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()

            context = CiFailureContext(
                failed_check_name="test",
                conclusion="failure",
                pr_number=456,
                head_sha="def456",
                head_branch="feature",
                error_summary=None,
                logs_url="https://github.com/test/repo/actions/runs/789",
            )

            result = fixer._build_ci_fix_description(
                context, pr_number=456, changed_files=["tests/test_main.py"]
            )

            assert "Fix CI failures for PR #456" in result
            assert "test" in result
            assert "failure" in result
            assert "https://github.com/test/repo/actions/runs/789" in result
            assert "tests/test_main.py" in result

    def test_build_description_with_no_optional_fields(self):
        """_build_ci_fix_description handles all None optional fields."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()

            context = CiFailureContext(
                failed_check_name="build",
                conclusion="timed_out",
                pr_number=789,
                head_sha="ghi789",
                head_branch="develop",
                error_summary=None,
                logs_url=None,
            )

            result = fixer._build_ci_fix_description(
                context, pr_number=789, changed_files=["src/app.py"]
            )

            assert "Fix CI failures for PR #789" in result
            assert "build" in result
            assert "timed_out" in result
            assert "review the changed files" in result
            assert "src/app.py" in result

    def test_build_description_without_pr_number(self):
        """_build_ci_fix_description handles None pr_number."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()

            context = CiFailureContext(
                failed_check_name="lint",
                conclusion="failure",
                pr_number=123,
                head_sha="abc123",
                head_branch="main",
            )

            result = fixer._build_ci_fix_description(
                context, pr_number=None, changed_files=["src/main.py"]
            )

            assert "Fix CI failures found in automated checks" in result
            assert "lint" in result


class TestFallbackWhenContextMissing:
    """Test fallback behavior when ci_failure_trigger=True but ci_failure_context is missing."""

    @pytest.mark.asyncio
    async def test_fallback_to_reviewer_when_context_none(self):
        """ci_failure_trigger=True with missing context falls back to ReviewerAgent."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()
            fixer.settings = MagicMock()
            fixer.settings.enable_project_engineer_codegen = True
            fixer._project_engineer_agent = None
            fixer._dev_agent = None

            mock_review_result = MagicMock()
            mock_review_result.passed = True

            state = {
                "trace_id": "test-trace-123",
                "ci_failure_trigger": True,
                "ci_failure_context": None,
                "repo": "test/repo",
                "pr_number": 123,
            }

            with patch.object(
                fixer, "_get_changed_files", new_callable=AsyncMock
            ) as mock_get_files:
                mock_get_files.return_value = ["src/main.py"]

                with patch.object(
                    fixer, "_run_reviewer", new_callable=AsyncMock
                ) as mock_reviewer:
                    mock_reviewer.return_value = mock_review_result

                    await fixer.run_auto_fix(state)

                    mock_reviewer.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_to_reviewer_when_context_missing_key(self):
        """ci_failure_trigger=True with missing ci_failure_context key falls back to ReviewerAgent."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()
            fixer.settings = MagicMock()
            fixer.settings.enable_project_engineer_codegen = True
            fixer._project_engineer_agent = None
            fixer._dev_agent = None

            mock_review_result = MagicMock()
            mock_review_result.passed = True

            state = {
                "trace_id": "test-trace-456",
                "ci_failure_trigger": True,
                "repo": "test/repo",
                "pr_number": 456,
            }

            with patch.object(
                fixer, "_get_changed_files", new_callable=AsyncMock
            ) as mock_get_files:
                mock_get_files.return_value = ["src/app.py"]

                with patch.object(
                    fixer, "_run_reviewer", new_callable=AsyncMock
                ) as mock_reviewer:
                    mock_reviewer.return_value = mock_review_result

                    await fixer.run_auto_fix(state)

                    mock_reviewer.assert_called_once()

    @pytest.mark.asyncio
    async def test_ci_mode_used_when_context_present(self):
        """ci_failure_trigger=True with valid context uses CI evidence directly."""
        from project_engineer.fixer_integration import AutoFixer

        with patch.object(AutoFixer, "__init__", lambda self: None):
            fixer = AutoFixer()
            fixer.settings = MagicMock()
            fixer.settings.enable_project_engineer_codegen = True
            fixer.settings.github_repo = "test/repo"
            fixer._project_engineer_agent = None
            fixer._dev_agent = None

            ci_context = CiFailureContext(
                failed_check_name="lint",
                conclusion="failure",
                pr_number=789,
                head_sha="abc123",
                head_branch="main",
                error_summary="F401: unused import",
            )

            state = {
                "trace_id": "test-trace-789",
                "ci_failure_trigger": True,
                "ci_failure_context": ci_context.to_dict(),
                "repo": "test/repo",
                "pr_number": 789,
            }

            with patch.object(
                fixer, "_get_changed_files", new_callable=AsyncMock
            ) as mock_get_files:
                mock_get_files.return_value = ["src/main.py"]

                with patch.object(
                    fixer, "_run_reviewer", new_callable=AsyncMock
                ) as mock_reviewer:
                    with patch.object(
                        fixer, "_run_project_engineer", new_callable=AsyncMock
                    ) as mock_engineer:
                        mock_engineer.return_value = {"success": True, "pr_number": 100}

                        await fixer.run_auto_fix(state)

                        mock_reviewer.assert_not_called()
                        mock_engineer.assert_called_once()
                        assert "lint" in mock_engineer.call_args[0][0]


class TestCiFailureContextVersioning:
    """Test CiFailureContext schema versioning for backward compatibility."""

    def test_version_defaults_to_1(self):
        """Version field defaults to 1."""
        context = CiFailureContext(
            failed_check_name="lint",
            conclusion="failure",
            pr_number=123,
            head_sha="abc123",
            head_branch="main",
        )

        assert context.version == 1

    def test_from_dict_handles_missing_version(self):
        """from_dict() defaults version to 1 when missing."""
        data = {
            "failed_check_name": "test",
            "conclusion": "failure",
            "pr_number": 456,
            "head_sha": "def456",
            "head_branch": "feature",
        }

        context = CiFailureContext.from_dict(data)

        assert context.version == 1

    def test_version_preserved_in_roundtrip(self):
        """Version field is preserved through serialization roundtrip."""
        original = CiFailureContext(
            failed_check_name="build",
            conclusion="failure",
            pr_number=789,
            head_sha="ghi789",
            head_branch="develop",
            version=2,
        )

        restored = CiFailureContext.from_dict(original.to_dict())

        assert restored.version == 2
