"""
Tests for Design Doc Gate - 強制架構審查 (Blueprint Section 4.1 Safety Governor v2)

P2 Feature: Mandatory architecture review before GeneralCoder execution.
This gate ensures that GeneralCoder cannot proceed without a valid ArchitectureSpec
from SeniorCoder.

Issue: EPIC D - Design Doc Gate
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph_orchestrator import (  # noqa: E402
    _validate_design_doc_gate,
    _DESIGN_DOC_REQUIRED_FIELDS,
)


class TestDesignDocGateRequiredFields:
    """Tests for required fields configuration."""

    def test_required_fields_defined(self):
        """Test that required fields are properly defined."""
        assert isinstance(_DESIGN_DOC_REQUIRED_FIELDS, list)
        assert len(_DESIGN_DOC_REQUIRED_FIELDS) > 0

    def test_required_fields_content(self):
        """Test that required fields include expected values."""
        assert "task_analysis" in _DESIGN_DOC_REQUIRED_FIELDS
        assert "architecture" in _DESIGN_DOC_REQUIRED_FIELDS
        assert "implementation_plan" in _DESIGN_DOC_REQUIRED_FIELDS


class TestDesignDocGateValidation:
    """Tests for _validate_design_doc_gate function."""

    def test_gate_pass_with_valid_spec(self):
        """Test gate passes with valid ArchitectureSpec."""
        spec_dict = {
            "task_analysis": {
                "complexity": "simple",
                "reasoning": "Simple fix"
            },
            "architecture": {
                "approach": "Direct modification"
            },
            "implementation_plan": [
                {"step": 1, "description": "Fix the bug"}
            ],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is True
        assert "Valid ArchitectureSpec" in reason
        assert "requires_hitl_approval" not in state or state.get("requires_hitl_approval") is False

    def test_gate_fail_with_none_spec(self):
        """Test gate fails when spec_dict is None."""
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "No ArchitectureSpec available" in reason
        assert state["requires_hitl_approval"] is True
        assert state["hitl_approved"] is False
        assert state["hitl_reason"] == "design_doc_gate_missing_spec"
        assert "DesignDocGate" in state["hitl_details"]["escalation_source"]

    def test_gate_fail_with_missing_task_analysis(self):
        """Test gate fails when task_analysis is missing."""
        spec_dict = {
            "architecture": {"approach": "Direct modification"},
            "implementation_plan": [{"step": 1}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "task_analysis" in reason
        assert state["requires_hitl_approval"] is True
        assert state["hitl_reason"] == "design_doc_gate_invalid_spec"
        assert "task_analysis" in state["hitl_details"]["missing_fields"]

    def test_gate_fail_with_missing_architecture(self):
        """Test gate fails when architecture is missing."""
        spec_dict = {
            "task_analysis": {"complexity": "simple"},
            "implementation_plan": [{"step": 1}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "architecture" in reason
        assert state["requires_hitl_approval"] is True
        assert "architecture" in state["hitl_details"]["missing_fields"]

    def test_gate_fail_with_missing_implementation_plan(self):
        """Test gate fails when implementation_plan is missing."""
        spec_dict = {
            "task_analysis": {"complexity": "simple"},
            "architecture": {"approach": "Direct modification"},
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "implementation_plan" in reason
        assert state["requires_hitl_approval"] is True
        assert "implementation_plan" in state["hitl_details"]["missing_fields"]

    def test_gate_fail_with_empty_task_analysis(self):
        """Test gate fails when task_analysis is empty."""
        spec_dict = {
            "task_analysis": {},
            "architecture": {"approach": "Direct modification"},
            "implementation_plan": [{"step": 1}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "task_analysis" in reason

    def test_gate_fail_with_empty_implementation_plan(self):
        """Test gate fails when implementation_plan is empty list."""
        spec_dict = {
            "task_analysis": {"complexity": "simple"},
            "architecture": {"approach": "Direct modification"},
            "implementation_plan": [],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert "implementation_plan" in reason

    def test_gate_fail_with_multiple_missing_fields(self):
        """Test gate fails and reports all missing fields."""
        spec_dict = {}
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is False
        assert state["requires_hitl_approval"] is True
        missing_fields = state["hitl_details"]["missing_fields"]
        assert "task_analysis" in missing_fields
        assert "architecture" in missing_fields
        assert "implementation_plan" in missing_fields


class TestDesignDocGateHITLDetails:
    """Tests for HITL escalation details in Design Doc Gate."""

    def test_hitl_details_version(self):
        """Test HITL details include version field."""
        state = {}

        _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=3,
        )

        assert state["hitl_details"]["version"] == "1.0"

    def test_hitl_details_task_description(self):
        """Test HITL details include task description."""
        state = {}
        task_desc = "Fix the critical bug in authentication"

        _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description=task_desc,
            file_count=3,
        )

        assert state["hitl_details"]["task_description"] == task_desc

    def test_hitl_details_file_count(self):
        """Test HITL details include file count."""
        state = {}

        _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=5,
        )

        assert state["hitl_details"]["file_count"] == 5

    def test_hitl_details_escalation_source(self):
        """Test HITL details include escalation source."""
        state = {}

        _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert state["hitl_details"]["escalation_source"] == "DesignDocGate"

    def test_hitl_details_recommendation_for_missing_spec(self):
        """Test HITL details include recommendation for missing spec."""
        state = {}

        _validate_design_doc_gate(
            spec_dict=None,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        recommendation = state["hitl_details"]["recommendation"]
        assert "SeniorCoder" in recommendation
        assert "architecture review" in recommendation

    def test_hitl_details_recommendation_for_invalid_spec(self):
        """Test HITL details include recommendation for invalid spec."""
        spec_dict = {"task_analysis": {"complexity": "simple"}}
        state = {}

        _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        recommendation = state["hitl_details"]["recommendation"]
        assert "incomplete" in recommendation


class TestDesignDocGateComplexityExtraction:
    """Tests for complexity extraction from valid specs."""

    def test_extracts_simple_complexity(self):
        """Test complexity extraction for simple tasks."""
        spec_dict = {
            "task_analysis": {"complexity": "simple", "reasoning": "Easy fix"},
            "architecture": {"approach": "Direct"},
            "implementation_plan": [{"step": 1}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is True
        assert "complexity=simple" in reason

    def test_extracts_moderate_complexity(self):
        """Test complexity extraction for moderate tasks."""
        spec_dict = {
            "task_analysis": {"complexity": "moderate", "reasoning": "Medium fix"},
            "architecture": {"approach": "Refactor"},
            "implementation_plan": [{"step": 1}, {"step": 2}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=2,
        )

        assert passed is True
        assert "complexity=moderate" in reason

    def test_extracts_step_count(self):
        """Test step count extraction from implementation plan."""
        spec_dict = {
            "task_analysis": {"complexity": "complex"},
            "architecture": {"approach": "Major refactor"},
            "implementation_plan": [
                {"step": 1, "description": "Step 1"},
                {"step": 2, "description": "Step 2"},
                {"step": 3, "description": "Step 3"},
            ],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=3,
        )

        assert passed is True
        assert "steps=3" in reason

    def test_handles_missing_complexity_gracefully(self):
        """Test graceful handling when complexity field is missing."""
        spec_dict = {
            "task_analysis": {"reasoning": "Some reasoning but no complexity"},
            "architecture": {"approach": "Direct"},
            "implementation_plan": [{"step": 1}],
        }
        state = {}

        passed, reason = _validate_design_doc_gate(
            spec_dict=spec_dict,
            trace_id="test-trace-123",
            state=state,
            task_description="Fix a bug",
            file_count=1,
        )

        assert passed is True
        assert "complexity=unknown" in reason
