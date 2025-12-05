"""
State Persistence - Save and Restore Execution State for Meta Agent

This module provides state persistence capabilities for long-running execution plans,
allowing recovery from interruptions and resumption of paused executions.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionStateManager:
    """
    Manages persistence of execution state for recovery and resumption.

    Supports saving execution state to disk and restoring it later,
    enabling recovery from crashes or intentional pauses.
    """

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        auto_save_interval: int = 30,
    ):
        """
        Initialize the ExecutionStateManager.

        Args:
            storage_dir: Directory to store state files. Defaults to ~/.meta_agent/state
            auto_save_interval: Seconds between auto-saves (0 to disable)
        """
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.meta_agent/state"))
        self.auto_save_interval = auto_save_interval
        self._ensure_storage_dir()

        logger.info(
            "[StateManager] Initialized with storage_dir=%s, auto_save=%ds",
            self.storage_dir, auto_save_interval)

    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

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

        Args:
            execution_id: Unique execution identifier
            state: State dictionary to save

        Returns:
            Path to saved state file
        """
        state_path = self._get_state_path(execution_id)

        # Add metadata
        state_with_meta = {
            "execution_id": execution_id,
            "saved_at": datetime.now().isoformat(),
            "version": "1.0",
            "state": state,
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
