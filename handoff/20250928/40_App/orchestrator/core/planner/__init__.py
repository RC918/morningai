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

from .flow_controller import (
    FlowTemplate,
    FlowStage,
    FlowDefinition,
    FlowState,
    FlowController,
    TaskExecutor as FlowTaskExecutor,
    DefaultTaskExecutor,
    create_flow_controller,
    FLOW_DEFINITIONS,
)

from .agent_task_executor import (
    AgentTaskExecutor,
    AgentTaskExecutorConfig,
    AgentDispatcher,
    DefaultAgentDispatcher,
    create_agent_task_executor,
)

from .flow_integration import (
    FlowIntegrationConfig,
    AgentStateUpdate,
    execute_with_flow_controller,
    create_flow_executor_node,
    validate_flow_integration_ready,
)

from .self_refinement import (
    FeedbackStatus,
    ExecutionFeedback,
    PlanFeedback,
    FeedbackCollector,
    Replanner,
    RefinementResult,
    SelfRefinementLoop,
)

from .agent_assignment import (
    AssignmentContext,
    SelectionContext,
    AgentAssigner,
    FlowTemplateSelector,
    assign_and_select,
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
    # Flow Controller (Phase F-2)
    "FlowTemplate",
    "FlowStage",
    "FlowDefinition",
    "FlowState",
    "FlowController",
    "FlowTaskExecutor",
    "DefaultTaskExecutor",
    "create_flow_controller",
    "FLOW_DEFINITIONS",
    # Agent Task Executor (Phase F-3a)
    "AgentTaskExecutor",
    "AgentTaskExecutorConfig",
    "AgentDispatcher",
    "DefaultAgentDispatcher",
    "create_agent_task_executor",
    # Flow Integration (Phase F-3b)
    "FlowIntegrationConfig",
    "AgentStateUpdate",
    "execute_with_flow_controller",
    "create_flow_executor_node",
    "validate_flow_integration_ready",
    # Self-refinement Loop (Phase F-5)
    "FeedbackStatus",
    "ExecutionFeedback",
    "PlanFeedback",
    "FeedbackCollector",
    "Replanner",
    "RefinementResult",
    "SelfRefinementLoop",
    # Agent Assignment (Phase F-4)
    "AssignmentContext",
    "SelectionContext",
    "AgentAssigner",
    "FlowTemplateSelector",
    "assign_and_select",
]
