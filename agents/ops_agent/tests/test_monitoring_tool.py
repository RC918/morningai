#!/usr/bin/env python3
"""
Tests for Monitoring Tool
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.monitoring_tool import MonitoringTool, HealthStatus, create_monitoring_tool


class TestMonitoringTool:
    """Tests for MonitoringTool"""
    
    @pytest.fixture
    def monitoring_tool(self):
        """Create monitoring tool for testing"""
        return MonitoringTool()
    
    def test_initialization(self, monitoring_tool):
        """Test MonitoringTool initialization"""
        assert monitoring_tool.custom_metrics == {}
        assert monitoring_tool.health_checks == {}
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, monitoring_tool):
        """Test getting system metrics"""
        result = await monitoring_tool.get_system_metrics()
        
        assert result['success'] is True
        assert 'metrics' in result
        assert 'cpu' in result['metrics']
        assert 'memory' in result['metrics']
        assert 'disk' in result['metrics']
        assert 'network' in result['metrics']
        
        assert 'percent' in result['metrics']['cpu']
        assert 'count' in result['metrics']['cpu']
        
        assert 'total' in result['metrics']['memory']
        assert 'available' in result['metrics']['memory']
        assert 'percent' in result['metrics']['memory']
    
    @pytest.mark.asyncio
    async def test_check_service_health_default(self, monitoring_tool):
        """Test default service health check"""
        result = await monitoring_tool.check_service_health("test_service")
        
        assert result['success'] is True
        assert result['service'] == "test_service"
        assert result['status'] == HealthStatus.HEALTHY.value
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_check_service_health_custom(self, monitoring_tool):
        """Test custom health check function"""
        async def custom_health_check():
            return True
        
        monitoring_tool.register_health_check("api", custom_health_check)
        
        result = await monitoring_tool.check_service_health("api")
        
        assert result['success'] is True
        assert result['status'] == HealthStatus.HEALTHY.value
    
    @pytest.mark.asyncio
    async def test_check_service_health_unhealthy(self, monitoring_tool):
        """Test unhealthy service"""
        async def failing_health_check():
            return False
        
        monitoring_tool.register_health_check("broken_service", failing_health_check)
        
        result = await monitoring_tool.check_service_health("broken_service")
        
        assert result['success'] is True
        assert result['status'] == HealthStatus.UNHEALTHY.value
    
    @pytest.mark.asyncio
    async def test_add_custom_metric(self, monitoring_tool):
        """Test adding custom metric"""
        result = await monitoring_tool.add_custom_metric(
            name="api_latency",
            value=125.5,
            metric_type="gauge",
            labels={"endpoint": "/api/users"}
        )
        
        assert result['success'] is True
        assert result['metric']['name'] == "api_latency"
        assert result['metric']['value'] == 125.5
        assert result['metric']['type'] == "gauge"
        assert result['metric']['labels'] == {"endpoint": "/api/users"}
        
        assert "api_latency" in monitoring_tool.custom_metrics
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, monitoring_tool):
        """Test getting metrics summary"""
        await monitoring_tool.add_custom_metric("metric1", 100.0)
        await monitoring_tool.add_custom_metric("metric2", 200.0)
        
        result = await monitoring_tool.get_metrics_summary()
        
        assert result['success'] is True
        assert 'summary' in result
        assert 'system_metrics' in result['summary']
        assert 'custom_metrics' in result['summary']
        assert result['summary']['total_custom_metrics'] == 2
        
        assert 'metric1' in result['summary']['custom_metrics']
        assert 'metric2' in result['summary']['custom_metrics']
    
    @pytest.mark.asyncio
    async def test_multiple_custom_metrics(self, monitoring_tool):
        """Test adding multiple custom metrics"""
        metrics = [
            ("cpu_usage", 45.2, "gauge"),
            ("request_count", 1000, "counter"),
            ("response_time", 0.25, "histogram")
        ]
        
        for name, value, metric_type in metrics:
            result = await monitoring_tool.add_custom_metric(name, value, metric_type)
            assert result['success'] is True
        
        assert len(monitoring_tool.custom_metrics) == 3
    
    def test_register_health_check(self, monitoring_tool):
        """Test registering a health check"""
        async def my_check():
            return True
        
        monitoring_tool.register_health_check("my_service", my_check)
        
        assert "my_service" in monitoring_tool.health_checks
        assert monitoring_tool.health_checks["my_service"] == my_check


class TestMonitoringToolFactory:
    """Tests for monitoring tool factory function"""
    
    def test_create_monitoring_tool(self):
        """Test factory function"""
        tool = create_monitoring_tool()
        
        assert isinstance(tool, MonitoringTool)
        assert tool.custom_metrics == {}
        assert tool.health_checks == {}


class TestMonitoringToolEdgeCases:
    """Edge case tests for MonitoringTool"""
    
    @pytest.fixture
    def monitoring_tool(self):
        return MonitoringTool()
    
    @pytest.mark.asyncio
    async def test_add_metric_with_invalid_type(self, monitoring_tool):
        """Test adding metric with invalid type"""
        result = await monitoring_tool.add_custom_metric(
            name="test_metric",
            value=100.0,
            metric_type="invalid_type"
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_add_metric_no_labels(self, monitoring_tool):
        """Test adding metric without labels"""
        result = await monitoring_tool.add_custom_metric(
            name="simple_metric",
            value=50.0
        )
        
        assert result['success'] is True
        assert result['metric']['labels'] is None or result['metric']['labels'] == {}
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, monitoring_tool):
        """Test health check that raises exception"""
        async def failing_check():
            raise Exception("Check failed")
        
        monitoring_tool.register_health_check("error_service", failing_check)
        
        result = await monitoring_tool.check_service_health("error_service")
        
        assert result['success'] is False
        assert result['status'] == HealthStatus.UNHEALTHY.value
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary_empty(self, monitoring_tool):
        """Test metrics summary with no custom metrics"""
        result = await monitoring_tool.get_metrics_summary()
        
        assert result['success'] is True
        assert result['summary']['total_custom_metrics'] == 0
        assert result['summary']['custom_metrics'] == {}
    
    @pytest.mark.asyncio
    async def test_overwrite_custom_metric(self, monitoring_tool):
        """Test overwriting an existing custom metric"""
        await monitoring_tool.add_custom_metric("test_metric", 100.0)
        await monitoring_tool.add_custom_metric("test_metric", 200.0)
        
        assert len(monitoring_tool.custom_metrics) == 1
        assert monitoring_tool.custom_metrics["test_metric"].value == 200.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
