"""
Tests for Flow Controller v3 - Candidate Registry (C-8)

Issue #2751: C-8 Candidate Governance
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 2: Extension & Cost Optimization

These tests verify:
- CandidateRegistry correctly manages transition points
- Invalid candidates are rejected
- Deprecated nodes are blocked
- Integration with HybridRouter works correctly
"""
import pytest

from core.flow.candidate_registry import (
    CandidateRegistry,
    get_candidate_registry,
    reset_candidate_registry,
    validate_routing_decision,
    get_candidates_for_router,
    is_valid_router_candidate,
    InvalidCandidateError,
    DeprecatedNodeError,
    DEPRECATED_NODES,
    SAFETY_CRITICAL_NODES,
)
from core.flow.schema import RoutingCandidate


class TestCandidateRegistry:
    """Tests for CandidateRegistry class."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_candidate_registry()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_candidate_registry()

    def test_default_initialization(self):
        """Test that registry initializes with default transition points."""
        registry = CandidateRegistry()

        # Should have 4 default transition points
        transition_points = registry.get_all_transition_points()
        assert len(transition_points) == 4
        assert "router" in transition_points
        assert "hitl_gate" in transition_points
        assert "policy_enforcement" in transition_points
        assert "executor" in transition_points

    def test_router_candidates(self):
        """Test router transition point has correct candidates."""
        registry = CandidateRegistry()
        candidates = registry.get_candidate_names("router")

        assert "publisher" in candidates
        assert "fixer" in candidates
        assert "executor" in candidates
        assert "decision" in candidates
        assert len(candidates) == 4

    def test_hitl_gate_candidates(self):
        """Test hitl_gate transition point has correct candidates."""
        registry = CandidateRegistry()
        candidates = registry.get_candidate_names("hitl_gate")

        assert "fixer" in candidates
        assert "ci_monitor" in candidates
        assert "publisher" in candidates
        assert len(candidates) == 3

    def test_policy_enforcement_candidates(self):
        """Test policy_enforcement transition point has correct candidates."""
        registry = CandidateRegistry()
        candidates = registry.get_candidate_names("policy_enforcement")

        assert "executor" in candidates
        assert "publisher" in candidates
        assert len(candidates) == 2

    def test_executor_candidates(self):
        """Test executor transition point has correct candidates."""
        registry = CandidateRegistry()
        candidates = registry.get_candidate_names("executor")

        assert "executor" in candidates
        assert "ci_monitor" in candidates
        assert "fixer" in candidates
        assert "publisher" in candidates
        assert len(candidates) == 4

    def test_is_valid_candidate_true(self):
        """Test is_valid_candidate returns True for valid candidates."""
        registry = CandidateRegistry()

        assert registry.is_valid_candidate("router", "publisher")
        assert registry.is_valid_candidate("router", "fixer")
        assert registry.is_valid_candidate("hitl_gate", "ci_monitor")

    def test_is_valid_candidate_false(self):
        """Test is_valid_candidate returns False for invalid candidates."""
        registry = CandidateRegistry()

        # planner is not a valid router candidate
        assert not registry.is_valid_candidate("router", "planner")
        # nonexistent node
        assert not registry.is_valid_candidate("router", "nonexistent_node")
        # valid node but wrong transition point
        assert not registry.is_valid_candidate("hitl_gate", "decision")

    def test_validate_valid_candidate(self):
        """Test validate passes for valid candidates."""
        registry = CandidateRegistry()

        # Should not raise
        registry.validate("router", "publisher")
        registry.validate("router", "fixer")
        registry.validate("hitl_gate", "ci_monitor")

    def test_validate_invalid_candidate_raises(self):
        """Test validate raises InvalidCandidateError for invalid candidates."""
        registry = CandidateRegistry()

        with pytest.raises(InvalidCandidateError) as exc_info:
            registry.validate("router", "planner")

        assert exc_info.value.transition_point == "router"
        assert exc_info.value.selected_node == "planner"
        assert "publisher" in exc_info.value.valid_nodes

    def test_validate_deprecated_node_raises(self):
        """Test validate raises DeprecatedNodeError for deprecated nodes."""
        registry = CandidateRegistry()
        registry.add_deprecated_node("legacy_node")

        with pytest.raises(DeprecatedNodeError) as exc_info:
            registry.validate("router", "legacy_node")

        assert exc_info.value.selected_node == "legacy_node"
        assert "deprecated" in exc_info.value.reason

    def test_register_custom_candidates(self):
        """Test registering custom candidates for a transition point."""
        registry = CandidateRegistry()

        custom_candidates = [
            RoutingCandidate(node_name="custom_node", description="Custom node"),
        ]
        registry.register("custom_point", custom_candidates)

        assert registry.is_valid_candidate("custom_point", "custom_node")
        assert not registry.is_valid_candidate("custom_point", "other_node")

    def test_register_empty_candidates_raises(self):
        """Test registering empty candidates raises ValueError."""
        registry = CandidateRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.register("empty_point", [])

        assert "empty" in str(exc_info.value).lower()

    def test_register_deprecated_node_raises(self):
        """Test registering deprecated node raises ValueError."""
        registry = CandidateRegistry()
        registry.add_deprecated_node("deprecated_node")

        with pytest.raises(ValueError) as exc_info:
            registry.register(
                "bad_point",
                [RoutingCandidate(node_name="deprecated_node", description="Bad")]
            )

        assert "deprecated" in str(exc_info.value).lower()

    def test_get_registry_summary(self):
        """Test get_registry_summary returns correct structure."""
        registry = CandidateRegistry()
        summary = registry.get_registry_summary()

        assert isinstance(summary, dict)
        assert "router" in summary
        assert isinstance(summary["router"], list)
        assert "publisher" in summary["router"]

    def test_unknown_transition_point_returns_empty(self):
        """Test unknown transition point returns empty list."""
        registry = CandidateRegistry()

        candidates = registry.get_candidates("unknown_point")
        assert candidates == []

        names = registry.get_candidate_names("unknown_point")
        assert names == []


class TestSingletonFunctions:
    """Tests for singleton convenience functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_candidate_registry()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_candidate_registry()

    def test_get_candidate_registry_singleton(self):
        """Test get_candidate_registry returns same instance."""
        registry1 = get_candidate_registry()
        registry2 = get_candidate_registry()

        assert registry1 is registry2

    def test_reset_candidate_registry(self):
        """Test reset_candidate_registry creates new instance."""
        registry1 = get_candidate_registry()
        reset_candidate_registry()
        registry2 = get_candidate_registry()

        assert registry1 is not registry2

    def test_validate_routing_decision_valid(self):
        """Test validate_routing_decision passes for valid decisions."""
        # Should not raise
        validate_routing_decision("router", "publisher")
        validate_routing_decision("router", "fixer")

    def test_validate_routing_decision_invalid(self):
        """Test validate_routing_decision raises for invalid decisions."""
        with pytest.raises(InvalidCandidateError):
            validate_routing_decision("router", "planner")

    def test_get_candidates_for_router(self):
        """Test get_candidates_for_router returns router candidates."""
        candidates = get_candidates_for_router()

        assert len(candidates) == 4
        node_names = [c.node_name for c in candidates]
        assert "publisher" in node_names
        assert "fixer" in node_names

    def test_is_valid_router_candidate(self):
        """Test is_valid_router_candidate convenience function."""
        assert is_valid_router_candidate("publisher")
        assert is_valid_router_candidate("fixer")
        assert not is_valid_router_candidate("planner")
        assert not is_valid_router_candidate("nonexistent")


class TestConstants:
    """Tests for module constants."""

    def test_deprecated_nodes_is_frozenset(self):
        """Test DEPRECATED_NODES is a frozenset."""
        assert isinstance(DEPRECATED_NODES, frozenset)

    def test_safety_critical_nodes_is_frozenset(self):
        """Test SAFETY_CRITICAL_NODES is a frozenset."""
        assert isinstance(SAFETY_CRITICAL_NODES, frozenset)

    def test_safety_critical_nodes_contains_expected(self):
        """Test SAFETY_CRITICAL_NODES contains expected nodes."""
        assert "policy_enforcement" in SAFETY_CRITICAL_NODES
        assert "hitl_gate" in SAFETY_CRITICAL_NODES
        assert "security_advisor" in SAFETY_CRITICAL_NODES
        assert "governance_advisor" in SAFETY_CRITICAL_NODES


class TestHybridRouterIntegration:
    """Tests for CandidateRegistry integration with HybridRouter."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_candidate_registry()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_candidate_registry()

    def test_hybrid_router_validates_llm_response(self):
        """Test HybridRouter validates LLM response against registry."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        # Create router with mock LLM that returns invalid node
        def mock_llm_invalid(prompt: str) -> str:
            return '{"next_node": "planner", "reasoning": "test"}'

        router = HybridRoutingPolicy(llm_generate_fn=mock_llm_invalid)
        decision = router.route(
            verdict="request_changes",
            severity="high",
            summary="Test issue"
        )

        # Should fall back to deterministic since planner is invalid
        assert decision.next_node in ("fixer", "executor")
        assert "fallback" in decision.reasoning.lower() or "Deterministic" in decision.reasoning

    def test_hybrid_router_accepts_valid_llm_response(self):
        """Test HybridRouter accepts valid LLM response."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        # Create router with mock LLM that returns valid node
        def mock_llm_valid(prompt: str) -> str:
            return '{"next_node": "fixer", "reasoning": "test fix"}'

        router = HybridRoutingPolicy(llm_generate_fn=mock_llm_valid)
        decision = router.route(
            verdict="request_changes",
            severity="high",
            summary="Test issue"
        )

        assert decision.next_node == "fixer"
        assert "LLM decision" in decision.reasoning

    def test_hybrid_router_fast_path_uses_valid_nodes(self):
        """Test HybridRouter fast path returns valid nodes."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        router = HybridRoutingPolicy(llm_generate_fn=None)

        # approve -> publisher (valid)
        decision = router.route(verdict="approve", severity="low", summary="")
        assert is_valid_router_candidate(decision.next_node)
        assert decision.next_node == "publisher"

        # blocked -> decision (valid)
        decision = router.route(verdict="blocked", severity="high", summary="")
        assert is_valid_router_candidate(decision.next_node)
        assert decision.next_node == "decision"

        # request_changes low -> fixer (valid)
        decision = router.route(verdict="request_changes", severity="low", summary="")
        assert is_valid_router_candidate(decision.next_node)
        assert decision.next_node == "fixer"


class TestCIValidation:
    """Tests for CI validation of candidate registry completeness."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_candidate_registry()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_candidate_registry()

    def test_all_transition_points_have_candidates(self):
        """Test all registered transition points have non-empty candidates."""
        registry = get_candidate_registry()

        for tp in registry.get_all_transition_points():
            candidates = registry.get_candidates(tp)
            assert len(candidates) > 0, f"Transition point '{tp}' has no candidates"

    def test_all_candidates_have_descriptions(self):
        """Test all candidates have non-empty descriptions."""
        registry = get_candidate_registry()

        for tp in registry.get_all_transition_points():
            for candidate in registry.get_candidates(tp):
                assert candidate.description, (
                    f"Candidate '{candidate.node_name}' at '{tp}' has no description"
                )

    def test_no_deprecated_nodes_in_candidates(self):
        """Test no deprecated nodes are registered as candidates."""
        registry = get_candidate_registry()

        for tp in registry.get_all_transition_points():
            for candidate in registry.get_candidates(tp):
                assert candidate.node_name not in DEPRECATED_NODES, (
                    f"Deprecated node '{candidate.node_name}' found in '{tp}'"
                )

    def test_router_candidates_match_graph_structure(self):
        """Test router candidates match the LangGraph structure.

        Based on langgraph_orchestrator.py lines 7268-7336:
        - router can route to: hitl_gate (which then routes to fixer/ci_monitor/publisher)
        - But router's decision is about what action to take, not direct graph edges
        - Valid router decisions: publisher, fixer, executor, decision
        """
        registry = get_candidate_registry()
        router_candidates = set(registry.get_candidate_names("router"))

        # These are the valid decisions Router can make
        expected = {"publisher", "fixer", "executor", "decision"}
        assert router_candidates == expected, (
            f"Router candidates mismatch. Expected: {expected}, Got: {router_candidates}"
        )

    def test_hitl_gate_candidates_match_graph_structure(self):
        """Test hitl_gate candidates match the LangGraph structure.

        Based on langgraph_orchestrator.py lines 7316-7324:
        hitl_gate -> (fixer | ci_monitor | publisher)
        """
        registry = get_candidate_registry()
        hitl_candidates = set(registry.get_candidate_names("hitl_gate"))

        expected = {"fixer", "ci_monitor", "publisher"}
        assert hitl_candidates == expected, (
            f"HITL gate candidates mismatch. Expected: {expected}, Got: {hitl_candidates}"
        )

    def test_policy_enforcement_candidates_match_graph_structure(self):
        """Test policy_enforcement candidates match the LangGraph structure.

        Based on langgraph_orchestrator.py lines 7268-7275:
        policy_enforcement -> (executor | publisher)
        """
        registry = get_candidate_registry()
        policy_candidates = set(registry.get_candidate_names("policy_enforcement"))

        expected = {"executor", "publisher"}
        assert policy_candidates == expected, (
            f"Policy enforcement candidates mismatch. Expected: {expected}, Got: {policy_candidates}"
        )

    def test_executor_candidates_match_graph_structure(self):
        """Test executor candidates match the LangGraph structure.

        Based on langgraph_orchestrator.py lines 7279-7288:
        executor -> (executor | ci_monitor | fixer | publisher)
        """
        registry = get_candidate_registry()
        executor_candidates = set(registry.get_candidate_names("executor"))

        expected = {"executor", "ci_monitor", "fixer", "publisher"}
        assert executor_candidates == expected, (
            f"Executor candidates mismatch. Expected: {expected}, Got: {executor_candidates}"
        )
