"""
Tests for state_persistence module - Save and Restore Execution State for Meta Agent

Issue: #1958 - Meta Agent: 新模組單元測試
"""

import json
import os
import pytest
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from meta_agent.state_persistence import (
    ExecutionStateManager,
    ExecutionCheckpoint,
    create_checkpoint_from_execution,
)


class TestExecutionStateManager:
    """Tests for ExecutionStateManager class"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for state storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def state_manager(self, temp_storage_dir):
        """Create a state manager with temporary storage"""
        return ExecutionStateManager(storage_dir=temp_storage_dir)

    def test_initialization_with_custom_dir(self, temp_storage_dir):
        """Test initialization with custom storage directory"""
        manager = ExecutionStateManager(storage_dir=temp_storage_dir)

        assert manager.storage_dir == Path(temp_storage_dir)
        assert manager.auto_save_interval == 30  # default

    def test_initialization_with_auto_save_interval(self, temp_storage_dir):
        """Test initialization with custom auto_save_interval"""
        manager = ExecutionStateManager(
            storage_dir=temp_storage_dir,
            auto_save_interval=60,
        )

        assert manager.auto_save_interval == 60

    def test_initialization_creates_storage_dir(self, temp_storage_dir):
        """Test that initialization creates storage directory"""
        new_dir = os.path.join(temp_storage_dir, "nested", "state")
        ExecutionStateManager(storage_dir=new_dir)

        assert Path(new_dir).exists()

    def test_save_state(self, state_manager, temp_storage_dir):
        """Test saving execution state"""
        state = {
            "status": "running",
            "tasks_completed": 5,
            "current_task": "task-006",
        }

        path = state_manager.save_state("exec-123", state)

        assert os.path.exists(path)
        with open(path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["execution_id"] == "exec-123"
        assert saved_data["version"] == "1.0"
        assert saved_data["state"] == state
        assert "saved_at" in saved_data

    def test_save_state_overwrites_existing(self, state_manager):
        """Test that save_state overwrites existing state"""
        state1 = {"status": "running", "tasks_completed": 5}
        state2 = {"status": "completed", "tasks_completed": 10}

        state_manager.save_state("exec-123", state1)
        path = state_manager.save_state("exec-123", state2)

        with open(path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["state"]["status"] == "completed"
        assert saved_data["state"]["tasks_completed"] == 10

    def test_save_state_atomic_write(self, state_manager, temp_storage_dir):
        """Test that save_state uses atomic write (temp file)"""
        state = {"status": "running"}

        state_manager.save_state("exec-123", state)

        # Temp file should not exist after successful save
        temp_path = Path(temp_storage_dir) / "exec-123.tmp"
        assert not temp_path.exists()

    def test_load_state_existing(self, state_manager):
        """Test loading existing state"""
        state = {"status": "running", "tasks_completed": 5}
        state_manager.save_state("exec-123", state)

        loaded = state_manager.load_state("exec-123")

        assert loaded == state

    def test_load_state_not_found(self, state_manager):
        """Test loading non-existent state returns None"""
        loaded = state_manager.load_state("non-existent")

        assert loaded is None

    def test_load_state_corrupted_file(self, state_manager, temp_storage_dir):
        """Test loading corrupted state file returns None"""
        # Create a corrupted JSON file
        state_path = Path(temp_storage_dir) / "exec-123.json"
        with open(state_path, "w") as f:
            f.write("not valid json {{{")

        loaded = state_manager.load_state("exec-123")

        assert loaded is None

    def test_delete_state_existing(self, state_manager):
        """Test deleting existing state"""
        state = {"status": "running"}
        state_manager.save_state("exec-123", state)

        result = state_manager.delete_state("exec-123")

        assert result is True
        assert state_manager.load_state("exec-123") is None

    def test_delete_state_not_found(self, state_manager):
        """Test deleting non-existent state returns False"""
        result = state_manager.delete_state("non-existent")

        assert result is False

    def test_list_saved_executions_empty(self, state_manager):
        """Test listing executions when none exist"""
        executions = state_manager.list_saved_executions()

        assert executions == []

    def test_list_saved_executions(self, state_manager, temp_storage_dir):
        """Test listing saved executions"""
        state_manager.save_state("exec-001", {"status": "completed"})
        state_manager.save_state("exec-002", {"status": "running"})
        state_manager.save_state("exec-003", {"status": "failed"})

        # Set different modification times to ensure deterministic ordering
        base_time = time.time()
        os.utime(Path(temp_storage_dir) / "exec-001.json", (base_time - 20, base_time - 20))
        os.utime(Path(temp_storage_dir) / "exec-002.json", (base_time - 10, base_time - 10))
        os.utime(Path(temp_storage_dir) / "exec-003.json", (base_time, base_time))

        executions = state_manager.list_saved_executions()

        assert len(executions) == 3
        # Should be sorted by saved_at descending (most recent first)
        assert executions[0]["execution_id"] == "exec-003"
        assert executions[1]["execution_id"] == "exec-002"
        assert executions[2]["execution_id"] == "exec-001"

    def test_list_saved_executions_metadata(self, state_manager, temp_storage_dir):
        """Test that list_saved_executions returns correct metadata"""
        state_manager.save_state("exec-123", {"status": "running"})

        executions = state_manager.list_saved_executions()

        assert len(executions) == 1
        assert executions[0]["execution_id"] == "exec-123"
        assert "saved_at" in executions[0]
        assert "file_path" in executions[0]
        assert executions[0]["file_path"].endswith("exec-123.json")

    def test_list_saved_executions_skips_invalid_files(self, state_manager, temp_storage_dir):
        """Test that list_saved_executions skips invalid JSON files"""
        state_manager.save_state("exec-valid", {"status": "running"})

        # Create an invalid JSON file
        invalid_path = Path(temp_storage_dir) / "exec-invalid.json"
        with open(invalid_path, "w") as f:
            f.write("not valid json")

        executions = state_manager.list_saved_executions()

        assert len(executions) == 1
        assert executions[0]["execution_id"] == "exec-valid"

    def test_cleanup_old_states_no_old_files(self, state_manager):
        """Test cleanup when no files are old enough"""
        state_manager.save_state("exec-123", {"status": "running"})

        deleted = state_manager.cleanup_old_states(max_age_days=7)

        assert deleted == 0
        assert state_manager.load_state("exec-123") is not None

    def test_cleanup_old_states_with_old_files(self, state_manager, temp_storage_dir):
        """Test cleanup removes old files"""
        state_manager.save_state("exec-old", {"status": "completed"})

        # Manually set file modification time to 10 days ago
        state_path = Path(temp_storage_dir) / "exec-old.json"
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(state_path, (old_time, old_time))

        state_manager.save_state("exec-new", {"status": "running"})

        deleted = state_manager.cleanup_old_states(max_age_days=7)

        assert deleted == 1
        assert state_manager.load_state("exec-old") is None
        assert state_manager.load_state("exec-new") is not None

    def test_cleanup_old_states_custom_max_age(self, state_manager, temp_storage_dir):
        """Test cleanup with custom max_age_days"""
        state_manager.save_state("exec-123", {"status": "completed"})

        # Set file modification time to 2 days ago
        state_path = Path(temp_storage_dir) / "exec-123.json"
        old_time = time.time() - (2 * 24 * 60 * 60)
        os.utime(state_path, (old_time, old_time))

        # With 3 day max age, should not be deleted
        deleted = state_manager.cleanup_old_states(max_age_days=3)
        assert deleted == 0

        # With 1 day max age, should be deleted
        deleted = state_manager.cleanup_old_states(max_age_days=1)
        assert deleted == 1


class TestExecutionCheckpoint:
    """Tests for ExecutionCheckpoint class"""

    def test_checkpoint_creation(self):
        """Test creating an ExecutionCheckpoint"""
        checkpoint = ExecutionCheckpoint(
            execution_id="exec-123",
            plan_id="plan-456",
            status="running",
            current_task_index=3,
            tasks_state=[
                {"task_id": "task-1", "status": "completed"},
                {"task_id": "task-2", "status": "completed"},
                {"task_id": "task-3", "status": "in_progress"},
            ],
            execution_metadata={"tasks_completed": 2},
        )

        assert checkpoint.execution_id == "exec-123"
        assert checkpoint.plan_id == "plan-456"
        assert checkpoint.status == "running"
        assert checkpoint.current_task_index == 3
        assert len(checkpoint.tasks_state) == 3
        assert checkpoint.execution_metadata == {"tasks_completed": 2}
        assert isinstance(checkpoint.created_at, datetime)

    def test_checkpoint_to_dict(self):
        """Test converting checkpoint to dictionary"""
        checkpoint = ExecutionCheckpoint(
            execution_id="exec-123",
            plan_id="plan-456",
            status="running",
            current_task_index=2,
            tasks_state=[{"task_id": "task-1", "status": "completed"}],
            execution_metadata={"tasks_completed": 1},
        )

        result = checkpoint.to_dict()

        assert result["execution_id"] == "exec-123"
        assert result["plan_id"] == "plan-456"
        assert result["status"] == "running"
        assert result["current_task_index"] == 2
        assert result["tasks_state"] == [{"task_id": "task-1", "status": "completed"}]
        assert result["execution_metadata"] == {"tasks_completed": 1}
        assert "created_at" in result

    def test_checkpoint_from_dict(self):
        """Test creating checkpoint from dictionary"""
        data = {
            "execution_id": "exec-123",
            "plan_id": "plan-456",
            "status": "completed",
            "current_task_index": 5,
            "tasks_state": [
                {"task_id": "task-1", "status": "completed"},
                {"task_id": "task-2", "status": "completed"},
            ],
            "execution_metadata": {"tasks_completed": 2, "tasks_failed": 0},
            "created_at": "2025-01-01T12:00:00",
        }

        checkpoint = ExecutionCheckpoint.from_dict(data)

        assert checkpoint.execution_id == "exec-123"
        assert checkpoint.plan_id == "plan-456"
        assert checkpoint.status == "completed"
        assert checkpoint.current_task_index == 5
        assert len(checkpoint.tasks_state) == 2
        assert checkpoint.execution_metadata["tasks_completed"] == 2
        assert checkpoint.created_at == datetime.fromisoformat("2025-01-01T12:00:00")

    def test_checkpoint_from_dict_without_created_at(self):
        """Test creating checkpoint from dictionary without created_at"""
        data = {
            "execution_id": "exec-123",
            "plan_id": "plan-456",
            "status": "running",
            "current_task_index": 0,
            "tasks_state": [],
            "execution_metadata": {},
        }

        checkpoint = ExecutionCheckpoint.from_dict(data)

        # created_at should be set to current time
        assert isinstance(checkpoint.created_at, datetime)

    def test_checkpoint_roundtrip(self):
        """Test checkpoint can be serialized and deserialized"""
        original = ExecutionCheckpoint(
            execution_id="exec-123",
            plan_id="plan-456",
            status="paused",
            current_task_index=3,
            tasks_state=[
                {"task_id": "task-1", "status": "completed"},
                {"task_id": "task-2", "status": "completed"},
                {"task_id": "task-3", "status": "blocked"},
            ],
            execution_metadata={
                "tasks_completed": 2,
                "tasks_failed": 0,
                "started_at": "2025-01-01T10:00:00",
            },
        )

        data = original.to_dict()
        restored = ExecutionCheckpoint.from_dict(data)

        assert restored.execution_id == original.execution_id
        assert restored.plan_id == original.plan_id
        assert restored.status == original.status
        assert restored.current_task_index == original.current_task_index
        assert restored.tasks_state == original.tasks_state
        assert restored.execution_metadata == original.execution_metadata


class TestCreateCheckpointFromExecution:
    """Tests for create_checkpoint_from_execution function"""

    def test_create_checkpoint_basic(self):
        """Test creating checkpoint from execution result and plan"""
        # Create mock execution result
        execution_result = MagicMock()
        execution_result.execution_id = "exec-123"
        execution_result.status = MagicMock()
        execution_result.status.value = "running"
        execution_result.tasks_completed = 2
        execution_result.tasks_failed = 0
        execution_result.tasks_skipped = 0
        execution_result.started_at = datetime(2025, 1, 1, 10, 0, 0)
        execution_result.errors = []

        # Create mock plan
        plan = MagicMock()
        plan.plan_id = "plan-456"
        plan.current_task_index = 2

        # Create mock tasks
        task1 = MagicMock()
        task1.task_id = "task-1"
        task1.status = MagicMock()
        task1.status.value = "completed"
        task1.started_at = datetime(2025, 1, 1, 10, 0, 0)
        task1.completed_at = datetime(2025, 1, 1, 10, 5, 0)
        task1.error = None
        task1.outputs = {"result": "success"}

        task2 = MagicMock()
        task2.task_id = "task-2"
        task2.status = MagicMock()
        task2.status.value = "completed"
        task2.started_at = datetime(2025, 1, 1, 10, 5, 0)
        task2.completed_at = datetime(2025, 1, 1, 10, 10, 0)
        task2.error = None
        task2.outputs = {}

        plan.subtasks = [task1, task2]

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.execution_id == "exec-123"
        assert checkpoint.plan_id == "plan-456"
        assert checkpoint.status == "running"
        assert checkpoint.current_task_index == 2
        assert len(checkpoint.tasks_state) == 2
        assert checkpoint.tasks_state[0]["task_id"] == "task-1"
        assert checkpoint.tasks_state[0]["status"] == "completed"
        assert checkpoint.execution_metadata["tasks_completed"] == 2
        assert checkpoint.execution_metadata["tasks_failed"] == 0

    def test_create_checkpoint_with_failed_task(self):
        """Test creating checkpoint with a failed task"""
        execution_result = MagicMock()
        execution_result.execution_id = "exec-123"
        execution_result.status = MagicMock()
        execution_result.status.value = "failed"
        execution_result.tasks_completed = 1
        execution_result.tasks_failed = 1
        execution_result.tasks_skipped = 0
        execution_result.started_at = datetime(2025, 1, 1, 10, 0, 0)
        execution_result.errors = ["Task task-2 failed: Connection timeout"]

        plan = MagicMock()
        plan.plan_id = "plan-456"
        plan.current_task_index = 2

        task1 = MagicMock()
        task1.task_id = "task-1"
        task1.status = MagicMock()
        task1.status.value = "completed"
        task1.started_at = datetime(2025, 1, 1, 10, 0, 0)
        task1.completed_at = datetime(2025, 1, 1, 10, 5, 0)
        task1.error = None
        task1.outputs = {}

        task2 = MagicMock()
        task2.task_id = "task-2"
        task2.status = MagicMock()
        task2.status.value = "failed"
        task2.started_at = datetime(2025, 1, 1, 10, 5, 0)
        task2.completed_at = datetime(2025, 1, 1, 10, 6, 0)
        task2.error = "Connection timeout"
        task2.outputs = {}

        plan.subtasks = [task1, task2]

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.status == "failed"
        assert checkpoint.tasks_state[1]["status"] == "failed"
        assert checkpoint.tasks_state[1]["error"] == "Connection timeout"
        assert checkpoint.execution_metadata["tasks_failed"] == 1
        assert len(checkpoint.execution_metadata["errors"]) == 1

    def test_create_checkpoint_with_pending_tasks(self):
        """Test creating checkpoint with pending tasks"""
        execution_result = MagicMock()
        execution_result.execution_id = "exec-123"
        execution_result.status = MagicMock()
        execution_result.status.value = "paused"
        execution_result.tasks_completed = 1
        execution_result.tasks_failed = 0
        execution_result.tasks_skipped = 0
        execution_result.started_at = datetime(2025, 1, 1, 10, 0, 0)
        execution_result.errors = []

        plan = MagicMock()
        plan.plan_id = "plan-456"
        plan.current_task_index = 1

        task1 = MagicMock()
        task1.task_id = "task-1"
        task1.status = MagicMock()
        task1.status.value = "completed"
        task1.started_at = datetime(2025, 1, 1, 10, 0, 0)
        task1.completed_at = datetime(2025, 1, 1, 10, 5, 0)
        task1.error = None
        task1.outputs = {}

        task2 = MagicMock()
        task2.task_id = "task-2"
        task2.status = MagicMock()
        task2.status.value = "pending"
        task2.started_at = None
        task2.completed_at = None
        task2.error = None
        task2.outputs = {}

        plan.subtasks = [task1, task2]

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.tasks_state[0]["started_at"] is not None
        assert checkpoint.tasks_state[0]["completed_at"] is not None
        assert checkpoint.tasks_state[1]["started_at"] is None
        assert checkpoint.tasks_state[1]["completed_at"] is None

    def test_create_checkpoint_status_without_value(self):
        """Test creating checkpoint when status doesn't have .value attribute"""
        execution_result = MagicMock()
        execution_result.execution_id = "exec-123"
        execution_result.status = "running"  # String instead of enum
        execution_result.tasks_completed = 0
        execution_result.tasks_failed = 0
        execution_result.tasks_skipped = 0
        execution_result.started_at = None
        execution_result.errors = []

        plan = MagicMock()
        plan.plan_id = "plan-456"
        plan.current_task_index = 0

        task = MagicMock()
        task.task_id = "task-1"
        task.status = "pending"  # String instead of enum
        task.started_at = None
        task.completed_at = None
        task.error = None
        task.outputs = {}

        plan.subtasks = [task]

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.status == "running"
        assert checkpoint.tasks_state[0]["status"] == "pending"


class TestStateManagerIntegration:
    """Integration tests for state persistence"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for state storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_save_and_restore_checkpoint(self, temp_storage_dir):
        """Test saving and restoring a checkpoint through state manager"""
        manager = ExecutionStateManager(storage_dir=temp_storage_dir)

        # Create a checkpoint
        checkpoint = ExecutionCheckpoint(
            execution_id="exec-123",
            plan_id="plan-456",
            status="paused",
            current_task_index=3,
            tasks_state=[
                {"task_id": "task-1", "status": "completed"},
                {"task_id": "task-2", "status": "completed"},
                {"task_id": "task-3", "status": "in_progress"},
            ],
            execution_metadata={"tasks_completed": 2},
        )

        # Save checkpoint
        manager.save_state(checkpoint.execution_id, checkpoint.to_dict())

        # Restore checkpoint
        loaded_data = manager.load_state("exec-123")
        restored = ExecutionCheckpoint.from_dict(loaded_data)

        assert restored.execution_id == checkpoint.execution_id
        assert restored.plan_id == checkpoint.plan_id
        assert restored.status == checkpoint.status
        assert restored.current_task_index == checkpoint.current_task_index
        assert restored.tasks_state == checkpoint.tasks_state

    def test_multiple_executions_lifecycle(self, temp_storage_dir):
        """Test managing multiple execution states"""
        manager = ExecutionStateManager(storage_dir=temp_storage_dir)

        # Save multiple executions
        for i in range(5):
            manager.save_state(f"exec-{i}", {"status": "running", "index": i})
            time.sleep(0.01)

        # List all
        executions = manager.list_saved_executions()
        assert len(executions) == 5

        # Delete some
        manager.delete_state("exec-0")
        manager.delete_state("exec-2")

        # Verify remaining
        executions = manager.list_saved_executions()
        assert len(executions) == 3

        remaining_ids = [e["execution_id"] for e in executions]
        assert "exec-0" not in remaining_ids
        assert "exec-2" not in remaining_ids
        assert "exec-1" in remaining_ids
        assert "exec-3" in remaining_ids
        assert "exec-4" in remaining_ids


class TestCreateCheckpointWithRealTypes:
    """Tests for create_checkpoint_from_execution using real types instead of MagicMock"""

    def test_create_checkpoint_with_real_task_plan(self):
        """Test creating checkpoint using real TaskPlan and SubTask objects"""
        from datetime import datetime
        from meta_agent.task_planner import TaskPlan, SubTask, SubTaskType, SubTaskStatus
        from meta_agent.autonomous_executor import ExecutionResult, ExecutionStatus

        subtasks = [
            SubTask(
                task_id="task-1",
                task_type=SubTaskType.WRITE_CODE,
                description="Implement feature",
                status=SubTaskStatus.COMPLETED,
                started_at=datetime(2025, 1, 1, 10, 0, 0),
                completed_at=datetime(2025, 1, 1, 10, 5, 0),
                outputs={"files_modified": ["src/main.py"]},
            ),
            SubTask(
                task_id="task-2",
                task_type=SubTaskType.RUN_TEST,
                description="Run tests",
                status=SubTaskStatus.PENDING,
            ),
        ]

        dummy_goal = MagicMock()
        plan = TaskPlan(
            plan_id="plan-real-123",
            goal=dummy_goal,
            subtasks=subtasks,
            total_estimated_minutes=15,
            current_task_index=1,
        )

        execution_result = ExecutionResult(
            execution_id="exec-real-123",
            plan_id="plan-real-123",
            status=ExecutionStatus.RUNNING,
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            tasks_completed=1,
            tasks_failed=0,
            tasks_skipped=0,
            errors=[],
        )

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.execution_id == "exec-real-123"
        assert checkpoint.plan_id == "plan-real-123"
        assert checkpoint.status == "running"
        assert checkpoint.current_task_index == 1
        assert len(checkpoint.tasks_state) == 2

        assert checkpoint.tasks_state[0]["task_id"] == "task-1"
        assert checkpoint.tasks_state[0]["status"] == "completed"
        assert checkpoint.tasks_state[0]["started_at"] == "2025-01-01T10:00:00"
        assert checkpoint.tasks_state[0]["completed_at"] == "2025-01-01T10:05:00"
        assert checkpoint.tasks_state[0]["outputs"] == {"files_modified": ["src/main.py"]}

        assert checkpoint.tasks_state[1]["task_id"] == "task-2"
        assert checkpoint.tasks_state[1]["status"] == "pending"
        assert checkpoint.tasks_state[1]["started_at"] is None

        assert checkpoint.execution_metadata["tasks_completed"] == 1
        assert checkpoint.execution_metadata["tasks_failed"] == 0

    def test_create_checkpoint_with_real_failed_execution(self):
        """Test creating checkpoint with real types when execution has failed"""
        from datetime import datetime
        from meta_agent.task_planner import TaskPlan, SubTask, SubTaskType, SubTaskStatus
        from meta_agent.autonomous_executor import ExecutionResult, ExecutionStatus

        subtasks = [
            SubTask(
                task_id="task-1",
                task_type=SubTaskType.ANALYZE_CODE,
                description="Analyze code",
                status=SubTaskStatus.COMPLETED,
                started_at=datetime(2025, 1, 1, 10, 0, 0),
                completed_at=datetime(2025, 1, 1, 10, 3, 0),
            ),
            SubTask(
                task_id="task-2",
                task_type=SubTaskType.WRITE_CODE,
                description="Write code",
                status=SubTaskStatus.FAILED,
                started_at=datetime(2025, 1, 1, 10, 3, 0),
                completed_at=datetime(2025, 1, 1, 10, 4, 0),
                error="Syntax error in generated code",
            ),
        ]

        dummy_goal = MagicMock()
        plan = TaskPlan(
            plan_id="plan-fail-123",
            goal=dummy_goal,
            subtasks=subtasks,
            total_estimated_minutes=10,
            current_task_index=2,
        )

        execution_result = ExecutionResult(
            execution_id="exec-fail-123",
            plan_id="plan-fail-123",
            status=ExecutionStatus.FAILED,
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            tasks_completed=1,
            tasks_failed=1,
            tasks_skipped=0,
            errors=["Task task-2 failed: Syntax error in generated code"],
        )

        checkpoint = create_checkpoint_from_execution(execution_result, plan)

        assert checkpoint.status == "failed"
        assert checkpoint.tasks_state[1]["status"] == "failed"
        assert checkpoint.tasks_state[1]["error"] == "Syntax error in generated code"
        assert checkpoint.execution_metadata["tasks_failed"] == 1
        assert len(checkpoint.execution_metadata["errors"]) == 1


class TestListSavedExecutionsDeterministic:
    """Tests for list_saved_executions with deterministic timestamps (no time.sleep)"""

    @pytest.fixture
    def temp_storage_dir(self):
        """Create a temporary directory for state storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_list_saved_executions_sorted_by_saved_at(self, temp_storage_dir):
        """Test that list_saved_executions sorts by saved_at using manual JSON files"""
        exec1_data = {
            "execution_id": "exec-001",
            "saved_at": "2025-01-01T10:00:00",
            "version": "1.0",
            "state": {"status": "completed"},
        }
        exec2_data = {
            "execution_id": "exec-002",
            "saved_at": "2025-01-02T10:00:00",
            "version": "1.0",
            "state": {"status": "running"},
        }
        exec3_data = {
            "execution_id": "exec-003",
            "saved_at": "2025-01-03T10:00:00",
            "version": "1.0",
            "state": {"status": "failed"},
        }

        for data in [exec1_data, exec2_data, exec3_data]:
            path = Path(temp_storage_dir) / f"{data['execution_id']}.json"
            with open(path, "w") as f:
                json.dump(data, f)

        manager = ExecutionStateManager(storage_dir=temp_storage_dir)
        executions = manager.list_saved_executions()

        assert len(executions) == 3
        assert executions[0]["execution_id"] == "exec-003"
        assert executions[1]["execution_id"] == "exec-002"
        assert executions[2]["execution_id"] == "exec-001"

    def test_list_saved_executions_handles_same_timestamp(self, temp_storage_dir):
        """Test list_saved_executions when multiple files have same timestamp"""
        same_time = "2025-01-01T12:00:00"
        for i in range(3):
            data = {
                "execution_id": f"exec-{i:03d}",
                "saved_at": same_time,
                "version": "1.0",
                "state": {"status": "completed"},
            }
            path = Path(temp_storage_dir) / f"exec-{i:03d}.json"
            with open(path, "w") as f:
                json.dump(data, f)

        manager = ExecutionStateManager(storage_dir=temp_storage_dir)
        executions = manager.list_saved_executions()

        assert len(executions) == 3
        execution_ids = {e["execution_id"] for e in executions}
        assert execution_ids == {"exec-000", "exec-001", "exec-002"}


class TestDefaultStorageDirectory:
    """Tests for default storage directory behavior (~/.meta_agent/state)"""

    def test_default_path_uses_home_directory(self, monkeypatch, tmp_path):
        """Test that default storage_dir uses expanduser for home directory"""
        fake_home_state = str(tmp_path / ".meta_agent" / "state")

        def mock_expanduser(path):
            if path == "~/.meta_agent/state":
                return fake_home_state
            return path

        monkeypatch.setattr("meta_agent.state_persistence.os.path.expanduser", mock_expanduser)

        manager = ExecutionStateManager()

        assert manager.storage_dir == Path(fake_home_state)
        assert manager.storage_dir.exists()

    def test_explicit_storage_dir_overrides_default(self, tmp_path):
        """Test that explicit storage_dir parameter overrides default"""
        custom_dir = tmp_path / "custom_state"

        manager = ExecutionStateManager(storage_dir=str(custom_dir))

        assert manager.storage_dir == custom_dir
        assert manager.storage_dir.exists()

    def test_explicit_storage_dir_with_nested_path(self, tmp_path):
        """Test that explicit storage_dir creates nested directories"""
        nested_dir = tmp_path / "deeply" / "nested" / "state" / "dir"

        manager = ExecutionStateManager(storage_dir=str(nested_dir))

        assert manager.storage_dir == nested_dir
        assert manager.storage_dir.exists()

    def test_storage_dir_isolation_between_instances(self, tmp_path):
        """Test that different instances with different dirs are isolated"""
        dir1 = tmp_path / "state1"
        dir2 = tmp_path / "state2"

        manager1 = ExecutionStateManager(storage_dir=str(dir1))
        manager2 = ExecutionStateManager(storage_dir=str(dir2))

        manager1.save_state("exec-1", {"from": "manager1"})
        manager2.save_state("exec-2", {"from": "manager2"})

        assert manager1.load_state("exec-1") == {"from": "manager1"}
        assert manager1.load_state("exec-2") is None

        assert manager2.load_state("exec-2") == {"from": "manager2"}
        assert manager2.load_state("exec-1") is None
