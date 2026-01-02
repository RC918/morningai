"""
Flow Controller v3 - Schema Definitions (C-1)

Issue #2744: C-1 Schema Definition
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 0: Foundations

This module defines the data contracts for flow routing:
- DecisionMode: How a routing decision was made (Issue #3496)
- RoutingResult: Wrapper with decision + metadata (Issue #3496)
- RoutingCandidate: Candidate node definition for LLM selection
- RoutingDecision: LLM routing decision result
- RoutingContext: Minimal context for Router to make decisions

Usage:
    from core.flow.schema import RoutingCandidate, RoutingDecision, RoutingContext

    # Define candidates
    candidates = [
        RoutingCandidate(node_name="publisher", description="Deploy changes to GitHub"),
        RoutingCandidate(node_name="fixer", description="Fix code issues"),
    ]

    # Build context
    context = RoutingContext(
        task_type="code_review",
        current_stage="review",
        step_history=["planner", "coder", "reviewer"],
        last_agent_feedback="Variable naming issues found",
        candidates=candidates
    )

    # Parse LLM decision
    decision = RoutingDecision(
        next_node="fixer",
        reasoning="Reviewer found naming issues that need fixing",
        risk_assessment="Low risk - standard code fix"
    )
"""
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class DecisionMode(StrEnum):
    """How a routing decision was made (Issue #3496).

    This enum classifies the decision path taken by the router:
    - FAST_PATH: Deterministic rules applied (no LLM needed)
    - SLOW_PATH: LLM made the routing decision
    - LLM_FALLBACK: LLM was attempted but failed, fell back to deterministic
    - CI_FAILURE_FAST_PATH: CI failure triggered immediate fixer routing
    - OUTER_FALLBACK: Router exception, fell back to decision_node logic
    """

    FAST_PATH = "fast_path"
    SLOW_PATH = "slow_path"
    LLM_FALLBACK = "llm_fallback"
    CI_FAILURE_FAST_PATH = "ci_failure_fast_path"
    OUTER_FALLBACK = "outer_fallback"


class RoutingCandidate(BaseModel):
    """Candidate node definition for LLM selection.

    Each candidate represents a possible next step in the workflow.
    The description field is shown to the LLM to help it make decisions.
    """

    node_name: str = Field(
        description="Internal node identifier (e.g., 'publisher', 'fixer', 'finalizer')"
    )
    description: str = Field(
        description="Human-readable description for LLM (e.g., 'Deploy changes to GitHub')"
    )

    @field_validator("node_name")
    @classmethod
    def node_name_not_empty(cls, v: str) -> str:
        """Ensure node_name is not empty."""
        if not v or not v.strip():
            raise ValueError("node_name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Ensure description is not empty."""
        if not v or not v.strip():
            raise ValueError("description cannot be empty")
        return v.strip()

    class Config:
        """Pydantic model configuration."""
        frozen = True


class RoutingDecision(BaseModel):
    """LLM routing decision result.

    This is the structured output from the Router LLM.
    The reasoning field forces the LLM to explain its choice for debugging.
    """

    next_node: str = Field(
        description="Selected node identifier (must be in candidates list)"
    )
    reasoning: str = Field(
        description="LLM's explanation for choosing this node (for debugging)"
    )
    risk_assessment: str = Field(
        description="Lightweight risk assessment of this routing decision"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score (0.0 to 1.0)"
    )
    requires_hitl_approval: bool = Field(
        default=False,
        description="Whether this decision requires Human-in-the-Loop approval. "
                    "Set to True for blocked/unknown verdicts or high-risk decisions."
    )

    @field_validator("next_node")
    @classmethod
    def next_node_not_empty(cls, v: str) -> str:
        """Ensure next_node is not empty."""
        if not v or not v.strip():
            raise ValueError("next_node cannot be empty")
        return v.strip()

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, v: str) -> str:
        """Ensure reasoning is not empty."""
        if not v or not v.strip():
            raise ValueError("reasoning cannot be empty")
        return v.strip()

    @field_validator("risk_assessment")
    @classmethod
    def risk_assessment_not_empty(cls, v: str) -> str:
        """Ensure risk_assessment is not empty."""
        if not v or not v.strip():
            raise ValueError("risk_assessment cannot be empty")
        return v.strip()

    class Config:
        """Pydantic model configuration."""
        frozen = True


@dataclass(frozen=True)
class RoutingResult:
    """Wrapper for routing decision with metadata (Issue #3496).

    This is internal plumbing that combines the LLM decision with
    system-level metadata about how the decision was made.
    Unlike RoutingDecision (LLM contract), this is not shown to the LLM.
    """

    decision: RoutingDecision
    decision_mode: DecisionMode
    fallback_reason: Optional[str] = None


class RoutingContext(BaseModel):
    """Router context - minimal summary fields for routing decisions.

    This is the input to the Router LLM. It contains just enough context
    for the LLM to make a routing decision without overwhelming it.
    """

    task_type: str = Field(
        description="Type of task (e.g., 'code_review', 'bug_fix', 'feature')"
    )
    current_stage: str = Field(
        description="Current workflow stage (e.g., 'planning', 'coding', 'review')"
    )
    step_history: List[str] = Field(
        default_factory=list,
        description="History of nodes visited (e.g., ['planner', 'coder', 'reviewer'])"
    )
    last_agent_feedback: str = Field(
        default="",
        description="Feedback from the last agent (e.g., 'Variable naming issues found')"
    )
    candidates: List[RoutingCandidate] = Field(
        description="List of candidate nodes to choose from"
    )

    # Optional context from ReviewOutcome (EPIC B-6 integration)
    review_verdict: Optional[str] = Field(
        default=None,
        description="Review verdict from ReviewOutcome (approve/request_changes/comment/blocked/unknown)"
    )
    review_severity: Optional[str] = Field(
        default=None,
        description="Review severity from ReviewOutcome (low/medium/high/critical)"
    )
    blocker_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of blocking issues from ReviewOutcome"
    )

    @field_validator("task_type")
    @classmethod
    def task_type_not_empty(cls, v: str) -> str:
        """Ensure task_type is not empty."""
        if not v or not v.strip():
            raise ValueError("task_type cannot be empty")
        return v.strip()

    @field_validator("current_stage")
    @classmethod
    def current_stage_not_empty(cls, v: str) -> str:
        """Ensure current_stage is not empty."""
        if not v or not v.strip():
            raise ValueError("current_stage cannot be empty")
        return v.strip()

    @field_validator("candidates")
    @classmethod
    def candidates_not_empty(cls, v: List[RoutingCandidate]) -> List[RoutingCandidate]:
        """Ensure candidates list is not empty."""
        if not v:
            raise ValueError("candidates list cannot be empty")
        return v

    def get_candidate_names(self) -> List[str]:
        """Get list of valid candidate node names."""
        return [c.node_name for c in self.candidates]

    def is_valid_next_node(self, node_name: str) -> bool:
        """Check if a node name is in the candidates list."""
        return node_name in self.get_candidate_names()

    class Config:
        """Pydantic model configuration."""
        frozen = True


class InvalidNextNodeError(Exception):
    """Raised when next_node is not in the candidates list."""

    def __init__(self, next_node: str, valid_nodes: List[str]):
        self.next_node = next_node
        self.valid_nodes = valid_nodes
        super().__init__(
            f"Invalid next_node '{next_node}'. "
            f"Must be one of: {valid_nodes}"
        )


def validate_decision(
    decision: RoutingDecision,
    context: RoutingContext
) -> None:
    """Validate that a routing decision is valid for the given context.

    Args:
        decision: The routing decision to validate
        context: The routing context with valid candidates

    Raises:
        InvalidNextNodeError: If next_node is not in candidates
    """
    if not context.is_valid_next_node(decision.next_node):
        raise InvalidNextNodeError(
            next_node=decision.next_node,
            valid_nodes=context.get_candidate_names()
        )
