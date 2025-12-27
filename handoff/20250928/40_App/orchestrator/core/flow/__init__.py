"""
Flow Controller v3 - Core Flow Module

EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 0: Foundations (Issues #2744-#2747)

This module provides:
- Schema definitions for routing decisions (C-1)
- RouterNode interface with decision validation (C-2)
- Router metrics and telemetry (C-4)

Feature Flag: ENABLE_DYNAMIC_ROUTING (default: False)
When False, 100% of traffic uses the existing conditional_edges routing.
When True, enables LLM-driven dynamic routing with fail-safe fallback.

Usage:
    from core.flow import RoutingCandidate, RoutingDecision, RoutingContext
    from core.flow import RouterNode
    from core.flow import RouterMetrics
"""
from .schema import (
    RoutingCandidate,
    RoutingDecision,
    RoutingContext,
)
from .router_node import RouterNode
from .router_metrics import RouterMetrics

__all__ = [
    # C-1: Schema definitions
    'RoutingCandidate',
    'RoutingDecision',
    'RoutingContext',
    # C-2: Router node
    'RouterNode',
    # C-4: Metrics
    'RouterMetrics',
]
