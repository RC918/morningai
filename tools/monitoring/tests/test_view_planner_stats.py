"""
Tests for view_planner_stats.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Import functions from view_planner_stats
sys.path.insert(0, str(Path(__file__).parent.parent))
from view_planner_stats import (  # noqa: E402
    load_planner_events,
    compute_statistics,
    format_statistics,
    show_recent_entries
)


@pytest.fixture
def sample_events():
    """Sample planner events for testing"""
    return [
        {
            "trace_id": "test-trace-1",
            "goal": "[Phase1-Test] Create a function",
            "planner_type": "llm",
            "task_type": "code_generation",
            "actual_plan_steps": ["step1", "step2", "step3"],
            "num_steps": 3,
            "planning_time_ms": 5000.0,
            "timestamp": "2025-11-26T10:00:00.000000"
        },
        {
            "trace_id": "test-trace-2",
            "goal": "[Phase1-Test] Fix a bug",
            "planner_type": "llm",
            "task_type": "bug_fix",
            "actual_plan_steps": ["step1", "step2", "step3", "step4", "step5"],
            "num_steps": 5,
            "planning_time_ms": 8000.0,
            "timestamp": "2025-11-26T10:05:00.000000"
        },
        {
            "trace_id": "test-trace-3",
            "goal": "[Phase1-Test] Refactor code",
            "planner_type": "llm",
            "task_type": "refactoring",
            "actual_plan_steps": ["step1", "step2", "step3", "step4", "step5", "step6", "step7"],
            "num_steps": 7,
            "planning_time_ms": 12000.0,
            "timestamp": "2025-11-26T10:10:00.000000"
        },
        {
            "trace_id": "test-trace-4",
            "goal": "Regular task without prefix",
            "planner_type": "static",
            "task_type": "code_generation",
            "actual_plan_steps": ["step1", "step2", "step3", "step4"],
            "num_steps": 4,
            "planning_time_ms": 3000.0,
            "timestamp": "2025-11-26T10:15:00.000000"
        }
    ]


@pytest.fixture
def temp_jsonl_file(sample_events):
    """Create temporary JSONL file with sample events"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for event in sample_events:
            f.write(json.dumps(event) + '\n')
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


def test_load_planner_events(temp_jsonl_file, sample_events):
    """Test loading planner events from JSONL file"""
    events = load_planner_events(temp_jsonl_file)

    assert len(events) == len(sample_events)
    assert events[0]['trace_id'] == 'test-trace-1'
    assert events[1]['num_steps'] == 5
    assert events[2]['planning_time_ms'] == 12000.0


def test_load_planner_events_with_filter(temp_jsonl_file):
    """Test loading planner events with goal filter"""
    events = load_planner_events(temp_jsonl_file, filter_goal="[Phase1-Test]")

    assert len(events) == 3  # Only Phase1-Test tasks
    assert all("[Phase1-Test]" in e['goal'] for e in events)


def test_load_planner_events_nonexistent_file():
    """Test loading from nonexistent file"""
    events = load_planner_events("/nonexistent/path/file.jsonl")

    assert events == []


def test_compute_statistics(sample_events):
    """Test computing statistics from events"""
    stats = compute_statistics(sample_events)

    # Check total count
    assert stats['total_count'] == 4

    # Check planning time statistics
    assert stats['time_min'] == 3.0  # 3000ms = 3s
    assert stats['time_max'] == 12.0  # 12000ms = 12s
    assert stats['time_mean'] == 7.0  # (5+8+12+3)/4 = 7s
    assert stats['time_median'] == 6.5  # median of [3, 5, 8, 12] = (5+8)/2 = 6.5

    # Check step distribution
    assert stats['step_counts'][3] == 1
    assert stats['step_counts'][4] == 1
    assert stats['step_counts'][5] == 1
    assert stats['step_counts'][7] == 1

    # Check planner type distribution
    assert stats['planner_types']['llm'] == 3
    assert stats['planner_types']['static'] == 1

    # Check task type distribution
    assert stats['task_types']['code_generation'] == 2
    assert stats['task_types']['bug_fix'] == 1
    assert stats['task_types']['refactoring'] == 1

    # Check timestamps
    assert stats['first_timestamp'] == "2025-11-26T10:00:00.000000"
    assert stats['last_timestamp'] == "2025-11-26T10:15:00.000000"


def test_compute_statistics_empty():
    """Test computing statistics from empty events list"""
    stats = compute_statistics([])

    assert stats == {}


def test_format_statistics(sample_events, temp_jsonl_file):
    """Test formatting statistics as string"""
    stats = compute_statistics(sample_events)
    output = format_statistics(stats, temp_jsonl_file)

    # Check key sections are present
    assert "Planner Statistics" in output
    assert "Total Planner Runs: 4" in output
    assert "Planning Time" in output
    assert "Plan Steps Distribution" in output
    assert "Planner Type Distribution" in output
    assert "Task Type Distribution" in output
    assert "Timeline" in output


def test_format_statistics_empty(temp_jsonl_file):
    """Test formatting empty statistics"""
    stats = compute_statistics([])
    output = format_statistics(stats, temp_jsonl_file)

    assert "No planner events found" in output


def test_show_recent_entries(sample_events):
    """Test showing recent entries"""
    output = show_recent_entries(sample_events, 2)

    assert "Last 2 Entries" in output
    assert "test-trace-4" in output  # Most recent
    assert "test-trace-3" in output  # Second most recent
    assert "test-trace-1" not in output  # Not in last 2


def test_show_recent_entries_more_than_available(sample_events):
    """Test showing more recent entries than available"""
    output = show_recent_entries(sample_events, 10)

    assert "Last 4 Entries" in output  # Shows all 4
    assert "test-trace-1" in output
    assert "test-trace-4" in output


def test_show_recent_entries_empty():
    """Test showing recent entries with empty list"""
    output = show_recent_entries([], 5)

    assert output == "No entries to display"


def test_path_resolution_with_env_var(tmp_path, monkeypatch):
    """Test path resolution with environment variable override"""
    from common.utils.path_utils import resolve_planner_events_path
    
    # Test with absolute path
    abs_path = str(tmp_path / "custom" / "events.jsonl")
    monkeypatch.setenv('PLANNER_EVENTS_FILE', abs_path)
    
    resolved = resolve_planner_events_path()
    assert resolved == abs_path


def test_path_resolution_default():
    """Test path resolution with default relative path"""
    from common.utils.path_utils import resolve_planner_events_path
    
    resolved = resolve_planner_events_path()
    # Should end with the default path
    assert resolved.endswith('tools/agent_eval/data/planner_runs.jsonl')


def test_planning_time_conversion(sample_events):
    """Test that planning times are correctly converted from ms to seconds"""
    stats = compute_statistics(sample_events)

    # Original: 5000ms, 8000ms, 12000ms, 3000ms
    # Converted: 5s, 8s, 12s, 3s
    assert stats['planning_times'] == [5.0, 8.0, 12.0, 3.0]


def test_step_counts_accuracy(sample_events):
    """Test that step counts are accurately tallied"""
    stats = compute_statistics(sample_events)

    total_steps = sum(stats['step_counts'].values())
    assert total_steps == len(sample_events)

    # Verify each step count
    assert stats['step_counts'][3] == 1
    assert stats['step_counts'][4] == 1
    assert stats['step_counts'][5] == 1
    assert stats['step_counts'][7] == 1


def test_p95_calculation_single_event():
    """Test P95 calculation with single event"""
    events = [{
        "trace_id": "test",
        "goal": "test",
        "planner_type": "llm",
        "task_type": "test",
        "actual_plan_steps": ["step1"],
        "num_steps": 1,
        "planning_time_ms": 5000.0,
        "timestamp": "2025-11-26T10:00:00.000000"
    }]

    stats = compute_statistics(events)

    # With single event, P95 should equal the value
    assert stats['time_p95'] == 5.0


def test_p95_calculation_multi_event():
    """Test P95 calculation with multiple events to avoid returning max"""
    events = [
        {
            "trace_id": f"test-{i}",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": time_ms,
            "timestamp": "2025-11-26T10:00:00.000000"
        }
        for i, time_ms in enumerate([3000, 5000, 8000, 12000])
    ]

    stats = compute_statistics(events)

    # With [3, 5, 8, 12], P95 using int((N-1)*0.95) formula:
    # int((4-1)*0.95) = int(2.85) = 2, so sorted_times[2] = 8.0
    # This should NOT be 12.0 (the max)
    assert stats['time_p95'] == 8.0
    assert stats['time_p95'] != stats['time_max']  # P95 should not equal max for this sample


def test_median_calculation_odd_length():
    """Test median calculation with odd-length list"""
    events = [
        {
            "trace_id": f"test-{i}",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": time_ms,
            "timestamp": "2025-11-26T10:00:00.000000"
        }
        for i, time_ms in enumerate([3000, 5000, 8000])
    ]

    stats = compute_statistics(events)

    # With [3, 5, 8], median should be middle value: 5.0
    assert stats['time_median'] == 5.0


def test_non_numeric_planning_time():
    """Test handling of non-numeric planning_time_ms values"""
    events = [
        {
            "trace_id": "test-1",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": 5000.0,  # Valid numeric
            "timestamp": "2025-11-26T10:00:00.000000"
        },
        {
            "trace_id": "test-2",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": "8000",  # String but parseable
            "timestamp": "2025-11-26T10:00:00.000000"
        },
        {
            "trace_id": "test-3",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": None,  # None - should be skipped
            "timestamp": "2025-11-26T10:00:00.000000"
        },
        {
            "trace_id": "test-4",
            "goal": "test",
            "planner_type": "llm",
            "task_type": "test",
            "actual_plan_steps": ["step1"],
            "num_steps": 1,
            "planning_time_ms": "bad_value",  # Non-parseable - should be skipped
            "timestamp": "2025-11-26T10:00:00.000000"
        }
    ]

    stats = compute_statistics(events)

    # Should only include valid numeric values: 5.0 and 8.0
    assert stats['total_count'] == 4  # All events counted
    assert len(stats['planning_times']) == 2  # Only 2 valid planning times
    assert stats['planning_times'] == [5.0, 8.0]
    assert stats['time_min'] == 5.0
    assert stats['time_max'] == 8.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
