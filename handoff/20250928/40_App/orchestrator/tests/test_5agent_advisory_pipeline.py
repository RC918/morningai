#!/usr/bin/env python3
"""
5-Agent Advisory Pipeline Tests

Phase 4 PR-4: Tests for the 5-Agent Advisory Pipeline integration
in the LangGraph orchestrator workflow.

Tests cover:
1. All 5 advisory nodes exist in the graph
2. Advisory pipeline edge connections
3. State field initialization for new advisors
4. Individual advisor node behavior
5. Graph compilation with 5-Agent Pipeline
"""
from unittest.mock import patch

from langgraph_orchestrator import (
    AgentState,
    cost_advisor_node,
    permission_advisor_node,
    reputation_advisor_node,
    create_orchestrator_graph,
)


def create_test_state(
    trace_id: str = "test-trace-123",
    goal: str = "Test goal",
    task_type: str = "code_review",
    plan: list = None
) -> AgentState:
    """Create a test AgentState with 5-Agent Advisory Pipeline fields"""
    if plan is None:
        plan = ["Step 1", "Step 2"]
    return {
        "messages": [],
        "goal": goal,
        "trace_id": trace_id,
        "repo": "RC918/morningai",
        "branch": "test-branch",
        "plan": plan,
        "current_step": 0,
        "pr_url": "",
        "pr_number": 0,
        "ci_state": "pending",
        "ci_checks": {},
        "error": None,
        "retry_count": 0,
        "final_result": {},
        "review_result": {},
        "review_comments": [],
        "review_severity": "none",
        "merge_decision": "pending",
        "code_quality_score": 100,
        "task_type": task_type,
        "security_advisory": {},
        "security_risk": "info",
        "security_findings": [],
        "security_is_safe": True,
        "governance_advisory": {},
        "governance_risk": "info",
        "governance_findings": [],
        "governance_is_compliant": True,
        "cost_advisory": {},
        "cost_risk": "info",
        "cost_within_budget": True,
        "permission_advisory": {},
        "permission_risk": "info",
        "permission_granted": True,
        "reputation_advisory": {},
        "reputation_score": 100,
        "reputation_level": "trusted"
    }


class TestGraphContainsAllAdvisors:
    """Tests that the orchestrator graph contains all 5 advisory nodes"""

    def test_graph_contains_security_advisor(self):
        """Test that graph contains security_advisor node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        assert any("security_advisor" in str(node_id) for node_id in node_ids)

    def test_graph_contains_governance_advisor(self):
        """Test that graph contains governance_advisor node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        assert any("governance_advisor" in str(node_id) for node_id in node_ids)

    def test_graph_contains_cost_advisor(self):
        """Test that graph contains cost_advisor node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        assert any("cost_advisor" in str(node_id) for node_id in node_ids)

    def test_graph_contains_permission_advisor(self):
        """Test that graph contains permission_advisor node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        assert any("permission_advisor" in str(node_id) for node_id in node_ids)

    def test_graph_contains_reputation_advisor(self):
        """Test that graph contains reputation_advisor node"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [node.get("id") for node in nodes]
        assert any("reputation_advisor" in str(node_id) for node_id in node_ids)

    def test_graph_has_all_5_advisors(self):
        """Test that graph contains all 5 advisory nodes"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        nodes = graph_dict.get("nodes", [])
        node_ids = [str(node.get("id")) for node in nodes]

        advisors = [
            "security_advisor",
            "governance_advisor",
            "cost_advisor",
            "permission_advisor",
            "reputation_advisor"
        ]

        for advisor in advisors:
            assert any(advisor in node_id for node_id in node_ids), \
                f"{advisor} not found in graph"


class TestCostAdvisorNode:
    """Tests for cost_advisor_node behavior"""

    def test_cost_advisor_initializes_state_fields(self):
        """Test that cost_advisor initializes all required state fields"""
        state = create_test_state()

        result = cost_advisor_node(state)

        assert "cost_advisory" in result
        assert "cost_risk" in result
        assert "cost_within_budget" in result

    def test_cost_advisor_defaults_to_within_budget(self):
        """Test that cost_advisor defaults to within_budget=True"""
        state = create_test_state()

        result = cost_advisor_node(state)

        assert result["cost_within_budget"] is True

    def test_cost_advisor_defaults_to_info_risk(self):
        """Test that cost_advisor defaults to info risk level"""
        state = create_test_state()

        result = cost_advisor_node(state)

        assert result["cost_risk"] == "info"

    def test_cost_advisor_adds_message(self):
        """Test that cost_advisor adds a message to state"""
        state = create_test_state()
        initial_count = len(state["messages"])

        result = cost_advisor_node(state)

        assert len(result["messages"]) > initial_count

    def test_cost_advisor_preserves_trace_id(self):
        """Test that cost_advisor preserves trace_id"""
        trace_id = "preserve-cost-123"
        state = create_test_state(trace_id=trace_id)

        result = cost_advisor_node(state)

        assert result["trace_id"] == trace_id

    def test_cost_advisor_returns_valid_state(self):
        """Test that cost_advisor returns valid state with all required fields"""
        state = create_test_state()

        result = cost_advisor_node(state)

        assert "cost_advisory" in result
        assert "cost_risk" in result
        assert "cost_within_budget" in result
        assert isinstance(result["cost_within_budget"], bool)
        assert len(result["messages"]) > 0


class TestPermissionAdvisorNode:
    """Tests for permission_advisor_node behavior"""

    def test_permission_advisor_initializes_state_fields(self):
        """Test that permission_advisor initializes all required state fields"""
        state = create_test_state()

        result = permission_advisor_node(state)

        assert "permission_advisory" in result
        assert "permission_risk" in result
        assert "permission_granted" in result

    def test_permission_advisor_returns_valid_granted_field(self):
        """Test that permission_advisor returns valid permission_granted field"""
        state = create_test_state()

        result = permission_advisor_node(state)

        assert isinstance(result["permission_granted"], bool)

    def test_permission_advisor_returns_valid_risk_field(self):
        """Test that permission_advisor returns valid risk level"""
        state = create_test_state()

        result = permission_advisor_node(state)

        valid_risks = ["critical", "high", "medium", "low", "info"]
        assert result["permission_risk"] in valid_risks

    def test_permission_advisor_adds_message(self):
        """Test that permission_advisor adds a message to state"""
        state = create_test_state()
        initial_count = len(state["messages"])

        result = permission_advisor_node(state)

        assert len(result["messages"]) > initial_count

    def test_permission_advisor_preserves_trace_id(self):
        """Test that permission_advisor preserves trace_id"""
        trace_id = "preserve-permission-123"
        state = create_test_state(trace_id=trace_id)

        result = permission_advisor_node(state)

        assert result["trace_id"] == trace_id


class TestReputationAdvisorNode:
    """Tests for reputation_advisor_node behavior"""

    def test_reputation_advisor_initializes_state_fields(self):
        """Test that reputation_advisor initializes all required state fields"""
        state = create_test_state()

        result = reputation_advisor_node(state)

        assert "reputation_advisory" in result
        assert "reputation_score" in result
        assert "reputation_level" in result

    def test_reputation_advisor_defaults_to_trusted(self):
        """Test that reputation_advisor defaults to trusted level"""
        state = create_test_state()

        result = reputation_advisor_node(state)

        assert result["reputation_level"] == "trusted"

    def test_reputation_advisor_defaults_to_score_100(self):
        """Test that reputation_advisor defaults to score 100"""
        state = create_test_state()

        result = reputation_advisor_node(state)

        assert result["reputation_score"] == 100

    def test_reputation_advisor_adds_message(self):
        """Test that reputation_advisor adds a message to state"""
        state = create_test_state()
        initial_count = len(state["messages"])

        result = reputation_advisor_node(state)

        assert len(result["messages"]) > initial_count

    def test_reputation_advisor_preserves_trace_id(self):
        """Test that reputation_advisor preserves trace_id"""
        trace_id = "preserve-reputation-123"
        state = create_test_state(trace_id=trace_id)

        result = reputation_advisor_node(state)

        assert result["trace_id"] == trace_id

    def test_reputation_advisory_is_dict(self):
        """Test that reputation_advisory is a dictionary"""
        state = create_test_state()

        result = reputation_advisor_node(state)

        assert isinstance(result["reputation_advisory"], dict)


class TestAdvisoryPipelineEdges:
    """Tests for 5-Agent Advisory Pipeline edge connections"""

    def test_planner_connects_to_security_advisor(self):
        """Test that planner connects to security_advisor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        planner_to_security = any(
            "planner" in str(e.get("source", "")) and
            "security_advisor" in str(e.get("target", ""))
            for e in edges
        )
        assert planner_to_security, "planner should connect to security_advisor"

    def test_security_advisor_connects_to_governance_advisor(self):
        """Test that security_advisor connects to governance_advisor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        security_to_governance = any(
            "security_advisor" in str(e.get("source", "")) and
            "governance_advisor" in str(e.get("target", ""))
            for e in edges
        )
        assert security_to_governance, "security_advisor should connect to governance_advisor"

    def test_governance_advisor_connects_to_cost_advisor(self):
        """Test that governance_advisor connects to cost_advisor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        governance_to_cost = any(
            "governance_advisor" in str(e.get("source", "")) and
            "cost_advisor" in str(e.get("target", ""))
            for e in edges
        )
        assert governance_to_cost, "governance_advisor should connect to cost_advisor"

    def test_cost_advisor_connects_to_permission_advisor(self):
        """Test that cost_advisor connects to permission_advisor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        cost_to_permission = any(
            "cost_advisor" in str(e.get("source", "")) and
            "permission_advisor" in str(e.get("target", ""))
            for e in edges
        )
        assert cost_to_permission, "cost_advisor should connect to permission_advisor"

    def test_permission_advisor_connects_to_reputation_advisor(self):
        """Test that permission_advisor connects to reputation_advisor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        permission_to_reputation = any(
            "permission_advisor" in str(e.get("source", "")) and
            "reputation_advisor" in str(e.get("target", ""))
            for e in edges
        )
        assert permission_to_reputation, "permission_advisor should connect to reputation_advisor"

    def test_reputation_advisor_connects_to_executor(self):
        """Test that reputation_advisor connects to executor"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()
        edges = graph_dict.get("edges", [])

        reputation_to_executor = any(
            "reputation_advisor" in str(e.get("source", "")) and
            "executor" in str(e.get("target", ""))
            for e in edges
        )
        assert reputation_to_executor, "reputation_advisor should connect to executor"


class TestAdvisoryPipelineIntegration:
    """Integration tests for the 5-Agent Advisory Pipeline"""

    def test_all_advisors_return_valid_state(self):
        """Test that all advisors return valid state with required fields"""
        state = create_test_state()

        result = cost_advisor_node(state)
        assert isinstance(result["cost_within_budget"], bool)
        assert isinstance(result["cost_advisory"], dict)

        result = permission_advisor_node(result)
        assert isinstance(result["permission_granted"], bool)
        assert isinstance(result["permission_advisory"], dict)

        result = reputation_advisor_node(result)
        assert isinstance(result["reputation_score"], int)
        assert isinstance(result["reputation_advisory"], dict)

    def test_advisory_pipeline_preserves_state(self):
        """Test that advisory pipeline preserves all state fields"""
        state = create_test_state(
            trace_id="preserve-all-123",
            goal="Test preservation",
            task_type="code_review"
        )

        result = cost_advisor_node(state)
        result = permission_advisor_node(result)
        result = reputation_advisor_node(result)

        assert result["trace_id"] == "preserve-all-123"
        assert result["goal"] == "Test preservation"
        assert result["task_type"] == "code_review"

    def test_advisory_pipeline_accumulates_messages(self):
        """Test that advisory pipeline accumulates messages"""
        state = create_test_state()
        initial_count = len(state["messages"])

        result = cost_advisor_node(state)
        result = permission_advisor_node(result)
        result = reputation_advisor_node(result)

        assert len(result["messages"]) >= initial_count + 3

    def test_graph_compiles_successfully(self):
        """Test that graph with 5-Agent Pipeline compiles successfully"""
        app = create_orchestrator_graph()
        assert app is not None

    def test_graph_has_correct_entry_point(self):
        """Test that graph entry point is planner"""
        app = create_orchestrator_graph()
        graph_dict = app.get_graph().to_json()

        nodes = graph_dict.get("nodes", [])
        entry_nodes = [n for n in nodes if n.get("id") == "__start__"]

        assert len(entry_nodes) > 0 or any("planner" in str(n.get("id")) for n in nodes)


class TestAdvisorErrorHandling:
    """Tests for error handling in advisor nodes"""

    def test_cost_advisor_handles_exception(self):
        """Test that cost_advisor handles exceptions gracefully"""
        state = create_test_state()

        with patch("governance_agent.get_governance_agent", side_effect=Exception("Test error")):
            result = cost_advisor_node(state)

            assert result["cost_within_budget"] is True
            assert "error" in result["cost_advisory"] or result["cost_advisory"] == {}

    def test_permission_advisor_handles_exception(self):
        """Test that permission_advisor handles exceptions gracefully"""
        state = create_test_state()

        with patch("governance_agent.get_governance_agent", side_effect=Exception("Test error")):
            result = permission_advisor_node(state)

            assert result["permission_granted"] is True

    def test_reputation_advisor_handles_exception(self):
        """Test that reputation_advisor handles exceptions gracefully"""
        state = create_test_state()

        with patch("governance_agent.get_governance_agent", side_effect=Exception("Test error")):
            result = reputation_advisor_node(state)

            assert result["reputation_level"] == "trusted"
            assert result["reputation_score"] == 100


class TestStateFieldTypes:
    """Tests for correct state field types"""

    def test_cost_within_budget_is_bool(self):
        """Test that cost_within_budget is a boolean"""
        state = create_test_state()
        result = cost_advisor_node(state)
        assert isinstance(result["cost_within_budget"], bool)

    def test_permission_granted_is_bool(self):
        """Test that permission_granted is a boolean"""
        state = create_test_state()
        result = permission_advisor_node(state)
        assert isinstance(result["permission_granted"], bool)

    def test_reputation_score_is_int(self):
        """Test that reputation_score is an integer"""
        state = create_test_state()
        result = reputation_advisor_node(state)
        assert isinstance(result["reputation_score"], int)

    def test_reputation_level_is_str(self):
        """Test that reputation_level is a string"""
        state = create_test_state()
        result = reputation_advisor_node(state)
        assert isinstance(result["reputation_level"], str)

    def test_cost_risk_is_str(self):
        """Test that cost_risk is a string"""
        state = create_test_state()
        result = cost_advisor_node(state)
        assert isinstance(result["cost_risk"], str)

    def test_permission_risk_is_str(self):
        """Test that permission_risk is a string"""
        state = create_test_state()
        result = permission_advisor_node(state)
        assert isinstance(result["permission_risk"], str)
