"""
Unit tests for services.report_generator module

Tests report generation functionality including:
- Report generation for different types (performance, task_tracking, resilience, financial)
- CSV and PDF export
- Time range parsing
- Helper methods for calculations and summaries
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta
import io
import json


class TestReportGenerator:
    """Test ReportGenerator class initialization"""
    
    def test_init(self):
        """Should initialize ReportGenerator with logger"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator.logger is not None


class TestGenerateReport:
    """Test report generation dispatcher"""
    
    def test_generate_report_performance(self):
        """Should generate performance report"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch.object(generator, '_generate_performance_report') as mock_perf:
            mock_perf.return_value = Mock(title="Performance Report")
            
            result = generator.generate_report('performance', '24h')
            
            mock_perf.assert_called_once_with('24h')
            assert result.title == "Performance Report"
    
    def test_generate_report_task_tracking(self):
        """Should generate task tracking report"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch.object(generator, '_generate_task_tracking_report') as mock_task:
            mock_task.return_value = Mock(title="Task Tracking Report")
            
            result = generator.generate_report('task_tracking', '7d')
            
            mock_task.assert_called_once_with('7d')
            assert result.title == "Task Tracking Report"
    
    def test_generate_report_resilience(self):
        """Should generate resilience report"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch.object(generator, '_generate_resilience_report') as mock_res:
            mock_res.return_value = Mock(title="Resilience Report")
            
            result = generator.generate_report('resilience', '1w')
            
            mock_res.assert_called_once_with('1w')
            assert result.title == "Resilience Report"
    
    def test_generate_report_financial(self):
        """Should generate financial report"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch.object(generator, '_generate_financial_report') as mock_fin:
            mock_fin.return_value = Mock(title="Financial Report")
            
            result = generator.generate_report('financial', '30d')
            
            mock_fin.assert_called_once_with('30d')
            assert result.title == "Financial Report"
    
    def test_generate_report_unsupported_type(self):
        """Should raise ValueError for unsupported report type"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with pytest.raises(ValueError, match="Unsupported report type"):
            generator.generate_report('invalid_type', '24h')


class TestGeneratePerformanceReport:
    """Test performance report generation"""
    
    def test_generate_performance_report_success(self):
        """Should generate performance report with dashboard data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        mock_dashboard_data = {
            'system_health': {
                'error_rate': 0.02,
                'avg_latency': 145.0,
                'total_requests': 15420,
                'successful_requests': 15111
            }
        }
        
        with patch('services.monitoring_dashboard.monitoring_dashboard') as mock_dashboard:
            mock_dashboard.get_dashboard_data.return_value = mock_dashboard_data
            
            result = generator._generate_performance_report('24h')
            
            assert result.title == "系統性能報告 - 24h"
            assert result.time_range == '24h'
            assert result.metrics['error_rate'] == 0.02
            assert result.metrics['avg_response_time'] == 145.0
            assert result.metrics['total_requests'] == 15420
    
    def test_generate_performance_report_error_handling(self):
        """Should handle errors and return mock data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch('services.monitoring_dashboard.monitoring_dashboard') as mock_dashboard:
            mock_dashboard.get_dashboard_data.side_effect = Exception("Dashboard error")
            
            result = generator._generate_performance_report('24h')
            
            assert result.title == "系統性能報告 - 24h"
            assert 'avg_response_time' in result.metrics
            assert result.summary['status'] == 'error'


class TestGenerateTaskTrackingReport:
    """Test task tracking report generation"""
    
    def test_generate_task_tracking_report_success(self):
        """Should generate task tracking report"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch('services.monitoring_dashboard.monitoring_dashboard'):
            result = generator._generate_task_tracking_report('7d')
            
            assert result.title == "任務追蹤報告 - 7d"
            assert result.time_range == '7d'
            assert result.metrics['total_tasks_executed'] == 156
            assert result.metrics['success_rate'] == 0.955
            assert 'agent_performance' in result.metrics
    
    def test_generate_task_tracking_report_error_handling(self):
        """Should handle errors and return mock data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch('services.monitoring_dashboard.monitoring_dashboard') as mock_dashboard:
            mock_dashboard.get_dashboard_data.side_effect = Exception("Dashboard error")
            
            result = generator._generate_task_tracking_report('7d')
            
            assert result.title == "任務追蹤報告 - 7d"
            assert 'total_tasks_executed' in result.metrics
            assert result.summary['status'] == 'error'


class TestGenerateResilienceReport:
    """Test resilience report generation"""
    
    def test_generate_resilience_report_success(self):
        """Should generate resilience report with circuit breaker data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        mock_dashboard_data = {
            'circuit_breakers': [
                {'state': 'closed', 'name': 'cb1'},
                {'state': 'open', 'name': 'cb2'},
                {'state': 'closed', 'name': 'cb3'}
            ],
            'bulkheads': [
                {'rejected_requests': 5, 'utilization': 45.2},
                {'rejected_requests': 7, 'utilization': 52.1}
            ],
            'system_health': {}
        }
        
        with patch('services.monitoring_dashboard.monitoring_dashboard') as mock_dashboard:
            mock_dashboard.get_dashboard_data.return_value = mock_dashboard_data
            
            result = generator._generate_resilience_report('1w')
            
            assert result.title == "韌性模式報告 - 1w"
            assert result.metrics['circuit_breaker_count'] == 3
            assert result.metrics['open_circuit_breakers'] == 1
            assert result.metrics['bulkhead_count'] == 2
            assert result.metrics['total_rejected_requests'] == 12
    
    def test_generate_resilience_report_error_handling(self):
        """Should handle errors and return mock data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        with patch('services.monitoring_dashboard.monitoring_dashboard') as mock_dashboard:
            mock_dashboard.get_dashboard_data.side_effect = Exception("Dashboard error")
            
            result = generator._generate_resilience_report('1w')
            
            assert result.title == "韌性模式報告 - 1w"
            assert 'circuit_breaker_count' in result.metrics
            assert result.summary['status'] == 'error'


class TestGenerateFinancialReport:
    """Test financial report generation"""
    
    def test_generate_financial_report(self):
        """Should generate financial report with cost data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._generate_financial_report('30d')
        
        assert result.title == "成本分析報告 - 30d"
        assert result.time_range == '30d'
        assert result.metrics['total_cost'] == 145.67
        assert result.metrics['compute_cost'] == 89.23
        assert result.metrics['cost_per_request'] == 0.0023
        assert result.metrics['resource_efficiency'] == 0.87


class TestExportCSV:
    """Test CSV export functionality"""
    
    def test_export_csv_basic(self):
        """Should export report data to CSV format"""
        from services.report_generator import ReportGenerator, ReportData
        
        generator = ReportGenerator()
        report_data = ReportData(
            title="Test Report",
            generated_at=datetime(2025, 1, 15, 10, 30, 0),
            time_range="24h",
            metrics={'metric1': 100, 'metric2': 200},
            charts=[],
            summary={'status': 'good'}
        )
        
        result = generator.export_csv(report_data)
        
        assert "Test Report" in result
        assert "2025-01-15 10:30:00" in result
        assert "24h" in result
        assert "metric1" in result
        assert "100" in result
        assert "status" in result
        assert "good" in result
    
    def test_export_csv_with_nested_dict(self):
        """Should handle nested dictionary in metrics"""
        from services.report_generator import ReportGenerator, ReportData
        
        generator = ReportGenerator()
        report_data = ReportData(
            title="Test Report",
            generated_at=datetime(2025, 1, 15, 10, 30, 0),
            time_range="24h",
            metrics={'nested': {'key1': 'value1', 'key2': 'value2'}},
            charts=[],
            summary={}
        )
        
        result = generator.export_csv(report_data)
        
        assert "nested" in result
        assert '"key1"' in result or 'key1' in result


class TestExportPDF:
    """Test PDF export functionality"""
    
    def test_export_pdf_without_reportlab(self):
        """Should raise ImportError when reportlab not available"""
        from services.report_generator import ReportGenerator, ReportData
        
        generator = ReportGenerator()
        report_data = ReportData(
            title="Test Report",
            generated_at=datetime.now(),
            time_range="24h",
            metrics={},
            charts=[],
            summary={}
        )
        
        with patch('services.report_generator.REPORTLAB_AVAILABLE', False):
            with pytest.raises(ImportError, match="ReportLab not available"):
                generator.export_pdf(report_data, 'performance')
    
    def test_export_pdf_with_reportlab(self):
        """Should generate PDF when reportlab is available"""
        from services.report_generator import ReportGenerator, ReportData
        
        generator = ReportGenerator()
        report_data = ReportData(
            title="Test Report",
            generated_at=datetime(2025, 1, 15, 10, 30, 0),
            time_range="24h",
            metrics={'metric1': 100, 'metric2': 200},
            charts=[],
            summary={'status': 'good', 'message': 'All systems operational'}
        )
        
        with patch('services.report_generator.REPORTLAB_AVAILABLE', True):
            with patch('services.report_generator.SimpleDocTemplate') as mock_doc:
                with patch('services.report_generator.getSampleStyleSheet') as mock_styles:
                    mock_doc_instance = MagicMock()
                    mock_doc.return_value = mock_doc_instance
                    mock_styles.return_value = {'Title': Mock(), 'Normal': Mock(), 'Heading2': Mock()}
                    
                    result = generator.export_pdf(report_data, 'performance')
                    
                    assert 'report_performance_' in result
                    assert result.endswith('.pdf')
                    mock_doc_instance.build.assert_called_once()


class TestParseTimeRange:
    """Test time range parsing"""
    
    def test_parse_time_range_hours(self):
        """Should parse hours format"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator._parse_time_range('24h') == 24
        assert generator._parse_time_range('1h') == 1
        assert generator._parse_time_range('48h') == 48
    
    def test_parse_time_range_days(self):
        """Should parse days format"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator._parse_time_range('1d') == 24
        assert generator._parse_time_range('7d') == 168
        assert generator._parse_time_range('30d') == 720
    
    def test_parse_time_range_weeks(self):
        """Should parse weeks format"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator._parse_time_range('1w') == 168
        assert generator._parse_time_range('2w') == 336
    
    def test_parse_time_range_default(self):
        """Should return default 24 hours for invalid format"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        assert generator._parse_time_range('') == 24


class TestCalculateAvgResponseTime:
    """Test average response time calculation"""
    
    def test_calculate_avg_response_time(self):
        """Should extract avg_latency from dashboard data"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        dashboard_data = {
            'system_health': {
                'avg_latency': 123.45
            }
        }
        
        result = generator._calculate_avg_response_time(dashboard_data)
        
        assert result == 123.45
    
    def test_calculate_avg_response_time_missing_data(self):
        """Should return default when data missing"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        dashboard_data = {'system_health': {}}
        
        result = generator._calculate_avg_response_time(dashboard_data)
        
        assert result == 145.0


class TestCalculateUptime:
    """Test uptime calculation"""
    
    def test_calculate_uptime(self):
        """Should return mock uptime value"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._calculate_uptime({})
        
        assert result == 99.7


class TestGetPeakMetric:
    """Test peak metric retrieval"""
    
    def test_get_peak_metric_cpu(self):
        """Should return peak CPU usage"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_peak_metric({}, 'cpu')
        
        assert result == 85.2
    
    def test_get_peak_metric_memory(self):
        """Should return peak memory usage"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_peak_metric({}, 'memory')
        
        assert result == 78.9
    
    def test_get_peak_metric_unknown(self):
        """Should return 0 for unknown metric"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_peak_metric({}, 'unknown')
        
        assert result == 0.0


class TestCalculateAvgBulkheadUtilization:
    """Test bulkhead utilization calculation"""
    
    def test_calculate_avg_bulkhead_utilization_with_data(self):
        """Should calculate average utilization"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        bulkheads = [
            {'utilization': 45.2},
            {'utilization': 52.1},
            {'utilization': 38.7}
        ]
        
        result = generator._calculate_avg_bulkhead_utilization(bulkheads)
        
        assert result == pytest.approx(45.33, rel=0.01)
    
    def test_calculate_avg_bulkhead_utilization_empty(self):
        """Should return 0 for empty bulkheads"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._calculate_avg_bulkhead_utilization([])
        
        assert result == 0.0


class TestCalculateStabilityScore:
    """Test stability score calculation"""
    
    def test_calculate_stability_score_healthy(self):
        """Should calculate high score for healthy system"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        dashboard_data = {
            'system_health': {
                'error_rate': 0.01,
                'open_circuit_breakers': 0
            }
        }
        
        result = generator._calculate_stability_score(dashboard_data)
        
        assert result == 90.0
    
    def test_calculate_stability_score_degraded(self):
        """Should calculate lower score for degraded system"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        dashboard_data = {
            'system_health': {
                'error_rate': 0.05,
                'open_circuit_breakers': 2
            }
        }
        
        result = generator._calculate_stability_score(dashboard_data)
        
        assert result == 30.0
    
    def test_calculate_stability_score_bounds(self):
        """Should clamp score between 0 and 100"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        dashboard_data = {
            'system_health': {
                'error_rate': 1.0,
                'open_circuit_breakers': 50
            }
        }
        
        result = generator._calculate_stability_score(dashboard_data)
        
        assert result == 0.0


class TestGenerateSummaries:
    """Test summary generation methods"""
    
    def test_generate_performance_summary_healthy(self):
        """Should generate healthy performance summary"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        metrics = {
            'error_rate': 0.02,
            'avg_response_time': 145.0,
            'uptime_percentage': 99.7
        }
        
        result = generator._generate_performance_summary(metrics)
        
        assert result['系統狀態'] == '良好'
        assert '145.0ms' in result['平均響應時間']
        assert '99.7%' in result['系統可用性']
    
    def test_generate_performance_summary_needs_attention(self):
        """Should flag system needing attention"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        metrics = {
            'error_rate': 0.06,
            'avg_response_time': 500.0,
            'uptime_percentage': 95.0
        }
        
        result = generator._generate_performance_summary(metrics)
        
        assert result['系統狀態'] == '需要關注'
    
    def test_generate_task_tracking_summary(self):
        """Should generate task tracking summary"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        metrics = {
            'success_rate': 0.955,
            'total_tasks_executed': 156,
            'avg_task_duration': 3.2
        }
        
        result = generator._generate_task_tracking_summary(metrics)
        
        assert '95.5%' in result['任務成功率']
        assert result['總執行任務'] == 156
        assert '3.2秒' in result['平均執行時間']
    
    def test_generate_resilience_summary(self):
        """Should generate resilience summary"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        metrics = {
            'system_stability_score': 94.5,
            'open_circuit_breakers': 0,
            'mttr_minutes': 4.2
        }
        
        result = generator._generate_resilience_summary(metrics)
        
        assert '94.5/100' in result['系統穩定性評分']
        assert result['開啟的熔斷器'] == 0
        assert '4.2分鐘' in result['平均恢復時間']
    
    def test_generate_financial_summary(self):
        """Should generate financial summary"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        metrics = {
            'total_cost': 145.67,
            'cost_per_request': 0.0023,
            'resource_efficiency': 0.87,
            'cost_trend': 'decreasing'
        }
        
        result = generator._generate_financial_summary(metrics)
        
        assert '$145.67' in result['總成本']
        assert '$0.0023' in result['每請求成本']
        assert '87.0%' in result['資源效率']
        assert result['成本趨勢'] == 'decreasing'


class TestGetMockMetrics:
    """Test mock metrics retrieval"""
    
    def test_get_mock_performance_metrics(self):
        """Should return mock performance metrics"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_mock_performance_metrics()
        
        assert result['avg_response_time'] == 145.0
        assert result['error_rate'] == 0.02
        assert result['uptime_percentage'] == 99.7
        assert result['total_requests'] == 15420
    
    def test_get_mock_task_metrics(self):
        """Should return mock task metrics"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_mock_task_metrics()
        
        assert result['total_tasks_executed'] == 156
        assert result['successful_tasks'] == 149
        assert result['failed_tasks'] == 7
        assert result['success_rate'] == 0.955
    
    def test_get_mock_resilience_metrics(self):
        """Should return mock resilience metrics"""
        from services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        result = generator._get_mock_resilience_metrics()
        
        assert result['circuit_breaker_count'] == 5
        assert result['open_circuit_breakers'] == 0
        assert result['bulkhead_count'] == 3
        assert result['system_stability_score'] == 94.5
