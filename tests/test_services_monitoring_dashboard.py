"""
Unit tests for services.monitoring_dashboard module

Tests monitoring dashboard functionality including:
- Dashboard metrics collection
- System health calculation
- Data formatting for circuit breakers and bulkheads
- Trend analysis and alert generation
- Metrics export (JSON and Prometheus formats)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import json


class TestMonitoringDashboard:
    """Test MonitoringDashboard class initialization"""
    
    def test_init(self):
        """Should initialize MonitoringDashboard with default values"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        assert dashboard.logger is not None
        assert dashboard.metrics_history == []
        assert dashboard.alert_thresholds['error_rate'] == 0.05
        assert dashboard.alert_thresholds['latency_p95'] == 1000
        assert dashboard.alert_thresholds['circuit_breaker_open'] is True
        assert dashboard.alert_thresholds['storage_errors'] == 10


class TestGetDashboardData:
    """Test dashboard data retrieval"""
    
    def test_get_dashboard_data_no_metrics(self):
        """Should return default structure when no metrics available"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        result = dashboard.get_dashboard_data(hours=1)
        
        assert result['system_health'] == 'healthy'
        assert result['circuit_breakers'] == {}
        assert result['bulkheads'] == {}
        assert result['saga_orchestrator']['active_sagas'] == 0
        assert result['storage_stats']['total_tables'] == 5
        assert result['trends'] == {}
        assert result['alerts'] == []
    
    def test_get_dashboard_data_with_metrics(self):
        """Should return formatted data when metrics available"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={'cb1': {'state': 'closed', 'total_requests': 100}},
            bulkheads={'bh1': {'active_requests': 5, 'total_requests': 100}},
            saga_orchestrator={'active_sagas': 3, 'completed_sagas': 10},
            storage_stats={'total_tables': 5},
            system_health={'error_rate': 0.01, 'overall_status': 'healthy'}
        )
        dashboard.metrics_history.append(metrics)
        
        result = dashboard.get_dashboard_data(hours=1)
        
        assert result['system_health']['error_rate'] == 0.01
        assert len(result['circuit_breakers']) == 1
        assert len(result['bulkheads']) == 1
        assert result['saga_orchestrator']['active_sagas'] == 3


class TestCalculateSystemHealth:
    """Test system health calculation"""
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_healthy(self):
        """Should calculate healthy status"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        resilience_metrics = {
            'circuit_breakers': {
                'cb1': {'state': 'closed', 'total_requests': 100, 'failed_requests': 1}
            },
            'bulkheads': {
                'bh1': {'rejected_requests': 0}
            }
        }
        
        result = await dashboard._calculate_system_health(resilience_metrics)
        
        assert result['overall_status'] == 'healthy'
        assert result['error_rate'] == 0.01
        assert result['open_circuit_breakers'] == 0
        assert result['rejected_requests'] == 0
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_degraded_open_breaker(self):
        """Should mark as degraded when circuit breaker is open"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        resilience_metrics = {
            'circuit_breakers': {
                'cb1': {'state': 'open', 'total_requests': 100, 'failed_requests': 10}
            },
            'bulkheads': {}
        }
        
        result = await dashboard._calculate_system_health(resilience_metrics)
        
        assert result['overall_status'] == 'degraded'
        assert result['open_circuit_breakers'] == 1
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_unhealthy_high_error_rate(self):
        """Should mark as unhealthy when error rate exceeds threshold"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        resilience_metrics = {
            'circuit_breakers': {
                'cb1': {'state': 'closed', 'total_requests': 100, 'failed_requests': 10}
            },
            'bulkheads': {}
        }
        
        result = await dashboard._calculate_system_health(resilience_metrics)
        
        assert result['overall_status'] == 'unhealthy'
        assert result['error_rate'] == 0.1
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_degraded_rejected_requests(self):
        """Should mark as degraded when bulkheads reject requests"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        resilience_metrics = {
            'circuit_breakers': {},
            'bulkheads': {
                'bh1': {'rejected_requests': 5}
            }
        }
        
        result = await dashboard._calculate_system_health(resilience_metrics)
        
        assert result['overall_status'] == 'degraded'
        assert result['rejected_requests'] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_error_handling(self):
        """Should handle errors gracefully"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        resilience_metrics = {'invalid': 'data'}
        
        result = await dashboard._calculate_system_health(resilience_metrics)
        
        assert result['overall_status'] == 'unknown'


class TestFormatCircuitBreakerData:
    """Test circuit breaker data formatting"""
    
    def test_format_circuit_breaker_data_empty(self):
        """Should handle empty circuit breakers"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        result = dashboard._format_circuit_breaker_data({})
        
        assert result == []
    
    def test_format_circuit_breaker_data_with_metrics(self):
        """Should format circuit breaker metrics"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        circuit_breakers = {
            'cb1': {
                'state': 'closed',
                'total_requests': 100,
                'failed_requests': 5,
                'success_requests': 95,
                'failure_rate': 0.05,
                'consecutive_failures': 0,
                'last_failure_time': '2025-01-15T10:30:00'
            },
            'cb2': {
                'state': 'open',
                'total_requests': 50,
                'failed_requests': 10,
                'success_requests': 40,
                'failure_rate': 0.2,
                'consecutive_failures': 5
            }
        }
        
        result = dashboard._format_circuit_breaker_data(circuit_breakers)
        
        assert len(result) == 2
        assert result[0]['name'] == 'cb1'
        assert result[0]['state'] == 'closed'
        assert result[0]['status_color'] == 'green'
        assert result[1]['name'] == 'cb2'
        assert result[1]['state'] == 'open'
        assert result[1]['status_color'] == 'red'


class TestFormatBulkheadData:
    """Test bulkhead data formatting"""
    
    def test_format_bulkhead_data_empty(self):
        """Should handle empty bulkheads"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        result = dashboard._format_bulkhead_data({})
        
        assert result == []
    
    def test_format_bulkhead_data_with_metrics(self):
        """Should format bulkhead metrics"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        bulkheads = {
            'bh1': {
                'active_requests': 5,
                'total_requests': 100,
                'rejected_requests': 2,
                'rejection_rate': 0.02,
                'available_capacity': 15
            }
        }
        
        result = dashboard._format_bulkhead_data(bulkheads)
        
        assert len(result) == 1
        assert result[0]['name'] == 'bh1'
        assert result[0]['active_requests'] == 5
        assert result[0]['utilization'] == 25.0


class TestCalculateUtilization:
    """Test bulkhead utilization calculation"""
    
    def test_calculate_utilization_normal(self):
        """Should calculate utilization percentage"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        metrics = {
            'active_requests': 5,
            'available_capacity': 15
        }
        
        result = dashboard._calculate_utilization(metrics)
        
        assert result == 25.0
    
    def test_calculate_utilization_zero_capacity(self):
        """Should return 0 when total capacity is 0"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        metrics = {
            'active_requests': 0,
            'available_capacity': 0
        }
        
        result = dashboard._calculate_utilization(metrics)
        
        assert result == 0


class TestGetStatusColor:
    """Test status color mapping"""
    
    def test_get_status_color_closed(self):
        """Should return green for closed state"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        assert dashboard._get_status_color('closed') == 'green'
    
    def test_get_status_color_open(self):
        """Should return red for open state"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        assert dashboard._get_status_color('open') == 'red'
    
    def test_get_status_color_half_open(self):
        """Should return yellow for half_open state"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        assert dashboard._get_status_color('half_open') == 'yellow'
    
    def test_get_status_color_unknown(self):
        """Should return gray for unknown state"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        assert dashboard._get_status_color('unknown') == 'gray'
        assert dashboard._get_status_color('invalid') == 'gray'


class TestCalculateTrends:
    """Test trend calculation"""
    
    def test_calculate_trends_insufficient_data(self):
        """Should return empty dict when insufficient data"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        result = dashboard._calculate_trends([])
        
        assert result == {}
    
    def test_calculate_trends_stable(self):
        """Should detect stable trend"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics_list = [
            DashboardMetrics(
                timestamp=datetime.now() - timedelta(hours=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.02}
            ),
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.021}
            )
        ]
        
        result = dashboard._calculate_trends(metrics_list)
        
        assert result['error_rate_trend'] == 'stable'
    
    def test_calculate_trends_increasing(self):
        """Should detect increasing trend"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics_list = [
            DashboardMetrics(
                timestamp=datetime.now() - timedelta(hours=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.02}
            ),
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.03}
            )
        ]
        
        result = dashboard._calculate_trends(metrics_list)
        
        assert result['error_rate_trend'] == 'increasing'
    
    def test_calculate_trends_decreasing(self):
        """Should detect decreasing trend"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics_list = [
            DashboardMetrics(
                timestamp=datetime.now() - timedelta(hours=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.03}
            ),
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.02}
            )
        ]
        
        result = dashboard._calculate_trends(metrics_list)
        
        assert result['error_rate_trend'] == 'decreasing'


class TestGenerateAlerts:
    """Test alert generation"""
    
    def test_generate_alerts_no_issues(self):
        """Should generate no alerts when system is healthy"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 0,
                'rejected_requests': 5
            }
        )
        
        result = dashboard._generate_alerts(metrics)
        
        assert len(result) == 0
    
    def test_generate_alerts_high_error_rate(self):
        """Should generate critical alert for high error rate"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.1,
                'open_circuit_breakers': 0,
                'rejected_requests': 0
            }
        )
        
        result = dashboard._generate_alerts(metrics)
        
        assert len(result) == 1
        assert result[0]['level'] == 'critical'
        assert 'error rate' in result[0]['message'].lower()
    
    def test_generate_alerts_open_circuit_breakers(self):
        """Should generate warning for open circuit breakers"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 2,
                'rejected_requests': 0
            }
        )
        
        result = dashboard._generate_alerts(metrics)
        
        assert len(result) == 1
        assert result[0]['level'] == 'warning'
        assert 'circuit breaker' in result[0]['message'].lower()
    
    def test_generate_alerts_rejected_requests(self):
        """Should generate warning for rejected requests"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 0,
                'rejected_requests': 15
            }
        )
        
        result = dashboard._generate_alerts(metrics)
        
        assert len(result) == 1
        assert result[0]['level'] == 'warning'
        assert 'rejected' in result[0]['message'].lower()
    
    def test_generate_alerts_multiple_issues(self):
        """Should generate multiple alerts for multiple issues"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
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
        
        result = dashboard._generate_alerts(metrics)
        
        assert len(result) == 3


class TestExportMetrics:
    """Test metrics export"""
    
    def test_export_metrics_no_data(self):
        """Should return error when no metrics available"""
        from services.monitoring_dashboard import MonitoringDashboard
        
        dashboard = MonitoringDashboard()
        
        result = dashboard.export_metrics(format='json')
        
        assert 'error' in result
        assert 'No metrics available' in result
    
    def test_export_metrics_json(self):
        """Should export metrics in JSON format"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            circuit_breakers={'cb1': {'state': 'closed'}},
            bulkheads={'bh1': {'active_requests': 5}},
            saga_orchestrator={'active_sagas': 3},
            storage_stats={'total_tables': 5},
            system_health={'error_rate': 0.01}
        )
        dashboard.metrics_history.append(metrics)
        
        result = dashboard.export_metrics(format='json')
        
        assert 'timestamp' in result
        assert 'circuit_breakers' in result
        assert 'cb1' in result
    
    def test_export_metrics_prometheus(self):
        """Should export metrics in Prometheus format"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            circuit_breakers={
                'cb1': {
                    'total_requests': 100,
                    'failed_requests': 5,
                    'failure_rate': 0.05
                }
            },
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.01, 'open_circuit_breakers': 0}
        )
        dashboard.metrics_history.append(metrics)
        
        result = dashboard.export_metrics(format='prometheus')
        
        assert 'circuit_breaker_total_requests' in result
        assert 'circuit_breaker_failed_requests' in result
        assert 'system_error_rate' in result
    
    def test_export_metrics_unsupported_format(self):
        """Should return error for unsupported format"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={}
        )
        dashboard.metrics_history.append(metrics)
        
        result = dashboard.export_metrics(format='xml')
        
        assert 'Unsupported format' in result


class TestExportPrometheusFormat:
    """Test Prometheus format export"""
    
    def test_export_prometheus_format(self):
        """Should format metrics in Prometheus format"""
        from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics
        
        dashboard = MonitoringDashboard()
        metrics = DashboardMetrics(
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            circuit_breakers={
                'service1': {
                    'total_requests': 100,
                    'failed_requests': 5,
                    'failure_rate': 0.05
                }
            },
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={'error_rate': 0.01, 'open_circuit_breakers': 0}
        )
        
        result = dashboard._export_prometheus_format(metrics)
        
        lines = result.split('\n')
        assert any('circuit_breaker_total_requests{service="service1"} 100' in line for line in lines)
        assert any('circuit_breaker_failed_requests{service="service1"} 5' in line for line in lines)
        assert any('system_error_rate 0.01' in line for line in lines)
