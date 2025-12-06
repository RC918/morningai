"""
Unit tests for Audit Log Security Features

Tests cover:
- Sensitive data masking in event details
- Sensitive data masking in event metadata
- Masking can be disabled
- Custom masker can be provided
- Masking in exported events

Issue: #1960 - 狀態目錄權限與敏感資料遮罩
Milestone: M5 - Meta Agent 優化
"""

import json

import pytest

from meta_agent.audit_log import AuditEventType, AuditLogger
from meta_agent.sensitive_data_masker import SensitiveDataMasker


class TestAuditLoggerMasking:
    """Tests for AuditLogger sensitive data masking"""

    def test_init_with_masking_enabled_by_default(self):
        """Test that masking is enabled by default"""
        logger = AuditLogger(execution_id="exec-001")
        assert logger.mask_sensitive_data is True
        assert logger.masker is not None

    def test_init_with_masking_disabled(self):
        """Test initialization with masking disabled"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=False,
        )
        assert logger.mask_sensitive_data is False

    def test_init_with_custom_masker(self):
        """Test initialization with custom masker"""
        custom_masker = SensitiveDataMasker(mask_char="#")
        logger = AuditLogger(
            execution_id="exec-001",
            masker=custom_masker,
        )
        assert logger.masker is custom_masker

    def test_log_execution_started_masks_sensitive_data(self):
        """Test that log_execution_started masks sensitive data"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_execution_started(
            goal_text="Deploy with API key sk-1234567890abcdefghij",
            plan_id="plan-001",
            task_count=5,
            api_key="sk-1234567890abcdefghij",
        )

        # Check that sensitive data is masked in details
        assert "sk-1234567890abcdefghij" not in str(event.details)

    def test_log_task_started_masks_sensitive_data(self):
        """Test that log_task_started masks sensitive data in sensitive keys"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_task_started(
            task_id="task-001",
            task_type="API_CALL",
            description="Call API",
            auth_token="ghp_abcdefghijklmnopqrstuvwxyz123456",
        )

        # Check that sensitive key value is masked
        assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in event.details["auth_token"]
        # auth_token should be masked because it's a sensitive key
        assert "****" in event.details["auth_token"]

    def test_log_task_failed_masks_sensitive_keys(self):
        """Test that log_task_failed masks sensitive key values"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_task_failed(
            task_id="task-001",
            error="Auth failed",
            attempt=1,
            api_key="sk-1234567890abcdefghij",
        )

        # Check that sensitive key value is masked
        assert "sk-1234567890abcdefghij" not in event.details["api_key"]
        assert "****" in event.details["api_key"]

    def test_log_approval_requested_masks_sensitive_keys(self):
        """Test that log_approval_requested masks sensitive key values"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_approval_requested(
            task_id="task-001",
            operation="deploy",
            resource="production",
            reason="Deploying to production",
            secret_key="sk-secretkey12345678901234",
        )

        # Check that sensitive key value is masked
        assert "sk-secretkey12345678901234" not in event.details["secret_key"]
        assert "****" in event.details["secret_key"]

    def test_log_high_risk_operation_masks_sensitive_keys(self):
        """Test that log_high_risk_operation masks sensitive key values"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_high_risk_operation(
            task_id="task-001",
            operation="database_migration",
            resource="production_db",
            risk_level="high",
            db_password="supersecretdbpassword",
        )

        # Check that sensitive key value is masked
        assert "supersecretdbpassword" not in event.details["db_password"]
        assert "****" in event.details["db_password"]

    def test_masking_disabled_preserves_data(self):
        """Test that disabling masking preserves sensitive data"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=False,
        )

        event = logger.log_execution_started(
            goal_text="Test goal",
            plan_id="plan-001",
            task_count=1,
            api_key="sk-1234567890abcdefghij",
        )

        # Check that data is NOT masked
        assert event.details["api_key"] == "sk-1234567890abcdefghij"

    def test_export_events_contains_masked_data(self):
        """Test that exported events contain masked data"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-001",
            task_count=1,
            secret_key="mysupersecretkey123",
        )

        exported = logger.export_events()
        assert len(exported) == 1
        assert "mysupersecretkey123" not in str(exported[0])

    def test_export_json_contains_masked_data(self):
        """Test that JSON export contains masked data"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        logger.log_task_completed(
            task_id="task-001",
            duration_seconds=10.5,
            outputs={"result": "success"},
            api_response_token="Bearer eyJhbGciOiJIUzI1NiJ9",
        )

        json_output = logger.export_json()
        assert "eyJhbGciOiJIUzI1NiJ9" not in json_output

    def test_get_events_returns_masked_events(self):
        """Test that get_events returns masked events"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        logger.log_task_started(
            task_id="task-001",
            task_type="API_CALL",
            description="Test task",
            password="secretpassword123",
        )

        events = logger.get_events(task_id="task-001")
        assert len(events) == 1
        assert "secretpassword123" not in str(events[0].details)


class TestAuditLoggerMaskingEdgeCases:
    """Tests for edge cases in audit logger masking"""

    def test_empty_details_handled(self):
        """Test that empty details are handled gracefully"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        # This should not raise an error
        event = logger.log_execution_completed(
            status="completed",
            tasks_completed=5,
            tasks_failed=0,
            duration_seconds=100.0,
        )

        assert event.details is not None

    def test_none_values_in_details_handled(self):
        """Test that None values in details are handled"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_approval_denied(
            task_id="task-001",
            denier="admin",
            operation="deploy",
            reason=None,
        )

        assert event.details["reason"] is None

    def test_nested_sensitive_data_masked(self):
        """Test that nested sensitive data is masked"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        event = logger.log_policy_violation(
            violation_type="unauthorized_access",
            details="Attempted access",
            context={
                "user": "john",
                "attempted_token": "ghp_abcdefghijklmnopqrstuvwxyz123456",
            },
        )

        # Check nested data is masked
        context = event.details.get("context", {})
        if isinstance(context, dict):
            assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in str(context)

    def test_multiple_events_all_masked(self):
        """Test that multiple events are all masked"""
        logger = AuditLogger(
            execution_id="exec-001",
            mask_sensitive_data=True,
        )

        # Log multiple events with sensitive data
        logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-001",
            task_count=2,
            key1="sk-key1234567890abc",
        )

        logger.log_task_started(
            task_id="task-001",
            task_type="TEST",
            description="Test",
            key2="ghp_key1234567890abcdefghijklmnopqrst",
        )

        logger.log_task_completed(
            task_id="task-001",
            duration_seconds=5.0,
            key3="xoxb-token-12345678901234567890",
        )

        # Check all events are masked
        for event in logger.events:
            event_str = str(event.details)
            assert "sk-key1234567890abc" not in event_str
            assert "ghp_key1234567890abcdefghijklmnopqrst" not in event_str
            assert "xoxb-token-12345678901234567890" not in event_str


class TestCustomMaskerInAuditLogger:
    """Tests for custom masker usage in AuditLogger"""

    def test_custom_mask_character(self):
        """Test that custom mask character is used"""
        custom_masker = SensitiveDataMasker(mask_char="#")
        logger = AuditLogger(
            execution_id="exec-001",
            masker=custom_masker,
            mask_sensitive_data=True,
        )

        event = logger.log_execution_started(
            goal_text="Test",
            plan_id="plan-001",
            task_count=1,
            password="mysecretpassword",
        )

        # Check custom mask character is used
        assert "####" in event.details["password"]

    def test_custom_sensitive_keys(self):
        """Test that custom sensitive keys are respected"""
        custom_masker = SensitiveDataMasker(
            sensitive_keys={"custom_secret_field"}
        )
        logger = AuditLogger(
            execution_id="exec-001",
            masker=custom_masker,
            mask_sensitive_data=True,
        )

        event = logger.log_task_started(
            task_id="task-001",
            task_type="TEST",
            description="Test",
            custom_secret_field="this_should_be_masked_123",
        )

        # Check custom field is masked
        assert "this_should_be_masked_123" not in event.details["custom_secret_field"]
