#!/usr/bin/env python3
"""
Tests for HITL Action Requests Module - Phase 2 Coverage (#1920)

Comprehensive test suite for action_requests.py functionality.
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

# Add orchestrator to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hitl.action_requests import (
    ActionRequest,
    ActionRequestStatus,
    RiskLevel,
    HIGH_RISK_PATTERNS,
    detect_risk_level,
    create_action_request,
    approve_action_request,
    reject_action_request,
    get_pending_requests,
    get_request_status,
    process_timed_out_requests,
    get_action_request_statistics,
)


class TestActionRequestStatus:
    """Tests for ActionRequestStatus enum"""

    def test_status_values(self):
        """Test ActionRequestStatus enum values"""
        assert ActionRequestStatus.PENDING.value == "pending"
        assert ActionRequestStatus.APPROVED.value == "approved"
        assert ActionRequestStatus.REJECTED.value == "rejected"
        assert ActionRequestStatus.TIMEOUT.value == "timeout"
        assert ActionRequestStatus.CANCELLED.value == "cancelled"

    def test_all_statuses_defined(self):
        """Test all expected statuses are defined"""
        expected_statuses = {"pending", "approved", "rejected", "timeout", "cancelled"}
        actual_statuses = {s.value for s in ActionRequestStatus}
        assert actual_statuses == expected_statuses


class TestRiskLevel:
    """Tests for RiskLevel enum"""

    def test_risk_level_values(self):
        """Test RiskLevel enum values"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_all_risk_levels_defined(self):
        """Test all expected risk levels are defined"""
        expected_levels = {"low", "medium", "high", "critical"}
        actual_levels = {r.value for r in RiskLevel}
        assert actual_levels == expected_levels


class TestHighRiskPatterns:
    """Tests for HIGH_RISK_PATTERNS constant"""

    def test_database_patterns_exist(self):
        """Test database patterns are defined"""
        assert "database" in HIGH_RISK_PATTERNS
        assert "DROP TABLE" in HIGH_RISK_PATTERNS["database"]
        assert "DELETE FROM" in HIGH_RISK_PATTERNS["database"]
        assert "TRUNCATE" in HIGH_RISK_PATTERNS["database"]

    def test_filesystem_patterns_exist(self):
        """Test filesystem patterns are defined"""
        assert "filesystem" in HIGH_RISK_PATTERNS
        assert "rm -rf" in HIGH_RISK_PATTERNS["filesystem"]
        assert "chmod 777" in HIGH_RISK_PATTERNS["filesystem"]

    def test_deployment_patterns_exist(self):
        """Test deployment patterns are defined"""
        assert "deployment" in HIGH_RISK_PATTERNS
        assert "deploy production" in HIGH_RISK_PATTERNS["deployment"]

    def test_secrets_patterns_exist(self):
        """Test secrets patterns are defined"""
        assert "secrets" in HIGH_RISK_PATTERNS
        assert ".env" in HIGH_RISK_PATTERNS["secrets"]
        assert "credentials" in HIGH_RISK_PATTERNS["secrets"]


class TestActionRequest:
    """Tests for ActionRequest dataclass"""

    def test_action_request_creation(self):
        """Test ActionRequest creation with required fields"""
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="test_agent",
            action_type="DELETE_FILE",
            action_description="Delete test file",
        )
        assert request.request_id == "ar_test123"
        assert request.agent_id == "test_agent"
        assert request.action_type == "DELETE_FILE"
        assert request.action_description == "Delete test file"
        assert request.status == ActionRequestStatus.PENDING
        assert request.risk_level == RiskLevel.HIGH

    def test_action_request_with_all_fields(self):
        """Test ActionRequest creation with all fields"""
        created_at = datetime.now(timezone.utc)
        request = ActionRequest(
            request_id="ar_test456",
            agent_id="test_agent",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            risk_level=RiskLevel.CRITICAL,
            risk_reason="Database destructive operation",
            action_payload={"table": "users"},
            affected_resources=["users", "user_sessions"],
            trace_id="trace_123",
            status=ActionRequestStatus.PENDING,
            timeout_hours=48,
            created_at=created_at,
        )
        assert request.risk_level == RiskLevel.CRITICAL
        assert request.risk_reason == "Database destructive operation"
        assert request.action_payload == {"table": "users"}
        assert request.affected_resources == ["users", "user_sessions"]
        assert request.trace_id == "trace_123"
        assert request.timeout_hours == 48

    def test_timeout_at_property(self):
        """Test timeout_at property calculation"""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="TEST",
            action_description="Test",
            timeout_hours=24,
            created_at=created_at,
        )
        expected_timeout = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        assert request.timeout_at == expected_timeout

    def test_is_expired_property_not_expired(self):
        """Test is_expired property when not expired"""
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="TEST",
            action_description="Test",
            timeout_hours=24,
            created_at=datetime.now(timezone.utc),
        )
        assert request.is_expired is False

    def test_is_expired_property_expired(self):
        """Test is_expired property when expired"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="TEST",
            action_description="Test",
            timeout_hours=24,
            created_at=old_time,
        )
        assert request.is_expired is True

    def test_to_dict(self):
        """Test to_dict serialization"""
        created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="DELETE_FILE",
            action_description="Delete file",
            risk_level=RiskLevel.HIGH,
            risk_reason="Sensitive file",
            action_payload={"file": "test.txt"},
            affected_resources=["test.txt"],
            trace_id="trace_123",
            timeout_hours=24,
            created_at=created_at,
        )
        result = request.to_dict()

        assert result["request_id"] == "ar_test"
        assert result["agent_id"] == "test_agent"
        assert result["action_type"] == "DELETE_FILE"
        assert result["risk_level"] == "high"
        assert result["status"] == "pending"
        assert result["trace_id"] == "trace_123"
        assert "timeout_at" in result
        assert "created_at" in result


class TestDetectRiskLevel:
    """Tests for detect_risk_level function"""

    def test_detect_critical_database_operation(self):
        """Test detection of critical database operations"""
        risk_level, reason = detect_risk_level("sql", "DROP TABLE users")
        assert risk_level == RiskLevel.CRITICAL
        assert "Database destructive operation" in reason

    def test_detect_critical_delete_from(self):
        """Test detection of DELETE FROM operations"""
        risk_level, reason = detect_risk_level("sql", "DELETE FROM users WHERE id > 0")
        assert risk_level == RiskLevel.CRITICAL
        assert "Database destructive operation" in reason

    def test_detect_high_risk_filesystem(self):
        """Test detection of high-risk filesystem operations"""
        risk_level, reason = detect_risk_level("shell", "rm -rf /var/data")
        assert risk_level == RiskLevel.HIGH
        assert "Dangerous filesystem operation" in reason

    def test_detect_high_risk_chmod(self):
        """Test detection of chmod 777 operations"""
        risk_level, reason = detect_risk_level("shell", "chmod 777 /etc/passwd")
        assert risk_level == RiskLevel.HIGH
        assert "Dangerous filesystem operation" in reason

    def test_detect_high_risk_deployment(self):
        """Test detection of production deployment"""
        risk_level, reason = detect_risk_level("deploy", "deploy production")
        assert risk_level == RiskLevel.HIGH
        assert "Production deployment" in reason

    def test_detect_high_risk_secrets(self):
        """Test detection of secrets access"""
        risk_level, reason = detect_risk_level("file", "modify .env file")
        assert risk_level == RiskLevel.HIGH
        assert "Sensitive file access" in reason

    def test_detect_high_risk_by_action_type(self):
        """Test detection based on action type"""
        risk_level, reason = detect_risk_level("delete_database", "remove old data")
        assert risk_level == RiskLevel.HIGH
        assert "Destructive action type" in reason

    def test_detect_medium_risk_deployment(self):
        """Test detection of medium-risk deployment"""
        risk_level, reason = detect_risk_level("deploy_staging", "deploy to staging")
        assert risk_level == RiskLevel.MEDIUM
        assert "Deployment action" in reason

    def test_detect_low_risk_safe_action(self):
        """Test detection of low-risk safe actions"""
        risk_level, reason = detect_risk_level("read_file", "read config.json")
        assert risk_level == RiskLevel.LOW
        assert reason is None


class TestCreateActionRequest:
    """Tests for create_action_request function"""

    @patch('hitl.action_requests._get_supabase')
    def test_create_request_success(self, mock_get_supabase):
        """Test successful action request creation"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        request = create_action_request(
            agent_id="test_agent",
            action_type="DELETE_FILE",
            action_description="Delete test.txt",
        )

        assert request is not None
        assert request.agent_id == "test_agent"
        assert request.action_type == "DELETE_FILE"
        assert request.request_id.startswith("ar_")
        mock_supabase.rpc.assert_called_once()

    @patch('hitl.action_requests._get_supabase')
    def test_create_request_with_auto_risk_detection(self, mock_get_supabase):
        """Test action request creation with auto risk detection"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        request = create_action_request(
            agent_id="test_agent",
            action_type="sql",
            action_description="DROP TABLE users",
        )

        assert request is not None
        assert request.risk_level == RiskLevel.CRITICAL

    @patch('hitl.action_requests._get_supabase')
    def test_create_request_with_explicit_risk_level(self, mock_get_supabase):
        """Test action request creation with explicit risk level"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        request = create_action_request(
            agent_id="test_agent",
            action_type="custom",
            action_description="Custom action",
            risk_level=RiskLevel.MEDIUM,
            risk_reason="Custom reason",
        )

        assert request is not None
        assert request.risk_level == RiskLevel.MEDIUM
        assert request.risk_reason == "Custom reason"

    @patch('hitl.action_requests._get_supabase')
    def test_create_request_no_database(self, mock_get_supabase):
        """Test action request creation when database unavailable"""
        mock_get_supabase.return_value = None

        request = create_action_request(
            agent_id="test_agent",
            action_type="DELETE_FILE",
            action_description="Delete test.txt",
        )

        assert request is None

    @patch('hitl.action_requests._get_supabase')
    def test_create_request_database_error(self, mock_get_supabase):
        """Test action request creation with database error"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB Error")
        mock_get_supabase.return_value = mock_supabase

        request = create_action_request(
            agent_id="test_agent",
            action_type="DELETE_FILE",
            action_description="Delete test.txt",
        )

        assert request is None


class TestApproveActionRequest:
    """Tests for approve_action_request function"""

    @patch('hitl.action_requests._get_supabase')
    def test_approve_request_success(self, mock_get_supabase):
        """Test successful request approval"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=True)
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_test123", "admin_user")

        assert result is True
        mock_supabase.rpc.assert_called_once_with(
            "approve_action_request",
            {"p_request_id": "ar_test123", "p_approved_by": "admin_user"}
        )

    @patch('hitl.action_requests._get_supabase')
    def test_approve_request_not_found(self, mock_get_supabase):
        """Test approval of non-existent request"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=False)
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_nonexistent", "admin_user")

        assert result is False

    @patch('hitl.action_requests._get_supabase')
    def test_approve_request_no_database(self, mock_get_supabase):
        """Test approval when database unavailable"""
        mock_get_supabase.return_value = None

        result = approve_action_request("ar_test123", "admin_user")

        assert result is False

    @patch('hitl.action_requests._get_supabase')
    def test_approve_request_database_error(self, mock_get_supabase):
        """Test approval with database error"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB Error")
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_test123", "admin_user")

        assert result is False


class TestRejectActionRequest:
    """Tests for reject_action_request function"""

    @patch('hitl.action_requests._get_supabase')
    def test_reject_request_success(self, mock_get_supabase):
        """Test successful request rejection"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=True)
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_test123", "admin_user", "Too risky")

        assert result is True
        mock_supabase.rpc.assert_called_once_with(
            "reject_action_request",
            {
                "p_request_id": "ar_test123",
                "p_rejected_by": "admin_user",
                "p_reason": "Too risky"
            }
        )

    @patch('hitl.action_requests._get_supabase')
    def test_reject_request_without_reason(self, mock_get_supabase):
        """Test rejection without reason"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=True)
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_test123", "admin_user")

        assert result is True

    @patch('hitl.action_requests._get_supabase')
    def test_reject_request_not_found(self, mock_get_supabase):
        """Test rejection of non-existent request"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=False)
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_nonexistent", "admin_user")

        assert result is False

    @patch('hitl.action_requests._get_supabase')
    def test_reject_request_no_database(self, mock_get_supabase):
        """Test rejection when database unavailable"""
        mock_get_supabase.return_value = None

        result = reject_action_request("ar_test123", "admin_user")

        assert result is False


class TestGetPendingRequests:
    """Tests for get_pending_requests function"""

    @patch('hitl.action_requests._get_supabase')
    def test_get_pending_requests_success(self, mock_get_supabase):
        """Test successful retrieval of pending requests"""
        mock_data = [
            {"request_id": "ar_1", "status": "pending"},
            {"request_id": "ar_2", "status": "pending"},
        ]
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_pending_requests()

        assert len(result) == 2
        assert result[0]["request_id"] == "ar_1"

    @patch('hitl.action_requests._get_supabase')
    def test_get_pending_requests_with_filter(self, mock_get_supabase):
        """Test retrieval with risk level filter"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
        mock_get_supabase.return_value = mock_supabase

        get_pending_requests(limit=10, risk_level_filter=RiskLevel.CRITICAL)

        mock_supabase.rpc.assert_called_once_with(
            "get_pending_action_requests",
            {"p_limit": 10, "p_risk_level_filter": "critical"}
        )

    @patch('hitl.action_requests._get_supabase')
    def test_get_pending_requests_no_database(self, mock_get_supabase):
        """Test retrieval when database unavailable"""
        mock_get_supabase.return_value = None

        result = get_pending_requests()

        assert result == []

    @patch('hitl.action_requests._get_supabase')
    def test_get_pending_requests_empty(self, mock_get_supabase):
        """Test retrieval when no pending requests"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=None)
        mock_get_supabase.return_value = mock_supabase

        result = get_pending_requests()

        assert result == []


class TestGetRequestStatus:
    """Tests for get_request_status function"""

    @patch('hitl.action_requests._get_supabase')
    def test_get_request_status_success(self, mock_get_supabase):
        """Test successful status retrieval"""
        mock_data = {"request_id": "ar_test", "status": "approved"}
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_request_status("ar_test")

        assert result is not None
        assert result["status"] == "approved"

    @patch('hitl.action_requests._get_supabase')
    def test_get_request_status_not_found(self, mock_get_supabase):
        """Test status retrieval for non-existent request"""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=None)
        mock_get_supabase.return_value = mock_supabase

        result = get_request_status("ar_nonexistent")

        assert result is None

    @patch('hitl.action_requests._get_supabase')
    def test_get_request_status_no_database(self, mock_get_supabase):
        """Test status retrieval when database unavailable"""
        mock_get_supabase.return_value = None

        result = get_request_status("ar_test")

        assert result is None


class TestProcessTimedOutRequests:
    """Tests for process_timed_out_requests function"""

    @patch('hitl.action_requests._get_supabase')
    def test_process_timed_out_success(self, mock_get_supabase):
        """Test successful processing of timed out requests"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=5)
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()

        assert result == 5
        mock_supabase.rpc.assert_called_once_with("process_timed_out_requests")

    @patch('hitl.action_requests._get_supabase')
    def test_process_timed_out_none(self, mock_get_supabase):
        """Test processing when no timed out requests"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=0)
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()

        assert result == 0

    @patch('hitl.action_requests._get_supabase')
    def test_process_timed_out_no_database(self, mock_get_supabase):
        """Test processing when database unavailable"""
        mock_get_supabase.return_value = None

        result = process_timed_out_requests()

        assert result == 0

    @patch('hitl.action_requests._get_supabase')
    def test_process_timed_out_error(self, mock_get_supabase):
        """Test processing with database error"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB Error")
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()

        assert result == 0


class TestGetActionRequestStatistics:
    """Tests for get_action_request_statistics function"""

    @patch('hitl.action_requests._get_supabase')
    def test_get_statistics_success(self, mock_get_supabase):
        """Test successful statistics retrieval"""
        mock_data = {
            "pending_count": 10,
            "critical_count": 2,
            "high_count": 5,
            "medium_count": 2,
            "low_count": 1,
        }
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_action_request_statistics()

        assert result["pending_count"] == 10
        assert result["by_risk_level"]["critical"] == 2
        assert result["by_risk_level"]["high"] == 5

    @patch('hitl.action_requests._get_supabase')
    def test_get_statistics_no_database(self, mock_get_supabase):
        """Test statistics retrieval when database unavailable"""
        mock_get_supabase.return_value = None

        result = get_action_request_statistics()

        assert result["pending_count"] == 0
        assert result["by_risk_level"]["critical"] == 0

    @patch('hitl.action_requests._get_supabase')
    def test_get_statistics_error(self, mock_get_supabase):
        """Test statistics retrieval with error"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB Error")
        mock_get_supabase.return_value = mock_supabase

        result = get_action_request_statistics()

        assert result["pending_count"] == 0


class TestEdgeCases:
    """Tests for edge cases"""

    def test_action_request_with_empty_payload(self):
        """Test ActionRequest with empty payload"""
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="TEST",
            action_description="Test",
            action_payload={},
            affected_resources=[],
        )
        result = request.to_dict()
        assert result["action_payload"] == {}
        assert result["affected_resources"] == []

    def test_detect_risk_level_case_insensitive(self):
        """Test risk level detection is case insensitive"""
        risk_level, _ = detect_risk_level("sql", "drop table USERS")
        assert risk_level == RiskLevel.CRITICAL

        risk_level, _ = detect_risk_level("shell", "RM -RF /data")
        assert risk_level == RiskLevel.HIGH

    def test_detect_risk_level_with_unicode(self):
        """Test risk level detection with unicode characters"""
        risk_level, reason = detect_risk_level("file", "刪除 .env 檔案")
        assert risk_level == RiskLevel.HIGH

    def test_action_request_resolved_at_serialization(self):
        """Test to_dict with resolved_at set"""
        resolved_time = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test",
            agent_id="test_agent",
            action_type="TEST",
            action_description="Test",
            resolved_at=resolved_time,
        )
        result = request.to_dict()
        assert result["resolved_at"] == "2024-01-02T12:00:00+00:00"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
