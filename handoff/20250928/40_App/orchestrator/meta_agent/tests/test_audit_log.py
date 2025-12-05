"""
Tests for audit_log module - Structured Event Logging for Meta Agent

Issue: #1958 - Meta Agent: 新模組單元測試
"""

import json
from datetime import datetime
from unittest.mock import MagicMock

from meta_agent.audit_log import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
)

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2025, 1, 1, 12, 0, 0)


class TestAuditEventType:
    """Tests for AuditEventType enum"""

    def test_all_event_types_exist(self):
        """Verify all expected event types are defined"""
        expected_types = {
            "EXECUTION_STARTED",
            "EXECUTION_COMPLETED",
            "EXECUTION_FAILED",
            "EXECUTION_CANCELLED",
            "EXECUTION_PAUSED",
            "EXECUTION_RESUMED",
            "TASK_STARTED",
            "TASK_COMPLETED",
            "TASK_FAILED",
            "TASK_SKIPPED",
            "TASK_RETRIED",
            "APPROVAL_REQUESTED",
            "APPROVAL_GRANTED",
            "APPROVAL_DENIED",
            "APPROVAL_TIMEOUT",
            "POLICY_VIOLATION",
            "SAFETY_LIMIT_REACHED",
            "HIGH_RISK_OPERATION",
            "OPERATION_BLOCKED",
        }
        actual_types = {member.name for member in AuditEventType}
        assert actual_types == expected_types

    def test_event_type_values(self):
        """Verify event type values are lowercase strings"""
        assert AuditEventType.EXECUTION_STARTED.value == "execution_started"
        assert AuditEventType.TASK_COMPLETED.value == "task_completed"
        assert AuditEventType.APPROVAL_GRANTED.value == "approval_granted"


class TestAuditEvent:
    """Tests for AuditEvent dataclass"""

    def test_audit_event_creation(self):
        """Test creating an AuditEvent"""
        event = AuditEvent(
            event_id="test-evt-0001",
            event_type=AuditEventType.EXECUTION_STARTED,
            timestamp=FIXED_TIMESTAMP,
            execution_id="exec-123",
            actor="test_user",
            action="start_execution",
        )
        assert event.event_id == "test-evt-0001"
        assert event.event_type == AuditEventType.EXECUTION_STARTED
        assert event.execution_id == "exec-123"
        assert event.actor == "test_user"
        assert event.action == "start_execution"

    def test_audit_event_optional_fields(self):
        """Test AuditEvent with optional fields"""
        event = AuditEvent(
            event_id="test-evt-0001",
            event_type=AuditEventType.TASK_STARTED,
            timestamp=FIXED_TIMESTAMP,
            execution_id="exec-123",
            task_id="task-456",
            resource="/path/to/file",
            details={"key": "value"},
            metadata={"version": "1.0"},
        )
        assert event.task_id == "task-456"
        assert event.resource == "/path/to/file"
        assert event.details == {"key": "value"}
        assert event.metadata == {"version": "1.0"}

    def test_audit_event_to_dict(self):
        """Test converting AuditEvent to dictionary"""
        event = AuditEvent(
            event_id="test-evt-0001",
            event_type=AuditEventType.EXECUTION_STARTED,
            timestamp=FIXED_TIMESTAMP,
            execution_id="exec-123",
            actor="test_user",
            action="start_execution",
            details={"goal": "test goal"},
        )
        result = event.to_dict()

        assert result["event_id"] == "test-evt-0001"
        assert result["event_type"] == "execution_started"
        assert result["timestamp"] == FIXED_TIMESTAMP.isoformat()
        assert result["execution_id"] == "exec-123"
        assert result["actor"] == "test_user"
        assert result["action"] == "start_execution"
        assert result["details"] == {"goal": "test goal"}

    def test_audit_event_to_json(self):
        """Test converting AuditEvent to JSON string"""
        event = AuditEvent(
            event_id="test-evt-0001",
            event_type=AuditEventType.EXECUTION_STARTED,
            timestamp=FIXED_TIMESTAMP,
            execution_id="exec-123",
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_id"] == "test-evt-0001"
        assert parsed["event_type"] == "execution_started"
        assert parsed["execution_id"] == "exec-123"


class TestAuditLogger:
    """Tests for AuditLogger class"""

    def test_audit_logger_initialization(self):
        """Test AuditLogger initialization"""
        logger = AuditLogger(execution_id="exec-123", actor="test_user")

        assert logger.execution_id == "exec-123"
        assert logger.actor == "test_user"
        assert logger.events == []
        assert logger.handlers == []

    def test_audit_logger_default_actor(self):
        """Test AuditLogger uses 'system' as default actor"""
        logger = AuditLogger(execution_id="exec-123")
        assert logger.actor == "system"

    def test_audit_logger_with_handlers(self):
        """Test AuditLogger with custom handlers"""
        handler = MagicMock()
        logger = AuditLogger(
            execution_id="exec-123",
            handlers=[handler],
        )

        logger.log_execution_started(
            goal_text="Test goal",
            plan_id="plan-123",
            task_count=5,
        )

        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert isinstance(call_args, AuditEvent)
        assert call_args.event_type == AuditEventType.EXECUTION_STARTED

    def test_handler_exception_does_not_propagate(self):
        """Test that handler exceptions are caught and logged"""
        def failing_handler(event):
            raise ValueError("Handler error")

        logger = AuditLogger(
            execution_id="exec-123",
            handlers=[failing_handler],
        )

        # Should not raise
        event = logger.log_execution_started(
            goal_text="Test goal",
            plan_id="plan-123",
            task_count=5,
        )
        assert event is not None

    def test_generate_event_id(self):
        """Test event ID generation"""
        logger = AuditLogger(execution_id="exec-123")

        event1 = logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-1",
            task_count=1,
        )
        event2 = logger.log_execution_completed(
            status="completed",
            tasks_completed=1,
            tasks_failed=0,
            duration_seconds=10.0,
        )

        assert event1.event_id == "exec-123-evt-0001"
        assert event2.event_id == "exec-123-evt-0002"

    def test_log_execution_started(self):
        """Test logging execution started event"""
        logger = AuditLogger(execution_id="exec-123", actor="meta_agent")

        event = logger.log_execution_started(
            goal_text="Implement new feature",
            plan_id="plan-456",
            task_count=10,
            extra_field="extra_value",
        )

        assert event.event_type == AuditEventType.EXECUTION_STARTED
        assert event.action == "start_execution"
        assert event.details["goal_text"] == "Implement new feature"
        assert event.details["plan_id"] == "plan-456"
        assert event.details["task_count"] == 10
        assert event.details["extra_field"] == "extra_value"
        assert len(logger.events) == 1

    def test_log_execution_started_truncates_long_goal(self):
        """Test that long goal text is truncated"""
        logger = AuditLogger(execution_id="exec-123")
        long_goal = "x" * 500

        event = logger.log_execution_started(
            goal_text=long_goal,
            plan_id="plan-123",
            task_count=1,
        )

        assert len(event.details["goal_text"]) == 200

    def test_log_execution_completed(self):
        """Test logging execution completed event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_execution_completed(
            status="completed",
            tasks_completed=8,
            tasks_failed=2,
            duration_seconds=120.5,
        )

        assert event.event_type == AuditEventType.EXECUTION_COMPLETED
        assert event.action == "complete_execution"
        assert event.details["status"] == "completed"
        assert event.details["tasks_completed"] == 8
        assert event.details["tasks_failed"] == 2
        assert event.details["duration_seconds"] == 120.5

    def test_log_execution_failed(self):
        """Test logging execution failed event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_execution_failed(
            error="Connection timeout",
        )

        assert event.event_type == AuditEventType.EXECUTION_FAILED
        assert event.action == "fail_execution"
        assert event.details["error"] == "Connection timeout"

    def test_log_execution_failed_truncates_long_error(self):
        """Test that long error messages are truncated"""
        logger = AuditLogger(execution_id="exec-123")
        long_error = "e" * 1000

        event = logger.log_execution_failed(error=long_error)

        assert len(event.details["error"]) == 500

    def test_log_task_started(self):
        """Test logging task started event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_task_started(
            task_id="task-001",
            task_type="write_code",
            description="Write unit tests for module",
        )

        assert event.event_type == AuditEventType.TASK_STARTED
        assert event.task_id == "task-001"
        assert event.action == "start_task"
        assert event.details["task_type"] == "write_code"
        assert event.details["description"] == "Write unit tests for module"

    def test_log_task_completed(self):
        """Test logging task completed event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_task_completed(
            task_id="task-001",
            duration_seconds=45.2,
            outputs={"files_created": ["test.py"]},
        )

        assert event.event_type == AuditEventType.TASK_COMPLETED
        assert event.task_id == "task-001"
        assert event.action == "complete_task"
        assert event.details["duration_seconds"] == 45.2
        assert event.details["outputs_keys"] == ["files_created"]

    def test_log_task_completed_without_outputs(self):
        """Test logging task completed without outputs"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_task_completed(
            task_id="task-001",
            duration_seconds=10.0,
        )

        assert event.details["outputs_keys"] == []

    def test_log_task_failed(self):
        """Test logging task failed event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_task_failed(
            task_id="task-001",
            error="File not found",
            attempt=3,
        )

        assert event.event_type == AuditEventType.TASK_FAILED
        assert event.task_id == "task-001"
        assert event.action == "fail_task"
        assert event.details["error"] == "File not found"
        assert event.details["attempt"] == 3

    def test_log_approval_requested(self):
        """Test logging approval requested event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_approval_requested(
            task_id="task-001",
            operation="deploy_production",
            resource="api-server",
            reason="High-risk deployment",
        )

        assert event.event_type == AuditEventType.APPROVAL_REQUESTED
        assert event.task_id == "task-001"
        assert event.action == "request_approval"
        assert event.resource == "api-server"
        assert event.details["operation"] == "deploy_production"
        assert event.details["reason"] == "High-risk deployment"

    def test_log_approval_granted(self):
        """Test logging approval granted event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_approval_granted(
            task_id="task-001",
            approver="admin_user",
            operation="deploy_production",
        )

        assert event.event_type == AuditEventType.APPROVAL_GRANTED
        assert event.task_id == "task-001"
        assert event.actor == "admin_user"
        assert event.action == "grant_approval"
        assert event.details["operation"] == "deploy_production"

    def test_log_approval_denied(self):
        """Test logging approval denied event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_approval_denied(
            task_id="task-001",
            denier="security_team",
            operation="deploy_production",
            reason="Security review pending",
        )

        assert event.event_type == AuditEventType.APPROVAL_DENIED
        assert event.task_id == "task-001"
        assert event.actor == "security_team"
        assert event.action == "deny_approval"
        assert event.details["operation"] == "deploy_production"
        assert event.details["reason"] == "Security review pending"

    def test_log_policy_violation(self):
        """Test logging policy violation event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_policy_violation(
            violation_type="operation_not_allowed",
            details="Attempted to delete production database",
        )

        assert event.event_type == AuditEventType.POLICY_VIOLATION
        assert event.action == "policy_violation"
        assert event.details["violation_type"] == "operation_not_allowed"
        assert event.details["details"] == "Attempted to delete production database"

    def test_log_safety_limit_reached(self):
        """Test logging safety limit reached event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_safety_limit_reached(
            limit_type="max_loop_iterations",
            limit_value=1000,
            current_value=1001,
        )

        assert event.event_type == AuditEventType.SAFETY_LIMIT_REACHED
        assert event.action == "safety_limit_reached"
        assert event.details["limit_type"] == "max_loop_iterations"
        assert event.details["limit_value"] == 1000
        assert event.details["current_value"] == 1001

    def test_log_high_risk_operation(self):
        """Test logging high risk operation event"""
        logger = AuditLogger(execution_id="exec-123")

        event = logger.log_high_risk_operation(
            task_id="task-001",
            operation="database_migration",
            resource="users_table",
            risk_level="high",
        )

        assert event.event_type == AuditEventType.HIGH_RISK_OPERATION
        assert event.task_id == "task-001"
        assert event.action == "high_risk_operation"
        assert event.resource == "users_table"
        assert event.details["operation"] == "database_migration"
        assert event.details["risk_level"] == "high"

    def test_get_events_all(self):
        """Test getting all events"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-1",
            task_count=2,
        )
        logger.log_task_started(
            task_id="task-1",
            task_type="analyze",
            description="Analyze code",
        )
        logger.log_task_completed(
            task_id="task-1",
            duration_seconds=10.0,
        )

        events = logger.get_events()
        assert len(events) == 3

    def test_get_events_by_type(self):
        """Test filtering events by type"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-1",
            task_count=2,
        )
        logger.log_task_started(
            task_id="task-1",
            task_type="analyze",
            description="Analyze code",
        )
        logger.log_task_completed(
            task_id="task-1",
            duration_seconds=10.0,
        )

        task_events = logger.get_events(event_type=AuditEventType.TASK_STARTED)
        assert len(task_events) == 1
        assert task_events[0].event_type == AuditEventType.TASK_STARTED

    def test_get_events_by_task_id(self):
        """Test filtering events by task ID"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_task_started(
            task_id="task-1",
            task_type="analyze",
            description="Analyze code",
        )
        logger.log_task_started(
            task_id="task-2",
            task_type="write",
            description="Write code",
        )
        logger.log_task_completed(
            task_id="task-1",
            duration_seconds=10.0,
        )

        task1_events = logger.get_events(task_id="task-1")
        assert len(task1_events) == 2
        for event in task1_events:
            assert event.task_id == "task-1"

    def test_get_events_combined_filters(self):
        """Test filtering events with multiple filters"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_task_started(
            task_id="task-1",
            task_type="analyze",
            description="Analyze code",
        )
        logger.log_task_completed(
            task_id="task-1",
            duration_seconds=10.0,
        )
        logger.log_task_started(
            task_id="task-2",
            task_type="write",
            description="Write code",
        )

        events = logger.get_events(
            event_type=AuditEventType.TASK_STARTED,
            task_id="task-1",
        )
        assert len(events) == 1
        assert events[0].task_id == "task-1"
        assert events[0].event_type == AuditEventType.TASK_STARTED

    def test_export_events(self):
        """Test exporting events as dictionaries"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-1",
            task_count=1,
        )
        logger.log_execution_completed(
            status="completed",
            tasks_completed=1,
            tasks_failed=0,
            duration_seconds=10.0,
        )

        exported = logger.export_events()
        assert len(exported) == 2
        assert all(isinstance(e, dict) for e in exported)
        assert exported[0]["event_type"] == "execution_started"
        assert exported[1]["event_type"] == "execution_completed"

    def test_export_json(self):
        """Test exporting events as JSON string"""
        logger = AuditLogger(execution_id="exec-123")

        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-1",
            task_count=1,
        )

        json_str = logger.export_json()
        parsed = json.loads(json_str)

        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["event_type"] == "execution_started"
