"""
Planner v3 Core Module

EPIC F: Planner v3 - Intelligent Planning System

This module provides the unified Planner v3 interface and data structures
for task decomposition, DAG-based execution planning, and agent assignment.

Components:
- planner_types: Data structures for Planner v3 output (TaskNode, TaskEdge, PlannerOutput)
- consumer: Flow Controller consumption interface (PlanConsumer protocol)
"""

from .planner_types import (
    TaskType,
    EdgeType,
    RiskLevel,
    PlanType,
    TaskNode,
    TaskEdge,
    TaskTree,
    RiskMetadata,
    CostEstimate,
    PlannerMetadata,
    PlannerOutput,
)

from .consumer import (
    ExecutionStatus,
    TaskResult,
    ExecutionResult,
    PlanConsumer,
    BasePlanConsumer,
    DryRunPlanConsumer,
)

__all__ = [
    # Planner types
    "TaskType",
    "EdgeType",
    "RiskLevel",
    "PlanType",
    "TaskNode",
    "TaskEdge",
    "TaskTree",
    "RiskMetadata",
    "CostEstimate",
    "PlannerMetadata",
    "PlannerOutput",
    # Consumer types
    "ExecutionStatus",
    "TaskResult",
    "ExecutionResult",
    "PlanConsumer",
    "BasePlanConsumer",
    "DryRunPlanConsumer",
]
