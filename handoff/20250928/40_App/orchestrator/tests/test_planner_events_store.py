#!/usr/bin/env python3
"""
Unit tests for planner_events_store module

Tests database operations for planner events storage.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from persistence.planner_events_store import (
    insert_planner_event,
    query_planner_events,
    get_planner_stats_summary
)


class TestInsertPlannerEvent:
    """Tests for insert_planner_event function"""

    @patch('persistence.planner_events_store.get_client')
    def test_insert_planner_event_success(self, mock_get_client):
        """Test successful planner event insertion"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock()
        
        # Test data
        trace_id = "test-trace-123"
        goal = "Test goal"
        planner_type = "llm"
        task_type = "codegen"
        actual_plan_steps = ["step1", "step2", "step3"]
        planning_time_ms = 1500.0
        timestamp = datetime(2025, 11, 27, 1, 0, 0, tzinfo=timezone.utc)
        
        # Execute
        result = insert_planner_event(
            trace_id=trace_id,
            goal=goal,
            planner_type=planner_type,
            task_type=task_type,
            actual_plan_steps=actual_plan_steps,
            planning_time_ms=planning_time_ms,
            timestamp=timestamp
        )
        
        # Verify
        assert result is True
        mock_client.table.assert_called_once_with("planner_events")
        
        # Verify insert was called with correct data
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["trace_id"] == trace_id
        assert call_args["goal"] == goal
        assert call_args["planner_type"] == planner_type
        assert call_args["task_type"] == task_type
        assert call_args["actual_plan_steps"] == actual_plan_steps
        assert call_args["num_steps"] == 3
        assert call_args["planning_time_ms"] == planning_time_ms
        assert call_args["timestamp"] == timestamp.isoformat()

    @patch('persistence.planner_events_store.get_client')
    def test_insert_planner_event_default_timestamp(self, mock_get_client):
        """Test insertion with default timestamp"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock()
        
        # Execute without timestamp
        result = insert_planner_event(
            trace_id="test-123",
            goal="Test",
            planner_type="llm",
            task_type="codegen",
            actual_plan_steps=["step1"],
            planning_time_ms=1000.0
        )
        
        # Verify
        assert result is True
        call_args = mock_table.insert.call_args[0][0]
        assert "timestamp" in call_args
        # Timestamp should be recent (within last minute)
        timestamp_str = call_args["timestamp"]
        assert isinstance(timestamp_str, str)

    @patch('persistence.planner_events_store.get_client')
    def test_insert_planner_event_failure(self, mock_get_client):
        """Test handling of insertion failure"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.table.side_effect = Exception("Database connection failed")
        
        # Execute
        result = insert_planner_event(
            trace_id="test-123",
            goal="Test",
            planner_type="llm",
            task_type="codegen",
            actual_plan_steps=["step1"],
            planning_time_ms=1000.0
        )
        
        # Verify
        assert result is False


class TestQueryPlannerEvents:
    """Tests for query_planner_events function"""

    @patch('persistence.planner_events_store.get_client')
    def test_query_all_events(self, mock_get_client):
        """Test querying all events"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_order = Mock()
        mock_execute = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.execute.return_value = Mock(data=[
            {"trace_id": "1", "planner_type": "llm", "num_steps": 3},
            {"trace_id": "2", "planner_type": "static", "num_steps": 5}
        ])
        
        # Execute
        events = query_planner_events()
        
        # Verify
        assert len(events) == 2
        assert events[0]["trace_id"] == "1"
        assert events[1]["trace_id"] == "2"
        mock_select.order.assert_called_once_with("timestamp", desc=True)

    @patch('persistence.planner_events_store.get_client')
    def test_query_with_limit(self, mock_get_client):
        """Test querying with limit"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        mock_execute = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[{"trace_id": "1"}])
        
        # Execute
        events = query_planner_events(limit=10)
        
        # Verify
        mock_order.limit.assert_called_once_with(10)

    @patch('persistence.planner_events_store.get_client')
    def test_query_with_planner_type_filter(self, mock_get_client):
        """Test querying with planner type filter"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute.return_value = Mock(data=[])
        
        # Execute
        events = query_planner_events(planner_type_filter="llm")
        
        # Verify
        mock_select.eq.assert_called_once_with("planner_type", "llm")

    @patch('persistence.planner_events_store.get_client')
    def test_query_with_trace_id(self, mock_get_client):
        """Test querying by trace_id"""
        # Setup mock
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        
        mock_get_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute.return_value = Mock(data=[{"trace_id": "test-123"}])
        
        # Execute
        events = query_planner_events(trace_id="test-123")
        
        # Verify
        assert len(events) == 1
        assert events[0]["trace_id"] == "test-123"
        mock_select.eq.assert_called_once_with("trace_id", "test-123")

    @patch('persistence.planner_events_store.get_client')
    def test_query_failure(self, mock_get_client):
        """Test handling of query failure"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.table.side_effect = Exception("Query failed")
        
        # Execute
        events = query_planner_events()
        
        # Verify
        assert events == []


class TestGetPlannerStatsSummary:
    """Tests for get_planner_stats_summary function"""

    @patch('persistence.planner_events_store.query_planner_events')
    def test_stats_summary_with_events(self, mock_query):
        """Test statistics summary calculation"""
        # Setup mock data
        mock_query.return_value = [
            {"planning_time_ms": 1000, "num_steps": 3},
            {"planning_time_ms": 2000, "num_steps": 5},
            {"planning_time_ms": 3000, "num_steps": 4},
        ]
        
        # Execute
        stats = get_planner_stats_summary()
        
        # Verify
        assert stats["count"] == 3
        assert stats["avg_planning_time_ms"] == 2000.0
        assert stats["median_planning_time_ms"] == 2000.0
        assert stats["avg_num_steps"] == 4.0
        assert stats["median_num_steps"] == 4.0

    @patch('persistence.planner_events_store.query_planner_events')
    def test_stats_summary_empty(self, mock_query):
        """Test statistics summary with no events"""
        # Setup mock
        mock_query.return_value = []
        
        # Execute
        stats = get_planner_stats_summary()
        
        # Verify
        assert stats["count"] == 0
        assert stats["avg_planning_time_ms"] == 0
        assert stats["median_planning_time_ms"] == 0

    @patch('persistence.planner_events_store.query_planner_events')
    def test_stats_summary_even_count(self, mock_query):
        """Test median calculation with even number of events"""
        # Setup mock data (even count)
        mock_query.return_value = [
            {"planning_time_ms": 1000, "num_steps": 3},
            {"planning_time_ms": 2000, "num_steps": 4},
            {"planning_time_ms": 3000, "num_steps": 5},
            {"planning_time_ms": 4000, "num_steps": 6},
        ]
        
        # Execute
        stats = get_planner_stats_summary()
        
        # Verify median is average of two middle values
        assert stats["median_planning_time_ms"] == 2500.0  # (2000 + 3000) / 2
        assert stats["median_num_steps"] == 4.5  # (4 + 5) / 2
