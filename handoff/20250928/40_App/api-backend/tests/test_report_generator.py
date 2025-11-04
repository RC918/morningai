#!/usr/bin/env python3
"""
Tests for Report Generator Service
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.services.report_generator import (
    ReportGenerator,
    ReportData,
    report_generator
)


class TestReportGenerator:
    """Test suite for ReportGenerator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ReportGenerator()
    
    def test_init(self):
        """Test report generator initialization"""
        generator = ReportGenerator()
        assert generator.logger is not None
    
    def test_generate_performance_report(self):
        """Test generating performance report"""
        report = self.generator.generate_report('performance', '24h')
        
        assert report.title.startswith('系統性能報告')
        assert report.time_range == '24h'
        assert 'avg_response_time' in report.metrics
        assert 'error_rate' in report.metrics
        assert 'uptime_percentage' in report.metrics
    
    def test_generate_task_tracking_report(self):
        """Test generating task tracking report"""
        report = self.generator.generate_report('task_tracking', '7d')
        
        assert report.title.startswith('任務追蹤報告')
        assert report.time_range == '7d'
        assert 'total_tasks_executed' in report.metrics
        assert 'success_rate' in report.metrics
        assert 'agent_performance' in report.metrics
    
    def test_generate_resilience_report(self):
        """Test generating resilience report"""
        report = self.generator.generate_report('resilience', '1h')
        
        assert report.title.startswith('韌性模式報告')
        assert report.time_range == '1h'
        assert 'circuit_breaker_count' in report.metrics
        assert 'bulkhead_count' in report.metrics
    
    def test_generate_financial_report(self):
        """Test generating financial report"""
        report = self.generator.generate_report('financial', '30d')
        
        assert report.title.startswith('成本分析報告')
        assert report.time_range == '30d'
        assert 'total_cost' in report.metrics
        assert 'compute_cost' in report.metrics
        assert 'storage_cost' in report.metrics
    
    def test_generate_report_unsupported_type(self):
        """Test generating report with unsupported type"""
        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_report('invalid_type', '24h')
        
        assert 'Unsupported report type' in str(exc_info.value)
    
    def test_export_csv(self):
        """Test exporting report as CSV"""
        report = ReportData(
            title='Test Report',
            generated_at=datetime.now(),
            time_range='24h',
            metrics={'metric1': 100, 'metric2': 200},
            charts=[],
            summary={'status': 'good'}
        )
        
        csv_output = self.generator.export_csv(report)
        
        assert 'Test Report' in csv_output
        assert 'metric1' in csv_output
        assert '100' in csv_output
    
    def test_parse_time_range_hours(self):
        """Test parsing time range in hours"""
        assert self.generator._parse_time_range('1h') == 1
        assert self.generator._parse_time_range('24h') == 24
    
    def test_parse_time_range_days(self):
        """Test parsing time range in days"""
        assert self.generator._parse_time_range('1d') == 24
        assert self.generator._parse_time_range('7d') == 168
    
    def test_parse_time_range_weeks(self):
        """Test parsing time range in weeks"""
        assert self.generator._parse_time_range('1w') == 168
        assert self.generator._parse_time_range('2w') == 336
    
    def test_parse_time_range_default(self):
        """Test parsing time range with invalid format"""
        assert self.generator._parse_time_range('24') == 24
    
    def test_calculate_avg_response_time(self):
        """Test calculating average response time"""
        dashboard_data = {
            'system_health': {
                'avg_latency': 123.45
            }
        }
        
        result = self.generator._calculate_avg_response_time(dashboard_data)
        assert result == 123.45
    
    def test_calculate_avg_response_time_missing(self):
        """Test calculating average response time with missing data"""
        dashboard_data = {'system_health': {}}
        
        result = self.generator._calculate_avg_response_time(dashboard_data)
        assert result == 145.0
    
    def test_calculate_uptime(self):
        """Test calculating uptime"""
        result = self.generator._calculate_uptime({})
        assert result == 99.7
    
    def test_get_peak_metric(self):
        """Test getting peak metric values"""
        assert self.generator._get_peak_metric({}, 'cpu') == 85.2
        assert self.generator._get_peak_metric({}, 'memory') == 78.9
        assert self.generator._get_peak_metric({}, 'invalid') == 0.0
    
    def test_calculate_avg_bulkhead_utilization(self):
        """Test calculating average bulkhead utilization"""
        bulkheads = [
            {'utilization': 50.0},
            {'utilization': 60.0},
            {'utilization': 70.0}
        ]
        
        result = self.generator._calculate_avg_bulkhead_utilization(bulkheads)
        assert result == 60.0
    
    def test_calculate_avg_bulkhead_utilization_empty(self):
        """Test calculating average bulkhead utilization with empty list"""
        result = self.generator._calculate_avg_bulkhead_utilization([])
        assert result == 0.0
    
    def test_calculate_stability_score(self):
        """Test calculating system stability score"""
        dashboard_data = {
            'system_health': {
                'error_rate': 0.01,
                'open_circuit_breakers': 1
            }
        }
        
        result = self.generator._calculate_stability_score(dashboard_data)
        assert 0 <= result <= 100
    
    def test_calculate_stability_score_perfect(self):
        """Test calculating stability score with perfect metrics"""
        dashboard_data = {
            'system_health': {
                'error_rate': 0.0,
                'open_circuit_breakers': 0
            }
        }
        
        result = self.generator._calculate_stability_score(dashboard_data)
        assert result == 100.0
    
    def test_generate_performance_summary(self):
        """Test generating performance summary"""
        metrics = {
            'error_rate': 0.02,
            'avg_response_time': 150.0,
            'uptime_percentage': 99.5
        }
        
        summary = self.generator._generate_performance_summary(metrics)
        
        assert '系統狀態' in summary
        assert '平均響應時間' in summary
        assert '150.0ms' in summary['平均響應時間']
    
    def test_generate_task_tracking_summary(self):
        """Test generating task tracking summary"""
        metrics = {
            'success_rate': 0.955,
            'total_tasks_executed': 156,
            'avg_task_duration': 3.2
        }
        
        summary = self.generator._generate_task_tracking_summary(metrics)
        
        assert '任務成功率' in summary
        assert '總執行任務' in summary
        assert summary['總執行任務'] == 156
    
    def test_generate_resilience_summary(self):
        """Test generating resilience summary"""
        metrics = {
            'system_stability_score': 94.5,
            'open_circuit_breakers': 1,
            'mttr_minutes': 4.2
        }
        
        summary = self.generator._generate_resilience_summary(metrics)
        
        assert '系統穩定性評分' in summary
        assert '開啟的熔斷器' in summary
        assert summary['開啟的熔斷器'] == 1
    
    def test_generate_financial_summary(self):
        """Test generating financial summary"""
        metrics = {
            'total_cost': 145.67,
            'cost_per_request': 0.0023,
            'resource_efficiency': 0.87,
            'cost_trend': 'decreasing'
        }
        
        summary = self.generator._generate_financial_summary(metrics)
        
        assert '總成本' in summary
        assert '$145.67' in summary['總成本']
        assert '成本趨勢' in summary
    
    def test_get_mock_performance_metrics(self):
        """Test getting mock performance metrics"""
        metrics = self.generator._get_mock_performance_metrics()
        
        assert 'avg_response_time' in metrics
        assert 'error_rate' in metrics
        assert 'uptime_percentage' in metrics
        assert metrics['avg_response_time'] == 145.0
    
    def test_get_mock_task_metrics(self):
        """Test getting mock task metrics"""
        metrics = self.generator._get_mock_task_metrics()
        
        assert 'total_tasks_executed' in metrics
        assert 'success_rate' in metrics
        assert metrics['total_tasks_executed'] == 156
    
    def test_get_mock_resilience_metrics(self):
        """Test getting mock resilience metrics"""
        metrics = self.generator._get_mock_resilience_metrics()
        
        assert 'circuit_breaker_count' in metrics
        assert 'bulkhead_count' in metrics
        assert metrics['circuit_breaker_count'] == 5


class TestReportData:
    """Test suite for ReportData dataclass"""
    
    def test_report_data_creation(self):
        """Test creating ReportData instance"""
        report = ReportData(
            title='Test Report',
            generated_at=datetime.now(),
            time_range='24h',
            metrics={'test': 123},
            charts=[],
            summary={'status': 'ok'}
        )
        
        assert report.title == 'Test Report'
        assert report.time_range == '24h'
        assert report.metrics['test'] == 123
        assert report.summary['status'] == 'ok'
