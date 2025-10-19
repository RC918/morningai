#!/usr/bin/env python3
"""
End-to-End Tests for Ops Agent OODA Loop
"""
import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ops_agent_ooda import OpsAgentOODA, create_ops_agent


class TestOpsAgentOODA:
    """Tests for OpsAgentOODA"""
    
    @pytest.fixture
    def ops_agent(self):
        """Create ops agent for testing"""
        return OpsAgentOODA(
            vercel_token="test_token",
            enable_monitoring=True,
            enable_alerts=True
        )
    
    def test_initialization(self, ops_agent):
        """Test OpsAgentOODA initialization"""
        assert ops_agent.deployment_tool is not None
        assert ops_agent.monitoring_tool is not None
        assert ops_agent.log_tool is not None
        assert ops_agent.alert_tool is not None
        assert ops_agent.context == {}
        assert ops_agent.task_history == []
    
    @pytest.mark.asyncio
    async def test_observe_phase(self, ops_agent):
        """Test OBSERVE phase"""
        observations = await ops_agent._observe()
        
        assert isinstance(observations, dict)
        assert 'system_metrics' in observations or observations == {}
    
    @pytest.mark.asyncio
    async def test_orient_phase(self, ops_agent):
        """Test ORIENT phase"""
        task = "Deploy application to production"
        observations = {}
        context = {}
        
        orientation = await ops_agent._orient(task, observations, context)
        
        assert isinstance(orientation, dict)
        assert 'task_type' in orientation
    
    @pytest.mark.asyncio
    async def test_decide_phase_deployment(self, ops_agent):
        """Test DECIDE phase for deployment task"""
        orientation = {'task_type': 'deployment'}
        
        decision = await ops_agent._decide(orientation)
        
        assert isinstance(decision, dict)
        assert decision['action'] == 'deploy'
        assert 'reason' in decision
    
    @pytest.mark.asyncio
    async def test_decide_phase_monitoring(self, ops_agent):
        """Test DECIDE phase for monitoring task"""
        orientation = {'task_type': 'monitoring'}
        
        decision = await ops_agent._decide(orientation)
        
        assert decision['action'] == 'monitor'
    
    @pytest.mark.asyncio
    async def test_act_phase_monitoring(self, ops_agent):
        """Test ACT phase for monitoring"""
        decision = {'action': 'monitor', 'parameters': {}}
        
        result = await ops_agent._act(decision)
        
        assert isinstance(result, dict)
        assert 'success' in result
    
    def test_classify_task_deployment(self, ops_agent):
        """Test task classification for deployment"""
        task = "Deploy the latest version to production"
        task_type = ops_agent._classify_task(task)
        
        assert task_type == 'deployment'
    
    def test_classify_task_monitoring(self, ops_agent):
        """Test task classification for monitoring"""
        task = "Monitor system metrics and performance"
        task_type = ops_agent._classify_task(task)
        
        assert task_type == 'monitoring'
    
    def test_classify_task_log_analysis(self, ops_agent):
        """Test task classification for log analysis"""
        task = "Analyze error logs from the past hour"
        task_type = ops_agent._classify_task(task)
        
        assert task_type == 'log_analysis'
    
    def test_classify_task_alert_management(self, ops_agent):
        """Test task classification for alert management"""
        task = "Check active alerts and notifications"
        task_type = ops_agent._classify_task(task)
        
        assert task_type == 'alert_management'
    
    def test_analyze_system_health_healthy(self, ops_agent):
        """Test system health analysis for healthy system"""
        metrics = {
            'success': True,
            'metrics': {
                'cpu': {'percent': 50},
                'memory': {'percent': 60},
                'disk': {'percent': 70}
            }
        }
        
        health = ops_agent._analyze_system_health(metrics)
        
        assert health['status'] == 'healthy'
        assert len(health['issues']) == 0
    
    def test_analyze_system_health_degraded(self, ops_agent):
        """Test system health analysis for degraded system"""
        metrics = {
            'success': True,
            'metrics': {
                'cpu': {'percent': 85},
                'memory': {'percent': 90},
                'disk': {'percent': 95}
            }
        }
        
        health = ops_agent._analyze_system_health(metrics)
        
        assert health['status'] == 'degraded'
        assert len(health['issues']) > 0
    
    def test_analyze_errors(self, ops_agent):
        """Test error analysis"""
        error_data = {
            'success': True,
            'patterns': [
                {'pattern': 'KeyError', 'count': 10},
                {'pattern': 'ValueError', 'count': 3}
            ],
            'total_errors': 13
        }
        
        analysis = ops_agent._analyze_errors(error_data)
        
        assert analysis['total_errors'] == 13
        assert len(analysis['critical_patterns']) > 0


class TestOpsAgentOODAIntegration:
    """Integration tests for full OODA loop"""
    
    @pytest.fixture
    def ops_agent(self):
        return OpsAgentOODA(
            vercel_token="test_token",
            enable_monitoring=True,
            enable_alerts=True
        )
    
    @pytest.mark.asyncio
    async def test_execute_monitoring_task(self, ops_agent):
        """Test executing a monitoring task"""
        result = await ops_agent.execute_task(
            task="Monitor system metrics",
            priority="medium"
        )
        
        assert result['success'] is True
        assert 'task_id' in result
        assert 'result' in result
    
    @pytest.mark.asyncio
    async def test_execute_log_analysis_task(self, ops_agent):
        """Test executing a log analysis task"""
        await ops_agent.log_tool.add_log_entry("Test error", "error")
        
        result = await ops_agent.execute_task(
            task="Analyze error logs",
            priority="high"
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_execute_alert_task(self, ops_agent):
        """Test executing an alert management task"""
        result = await ops_agent.execute_task(
            task="Check active alerts",
            priority="medium"
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_execute_deployment_task(self, ops_agent):
        """Test executing a deployment task (mocked)"""
        with patch.object(ops_agent.deployment_tool, 'deploy', new_callable=AsyncMock) as mock_deploy, \
             patch.object(ops_agent.deployment_tool, 'wait_for_deployment', new_callable=AsyncMock) as mock_wait:
            
            mock_deploy.return_value = {
                'success': True,
                'deployment_id': 'dep_123'
            }
            mock_wait.return_value = {
                'success': True,
                'state': 'READY'
            }
            
            result = await ops_agent.execute_task(
                task="Deploy to production",
                priority="high"
            )
            
            assert result['success'] is True
            assert mock_deploy.called
    
    @pytest.mark.asyncio
    async def test_task_history_recording(self, ops_agent):
        """Test that tasks are recorded in history"""
        await ops_agent.execute_task(
            task="Test task 1",
            priority="low"
        )
        await ops_agent.execute_task(
            task="Test task 2",
            priority="medium"
        )
        
        assert len(ops_agent.task_history) == 2
        assert ops_agent.task_history[0]['task'] == "Test task 1"
        assert ops_agent.task_history[1]['task'] == "Test task 2"
    
    @pytest.mark.asyncio
    async def test_execute_with_context(self, ops_agent):
        """Test executing task with context"""
        context = {
            'project': 'morningai',
            'environment': 'staging'
        }
        
        result = await ops_agent.execute_task(
            task="Monitor system",
            priority="medium",
            context=context
        )
        
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_troubleshooting_task(self, ops_agent):
        """Test troubleshooting task execution"""
        result = await ops_agent.execute_task(
            task="Troubleshoot application errors",
            priority="critical"
        )
        
        assert result['success'] is True
        assert 'result' in result


class TestOpsAgentFactory:
    """Tests for ops agent factory function"""
    
    def test_create_ops_agent(self):
        """Test factory function"""
        agent = create_ops_agent(
            vercel_token="test_token",
            enable_monitoring=True
        )
        
        assert isinstance(agent, OpsAgentOODA)
        assert agent.monitoring_tool is not None
    
    def test_create_ops_agent_no_monitoring(self):
        """Test creating agent without monitoring"""
        agent = create_ops_agent(
            enable_monitoring=False,
            enable_alerts=False
        )
        
        assert agent.monitoring_tool is None
        assert agent.alert_tool is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
