"""
Tests for hitl/action_requests.py module

This module tests the Human-in-the-Loop (HITL) action request functionality
for high-risk operations requiring human approval.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

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
        """Test all status values exist"""
        assert ActionRequestStatus.PENDING.value == "pending"
        assert ActionRequestStatus.APPROVED.value == "approved"
        assert ActionRequestStatus.REJECTED.value == "rejected"
        assert ActionRequestStatus.TIMEOUT.value == "timeout"
        assert ActionRequestStatus.CANCELLED.value == "cancelled"


class TestRiskLevel:
    """Tests for RiskLevel enum"""

    def test_risk_level_values(self):
        """Test all risk level values exist"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestHighRiskPatterns:
    """Tests for HIGH_RISK_PATTERNS constant"""

    def test_database_patterns_exist(self):
        """Test database patterns are defined"""
        assert "database" in HIGH_RISK_PATTERNS
        assert "DROP TABLE" in HIGH_RISK_PATTERNS["database"]
        assert "DELETE FROM" in HIGH_RISK_PATTERNS["database"]

    def test_filesystem_patterns_exist(self):
        """Test filesystem patterns are defined"""
        assert "filesystem" in HIGH_RISK_PATTERNS
        assert "rm -rf" in HIGH_RISK_PATTERNS["filesystem"]

    def test_deployment_patterns_exist(self):
        """Test deployment patterns are defined"""
        assert "deployment" in HIGH_RISK_PATTERNS
        assert "deploy production" in HIGH_RISK_PATTERNS["deployment"]

    def test_secrets_patterns_exist(self):
        """Test secrets patterns are defined"""
        assert "secrets" in HIGH_RISK_PATTERNS
        assert ".env" in HIGH_RISK_PATTERNS["secrets"]


class TestActionRequest:
    """Tests for ActionRequest dataclass"""

    def test_create_action_request_dataclass(self):
        """Test creating an ActionRequest instance"""
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
        )
        assert request.request_id == "ar_test123"
        assert request.agent_id == "agent_001"
        assert request.action_type == "DROP_TABLE"
        assert request.action_description == "Drop users table"
        assert request.status == ActionRequestStatus.PENDING
        assert request.risk_level == RiskLevel.HIGH

    def test_timeout_at_property(self):
        """Test timeout_at property calculation"""
        created = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            timeout_hours=24,
            created_at=created,
        )
        expected_timeout = created + timedelta(hours=24)
        assert request.timeout_at == expected_timeout

    def test_is_expired_false(self):
        """Test is_expired returns False for non-expired request"""
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            timeout_hours=24,
            created_at=datetime.now(timezone.utc),
        )
        assert request.is_expired is False

    def test_is_expired_true(self):
        """Test is_expired returns True for expired request"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            timeout_hours=24,
            created_at=old_time,
        )
        assert request.is_expired is True

    def test_to_dict(self):
        """Test to_dict serialization"""
        created = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            risk_level=RiskLevel.CRITICAL,
            risk_reason="Database destructive operation",
            action_payload={"table": "users"},
            affected_resources=["users_table"],
            trace_id="trace_001",
            timeout_hours=24,
            created_at=created,
        )
        result = request.to_dict()

        assert result["request_id"] == "ar_test123"
        assert result["agent_id"] == "agent_001"
        assert result["action_type"] == "DROP_TABLE"
        assert result["action_description"] == "Drop users table"
        assert result["risk_level"] == "critical"
        assert result["risk_reason"] == "Database destructive operation"
        assert result["action_payload"] == {"table": "users"}
        assert result["affected_resources"] == ["users_table"]
        assert result["trace_id"] == "trace_001"
        assert result["status"] == "pending"
        assert result["resolved_at"] is None

    def test_to_dict_with_resolved_at(self):
        """Test to_dict with resolved_at set"""
        created = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        resolved = datetime(2025, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        request = ActionRequest(
            request_id="ar_test123",
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
            created_at=created,
            resolved_at=resolved,
        )
        result = request.to_dict()
        assert result["resolved_at"] == resolved.isoformat()


class TestDetectRiskLevel:
    """Tests for detect_risk_level function"""

    def test_detect_critical_drop_table(self):
        """Test detection of critical DROP TABLE operation"""
        level, reason = detect_risk_level("sql", "DROP TABLE users")
        assert level == RiskLevel.CRITICAL
        assert "DROP TABLE" in reason

    def test_detect_critical_delete_from(self):
        """Test detection of critical DELETE FROM operation"""
        level, reason = detect_risk_level("sql", "DELETE FROM users WHERE 1=1")
        assert level == RiskLevel.CRITICAL
        assert "DELETE FROM" in reason

    def test_detect_high_rm_rf(self):
        """Test detection of high-risk rm -rf operation"""
        level, reason = detect_risk_level("shell", "rm -rf /var/data")
        assert level == RiskLevel.HIGH
        assert "rm -rf" in reason

    def test_detect_high_deploy_production(self):
        """Test detection of high-risk production deployment"""
        level, reason = detect_risk_level("deploy", "deploy production app")
        assert level == RiskLevel.HIGH
        assert "deploy production" in reason

    def test_detect_high_env_file(self):
        """Test detection of high-risk .env file access"""
        level, reason = detect_risk_level("file", "modify .env file")
        assert level == RiskLevel.HIGH
        assert ".env" in reason

    def test_detect_high_delete_action_type(self):
        """Test detection of high-risk delete action type"""
        level, reason = detect_risk_level("delete_user", "remove user account")
        assert level == RiskLevel.HIGH
        assert "Destructive action type" in reason

    def test_detect_medium_deploy_action_type(self):
        """Test detection of medium-risk deploy action type"""
        level, reason = detect_risk_level("deploy_staging", "deploy to staging")
        assert level == RiskLevel.MEDIUM
        assert "Deployment action" in reason

    def test_detect_low_default(self):
        """Test default low risk level"""
        level, reason = detect_risk_level("read", "read user data")
        assert level == RiskLevel.LOW
        assert reason is None


class TestCreateActionRequest:
    """Tests for create_action_request function"""

    @patch("hitl.action_requests._get_supabase")
    def test_create_request_no_database(self, mock_get_supabase):
        """Test create_action_request when database is unavailable"""
        mock_get_supabase.return_value = None

        result = create_action_request(
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
        )

        assert result is None

    @patch("hitl.action_requests._get_supabase")
    def test_create_request_success(self, mock_get_supabase):
        """Test successful action request creation"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        result = create_action_request(
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
        )

        assert result is not None
        assert result.agent_id == "agent_001"
        assert result.action_type == "DROP_TABLE"
        assert result.request_id.startswith("ar_")

    @patch("hitl.action_requests._get_supabase")
    def test_create_request_with_custom_risk_level(self, mock_get_supabase):
        """Test create_action_request with custom risk level"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        result = create_action_request(
            agent_id="agent_001",
            action_type="custom_action",
            action_description="Custom action",
            risk_level=RiskLevel.MEDIUM,
            risk_reason="Custom reason",
        )

        assert result is not None
        assert result.risk_level == RiskLevel.MEDIUM
        assert result.risk_reason == "Custom reason"

    @patch("hitl.action_requests._get_supabase")
    def test_create_request_database_error(self, mock_get_supabase):
        """Test create_action_request when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = create_action_request(
            agent_id="agent_001",
            action_type="DROP_TABLE",
            action_description="Drop users table",
        )

        assert result is None


class TestApproveActionRequest:
    """Tests for approve_action_request function"""

    @patch("hitl.action_requests._get_supabase")
    def test_approve_no_database(self, mock_get_supabase):
        """Test approve_action_request when database is unavailable"""
        mock_get_supabase.return_value = None

        result = approve_action_request("ar_test123", "admin")
        assert result is False

    @patch("hitl.action_requests._get_supabase")
    def test_approve_success(self, mock_get_supabase):
        """Test successful approval"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=True)
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_test123", "admin")
        assert result is True

    @patch("hitl.action_requests._get_supabase")
    def test_approve_not_found(self, mock_get_supabase):
        """Test approval when request not found"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=False)
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_nonexistent", "admin")
        assert result is False

    @patch("hitl.action_requests._get_supabase")
    def test_approve_database_error(self, mock_get_supabase):
        """Test approval when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = approve_action_request("ar_test123", "admin")
        assert result is False


class TestRejectActionRequest:
    """Tests for reject_action_request function"""

    @patch("hitl.action_requests._get_supabase")
    def test_reject_no_database(self, mock_get_supabase):
        """Test reject_action_request when database is unavailable"""
        mock_get_supabase.return_value = None

        result = reject_action_request("ar_test123", "admin", "Not needed")
        assert result is False

    @patch("hitl.action_requests._get_supabase")
    def test_reject_success(self, mock_get_supabase):
        """Test successful rejection"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=True)
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_test123", "admin", "Not needed")
        assert result is True

    @patch("hitl.action_requests._get_supabase")
    def test_reject_not_found(self, mock_get_supabase):
        """Test rejection when request not found"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=False)
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_nonexistent", "admin")
        assert result is False

    @patch("hitl.action_requests._get_supabase")
    def test_reject_database_error(self, mock_get_supabase):
        """Test rejection when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = reject_action_request("ar_test123", "admin")
        assert result is False


class TestGetPendingRequests:
    """Tests for get_pending_requests function"""

    @patch("hitl.action_requests._get_supabase")
    def test_get_pending_no_database(self, mock_get_supabase):
        """Test get_pending_requests when database is unavailable"""
        mock_get_supabase.return_value = None

        result = get_pending_requests()
        assert result == []

    @patch("hitl.action_requests._get_supabase")
    def test_get_pending_success(self, mock_get_supabase):
        """Test successful retrieval of pending requests"""
        mock_supabase = MagicMock()
        mock_data = [{"request_id": "ar_1"}, {"request_id": "ar_2"}]
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_pending_requests()
        assert len(result) == 2
        assert result[0]["request_id"] == "ar_1"

    @patch("hitl.action_requests._get_supabase")
    def test_get_pending_with_filter(self, mock_get_supabase):
        """Test get_pending_requests with risk level filter"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
        mock_get_supabase.return_value = mock_supabase

        get_pending_requests(limit=10, risk_level_filter=RiskLevel.CRITICAL)

        mock_supabase.rpc.assert_called_once_with(
            "get_pending_action_requests",
            {"p_limit": 10, "p_risk_level_filter": "critical"}
        )

    @patch("hitl.action_requests._get_supabase")
    def test_get_pending_database_error(self, mock_get_supabase):
        """Test get_pending_requests when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = get_pending_requests()
        assert result == []


class TestGetRequestStatus:
    """Tests for get_request_status function"""

    @patch("hitl.action_requests._get_supabase")
    def test_get_status_no_database(self, mock_get_supabase):
        """Test get_request_status when database is unavailable"""
        mock_get_supabase.return_value = None

        result = get_request_status("ar_test123")
        assert result is None

    @patch("hitl.action_requests._get_supabase")
    def test_get_status_success(self, mock_get_supabase):
        """Test successful status retrieval"""
        mock_supabase = MagicMock()
        mock_data = {"request_id": "ar_test123", "status": "pending"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_request_status("ar_test123")
        assert result["request_id"] == "ar_test123"
        assert result["status"] == "pending"

    @patch("hitl.action_requests._get_supabase")
    def test_get_status_not_found(self, mock_get_supabase):
        """Test get_request_status when request not found"""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=None)
        mock_get_supabase.return_value = mock_supabase

        result = get_request_status("ar_nonexistent")
        assert result is None

    @patch("hitl.action_requests._get_supabase")
    def test_get_status_database_error(self, mock_get_supabase):
        """Test get_request_status when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = get_request_status("ar_test123")
        assert result is None


class TestProcessTimedOutRequests:
    """Tests for process_timed_out_requests function"""

    @patch("hitl.action_requests._get_supabase")
    def test_process_timeout_no_database(self, mock_get_supabase):
        """Test process_timed_out_requests when database is unavailable"""
        mock_get_supabase.return_value = None

        result = process_timed_out_requests()
        assert result == 0

    @patch("hitl.action_requests._get_supabase")
    def test_process_timeout_success(self, mock_get_supabase):
        """Test successful timeout processing"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=5)
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()
        assert result == 5

    @patch("hitl.action_requests._get_supabase")
    def test_process_timeout_none_result(self, mock_get_supabase):
        """Test timeout processing with None result"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=None)
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()
        assert result == 0

    @patch("hitl.action_requests._get_supabase")
    def test_process_timeout_database_error(self, mock_get_supabase):
        """Test timeout processing when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = process_timed_out_requests()
        assert result == 0


class TestGetActionRequestStatistics:
    """Tests for get_action_request_statistics function"""

    @patch("hitl.action_requests._get_supabase")
    def test_get_stats_no_database(self, mock_get_supabase):
        """Test get_action_request_statistics when database is unavailable"""
        mock_get_supabase.return_value = None

        result = get_action_request_statistics()
        assert result["pending_count"] == 0
        assert result["by_risk_level"]["critical"] == 0
        assert result["by_risk_level"]["high"] == 0
        assert result["by_risk_level"]["medium"] == 0
        assert result["by_risk_level"]["low"] == 0

    @patch("hitl.action_requests._get_supabase")
    def test_get_stats_success(self, mock_get_supabase):
        """Test successful statistics retrieval"""
        mock_supabase = MagicMock()
        mock_data = {
            "pending_count": 10,
            "critical_count": 2,
            "high_count": 5,
            "medium_count": 2,
            "low_count": 1,
        }
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=mock_data)
        mock_get_supabase.return_value = mock_supabase

        result = get_action_request_statistics()
        assert result["pending_count"] == 10
        assert result["by_risk_level"]["critical"] == 2
        assert result["by_risk_level"]["high"] == 5
        assert result["by_risk_level"]["medium"] == 2
        assert result["by_risk_level"]["low"] == 1

    @patch("hitl.action_requests._get_supabase")
    def test_get_stats_empty_data(self, mock_get_supabase):
        """Test statistics retrieval with empty data"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data={})
        mock_get_supabase.return_value = mock_supabase

        result = get_action_request_statistics()
        assert result["pending_count"] == 0
        assert result["by_risk_level"]["critical"] == 0

    @patch("hitl.action_requests._get_supabase")
    def test_get_stats_database_error(self, mock_get_supabase):
        """Test statistics retrieval when database raises exception"""
        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB error")
        mock_get_supabase.return_value = mock_supabase

        result = get_action_request_statistics()
        assert result["pending_count"] == 0
        assert result["by_risk_level"]["critical"] == 0
