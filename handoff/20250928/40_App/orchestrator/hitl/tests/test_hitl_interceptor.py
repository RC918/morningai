"""
Tests for HITLInterceptor - Integration with SemanticRulesValidator

This test file verifies that HITLInterceptor correctly integrates with
SemanticRulesValidator after the bug fix that removed the invalid
constructor argument.

Bug Fixed:
- hitl_interceptor.py line 107 was passing `require_hitl_for_high_risk`
  to SemanticRulesValidator(), but the constructor doesn't accept any parameters.
- This caused TypeError when SEMANTIC_RULES_AVAILABLE=True.
- Fix: Remove the invalid argument; SemanticRulesValidator loads this setting
  from environment/settings internally.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestHITLInterceptorConstruction:
    """Test that HITLInterceptor can be constructed without TypeError"""

    def test_interceptor_construction_with_semantic_rules_available(self):
        """
        Verify HITLInterceptor can be constructed when SEMANTIC_RULES_AVAILABLE=True.
        
        This test proves the bug fix works - previously this would raise:
        TypeError: SemanticRulesValidator.__init__() got an unexpected keyword argument 'require_hitl_for_high_risk'
        """
        # Import the module to test
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        # Only run this test if semantic rules are available
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        # This should NOT raise TypeError after the bug fix
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            trace_id="test_trace",
            require_hitl_for_high_risk=True,
            timeout_hours=24,
        )
        
        # Verify the interceptor was created correctly
        assert interceptor.agent_id == "test_agent"
        assert interceptor.trace_id == "test_trace"
        assert interceptor.require_hitl_for_high_risk is True
        assert interceptor.timeout_hours == 24
        assert interceptor.validator is not None

    def test_interceptor_construction_with_hitl_disabled(self):
        """
        Verify HITLInterceptor can be constructed with HITL disabled.
        """
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,
        )
        
        assert interceptor.agent_id == "test_agent"
        assert interceptor.require_hitl_for_high_risk is False

    def test_create_interceptor_factory_function(self):
        """
        Verify the create_interceptor factory function works correctly.
        """
        from hitl.hitl_interceptor import create_interceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        # This should NOT raise TypeError after the bug fix
        interceptor = create_interceptor(
            agent_id="factory_test_agent",
            trace_id="factory_trace",
            require_hitl=True,
        )
        
        assert interceptor.agent_id == "factory_test_agent"
        assert interceptor.trace_id == "factory_trace"
        assert interceptor.require_hitl_for_high_risk is True


class TestHITLInterceptorWithMockedDB:
    """Test HITLInterceptor functionality with mocked database"""

    @patch('hitl.action_requests._get_supabase')
    def test_check_action_with_high_risk_pattern(self, mock_get_supabase):
        """Test that high-risk actions are detected correctly"""
        from hitl.hitl_interceptor import HITLInterceptor, SEMANTIC_RULES_AVAILABLE
        
        if not SEMANTIC_RULES_AVAILABLE:
            pytest.skip("SemanticRulesValidator not available in this environment")
        
        # Mock the Supabase client
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
        
        # Test with a high-risk action (DROP TABLE)
        requires_approval, request = interceptor.check_action(
            action_type="DATABASE_OPERATION",
            action_description="DROP TABLE users",
        )
        
        # Should require approval for high-risk actions
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
        
        # Test with a safe action (no high-risk patterns)
        requires_approval, request = interceptor.check_action(
            action_type="READ_FILE",
            action_description="Read config.json file",
        )
        
        # Should NOT require approval for safe actions
        assert requires_approval is False
        assert request is None

    def test_check_action_with_hitl_disabled(self):
        """Test that no approval is required when HITL is disabled"""
        from hitl.hitl_interceptor import HITLInterceptor
        
        interceptor = HITLInterceptor(
            agent_id="test_agent",
            require_hitl_for_high_risk=False,  # HITL disabled
        )
        
        # Even high-risk actions should not require approval when HITL is disabled
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
        
        # Mock the Supabase client
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
        
        # Test with a dangerous command (rm -rf)
        requires_approval, request = interceptor.check_command(
            command="rm -rf /important/data",
        )
        
        # Should require approval for dangerous commands
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
        
        # Create mock violations with different severities
        class MockViolation:
            def __init__(self, severity):
                self.severity = severity
        
        assert interceptor._violation_to_risk_level(MockViolation('critical')) == RiskLevel.CRITICAL
        assert interceptor._violation_to_risk_level(MockViolation('high')) == RiskLevel.HIGH
        assert interceptor._violation_to_risk_level(MockViolation('medium')) == RiskLevel.MEDIUM
        assert interceptor._violation_to_risk_level(MockViolation('low')) == RiskLevel.LOW
        
        # Unknown severity defaults to HIGH
        assert interceptor._violation_to_risk_level(MockViolation('unknown')) == RiskLevel.HIGH
