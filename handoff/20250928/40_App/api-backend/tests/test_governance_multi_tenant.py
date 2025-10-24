"""Test governance multi-tenant policy isolation and inheritance"""
import pytest
import tempfile
import yaml
import os


@pytest.fixture
def multi_tenant_policy():
    """Create a policy file with tenant-specific configurations"""
    policy_content = {
        'global_policy': {
            'default_permission_level': 'sandbox_only',
            'max_cost_per_day': 100.0,
            'allowed_tools': ['read', 'write', 'search']
        },
        'tenant_policies': {
            'tenant_a': {
                'permission_level': 'prod_full_access',
                'max_cost_per_day': 500.0,
                'allowed_tools': ['read', 'write', 'search', 'deploy', 'database'],
                'custom_rules': {
                    'allow_production_access': True,
                    'require_approval_threshold': 1000.0
                }
            },
            'tenant_b': {
                'permission_level': 'staging_access',
                'max_cost_per_day': 200.0,
                'allowed_tools': ['read', 'write', 'search', 'test'],
                'custom_rules': {
                    'allow_production_access': False,
                    'require_approval_threshold': 100.0
                }
            }
        },
        'resource_sandbox': {
            'file_access': {
                'deny': ['/etc/passwd'],
                'allow': ['/tmp/**', '/home/**']
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


class TestTenantPolicyIsolation:
    """Test that tenant policies are properly isolated"""
    
    def test_tenant_a_cannot_affect_tenant_b(self, multi_tenant_policy, monkeypatch):
        """Test that tenant A's policy doesn't affect tenant B"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard_a = PolicyGuard()
        
        guard_b = PolicyGuard()
        
        assert guard_a.policies is not None
        assert guard_b.policies is not None
        
        assert guard_a.check_file_access('/tmp/test.txt') is True
        assert guard_b.check_file_access('/tmp/test.txt') is True
        
        with pytest.raises(Exception):
            guard_a.check_file_access('/etc/passwd')
        
        with pytest.raises(Exception):
            guard_b.check_file_access('/etc/passwd')
    
    def test_tenant_specific_permission_levels(self, multi_tenant_policy, monkeypatch):
        """Test that tenants have different permission levels"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        tenant_policies = guard.policies.get('tenant_policies', {})
        assert 'tenant_a' in tenant_policies
        assert 'tenant_b' in tenant_policies
        
        assert tenant_policies['tenant_a']['permission_level'] == 'prod_full_access'
        
        assert tenant_policies['tenant_b']['permission_level'] == 'staging_access'
    
    def test_tenant_cost_limits_are_isolated(self, multi_tenant_policy, monkeypatch):
        """Test that tenant cost limits are separate"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        tenant_policies = guard.policies.get('tenant_policies', {})
        
        assert tenant_policies['tenant_a']['max_cost_per_day'] == 500.0
        
        assert tenant_policies['tenant_b']['max_cost_per_day'] == 200.0
        
        global_policy = guard.policies.get('global_policy', {})
        assert global_policy['max_cost_per_day'] == 100.0
    
    def test_tenant_tool_access_isolation(self, multi_tenant_policy, monkeypatch):
        """Test that tenants have different tool access"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        tenant_policies = guard.policies.get('tenant_policies', {})
        
        tenant_a_tools = tenant_policies['tenant_a']['allowed_tools']
        assert 'deploy' in tenant_a_tools
        assert 'database' in tenant_a_tools
        
        tenant_b_tools = tenant_policies['tenant_b']['allowed_tools']
        assert 'deploy' not in tenant_b_tools
        assert 'database' not in tenant_b_tools
        assert 'test' in tenant_b_tools


class TestTenantPolicyInheritance:
    """Test that tenant policies inherit from global policy"""
    
    def test_tenant_inherits_global_sandbox_rules(self, multi_tenant_policy, monkeypatch):
        """Test that tenants inherit global resource sandbox rules"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_file_access('/tmp/test.txt') is True
        assert guard.check_file_access('/home/test.txt') is True
        
        with pytest.raises(Exception):
            guard.check_file_access('/etc/passwd')
    
    def test_tenant_overrides_global_defaults(self, multi_tenant_policy, monkeypatch):
        """Test that tenant-specific settings override global defaults"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        global_policy = guard.policies.get('global_policy', {})
        tenant_a = guard.policies.get('tenant_policies', {}).get('tenant_a', {})
        
        assert global_policy['default_permission_level'] == 'sandbox_only'
        assert tenant_a['permission_level'] == 'prod_full_access'
        
        assert global_policy['max_cost_per_day'] == 100.0
        assert tenant_a['max_cost_per_day'] == 500.0


class TestTenantPolicyConflictResolution:
    """Test how conflicts between tenant and global policies are resolved"""
    
    def test_tenant_policy_takes_precedence_over_global(self, multi_tenant_policy, monkeypatch):
        """Test that tenant policy takes precedence when there's a conflict"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        global_policy = guard.policies.get('global_policy', {})
        tenant_a = guard.policies.get('tenant_policies', {}).get('tenant_a', {})
        
        assert 'allowed_tools' in global_policy
        assert 'allowed_tools' in tenant_a
        
        assert len(tenant_a['allowed_tools']) > len(global_policy['allowed_tools'])
    
    def test_missing_tenant_policy_uses_global(self, multi_tenant_policy, monkeypatch):
        """Test that missing tenant falls back to global policy"""
        monkeypatch.setenv('POLICIES_PATH', multi_tenant_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        tenant_policies = guard.policies.get('tenant_policies', {})
        
        assert 'tenant_c' not in tenant_policies
        
        global_policy = guard.policies.get('global_policy', {})
        assert global_policy is not None
        assert 'default_permission_level' in global_policy
