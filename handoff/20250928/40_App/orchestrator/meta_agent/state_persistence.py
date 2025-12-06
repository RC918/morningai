"""
State Persistence - Save and Restore Execution State for Meta Agent

This module provides state persistence capabilities for long-running execution plans,
allowing recovery from interruptions and resumption of paused executions.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Issue: #1960 - 狀態目錄權限與敏感資料遮罩
Milestone: M5 - Meta Agent 優化
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .sensitive_data_masker import SensitiveDataMasker, get_masker

logger = logging.getLogger(__name__)

# Directory permission constants
STATE_DIR_PERMISSIONS = 0o700  # Owner read/write/execute only
STATE_DIR_ENV_VAR = "META_AGENT_STATE_DIR"


class ExecutionStateManager:
    """
    Manages persistence of execution state for recovery and resumption.

    Supports saving execution state to disk and restoring it later,
    enabling recovery from crashes or intentional pauses.

    Security features (#1960):
    - Directory permissions set to 0700 (owner only)
    - Sensitive data masking in saved state
    - Environment variable support for state directory
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        auto_save_interval: int = 30,
        masker: Optional[SensitiveDataMasker] = None,
        mask_sensitive_data: bool = True,
    ):
        """
        Initialize the ExecutionStateManager.

        Args:
            storage_dir: Directory to store state files.
                        Defaults to META_AGENT_STATE_DIR env var or ~/.meta_agent/state
            auto_save_interval: Seconds between auto-saves (0 to disable)
            masker: Optional SensitiveDataMasker instance for masking sensitive data
            mask_sensitive_data: Whether to mask sensitive data in saved state
        """
        # Check environment variable first, then fallback to parameter or default
        env_dir = os.environ.get(STATE_DIR_ENV_VAR)
        if env_dir:
            self.storage_dir = Path(env_dir)
        elif storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(os.path.expanduser("~/.meta_agent/state"))

        self.auto_save_interval = auto_save_interval
        self.masker = masker or get_masker()
        self.mask_sensitive_data = mask_sensitive_data
        self._ensure_storage_dir()

        logger.info(
            "[StateManager] Initialized with storage_dir=%s, auto_save=%ds, masking=%s",
            self.storage_dir, auto_save_interval, mask_sensitive_data)

    def _ensure_storage_dir(self) -> None:
        """
        Ensure storage directory exists with secure permissions.

        Creates the directory if it doesn't exist and sets permissions to 0700
        (owner read/write/execute only). Warns if existing directory has
        permissions that are too permissive.
        """
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            # Set secure permissions on new directory
            self.storage_dir.chmod(STATE_DIR_PERMISSIONS)
            logger.info(
                "[StateManager] Created state directory with permissions 0700: %s",
                self.storage_dir)
        else:
            # Verify existing directory permissions
            self._verify_directory_permissions()

    def _verify_directory_permissions(self) -> None:
        """
        Verify that directory permissions are secure.

        Warns if permissions are more permissive than 0700.
        """
        try:
            current_mode = self.storage_dir.stat().st_mode
            # Extract permission bits (last 9 bits)
            current_perms = current_mode & 0o777

            if current_perms != STATE_DIR_PERMISSIONS:
                # Check if group or others have any access
                group_perms = (current_perms >> 3) & 0o7
                other_perms = current_perms & 0o7

                if group_perms > 0 or other_perms > 0:
                    logger.warning(
                        "[StateManager] SECURITY WARNING: State directory %s has "
                        "permissive permissions (0%o). Recommended: 0700. "
                        "Run 'chmod 700 %s' to fix.",
                        self.storage_dir, current_perms, self.storage_dir)
        except OSError as e:
            logger.warning(
                "[StateManager] Could not verify directory permissions: %s", e)

    def set_secure_permissions(self) -> bool:
        """
        Set secure permissions (0700) on the state directory.

        Returns:
            True if permissions were set successfully, False otherwise
        """
        try:
            self.storage_dir.chmod(STATE_DIR_PERMISSIONS)
            logger.info(
                "[StateManager] Set secure permissions (0700) on %s",
                self.storage_dir)
            return True
        except OSError as e:
            logger.error(
                "[StateManager] Failed to set directory permissions: %s", e)
            return False

    def _get_state_path(self, execution_id: str) -> Path:
        """Get path for execution state file"""
        return self.storage_dir / f"{execution_id}.json"

    def save_state(
        self,
        execution_id: str,
        state: Dict[str, Any],
    ) -> str:
        """
        Save execution state to disk.

        Sensitive data is automatically masked if mask_sensitive_data is enabled.

        Args:
            execution_id: Unique execution identifier
            state: State dictionary to save

        Returns:
            Path to saved state file
        """
        state_path = self._get_state_path(execution_id)

        # Mask sensitive data if enabled
        state_to_save = state
        if self.mask_sensitive_data:
            state_to_save = self.masker.mask_dict(state)

        # Add metadata
        state_with_meta = {
            "execution_id": execution_id,
            "saved_at": datetime.now().isoformat(),
            "version": "1.0",
            "masked": self.mask_sensitive_data,
            "state": state_to_save,
        }

        # Write atomically using temp file
        temp_path = state_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(state_with_meta, f, indent=2, default=str)
            temp_path.rename(state_path)

            logger.info("[StateManager] Saved state for execution %s", execution_id)
            return str(state_path)

        except Exception as e:
            logger.error("[StateManager] Failed to save state: %s", e)
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Load execution state from disk.

        Args:
            execution_id: Unique execution identifier

        Returns:
            State dictionary or None if not found
        """
        state_path = self._get_state_path(execution_id)

        if not state_path.exists():
            logger.warning("[StateManager] No state found for execution %s", execution_id)
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            logger.info(
                "[StateManager] Loaded state for execution %s (saved at %s)",
                execution_id, data.get("saved_at"))

            return data.get("state")

        except Exception as e:
            logger.error("[StateManager] Failed to load state: %s", e)
            return None

    def delete_state(self, execution_id: str) -> bool:
        """
        Delete execution state from disk.

        Args:
            execution_id: Unique execution identifier

        Returns:
            True if deleted, False if not found
        """
        state_path = self._get_state_path(execution_id)

        if not state_path.exists():
            return False

        try:
            state_path.unlink()
            logger.info("[StateManager] Deleted state for execution %s", execution_id)
            return True

        except Exception as e:
            logger.error("[StateManager] Failed to delete state: %s", e)
            return False

    def list_saved_executions(self) -> List[Dict[str, Any]]:
        """
        List all saved execution states.

        Returns:
            List of execution metadata dictionaries
        """
        executions = []

        for state_file in self.storage_dir.glob("*.json"):
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                executions.append({
                    "execution_id": data.get("execution_id"),
                    "saved_at": data.get("saved_at"),
                    "file_path": str(state_file),
                })

            except Exception as e:
                logger.warning("[StateManager] Failed to read %s: %s", state_file, e)

        return sorted(executions, key=lambda x: x.get("saved_at", ""), reverse=True)

    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """
        Clean up old state files.

        Args:
            max_age_days: Maximum age in days for state files

        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for state_file in self.storage_dir.glob("*.json"):
            if state_file.stat().st_mtime < cutoff:
                try:
                    state_file.unlink()
                    deleted += 1
                    logger.info("[StateManager] Cleaned up old state: %s", state_file.name)
                except Exception as e:
                    logger.warning("[StateManager] Failed to delete %s: %s", state_file, e)

        return deleted


class ExecutionCheckpoint:
    """
    Represents a checkpoint in execution that can be saved and restored.

    Checkpoints capture the complete state of an execution at a point in time,
    including the plan, task states, and execution metadata.
    """

    def __init__(
        self,
        execution_id: str,
        plan_id: str,
        status: str,
        current_task_index: int,
        tasks_state: List[Dict[str, Any]],
        execution_metadata: Dict[str, Any],
    ):
        self.execution_id = execution_id
        self.plan_id = plan_id
        self.status = status
        self.current_task_index = current_task_index
        self.tasks_state = tasks_state
        self.execution_metadata = execution_metadata
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary"""
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "current_task_index": self.current_task_index,
            "tasks_state": self.tasks_state,
            "execution_metadata": self.execution_metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionCheckpoint":
        """Create checkpoint from dictionary"""
        checkpoint = cls(
            execution_id=data["execution_id"],
            plan_id=data["plan_id"],
            status=data["status"],
            current_task_index=data["current_task_index"],
            tasks_state=data["tasks_state"],
            execution_metadata=data["execution_metadata"],
        )
        if "created_at" in data:
            checkpoint.created_at = datetime.fromisoformat(data["created_at"])
        return checkpoint


def create_checkpoint_from_execution(
    execution_result: Any,
    plan: Any,
) -> ExecutionCheckpoint:
    """
    Create a checkpoint from current execution state.

    Args:
        execution_result: Current ExecutionResult
        plan: Current TaskPlan

    Returns:
        ExecutionCheckpoint capturing current state
    """
    tasks_state = []
    for task in plan.subtasks:
        task_state = {
            "task_id": task.task_id,
            "status": task.status.value if hasattr(task.status, "value") else str(task.status),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error,
            "outputs": task.outputs if hasattr(task, "outputs") else {},
        }
        tasks_state.append(task_state)

    return ExecutionCheckpoint(
        execution_id=execution_result.execution_id,
        plan_id=plan.plan_id,
        status=execution_result.status.value if hasattr(execution_result.status, "value") else str(execution_result.status),
        current_task_index=plan.current_task_index,
        tasks_state=tasks_state,
        execution_metadata={
            "tasks_completed": execution_result.tasks_completed,
            "tasks_failed": execution_result.tasks_failed,
            "tasks_skipped": execution_result.tasks_skipped,
            "started_at": execution_result.started_at.isoformat() if execution_result.started_at else None,
            "errors": execution_result.errors,
        },
    )
