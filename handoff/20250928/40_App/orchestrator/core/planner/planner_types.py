"""
Planner v3 Types - Data structures for EPIC F Planner v3

EPIC F Phase F-0: Planner Output Contract + Hierarchical Schema

This module defines the unified data structures for Planner v3 output,
enabling consistent plan representation across all planning mechanisms
(LLMPlannerAdapter, TaskPlanner, PMAgent).

Key Features:
- DAG-based task representation (TaskNode, TaskEdge, TaskTree)
- Hierarchical planning support (plan_type: milestone/detailed)
- Risk metadata for EPIC E integration
- Cost estimation hooks for Plan Oracle (future)
- Provider health input for resource-aware planning (future)

Blueprint Reference: Section 3.1 (Planner v3 - Intelligent Planner)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


class TaskType(Enum):
    """
    Types of tasks in a plan

    These task types align with the existing SubTaskType in TaskPlanner
    and provide a unified vocabulary for all planners.
    """
    SETUP = "setup"
    ANALYZE = "analyze"
    CODE = "code"
    TEST = "test"
    REVIEW = "review"
    DOCUMENT = "document"
    DEPLOY = "deploy"
    VERIFY = "verify"
    CLEANUP = "cleanup"


class EdgeType(Enum):
    """
    Types of edges in the task DAG

    - DEPENDS_ON: Target task cannot start until source completes
    - PARALLEL_WITH: Tasks can execute concurrently
    - OPTIONAL_AFTER: Target can start after source, but not required
    """
    DEPENDS_ON = "depends_on"
    PARALLEL_WITH = "parallel_with"
    OPTIONAL_AFTER = "optional_after"


class RiskLevel(Enum):
    """
    Risk levels for tasks and plans

    Aligns with PMRisk from PMAgent and risk levels in LLMPlannerAdapter.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanType(Enum):
    """
    Types of plans for hierarchical planning support

    - MILESTONE: High-level plan with expandable milestones
    - DETAILED: Fully expanded plan with all subtasks
    """
    MILESTONE = "milestone"
    DETAILED = "detailed"


@dataclass
class TaskNode:
    """
    Represents a single task in the plan DAG

    This is the unified task representation that all planners must produce.
    It combines fields from TaskPlanner.SubTask, PMAgent.SubTask, and
    LLMPlannerAdapter plan steps.

    Attributes:
        task_id: Unique identifier for this task
        task_type: Type of task (setup, analyze, code, etc.)
        description: Human-readable description of the task
        agent_assignment: Assigned agent type (e.g., 'dev_agent', 'reviewer_agent')
        estimated_duration_minutes: Estimated time to complete
        priority: Execution priority (lower = higher priority)
        risk_level: Risk level for this task
        requires_approval: Whether HITL approval is required
        expandable: For hierarchical planning - can this milestone be expanded?
        inputs: Input data/context for the task
        outputs: Expected outputs from the task
    """
    task_id: str
    task_type: TaskType
    description: str
    agent_assignment: str = "dev_agent"
    estimated_duration_minutes: int = 5
    priority: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    expandable: bool = False
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "agent_assignment": self.agent_assignment,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "priority": self.priority,
            "risk_level": self.risk_level.value,
            "requires_approval": self.requires_approval,
            "expandable": self.expandable,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        """Create TaskNode from dictionary"""
        return cls(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            description=data["description"],
            agent_assignment=data.get("agent_assignment", "dev_agent"),
            estimated_duration_minutes=data.get("estimated_duration_minutes", 5),
            priority=data.get("priority", 0),
            risk_level=RiskLevel(data.get("risk_level", "low")),
            requires_approval=data.get("requires_approval", False),
            expandable=data.get("expandable", False),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
        )


@dataclass
class TaskEdge:
    """
    Represents a dependency edge in the task DAG

    Attributes:
        from_task: Source task_id
        to_task: Target task_id
        edge_type: Type of dependency relationship
    """
    from_task: str
    to_task: str
    edge_type: EdgeType = EdgeType.DEPENDS_ON

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "from": self.from_task,
            "to": self.to_task,
            "type": self.edge_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskEdge":
        """Create TaskEdge from dictionary"""
        return cls(
            from_task=data["from"],
            to_task=data["to"],
            edge_type=EdgeType(data.get("type", "depends_on")),
        )


@dataclass
class TaskTree:
    """
    DAG representation of tasks

    This structure enables:
    - Dependency tracking between tasks
    - Parallel execution detection
    - Topological ordering for execution

    Attributes:
        nodes: List of TaskNode objects
        edges: List of TaskEdge objects defining dependencies
    """
    nodes: List[TaskNode] = field(default_factory=list)
    edges: List[TaskEdge] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskTree":
        """Create TaskTree from dictionary"""
        return cls(
            nodes=[TaskNode.from_dict(n) for n in data.get("nodes", [])],
            edges=[TaskEdge.from_dict(e) for e in data.get("edges", [])],
        )

    def get_node(self, task_id: str) -> Optional[TaskNode]:
        """Get a node by task_id"""
        for node in self.nodes:
            if node.task_id == task_id:
                return node
        return None

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get all task_ids that this task depends on"""
        return [
            edge.from_task
            for edge in self.edges
            if edge.to_task == task_id and edge.edge_type == EdgeType.DEPENDS_ON
        ]

    def get_dependents(self, task_id: str) -> List[str]:
        """Get all task_ids that depend on this task"""
        return [
            edge.to_task
            for edge in self.edges
            if edge.from_task == task_id and edge.edge_type == EdgeType.DEPENDS_ON
        ]

    def get_parallel_tasks(self, task_id: str) -> List[str]:
        """Get all task_ids that can run in parallel with this task"""
        parallel = []
        for edge in self.edges:
            if edge.edge_type == EdgeType.PARALLEL_WITH:
                if edge.from_task == task_id:
                    parallel.append(edge.to_task)
                elif edge.to_task == task_id:
                    parallel.append(edge.from_task)
        return parallel

    def get_executable_tasks(self, completed: Set[str]) -> List[TaskNode]:
        """
        Get tasks that are ready for execution (all dependencies met)

        Args:
            completed: Set of completed task_ids

        Returns:
            List of TaskNode objects ready for execution
        """
        executable = []
        for node in self.nodes:
            if node.task_id in completed:
                continue
            deps = self.get_dependencies(node.task_id)
            if all(dep in completed for dep in deps):
                executable.append(node)
        return executable

    def validate(self) -> List[str]:
        """
        Validate the DAG structure

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for missing nodes referenced in edges
        node_ids = {node.task_id for node in self.nodes}
        for edge in self.edges:
            if edge.from_task not in node_ids:
                errors.append(f"Edge references unknown source task: {edge.from_task}")
            if edge.to_task not in node_ids:
                errors.append(f"Edge references unknown target task: {edge.to_task}")

        # Check for cycles using DFS
        if not errors:
            visited: Set[str] = set()
            rec_stack: Set[str] = set()

            def has_cycle(task_id: str) -> bool:
                visited.add(task_id)
                rec_stack.add(task_id)

                for dep_id in self.get_dependents(task_id):
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

                rec_stack.remove(task_id)
                return False

            for node in self.nodes:
                if node.task_id not in visited:
                    if has_cycle(node.task_id):
                        errors.append("Cycle detected in task DAG")
                        break

        return errors


@dataclass
class RiskMetadata:
    """
    Risk metadata for a plan

    This structure provides hooks for EPIC E (Safety Governor v2) integration.

    Attributes:
        overall_risk: Overall risk level for the plan
        requires_approval: Whether the plan requires HITL approval
        trust_score_input: Hook for E+F+I closed loop (from EPIC I)
        risk_factors: List of identified risk factors
    """
    overall_risk: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    trust_score_input: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "overall_risk": self.overall_risk.value,
            "requires_approval": self.requires_approval,
            "trust_score_input": self.trust_score_input,
            "risk_factors": self.risk_factors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskMetadata":
        """Create RiskMetadata from dictionary"""
        return cls(
            overall_risk=RiskLevel(data.get("overall_risk", "low")),
            requires_approval=data.get("requires_approval", False),
            trust_score_input=data.get("trust_score_input"),
            risk_factors=data.get("risk_factors", []),
        )


@dataclass
class CostEstimate:
    """
    Cost estimation for a plan

    This structure provides hooks for Plan Oracle (future feature).

    Attributes:
        estimated_tokens: Estimated total tokens for the plan
        estimated_usd: Estimated cost in USD
        provider_breakdown: Cost breakdown by provider
    """
    estimated_tokens: int = 0
    estimated_usd: float = 0.0
    provider_breakdown: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "estimated_tokens": self.estimated_tokens,
            "estimated_usd": self.estimated_usd,
            "provider_breakdown": self.provider_breakdown,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostEstimate":
        """Create CostEstimate from dictionary"""
        return cls(
            estimated_tokens=data.get("estimated_tokens", 0),
            estimated_usd=data.get("estimated_usd", 0.0),
            provider_breakdown=data.get("provider_breakdown", {}),
        )


@dataclass
class PlannerMetadata:
    """
    Metadata about the planning process

    Attributes:
        planner_type: Which planner generated this plan (llm, template, pm_agent)
        planning_time_ms: Time taken to generate the plan
        confidence_score: Confidence in the plan (0.0 to 1.0)
        trace_id: Trace ID for telemetry
        provider: LLM provider used (if applicable)
    """
    planner_type: str = "unknown"
    planning_time_ms: float = 0.0
    confidence_score: float = 1.0
    trace_id: str = ""
    provider: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "planner_type": self.planner_type,
            "planning_time_ms": self.planning_time_ms,
            "confidence_score": self.confidence_score,
            "trace_id": self.trace_id,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerMetadata":
        """Create PlannerMetadata from dictionary"""
        return cls(
            planner_type=data.get("planner_type", "unknown"),
            planning_time_ms=data.get("planning_time_ms", 0.0),
            confidence_score=data.get("confidence_score", 1.0),
            trace_id=data.get("trace_id", ""),
            provider=data.get("provider"),
        )


@dataclass
class PlannerOutput:
    """
    Unified Planner v3 output schema

    This is the canonical output format for all Planner v3 operations.
    All existing planners (LLMPlannerAdapter, TaskPlanner, PMAgent) should
    be adapted to produce this format.

    Attributes:
        plan_id: Unique identifier for this plan
        plan_type: Type of plan (milestone or detailed)
        goal: Original goal/request that triggered planning
        task_tree: DAG representation of tasks
        flow_template: Selected flow template (e.g., 'review_heavy', 'code_only')
        model_tier_hints: Hints for model tier selection per task
        risk_metadata: Risk assessment for the plan
        cost_estimate: Cost estimation (hook for Plan Oracle)
        planner_metadata: Metadata about the planning process
        created_at: Creation timestamp in UTC
    """
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_type: PlanType = PlanType.DETAILED
    goal: str = ""
    task_tree: TaskTree = field(default_factory=TaskTree)
    flow_template: str = "full_pipeline"
    model_tier_hints: Dict[str, Any] = field(default_factory=dict)
    risk_metadata: RiskMetadata = field(default_factory=RiskMetadata)
    cost_estimate: CostEstimate = field(default_factory=CostEstimate)
    planner_metadata: PlannerMetadata = field(default_factory=PlannerMetadata)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type.value,
            "goal": self.goal,
            "task_tree": self.task_tree.to_dict(),
            "flow_template": self.flow_template,
            "model_tier_hints": self.model_tier_hints,
            "risk_metadata": self.risk_metadata.to_dict(),
            "cost_estimate": self.cost_estimate.to_dict(),
            "planner_metadata": self.planner_metadata.to_dict(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerOutput":
        """Create PlannerOutput from dictionary"""
        return cls(
            plan_id=data.get("plan_id", str(uuid.uuid4())),
            plan_type=PlanType(data.get("plan_type", "detailed")),
            goal=data.get("goal", ""),
            task_tree=TaskTree.from_dict(data.get("task_tree", {})),
            flow_template=data.get("flow_template", "full_pipeline"),
            model_tier_hints=data.get("model_tier_hints", {}),
            risk_metadata=RiskMetadata.from_dict(data.get("risk_metadata", {})),
            cost_estimate=CostEstimate.from_dict(data.get("cost_estimate", {})),
            planner_metadata=PlannerMetadata.from_dict(data.get("planner_metadata", {})),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    def get_total_estimated_minutes(self) -> int:
        """Calculate total estimated duration for the plan"""
        return sum(node.estimated_duration_minutes for node in self.task_tree.nodes)

    def get_task_count(self) -> int:
        """Get the number of tasks in the plan"""
        return len(self.task_tree.nodes)

    def validate(self) -> List[str]:
        """
        Validate the plan structure

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate task tree
        tree_errors = self.task_tree.validate()
        errors.extend(tree_errors)

        # Validate required fields
        if not self.goal:
            errors.append("Plan must have a goal")

        if not self.task_tree.nodes:
            errors.append("Plan must have at least one task")

        # Validate confidence score
        if not 0.0 <= self.planner_metadata.confidence_score <= 1.0:
            errors.append("Confidence score must be between 0.0 and 1.0")

        return errors

    def is_valid(self) -> bool:
        """Check if the plan is valid"""
        return len(self.validate()) == 0
