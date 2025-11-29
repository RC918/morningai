#!/usr/bin/env python3
"""
Tests for Governance Dashboard Module - Phase 4 PR-5

Tests the governance dashboard builder and formatting functions.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from governance_dashboard import (  # noqa: E402
    build_governance_dashboard,
    format_dashboard_text,
    get_governance_status,
    GovernanceDashboardSummary,
    DashboardRiskLevel,
    _get_risk_priority,
    _calculate_overall_risk,
    _count_findings,
    _extract_recommendations
)


class TestDashboardRiskLevel:
    """Tests for DashboardRiskLevel enum"""

    def test_risk_levels_exist(self):
        assert DashboardRiskLevel.CRITICAL.value == "critical"
        assert DashboardRiskLevel.HIGH.value == "high"
        assert DashboardRiskLevel.MEDIUM.value == "medium"
        assert DashboardRiskLevel.LOW.value == "low"
        assert DashboardRiskLevel.INFO.value == "info"


class TestRiskPriority:
    """Tests for _get_risk_priority function"""

    def test_critical_highest_priority(self):
        assert _get_risk_priority("critical") == 5

    def test_high_priority(self):
        assert _get_risk_priority("high") == 4

    def test_medium_priority(self):
        assert _get_risk_priority("medium") == 3

    def test_low_priority(self):
        assert _get_risk_priority("low") == 2

    def test_info_priority(self):
        assert _get_risk_priority("info") == 1

    def test_trusted_priority(self):
        assert _get_risk_priority("trusted") == 0

    def test_unknown_priority(self):
        assert _get_risk_priority("unknown") == 0

    def test_case_insensitive(self):
        assert _get_risk_priority("CRITICAL") == 5
        assert _get_risk_priority("High") == 4


class TestCalculateOverallRisk:
    """Tests for _calculate_overall_risk function"""

    def test_all_info_returns_info(self):
        result = _calculate_overall_risk("info", "info", "info", "info")
        assert result == DashboardRiskLevel.INFO

    def test_one_critical_returns_critical(self):
        result = _calculate_overall_risk("critical", "info", "info", "info")
        assert result == DashboardRiskLevel.CRITICAL

    def test_one_high_returns_high(self):
        result = _calculate_overall_risk("info", "high", "info", "info")
        assert result == DashboardRiskLevel.HIGH

    def test_one_medium_returns_medium(self):
        result = _calculate_overall_risk("info", "info", "medium", "info")
        assert result == DashboardRiskLevel.MEDIUM

    def test_one_low_returns_low(self):
        result = _calculate_overall_risk("info", "info", "info", "low")
        assert result == DashboardRiskLevel.LOW

    def test_highest_risk_wins(self):
        result = _calculate_overall_risk("low", "medium", "high", "info")
        assert result == DashboardRiskLevel.HIGH


class TestCountFindings:
    """Tests for _count_findings function"""

    def test_empty_advisory(self):
        total, high = _count_findings({})
        assert total == 0
        assert high == 0

    def test_no_findings(self):
        total, high = _count_findings({"findings": []})
        assert total == 0
        assert high == 0

    def test_count_all_findings(self):
        advisory = {
            "findings": [
                {"risk_level": "low"},
                {"risk_level": "medium"},
                {"risk_level": "high"}
            ]
        }
        total, high = _count_findings(advisory)
        assert total == 3
        assert high == 1

    def test_count_high_risk_findings(self):
        advisory = {
            "findings": [
                {"risk_level": "critical"},
                {"risk_level": "high"},
                {"risk_level": "low"}
            ]
        }
        total, high = _count_findings(advisory)
        assert total == 3
        assert high == 2


class TestExtractRecommendations:
    """Tests for _extract_recommendations function"""

    def test_empty_state(self):
        recs = _extract_recommendations({})
        assert recs == []

    def test_extract_from_single_advisory(self):
        state = {
            "security_advisory": {
                "recommendations": ["Fix security issue"]
            }
        }
        recs = _extract_recommendations(state)
        assert "Fix security issue" in recs

    def test_extract_from_multiple_advisories(self):
        state = {
            "security_advisory": {"recommendations": ["Fix security"]},
            "cost_advisory": {"recommendations": ["Reduce cost"]}
        }
        recs = _extract_recommendations(state)
        assert len(recs) == 2
        assert "Fix security" in recs
        assert "Reduce cost" in recs

    def test_deduplicate_recommendations(self):
        state = {
            "security_advisory": {"recommendations": ["Same recommendation"]},
            "governance_advisory": {"recommendations": ["Same recommendation"]}
        }
        recs = _extract_recommendations(state)
        assert len(recs) == 1


class TestBuildGovernanceDashboard:
    """Tests for build_governance_dashboard function"""

    @pytest.fixture
    def minimal_state(self):
        return {"trace_id": "test-trace-001"}

    @pytest.fixture
    def full_state(self):
        return {
            "trace_id": "test-trace-002",
            "goal": "Test goal",
            "plan": ["Step 1", "Step 2"],
            "task_type": "test_task",
            "agent_id": "test-agent",
            "environment": "sandbox",
            "security_risk": "low",
            "security_compliant": True,
            "security_advisory": {"findings": [], "recommendations": []},
            "governance_risk": "info",
            "governance_compliant": True,
            "governance_advisory": {"findings": [], "recommendations": []},
            "cost_risk": "info",
            "cost_within_budget": True,
            "cost_advisory": {"findings": [], "recommendations": []},
            "permission_risk": "info",
            "permission_granted": True,
            "permission_advisory": {"findings": [], "recommendations": []},
            "reputation_level": "trusted",
            "reputation_score": 100,
            "reputation_advisory": {"recommendations": []}
        }

    def test_returns_summary_object(self, minimal_state):
        result = build_governance_dashboard(minimal_state)
        assert isinstance(result, GovernanceDashboardSummary)

    def test_extracts_trace_id(self, minimal_state):
        result = build_governance_dashboard(minimal_state)
        assert result.trace_id == "test-trace-001"

    def test_defaults_to_info_risk(self, minimal_state):
        result = build_governance_dashboard(minimal_state)
        assert result.security_risk == "info"
        assert result.governance_risk == "info"
        assert result.cost_risk == "info"
        assert result.permission_risk == "info"

    def test_defaults_to_compliant(self, minimal_state):
        result = build_governance_dashboard(minimal_state)
        assert result.security_compliant is True
        assert result.governance_compliant is True
        assert result.cost_within_budget is True
        assert result.permission_granted is True

    def test_defaults_to_trusted_reputation(self, minimal_state):
        result = build_governance_dashboard(minimal_state)
        assert result.reputation_level == "trusted"
        assert result.reputation_score == 100

    def test_calculates_overall_risk(self, full_state):
        result = build_governance_dashboard(full_state)
        assert result.overall_risk == DashboardRiskLevel.LOW

    def test_high_risk_requires_approval(self, full_state):
        full_state["security_risk"] = "high"
        result = build_governance_dashboard(full_state)
        assert result.requires_human_approval is True

    def test_non_compliant_requires_approval(self, full_state):
        full_state["security_compliant"] = False
        result = build_governance_dashboard(full_state)
        assert result.requires_human_approval is True

    def test_counts_findings_by_category(self, full_state):
        full_state["security_advisory"] = {
            "findings": [{"risk_level": "low"}],
            "recommendations": []
        }
        result = build_governance_dashboard(full_state)
        assert result.findings_by_category["security"] == 1
        assert result.total_findings == 1

    def test_extracts_metadata(self, full_state):
        result = build_governance_dashboard(full_state)
        assert result.metadata["task_type"] == "test_task"
        assert result.metadata["plan_steps"] == 2
        assert result.metadata["agent_id"] == "test-agent"
        assert result.metadata["environment"] == "sandbox"


class TestGovernanceDashboardSummaryToDict:
    """Tests for GovernanceDashboardSummary.to_dict method"""

    def test_to_dict_returns_dict(self):
        summary = GovernanceDashboardSummary(
            overall_risk=DashboardRiskLevel.INFO,
            requires_human_approval=False,
            timestamp="2025-01-01T00:00:00",
            trace_id="test-001",
            security_risk="info",
            governance_risk="info",
            cost_risk="info",
            permission_risk="info",
            reputation_level="trusted",
            security_compliant=True,
            governance_compliant=True,
            cost_within_budget=True,
            permission_granted=True,
            reputation_score=100
        )
        result = summary.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_risk_levels(self):
        summary = GovernanceDashboardSummary(
            overall_risk=DashboardRiskLevel.MEDIUM,
            requires_human_approval=False,
            timestamp="2025-01-01T00:00:00",
            trace_id="test-001",
            security_risk="low",
            governance_risk="medium",
            cost_risk="info",
            permission_risk="info",
            reputation_level="trusted",
            security_compliant=True,
            governance_compliant=True,
            cost_within_budget=True,
            permission_granted=True,
            reputation_score=100
        )
        result = summary.to_dict()
        assert result["risk_levels"]["security"] == "low"
        assert result["risk_levels"]["governance"] == "medium"

    def test_to_dict_contains_compliance(self):
        summary = GovernanceDashboardSummary(
            overall_risk=DashboardRiskLevel.INFO,
            requires_human_approval=False,
            timestamp="2025-01-01T00:00:00",
            trace_id="test-001",
            security_risk="info",
            governance_risk="info",
            cost_risk="info",
            permission_risk="info",
            reputation_level="trusted",
            security_compliant=True,
            governance_compliant=False,
            cost_within_budget=True,
            permission_granted=True,
            reputation_score=95
        )
        result = summary.to_dict()
        assert result["compliance"]["security_compliant"] is True
        assert result["compliance"]["governance_compliant"] is False
        assert result["compliance"]["reputation_score"] == 95


class TestFormatDashboardText:
    """Tests for format_dashboard_text function"""

    @pytest.fixture
    def sample_summary(self):
        return GovernanceDashboardSummary(
            overall_risk=DashboardRiskLevel.INFO,
            requires_human_approval=False,
            timestamp="2025-01-01T00:00:00",
            trace_id="test-001",
            security_risk="info",
            governance_risk="info",
            cost_risk="info",
            permission_risk="info",
            reputation_level="trusted",
            security_compliant=True,
            governance_compliant=True,
            cost_within_budget=True,
            permission_granted=True,
            reputation_score=100,
            findings_by_category={"security": 0, "governance": 0},
            high_risk_findings=0,
            total_findings=0,
            recommendations=[],
            metadata={"task_type": "test", "plan_steps": 2}
        )

    def test_returns_string(self, sample_summary):
        result = format_dashboard_text(sample_summary)
        assert isinstance(result, str)

    def test_contains_header(self, sample_summary):
        result = format_dashboard_text(sample_summary)
        assert "Governance Dashboard" in result

    def test_contains_trace_id(self, sample_summary):
        result = format_dashboard_text(sample_summary)
        assert "test-001" in result

    def test_contains_risk_levels(self, sample_summary):
        result = format_dashboard_text(sample_summary)
        assert "Security:" in result
        assert "Governance:" in result
        assert "Cost:" in result
        assert "Permission:" in result

    def test_contains_findings_summary(self, sample_summary):
        result = format_dashboard_text(sample_summary)
        assert "Findings Summary" in result

    def test_shows_recommendations_when_present(self, sample_summary):
        sample_summary.recommendations = ["Fix issue 1", "Fix issue 2"]
        result = format_dashboard_text(sample_summary)
        assert "Recommendations" in result
        assert "Fix issue 1" in result


class TestGetGovernanceStatus:
    """Tests for get_governance_status function"""

    def test_returns_dict(self):
        state = {"trace_id": "test-001"}
        result = get_governance_status(state)
        assert isinstance(result, dict)

    def test_contains_overall_risk(self):
        state = {"trace_id": "test-001"}
        result = get_governance_status(state)
        assert "overall_risk" in result

    def test_contains_compliance(self):
        state = {"trace_id": "test-001"}
        result = get_governance_status(state)
        assert "compliance" in result

    def test_contains_findings(self):
        state = {"trace_id": "test-001"}
        result = get_governance_status(state)
        assert "findings" in result


class TestIntegration:
    """Integration tests for governance dashboard"""

    def test_full_pipeline_with_all_advisories(self):
        state = {
            "trace_id": "integration-test-001",
            "goal": "Complete integration test",
            "plan": ["Step 1", "Step 2", "Step 3"],
            "task_type": "integration_test",
            "agent_id": "test-orchestrator",
            "environment": "sandbox",
            "security_risk": "low",
            "security_compliant": True,
            "security_advisory": {
                "is_compliant": True,
                "overall_risk": "low",
                "findings": [{"risk_level": "low", "title": "Minor issue"}],
                "recommendations": ["Review code"]
            },
            "governance_risk": "info",
            "governance_compliant": True,
            "governance_advisory": {
                "is_compliant": True,
                "overall_risk": "info",
                "findings": [],
                "recommendations": []
            },
            "cost_risk": "medium",
            "cost_within_budget": True,
            "cost_advisory": {
                "is_compliant": True,
                "overall_risk": "medium",
                "findings": [{"risk_level": "medium", "title": "Budget warning"}],
                "recommendations": ["Monitor usage"]
            },
            "permission_risk": "info",
            "permission_granted": True,
            "permission_advisory": {
                "is_compliant": True,
                "overall_risk": "info",
                "findings": [],
                "recommendations": []
            },
            "reputation_level": "trusted",
            "reputation_score": 95,
            "reputation_advisory": {
                "agent_id": "test-orchestrator",
                "score": 95,
                "level": "trusted",
                "recommendations": []
            }
        }

        summary = build_governance_dashboard(state)

        assert summary.trace_id == "integration-test-001"
        assert summary.overall_risk == DashboardRiskLevel.MEDIUM
        assert summary.requires_human_approval is False
        assert summary.total_findings == 2
        assert summary.high_risk_findings == 0
        assert "Review code" in summary.recommendations
        assert "Monitor usage" in summary.recommendations

        text = format_dashboard_text(summary)
        assert "integration-test-001" in text
        assert "MEDIUM" in text

        status = get_governance_status(state)
        assert status["overall_risk"] == "medium"
        assert status["compliance"]["cost_within_budget"] is True
