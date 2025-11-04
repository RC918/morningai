"""Test governance risk routing and decision logic"""
import pytest
import tempfile
import yaml
import os


@pytest.fixture
def risk_routing_policy():
    """Create a policy file with comprehensive risk routing rules"""
    policy_content = {
        'risk_routing': {
            'auto_approve_labels': ['documentation', 'tests', 'refactor'],
            'high_risk_labels': ['production', 'database', 'security', 'migration'],
            'require_human_signoff': True,
            'risk_scoring': {
                'file_patterns': {
                    'high_risk': [
                        '**/migrations/**',
                        '**/production/**',
                        '**/config/production/**',
                        '**/.env.production',
                        '**/database/schema/**'
                    ],
                    'medium_risk': [
                        '**/config/**',
                        '**/settings/**',
                        '**/api/**',
                        '**/.env.staging'
                    ],
                    'low_risk': [
                        '**/tests/**',
                        '**/docs/**',
                        '**/*.md',
                        '**/*.test.js'
                    ]
                },
                'thresholds': {
                    'high_risk_score': 80,
                    'medium_risk_score': 50,
                    'low_risk_score': 20
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


class TestRiskLevelDetection:
    """Test risk level detection based on file patterns"""
    
    def test_high_risk_migration_files(self, risk_routing_policy, monkeypatch):
        """Test that migration files are detected as high risk"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/migrations/001_init.sql']) == 'high_risk'
        assert guard.check_risk_level(['/app/migrations/002_add_users.sql']) == 'high_risk'
        assert guard.check_risk_level(['/database/migrations/schema.sql']) == 'high_risk'
    
    def test_high_risk_production_files(self, risk_routing_policy, monkeypatch):
        """Test that production files are detected as high risk"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/production/deploy.sh']) == 'high_risk'
        assert guard.check_risk_level(['/config/production/settings.py']) == 'high_risk'
        assert guard.check_risk_level(['/app/.env.production']) == 'high_risk'
    
    def test_medium_risk_config_files(self, risk_routing_policy, monkeypatch):
        """Test that config files are detected as medium risk"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/config/settings.py']) == 'medium_risk'
        assert guard.check_risk_level(['/app/api/routes.py']) == 'medium_risk'
        assert guard.check_risk_level(['/app/.env.staging']) == 'medium_risk'
    
    def test_low_risk_documentation_files(self, risk_routing_policy, monkeypatch):
        """Test that documentation files are detected as low risk"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/docs/README.md']) == 'low_risk'
        assert guard.check_risk_level(['/app/tests/test_api.py']) == 'low_risk'
        assert guard.check_risk_level(['/app/src/utils.js']) == 'low_risk'
    
    def test_multiple_files_highest_risk_wins(self, risk_routing_policy, monkeypatch):
        """Test that when multiple files are provided, highest risk level is returned"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        files = [
            '/app/docs/README.md',  # low
            '/app/migrations/001_init.sql',  # high
            '/app/tests/test.py'  # low
        ]
        assert guard.check_risk_level(files) == 'high_risk'
        
        files = [
            '/app/docs/README.md',  # low
            '/app/config/settings.py',  # medium
            '/app/tests/test.py'  # low
        ]
        assert guard.check_risk_level(files) == 'medium_risk'
    
    def test_empty_file_list_returns_low_risk(self, risk_routing_policy, monkeypatch):
        """Test that empty file list returns low risk"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level([]) == 'low_risk'


class TestHumanApprovalRequirements:
    """Test human approval requirement logic"""
    
    def test_auto_approve_labels_bypass_approval(self, risk_routing_policy, monkeypatch):
        """Test that auto-approve labels bypass human approval"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval(['documentation'], 'high_risk') is False
        assert guard.requires_human_approval(['tests'], 'high_risk') is False
        assert guard.requires_human_approval(['refactor'], 'medium_risk') is False
        
        assert guard.requires_human_approval(['documentation', 'production'], 'high_risk') is False
    
    def test_high_risk_labels_require_approval(self, risk_routing_policy, monkeypatch):
        """Test that high-risk labels always require approval"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval(['production'], 'low_risk') is True
        assert guard.requires_human_approval(['database'], 'low_risk') is True
        assert guard.requires_human_approval(['security'], 'medium_risk') is True
        assert guard.requires_human_approval(['migration'], 'high_risk') is True
    
    def test_high_risk_level_requires_approval(self, risk_routing_policy, monkeypatch):
        """Test that high risk level requires approval"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval([], 'high_risk') is True
        
        assert guard.requires_human_approval([], 'medium_risk') is False
        assert guard.requires_human_approval([], 'low_risk') is False
    
    def test_label_priority_over_risk_level(self, risk_routing_policy, monkeypatch):
        """Test that labels take priority over risk level"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval(['documentation'], 'high_risk') is False
        
        assert guard.requires_human_approval(['production'], 'low_risk') is True
    
    def test_no_labels_no_high_risk_no_approval(self, risk_routing_policy, monkeypatch):
        """Test that no labels and low/medium risk don't require approval"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval([], 'low_risk') is False
        assert guard.requires_human_approval([], 'medium_risk') is False


class TestRiskScoringEdgeCases:
    """Test edge cases in risk scoring"""
    
    def test_pattern_matching_with_wildcards(self, risk_routing_policy, monkeypatch):
        """Test that wildcard patterns match correctly"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/migrations/test.sql']) == 'high_risk'
        assert guard.check_risk_level(['/app/production/deploy.sh']) == 'high_risk'
        
        assert guard.check_risk_level(['/app/config/production/db.yaml']) == 'high_risk'
    
    def test_case_sensitive_pattern_matching(self, risk_routing_policy, monkeypatch):
        """Test that pattern matching is case-sensitive"""
        monkeypatch.setenv('POLICIES_PATH', risk_routing_policy)
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/migrations/test.sql']) == 'high_risk'
        
        assert guard.check_risk_level(['/app/MIGRATIONS/test.sql']) == 'low_risk'
    
    def test_no_policy_defaults_to_low_risk(self, monkeypatch):
        """Test that missing policy defaults to low risk"""
        monkeypatch.setenv('POLICIES_PATH', '/tmp/nonexistent_policy.yaml')
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.check_risk_level(['/app/migrations/001_init.sql']) == 'low_risk'
        assert guard.check_risk_level(['/app/production/deploy.sh']) == 'low_risk'
    
    def test_no_policy_no_approval_required(self, monkeypatch):
        """Test that missing policy doesn't require approval"""
        monkeypatch.setenv('POLICIES_PATH', '/tmp/nonexistent_policy.yaml')
        
        from governance.policy_guard import PolicyGuard
        
        guard = PolicyGuard()
        
        assert guard.requires_human_approval(['production'], 'high_risk') is False
        assert guard.requires_human_approval([], 'high_risk') is False
