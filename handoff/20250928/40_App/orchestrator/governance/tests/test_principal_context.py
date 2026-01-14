"""
Tests for Principal Context - EPIC E Phase E-2

Tests the PrincipalContext dataclass, capability checking,
and integration with RuntimePolicyEnforcer.
"""
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from governance.principal_context import (
    PrincipalContext,
    AgentType,
    CapabilityType,
    PrincipalContextManager,
    UNKNOWN_PRINCIPAL,
    DEFAULT_CAPABILITIES,
    create_principal_context,
    get_principal_from_context,
)


class TestPrincipalContext:
    """Tests for PrincipalContext dataclass"""

    def test_create_basic_principal(self):
        """Test creating a basic principal context"""
        principal = PrincipalContext(
            agent_id="test-agent-123",
            agent_type="dev_agent",
        )
        assert principal.agent_id == "test-agent-123"
        assert principal.agent_type == "dev_agent"
        assert principal.permission_level == "sandbox_only"
        assert principal.trust_score == 100

    def test_principal_immutability(self):
        """Test that PrincipalContext is immutable (frozen)"""
        principal = PrincipalContext(
            agent_id="test-agent-123",
            agent_type="dev_agent",
        )
        with pytest.raises(AttributeError):
            principal.agent_id = "new-id"

    def test_principal_with_capabilities(self):
        """Test principal with capability set"""
        capabilities = frozenset(["file:read", "file:write", "shell:execute"])
        principal = PrincipalContext(
            agent_id="test-agent-123",
            agent_type="dev_agent",
            capability_set=capabilities,
        )
        assert principal.capability_set == capabilities

    def test_principal_to_dict(self):
        """Test serialization to dictionary"""
        principal = PrincipalContext(
            agent_id="test-agent-123",
            agent_type="dev_agent",
            capability_set=frozenset(["file:read"]),
            permission_level="staging_access",
            trust_score=120,
            session_id="session-456",
            metadata={"source": "test"},
        )
        result = principal.to_dict()
        
        assert result["agent_id"] == "test-agent-123"
        assert result["agent_type"] == "dev_agent"
        assert "file:read" in result["capability_set"]
        assert result["permission_level"] == "staging_access"
        assert result["trust_score"] == 120
        assert result["session_id"] == "session-456"
        assert result["metadata"] == {"source": "test"}

    def test_principal_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "agent_id": "test-agent-123",
            "agent_type": "ops_agent",
            "capability_set": ["file:read", "network:read"],
            "permission_level": "prod_low_risk",
            "trust_score": 150,
            "session_id": "session-789",
            "metadata": {"key": "value"},
        }
        principal = PrincipalContext.from_dict(data)
        
        assert principal.agent_id == "test-agent-123"
        assert principal.agent_type == "ops_agent"
        assert "file:read" in principal.capability_set
        assert "network:read" in principal.capability_set
        assert principal.permission_level == "prod_low_risk"
        assert principal.trust_score == 150


class TestCapabilityChecking:
    """Tests for capability checking methods"""

    def setup_method(self):
        """Set up test fixtures"""
        self.principal = PrincipalContext(
            agent_id="test-agent",
            agent_type="dev_agent",
            capability_set=frozenset([
                "file:read",
                "file:write",
                "shell:execute",
                "github:read",
            ]),
        )

    def test_has_capability_true(self):
        """Test has_capability returns True for existing capability"""
        assert self.principal.has_capability("file:read") is True
        assert self.principal.has_capability("shell:execute") is True

    def test_has_capability_false(self):
        """Test has_capability returns False for missing capability"""
        assert self.principal.has_capability("file:delete") is False
        assert self.principal.has_capability("deploy:production") is False

    def test_has_any_capability_true(self):
        """Test has_any_capability with at least one match"""
        assert self.principal.has_any_capability(["file:read", "file:delete"]) is True
        assert self.principal.has_any_capability(["deploy:production", "github:read"]) is True

    def test_has_any_capability_false(self):
        """Test has_any_capability with no matches"""
        assert self.principal.has_any_capability(["file:delete", "deploy:production"]) is False

    def test_has_all_capabilities_true(self):
        """Test has_all_capabilities with all present"""
        assert self.principal.has_all_capabilities(["file:read", "file:write"]) is True

    def test_has_all_capabilities_false(self):
        """Test has_all_capabilities with some missing"""
        assert self.principal.has_all_capabilities(["file:read", "file:delete"]) is False


class TestAgentType:
    """Tests for AgentType enum"""

    def test_valid_agent_types(self):
        """Test all valid agent types are defined"""
        assert AgentType.DEV_AGENT.value == "dev_agent"
        assert AgentType.OPS_AGENT.value == "ops_agent"
        assert AgentType.PM_AGENT.value == "pm_agent"
        assert AgentType.GROWTH_STRATEGIST.value == "growth_strategist"
        assert AgentType.META_AGENT.value == "meta_agent"
        assert AgentType.UNKNOWN.value == "unknown"


class TestCapabilityType:
    """Tests for CapabilityType enum"""

    def test_file_capabilities(self):
        """Test file operation capabilities"""
        assert CapabilityType.FILE_READ.value == "file:read"
        assert CapabilityType.FILE_WRITE.value == "file:write"
        assert CapabilityType.FILE_DELETE.value == "file:delete"

    def test_network_capabilities(self):
        """Test network operation capabilities"""
        assert CapabilityType.NETWORK_READ.value == "network:read"
        assert CapabilityType.NETWORK_WRITE.value == "network:write"

    def test_shell_capabilities(self):
        """Test shell operation capabilities"""
        assert CapabilityType.SHELL_EXECUTE.value == "shell:execute"
        assert CapabilityType.SHELL_EXECUTE_DANGEROUS.value == "shell:execute_dangerous"

    def test_deploy_capabilities(self):
        """Test deployment capabilities"""
        assert CapabilityType.DEPLOY_SANDBOX.value == "deploy:sandbox"
        assert CapabilityType.DEPLOY_STAGING.value == "deploy:staging"
        assert CapabilityType.DEPLOY_PRODUCTION.value == "deploy:production"


class TestDefaultCapabilities:
    """Tests for default capability sets"""

    def test_sandbox_only_capabilities(self):
        """Test sandbox_only has limited capabilities"""
        caps = DEFAULT_CAPABILITIES["sandbox_only"]
        assert CapabilityType.FILE_READ in caps
        assert CapabilityType.FILE_WRITE in caps
        assert CapabilityType.FILE_DELETE not in caps
        assert CapabilityType.DEPLOY_PRODUCTION not in caps

    def test_staging_access_capabilities(self):
        """Test staging_access has more capabilities"""
        caps = DEFAULT_CAPABILITIES["staging_access"]
        assert CapabilityType.FILE_READ in caps
        assert CapabilityType.GITHUB_PR_CREATE in caps
        assert CapabilityType.DEPLOY_STAGING in caps
        assert CapabilityType.DEPLOY_PRODUCTION not in caps

    def test_prod_full_access_capabilities(self):
        """Test prod_full_access has all capabilities"""
        caps = DEFAULT_CAPABILITIES["prod_full_access"]
        assert CapabilityType.FILE_DELETE in caps
        assert CapabilityType.SHELL_EXECUTE_DANGEROUS in caps
        assert CapabilityType.GITHUB_PR_MERGE in caps
        assert CapabilityType.DEPLOY_PRODUCTION in caps


class TestUnknownPrincipal:
    """Tests for UNKNOWN_PRINCIPAL constant"""

    def test_unknown_principal_defaults(self):
        """Test UNKNOWN_PRINCIPAL has safe defaults"""
        assert UNKNOWN_PRINCIPAL.agent_id == "00000000-0000-0000-0000-000000000000"
        assert UNKNOWN_PRINCIPAL.agent_type == "unknown"
        assert UNKNOWN_PRINCIPAL.permission_level == "sandbox_only"
        assert UNKNOWN_PRINCIPAL.trust_score == 100

    def test_unknown_principal_has_sandbox_capabilities(self):
        """Test UNKNOWN_PRINCIPAL has sandbox-level capabilities"""
        # Should have basic read/write but not dangerous operations
        assert UNKNOWN_PRINCIPAL.has_capability("file:read")
        assert not UNKNOWN_PRINCIPAL.has_capability("deploy:production")


class TestCreatePrincipalContext:
    """Tests for create_principal_context function"""

    def test_create_with_defaults(self):
        """Test creating principal with default values"""
        principal = create_principal_context()
        assert principal.agent_type == "unknown"
        assert principal.permission_level == "sandbox_only"
        assert principal.trust_score == 100

    def test_create_with_agent_type(self):
        """Test creating principal with specific agent type"""
        principal = create_principal_context(agent_type="dev_agent")
        assert principal.agent_type == "dev_agent"

    def test_create_with_session_id(self):
        """Test creating principal with session ID"""
        principal = create_principal_context(session_id="test-session-123")
        assert principal.session_id == "test-session-123"

    def test_create_with_metadata(self):
        """Test creating principal with metadata"""
        principal = create_principal_context(metadata={"source": "test"})
        assert principal.metadata == {"source": "test"}


class TestGetPrincipalFromContext:
    """Tests for get_principal_from_context function"""

    def test_empty_context_returns_unknown(self):
        """Test empty context returns UNKNOWN_PRINCIPAL"""
        result = get_principal_from_context(None)
        assert result == UNKNOWN_PRINCIPAL

    def test_context_with_principal_dict(self):
        """Test extracting principal from context dict"""
        context = {
            "principal": {
                "agent_id": "test-123",
                "agent_type": "ops_agent",
            }
        }
        result = get_principal_from_context(context)
        assert result.agent_id == "test-123"
        assert result.agent_type == "ops_agent"

    def test_context_with_principal_object(self):
        """Test passing PrincipalContext object in context"""
        original = PrincipalContext(
            agent_id="test-456",
            agent_type="pm_agent",
        )
        context = {"principal": original}
        result = get_principal_from_context(context)
        assert result == original

    def test_context_with_agent_info(self):
        """Test extracting agent info from context fields"""
        context = {
            "agent_id": "test-789",
            "agent_type": "dev_agent",
            "session_id": "session-abc",
        }
        result = get_principal_from_context(context)
        assert result.agent_id == "test-789"
        assert result.agent_type == "dev_agent"
        assert result.session_id == "session-abc"


class TestPrincipalContextManager:
    """Tests for PrincipalContextManager thread-local storage"""

    def test_get_current_default(self):
        """Test get_current returns UNKNOWN_PRINCIPAL by default"""
        PrincipalContextManager.clear()
        result = PrincipalContextManager.get_current()
        assert result == UNKNOWN_PRINCIPAL

    def test_set_and_get_current(self):
        """Test setting and getting current principal"""
        principal = PrincipalContext(
            agent_id="test-manager",
            agent_type="dev_agent",
        )
        PrincipalContextManager.set_current(principal)
        result = PrincipalContextManager.get_current()
        assert result == principal
        PrincipalContextManager.clear()

    def test_context_manager_scope(self):
        """Test context manager properly scopes principal"""
        principal = PrincipalContext(
            agent_id="scoped-agent",
            agent_type="ops_agent",
        )
        
        # Before scope
        PrincipalContextManager.clear()
        assert PrincipalContextManager.get_current() == UNKNOWN_PRINCIPAL
        
        # Inside scope
        with PrincipalContextManager.set_context(principal) as ctx:
            assert ctx == principal
            assert PrincipalContextManager.get_current() == principal
        
        # After scope
        assert PrincipalContextManager.get_current() == UNKNOWN_PRINCIPAL

    def test_nested_context_managers(self):
        """Test nested context managers restore correctly"""
        outer = PrincipalContext(agent_id="outer", agent_type="dev_agent")
        inner = PrincipalContext(agent_id="inner", agent_type="ops_agent")
        
        PrincipalContextManager.clear()
        
        with PrincipalContextManager.set_context(outer):
            assert PrincipalContextManager.get_current().agent_id == "outer"
            
            with PrincipalContextManager.set_context(inner):
                assert PrincipalContextManager.get_current().agent_id == "inner"
            
            # Should restore to outer
            assert PrincipalContextManager.get_current().agent_id == "outer"
        
        # Should restore to unknown
        assert PrincipalContextManager.get_current() == UNKNOWN_PRINCIPAL


class TestRuntimePolicyEnforcerIntegration:
    """Tests for RuntimePolicyEnforcer integration with PrincipalContext"""

    def test_check_resource_access_with_principal(self):
        """Test check_resource_access accepts principal parameter"""
        from governance.runtime_policy_enforcer import RuntimePolicyEnforcer
        
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.enable_ssot_telemetry = False
        
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        
        principal = PrincipalContext(
            agent_id="test-agent",
            agent_type="dev_agent",
            capability_set=frozenset(["file:read"]),
        )
        
        # This should not raise - just testing the interface accepts principal
        result = enforcer.check_resource_access(
            operation="read",
            resource="/tmp/test.txt",
            context={"task_id": "test-task"},
            principal=principal,
        )
        
        assert result is not None
        # Principal should be in the context
        assert "principal" in result.telemetry_event.get("context", {}) or \
               result.telemetry_event.get("principal") is not None
