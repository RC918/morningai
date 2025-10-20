#!/usr/bin/env python3
"""
Tests for Monitoring Dashboard Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.services.monitoring_dashboard import (
    MonitoringDashboard,
    DashboardMetrics,
    monitoring_dashboard
)


class TestMonitoringDashboard:
    """Test suite for MonitoringDashboard class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.dashboard = MonitoringDashboard()
        self.sample_metrics = {
            'circuit_breakers': {
                'api_service': {
                    'state': 'closed',
                    'total_requests': 1000,
                    'failed_requests': 10,
                    'success_requests': 990,
                    'failure_rate': 0.01,
                    'consecutive_failures': 0
                },
                'db_service': {
                    'state': 'open',
                    'total_requests': 500,
                    'failed_requests': 50,
                    'success_requests': 450,
                    'failure_rate': 0.1,
                    'consecutive_failures': 5
                }
            },
            'bulkheads': {
                'task_queue': {
                    'active_requests': 10,
                    'total_requests': 100,
                    'rejected_requests': 5,
                    'rejection_rate': 0.05,
                    'available_capacity': 40
                }
            }
        }
    
    def test_init(self):
        """Test dashboard initialization"""
        dashboard = MonitoringDashboard()
        assert dashboard.metrics_history == []
        assert 'error_rate' in dashboard.alert_thresholds
        assert 'latency_p95' in dashboard.alert_thresholds
        assert 'circuit_breaker_open' in dashboard.alert_thresholds
    
    @pytest.mark.asyncio
    async def test_calculate_system_health(self):
        """Test system health calculation"""
        health = await self.dashboard._calculate_system_health(self.sample_metrics)
        
        assert 'overall_status' in health
        assert 'error_rate' in health
        assert 'open_circuit_breakers' in health
        assert 'rejected_requests' in health
        assert health['open_circuit_breakers'] == 1
        assert health['rejected_requests'] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_degraded(self):
        """Test system health calculation for degraded status"""
        health = await self.dashboard._calculate_system_health(self.sample_metrics)
        assert health['overall_status'] == 'degraded'
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_unhealthy(self):
        """Test system health calculation for unhealthy status"""
        unhealthy_metrics = {
            'circuit_breakers': {
                'api_service': {
                    'state': 'closed',
                    'total_requests': 100,
                    'failed_requests': 10,
                    'success_requests': 90,
                    'failure_rate': 0.1
                }
            },
            'bulkheads': {}
        }
        health = await self.dashboard._calculate_system_health(unhealthy_metrics)
        assert health['overall_status'] == 'unhealthy'
    
    def test_get_dashboard_data_no_metrics(self):
        """Test get_dashboard_data when no metrics available"""
        data = self.dashboard.get_dashboard_data(hours=1)
        
        assert data['system_health'] == 'healthy'
        assert data['circuit_breakers'] == {}
        assert data['bulkheads'] == {}
        assert data['saga_orchestrator']['active_sagas'] == 0
        assert data['storage_stats']['total_tables'] == 5
    
    def test_get_dashboard_data_with_metrics(self):
        """Test get_dashboard_data with metrics"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers=self.sample_metrics['circuit_breakers'],
            bulkheads=self.sample_metrics['bulkheads'],
            saga_orchestrator={'active_sagas': 3, 'completed_sagas': 10},
            storage_stats={'total_tables': 8},
            system_health={'overall_status': 'healthy', 'error_rate': 0.01}
        )
        self.dashboard.metrics_history.append(metrics)
        
        data = self.dashboard.get_dashboard_data(hours=1)
        
        assert data['system_health']['overall_status'] == 'healthy'
        assert len(data['circuit_breakers']) == 2
        assert len(data['bulkheads']) == 1
    
    def test_format_circuit_breaker_data(self):
        """Test circuit breaker data formatting"""
        formatted = self.dashboard._format_circuit_breaker_data(
            self.sample_metrics['circuit_breakers']
        )
        
        assert len(formatted) == 2
        assert formatted[0]['name'] == 'api_service'
        assert formatted[0]['state'] == 'closed'
        assert formatted[0]['status_color'] == 'green'
        assert formatted[1]['name'] == 'db_service'
        assert formatted[1]['state'] == 'open'
        assert formatted[1]['status_color'] == 'red'
    
    def test_format_bulkhead_data(self):
        """Test bulkhead data formatting"""
        formatted = self.dashboard._format_bulkhead_data(
            self.sample_metrics['bulkheads']
        )
        
        assert len(formatted) == 1
        assert formatted[0]['name'] == 'task_queue'
        assert formatted[0]['active_requests'] == 10
        assert formatted[0]['utilization'] == 20.0
    
    def test_calculate_utilization(self):
        """Test bulkhead utilization calculation"""
        metrics = {
            'active_requests': 10,
            'available_capacity': 40
        }
        utilization = self.dashboard._calculate_utilization(metrics)
        assert utilization == 20.0
    
    def test_calculate_utilization_zero_capacity(self):
        """Test bulkhead utilization with zero capacity"""
        metrics = {
            'active_requests': 0,
            'available_capacity': 0
        }
        utilization = self.dashboard._calculate_utilization(metrics)
        assert utilization == 0.0
    
    def test_get_status_color(self):
        """Test status color mapping"""
        assert self.dashboard._get_status_color('closed') == 'green'
        assert self.dashboard._get_status_color('open') == 'red'
        assert self.dashboard._get_status_color('half_open') == 'yellow'
        assert self.dashboard._get_status_color('unknown') == 'gray'
        assert self.dashboard._get_status_color('invalid') == 'gray'
    
    def test_calculate_trends(self):
        """Test trends calculation"""
        metrics1 = DashboardMetrics(
            timestamp=datetime.now() - timedelta(hours=1),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.02}
        )
        metrics2 = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.05}
        )
        
        trends = self.dashboard._calculate_trends([metrics1, metrics2])
        
        assert 'error_rate_trend' in trends
        assert trends['error_rate_trend'] == 'increasing'
    
    def test_calculate_trends_single_metric(self):
        """Test trends calculation with single metric"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.02}
        )
        
        trends = self.dashboard._calculate_trends([metrics])
        assert trends == {}
    
    def test_generate_alerts(self):
        """Test alert generation"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.1,
                'open_circuit_breakers': 2,
                'rejected_requests': 15
            }
        )
        
        alerts = self.dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 3
        assert alerts[0]['level'] == 'critical'
        assert 'High error rate' in alerts[0]['message']
        assert alerts[1]['level'] == 'warning'
        assert 'circuit breaker' in alerts[1]['message']
    
    def test_export_metrics_no_data(self):
        """Test export metrics when no data available"""
        result = self.dashboard.export_metrics('json')
        assert 'No metrics available' in result
    
    def test_export_metrics_json(self):
        """Test export metrics as JSON"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.02}
        )
        self.dashboard.metrics_history.append(metrics)
        
        result = self.dashboard.export_metrics('json')
        assert 'timestamp' in result
        assert 'system_health' in result
    
    def test_export_metrics_prometheus(self):
        """Test export metrics in Prometheus format"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={
                'api_service': {
                    'total_requests': 100,
                    'failed_requests': 5,
                    'failure_rate': 0.05
                }
            },
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.02, 'open_circuit_breakers': 0}
        )
        self.dashboard.metrics_history.append(metrics)
        
        result = self.dashboard.export_metrics('prometheus')
        assert 'circuit_breaker_total_requests' in result
        assert 'system_error_rate' in result
    
    def test_export_metrics_unsupported_format(self):
        """Test export metrics with unsupported format"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={}
        )
        self.dashboard.metrics_history.append(metrics)
        
        result = self.dashboard.export_metrics('xml')
        assert 'Unsupported format' in result


class TestDashboardMetrics:
    """Test suite for DashboardMetrics dataclass"""
    
    def test_dashboard_metrics_creation(self):
        """Test creating DashboardMetrics instance"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={}
        )
        
        assert metrics.timestamp is not None
        assert metrics.circuit_breakers == {}
        assert metrics.bulkheads == {}
