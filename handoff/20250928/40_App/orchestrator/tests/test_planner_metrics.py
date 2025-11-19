#!/usr/bin/env python3
"""
Unit tests for Planner Metrics Recording - Phase 1 (B) Supplemental Implementation
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from llm_planner_adapter import LLMPlannerAdapter


class TestPlannerMetrics:
    """Test suite for Planner Metrics Recording"""

    def test_record_planner_event_creates_file(self):
        """Test that record_planner_event creates JSONL file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = os.path.join(tmpdir, "planner_runs.jsonl")

            with patch.dict(os.environ, {'PLANNER_EVENTS_FILE': events_file}):
                adapter = LLMPlannerAdapter()

                adapter.record_planner_event(
                    trace_id="test-123",
                    goal="Test goal",
                    planner_type="llm",
                    task_type="test_type",
                    actual_plan_steps=["Step 1", "Step 2", "Step 3"],
                    planning_time_ms=1500.0
                )

                assert os.path.exists(events_file)

    def test_record_planner_event_jsonl_format(self):
        """Test that record_planner_event writes valid JSONL"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = os.path.join(tmpdir, "planner_runs.jsonl")

            with patch.dict(os.environ, {'PLANNER_EVENTS_FILE': events_file}):
                adapter = LLMPlannerAdapter()

                adapter.record_planner_event(
                    trace_id="test-123",
                    goal="Test goal",
                    planner_type="llm",
                    task_type="test_type",
                    actual_plan_steps=["Step 1", "Step 2", "Step 3"],
                    planning_time_ms=1500.0
                )

                with open(events_file, 'r') as f:
                    line = f.readline()
                    event = json.loads(line)

                assert event["trace_id"] == "test-123"
                assert event["goal"] == "Test goal"
                assert event["planner_type"] == "llm"
                assert event["task_type"] == "test_type"
                assert event["actual_plan_steps"] == ["Step 1", "Step 2", "Step 3"]
                assert event["num_steps"] == 3
                assert event["planning_time_ms"] == 1500.0
                assert "timestamp" in event

    def test_record_planner_event_appends(self):
        """Test that record_planner_event appends to existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = os.path.join(tmpdir, "planner_runs.jsonl")

            with patch.dict(os.environ, {'PLANNER_EVENTS_FILE': events_file}):
                adapter = LLMPlannerAdapter()

                adapter.record_planner_event(
                    trace_id="test-1",
                    goal="Goal 1",
                    planner_type="llm",
                    task_type="type1",
                    actual_plan_steps=["Step 1"],
                    planning_time_ms=1000.0
                )

                adapter.record_planner_event(
                    trace_id="test-2",
                    goal="Goal 2",
                    planner_type="static",
                    task_type="type2",
                    actual_plan_steps=["Step 1", "Step 2"],
                    planning_time_ms=0.0
                )

                with open(events_file, 'r') as f:
                    lines = f.readlines()

                assert len(lines) == 2

                event1 = json.loads(lines[0])
                event2 = json.loads(lines[1])

                assert event1["trace_id"] == "test-1"
                assert event2["trace_id"] == "test-2"

    def test_record_planner_event_handles_io_error(self):
        """Test that record_planner_event handles IO errors gracefully"""
        with patch('llm_planner_adapter.open', side_effect=IOError("Permission denied")):
            adapter = LLMPlannerAdapter()

            try:
                adapter.record_planner_event(
                    trace_id="test-123",
                    goal="Test goal",
                    planner_type="llm",
                    task_type="test_type",
                    actual_plan_steps=["Step 1"],
                    planning_time_ms=1000.0
                )
            except Exception as e:
                pytest.fail(f"record_planner_event should not raise exception: {e}")

    def test_generate_plan_records_event_on_success(self):
        """Test that generate_plan records event on successful LLM planning"""
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = os.path.join(tmpdir, "planner_runs.jsonl")

            with patch.dict(os.environ, {'PLANNER_EVENTS_FILE': events_file}):
                with patch('llm_planner_adapter.settings') as mock_settings:
                    mock_settings.openai_api_key = "test-key"

                    with patch('llm_planner_adapter.OpenAI') as mock_openai_class:
                        mock_client = MagicMock()
                        mock_openai_class.return_value = mock_client

                        valid_plan = [
                            {"step": "Step 1", "rationale": "Reason 1", "risk": "low"},
                            {"step": "Step 2", "rationale": "Reason 2", "risk": "low"},
                            {"step": "Step 3", "rationale": "Reason 3", "risk": "low"}
                        ]

                        mock_response = MagicMock()
                        mock_response.choices = [MagicMock()]
                        mock_response.choices[0].message.content = json.dumps(valid_plan)
                        mock_client.chat.completions.create.return_value = mock_response

                        adapter = LLMPlannerAdapter()
                        result = adapter.generate_plan("test goal", "RC918/morningai", "trace-123")

                        assert result["planner_type"] == "llm"
                        assert os.path.exists(events_file)

                        with open(events_file, 'r') as f:
                            line = f.readline()
                            event = json.loads(line)

                        assert event["trace_id"] == "trace-123"
                        assert event["planner_type"] == "llm"
                        assert len(event["actual_plan_steps"]) == 3

    def test_record_planner_event_default_path(self):
        """Test that record_planner_event uses default relative path when env var not set"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_repo = os.path.join(tmpdir, 'morningai')
            os.makedirs(os.path.join(mock_repo, '.git'))
            
            original_cwd = os.getcwd()
            try:
                os.chdir(mock_repo)
                
                adapter = LLMPlannerAdapter()
                adapter.record_planner_event(
                    trace_id="test-123",
                    goal="Test goal",
                    planner_type="llm",
                    task_type="test_type",
                    actual_plan_steps=["Step 1"],
                    planning_time_ms=1000.0
                )

                default_path = os.path.join(
                    mock_repo, 'tools', 'agent_eval', 'data', 'planner_runs.jsonl'
                )
                assert os.path.exists(default_path)
            finally:
                os.chdir(original_cwd)
