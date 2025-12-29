"""
Routing Engine for Multi-Model LLM Selection

This module implements the routing policy for selecting appropriate LLM models
based on task type, risk level, and context size.

EPIC #2594 - Ticket 2: Routing Policy v1.1
EPIC B-6: Reviewer -> Router Interface (ReviewOutcome schema)

Usage:
    from core.routing import RoutingEngine, Tier, TaskType, RiskLevel

    engine = RoutingEngine()
    model_info = engine.select_model(
        task_type=TaskType.PLANNING,
        risk_level=RiskLevel.HIGH,
        context_size=1000
    )
    print(f"Selected: {model_info.model_name} from {model_info.provider}")

    # EPIC B-6: ReviewOutcome for Reviewer -> Router interface
    from core.routing import ReviewOutcome, build_review_outcome
    outcome = build_review_outcome(
        review_comments=state["review_comments"],
        review_severity=state["review_severity"],
        review_result=state["review_result"],
        diff_truncated=state.get("diff_truncated", False)
    )
"""
from .engine import RoutingEngine, Tier, TaskType, ModelInfo, RiskLevel
from .review_outcome import (
    ReviewOutcome,
    build_review_outcome,
    build_unknown_outcome,
    VerdictType,
    SeverityType,
)
from .fix_handoff import (
    FixSuggestion,
    ReviewToFixHandoff,
    build_fix_handoff,
    should_route_to_fixer,
    build_empty_handoff,
    FixCategoryType,
    HIGH_CONFIDENCE_THRESHOLD,
)

__all__ = [
    'RoutingEngine',
    'Tier',
    'TaskType',
    'ModelInfo',
    'RiskLevel',
    # EPIC B-6: Reviewer -> Router interface
    'ReviewOutcome',
    'build_review_outcome',
    'build_unknown_outcome',
    'VerdictType',
    'SeverityType',
    # EPIC D: Review -> Fix Handoff interface
    'FixSuggestion',
    'ReviewToFixHandoff',
    'build_fix_handoff',
    'should_route_to_fixer',
    'build_empty_handoff',
    'FixCategoryType',
    'HIGH_CONFIDENCE_THRESHOLD',
]
