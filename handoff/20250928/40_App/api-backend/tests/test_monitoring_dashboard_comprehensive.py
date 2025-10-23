"""
Comprehensive tests for Monitoring Dashboard Service

Tests all monitoring dashboard functionality including:
- Metrics collection from resilience components
- System health calculation
- Dashboard data formatting
- Trend analysis
- Alert generation
- Metrics export (JSON, Prometheus)
- Continuous monitoring loop
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'handoff', '20250928', '40_App', 'api-backend', 'src'))

from services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics


@pytest.fixture
def dashboard():
    """Create monitoring dashboard instance"""
    return MonitoringDashboard()


@pytest.fixture
def mock_resilience_metrics():
    """Mock resilience metrics"""
    return {
        'circuit_breakers': {
            'api_service': {
                'state': 'closed',
                'total_requests': 1000,
                'failed_requests': 10,
                'success_requests': 990,
                'failure_rate': 0.01,
                'consecutive_failures': 0,
                'last_failure_time': None
            },
            'database_service': {
                'state': 'open',
                'total_requests': 500,
                'failed_requests': 50,
                'success_requests': 450,
                'failure_rate': 0.10,
                'consecutive_failures': 5,
                'last_failure_time': datetime.now().isoformat()
            }
        },
        'bulkheads': {
            'worker_pool': {
                'active_requests': 8,
                'total_requests': 1500,
                'rejected_requests': 5,
                'rejection_rate': 0.003,
                'available_capacity': 2
            },
            'api_pool': {
                'active_requests': 15,
                'total_requests': 2000,
                'rejected_requests': 20,
                'rejection_rate': 0.01,
                'available_capacity': 5
            }
        }
    }


@pytest.fixture
def mock_saga_metrics():
    """Mock saga orchestrator metrics"""
    return {
        'active_sagas': 3,
        'completed_sagas': 150,
        'failed_sagas': 5,
        'compensated_sagas': 2,
        'avg_completion_time': 2.5
    }


@pytest.fixture
def mock_storage_stats():
    """Mock storage statistics"""
    return {
        'total_tables': 5,
        'total_records': 10000,
        'storage_errors': 2,
        'last_backup': datetime.now().isoformat()
    }


class TestMetricsCollection:
    """Test metrics collection functionality"""
    
    @pytest.mark.asyncio
    async def test_collect_metrics_success(self, dashboard, mock_resilience_metrics, mock_saga_metrics, mock_storage_stats):
        """Test successful metrics collection"""
        mock_resilience_manager = Mock()
        mock_resilience_manager.get_all_metrics.return_value = mock_resilience_metrics
        
        mock_state_manager = Mock()
        mock_state_manager.get_storage_stats.return_value = mock_storage_stats
        
        mock_saga_orchestrator = Mock()
        mock_saga_orchestrator.get_orchestrator_metrics.return_value = mock_saga_metrics
        
        with patch('services.monitoring_dashboard.resilience_manager', mock_resilience_manager), \
             patch('services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager), \
             patch('services.monitoring_dashboard.saga_orchestrator', mock_saga_orchestrator):
            
            metrics = await dashboard.collect_metrics()
            
            assert metrics is not None
            assert isinstance(metrics, DashboardMetrics)
            assert metrics.circuit_breakers == mock_resilience_metrics['circuit_breakers']
            assert metrics.bulkheads == mock_resilience_metrics['bulkheads']
            assert metrics.saga_orchestrator == mock_saga_metrics
            assert metrics.storage_stats == mock_storage_stats
    
    @pytest.mark.asyncio
    async def test_collect_metrics_adds_to_history(self, dashboard, mock_resilience_metrics, mock_saga_metrics, mock_storage_stats):
        """Test metrics are added to history"""
        mock_resilience_manager = Mock()
        mock_resilience_manager.get_all_metrics.return_value = mock_resilience_metrics
        
        mock_state_manager = Mock()
        mock_state_manager.get_storage_stats.return_value = mock_storage_stats
        
        mock_saga_orchestrator = Mock()
        mock_saga_orchestrator.get_orchestrator_metrics.return_value = mock_saga_metrics
        
        with patch('services.monitoring_dashboard.resilience_manager', mock_resilience_manager), \
             patch('services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager), \
             patch('services.monitoring_dashboard.saga_orchestrator', mock_saga_orchestrator):
            
            initial_count = len(dashboard.metrics_history)
            await dashboard.collect_metrics()
            
            assert len(dashboard.metrics_history) == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_collect_metrics_history_limit(self, dashboard, mock_resilience_metrics, mock_saga_metrics, mock_storage_stats):
        """Test metrics history is limited to prevent memory issues"""
        mock_resilience_manager = Mock()
        mock_resilience_manager.get_all_metrics.return_value = mock_resilience_metrics
        
        mock_state_manager = Mock()
        mock_state_manager.get_storage_stats.return_value = mock_storage_stats
        
        mock_saga_orchestrator = Mock()
        mock_saga_orchestrator.get_orchestrator_metrics.return_value = mock_saga_metrics
        
        with patch('services.monitoring_dashboard.resilience_manager', mock_resilience_manager), \
             patch('services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager), \
             patch('services.monitoring_dashboard.saga_orchestrator', mock_saga_orchestrator):
            
            for _ in range(1001):
                await dashboard.collect_metrics()
            
            assert len(dashboard.metrics_history) == 500
    
    @pytest.mark.asyncio
    async def test_collect_metrics_error_handling(self, dashboard):
        """Test error handling during metrics collection"""
        with patch('services.monitoring_dashboard.resilience_manager', side_effect=Exception('Collection failed')):
            metrics = await dashboard.collect_metrics()
            
            assert metrics is None


class TestSystemHealthCalculation:
    """Test system health calculation"""
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_healthy(self, dashboard):
        """Test system health calculation when system is healthy"""
        resilience_metrics = {
            'circuit_breakers': {
                'service1': {
                    'state': 'closed',
                    'total_requests': 1000,
                    'failed_requests': 10
                }
            },
            'bulkheads': {
                'pool1': {
                    'rejected_requests': 0
                }
            }
        }
        
        health = await dashboard._calculate_system_health(resilience_metrics)
        
        assert health['overall_status'] == 'healthy'
        assert health['error_rate'] == 0.01
        assert health['open_circuit_breakers'] == 0
        assert health['rejected_requests'] == 0
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_degraded(self, dashboard):
        """Test system health calculation when system is degraded"""
        resilience_metrics = {
            'circuit_breakers': {
                'service1': {
                    'state': 'open',
                    'total_requests': 1000,
                    'failed_requests': 30
                }
            },
            'bulkheads': {
                'pool1': {
                    'rejected_requests': 5
                }
            }
        }
        
        health = await dashboard._calculate_system_health(resilience_metrics)
        
        assert health['overall_status'] == 'degraded'
        assert health['open_circuit_breakers'] == 1
        assert health['rejected_requests'] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_unhealthy(self, dashboard):
        """Test system health calculation when system is unhealthy"""
        resilience_metrics = {
            'circuit_breakers': {
                'service1': {
                    'state': 'closed',
                    'total_requests': 1000,
                    'failed_requests': 100  # 10% error rate > 5% threshold
                }
            },
            'bulkheads': {}
        }
        
        health = await dashboard._calculate_system_health(resilience_metrics)
        
        assert health['overall_status'] == 'unhealthy'
        assert health['error_rate'] == 0.10
    
    @pytest.mark.asyncio
    async def test_calculate_system_health_no_requests(self, dashboard):
        """Test system health calculation with no requests"""
        resilience_metrics = {
            'circuit_breakers': {
                'service1': {
                    'state': 'closed',
                    'total_requests': 0,
                    'failed_requests': 0
                }
            },
            'bulkheads': {}
        }
        
        health = await dashboard._calculate_system_health(resilience_metrics)
        
        assert health['overall_status'] == 'healthy'
        assert health['error_rate'] == 0.0


class TestDashboardDataFormatting:
    """Test dashboard data formatting"""
    
    def test_get_dashboard_data_no_metrics(self, dashboard):
        """Test dashboard data with no metrics"""
        data = dashboard.get_dashboard_data()
        
        assert 'timestamp' in data
        assert data['system_health'] == 'healthy'
        assert data['circuit_breakers'] == {}
        assert data['bulkheads'] == {}
        assert data['saga_orchestrator']['active_sagas'] == 0
    
    def test_get_dashboard_data_with_metrics(self, dashboard):
        """Test dashboard data with metrics"""
        mock_metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={
                'service1': {
                    'state': 'closed',
                    'total_requests': 100,
                    'failed_requests': 5,
                    'success_requests': 95,
                    'failure_rate': 0.05,
                    'consecutive_failures': 0,
                    'last_failure_time': None
                }
            },
            bulkheads={
                'pool1': {
                    'active_requests': 5,
                    'total_requests': 100,
                    'rejected_requests': 2,
                    'rejection_rate': 0.02,
                    'available_capacity': 5
                }
            },
            saga_orchestrator={'active_sagas': 3},
            storage_stats={'total_tables': 5},
            system_health={'overall_status': 'healthy', 'error_rate': 0.05}
        )
        dashboard.metrics_history.append(mock_metrics)
        
        data = dashboard.get_dashboard_data()
        
        assert data['system_health']['overall_status'] == 'healthy'
        assert len(data['circuit_breakers']) == 1
        assert len(data['bulkheads']) == 1
        assert data['saga_orchestrator']['active_sagas'] == 3
    
    def test_format_circuit_breaker_data(self, dashboard):
        """Test circuit breaker data formatting"""
        circuit_breakers = {
            'api_service': {
                'state': 'closed',
                'total_requests': 1000,
                'failed_requests': 10,
                'success_requests': 990,
                'failure_rate': 0.01,
                'consecutive_failures': 0,
                'last_failure_time': None
            },
            'db_service': {
                'state': 'open',
                'total_requests': 500,
                'failed_requests': 50,
                'success_requests': 450,
                'failure_rate': 0.10,
                'consecutive_failures': 5,
                'last_failure_time': datetime.now().isoformat()
            }
        }
        
        formatted = dashboard._format_circuit_breaker_data(circuit_breakers)
        
        assert len(formatted) == 2
        assert formatted[0]['name'] == 'api_service'
        assert formatted[0]['state'] == 'closed'
        assert formatted[0]['status_color'] == 'green'
        assert formatted[1]['name'] == 'db_service'
        assert formatted[1]['state'] == 'open'
        assert formatted[1]['status_color'] == 'red'
    
    def test_format_bulkhead_data(self, dashboard):
        """Test bulkhead data formatting"""
        bulkheads = {
            'worker_pool': {
                'active_requests': 8,
                'total_requests': 1000,
                'rejected_requests': 5,
                'rejection_rate': 0.005,
                'available_capacity': 2
            }
        }
        
        formatted = dashboard._format_bulkhead_data(bulkheads)
        
        assert len(formatted) == 1
        assert formatted[0]['name'] == 'worker_pool'
        assert formatted[0]['active_requests'] == 8
        assert formatted[0]['utilization'] == 80.0  # 8 / (8+2) * 100
    
    def test_calculate_utilization(self, dashboard):
        """Test bulkhead utilization calculation"""
        metrics = {
            'active_requests': 7,
            'available_capacity': 3
        }
        
        utilization = dashboard._calculate_utilization(metrics)
        
        assert utilization == 70.0  # 7 / (7+3) * 100
    
    def test_calculate_utilization_zero_capacity(self, dashboard):
        """Test utilization calculation with zero capacity"""
        metrics = {
            'active_requests': 0,
            'available_capacity': 0
        }
        
        utilization = dashboard._calculate_utilization(metrics)
        
        assert utilization == 0
    
    def test_get_status_color(self, dashboard):
        """Test status color mapping"""
        assert dashboard._get_status_color('closed') == 'green'
        assert dashboard._get_status_color('open') == 'red'
        assert dashboard._get_status_color('half_open') == 'yellow'
        assert dashboard._get_status_color('unknown') == 'gray'
        assert dashboard._get_status_color('invalid') == 'gray'


class TestTrendAnalysis:
    """Test trend analysis"""
    
    def test_calculate_trends_insufficient_data(self, dashboard):
        """Test trend calculation with insufficient data"""
        metrics = [
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.01}
            )
        ]
        
        trends = dashboard._calculate_trends(metrics)
        
        assert trends == {}
    
    def test_calculate_trends_stable(self, dashboard):
        """Test trend calculation for stable metrics"""
        base_time = datetime.now()
        metrics = [
            DashboardMetrics(
                timestamp=base_time,
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.05}
            ),
            DashboardMetrics(
                timestamp=base_time + timedelta(minutes=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.05}
            )
        ]
        
        trends = dashboard._calculate_trends(metrics)
        
        assert trends['error_rate_trend'] == 'stable'
    
    def test_calculate_trends_increasing(self, dashboard):
        """Test trend calculation for increasing error rate"""
        base_time = datetime.now()
        metrics = [
            DashboardMetrics(
                timestamp=base_time,
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.01}
            ),
            DashboardMetrics(
                timestamp=base_time + timedelta(minutes=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.05}
            )
        ]
        
        trends = dashboard._calculate_trends(metrics)
        
        assert trends['error_rate_trend'] == 'increasing'
    
    def test_calculate_trends_decreasing(self, dashboard):
        """Test trend calculation for decreasing error rate"""
        base_time = datetime.now()
        metrics = [
            DashboardMetrics(
                timestamp=base_time,
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.10}
            ),
            DashboardMetrics(
                timestamp=base_time + timedelta(minutes=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.02}
            )
        ]
        
        trends = dashboard._calculate_trends(metrics)
        
        assert trends['error_rate_trend'] == 'decreasing'


class TestAlertGeneration:
    """Test alert generation"""
    
    def test_generate_alerts_no_issues(self, dashboard):
        """Test alert generation with no issues"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 0,
                'rejected_requests': 0
            }
        )
        
        alerts = dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 0
    
    def test_generate_alerts_high_error_rate(self, dashboard):
        """Test alert generation for high error rate"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.10,  # Above 5% threshold
                'open_circuit_breakers': 0,
                'rejected_requests': 0
            }
        )
        
        alerts = dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 1
        assert alerts[0]['level'] == 'critical'
        assert 'High error rate' in alerts[0]['message']
    
    def test_generate_alerts_open_circuit_breakers(self, dashboard):
        """Test alert generation for open circuit breakers"""
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
        
        alerts = dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 1
        assert alerts[0]['level'] == 'warning'
        assert 'circuit breaker(s) open' in alerts[0]['message']
    
    def test_generate_alerts_rejected_requests(self, dashboard):
        """Test alert generation for rejected requests"""
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
        
        alerts = dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 1
        assert alerts[0]['level'] == 'warning'
        assert 'requests rejected' in alerts[0]['message']
    
    def test_generate_alerts_multiple_issues(self, dashboard):
        """Test alert generation with multiple issues"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.10,
                'open_circuit_breakers': 1,
                'rejected_requests': 20
            }
        )
        
        alerts = dashboard._generate_alerts(metrics)
        
        assert len(alerts) == 3


class TestMetricsExport:
    """Test metrics export functionality"""
    
    def test_export_metrics_json(self, dashboard):
        """Test JSON metrics export"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={'service1': {'state': 'closed'}},
            bulkheads={'pool1': {'active_requests': 5}},
            saga_orchestrator={'active_sagas': 3},
            storage_stats={'total_tables': 5},
            system_health={'overall_status': 'healthy'}
        )
        dashboard.metrics_history.append(metrics)
        
        exported = dashboard.export_metrics(format='json')
        
        assert exported is not None
        data = json.loads(exported)
        assert 'circuit_breakers' in data
        assert 'bulkheads' in data
    
    def test_export_metrics_prometheus(self, dashboard):
        """Test Prometheus metrics export"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={
                'api_service': {
                    'total_requests': 1000,
                    'failed_requests': 10,
                    'failure_rate': 0.01
                }
            },
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 0
            }
        )
        dashboard.metrics_history.append(metrics)
        
        exported = dashboard.export_metrics(format='prometheus')
        
        assert 'circuit_breaker_total_requests{service="api_service"}' in exported
        assert 'circuit_breaker_failed_requests{service="api_service"}' in exported
        assert 'system_error_rate' in exported
    
    def test_export_metrics_no_data(self, dashboard):
        """Test metrics export with no data"""
        exported = dashboard.export_metrics(format='json')
        
        assert 'No metrics available' in exported
    
    def test_export_metrics_unsupported_format(self, dashboard):
        """Test metrics export with unsupported format"""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={}
        )
        dashboard.metrics_history.append(metrics)
        
        exported = dashboard.export_metrics(format='xml')
        
        assert 'Unsupported format' in exported


class TestContinuousMonitoring:
    """Test continuous monitoring loop"""
    
    @pytest.mark.asyncio
    async def test_start_monitoring_loop(self, dashboard, mock_resilience_metrics, mock_saga_metrics, mock_storage_stats):
        """Test continuous monitoring loop"""
        mock_resilience_manager = Mock()
        mock_resilience_manager.get_all_metrics.return_value = mock_resilience_metrics
        
        mock_state_manager = Mock()
        mock_state_manager.get_storage_stats.return_value = mock_storage_stats
        
        mock_saga_orchestrator = Mock()
        mock_saga_orchestrator.get_orchestrator_metrics.return_value = mock_saga_metrics
        
        with patch('services.monitoring_dashboard.resilience_manager', mock_resilience_manager), \
             patch('services.monitoring_dashboard.PersistentStateManager', return_value=mock_state_manager), \
             patch('services.monitoring_dashboard.saga_orchestrator', mock_saga_orchestrator):
            
            monitoring_task = asyncio.create_task(dashboard.start_monitoring(interval_seconds=0.1))
            
            await asyncio.sleep(0.3)
            
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            assert len(dashboard.metrics_history) >= 2
    
    @pytest.mark.asyncio
    async def test_start_monitoring_error_recovery(self, dashboard):
        """Test monitoring loop continues after errors"""
        call_count = 0
        
        def mock_collect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception('First call fails')
            return AsyncMock()
        
        dashboard.collect_metrics = mock_collect
        
        monitoring_task = asyncio.create_task(dashboard.start_monitoring(interval_seconds=0.1))
        
        await asyncio.sleep(0.3)
        
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass
        
        assert call_count >= 2


class TestAlertThresholds:
    """Test alert threshold configuration"""
    
    def test_default_alert_thresholds(self, dashboard):
        """Test default alert thresholds"""
        assert dashboard.alert_thresholds['error_rate'] == 0.05
        assert dashboard.alert_thresholds['latency_p95'] == 1000
        assert dashboard.alert_thresholds['circuit_breaker_open'] is True
        assert dashboard.alert_thresholds['storage_errors'] == 10
    
    def test_custom_alert_thresholds(self):
        """Test custom alert thresholds"""
        dashboard = MonitoringDashboard()
        dashboard.alert_thresholds['error_rate'] = 0.10
        dashboard.alert_thresholds['latency_p95'] = 2000
        
        assert dashboard.alert_thresholds['error_rate'] == 0.10
        assert dashboard.alert_thresholds['latency_p95'] == 2000
