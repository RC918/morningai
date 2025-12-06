"""
Unit tests for State Persistence Security Features

Tests cover:
- Directory permissions (0700)
- Environment variable configuration (META_AGENT_STATE_DIR)
- Permission verification and warnings
- Sensitive data masking in saved state
- set_secure_permissions method

Issue: #1960 - 狀態目錄權限與敏感資料遮罩
Milestone: M5 - Meta Agent 優化
"""

import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from meta_agent.state_persistence import (
    ExecutionStateManager,
    STATE_DIR_ENV_VAR,
    STATE_DIR_PERMISSIONS,
)
from meta_agent.sensitive_data_masker import SensitiveDataMasker


class TestDirectoryPermissions:
    """Tests for directory permission features"""

    def test_state_dir_permissions_constant(self):
        """Test that STATE_DIR_PERMISSIONS is 0700"""
        assert STATE_DIR_PERMISSIONS == 0o700

    def test_state_dir_env_var_constant(self):
        """Test that STATE_DIR_ENV_VAR is correct"""
        assert STATE_DIR_ENV_VAR == "META_AGENT_STATE_DIR"

    def test_new_directory_has_secure_permissions(self):
        """Test that newly created directory has 0700 permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "new_state_dir")
            manager = ExecutionStateManager(storage_dir=state_dir)

            # Check directory was created
            assert os.path.exists(state_dir)

            # Check permissions
            mode = os.stat(state_dir).st_mode
            perms = mode & 0o777
            assert perms == 0o700

    def test_existing_directory_permissions_verified(self):
        """Test that existing directory permissions are verified"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "existing_state_dir")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o755)  # Too permissive

            # Should log a warning but not fail
            with patch("meta_agent.state_persistence.logger") as mock_logger:
                manager = ExecutionStateManager(storage_dir=state_dir)
                # Check that warning was logged
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if "SECURITY WARNING" in str(call)
                ]
                assert len(warning_calls) > 0

    def test_set_secure_permissions(self):
        """Test set_secure_permissions method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "state_dir")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o755)  # Start with permissive

            manager = ExecutionStateManager(storage_dir=state_dir)
            result = manager.set_secure_permissions()

            assert result is True
            mode = os.stat(state_dir).st_mode
            perms = mode & 0o777
            assert perms == 0o700


class TestEnvironmentVariableConfiguration:
    """Tests for environment variable configuration"""

    def test_env_var_takes_precedence(self):
        """Test that META_AGENT_STATE_DIR env var takes precedence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = os.path.join(tmpdir, "env_state_dir")
            param_dir = os.path.join(tmpdir, "param_state_dir")

            with patch.dict(os.environ, {STATE_DIR_ENV_VAR: env_dir}):
                manager = ExecutionStateManager(storage_dir=param_dir)
                assert str(manager.storage_dir) == env_dir

    def test_param_used_when_no_env_var(self):
        """Test that storage_dir param is used when env var not set"""
        with tempfile.TemporaryDirectory() as tmpdir:
            param_dir = os.path.join(tmpdir, "param_state_dir")

            # Ensure env var is not set
            env = os.environ.copy()
            env.pop(STATE_DIR_ENV_VAR, None)

            with patch.dict(os.environ, env, clear=True):
                manager = ExecutionStateManager(storage_dir=param_dir)
                assert str(manager.storage_dir) == param_dir

    def test_default_used_when_nothing_specified(self):
        """Test that default path is used when nothing specified"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change HOME to use temp directory
            default_state_dir = os.path.join(tmpdir, ".meta_agent", "state")

            # Ensure env var is not set
            env = os.environ.copy()
            env.pop(STATE_DIR_ENV_VAR, None)

            with patch.dict(os.environ, env, clear=True):
                with patch("os.path.expanduser", return_value=default_state_dir):
                    manager = ExecutionStateManager()
                    assert str(manager.storage_dir) == default_state_dir


class TestSensitiveDataMaskingInState:
    """Tests for sensitive data masking in saved state"""

    def test_save_state_masks_sensitive_data(self):
        """Test that save_state masks sensitive data when enabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(
                storage_dir=tmpdir,
                mask_sensitive_data=True,
            )

            state = {
                "task_id": "task-123",
                "api_key": "sk-1234567890abcdefghij",
                "password": "supersecretpassword",
                "config": {
                    "token": "ghp_abcdefghijklmnopqrstuvwxyz123456",
                },
            }

            manager.save_state("exec-001", state)

            # Read the saved file directly
            state_path = manager._get_state_path("exec-001")
            with open(state_path, "r") as f:
                saved_data = json.load(f)

            # Check that sensitive data is masked
            saved_state = saved_data["state"]
            assert "sk-1234567890abcdefghij" not in saved_state["api_key"]
            assert "supersecretpassword" not in saved_state["password"]
            assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in str(saved_state)

            # Check metadata indicates masking
            assert saved_data["masked"] is True

    def test_save_state_preserves_data_when_masking_disabled(self):
        """Test that save_state preserves data when masking disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(
                storage_dir=tmpdir,
                mask_sensitive_data=False,
            )

            state = {
                "api_key": "sk-1234567890abcdefghij",
            }

            manager.save_state("exec-002", state)

            # Read the saved file directly
            state_path = manager._get_state_path("exec-002")
            with open(state_path, "r") as f:
                saved_data = json.load(f)

            # Check that data is NOT masked
            saved_state = saved_data["state"]
            assert saved_state["api_key"] == "sk-1234567890abcdefghij"
            assert saved_data["masked"] is False

    def test_custom_masker_can_be_provided(self):
        """Test that a custom masker can be provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_masker = SensitiveDataMasker(mask_char="#", mask_length=6)
            manager = ExecutionStateManager(
                storage_dir=tmpdir,
                masker=custom_masker,
                mask_sensitive_data=True,
            )

            state = {"password": "mysecretpassword"}
            manager.save_state("exec-003", state)

            state_path = manager._get_state_path("exec-003")
            with open(state_path, "r") as f:
                saved_data = json.load(f)

            # Check custom mask character is used
            assert "######" in saved_data["state"]["password"]

    def test_load_state_returns_masked_data(self):
        """Test that load_state returns the masked data as saved"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(
                storage_dir=tmpdir,
                mask_sensitive_data=True,
            )

            original_state = {
                "secret": "verysecretvalue123",
            }

            manager.save_state("exec-004", original_state)
            loaded_state = manager.load_state("exec-004")

            # Loaded state should have masked value
            assert "verysecretvalue123" not in loaded_state["secret"]


class TestStateManagerInitialization:
    """Tests for ExecutionStateManager initialization"""

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_masker = SensitiveDataMasker()
            manager = ExecutionStateManager(
                storage_dir=tmpdir,
                auto_save_interval=60,
                masker=custom_masker,
                mask_sensitive_data=False,
            )

            assert str(manager.storage_dir) == tmpdir
            assert manager.auto_save_interval == 60
            assert manager.masker is custom_masker
            assert manager.mask_sensitive_data is False

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(storage_dir=tmpdir)

            assert manager.auto_save_interval == 30
            assert manager.masker is not None
            assert manager.mask_sensitive_data is True


class TestPermissionVerification:
    """Tests for permission verification logic"""

    def test_no_warning_for_secure_permissions(self):
        """Test no warning is logged for secure permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "secure_dir")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o700)

            with patch("meta_agent.state_persistence.logger") as mock_logger:
                manager = ExecutionStateManager(storage_dir=state_dir)
                # Check that no security warning was logged
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if "SECURITY WARNING" in str(call)
                ]
                assert len(warning_calls) == 0

    def test_warning_for_group_readable(self):
        """Test warning is logged for group-readable directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "group_readable")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o740)  # Group readable

            with patch("meta_agent.state_persistence.logger") as mock_logger:
                manager = ExecutionStateManager(storage_dir=state_dir)
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if "SECURITY WARNING" in str(call)
                ]
                assert len(warning_calls) > 0

    def test_warning_for_world_readable(self):
        """Test warning is logged for world-readable directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "world_readable")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o704)  # World readable

            with patch("meta_agent.state_persistence.logger") as mock_logger:
                manager = ExecutionStateManager(storage_dir=state_dir)
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if "SECURITY WARNING" in str(call)
                ]
                assert len(warning_calls) > 0


class TestTOCTOUDefense:
    """Tests for TOCTOU (Time-of-check to time-of-use) defense in save_state()

    Issue: #2025 - add TOCTOU defense in save_state()
    """

    def test_save_state_verifies_permissions_before_write(self):
        """Test that save_state() calls _verify_directory_permissions() before writing

        This ensures that directory permissions are re-checked on each save,
        defending against TOCTOU attacks where permissions may have changed
        after ExecutionStateManager initialization.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(storage_dir=tmpdir)

            with patch.object(
                manager, "_verify_directory_permissions"
            ) as mock_verify:
                manager.save_state("exec-001", {"status": "running"})
                mock_verify.assert_called_once()

    def test_save_state_warns_if_permissions_changed_after_init(self):
        """Test that save_state() warns if permissions become insecure after init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "state_dir")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o700)  # Start secure

            manager = ExecutionStateManager(storage_dir=state_dir)

            # Change permissions to insecure after initialization
            os.chmod(state_dir, 0o755)

            with patch("meta_agent.state_persistence.logger") as mock_logger:
                manager.save_state("exec-001", {"status": "running"})

                # Should log a security warning
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if "SECURITY WARNING" in str(call)
                ]
                assert len(warning_calls) > 0

    def test_save_state_completes_despite_insecure_permissions(self):
        """Test that save_state() still writes data even with insecure permissions

        The current behavior is to warn but not block writes, maintaining
        backward compatibility while providing visibility into security issues.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, "state_dir")
            os.makedirs(state_dir)
            os.chmod(state_dir, 0o755)  # Insecure from the start

            manager = ExecutionStateManager(storage_dir=state_dir)

            # Should still save successfully
            path = manager.save_state("exec-001", {"status": "running"})
            assert os.path.exists(path)

            # Verify data was written correctly
            loaded = manager.load_state("exec-001")
            assert loaded["status"] == "running"

    def test_multiple_saves_verify_permissions_each_time(self):
        """Test that each save_state() call verifies permissions independently"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExecutionStateManager(storage_dir=tmpdir)

            with patch.object(
                manager, "_verify_directory_permissions"
            ) as mock_verify:
                manager.save_state("exec-001", {"status": "running"})
                manager.save_state("exec-002", {"status": "completed"})
                manager.save_state("exec-003", {"status": "failed"})

                # Should be called once per save
                assert mock_verify.call_count == 3
