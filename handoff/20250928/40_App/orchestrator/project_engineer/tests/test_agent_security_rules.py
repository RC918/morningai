#!/usr/bin/env python3
"""
Unit tests for ProjectEngineerAgent security rules (#1916)

Tests for security validation methods in agent.py:
- _validate_repo_allowed: Repository validation
- _validate_directories_allowed: Directory validation
- _validate_task_type_allowed: Task type validation
- _validate_task_semantic_rules: Comprehensive semantic rules validation
- _get_task_timeout: Timeout configuration
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

import pytest  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from project_engineer.agent import ProjectEngineerAgent  # noqa: E402


class TestValidateRepoAllowed:
    """Test _validate_repo_allowed method"""

    def test_validate_repo_allowed_default_repo(self):
        """Should allow default repo RC918/morningai"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("RC918/morningai")
        assert is_allowed is True
        assert error == ""

    def test_validate_repo_allowed_disallowed_repo(self):
        """Should reject repos not in allowed list"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("unknown/repo")
        assert is_allowed is False
        assert "not allowed" in error.lower() or "not in" in error.lower()

    def test_validate_repo_allowed_empty_repo(self):
        """Should handle empty repo name"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("")
        assert is_allowed is False
        assert error != ""

    @patch('project_engineer.semantic_rules.validate_repo')
    def test_validate_repo_allowed_uses_semantic_rules(self, mock_validate_repo):
        """Should delegate to semantic_rules.validate_repo"""
        mock_validate_repo.return_value = (True, "")
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("RC918/morningai")
        assert is_allowed is True

    @patch('project_engineer.semantic_rules.validate_repo')
    def test_validate_repo_allowed_semantic_rules_rejection(self, mock_validate_repo):
        """Should return error from semantic_rules when repo rejected"""
        mock_validate_repo.return_value = (False, "Repository not in allowed list")
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("forbidden/repo")
        assert is_allowed is False
        assert "not" in error.lower()


class TestValidateDirectoriesAllowed:
    """Test _validate_directories_allowed method"""

    def test_validate_directories_allowed_empty_list(self):
        """Should allow empty file paths list"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_directories_allowed([])
        assert is_allowed is True
        assert error == ""

    def test_validate_directories_allowed_none(self):
        """Should handle None file paths"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_directories_allowed(None)
        assert is_allowed is True
        assert error == ""

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_directories_allowed_valid_paths(self, mock_get_validator):
        """Should allow paths in allowed directories"""
        mock_validator = MagicMock()
        mock_validator.validate_file_paths.return_value = (True, [])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_directories_allowed(["docs/README.md"])
        assert is_allowed is True
        assert error == ""

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_directories_allowed_invalid_paths(self, mock_get_validator):
        """Should reject paths not in allowed directories"""
        mock_violation = MagicMock()
        mock_violation.message = "File not in allowed directory"
        mock_validator = MagicMock()
        mock_validator.validate_file_paths.return_value = (False, [mock_violation])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_directories_allowed(["src/secret.py"])
        assert is_allowed is False
        assert "not in allowed directory" in error.lower()

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_directories_allowed_multiple_violations(self, mock_get_validator):
        """Should collect multiple violations"""
        mock_violation1 = MagicMock()
        mock_violation1.message = "File 1 not allowed"
        mock_violation2 = MagicMock()
        mock_violation2.message = "File 2 not allowed"
        mock_validator = MagicMock()
        mock_validator.validate_file_paths.return_value = (False, [mock_violation1, mock_violation2])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_directories_allowed(["file1.py", "file2.py"])
        assert is_allowed is False
        assert "File 1" in error
        assert "File 2" in error

    def test_validate_directories_allowed_import_error_fallback(self):
        """Should fallback gracefully when semantic_rules not available"""
        agent = ProjectEngineerAgent()
        with patch.dict('sys.modules', {'project_engineer.semantic_rules': None}):
            is_allowed, error = agent._validate_directories_allowed(["any/path.py"])
            assert is_allowed is True
            assert error == ""


class TestValidateTaskTypeAllowed:
    """Test _validate_task_type_allowed method"""

    def test_validate_task_type_allowed_safe_type(self):
        """Should allow safe task types"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("documentation_update")
        assert is_allowed is True

    def test_validate_task_type_allowed_test_generation(self):
        """Should allow test_generation task type"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("test_generation")
        assert is_allowed is True

    def test_validate_task_type_allowed_unknown_type(self):
        """Should reject unknown task types"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("unknown")
        assert is_allowed is False
        assert "not" in error.lower()

    @patch('project_engineer.semantic_rules.validate_task_type')
    def test_validate_task_type_allowed_uses_semantic_rules(self, mock_validate):
        """Should delegate to semantic_rules.validate_task_type"""
        mock_validate.return_value = (True, "")
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("documentation_update")
        assert is_allowed is True

    @patch('project_engineer.semantic_rules.validate_task_type')
    def test_validate_task_type_allowed_semantic_rules_rejection(self, mock_validate):
        """Should return error from semantic_rules when task type rejected"""
        mock_validate.return_value = (False, "Task type not allowed")
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("forbidden_type")
        assert is_allowed is False
        assert "not" in error.lower()

    def test_validate_task_type_allowed_empty_type(self):
        """Should handle empty task type"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_task_type_allowed("")
        assert is_allowed is False


class TestValidateTaskSemanticRules:
    """Test _validate_task_semantic_rules method"""

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_valid_task(self, mock_get_validator):
        """Should validate a fully valid task"""
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (True, [])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="RC918/morningai",
            task_type="documentation_update",
            action="write_file",
            file_paths=["docs/README.md"],
            command=None,
            trace_id="test-trace"
        )

        assert is_valid is True
        assert error == ""
        assert requires_approval is False

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_repo_violation(self, mock_get_validator):
        """Should detect repo violations"""
        mock_violation = MagicMock()
        mock_violation.message = "Repository not allowed"
        mock_violation.requires_approval = False
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (False, [mock_violation])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="forbidden/repo",
            task_type="documentation_update",
            action="write_file"
        )

        assert is_valid is False
        assert "not allowed" in error.lower()
        assert requires_approval is False

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_requires_approval(self, mock_get_validator):
        """Should detect tasks requiring HITL approval"""
        mock_violation = MagicMock()
        mock_violation.message = "High-risk action requires approval"
        mock_violation.requires_approval = True
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (False, [mock_violation])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="RC918/morningai",
            task_type="documentation_update",
            action="rm -rf",
            command="rm -rf /tmp/test"
        )

        assert requires_approval is True
        assert "approval" in error.lower()

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_multiple_violations(self, mock_get_validator):
        """Should collect multiple violations"""
        mock_violation1 = MagicMock()
        mock_violation1.message = "Repo not allowed"
        mock_violation1.requires_approval = False
        mock_violation2 = MagicMock()
        mock_violation2.message = "Task type not allowed"
        mock_violation2.requires_approval = False
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (False, [mock_violation1, mock_violation2])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="forbidden/repo",
            task_type="forbidden_type",
            action="write_file"
        )

        assert is_valid is False
        assert "Repo" in error
        assert "Task type" in error

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_hard_blocking_violation(self, mock_get_validator):
        """Should detect hard-blocking violations"""
        mock_violation = MagicMock()
        mock_violation.message = "Sensitive file modification blocked"
        mock_violation.requires_approval = False
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (False, [mock_violation])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="RC918/morningai",
            task_type="documentation_update",
            action="write_file",
            file_paths=["secrets.yaml"]
        )

        assert is_valid is False
        assert requires_approval is False

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_approval_only_violations(self, mock_get_validator):
        """Should allow tasks with only approval-required violations"""
        mock_violation = MagicMock()
        mock_violation.message = "Requires approval"
        mock_violation.requires_approval = True
        mock_validator = MagicMock()
        mock_validator.validate_task.return_value = (False, [mock_violation])
        mock_get_validator.return_value = mock_validator

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="RC918/morningai",
            task_type="documentation_update",
            action="write_file"
        )

        assert is_valid is True
        assert requires_approval is True

    def test_validate_task_semantic_rules_import_error_fallback(self):
        """Should fallback gracefully when semantic_rules not available"""
        agent = ProjectEngineerAgent()
        with patch.dict('sys.modules', {'project_engineer.semantic_rules': None}):
            is_valid, error, requires_approval = agent._validate_task_semantic_rules(
                repo="RC918/morningai",
                task_type="documentation_update",
                action="write_file"
            )
            assert is_valid is True
            assert error == ""
            assert requires_approval is False

    @patch('project_engineer.semantic_rules.get_validator')
    def test_validate_task_semantic_rules_exception_handling(self, mock_get_validator):
        """Should fail closed on validation errors"""
        mock_get_validator.side_effect = Exception("Validation error")

        agent = ProjectEngineerAgent()
        is_valid, error, requires_approval = agent._validate_task_semantic_rules(
            repo="RC918/morningai",
            task_type="documentation_update",
            action="write_file"
        )

        assert is_valid is False
        assert "error" in error.lower()
        assert requires_approval is False


class TestGetTaskTimeout:
    """Test _get_task_timeout method"""

    def test_get_task_timeout_default(self):
        """Should return default timeout when settings not available"""
        agent = ProjectEngineerAgent()
        timeout = agent._get_task_timeout()
        assert timeout == 300

    def test_get_task_timeout_from_settings(self):
        """Should read timeout from settings"""
        agent = ProjectEngineerAgent()
        mock_settings = MagicMock()
        mock_settings.project_engineer_task_timeout_seconds = 600
        with patch.dict('sys.modules', {'common.config.settings': MagicMock(settings=mock_settings)}):
            timeout = agent._get_task_timeout()
            assert timeout == 600

    def test_get_task_timeout_import_error(self):
        """Should return default on import error"""
        agent = ProjectEngineerAgent()
        with patch.dict('sys.modules', {'common.config.settings': None}):
            timeout = agent._get_task_timeout()
            assert timeout == 300


class TestRunTaskSecurityValidation:
    """Test security validation in run_task method"""

    @pytest.mark.asyncio
    async def test_run_task_repo_validation_failure(self):
        """Should return validation error for disallowed repo"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("Update README", repo="forbidden/repo")

        assert len(results) == 1
        assert results[0].status == "failed"
        assert results[0].task_type == "validation_error"
        assert "not allowed" in results[0].error.lower() or "not in" in results[0].error.lower()

    @pytest.mark.asyncio
    async def test_run_task_allowed_repo(self):
        """Should proceed with allowed repo"""
        agent = ProjectEngineerAgent()
        results = await agent.run_task("Update README", repo="RC918/morningai")

        assert len(results) >= 1
        for result in results:
            assert result.task_type != "validation_error" or result.status != "failed"

    @pytest.mark.asyncio
    async def test_run_task_empty_description_validation(self):
        """Should validate empty description"""
        agent = ProjectEngineerAgent()
        with pytest.raises(ValueError, match="cannot be empty"):
            await agent.run_task("")


class TestProcessStepSecurityValidation:
    """Test security validation in _process_step method"""

    @pytest.mark.asyncio
    async def test_process_step_semantic_rules_blocked(self):
        """Should block step when semantic rules validation fails"""
        agent = ProjectEngineerAgent()

        with patch.object(agent, '_validate_task_semantic_rules') as mock_validate:
            mock_validate.return_value = (False, "Semantic rules validation failed", False)

            result = await agent._process_step(
                step_text="Update sensitive file",
                step_index=0,
                trace_id="test-trace",
                repo="RC918/morningai"
            )

            assert result.status == "blocked"
            assert "semantic rules" in result.details.lower()

    @pytest.mark.asyncio
    async def test_process_step_requires_approval(self):
        """Should return pending_approval when HITL required"""
        agent = ProjectEngineerAgent()

        with patch.object(agent, '_validate_task_semantic_rules') as mock_validate:
            mock_validate.return_value = (True, "Requires approval", True)

            with patch.object(agent, '_validate_task_type_allowed') as mock_task_type:
                mock_task_type.return_value = (True, "")

                result = await agent._process_step(
                    step_text="High-risk operation",
                    step_index=0,
                    trace_id="test-trace",
                    repo="RC918/morningai"
                )

                assert result.status == "pending_approval"
                assert "approval" in result.details.lower()

    @pytest.mark.asyncio
    async def test_process_step_task_type_validation(self):
        """Should validate task type"""
        agent = ProjectEngineerAgent()

        result = await agent._process_step(
            step_text="Update documentation",
            step_index=0,
            trace_id="test-trace",
            repo="RC918/morningai"
        )

        assert result.task_type is not None
        assert result.status in ["skipped", "blocked", "success", "pending_approval"]

    @pytest.mark.asyncio
    async def test_process_step_action_mapping(self):
        """Should map task types to actions correctly"""
        agent = ProjectEngineerAgent()

        # Action mapping must use whitelisted actions from DEFAULT_ALLOWED_ACTIONS
        # Note: 'unknown' maps to 'read_file' (not 'analyze_code') because:
        # - 'read_file' is in DEFAULT_ALLOWED_ACTIONS whitelist
        # - 'analyze_code' is NOT in the whitelist, causing semantic rules validation to fail
        # - This was fixed in PR #3553 to resolve Root Cause #9 in Probe 0 validation
        action_mapping = {
            "documentation_update": "write_file",
            "test_generation": "write_file",
            "code_review": "review_code",
            "bug_fix": "write_file",
            "unknown": "read_file",  # Changed from analyze_code (Issue #3552)
        }

        for task_type, expected_action in action_mapping.items():
            with patch.object(agent, '_validate_task_semantic_rules') as mock_validate:
                mock_validate.return_value = (True, "", False)

                if agent.classifier:
                    with patch.object(agent.classifier, 'classify') as mock_classify:
                        mock_enum = MagicMock()
                        mock_enum.value = task_type
                        mock_classify.return_value = mock_enum

                        await agent._process_step(
                            step_text="Test step",
                            step_index=0,
                            trace_id="test-trace",
                            repo="RC918/morningai"
                        )

                        call_args = mock_validate.call_args
                        if call_args:
                            assert call_args.kwargs.get('action') == expected_action


class TestSecurityFeatureFlags:
    """Test security-related feature flags in get_status"""

    def test_get_status_security_features(self):
        """Should report security features in status"""
        agent = ProjectEngineerAgent()
        status = agent.get_status()

        assert "features" in status
        features = status["features"]

        assert features["safe_task_gating"] is True
        assert features["semantic_rules_v3"] is True
        assert features["directory_validation"] is True
        assert features["task_type_validation"] is True
        assert features["action_whitelist"] is True
        assert features["sensitive_file_blocking"] is True
        assert features["hitl_approval"] is True

    def test_get_status_version(self):
        """Should report correct version with security"""
        agent = ProjectEngineerAgent()
        status = agent.get_status()

        assert "security" in status["version"].lower()


class TestSecurityEdgeCases:
    """Test edge cases for security validation"""

    def test_validate_repo_with_special_characters(self):
        """Should reject repos with special characters that are not allowlisted"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("user/repo-with-dashes")
        assert is_allowed is False
        assert error != ""
        assert "not allowed" in error.lower() or "not in" in error.lower()

    def test_validate_repo_with_numbers(self):
        """Should reject repos with numbers that are not allowlisted"""
        agent = ProjectEngineerAgent()
        is_allowed, error = agent._validate_repo_allowed("user123/repo456")
        assert is_allowed is False
        assert error != ""
        assert "not allowed" in error.lower() or "not in" in error.lower()

    @pytest.mark.asyncio
    async def test_process_step_exception_handling(self):
        """Should handle exceptions gracefully"""
        agent = ProjectEngineerAgent()

        with patch.object(agent, 'classifier', None):
            result = await agent._process_step(
                step_text="Test step",
                step_index=0,
                trace_id="test-trace",
                repo="RC918/morningai"
            )

            assert result.task_type == "unknown"
            assert result.status in ["skipped", "blocked", "failed"]

    @pytest.mark.asyncio
    async def test_run_task_with_trace_id_logging(self):
        """Should use trace_id for logging"""
        agent = ProjectEngineerAgent()

        with patch('project_engineer.agent.logger') as mock_logger:
            await agent.run_task("Update README", repo="RC918/morningai")
            assert mock_logger.info.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
