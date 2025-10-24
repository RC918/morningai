"""Comprehensive tests for governance framework"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../handoff/20250928/40_App/orchestrator'))

from governance.policy_guard import PolicyGuard, PolicyViolation
from governance.cost_tracker import CostTracker, CostBudgetExceeded
from governance.reputation_engine import ReputationEngine
from governance.permission_checker import PermissionChecker, PermissionDenied
from governance.violation_detector import ViolationDetector, ViolationError

POLICIES_PATH = os.path.join(os.path.dirname(__file__), '../config/policies.yaml')


class TestPolicyGuard:
    """Test PolicyGuard middleware"""
    
    def test_file_access_allow(self):
        """Test file access allow patterns"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.check_file_access('./apps/web/index.js') == True
        assert guard.check_file_access('./docs/README.md') == True
    
    def test_file_access_deny(self):
        """Test file access deny patterns"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        with pytest.raises(PolicyViolation):
            guard.check_file_access('./secrets/api_key.txt')
        
        with pytest.raises(PolicyViolation):
            guard.check_file_access('.env')
    
    def test_network_access_allow(self):
        """Test network access allow patterns"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.check_network_access('api.github.com') == True
        assert guard.check_network_access('registry.npmjs.org') == True
    
    def test_network_access_deny(self):
        """Test network access deny patterns"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        with pytest.raises(PolicyViolation):
            guard.check_network_access('malicious-site.com')
    
    def test_tool_permission_sandbox(self):
        """Test tool permissions for sandbox_only level"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.check_tool_permission('Git_Tool', 'commit', 'sandbox_only') == True
        
        with pytest.raises(PolicyViolation):
            guard.check_tool_permission('Render_Tool', 'deploy', 'sandbox_only')
    
    def test_tool_permission_prod(self):
        """Test tool permissions for prod_full_access level"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.check_tool_permission('Render_Tool', 'get_status', 'prod_full_access') == True
    
    def test_risk_level_detection(self):
        """Test risk level detection"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.check_risk_level(['./docs/README.md']) == 'low_risk'
        assert guard.check_risk_level(['./migrations/001_init.sql']) == 'high_risk'
        assert guard.check_risk_level(['./production/config.yaml']) == 'high_risk'
    
    def test_human_approval_required(self):
        """Test human approval requirement"""
        guard = PolicyGuard(policies_path=POLICIES_PATH)
        
        assert guard.requires_human_approval(['db_migration'], 'high_risk') == True
        assert guard.requires_human_approval(['docs_only'], 'low_risk') == False


class TestCostTracker:
    """Test CostTracker system"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.incrbyfloat.return_value = 0.0
        return redis_mock
    
    def test_track_usage(self, mock_redis):
        """Test usage tracking"""
        with patch('redis.from_url', return_value=mock_redis):
            tracker = CostTracker(policies_path=POLICIES_PATH)
            tracker.track_usage('trace-123', 1000, 0.03, model='gpt-4')
            
            assert mock_redis.hincrby.called or mock_redis.hincrbyfloat.called
    
    def test_estimate_cost(self):
        """Test cost estimation"""
        tracker = CostTracker(policies_path=POLICIES_PATH)
        
        cost_gpt4 = tracker.estimate_cost(1000, model='gpt-4')
        assert cost_gpt4 == 0.03
        
        cost_gpt35 = tracker.estimate_cost(1000, model='gpt-3.5-turbo')
        assert cost_gpt35 == 0.0015
    
    def test_budget_enforcement(self, mock_redis):
        """Test budget enforcement"""
        mock_redis.hget.side_effect = lambda key, field: '150000' if field == 'tokens' else ('6.0' if field == 'usd' else '1')
        
        with patch('redis.from_url', return_value=mock_redis):
            tracker = CostTracker(policies_path=POLICIES_PATH)
            
            with pytest.raises(CostBudgetExceeded):
                tracker.enforce_budget('trace-123', period='daily')
    
    def test_budget_status(self, mock_redis):
        """Test budget status reporting"""
        mock_redis.hget.side_effect = lambda key, field: '50000' if field == 'tokens' else ('2.5' if field == 'usd' else '10')
        
        with patch('redis.from_url', return_value=mock_redis):
            tracker = CostTracker(policies_path=POLICIES_PATH)
            status = tracker.get_budget_status('trace-123', period='daily')
            
            assert status['within_budget'] == True
            assert status['alert_level'] == 'ok'
            assert status['usage']['tokens'] == 50000
            assert status['usage']['usd'] == 2.5


class TestReputationEngine:
    """Test ReputationEngine"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        supabase_mock = MagicMock()
        
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            'agent_id': 'agent-123',
            'agent_type': 'dev_agent',
            'reputation_score': 100,
            'permission_level': 'sandbox_only'
        }])
        
        supabase_mock.table.return_value = table_mock
        supabase_mock.rpc.return_value = table_mock
        
        return supabase_mock
    
    def test_get_or_create_agent(self, mock_supabase):
        """Test agent creation"""
        engine = ReputationEngine(supabase_client=mock_supabase)
        agent_id = engine.get_or_create_agent('dev_agent')
        
        assert agent_id == 'agent-123'
    
    def test_record_event(self, mock_supabase):
        """Test event recording"""
        engine = ReputationEngine(supabase_client=mock_supabase)
        
        result = engine.record_event(
            'agent-123',
            'pr_merged_without_revert',
            trace_id='trace-123',
            reason='PR merged successfully'
        )
        
        assert result == True
    
    def test_get_reputation_score(self, mock_supabase):
        """Test reputation score retrieval"""
        engine = ReputationEngine(supabase_client=mock_supabase)
        score = engine.get_reputation_score('agent-123')
        
        assert score == 100
    
    def test_get_permission_level(self, mock_supabase):
        """Test permission level retrieval"""
        engine = ReputationEngine(supabase_client=mock_supabase)
        level = engine.get_permission_level('agent-123')
        
        assert level == 'sandbox_only'


class TestPermissionChecker:
    """Test PermissionChecker"""
    
    @pytest.fixture
    def mock_reputation_engine(self):
        """Mock ReputationEngine"""
        engine_mock = MagicMock()
        engine_mock.get_permission_level.return_value = 'sandbox_only'
        engine_mock.get_reputation_score.return_value = 50
        engine_mock.get_allowed_operations.return_value = ['read_file', 'write_file', 'run_tests']
        return engine_mock
    
    def test_check_permission_allowed(self, mock_reputation_engine):
        """Test permission check for allowed operation"""
        checker = PermissionChecker(reputation_engine=mock_reputation_engine)
        
        assert checker.check_permission('agent-123', 'read_file') == True
    
    def test_check_permission_denied(self, mock_reputation_engine):
        """Test permission check for denied operation"""
        checker = PermissionChecker(reputation_engine=mock_reputation_engine)
        
        with pytest.raises(PermissionDenied):
            checker.check_permission('agent-123', 'deploy_prod')
    
    def test_can_access_environment(self, mock_reputation_engine):
        """Test environment access check"""
        checker = PermissionChecker(reputation_engine=mock_reputation_engine)
        
        assert checker.can_access_environment('agent-123', 'sandbox') == True
        assert checker.can_access_environment('agent-123', 'production') == False
    
    def test_get_permission_summary(self, mock_reputation_engine):
        """Test permission summary"""
        checker = PermissionChecker(reputation_engine=mock_reputation_engine)
        summary = checker.get_permission_summary('agent-123')
        
        assert summary['permission_level'] == 'sandbox_only'
        assert summary['reputation_score'] == 50
        assert 'read_file' in summary['allowed_operations']
        assert summary['environment_access']['sandbox'] == True
        assert summary['environment_access']['production'] == False


class TestViolationDetector:
    """Test ViolationDetector"""
    
    @pytest.fixture
    def mock_policies(self):
        """Mock policies for ViolationDetector"""
        import yaml
        with open(POLICIES_PATH, 'r') as f:
            return yaml.safe_load(f)
    
    def test_check_secrets_access(self, mock_policies):
        """Test secrets access detection"""
        detector = ViolationDetector(policies=mock_policies)
        
        with pytest.raises(ViolationError):
            detector.check_secrets_access('export API_KEY=sk-1234567890')
    
    def test_check_dangerous_operations(self, mock_policies):
        """Test dangerous operations detection"""
        detector = ViolationDetector(policies=mock_policies)
        
        with pytest.raises(ViolationError):
            detector.check_dangerous_operations('rm -rf /')
    
    def test_check_file_access_secrets(self, mock_policies):
        """Test file access to secrets"""
        detector = ViolationDetector(policies=mock_policies)
        
        with pytest.raises(ViolationError):
            detector.check_file_access('.env')
        
        with pytest.raises(ViolationError):
            detector.check_file_access('./secrets/api_key.pem')
    
    def test_sanitize_content(self, mock_policies):
        """Test content sanitization"""
        detector = ViolationDetector(policies=mock_policies)
        
        content = "API_KEY=sk-1234567890 PASSWORD=secret123"
        sanitized = detector.sanitize_content(content)
        
        assert 'sk-1234567890' not in sanitized
        assert 'secret123' not in sanitized
        assert '<REDACTED>' in sanitized


class TestIntegration:
    """Integration tests for governance system"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.incrbyfloat.return_value = 0.0
        return redis_mock
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        supabase_mock = MagicMock()
        
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[{
            'agent_id': 'agent-123',
            'agent_type': 'dev_agent',
            'reputation_score': 150,
            'permission_level': 'prod_low_risk'
        }])
        
        supabase_mock.table.return_value = table_mock
        supabase_mock.rpc.return_value = table_mock
        
        return supabase_mock
    
    def test_full_governance_flow(self, mock_redis, mock_supabase):
        """Test complete governance flow"""
        agent_data = {
            'agent_id': 'agent-123',
            'agent_type': 'dev_agent',
            'reputation_score': 150,
            'permission_level': 'prod_low_risk'
        }
        
        table_mock = MagicMock()
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.single.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.execute.return_value = MagicMock(data=[agent_data])
        
        single_mock = MagicMock()
        single_mock.execute.return_value = MagicMock(data=agent_data)
        table_mock.single.return_value = single_mock
        
        mock_supabase.table.return_value = table_mock
        mock_supabase.rpc.return_value = table_mock
        
        with patch('redis.from_url', return_value=mock_redis):
            policy_guard = PolicyGuard(policies_path=POLICIES_PATH)
            cost_tracker = CostTracker(policies_path=POLICIES_PATH)
            reputation_engine = ReputationEngine(supabase_client=mock_supabase, policies_path=POLICIES_PATH)
            permission_checker = PermissionChecker(reputation_engine=reputation_engine)
            
            agent_id = reputation_engine.get_or_create_agent('dev_agent')
            assert agent_id == 'agent-123'
            
            assert policy_guard.check_file_access('./apps/web/index.js') == True
            
            cost_tracker.track_usage('trace-123', 1000, 0.03)
            
            assert permission_checker.check_permission(agent_id, 'create_prod_pr') == True
            
            reputation_engine.record_event(
                agent_id,
                'pr_merged_without_revert',
                trace_id='trace-123'
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
