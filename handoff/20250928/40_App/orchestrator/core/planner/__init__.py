"""
Planner v3 Core Module

EPIC F: Planner v3 - Intelligent Planning System

This module provides the unified Planner v3 interface and data structures
for task decomposition, DAG-based execution planning, and agent assignment.

Components:
- planner_types: Data structures for Planner v3 output (TaskNode, TaskEdge, PlannerOutput)
- consumer: Flow Controller consumption interface (PlanConsumer protocol)
- dag_builder: DAG construction utilities (Phase F-2)
- parallel_executor: Parallel task execution (Phase F-2)
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

from .adapters import (
    adapt_llm_planner_output,
    adapt_task_planner_output,
    adapt_pm_agent_output,
)

from .dag_builder import (
    DAGBuilder,
    ValidationResult,
    PARALLEL_SAFE_TASK_TYPES,
    PARALLEL_UNSAFE_TASK_TYPES,
)

from .parallel_executor import (
    ExecutionStatus as ParallelExecutionStatus,
    TaskExecutionResult,
    BatchExecutionResult,
    TaskExecutor,
    SimpleTaskExecutor,
    ParallelExecutor,
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
    # Adapters (Phase F-1)
    "adapt_llm_planner_output",
    "adapt_task_planner_output",
    "adapt_pm_agent_output",
    # DAG Builder (Phase F-2)
    "DAGBuilder",
    "ValidationResult",
    "PARALLEL_SAFE_TASK_TYPES",
    "PARALLEL_UNSAFE_TASK_TYPES",
    # Parallel Executor (Phase F-2)
    "ParallelExecutionStatus",
    "TaskExecutionResult",
    "BatchExecutionResult",
    "TaskExecutor",
    "SimpleTaskExecutor",
    "ParallelExecutor",
]
