"""
Planner Adapters - Phase F-1 Unified Output Conversion

EPIC F Phase F-1: Planner Adapter Layer

This module provides adapter functions to convert output from existing planners
(LLMPlannerAdapter, TaskPlanner, PMAgent) to the unified PlannerOutput format
defined in Phase F-0.

Blueprint Reference: Section 3.1 (Planner v3 - Unified Planning Interface)
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

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

if TYPE_CHECKING:
    from orchestrator.meta_agent.task_planner import TaskPlan
    from orchestrator.pm_agent.agent import PMAdvisory

logger = logging.getLogger(__name__)


# Mapping from TaskPlanner SubTaskType to unified TaskType
SUBTASK_TYPE_TO_TASK_TYPE: Dict[str, TaskType] = {
    "setup_environment": TaskType.SETUP,
    "analyze_code": TaskType.ANALYZE,
    "write_code": TaskType.CODE,
    "write_test": TaskType.TEST,
    "run_test": TaskType.TEST,
    "code_review": TaskType.REVIEW,
    "documentation": TaskType.DOCUMENT,
    "deployment": TaskType.DEPLOY,
    "verification": TaskType.VERIFY,
    "cleanup": TaskType.CLEANUP,
}

# Mapping from PMAgent task types to unified TaskType
PM_TASK_TYPE_TO_TASK_TYPE: Dict[str, TaskType] = {
    "documentation": TaskType.DOCUMENT,
    "bug_fix": TaskType.CODE,
    "feature": TaskType.CODE,
    "refactor": TaskType.CODE,
    "test": TaskType.TEST,
    "config": TaskType.SETUP,
    "security": TaskType.CODE,
    "performance": TaskType.CODE,
    "unknown": TaskType.CODE,
}

# Mapping from PMRisk to RiskLevel
PM_RISK_TO_RISK_LEVEL: Dict[str, RiskLevel] = {
    "critical": RiskLevel.CRITICAL,
    "high": RiskLevel.HIGH,
    "medium": RiskLevel.MEDIUM,
    "low": RiskLevel.LOW,
    "info": RiskLevel.LOW,
}

# Effort to duration mapping (minutes)
EFFORT_TO_DURATION: Dict[str, int] = {
    "small": 15,
    "medium": 30,
    "large": 60,
}


def adapt_llm_planner_output(
    llm_result: Dict[str, Any],
    goal: str = "",
    trace_id: Optional[str] = None,
) -> PlannerOutput:
    """
    Convert LLMPlannerAdapter output to unified PlannerOutput format.

    Args:
        llm_result: Output from LLMPlannerAdapter.generate_plan()
            Expected keys: plan, plan_details, planner_type, task_type,
                          planning_time_ms, provider
        goal: Original goal/request
        trace_id: Optional trace ID for logging

    Returns:
        PlannerOutput with converted task tree
    """
    trace_id = trace_id or str(uuid.uuid4())
    plan_id = str(uuid.uuid4())

    logger.info(
        "[Adapter] Converting LLMPlannerAdapter output to PlannerOutput",
        extra={"operation": "adapt_llm_planner", "trace_id": trace_id}
    )

    # Extract plan steps
    plan_steps = llm_result.get("plan", [])
    plan_details = llm_result.get("plan_details", [])

    # Build TaskNodes from plan steps
    nodes: List[TaskNode] = []
    edges: List[TaskEdge] = []

    for i, step in enumerate(plan_steps):
        task_id = f"task-{i + 1}"

        # Get details if available
        detail = plan_details[i] if i < len(plan_details) else {}
        estimated_minutes = detail.get("estimated_minutes", 10)

        # Infer task type from step description
        task_type = _infer_task_type_from_description(step)

        node = TaskNode(
            task_id=task_id,
            task_type=task_type,
            description=step,
            estimated_duration_minutes=estimated_minutes,
            inputs={},
            outputs={},
            requires_approval=False,
            metadata={"original_detail": detail} if detail else {},
        )
        nodes.append(node)

        # Create sequential dependency edges (each task depends on previous)
        if i > 0:
            edge = TaskEdge(
                source_id=f"task-{i}",
                target_id=task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

    # Build TaskTree
    task_tree = TaskTree(nodes=nodes, edges=edges)

    # Build metadata
    planner_metadata = PlannerMetadata(
        planner_type=llm_result.get("planner_type", "llm"),
        planning_time_ms=llm_result.get("planning_time_ms", 0.0),
        confidence_score=0.8,  # LLM plans have moderate confidence
        trace_id=trace_id,
        provider=llm_result.get("provider"),
    )

    # Determine flow template based on task type
    task_type_str = llm_result.get("task_type", "unknown")
    flow_template = _determine_flow_template(task_type_str)

    return PlannerOutput(
        plan_id=plan_id,
        plan_type=PlanType.DETAILED,
        goal=goal,
        task_tree=task_tree,
        flow_template=flow_template,
        model_tier_hints={},
        risk_metadata=RiskMetadata(overall_risk=RiskLevel.MEDIUM),
        cost_estimate=CostEstimate(),
        planner_metadata=planner_metadata,
    )


def adapt_task_planner_output(
    task_plan: "TaskPlan",
    trace_id: Optional[str] = None,
) -> PlannerOutput:
    """
    Convert TaskPlanner output to unified PlannerOutput format.

    Args:
        task_plan: Output from TaskPlanner.create_plan()
        trace_id: Optional trace ID for logging

    Returns:
        PlannerOutput with converted task tree
    """
    trace_id = trace_id or str(uuid.uuid4())

    logger.info(
        "[Adapter] Converting TaskPlanner output to PlannerOutput",
        extra={"operation": "adapt_task_planner", "trace_id": trace_id}
    )

    # Build TaskNodes from subtasks
    nodes: List[TaskNode] = []
    edges: List[TaskEdge] = []

    for subtask in task_plan.subtasks:
        # Map SubTaskType to TaskType
        task_type_str = subtask.task_type.value if hasattr(subtask.task_type, 'value') else str(subtask.task_type)
        task_type = SUBTASK_TYPE_TO_TASK_TYPE.get(task_type_str, TaskType.CODE)

        node = TaskNode(
            task_id=subtask.task_id,
            task_type=task_type,
            description=subtask.description,
            estimated_duration_minutes=subtask.estimated_duration_minutes,
            inputs=subtask.inputs,
            outputs=subtask.outputs,
            requires_approval=subtask.requires_approval,
            metadata={
                "agent_type": subtask.agent_type,
                "priority": subtask.priority,
            },
        )
        nodes.append(node)

        # Create dependency edges
        for dep_id in subtask.dependencies:
            edge = TaskEdge(
                source_id=dep_id,
                target_id=subtask.task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

    # Build TaskTree
    task_tree = TaskTree(nodes=nodes, edges=edges)

    # Extract goal summary
    goal_summary = ""
    if hasattr(task_plan.goal, 'summary'):
        goal_summary = task_plan.goal.summary
    elif hasattr(task_plan.goal, 'raw_input'):
        goal_summary = task_plan.goal.raw_input

    # Determine flow template from goal type
    flow_template = "full_pipeline"
    if hasattr(task_plan.goal, 'goal_type'):
        goal_type = task_plan.goal.goal_type.value if hasattr(task_plan.goal.goal_type, 'value') else str(task_plan.goal.goal_type)
        flow_template = _determine_flow_template(goal_type)

    # Build metadata
    planner_metadata = PlannerMetadata(
        planner_type="task_planner",
        planning_time_ms=0.0,  # TaskPlanner doesn't track this
        confidence_score=0.9,  # Template-based plans have high confidence
        trace_id=trace_id,
    )

    return PlannerOutput(
        plan_id=task_plan.plan_id,
        plan_type=PlanType.DETAILED,
        goal=goal_summary,
        task_tree=task_tree,
        flow_template=flow_template,
        model_tier_hints={},
        risk_metadata=RiskMetadata(overall_risk=RiskLevel.LOW),
        cost_estimate=CostEstimate(
            estimated_total_minutes=task_plan.total_estimated_minutes
        ),
        planner_metadata=planner_metadata,
    )


def adapt_pm_agent_output(
    pm_advisory: "PMAdvisory",
    trace_id: Optional[str] = None,
) -> PlannerOutput:
    """
    Convert PMAgent output to unified PlannerOutput format.

    Args:
        pm_advisory: Output from PMAgent.decompose_goal()
        trace_id: Optional trace ID for logging

    Returns:
        PlannerOutput with converted task tree
    """
    trace_id = trace_id or str(uuid.uuid4())
    plan_id = str(uuid.uuid4())

    logger.info(
        "[Adapter] Converting PMAgent output to PlannerOutput",
        extra={"operation": "adapt_pm_agent", "trace_id": trace_id}
    )

    # Build TaskNodes from sub_tasks
    nodes: List[TaskNode] = []
    edges: List[TaskEdge] = []

    sub_tasks = pm_advisory.sub_tasks if hasattr(pm_advisory, 'sub_tasks') else []

    for subtask in sub_tasks:
        # Map PM task type to TaskType
        task_type_str = subtask.task_type if hasattr(subtask, 'task_type') else "unknown"
        task_type = PM_TASK_TYPE_TO_TASK_TYPE.get(task_type_str, TaskType.CODE)

        # Convert effort to duration
        effort = subtask.estimated_effort if hasattr(subtask, 'estimated_effort') else "medium"
        estimated_minutes = EFFORT_TO_DURATION.get(effort, 30)

        node = TaskNode(
            task_id=subtask.task_id,
            task_type=task_type,
            description=subtask.description,
            estimated_duration_minutes=estimated_minutes,
            inputs={},
            outputs={},
            requires_approval=False,
            metadata={
                "title": subtask.title if hasattr(subtask, 'title') else "",
                "affected_files": subtask.affected_files if hasattr(subtask, 'affected_files') else [],
                "priority": subtask.priority if hasattr(subtask, 'priority') else 0,
            },
        )
        nodes.append(node)

        # Create dependency edges
        dependencies = subtask.dependencies if hasattr(subtask, 'dependencies') else []
        for dep_id in dependencies:
            edge = TaskEdge(
                source_id=dep_id,
                target_id=subtask.task_id,
                edge_type=EdgeType.DEPENDS_ON,
            )
            edges.append(edge)

    # Build TaskTree
    task_tree = TaskTree(nodes=nodes, edges=edges)

    # Map PMRisk to RiskLevel
    overall_risk_str = pm_advisory.overall_risk.value if hasattr(pm_advisory.overall_risk, 'value') else str(pm_advisory.overall_risk)
    overall_risk = PM_RISK_TO_RISK_LEVEL.get(overall_risk_str.lower(), RiskLevel.MEDIUM)

    # Build risk metadata from findings
    risk_factors = []
    if hasattr(pm_advisory, 'findings'):
        for finding in pm_advisory.findings:
            risk_factors.append(finding.title if hasattr(finding, 'title') else str(finding))

    risk_metadata = RiskMetadata(
        overall_risk=overall_risk,
        risk_factors=risk_factors[:5],  # Limit to top 5
        mitigation_suggestions=pm_advisory.recommendations if hasattr(pm_advisory, 'recommendations') else [],
    )

    # Build metadata
    planner_metadata = PlannerMetadata(
        planner_type="pm_agent",
        planning_time_ms=pm_advisory.metadata.get("latency_ms", 0.0) if hasattr(pm_advisory, 'metadata') and pm_advisory.metadata else 0.0,
        confidence_score=pm_advisory.confidence_score if hasattr(pm_advisory, 'confidence_score') else 0.7,
        trace_id=trace_id,
    )

    return PlannerOutput(
        plan_id=plan_id,
        plan_type=PlanType.DETAILED,
        goal=pm_advisory.goal if hasattr(pm_advisory, 'goal') else "",
        task_tree=task_tree,
        flow_template="full_pipeline",
        model_tier_hints={},
        risk_metadata=risk_metadata,
        cost_estimate=CostEstimate(),
        planner_metadata=planner_metadata,
    )


def _infer_task_type_from_description(description: str) -> TaskType:
    """
    Infer TaskType from step description using keyword matching.

    Args:
        description: Step description text

    Returns:
        Inferred TaskType
    """
    description_lower = description.lower()

    # Check for keywords in order of specificity
    if any(kw in description_lower for kw in ["setup", "install", "configure", "environment"]):
        return TaskType.SETUP
    if any(kw in description_lower for kw in ["analyze", "investigate", "examine", "review code", "understand"]):
        return TaskType.ANALYZE
    if any(kw in description_lower for kw in ["test", "spec", "coverage", "unit test", "integration test"]):
        return TaskType.TEST
    if any(kw in description_lower for kw in ["review", "code review", "self-review", "peer review"]):
        return TaskType.REVIEW
    if any(kw in description_lower for kw in ["document", "readme", "comment", "doc"]):
        return TaskType.DOCUMENT
    if any(kw in description_lower for kw in ["deploy", "release", "publish"]):
        return TaskType.DEPLOY
    if any(kw in description_lower for kw in ["verify", "validate", "check", "confirm"]):
        return TaskType.VERIFY
    if any(kw in description_lower for kw in ["cleanup", "clean up", "remove", "delete"]):
        return TaskType.CLEANUP
    if any(kw in description_lower for kw in ["implement", "code", "write", "create", "add", "fix", "modify"]):
        return TaskType.CODE

    # Default to CODE for unrecognized descriptions
    return TaskType.CODE


def _determine_flow_template(task_type: str) -> str:
    """
    Determine appropriate flow template based on task type.

    Args:
        task_type: Task type string from classifier

    Returns:
        Flow template name
    """
    task_type_lower = task_type.lower()

    if task_type_lower in ["documentation", "doc"]:
        return "doc_only"
    if task_type_lower in ["test", "testing"]:
        return "test_heavy"
    if task_type_lower in ["bug_fix", "bugfix"]:
        return "review_heavy"
    if task_type_lower in ["refactor", "refactoring"]:
        return "review_heavy"
    if task_type_lower in ["feature", "feature_development"]:
        return "full_pipeline"
    if task_type_lower in ["investigation"]:
        return "analysis_only"

    return "full_pipeline"
