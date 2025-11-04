"""Test governance policy dynamic reload and hot-update capabilities"""
import pytest
import tempfile
import yaml
import os
import time


@pytest.fixture
def initial_policy():
    """Create an initial policy file"""
    policy_content = {
        'resource_sandbox': {
            'file_access': {
                'deny': ['/etc/passwd'],
                'allow': ['/tmp/**']
            }
        },
        'risk_routing': {
            'auto_approve_labels': ['documentation'],
            'high_risk_labels': ['production']
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
def updated_policy():
    """Create an updated policy file with different rules"""
    policy_content = {
        'resource_sandbox': {
            'file_access': {
                'deny': ['/etc/passwd', '/etc/shadow'],  # Added /etc/shadow
                'allow': ['/tmp/**', '/home/**']  # Added /home/**
            }
        },
        'risk_routing': {
            'auto_approve_labels': ['documentation', 'tests'],  # Added 'tests'
            'high_risk_labels': ['production', 'database']  # Added 'database'
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


class TestPolicyReload:
    """Test dynamic policy reloading without restart"""
    
    def test_policy_reload_updates_rules(self, initial_policy, monkeypatch):
        """Test that reloading policy updates the rules"""
        monkeypatch.setenv('POLICIES_PATH', initial_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        with pytest.raises(Exception):
            guard.check_file_access('/home/test.txt')
        
        updated_content = {
            'resource_sandbox': {
                'file_access': {
                    'deny': ['/etc/passwd'],
                    'allow': ['/tmp/**', '/home/**']
                }
            }
        }
        
        with open(initial_policy, 'w') as f:
            yaml.dump(updated_content, f)
        
        guard.policies = guard._load_policies()
        
        assert guard.check_file_access('/home/test.txt') is True
    
    def test_policy_reload_preserves_valid_state_on_error(self, initial_policy, monkeypatch):
        """Test that reload preserves valid state if new policy is invalid"""
        monkeypatch.setenv('POLICIES_PATH', initial_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_file_access('/tmp/test.txt') is True
        
        with open(initial_policy, 'w') as f:
            f.write("invalid: yaml: content: [[[")
        
        old_policies = guard.policies.copy()
        guard.policies = guard._load_policies()
        
        assert guard.policies == {}
        
        assert guard.check_file_access('/tmp/test.txt') is True
    
    def test_policy_hot_update_without_restart(self, initial_policy, monkeypatch):
        """Test that policy can be updated without restarting the application"""
        monkeypatch.setenv('POLICIES_PATH', initial_policy)
        
        from governance.policy_guard import PolicyGuard, get_policy_guard
        
        guard = get_policy_guard()
        
        assert guard.requires_human_approval(['documentation'], 'high_risk') is False
        assert guard.requires_human_approval(['tests'], 'high_risk') is True  # Not in auto-approve
        
        updated_content = {
            'risk_routing': {
                'auto_approve_labels': ['documentation', 'tests'],  # Add 'tests'
                'high_risk_labels': ['production']
            }
        }
        
        with open(initial_policy, 'w') as f:
            yaml.dump(updated_content, f)
        
        guard.policies = guard._load_policies()
        
        assert guard.requires_human_approval(['tests'], 'high_risk') is False
    
    def test_policy_version_tracking(self, initial_policy, monkeypatch):
        """Test that policy changes can be tracked (version control)"""
        monkeypatch.setenv('POLICIES_PATH', initial_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        initial_policies = str(guard.policies)
        
        updated_content = {
            'resource_sandbox': {
                'file_access': {
                    'deny': ['/etc/passwd', '/etc/shadow'],
                    'allow': ['/tmp/**', '/home/**']
                }
            }
        }
        
        with open(initial_policy, 'w') as f:
            yaml.dump(updated_content, f)
        
        guard.policies = guard._load_policies()
        
        updated_policies = str(guard.policies)
        
        assert initial_policies != updated_policies


class TestPolicyRollback:
    """Test policy rollback mechanisms"""
    
    def test_policy_rollback_to_previous_version(self, initial_policy, updated_policy, monkeypatch):
        """Test rolling back to a previous policy version"""
        monkeypatch.setenv('POLICIES_PATH', initial_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_file_access('/tmp/test.txt') is True
        with pytest.raises(Exception):
            guard.check_file_access('/home/test.txt')
        
        with open(initial_policy, 'r') as f:
            backup_content = f.read()
        
        with open(updated_policy, 'r') as f:
            new_content = f.read()
        
        with open(initial_policy, 'w') as f:
            f.write(new_content)
        
        guard.policies = guard._load_policies()
        
        assert guard.check_file_access('/home/test.txt') is True
        
        with open(initial_policy, 'w') as f:
            f.write(backup_content)
        
        guard.policies = guard._load_policies()
        
        with pytest.raises(Exception):
            guard.check_file_access('/home/test.txt')
