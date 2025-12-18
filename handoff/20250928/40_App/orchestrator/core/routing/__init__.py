"""
Routing Engine for Multi-Model LLM Selection

This module implements the routing policy for selecting appropriate LLM models
based on task type, risk level, and context size.

EPIC #2594 - Ticket 2: Routing Policy v1.1

Usage:
    from core.routing import RoutingEngine, Tier, TaskType, RiskLevel

    engine = RoutingEngine()
    model_info = engine.select_model(
        task_type=TaskType.PLANNING,
        risk_level=RiskLevel.HIGH,
        context_size=1000
    )
    print(f"Selected: {model_info.model_name} from {model_info.provider}")
"""
from .engine import RoutingEngine, Tier, TaskType, ModelInfo, RiskLevel

__all__ = [
    'RoutingEngine',
    'Tier',
    'TaskType',
    'ModelInfo',
    'RiskLevel',
]
