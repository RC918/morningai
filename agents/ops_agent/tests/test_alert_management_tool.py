#!/usr/bin/env python3
"""
Tests for Alert Management Tool
"""
import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.alert_management_tool import (
    AlertManagementTool,
    AlertSeverity,
    AlertStatus,
    create_alert_management_tool
)


class TestAlertManagementTool:
    """Tests for AlertManagementTool"""
    
    @pytest.fixture
    def alert_tool(self):
        """Create alert management tool for testing"""
        return AlertManagementTool()
    
    def test_initialization(self, alert_tool):
        """Test AlertManagementTool initialization"""
        assert alert_tool.alert_rules == {}
        assert alert_tool.alerts == {}
        assert alert_tool.alert_counter == 0
        assert alert_tool.rule_counter == 0
    
    @pytest.mark.asyncio
    async def test_create_alert_rule(self, alert_tool):
        """Test creating an alert rule"""
        result = await alert_tool.create_alert_rule(
            name="high_error_rate",
            condition="error_rate > 5%",
            severity="critical",
            channels=["email", "slack"],
            threshold=5.0
        )
        
        assert result['success'] is True
        assert 'rule' in result
        assert result['rule']['name'] == "high_error_rate"
        assert result['rule']['severity'] == "critical"
        assert result['rule']['enabled'] is True
        assert len(alert_tool.alert_rules) == 1
    
    @pytest.mark.asyncio
    async def test_trigger_alert(self, alert_tool):
        """Test triggering an alert"""
        rule_result = await alert_tool.create_alert_rule(
            name="test_rule",
            condition="test condition",
            severity="high"
        )
        rule_id = rule_result['rule']['id']
        
        result = await alert_tool.trigger_alert(
            rule_id=rule_id,
            message="Test alert triggered",
            metadata={"value": 100}
        )
        
        assert result['success'] is True
        assert result['alert']['rule_id'] == rule_id
        assert result['alert']['severity'] == "high"
        assert result['alert']['message'] == "Test alert triggered"
        assert len(alert_tool.alerts) == 1
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, alert_tool):
        """Test getting active alerts"""
        rule_result = await alert_tool.create_alert_rule(
            name="test_rule",
            condition="test",
            severity="medium"
        )
        rule_id = rule_result['rule']['id']
        
        await alert_tool.trigger_alert(rule_id, "Alert 1")
        await alert_tool.trigger_alert(rule_id, "Alert 2")
        
        result = await alert_tool.get_active_alerts()
        
        assert result['success'] is True
        assert result['total'] == 2
        assert len(result['alerts']) == 2
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_tool):
        """Test acknowledging an alert"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        alert_result = await alert_tool.trigger_alert(rule_id, "Test")
        alert_id = alert_result['alert']['id']
        
        result = await alert_tool.acknowledge_alert(alert_id)
        
        assert result['success'] is True
        assert result['status'] == AlertStatus.ACKNOWLEDGED.value
        assert 'acknowledged_at' in result
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_tool):
        """Test resolving an alert"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        alert_result = await alert_tool.trigger_alert(rule_id, "Test")
        alert_id = alert_result['alert']['id']
        
        result = await alert_tool.resolve_alert(alert_id)
        
        assert result['success'] is True
        assert result['status'] == AlertStatus.RESOLVED.value
        assert 'resolved_at' in result
    
    @pytest.mark.asyncio
    async def test_get_alert_history(self, alert_tool):
        """Test getting alert history"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        
        for i in range(5):
            await alert_tool.trigger_alert(rule_id, f"Alert {i}")
        
        result = await alert_tool.get_alert_history(limit=10)
        
        assert result['success'] is True
        assert result['total'] == 5
        assert len(result['alerts']) == 5
    
    @pytest.mark.asyncio
    async def test_update_alert_rule(self, alert_tool):
        """Test updating an alert rule"""
        rule_result = await alert_tool.create_alert_rule(
            name="test_rule",
            condition="test",
            severity="low"
        )
        rule_id = rule_result['rule']['id']
        
        result = await alert_tool.update_alert_rule(
            rule_id=rule_id,
            enabled=False,
            severity="critical",
            channels=["webhook"]
        )
        
        assert result['success'] is True
        assert result['rule']['enabled'] is False
        assert result['rule']['severity'] == "critical"
        assert "webhook" in result['rule']['channels']
    
    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, alert_tool):
        """Test deleting an alert rule"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        
        result = await alert_tool.delete_alert_rule(rule_id)
        
        assert result['success'] is True
        assert result['deleted'] is True
        assert rule_id not in alert_tool.alert_rules
    
    @pytest.mark.asyncio
    async def test_filter_alerts_by_severity(self, alert_tool):
        """Test filtering alerts by severity"""
        critical_rule = await alert_tool.create_alert_rule("critical", "test", "critical")
        low_rule = await alert_tool.create_alert_rule("low", "test", "low")
        
        await alert_tool.trigger_alert(critical_rule['rule']['id'], "Critical alert")
        await alert_tool.trigger_alert(low_rule['rule']['id'], "Low alert")
        
        result = await alert_tool.get_active_alerts(severity="critical")
        
        assert result['success'] is True
        assert result['total'] == 1
        assert result['alerts'][0]['severity'] == "critical"


class TestAlertManagementToolFactory:
    """Tests for alert management tool factory function"""
    
    def test_create_alert_management_tool(self):
        """Test factory function"""
        tool = create_alert_management_tool()
        
        assert isinstance(tool, AlertManagementTool)
        assert tool.alert_rules == {}
        assert tool.alerts == {}


class TestAlertManagementToolEdgeCases:
    """Edge case tests for AlertManagementTool"""
    
    @pytest.fixture
    def alert_tool(self):
        return AlertManagementTool()
    
    @pytest.mark.asyncio
    async def test_trigger_alert_nonexistent_rule(self, alert_tool):
        """Test triggering alert with nonexistent rule"""
        result = await alert_tool.trigger_alert("nonexistent", "Test")
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_trigger_alert_disabled_rule(self, alert_tool):
        """Test triggering alert on disabled rule"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        await alert_tool.update_alert_rule(rule_id, enabled=False)
        
        result = await alert_tool.trigger_alert(rule_id, "Test")
        
        assert result['success'] is False
        assert 'disabled' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_alert(self, alert_tool):
        """Test acknowledging nonexistent alert"""
        result = await alert_tool.acknowledge_alert("nonexistent")
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_alert_history_with_limit(self, alert_tool):
        """Test alert history with limit"""
        rule_result = await alert_tool.create_alert_rule("test", "test")
        rule_id = rule_result['rule']['id']
        
        for i in range(10):
            await alert_tool.trigger_alert(rule_id, f"Alert {i}")
        
        result = await alert_tool.get_alert_history(limit=5)
        
        assert result['success'] is True
        assert result['total'] == 5
    
    @pytest.mark.asyncio
    async def test_get_alert_history_filter_severity(self, alert_tool):
        """Test alert history filtered by severity"""
        critical_rule = await alert_tool.create_alert_rule("critical", "test", "critical")
        low_rule = await alert_tool.create_alert_rule("low", "test", "low")
        
        await alert_tool.trigger_alert(critical_rule['rule']['id'], "Critical")
        await alert_tool.trigger_alert(low_rule['rule']['id'], "Low")
        
        result = await alert_tool.get_alert_history(severity="critical")
        
        assert result['success'] is True
        assert all(a['severity'] == "critical" for a in result['alerts'])
    
    @pytest.mark.asyncio
    async def test_create_rule_default_channels(self, alert_tool):
        """Test creating rule with default channels"""
        result = await alert_tool.create_alert_rule("test", "test")
        
        assert result['success'] is True
        assert "email" in result['rule']['channels']
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(self, alert_tool):
        """Test updating nonexistent rule"""
        result = await alert_tool.update_alert_rule("nonexistent", enabled=False)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, alert_tool):
        """Test deleting nonexistent rule"""
        result = await alert_tool.delete_alert_rule("nonexistent")
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_active_alerts_empty(self, alert_tool):
        """Test getting active alerts when none exist"""
        result = await alert_tool.get_active_alerts()
        
        assert result['success'] is True
        assert result['total'] == 0
        assert result['alerts'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
