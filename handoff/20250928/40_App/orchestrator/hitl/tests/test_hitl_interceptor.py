#!/usr/bin/env python3
"""
Tests for HITL Interceptor Module - Phase 2 Coverage (#1920) + Bug Fix

Comprehensive test suite for hitl_interceptor.py functionality.

Bug Fixed (PR #1957):
- hitl_interceptor.py line 107 was passing `require_hitl_for_high_risk`
  to SemanticRulesValidator(), but the constructor doesn't accept any parameters.
- This caused TypeError when SEMANTIC_RULES_AVAILABLE=True.
- Fix: Remove the invalid argument; SemanticRulesValidator loads this setting
  from environment/settings internally.

Now that the bug is fixed, tests can use the real SemanticRulesValidator
when SEMANTIC_RULES_AVAILABLE=True.
"""
import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# Bug Fix Verification Tests (PR #1957)
# =============================================================================

class TestHITLInterceptorConstruction:
    """Test that HITLInterceptor can be constructed without TypeError"""

    def test_interceptor_construction_with_semantic_rules_available(self):
        """
        Verify HITLInterceptor can be constructed when SEMANTIC_RULES_AVAILABLE=True.
        
        This test proves the bug fix works - previously this would raise:
        TypeError: SemanticRulesValidator.__init__() got an unexpected keyword argument 'require_hitl_for_high_risk'
        """
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        # This should NOT raise TypeError after the bug fix
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            trace_id="test_trace",
            require_hitl_for_high_risk=True,
            timeout_hours=24,
        )
        
        assert interceptor.agent_id == "test_agent"
        assert interceptor.trace_id == "test_trace"
        assert interceptor.require_hitl_for_high_risk is True
        assert interceptor.timeout_hours == 24
        assert interceptor.validator is not None

    def test_interceptor_construction_with_hitl_disabled(self):
        """Verify HITLInterceptor can be constructed with HITL disabled."""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        assert interceptor.agent_id == "test_agent"
        assert interceptor.require_hitl_for_high_risk is False

    def test_create_interceptor_factory_function(self):
        """Verify the create_interceptor factory function works correctly."""
        from hitl.hitl_interceptor import create_interceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        interceptor = create_interceptor(
            agent_id="factory_test_agent",
            trace_id="factory_trace",
            require_hitl=True,
        )
        
        assert interceptor.agent_id == "factory_test_agent"
        assert interceptor.trace_id == "factory_trace"
        assert interceptor.require_hitl_for_high_risk is True


# =============================================================================
# Integration Tests with Mocked Database
# =============================================================================

class TestHITLInterceptorWithMockedDB:
    """Test HITLInterceptor functionality with mocked database"""

    @patch('hitl.action_requests._get_supabase')
    def test_check_action_with_high_risk_pattern(self, mock_get_supabase):
        """Test that high-risk actions are detected correctly"""
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.rpc.return_value.execute.return_value.data = [{
            'id': 'test-request-id',
            'status': 'pending',
            'agent_id': 'test_agent',
            'action_type': 'DATABASE_OPERATION',
            'action_description': 'DROP TABLE users',
            'risk_level': 'critical',
        }]
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=True,
        )
        
        requires_approval, request = interceptor.check_action(
            action_type="DATABASE_OPERATION",
            action_description="DROP TABLE users",
        )
        
        assert requires_approval is True
        assert request is not None

    def test_check_action_with_safe_action(self):
        """Test that safe actions don't require approval"""
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=True,
        )
        
        requires_approval, request = interceptor.check_action(
            action_type="READ_FILE",
            action_description="Read config.json file",
        )
        
        assert requires_approval is False
        assert request is None

    def test_check_action_with_hitl_disabled(self):
        """Test that no approval is required when HITL is disabled"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_action(
            action_type="DATABASE_OPERATION",
            action_description="DROP TABLE users",
        )
        
        assert requires_approval is False
        assert request is None

    @patch('hitl.action_requests._get_supabase')
    def test_check_command_with_dangerous_command(self, mock_get_supabase):
        """Test that dangerous commands are detected"""
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.rpc.return_value.execute.return_value.data = [{
            'id': 'test-request-id',
            'status': 'pending',
            'agent_id': 'test_agent',
            'action_type': 'SHELL_COMMAND',
            'action_description': 'Execute command: rm -rf /important/data',
            'risk_level': 'critical',
        }]
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=True,
        )
        
        requires_approval, request = interceptor.check_command(
            command="rm -rf /important/data",
        )
        
        assert requires_approval is True
        assert request is not None

    def test_check_command_with_hitl_disabled(self):
        """Test that no approval is required for commands when HITL is disabled"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_command(
            command="rm -rf /important/data",
        )
        
        assert requires_approval is False
        assert request is None

    def test_check_file_access_hitl_disabled(self):
        """Test check_file_access when HITL is disabled"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_file_access(
            file_path=".env",
            operation="modify",
        )
        
        assert requires_approval is False
        assert request is None

    def test_check_file_access_safe_file(self):
        """Test check_file_access with safe file"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_file_access(
            file_path="src/main.py",
            operation="modify",
        )
        
        assert requires_approval is False
        assert request is None


# =============================================================================
# Helper Method Tests
# =============================================================================

class TestHITLInterceptorHelperMethods:
    """Test helper methods of HITLInterceptor"""

    def test_is_high_risk_action_detection(self):
        """Test _is_high_risk_action helper method"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        # High-risk patterns
        assert interceptor._is_high_risk_action("DROP TABLE users") is True
        assert interceptor._is_high_risk_action("DELETE FROM orders") is True
        assert interceptor._is_high_risk_action("rm -rf /data") is True
        assert interceptor._is_high_risk_action("sudo rm important_file") is True
        
        # Safe patterns
        assert interceptor._is_high_risk_action("SELECT * FROM users") is False
        assert interceptor._is_high_risk_action("Read file config.json") is False

    def test_is_sensitive_file_detection(self):
        """Test _is_sensitive_file helper method"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        # Sensitive files
        assert interceptor._is_sensitive_file("id_rsa") is True
        assert interceptor._is_sensitive_file("/home/user/.ssh/id_rsa") is True
        assert interceptor._is_sensitive_file("private_key.pem") is True
        assert interceptor._is_sensitive_file("secrets.yaml") is True
        
        # Non-sensitive files
        assert interceptor._is_sensitive_file("config.json") is False
        assert interceptor._is_sensitive_file("README.md") is False

    def test_violation_to_risk_level_mapping(self):
        """Test _violation_to_risk_level helper method"""
        from hitl.hitl_interceptor import HITLInterceptor
        from hitl.action_requests import RiskLevel
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        class MockViolation:
            def __init__(self, severity):
                self.severity = severity
        
        assert interceptor._violation_to_risk_level(MockViolation('critical')) == RiskLevel.CRITICAL
        assert interceptor._violation_to_risk_level(MockViolation('high')) == RiskLevel.HIGH
        assert interceptor._violation_to_risk_level(MockViolation('medium')) == RiskLevel.MEDIUM
        assert interceptor._violation_to_risk_level(MockViolation('low')) == RiskLevel.LOW
        assert interceptor._violation_to_risk_level(MockViolation('unknown')) == RiskLevel.HIGH


# =============================================================================
# Enum Tests (from Phase 2 Coverage)
# =============================================================================

class TestActionRequestStatusEnum:
    """Tests for ActionRequestStatus enum values"""

    def test_approved_status_value(self):
        """Test APPROVED status has correct value"""
        from hitl.action_requests import ActionRequestStatus
        assert ActionRequestStatus.APPROVED.value == "approved"

    def test_rejected_status_value(self):
        """Test REJECTED status has correct value"""
        from hitl.action_requests import ActionRequestStatus
        assert ActionRequestStatus.REJECTED.value == "rejected"

    def test_pending_status_value(self):
        """Test PENDING status has correct value"""
        from hitl.action_requests import ActionRequestStatus
        assert ActionRequestStatus.PENDING.value == "pending"

    def test_timeout_status_value(self):
        """Test TIMEOUT status has correct value"""
        from hitl.action_requests import ActionRequestStatus
        assert ActionRequestStatus.TIMEOUT.value == "timeout"

    def test_cancelled_status_value(self):
        """Test CANCELLED status has correct value"""
        from hitl.action_requests import ActionRequestStatus
        assert ActionRequestStatus.CANCELLED.value == "cancelled"


class TestRiskLevelEnum:
    """Tests for RiskLevel enum values"""

    def test_low_risk_value(self):
        """Test LOW risk level has correct value"""
        from hitl.action_requests import RiskLevel
        assert RiskLevel.LOW.value == "low"

    def test_medium_risk_value(self):
        """Test MEDIUM risk level has correct value"""
        from hitl.action_requests import RiskLevel
        assert RiskLevel.MEDIUM.value == "medium"

    def test_high_risk_value(self):
        """Test HIGH risk level has correct value"""
        from hitl.action_requests import RiskLevel
        assert RiskLevel.HIGH.value == "high"

    def test_critical_risk_value(self):
        """Test CRITICAL risk level has correct value"""
        from hitl.action_requests import RiskLevel
        assert RiskLevel.CRITICAL.value == "critical"


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestHITLInterceptorEdgeCases:
    """Edge case tests for HITLInterceptor"""

    def test_interceptor_with_empty_agent_id(self):
        """Test interceptor with empty agent_id"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="",
            require_hitl_for_high_risk=False,
        )
        assert interceptor.agent_id == ""

    def test_check_action_with_empty_description(self):
        """Test check_action with empty description"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_action(
            action_type="TEST",
            action_description="",
        )
        
        assert requires_approval is False
        assert request is None

    def test_check_file_access_with_unicode_path(self):
        """Test check_file_access with unicode path"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        requires_approval, request = interceptor.check_file_access(
            file_path="/path/to/文件.txt",
            operation="read",
        )
        
        assert requires_approval is False
        assert request is None

    def test_check_command_with_long_command(self):
        """Test check_command with very long command"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        long_command = "echo " + "a" * 1000
        requires_approval, request = interceptor.check_command(long_command)
        
        assert requires_approval is False
        assert request is None

    def test_interceptor_preserves_trace_id(self):
        """Test that interceptor preserves trace_id"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            trace_id="trace_123",
            require_hitl_for_high_risk=False,
        )
        
        assert interceptor.trace_id == "trace_123"

    @patch('hitl.action_requests._get_supabase')
    def test_get_approval_status_no_database(self, mock_get_supabase):
        """Test get_approval_status when database returns None"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        mock_get_supabase.return_value = None
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        status = interceptor.get_approval_status("nonexistent_id")
        assert status is None
