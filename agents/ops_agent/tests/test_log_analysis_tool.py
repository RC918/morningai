#!/usr/bin/env python3
"""
Tests for Log Analysis Tool
"""
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.log_analysis_tool import LogAnalysisTool, LogLevel, create_log_analysis_tool


class TestLogAnalysisTool:
    """Tests for LogAnalysisTool"""
    
    @pytest.fixture
    def log_tool(self):
        """Create log analysis tool for testing"""
        return LogAnalysisTool()
    
    def test_initialization(self, log_tool):
        """Test LogAnalysisTool initialization"""
        assert log_tool.logs == []
        assert log_tool.error_patterns == {}
    
    @pytest.mark.asyncio
    async def test_add_log_entry(self, log_tool):
        """Test adding a log entry"""
        result = await log_tool.add_log_entry(
            message="Test log message",
            level="info",
            source="test",
            metadata={"user_id": "123"}
        )
        
        assert result['success'] is True
        assert 'log_id' in result
        assert len(log_tool.logs) == 1
        assert log_tool.logs[0].message == "Test log message"
        assert log_tool.logs[0].level == LogLevel.INFO
    
    @pytest.mark.asyncio
    async def test_search_logs_by_query(self, log_tool):
        """Test searching logs by query"""
        await log_tool.add_log_entry("Error occurred", "error")
        await log_tool.add_log_entry("Success message", "info")
        await log_tool.add_log_entry("Another error", "error")
        
        result = await log_tool.search_logs(query="error")
        
        assert result['success'] is True
        assert result['total'] == 2
        assert len(result['logs']) == 2
    
    @pytest.mark.asyncio
    async def test_search_logs_by_severity(self, log_tool):
        """Test searching logs by severity"""
        await log_tool.add_log_entry("Info message", "info")
        await log_tool.add_log_entry("Error message", "error")
        await log_tool.add_log_entry("Critical message", "critical")
        
        result = await log_tool.search_logs(query="", severity="error")
        
        assert result['success'] is True
        assert result['total'] == 1
        assert result['logs'][0]['level'] == 'error'
    
    @pytest.mark.asyncio
    async def test_search_logs_with_limit(self, log_tool):
        """Test searching logs with limit"""
        for i in range(20):
            await log_tool.add_log_entry(f"Log {i}", "info")
        
        result = await log_tool.search_logs(query="Log", limit=10)
        
        assert result['success'] is True
        assert result['total'] == 10
    
    @pytest.mark.asyncio
    async def test_analyze_error_patterns(self, log_tool):
        """Test analyzing error patterns"""
        await log_tool.add_log_entry("KeyError: 'user_id'", "error")
        await log_tool.add_log_entry("KeyError: 'name'", "error")
        await log_tool.add_log_entry("ValueError: invalid input", "error")
        await log_tool.add_log_entry("Info message", "info")
        
        result = await log_tool.analyze_error_patterns(time_range="1h")
        
        assert result['success'] is True
        assert result['total_errors'] == 3
        assert result['unique_patterns'] > 0
        assert len(result['patterns']) > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies_no_spike(self, log_tool):
        """Test anomaly detection with normal error rate"""
        for i in range(5):
            await log_tool.add_log_entry(f"Error {i}", "error")
        
        result = await log_tool.detect_anomalies()
        
        assert result['success'] is True
        assert result['total_anomalies'] == 0
    
    @pytest.mark.asyncio
    async def test_parse_time_range_hours(self, log_tool):
        """Test parsing time range in hours"""
        cutoff = log_tool._parse_time_range("2h")
        
        expected = datetime.utcnow() - timedelta(hours=2)
        assert abs((cutoff - expected).total_seconds()) < 2
    
    @pytest.mark.asyncio
    async def test_parse_time_range_days(self, log_tool):
        """Test parsing time range in days"""
        cutoff = log_tool._parse_time_range("7d")
        
        expected = datetime.utcnow() - timedelta(days=7)
        assert abs((cutoff - expected).total_seconds()) < 2
    
    @pytest.mark.asyncio
    async def test_search_logs_with_time_range(self, log_tool):
        """Test searching logs with time range filter"""
        await log_tool.add_log_entry("Recent log", "info")
        
        result = await log_tool.search_logs(query="log", time_range="1h")
        
        assert result['success'] is True


class TestLogAnalysisToolFactory:
    """Tests for log analysis tool factory function"""
    
    def test_create_log_analysis_tool(self):
        """Test factory function"""
        tool = create_log_analysis_tool()
        
        assert isinstance(tool, LogAnalysisTool)
        assert tool.logs == []


class TestLogAnalysisToolEdgeCases:
    """Edge case tests for LogAnalysisTool"""
    
    @pytest.fixture
    def log_tool(self):
        return LogAnalysisTool()
    
    @pytest.mark.asyncio
    async def test_search_empty_logs(self, log_tool):
        """Test searching with no logs"""
        result = await log_tool.search_logs(query="test")
        
        assert result['success'] is True
        assert result['total'] == 0
        assert result['logs'] == []
    
    @pytest.mark.asyncio
    async def test_add_log_invalid_level(self, log_tool):
        """Test adding log with invalid level"""
        result = await log_tool.add_log_entry(
            message="Test",
            level="invalid_level"
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_search_logs_no_matches(self, log_tool):
        """Test searching logs with no matches"""
        await log_tool.add_log_entry("Log message", "info")
        
        result = await log_tool.search_logs(query="nomatch")
        
        assert result['success'] is True
        assert result['total'] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_error_patterns_no_errors(self, log_tool):
        """Test error pattern analysis with no errors"""
        await log_tool.add_log_entry("Info message", "info")
        
        result = await log_tool.analyze_error_patterns()
        
        assert result['success'] is True
        assert result['total_errors'] == 0
        assert result['unique_patterns'] == 0
    
    @pytest.mark.asyncio
    async def test_parse_invalid_time_range(self, log_tool):
        """Test parsing invalid time range"""
        with pytest.raises(ValueError):
            log_tool._parse_time_range("invalid")
    
    @pytest.mark.asyncio
    async def test_extract_error_pattern(self, log_tool):
        """Test error pattern extraction"""
        patterns = [
            ("KeyError: 'user_id'", "KeyError"),
            ("ValueError: invalid input", "ValueError"),
            ("Failed to connect to database", "Failed to connect"),
        ]
        
        for message, expected_pattern in patterns:
            pattern = log_tool._extract_error_pattern(message)
            assert expected_pattern in pattern or pattern == message[:50]
    
    @pytest.mark.asyncio
    async def test_add_log_with_metadata(self, log_tool):
        """Test adding log with complex metadata"""
        metadata = {
            "user_id": "123",
            "endpoint": "/api/users",
            "duration_ms": 250,
            "nested": {"key": "value"}
        }
        
        result = await log_tool.add_log_entry(
            message="Request completed",
            level="info",
            metadata=metadata
        )
        
        assert result['success'] is True
        assert log_tool.logs[0].metadata == metadata


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
