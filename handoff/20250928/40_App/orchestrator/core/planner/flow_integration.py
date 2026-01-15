"""
Flow Integration - FlowController ↔ AgentState Bridge

EPIC F Phase F-3b: Flow Integration Layer

This module provides the integration layer between FlowController and the
existing LangGraph orchestrator's AgentState. It handles:
- Converting existing planner output to PlannerOutput format
- Executing plans via FlowController with AgentTaskExecutor
- Mapping ExecutionResult back to AgentState updates

Blueprint Reference: Section 3.2 (Flow Controller v3 - Intelligent Dynamic State Machine)

Usage:
    from core.planner.flow_integration import execute_with_flow_controller

    # In a LangGraph node
    def flow_executor_node(state: AgentState) -> AgentState:
        return execute_with_flow_controller(state)
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from .adapters import _infer_task_type_from_description
from .agent_assignment import (
    AssignmentContext,
    SelectionContext,
    assign_and_select,
)
from .agent_task_executor import (
    AgentTaskExecutor,
    AgentTaskExecutorConfig,
)
from .consumer import ExecutionResult, ExecutionStatus, TaskResult
from .flow_controller import FlowController, create_flow_controller
from .self_refinement import (
    FeedbackCollector,
    Replanner,
    _use_self_refinement,
)
from .planner_types import (
    CostEstimate,
    EdgeType,
    PlannerMetadata,
    PlannerOutput,
    PlanType,
    RiskLevel,
    RiskMetadata,
    TaskEdge,
    TaskNode,
    TaskTree,
    TaskType,
)
from memory.memory_integration import (
    save_flow_state,
    clear_flow_state,
)

logger = logging.getLogger(__name__)


@dataclass
class FlowIntegrationConfig:
    """
    Configuration for flow integration.

    Attributes:
        dry_run: If True, simulate execution without calling real agents
        max_parallel: Maximum number of tasks to execute in parallel
        stop_on_failure: Whether to stop execution on task failure
        timeout_seconds: Timeout for task execution in seconds
        max_retries: Maximum number of retries for failed tasks
        max_refinement_iterations: Maximum F-5 self-refinement iterations (default 3)
    """
    dry_run: bool = False
    max_parallel: int = 3
    stop_on_failure: bool = True
    timeout_seconds: int = 300
    max_retries: int = 2
    max_refinement_iterations: int = 3


class AgentStateUpdate(TypedDict, total=False):
    """
    Partial AgentState update returned by flow integration.

    This TypedDict defines the fields that flow integration may update
    in the AgentState after plan execution.
    """
    plan: List[str]
    current_step: int
    error: str
    final_result: Dict[str, Any]
    flow_execution_result: Dict[str, Any]
    flow_execution_status: str
    flow_completed_tasks: List[str]
    flow_failed_tasks: List[str]


def _convert_string_plan_to_planner_output(
    plan_steps: List[str],
    goal: str,
    trace_id: str,
) -> PlannerOutput:
    """
    Convert a list of string plan steps to PlannerOutput.

    This handles the common AgentState plan format where plan is a list
    of string descriptions (e.g., from LLM planner).

    Args:
        plan_steps: List of plan step descriptions
        goal: Original goal/request
        trace_id: Trace ID for logging

    Returns:
        PlannerOutput with converted task tree
    """
    plan_id = str(uuid.uuid4())

    nodes: List[TaskNode] = []
    edges: List[TaskEdge] = []

    for i, step in enumerate(plan_steps):
        task_id = f"task-{i + 1}"
        task_type = _infer_task_type_from_description(step)

        node = TaskNode(
            task_id=task_id,
            task_type=task_type,
            description=step if step else "",
            estimated_duration_minutes=10,
            inputs={},
            outputs={},
            requires_approval=False,
        )
        nodes.append(node)

        if i > 0:
            edge = TaskEdge(
                from_task=f"task-{i}",
                to_task=task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

    task_tree = TaskTree(nodes=nodes, edges=edges)

    return PlannerOutput(
        plan_id=plan_id,
        plan_type=PlanType.DETAILED,
        goal=goal,
        task_tree=task_tree,
        flow_template="full_pipeline",
        model_tier_hints={},
        risk_metadata=RiskMetadata(overall_risk=RiskLevel.MEDIUM),
        cost_estimate=CostEstimate(),
        planner_metadata=PlannerMetadata(
            planner_type="flow_integration",
            trace_id=trace_id,
            confidence_score=0.8,
        ),
    )


def _convert_dict_plan_to_planner_output(
    plan_dicts: List[Dict[str, Any]],
    goal: str,
    trace_id: str,
) -> PlannerOutput:
    """
    Convert a list of dict plan items to PlannerOutput.

    This handles AgentState plan formats where plan is a list of dicts
    (e.g., from TaskPlanner or PMAgent).

    Args:
        plan_dicts: List of plan item dictionaries
        goal: Original goal/request
        trace_id: Trace ID for logging

    Returns:
        PlannerOutput with converted task tree
    """
    plan_id = str(uuid.uuid4())

    nodes: List[TaskNode] = []
    edges: List[TaskEdge] = []

    for i, item in enumerate(plan_dicts):
        task_id = item.get("task_id", f"task-{i + 1}")
        description = item.get("description", item.get("task", ""))
        task_type_str = item.get("task_type", item.get("task", "code"))
        task_type = _infer_task_type_from_description(description) if description else TaskType.CODE

        node = TaskNode(
            task_id=task_id,
            task_type=task_type,
            description=description,
            estimated_duration_minutes=item.get("estimated_duration_minutes", 10),
            inputs=item.get("inputs", {}),
            outputs=item.get("outputs", {}),
            requires_approval=item.get("requires_approval", False),
        )
        nodes.append(node)

        dependencies = item.get("dependencies", [])
        for dep_id in dependencies:
            edge = TaskEdge(
                from_task=dep_id,
                to_task=task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

        if not dependencies and i > 0:
            edge = TaskEdge(
                from_task=f"task-{i}",
                to_task=task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

    task_tree = TaskTree(nodes=nodes, edges=edges)

    return PlannerOutput(
        plan_id=plan_id,
        plan_type=PlanType.DETAILED,
        goal=goal,
        task_tree=task_tree,
        flow_template="full_pipeline",
        model_tier_hints={},
        risk_metadata=RiskMetadata(overall_risk=RiskLevel.MEDIUM),
        cost_estimate=CostEstimate(),
        planner_metadata=PlannerMetadata(
            planner_type="flow_integration",
            trace_id=trace_id,
            confidence_score=0.8,
        ),
    )


def _extract_plan_from_state(state: Dict[str, Any]) -> Optional[PlannerOutput]:
    """
    Extract and convert plan from AgentState to PlannerOutput.

    This function converts the plan in AgentState to a unified PlannerOutput
    format. It handles multiple plan formats:
    - List of strings (LLM planner output)
    - List of dicts (TaskPlanner or PMAgent output)

    Args:
        state: The AgentState dictionary

    Returns:
        PlannerOutput if conversion successful, None otherwise
    """
    plan = state.get("plan")
    goal = state.get("goal", "")
    trace_id = state.get("trace_id", str(uuid.uuid4()))

    if not plan:
        logger.debug("[FlowIntegration] No plan found in state")
        return None

    if isinstance(plan, list) and len(plan) > 0:
        if isinstance(plan[0], str):
            result = _convert_string_plan_to_planner_output(plan, goal, trace_id)
            logger.info(
                "[FlowIntegration] Converted string plan to PlannerOutput",
                extra={
                    "task_count": len(result.task_tree.nodes),
                    "operation": "extract_plan",
                }
            )
            return result
        elif isinstance(plan[0], dict):
            result = _convert_dict_plan_to_planner_output(plan, goal, trace_id)
            logger.info(
                "[FlowIntegration] Converted dict plan to PlannerOutput",
                extra={
                    "task_count": len(result.task_tree.nodes),
                    "operation": "extract_plan",
                }
            )
            return result

    logger.warning(
        "[FlowIntegration] Unable to convert plan to PlannerOutput",
        extra={"plan_type": type(plan).__name__, "operation": "extract_plan"}
    )
    return None


def _map_execution_result_to_state_update(
    result: ExecutionResult,
    plan: PlannerOutput,
) -> AgentStateUpdate:
    """
    Map ExecutionResult to AgentState update fields.

    This function converts the FlowController's ExecutionResult into
    fields that can be merged into AgentState.

    Args:
        result: The ExecutionResult from FlowController
        plan: The original PlannerOutput that was executed

    Returns:
        AgentStateUpdate with fields to merge into AgentState
    """
    completed_tasks = [
        r.task_id for r in result.task_results
        if r.status == ExecutionStatus.COMPLETED
    ]
    failed_tasks = [
        r.task_id for r in result.task_results
        if r.status == ExecutionStatus.FAILED
    ]
    skipped_tasks = [
        r.task_id for r in result.task_results
        if r.status == ExecutionStatus.SKIPPED
    ]

    update: AgentStateUpdate = {
        "current_step": len(completed_tasks),
        "flow_execution_result": result.to_dict(),
        "flow_execution_status": result.status.value,
        "flow_completed_tasks": completed_tasks,
        "flow_failed_tasks": failed_tasks,
    }

    if result.status == ExecutionStatus.COMPLETED:
        update["final_result"] = {
            "status": "success",
            "plan_id": result.plan_id,
            "completed_tasks": len(completed_tasks),
            "total_tasks": len(plan.task_tree.nodes),
            "duration_minutes": result.total_duration_minutes,
            "task_results": [r.to_dict() for r in result.task_results],
        }
        update["error"] = ""
    elif result.status == ExecutionStatus.FAILED:
        error_msg = result.error_summary or "Plan execution failed"
        update["error"] = error_msg
        update["final_result"] = {
            "status": "failed",
            "plan_id": result.plan_id,
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "skipped_tasks": len(skipped_tasks),
            "total_tasks": len(plan.task_tree.nodes),
            "duration_minutes": result.total_duration_minutes,
            "error": error_msg,
            "task_results": [r.to_dict() for r in result.task_results],
        }

    return update


def execute_with_flow_controller(
    state: Dict[str, Any],
    config: Optional[FlowIntegrationConfig] = None,
) -> AgentStateUpdate:
    """
    Execute the plan in AgentState using FlowController.

    This is the main entry point for flow integration. It:
    1. Extracts and converts the plan from AgentState
    2. Creates a FlowController with AgentTaskExecutor
    3. Executes the plan
    4. Maps the result back to AgentState update fields

    Args:
        state: The current AgentState dictionary
        config: Optional FlowIntegrationConfig for customization

    Returns:
        AgentStateUpdate with fields to merge into AgentState

    Example:
        def flow_executor_node(state: AgentState) -> AgentState:
            update = execute_with_flow_controller(state)
            return {**state, **update}
    """
    config = config or FlowIntegrationConfig()
    trace_id = state.get("trace_id", "unknown")

    logger.info(
        "[FlowIntegration] Starting flow execution",
        extra={
            "trace_id": trace_id,
            "dry_run": config.dry_run,
            "operation": "execute_with_flow_controller",
        }
    )

    plan = _extract_plan_from_state(state)
    if plan is None:
        logger.warning(
            "[FlowIntegration] No valid plan found, returning empty update",
            extra={"trace_id": trace_id, "operation": "execute_with_flow_controller"}
        )
        return AgentStateUpdate(
            error="No valid plan found in state",
            flow_execution_status="failed",
        )

    # EPIC F Phase F-4: Apply agent assignments and flow template selection
    # This is controlled by USE_AGENT_ASSIGNMENT feature flag (checked internally)
    try:
        trust_score = state.get("trust_score")
        assignment_context = AssignmentContext(
            trust_score=trust_score,
        ) if trust_score is not None else None

        is_hotfix = state.get("is_hotfix", False)
        user_preference = state.get("flow_template_preference")
        selection_context = SelectionContext(
            is_hotfix=is_hotfix,
            user_preference=user_preference,
            trust_score=trust_score,
        ) if is_hotfix or user_preference or trust_score is not None else None

        plan = assign_and_select(plan, assignment_context, selection_context)

        logger.info(
            "[FlowIntegration] F-4 agent assignment applied",
            extra={
                "trace_id": trace_id,
                "flow_template": plan.flow_template,
                "task_count": len(plan.task_tree.nodes),
                "operation": "execute_with_flow_controller",
            }
        )
    except Exception as e:
        # F-4 is non-critical, log and continue with unassigned plan
        logger.warning(
            "[FlowIntegration] F-4 agent assignment failed, continuing with default",
            extra={
                "trace_id": trace_id,
                "error_type": type(e).__name__,
                "operation": "execute_with_flow_controller",
            }
        )

    executor_config = AgentTaskExecutorConfig(
        dry_run=config.dry_run,
        timeout_seconds=config.timeout_seconds,
        retry_count=config.max_retries,
    )
    task_executor = AgentTaskExecutor(config=executor_config)

    controller = create_flow_controller(
        task_executor=task_executor,
        max_parallel=config.max_parallel,
        stop_on_failure=config.stop_on_failure,
    )

    logger.info(
        "[FlowIntegration] Executing plan via FlowController",
        extra={
            "trace_id": trace_id,
            "plan_id": plan.plan_id,
            "task_count": len(plan.task_tree.nodes),
            "flow_template": plan.flow_template,
            "operation": "execute_with_flow_controller",
        }
    )

    # EPIC G: Save initial flow state to Memory v2 for recovery
    # This is controlled by ENABLE_MEMORY_V2_FLOW_STATE feature flag (checked internally)
    save_flow_state(
        plan_id=plan.plan_id,
        trace_id=trace_id,
        state_data={
            "goal": state.get("goal", ""),
            "plan": state.get("plan", []),
            "flow_template": plan.flow_template,
        },
        current_stage="initialized",
        completed_tasks=[],
        failed_tasks=[],
    )

    # EPIC F Phase F-5: Self-refinement loop with automatic replanning
    # This is controlled by USE_SELF_REFINEMENT feature flag (checked internally)
    use_refinement = _use_self_refinement()
    feedback_collector = FeedbackCollector() if use_refinement else None
    replanner = Replanner() if use_refinement else None
    replan_history = []
    current_plan = plan
    max_refinement_iterations = config.max_refinement_iterations

    for iteration in range(max_refinement_iterations + 1):
        try:
            result = controller.execute_plan(current_plan)

            # EPIC G: Update flow state after each iteration
            completed_tasks = [
                r.task_id for r in result.task_results
                if r.status == ExecutionStatus.COMPLETED
            ]
            failed_tasks = [
                r.task_id for r in result.task_results
                if r.status == ExecutionStatus.FAILED
            ]
            save_flow_state(
                plan_id=current_plan.plan_id,
                trace_id=trace_id,
                state_data={
                    "goal": state.get("goal", ""),
                    "plan": state.get("plan", []),
                    "flow_template": current_plan.flow_template,
                    "iteration": iteration,
                    "result_status": result.status.value,
                },
                current_stage=f"iteration_{iteration}",
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
            )
        except Exception as e:
            logger.error(
                "[FlowIntegration] Plan execution raised exception",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "operation": "execute_with_flow_controller",
                    "iteration": iteration,
                },
                exc_info=True,
            )
            return AgentStateUpdate(
                error="Plan execution failed due to an internal error. Check logs for details.",
                flow_execution_status="failed",
            )

        # If execution succeeded or refinement is disabled, return result
        if result.status == ExecutionStatus.COMPLETED or not use_refinement:
            break

        # F-5: Collect feedback and attempt replanning on failure
        if iteration < max_refinement_iterations:
            try:
                feedbacks = [
                    feedback_collector.collect(r.task_id, r)
                    for r in result.task_results
                ]
                plan_feedback = feedback_collector.aggregate(
                    feedbacks, current_plan.plan_id
                )

                if not replanner.should_replan(current_plan, plan_feedback):
                    logger.warning(
                        "[FlowIntegration] F-5 cannot replan, escalating to HITL",
                        extra={
                            "trace_id": trace_id,
                            "plan_id": current_plan.plan_id,
                            "iteration": iteration,
                            "operation": "execute_with_flow_controller",
                        }
                    )
                    break

                # Determine replan type based on failure pattern
                failed_task_ids = plan_feedback.failed_task_ids
                if len(failed_task_ids) == 1:
                    failed_task_id = failed_task_ids[0]
                    failed_feedback = next(
                        (f for f in feedbacks if f.task_id == failed_task_id),
                        None
                    )
                    if failed_feedback is None:
                        # Consistency error: failed task ID not found in feedback
                        logger.warning(
                            "[FlowIntegration] F-5 consistency error: failed task ID %s "
                            "not found in feedback list. Escalating to HITL.",
                            failed_task_id,
                            extra={
                                "trace_id": trace_id,
                                "plan_id": current_plan.plan_id,
                                "iteration": iteration,
                                "operation": "execute_with_flow_controller",
                            }
                        )
                        break
                    current_plan = replanner.replan_partial(
                        current_plan, failed_task_id, failed_feedback
                    )
                    replan_history.append({
                        "type": "partial",
                        "failed_task_id": failed_task_id,
                        "iteration": iteration,
                    })
                else:
                    current_plan = replanner.replan_full(
                        current_plan, plan_feedback
                    )
                    replan_history.append({
                        "type": "full",
                        "failed_task_ids": failed_task_ids,
                        "iteration": iteration,
                    })

                logger.info(
                    "[FlowIntegration] F-5 replanned, continuing execution",
                    extra={
                        "trace_id": trace_id,
                        "plan_id": current_plan.plan_id,
                        "replan_type": replan_history[-1]["type"],
                        "iteration": iteration + 1,
                        "operation": "execute_with_flow_controller",
                    }
                )
            except Exception as e:
                logger.warning(
                    "[FlowIntegration] F-5 replanning failed, returning current result",
                    extra={
                        "trace_id": trace_id,
                        "error_type": type(e).__name__,
                        "iteration": iteration,
                        "operation": "execute_with_flow_controller",
                    }
                )
                break

    logger.info(
        "[FlowIntegration] Plan execution completed",
        extra={
            "trace_id": trace_id,
            "plan_id": current_plan.plan_id,
            "status": result.status.value,
            "completed_tasks": result.get_completed_count(),
            "failed_tasks": result.get_failed_count(),
            "duration_minutes": result.total_duration_minutes,
            "replan_count": len(replan_history),
            "operation": "execute_with_flow_controller",
        }
    )

    # EPIC G: Clear flow state on successful completion
    # This cleans up Short-Term Memory after plan execution
    if result.status == ExecutionStatus.COMPLETED:
        clear_flow_state(current_plan.plan_id)

    return _map_execution_result_to_state_update(result, current_plan)


def create_flow_executor_node(
    config: Optional[FlowIntegrationConfig] = None,
):
    """
    Factory function to create a flow executor node for LangGraph.

    This creates a node function that can be added to a LangGraph StateGraph.
    The node executes the plan using FlowController and returns state updates.

    Args:
        config: Optional FlowIntegrationConfig for customization

    Returns:
        A node function compatible with LangGraph StateGraph

    Example:
        from langgraph.graph import StateGraph
        from core.planner.flow_integration import create_flow_executor_node

        graph = StateGraph(AgentState)
        graph.add_node("flow_executor", create_flow_executor_node())
    """
    config = config or FlowIntegrationConfig()

    def flow_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node that executes plans via FlowController.

        Args:
            state: The current AgentState

        Returns:
            Updated state fields
        """
        update = execute_with_flow_controller(state, config)
        return dict(update)

    return flow_executor_node


def validate_flow_integration_ready(state: Dict[str, Any]) -> bool:
    """
    Check if the state is ready for flow integration execution.

    This function validates that the state contains the necessary
    fields for flow integration to work properly.

    Args:
        state: The AgentState dictionary to validate

    Returns:
        True if state is ready for flow integration, False otherwise
    """
    required_fields = ["plan", "goal"]
    for field in required_fields:
        if field not in state or not state[field]:
            logger.debug(
                f"[FlowIntegration] Missing required field: {field}",
                extra={"operation": "validate_flow_integration_ready"}
            )
            return False

    plan = state.get("plan")
    if not isinstance(plan, list) or len(plan) == 0:
        logger.debug(
            "[FlowIntegration] Plan is empty or not a list",
            extra={"operation": "validate_flow_integration_ready"}
        )
        return False

    return True
