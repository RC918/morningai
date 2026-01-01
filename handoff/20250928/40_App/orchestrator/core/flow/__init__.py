"""
Flow Controller v3 - Core Flow Module

EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 0: Foundations (Issues #2744-#2747)
Stage 1: Hybrid Router (C-2 Router Node Logic)

This module provides:
- Schema definitions for routing decisions (C-1)
- RouterNode interface with decision validation (C-2)
- HybridRoutingPolicy for Rules + AI routing (C-2)
- Router metrics and telemetry (C-4)

Feature Flag: ENABLE_DYNAMIC_ROUTING (default: False)
When False, 100% of traffic uses the existing conditional_edges routing.
When True, enables LLM-driven dynamic routing with fail-safe fallback.

Usage:
    from core.flow import RoutingCandidate, RoutingDecision, RoutingContext
    from core.flow import RouterNode
    from core.flow import HybridRoutingPolicy, get_hybrid_router
    from core.flow import RouterMetrics
"""
from .schema import (
    RoutingCandidate,
    RoutingDecision,
    RoutingContext,
)
from .llm_safety import (
    check_json_safety,
    extract_json_from_response,
    parse_json_safely,
    JSONSafetyError,
    MAX_RESPONSE_SIZE,
    MAX_NESTING_DEPTH,
)
from .router_node import RouterNode
from .router_metrics import RouterMetrics
from .hybrid_router import (
    HybridRoutingPolicy,
    get_hybrid_router,
    canonicalize_node_name,
    NODE_ALIASES,
    CANONICAL_NODES,
    SEVERITY_ORDER,
)
from .candidate_registry import (
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

__all__ = [
    # C-1: Schema definitions
    'RoutingCandidate',
    'RoutingDecision',
    'RoutingContext',
    # LLM Safety (shared utilities)
    'check_json_safety',
    'extract_json_from_response',
    'parse_json_safely',
    'JSONSafetyError',
    'MAX_RESPONSE_SIZE',
    'MAX_NESTING_DEPTH',
    # C-2: Router node
    'RouterNode',
    # C-2: Hybrid router (Stage 1)
    'HybridRoutingPolicy',
    'get_hybrid_router',
    'canonicalize_node_name',
    'NODE_ALIASES',
    'CANONICAL_NODES',
    'SEVERITY_ORDER',
    # C-4: Metrics
    'RouterMetrics',
    # C-8: Candidate Registry (Stage 2)
    'CandidateRegistry',
    'get_candidate_registry',
    'reset_candidate_registry',
    'validate_routing_decision',
    'get_candidates_for_router',
    'is_valid_router_candidate',
    'InvalidCandidateError',
    'DeprecatedNodeError',
    'DEPRECATED_NODES',
    'SAFETY_CRITICAL_NODES',
]
