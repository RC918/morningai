"""
Agent Registry Models
Issue #760 - Agent Registry & Task Router
Feature Flag: MVP_AGENT_REGISTRY
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Type of agent as defined in Blueprint Section 3.3 (Agent Catalog V2).

    Blueprint Reference: Section 3.3 - 13 Agent Types
    Issue: #4118 (EPIC K P0: AgentType Enum Extension)
    Sync: Aligned with orchestrator/governance/principal_context.py::AgentType

    Note: This enum is used for API models (Pydantic) and must stay in sync with:
    - agent_registry_db.py::AgentTypeDB (SQLAlchemy/Database model)
    - migration 045_extend_agenttypedb_enum.sql (PostgreSQL enum)

    Categories (13 Blueprint types + legacy types + unknown):
    - Core Engineering Agents (5): Planner, Coding, Reviewer, Test, Debugger
    - UX/UI Agents (4): UI Consistency, UX Heuristic, Visual Regression, Design Token
    - Governance/Reasoning Agents (4): Judge, Debate Left, Debate Right, Risk Analyzer
    - Legacy/Compatibility (6): dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent, unknown
    """
    # === Core Engineering Agents (Blueprint 3.3) ===
    PLANNER = "planner"
    CODING = "coding"
    REVIEWER = "reviewer"
    TEST = "test"
    DEBUGGER = "debugger"

    # === UX/UI Agents (Blueprint 3.3) ===
    UI_CONSISTENCY = "ui_consistency"
    UX_HEURISTIC = "ux_heuristic"
    VISUAL_REGRESSION = "visual_regression"
    DESIGN_TOKEN_GOVERNANCE = "design_token_governance"

    # === Governance/Reasoning Agents (Blueprint 3.3) ===
    JUDGE = "judge"
    DEBATE_LEFT = "debate_left"
    DEBATE_RIGHT = "debate_right"
    RISK_ANALYZER = "risk_analyzer"

    # === Legacy Agent Types (backward compatibility) ===
    DEV_AGENT = "dev_agent"
    OPS_AGENT = "ops_agent"
    PM_AGENT = "pm_agent"
    GROWTH_STRATEGIST = "growth_strategist"
    META_AGENT = "meta_agent"
    UNKNOWN = "unknown"  # Default for backward compatibility


class AgentStatus(str, Enum):
    """Current status of the agent"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class PermissionLevel(str, Enum):
    """Permission level based on reputation score"""
    SANDBOX_ONLY = "sandbox_only"
    STAGING_ACCESS = "staging_access"
    PROD_LOW_RISK = "prod_low_risk"
    PROD_FULL_ACCESS = "prod_full_access"


class TaskStatus(str, Enum):
    """Current status of the task"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatistics(BaseModel):
    """Agent performance statistics"""
    pr_merged_count: int = Field(default=0, ge=0)
    pr_reverted_count: int = Field(default=0, ge=0)
    test_pass_count: int = Field(default=0, ge=0)
    test_fail_count: int = Field(default=0, ge=0)
    test_pass_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class Agent(BaseModel):
    """Agent model matching OpenAPI spec"""
    agent_id: str = Field(..., description="Unique agent identifier (UUID)")
    agent_type: AgentType
    status: AgentStatus
    permission_level: PermissionLevel
    reputation_score: int = Field(..., ge=0, le=999, description="Agent reputation score (0-999)")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional agent metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    statistics: Optional[AgentStatistics] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentRegistrationRequest(BaseModel):
    """Request model for agent registration"""
    agent_type: AgentType
    capabilities: List[str] = Field(..., min_length=1, description="List of agent capabilities")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Validate capabilities list is not empty"""
        if not v:
            raise ValueError('capabilities cannot be empty')
        return v


class AgentUpdateRequest(BaseModel):
    """Request model for agent updates"""
    status: Optional[AgentStatus] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentHealthMetrics(BaseModel):
    """Agent health metrics"""
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_usage: Optional[float] = Field(None, ge=0.0, le=100.0)
    active_tasks: Optional[int] = Field(None, ge=0)
    queue_depth: Optional[int] = Field(None, ge=0)


class AgentHealthError(BaseModel):
    """Agent health error record"""
    timestamp: datetime
    error_type: str
    message: str


class AgentHealth(BaseModel):
    """Agent health status"""
    agent_id: str
    status: AgentStatus
    last_heartbeat: datetime
    metrics: Optional[AgentHealthMetrics] = None
    errors: List[AgentHealthError] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentHealthReport(BaseModel):
    """Health report from agent (heartbeat)"""
    status: AgentStatus
    metrics: Optional[AgentHealthMetrics] = None


class Task(BaseModel):
    """Task model matching OpenAPI spec"""
    task_id: str = Field(..., description="Unique task identifier (UUID)")
    status: TaskStatus
    agent_id: Optional[str] = Field(None, description="Assigned agent UUID")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID")
    task_type: str = Field(..., description="Type of task (e.g., 'faq', 'bug_fix', 'deployment')")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskCreationRequest(BaseModel):
    """Request model for task creation"""
    task_type: str = Field(..., description="Type of task")
    payload: Dict[str, Any] = Field(..., description="Task payload")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID (optional, auto-resolved from JWT)")

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        """Validate task type is not empty"""
        if not v or not v.strip():
            raise ValueError('task_type cannot be empty')
        return v.strip()


class TaskUpdateRequest(BaseModel):
    """Request model for task updates"""
    status: Optional[TaskStatus] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class Pagination(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class AgentListResponse(BaseModel):
    """Response model for agent list"""
    agents: List[Agent]
    pagination: Pagination


class TaskListResponse(BaseModel):
    """Response model for task list"""
    tasks: List[Task]
    pagination: Pagination
