"""
Tests for governance/policy_guard.py

Phase 0: Test coverage improvement (17% -> 60%+)
Focus: Deterministic unit tests without external dependencies
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from governance.policy_guard import (
    PolicyGuard,
    PolicyViolation,
    get_policy_guard,
    guarded
)


class TestPolicyGuardInit:
    """Test PolicyGuard initialization"""
    
    def test_init_with_valid_policies_path(self):
        """PolicyGuard should load policies from provided path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("resource_sandbox:\n  file_access:\n    allow: ['*.py']")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.policies_path == temp_path
            assert 'resource_sandbox' in guard.policies
        finally:
            os.unlink(temp_path)
    
    def test_init_with_missing_policies_file(self):
        """PolicyGuard should handle missing policies file gracefully"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.policies == {}
    
    def test_init_with_invalid_yaml(self):
        """PolicyGuard should handle invalid YAML gracefully"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [[[")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.policies == {}
        finally:
            os.unlink(temp_path)


class TestFileAccessControl:
    """Test file access control logic"""
    
    def test_check_file_access_no_policies(self):
        """Should allow all file access when no policies loaded"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.check_file_access('/any/file.py') is True
    
    def test_check_file_access_deny_pattern(self):
        """Should deny file access matching deny pattern"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  file_access:
    deny:
      - '*.env'
      - 'secrets/**'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            
            with pytest.raises(PolicyViolation, match="File access denied.*\\.env"):
                guard.check_file_access('.env')
            
            with pytest.raises(PolicyViolation, match="File access denied.*secrets/"):
                guard.check_file_access('secrets/api_key.txt')
        finally:
            os.unlink(temp_path)
    
    def test_check_file_access_allow_pattern(self):
        """Should allow file access matching allow pattern"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  file_access:
    allow:
      - '*.py'
      - 'tests/**'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.check_file_access('main.py') is True
            assert guard.check_file_access('tests/test_main.py') is True
            
            with pytest.raises(PolicyViolation, match="not in allow list"):
                guard.check_file_access('config.json')
        finally:
            os.unlink(temp_path)


class TestNetworkAccessControl:
    """Test network access control logic"""
    
    def test_check_network_access_no_policies(self):
        """Should allow all network access when no policies loaded"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.check_network_access('example.com') is True
    
    def test_check_network_access_allow_domains(self):
        """Should allow network access to whitelisted domains"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  network:
    allow_domains:
      - 'api.github.com'
      - '*.openai.com'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.check_network_access('api.github.com') is True
            assert guard.check_network_access('api.openai.com') is True
            
            with pytest.raises(PolicyViolation, match="Network access denied"):
                guard.check_network_access('malicious.com')
        finally:
            os.unlink(temp_path)
    
    def test_check_network_access_wildcard_domain(self):
        """Should handle wildcard domain patterns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  network:
    allow_domains:
      - '*.example.com'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.check_network_access('api.example.com') is True
            assert guard.check_network_access('example.com') is True
            
            with pytest.raises(PolicyViolation):
                guard.check_network_access('example.org')
        finally:
            os.unlink(temp_path)


class TestToolPermissions:
    """Test tool permission checks"""
    
    def test_check_tool_permission_no_policies(self):
        """Should allow all tool access when no policies loaded"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.check_tool_permission('any_tool', 'execute', 'sandbox_only') is True
    
    def test_check_tool_permission_level_check(self):
        """Should enforce permission level requirements"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
capability_constraints:
  restricted_tools:
    - name: 'deploy'
      permission_level: 'prod_full_access'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            
            with pytest.raises(PolicyViolation, match="requires prod_full_access"):
                guard.check_tool_permission('deploy', 'execute', 'sandbox_only')
            
            assert guard.check_tool_permission('deploy', 'execute', 'prod_full_access') is True
        finally:
            os.unlink(temp_path)
    
    def test_check_tool_permission_denied_operations(self):
        """Should deny explicitly denied operations"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
capability_constraints:
  restricted_tools:
    - name: 'database'
      permission_level: 'sandbox_only'
      denied_operations:
        - 'drop_table'
        - 'truncate'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            
            with pytest.raises(PolicyViolation, match="Operation denied.*drop_table"):
                guard.check_tool_permission('database', 'drop_table', 'prod_full_access')
            
            assert guard.check_tool_permission('database', 'select', 'sandbox_only') is True
        finally:
            os.unlink(temp_path)
    
    def test_check_tool_permission_allowed_operations(self):
        """Should enforce allowed operations whitelist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
capability_constraints:
  restricted_tools:
    - name: 'api'
      permission_level: 'sandbox_only'
      allowed_operations:
        - 'read'
        - 'list'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            
            assert guard.check_tool_permission('api', 'read', 'sandbox_only') is True
            
            with pytest.raises(PolicyViolation, match="not in allowed list"):
                guard.check_tool_permission('api', 'write', 'sandbox_only')
        finally:
            os.unlink(temp_path)


class TestRiskLevelDetection:
    """Test risk level detection logic"""
    
    def test_check_risk_level_no_policies(self):
        """Should return low_risk when no policies loaded"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.check_risk_level(['any/file.py']) == 'low_risk'
    
    def test_check_risk_level_high_risk_patterns(self):
        """Should detect high risk file patterns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
risk_routing:
  risk_scoring:
    file_patterns:
      high_risk:
        - 'config/database.yml'
        - '*.env'
      medium_risk:
        - 'migrations/**'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            
            assert guard.check_risk_level(['config/database.yml']) == 'high_risk'
            assert guard.check_risk_level(['.env']) == 'high_risk'
            assert guard.check_risk_level(['migrations/001_init.sql']) == 'medium_risk'
            assert guard.check_risk_level(['src/utils.py']) == 'low_risk'
        finally:
            os.unlink(temp_path)


class TestHumanApprovalRequirement:
    """Test human approval requirement logic"""
    
    def test_requires_human_approval_no_policies(self):
        """Should not require approval when no policies loaded"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard.requires_human_approval(['any'], 'high_risk') is False
    
    def test_requires_human_approval_auto_approve_labels(self):
        """Should auto-approve whitelisted labels"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
risk_routing:
  auto_approve_labels:
    - 'documentation'
    - 'tests'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.requires_human_approval(['documentation'], 'high_risk') is False
            assert guard.requires_human_approval(['tests'], 'medium_risk') is False
        finally:
            os.unlink(temp_path)
    
    def test_requires_human_approval_high_risk_labels(self):
        """Should require approval for high risk labels"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
risk_routing:
  high_risk_labels:
    - 'security'
    - 'production'
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.requires_human_approval(['security'], 'low_risk') is True
            assert guard.requires_human_approval(['production'], 'low_risk') is True
        finally:
            os.unlink(temp_path)
    
    def test_requires_human_approval_high_risk_level(self):
        """Should require approval for high risk level"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
risk_routing:
  require_human_signoff: true
""")
            f.flush()
            temp_path = f.name
        
        try:
            guard = PolicyGuard(policies_path=temp_path)
            assert guard.requires_human_approval([], 'high_risk') is True
            assert guard.requires_human_approval([], 'low_risk') is False
        finally:
            os.unlink(temp_path)


class TestPatternMatching:
    """Test pattern matching utilities"""
    
    def test_match_pattern_exact(self):
        """Should match exact file paths"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._match_pattern('config.yaml', 'config.yaml') is True
        assert guard._match_pattern('config.yml', 'config.yaml') is False
    
    def test_match_pattern_wildcard(self):
        """Should match wildcard patterns"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._match_pattern('test.py', '*.py') is True
        assert guard._match_pattern('test.js', '*.py') is False
    
    def test_match_pattern_double_wildcard(self):
        """Should match double wildcard patterns"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._match_pattern('src/utils/helper.py', 'src/**/*.py') is True
        assert guard._match_pattern('tests/unit/test_main.py', 'tests/**/*.py') is True
        assert guard._match_pattern('config/db/settings.yml', 'config/**/*.yml') is True
    
    def test_match_domain_exact(self):
        """Should match exact domains"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._match_domain('api.github.com', 'api.github.com') is True
        assert guard._match_domain('github.com', 'api.github.com') is False
    
    def test_match_domain_wildcard(self):
        """Should match wildcard domain patterns"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._match_domain('api.example.com', '*.example.com') is True
        assert guard._match_domain('example.com', '*.example.com') is True
        assert guard._match_domain('example.org', '*.example.com') is False


class TestPermissionLevels:
    """Test permission level hierarchy"""
    
    def test_has_permission_level_hierarchy(self):
        """Should enforce permission level hierarchy"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        
        assert guard._has_permission_level('prod_full_access', 'sandbox_only') is True
        assert guard._has_permission_level('prod_full_access', 'staging_access') is True
        assert guard._has_permission_level('prod_full_access', 'prod_low_risk') is True
        assert guard._has_permission_level('prod_full_access', 'prod_full_access') is True
        
        assert guard._has_permission_level('sandbox_only', 'staging_access') is False
        assert guard._has_permission_level('sandbox_only', 'prod_full_access') is False
    
    def test_has_permission_level_invalid(self):
        """Should handle invalid permission levels"""
        guard = PolicyGuard(policies_path='/nonexistent/policies.yaml')
        assert guard._has_permission_level('invalid_level', 'sandbox_only') is False
        assert guard._has_permission_level('sandbox_only', 'invalid_level') is False


class TestGlobalPolicyGuard:
    """Test global policy guard singleton"""
    
    def test_get_policy_guard_singleton(self):
        """Should return same instance on multiple calls"""
        guard1 = get_policy_guard()
        guard2 = get_policy_guard()
        assert guard1 is guard2


class TestGuardedDecorator:
    """Test @guarded decorator"""
    
    def test_guarded_decorator_file_access(self):
        """Should enforce file access checks via decorator"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  file_access:
    deny:
      - '*.env'
""")
            f.flush()
            temp_path = f.name
        
        try:
            with patch('governance.policy_guard._policy_guard', PolicyGuard(policies_path=temp_path)):
                @guarded
                def test_func(ctx=None):
                    return "success"
                
                result = test_func(ctx={'file_path': 'config.yaml'})
                assert result == "success"
                
                with pytest.raises(PolicyViolation):
                    test_func(ctx={'file_path': '.env'})
        finally:
            os.unlink(temp_path)
    
    def test_guarded_decorator_network_access(self):
        """Should enforce network access checks via decorator"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
resource_sandbox:
  network:
    allow_domains:
      - 'api.github.com'
""")
            f.flush()
            temp_path = f.name
        
        try:
            with patch('governance.policy_guard._policy_guard', PolicyGuard(policies_path=temp_path)):
                @guarded
                def test_func(ctx=None):
                    return "success"
                
                result = test_func(ctx={'domain': 'api.github.com'})
                assert result == "success"
                
                with pytest.raises(PolicyViolation):
                    test_func(ctx={'domain': 'malicious.com'})
        finally:
            os.unlink(temp_path)
