"""
Flow Controller v3 - Candidate Registry (C-8)

Issue #2751: C-8 Candidate Governance
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 2: Extension & Cost Optimization

This module implements the CandidateRegistry which:
- Manages valid candidate sets for each transition point
- Prevents LLM hallucination from selecting invalid paths
- Enforces safety constraints (no skipping security nodes)
- Provides static analysis for CI validation

Transition Points:
- "router": After reviewer, Router decides next step (fixer/executor/publisher/decision)
- "hitl_gate": After HITL gate, decides next step (fixer/ci_monitor/publisher)
- "policy_enforcement": After policy check, decides next step (executor/publisher)
- "executor": After execution, decides next step (executor/ci_monitor/fixer/publisher)

Safety Constraints:
- Router cannot skip policy_enforcement (already enforced by graph structure)
- Router cannot select deprecated nodes
- All LLM-selected nodes must be in the whitelist

Event Codes (greppable):
- [CANDIDATE_REGISTRY] - Registry operations
- [CANDIDATE_INVALID] - Invalid candidate selection detected
- [CANDIDATE_DEPRECATED] - Deprecated node selection detected

Usage:
    from core.flow.candidate_registry import (
        get_candidate_registry,
        validate_routing_decision,
        InvalidCandidateError,
    )

    registry = get_candidate_registry()
    candidates = registry.get_candidates("router")

    # Validate a routing decision
    validate_routing_decision("router", "fixer")  # OK
    validate_routing_decision("router", "planner")  # Raises InvalidCandidateError
"""
import logging
from typing import Dict, FrozenSet, List, Optional, Set

from .schema import RoutingCandidate

logger = logging.getLogger(__name__)


# Deprecated nodes that should never be selected
DEPRECATED_NODES: FrozenSet[str] = frozenset({
    # Add deprecated nodes here as they are phased out
    # Example: "legacy_reviewer", "old_fixer"
})


# Safety-critical nodes that cannot be skipped
# These are enforced by graph structure, but we track them for documentation
SAFETY_CRITICAL_NODES: FrozenSet[str] = frozenset({
    "policy_enforcement",
    "hitl_gate",
    "security_advisor",
    "governance_advisor",
})


class InvalidCandidateError(Exception):
    """Raised when an invalid candidate is selected."""

    def __init__(
        self,
        transition_point: str,
        selected_node: str,
        valid_nodes: List[str],
        reason: str = "not in candidate list"
    ):
        self.transition_point = transition_point
        self.selected_node = selected_node
        self.valid_nodes = valid_nodes
        self.reason = reason
        super().__init__(
            f"[CANDIDATE_INVALID] Invalid candidate '{selected_node}' at "
            f"transition point '{transition_point}': {reason}. "
            f"Valid candidates: {valid_nodes}"
        )


class DeprecatedNodeError(InvalidCandidateError):
    """Raised when a deprecated node is selected."""

    def __init__(self, transition_point: str, selected_node: str, valid_nodes: List[str]):
        super().__init__(
            transition_point=transition_point,
            selected_node=selected_node,
            valid_nodes=valid_nodes,
            reason="node is deprecated"
        )


class CandidateRegistry:
    """Manages valid candidate sets for each transition point.

    This registry defines which nodes can be selected at each decision point
    in the orchestrator graph. It prevents LLM hallucination from selecting
    invalid or deprecated nodes.

    Attributes:
        _registry: Mapping of transition point to valid candidates
        _deprecated_nodes: Set of deprecated node names
    """

    def __init__(self):
        """Initialize the CandidateRegistry with default transition rules."""
        self._registry: Dict[str, List[RoutingCandidate]] = {}
        self._deprecated_nodes: Set[str] = set(DEPRECATED_NODES)
        self._initialize_default_candidates()

    def _initialize_default_candidates(self) -> None:
        """Initialize default candidate sets for all transition points.

        These are derived from the LangGraph orchestrator graph structure:
        - langgraph_orchestrator.py lines 7268-7336

        Transition Points:
        1. router: After reviewer node (when ENABLE_DYNAMIC_ROUTING=true)
           - reviewer -> router -> hitl_gate
           - Router can suggest: fixer, executor, publisher, decision

        2. hitl_gate: After HITL gate approval check
           - hitl_gate -> (fixer | ci_monitor | publisher)

        3. policy_enforcement: After policy check
           - policy_enforcement -> (executor | publisher)

        4. executor: After code execution
           - executor -> (executor | ci_monitor | fixer | publisher)
        """
        # Router transition point (C-6: Hybrid Router)
        # After reviewer, Router decides the next step
        self.register(
            "router",
            [
                RoutingCandidate(
                    node_name="publisher",
                    description="Deploy changes to GitHub (for approved reviews)"
                ),
                RoutingCandidate(
                    node_name="fixer",
                    description="Auto-fix minor issues (for low/medium severity)"
                ),
                RoutingCandidate(
                    node_name="executor",
                    description="Re-generate code (for major issues requiring restructuring)"
                ),
                RoutingCandidate(
                    node_name="decision",
                    description="Escalate to human review (for blocked/unknown verdicts)"
                ),
            ]
        )

        # HITL Gate transition point (C-5: HITL Gate)
        # After HITL approval check, decides next step
        self.register(
            "hitl_gate",
            [
                RoutingCandidate(
                    node_name="fixer",
                    description="Fix issues identified in review"
                ),
                RoutingCandidate(
                    node_name="ci_monitor",
                    description="Monitor CI status after changes"
                ),
                RoutingCandidate(
                    node_name="publisher",
                    description="Publish approved changes"
                ),
            ]
        )

        # Policy Enforcement transition point
        # After policy check, decides whether to execute or finalize
        self.register(
            "policy_enforcement",
            [
                RoutingCandidate(
                    node_name="executor",
                    description="Execute planned tasks"
                ),
                RoutingCandidate(
                    node_name="publisher",
                    description="Skip execution and finalize (policy blocked)"
                ),
            ]
        )

        # Executor transition point
        # After code execution, decides next step
        self.register(
            "executor",
            [
                RoutingCandidate(
                    node_name="executor",
                    description="Continue execution (more steps remaining)"
                ),
                RoutingCandidate(
                    node_name="ci_monitor",
                    description="Monitor CI after code changes"
                ),
                RoutingCandidate(
                    node_name="fixer",
                    description="Fix issues found during execution"
                ),
                RoutingCandidate(
                    node_name="publisher",
                    description="Finalize execution"
                ),
            ]
        )

        logger.info(
            f"[CANDIDATE_REGISTRY] Initialized with {len(self._registry)} "
            f"transition points: {list(self._registry.keys())}"
        )

    def register(
        self,
        transition_point: str,
        candidates: List[RoutingCandidate]
    ) -> None:
        """Register valid candidates for a transition point.

        Args:
            transition_point: Name of the transition point (e.g., "router")
            candidates: List of valid candidate nodes

        Raises:
            ValueError: If candidates list is empty or contains deprecated nodes
        """
        if not candidates:
            raise ValueError(
                f"Cannot register empty candidate list for '{transition_point}'"
            )

        # Check for deprecated nodes
        for candidate in candidates:
            if candidate.node_name in self._deprecated_nodes:
                raise ValueError(
                    f"Cannot register deprecated node '{candidate.node_name}' "
                    f"for transition point '{transition_point}'"
                )

        self._registry[transition_point] = candidates
        logger.debug(
            f"[CANDIDATE_REGISTRY] Registered {len(candidates)} candidates "
            f"for '{transition_point}': {[c.node_name for c in candidates]}"
        )

    def get_candidates(self, transition_point: str) -> List[RoutingCandidate]:
        """Get valid candidates for a transition point.

        Args:
            transition_point: Name of the transition point

        Returns:
            List of valid candidate nodes (empty if not registered)
        """
        return self._registry.get(transition_point, [])

    def get_candidate_names(self, transition_point: str) -> List[str]:
        """Get valid candidate node names for a transition point.

        Args:
            transition_point: Name of the transition point

        Returns:
            List of valid candidate node names
        """
        return [c.node_name for c in self.get_candidates(transition_point)]

    def is_valid_candidate(
        self,
        transition_point: str,
        node_name: str
    ) -> bool:
        """Check if a node is a valid candidate at a transition point.

        Args:
            transition_point: Name of the transition point
            node_name: Name of the node to check

        Returns:
            True if the node is a valid candidate
        """
        if node_name in self._deprecated_nodes:
            return False
        return node_name in self.get_candidate_names(transition_point)

    def validate(
        self,
        transition_point: str,
        node_name: str
    ) -> None:
        """Validate that a node is a valid candidate.

        Args:
            transition_point: Name of the transition point
            node_name: Name of the selected node

        Raises:
            DeprecatedNodeError: If the node is deprecated
            InvalidCandidateError: If the node is not a valid candidate
        """
        valid_nodes = self.get_candidate_names(transition_point)

        if node_name in self._deprecated_nodes:
            logger.warning(
                f"[CANDIDATE_DEPRECATED] Deprecated node '{node_name}' "
                f"selected at '{transition_point}'"
            )
            raise DeprecatedNodeError(
                transition_point=transition_point,
                selected_node=node_name,
                valid_nodes=valid_nodes
            )

        if not self.is_valid_candidate(transition_point, node_name):
            logger.warning(
                f"[CANDIDATE_INVALID] Invalid node '{node_name}' "
                f"selected at '{transition_point}'. Valid: {valid_nodes}"
            )
            raise InvalidCandidateError(
                transition_point=transition_point,
                selected_node=node_name,
                valid_nodes=valid_nodes
            )

    def get_all_transition_points(self) -> List[str]:
        """Get all registered transition points.

        Returns:
            List of transition point names
        """
        return list(self._registry.keys())

    def add_deprecated_node(self, node_name: str) -> None:
        """Mark a node as deprecated.

        Args:
            node_name: Name of the node to deprecate
        """
        self._deprecated_nodes.add(node_name)
        logger.info(f"[CANDIDATE_REGISTRY] Marked node '{node_name}' as deprecated")

    def get_registry_summary(self) -> Dict[str, List[str]]:
        """Get a summary of all registered candidates.

        Returns:
            Dict mapping transition points to candidate node names
        """
        return {
            tp: self.get_candidate_names(tp)
            for tp in self._registry
        }


# Singleton instance
_CANDIDATE_REGISTRY: Optional[CandidateRegistry] = None


def get_candidate_registry() -> CandidateRegistry:
    """Get the singleton CandidateRegistry instance.

    Returns:
        The global CandidateRegistry instance
    """
    global _CANDIDATE_REGISTRY
    if _CANDIDATE_REGISTRY is None:
        _CANDIDATE_REGISTRY = CandidateRegistry()
    return _CANDIDATE_REGISTRY


def reset_candidate_registry() -> None:
    """Reset the singleton CandidateRegistry (for testing)."""
    global _CANDIDATE_REGISTRY
    _CANDIDATE_REGISTRY = None


def validate_routing_decision(
    transition_point: str,
    node_name: str
) -> None:
    """Validate a routing decision against the candidate registry.

    This is a convenience function that uses the singleton registry.

    Args:
        transition_point: Name of the transition point
        node_name: Name of the selected node

    Raises:
        DeprecatedNodeError: If the node is deprecated
        InvalidCandidateError: If the node is not a valid candidate
    """
    registry = get_candidate_registry()
    registry.validate(transition_point, node_name)


def get_candidates_for_router() -> List[RoutingCandidate]:
    """Get valid candidates for the Router transition point.

    This is a convenience function for the most common use case.

    Returns:
        List of valid candidate nodes for the Router
    """
    registry = get_candidate_registry()
    return registry.get_candidates("router")


def is_valid_router_candidate(node_name: str) -> bool:
    """Check if a node is a valid Router candidate.

    This is a convenience function for the most common use case.

    Args:
        node_name: Name of the node to check

    Returns:
        True if the node is a valid Router candidate
    """
    registry = get_candidate_registry()
    return registry.is_valid_candidate("router", node_name)
