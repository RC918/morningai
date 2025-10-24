"""Test governance policy authorization with POLICIES_PATH support"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path


@pytest.fixture
def valid_policy_file():
    """Create a temporary valid policy file"""
    policy_content = {
        'resource_sandbox': {
            'file_access': {
                'deny': ['/etc/passwd', '/etc/shadow'],
                'allow': ['/tmp/**', '/home/**']
            },
            'network': {
                'allow_domains': ['api.example.com', '*.github.com']
            }
        },
        'capability_constraints': {
            'restricted_tools': [
                {
                    'name': 'deploy',
                    'permission_level': 'prod_full_access',
                    'denied_operations': ['delete_database']
                }
            ]
        },
        'risk_routing': {
            'auto_approve_labels': ['documentation', 'tests'],
            'high_risk_labels': ['production', 'database'],
            'require_human_signoff': True,
            'risk_scoring': {
                'file_patterns': {
                    'high_risk': ['**/migrations/**', '**/production/**'],
                    'medium_risk': ['**/config/**', '**/settings/**']
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy_content, f)
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except:
        pass


@pytest.fixture
def invalid_policy_file():
    """Create a temporary invalid YAML file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [[[")
        temp_path = f.name
    
    yield temp_path
    
    try:
        os.unlink(temp_path)
    except:
        pass


class TestPolicyGuardWithEnvironmentVariable:
    """Test PolicyGuard with POLICIES_PATH environment variable"""
    
    def test_policy_exists_and_loads_correctly(self, valid_policy_file, monkeypatch):
        """Test scenario 1: Policy file exists and loads correctly"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.policies_path == valid_policy_file
        assert guard.policies is not None
        assert 'resource_sandbox' in guard.policies
        assert 'capability_constraints' in guard.policies
        assert 'risk_routing' in guard.policies
        
        assert guard.check_file_access('/tmp/test.txt') is True
        
        with pytest.raises(Exception) as exc_info:
            guard.check_file_access('/etc/passwd')
        assert 'denied' in str(exc_info.value).lower()
        
        assert guard.check_network_access('api.example.com') is True
        assert guard.check_network_access('api.github.com') is True
        
        with pytest.raises(Exception) as exc_info:
            guard.check_network_access('malicious.com')
        assert 'denied' in str(exc_info.value).lower()
        
        risk_level = guard.check_risk_level(['/app/migrations/001_init.sql'])
        assert risk_level == 'high_risk'
        
        risk_level = guard.check_risk_level(['/app/config/settings.py'])
        assert risk_level == 'medium_risk'
        
        risk_level = guard.check_risk_level(['/app/src/utils.py'])
        assert risk_level == 'low_risk'
    
    def test_policy_missing_uses_default(self, monkeypatch):
        """Test scenario 2: POLICIES_PATH points to non-existent file, uses default"""
        non_existent_path = '/tmp/non_existent_policy_12345.yaml'
        monkeypatch.setenv('POLICIES_PATH', non_existent_path)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.policies_path == non_existent_path
        assert guard.policies == {}
        
        assert guard.check_file_access('/etc/passwd') is True
        assert guard.check_file_access('/tmp/test.txt') is True
        
        assert guard.check_network_access('any-domain.com') is True
        
        risk_level = guard.check_risk_level(['/app/migrations/001_init.sql'])
        assert risk_level == 'low_risk'
    
    def test_policy_invalid_yaml_uses_default(self, invalid_policy_file, monkeypatch):
        """Test scenario 3: POLICIES_PATH points to invalid YAML, uses default"""
        monkeypatch.setenv('POLICIES_PATH', invalid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.policies_path == invalid_policy_file
        assert guard.policies == {}
        
        assert guard.check_file_access('/etc/passwd') is True
        assert guard.check_file_access('/tmp/test.txt') is True
        
        assert guard.check_network_access('any-domain.com') is True
        
        risk_level = guard.check_risk_level(['/app/migrations/001_init.sql'])
        assert risk_level == 'low_risk'
    
    def test_no_policies_path_env_uses_default_location(self, monkeypatch):
        """Test that when POLICIES_PATH is not set, default location is used"""
        monkeypatch.delenv('POLICIES_PATH', raising=False)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert 'config/policies.yaml' in guard.policies_path
    
    def test_explicit_policies_path_overrides_env(self, valid_policy_file, monkeypatch):
        """Test that explicit policies_path parameter overrides environment variable"""
        monkeypatch.setenv('POLICIES_PATH', '/tmp/wrong_path.yaml')
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard(policies_path=valid_policy_file)
        
        assert guard.policies_path == valid_policy_file
        assert guard.policies is not None
        assert 'resource_sandbox' in guard.policies


class TestPolicyGuardToolPermissions:
    """Test tool permission checking with policies"""
    
    def test_tool_permission_with_sufficient_level(self, valid_policy_file, monkeypatch):
        """Test tool access with sufficient permission level"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        result = guard.check_tool_permission('deploy', 'execute', 'prod_full_access')
        assert result is True
    
    def test_tool_permission_with_insufficient_level(self, valid_policy_file, monkeypatch):
        """Test tool access with insufficient permission level"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        with pytest.raises(Exception) as exc_info:
            guard.check_tool_permission('deploy', 'execute', 'sandbox_only')
        assert 'denied' in str(exc_info.value).lower()
        assert 'prod_full_access' in str(exc_info.value)
    
    def test_tool_permission_denied_operation(self, valid_policy_file, monkeypatch):
        """Test denied operation even with sufficient permission level"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        with pytest.raises(Exception) as exc_info:
            guard.check_tool_permission('deploy', 'delete_database', 'prod_full_access')
        assert 'denied' in str(exc_info.value).lower()
        assert 'delete_database' in str(exc_info.value)


class TestPolicyGuardRiskRouting:
    """Test risk routing and human approval requirements"""
    
    def test_auto_approve_labels(self, valid_policy_file, monkeypatch):
        """Test auto-approve labels bypass human approval"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        requires_approval = guard.requires_human_approval(['documentation'], 'low_risk')
        assert requires_approval is False
        
        requires_approval = guard.requires_human_approval(['tests'], 'medium_risk')
        assert requires_approval is False
    
    def test_high_risk_labels_require_approval(self, valid_policy_file, monkeypatch):
        """Test high-risk labels require human approval"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        requires_approval = guard.requires_human_approval(['production'], 'low_risk')
        assert requires_approval is True
        
        requires_approval = guard.requires_human_approval(['database'], 'medium_risk')
        assert requires_approval is True
    
    def test_high_risk_level_requires_approval(self, valid_policy_file, monkeypatch):
        """Test high risk level requires human approval"""
        monkeypatch.setenv('POLICIES_PATH', valid_policy_file)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        requires_approval = guard.requires_human_approval([], 'high_risk')
        assert requires_approval is True
        
        requires_approval = guard.requires_human_approval([], 'medium_risk')
        assert requires_approval is False
        
        requires_approval = guard.requires_human_approval([], 'low_risk')
        assert requires_approval is False
