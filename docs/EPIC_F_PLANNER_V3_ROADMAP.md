# EPIC F: Planner v3 Roadmap

**Issue**: [#3490](https://github.com/RC918/morningai/issues/3490)  
**Blueprint Reference**: Section 3.1 (Planner v3 - Intelligent Planner)  
**Status**: Phase F-3 Completed (Pilot Ready)  
**Last Updated**: 2026-01-12

## Executive Summary

EPIC F transforms MorningAI's planning infrastructure from "task decomposition" to "dynamic resource scheduling". This roadmap integrates evidence-based analysis of existing components with strategic vision for hierarchical planning and resource-aware execution.

## Architecture Vision

### From "Task Decomposition" to "Dynamic Resource Scheduling"

| Layer | Current Component | Integrated Role | North Star Extension |
|-------|-------------------|-----------------|----------------------|
| LLM Planning | LLMPlannerAdapter | Plan generation | Hierarchical Planning |
| Template Planning | TaskPlanner | Dependencies + templates | DAG + Parallelization |
| Goal Decomposition | PMAgent | Confidence scoring | Resource-Aware Planning |
| Simulation | (New) | Risk/cost estimation | Plan Oracle |

### Existing Components Analysis

| Component | File | Lines | Current Coverage |
|-----------|------|-------|------------------|
| LLMPlannerAdapter | `llm_planner_adapter.py` | 624 | LLM-powered plan generation |
| TaskPlanner | `meta_agent/task_planner.py` | 561 | Template-based + linear dependencies |
| PMAgent | `pm_agent/agent.py` | 788 | Goal decomposition + confidence scoring |

**Important Note**: Three separate planning mechanisms exist with inconsistent output formats. Flow Controller v3 consumption pattern needs clarification.

## Implementation Status Summary

| Phase | Description | Status | Implementation / PR |
|-------|-------------|--------|---------------------|
| F-0 | Planner Output Contract + Schema | **Completed** | `planner_types.py` |
| F-1 | Single Entrypoint + Adapter | **Completed** | `adapters.py` |
| F-2 | DAG + Parallelization | **Completed** | [#3854](https://github.com/RC918/morningai/pull/3854) |
| F-3 | Flow Integration | **Completed** | [#3856](https://github.com/RC918/morningai/pull/3856), [#3864](https://github.com/RC918/morningai/pull/3864), [#3868](https://github.com/RC918/morningai/pull/3868) |
| F-4 | Agent Assignment + Flow Template | Planning | (原 F-3) |
| F-5 | Self-refinement Loop | Planning | (原 F-4) |
| F-6 | Model Tier Selection + Hooks | Planning | (原 F-5) |

**Note**: Phase F-3 was restructured to prioritize Flow Integration (FlowController v3 端到端整合) over Agent Assignment. This enables staging pilot testing with feature flags.

---

## Phase Breakdown

### Phase F-0: Planner Output Contract + Hierarchical Schema ✓ COMPLETED

**Objective**: Define unified Planner output schema as the "API specification" for Planner v3, with support for hierarchical planning.

**Implementation**: `handoff/20250928/40_App/orchestrator/core/planner/planner_types.py`

**Deliverables**:

1. **Unified Planner Output Schema** (JSON Schema):

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "PlannerOutput",
  "type": "object",
  "required": ["plan_id", "plan_type", "task_tree", "created_at"],
  "properties": {
    "plan_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this plan"
    },
    "plan_type": {
      "type": "string",
      "enum": ["milestone", "detailed"],
      "description": "Hierarchical planning support: milestone (high-level) or detailed (full subtasks)"
    },
    "goal": {
      "type": "string",
      "description": "Original goal/request that triggered planning"
    },
    "task_tree": {
      "type": "object",
      "description": "DAG representation of tasks",
      "properties": {
        "nodes": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/TaskNode"
          }
        },
        "edges": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/TaskEdge"
          }
        }
      }
    },
    "flow_template": {
      "type": "string",
      "description": "Selected flow template (e.g., 'review_heavy', 'code_only', 'full_pipeline')"
    },
    "model_tier_hints": {
      "type": "object",
      "properties": {
        "default_tier": {
          "type": "string",
          "enum": ["tier_0", "tier_1", "tier_2", "tier_3"]
        },
        "per_task_overrides": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "risk_metadata": {
      "type": "object",
      "properties": {
        "overall_risk": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"]
        },
        "requires_approval": {
          "type": "boolean"
        },
        "trust_score_input": {
          "type": "number",
          "description": "Hook for E+F+I closed loop"
        },
        "risk_factors": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "cost_estimate": {
      "type": "object",
      "description": "Hook for Plan Oracle",
      "properties": {
        "estimated_tokens": { "type": "integer" },
        "estimated_usd": { "type": "number" },
        "provider_breakdown": {
          "type": "object",
          "additionalProperties": { "type": "number" }
        }
      }
    },
    "provider_health_input": {
      "type": "object",
      "description": "Hook for resource-aware planning",
      "properties": {
        "snapshot_time": { "type": "string", "format": "date-time" },
        "provider_status": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "health_score": { "type": "number" },
              "rate_limit_remaining": { "type": "integer" },
              "latency_p99_ms": { "type": "number" }
            }
          }
        }
      }
    },
    "planner_metadata": {
      "type": "object",
      "properties": {
        "planner_type": { "type": "string" },
        "planning_time_ms": { "type": "number" },
        "confidence_score": { "type": "number" },
        "trace_id": { "type": "string" }
      }
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Creation timestamp in UTC with millisecond precision (ISO 8601)"
    }
  },
  "definitions": {
    "TaskNode": {
      "type": "object",
      "required": ["task_id", "task_type", "description"],
      "properties": {
        "task_id": { "type": "string" },
        "task_type": {
          "type": "string",
          "enum": ["setup", "analyze", "code", "test", "review", "document", "deploy", "verify", "cleanup"]
        },
        "description": { "type": "string" },
        "agent_assignment": {
          "type": "string",
          "description": "Assigned agent type (e.g., 'dev_agent', 'reviewer_agent', 'ops_agent')"
        },
        "estimated_duration_minutes": { "type": "integer" },
        "priority": { "type": "integer" },
        "risk_level": {
          "type": "string",
          "enum": ["low", "medium", "high"]
        },
        "requires_approval": { "type": "boolean" },
        "expandable": {
          "type": "boolean",
          "description": "For hierarchical planning: can this milestone be expanded into subtasks?"
        },
        "inputs": { "type": "object" },
        "outputs": { "type": "object" }
      }
    },
    "TaskEdge": {
      "type": "object",
      "required": ["from", "to", "type"],
      "properties": {
        "from": { "type": "string", "description": "Source task_id" },
        "to": { "type": "string", "description": "Target task_id" },
        "type": {
          "type": "string",
          "enum": ["depends_on", "parallel_with", "optional_after"]
        }
      }
    }
  }
}
```

2. **Flow Controller v3 Consumption Interface**:

```python
class PlanConsumer(Protocol):
    """Protocol for consuming Planner v3 output"""
    
    def execute_plan(self, plan: PlannerOutput) -> ExecutionResult:
        """Execute a plan, respecting DAG dependencies"""
        ...
    
    def get_next_executable_tasks(self, plan: PlannerOutput, completed: Set[str]) -> List[TaskNode]:
        """Get tasks ready for execution (all dependencies met)"""
        ...
    
    def can_parallelize(self, tasks: List[TaskNode]) -> bool:
        """Check if tasks can be executed in parallel"""
        ...
```

3. **Planner Events Schema** (for telemetry):

```json
{
  "title": "PlannerEvent",
  "type": "object",
  "required": ["event_id", "event_type", "plan_id", "timestamp"],
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_type": {
      "type": "string",
      "enum": ["plan_created", "plan_executed", "plan_failed", "plan_replanned", "task_completed", "task_failed"]
    },
    "plan_id": { "type": "string" },
    "task_id": { "type": "string" },
    "timestamp": { 
      "type": "string", 
      "format": "date-time",
      "description": "Timestamp in UTC with millisecond precision (ISO 8601)"
    },
    "metadata": { "type": "object" }
  }
}
```

**Acceptance Criteria**:
- [ ] PlannerOutput schema defined and documented
- [ ] TaskNode and TaskEdge schemas support DAG representation
- [ ] Flow Controller consumption interface defined
- [ ] Planner events schema defined
- [ ] Hierarchical planning fields (plan_type, expandable) included

**North Star Hook**: `plan_type: "milestone"` and `expandable: true` enable future Hierarchical Planning.

---

### Phase F-1: Single Entrypoint + Adapter Consolidation ✓ COMPLETED

**Objective**: Create unified Planner facade wrapping existing three planners with consistent output.

**Implementation**: `handoff/20250928/40_App/orchestrator/core/planner/adapters.py`

**Deliverables**:

1. **Planner Facade**:

```python
class PlannerV3:
    """
    Unified Planner v3 facade wrapping existing planners.
    
    Supports:
    - LLM-powered planning (via LLMPlannerAdapter)
    - Template-based planning (via TaskPlanner)
    - Goal decomposition (via PMAgent)
    
    All outputs conform to PlannerOutput schema.
    """
    
    def __init__(
        self,
        llm_planner: Optional[LLMPlannerAdapter] = None,
        task_planner: Optional[TaskPlanner] = None,
        pm_agent: Optional[PMAgent] = None
    ):
        self.llm_planner = llm_planner or LLMPlannerAdapter()
        self.task_planner = task_planner or TaskPlanner()
        self.pm_agent = pm_agent or PMAgent()
    
    def create_plan(
        self,
        goal: str,
        repo: str,
        trace_id: str,
        plan_type: str = "detailed",  # "milestone" or "detailed"
        context: Optional[Dict[str, Any]] = None
    ) -> PlannerOutput:
        """
        Create a plan using the best available planner.
        
        Fallback chain: LLM → Template → Static
        """
        ...
    
    def expand_milestone(
        self,
        plan: PlannerOutput,
        milestone_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PlannerOutput:
        """
        Expand a milestone into detailed subtasks (hierarchical planning).
        """
        ...
```

2. **Adapter Layer** (for each existing planner):

```python
class LLMPlannerOutputAdapter:
    """Adapts LLMPlannerAdapter output to PlannerOutput schema"""
    
    def adapt(self, llm_result: Dict[str, Any], goal: str, trace_id: str) -> PlannerOutput:
        # Convert flat plan steps to task_tree with linear edges
        ...

class TaskPlannerOutputAdapter:
    """Adapts TaskPlanner output to PlannerOutput schema"""
    
    def adapt(self, task_plan: TaskPlan) -> PlannerOutput:
        # Convert SubTask list to task_tree with dependency edges
        ...

class PMAgentOutputAdapter:
    """Adapts PMAgent output to PlannerOutput schema"""
    
    def adapt(self, advisory: PMAdvisory) -> PlannerOutput:
        # Convert sub_tasks to task_tree
        ...
```

3. **Fallback Logic**:
   - Try LLM planner first (if available and enabled)
   - Fall back to template planner on LLM failure
   - Fall back to static plan on template failure
   - Log fallback events for monitoring

**Acceptance Criteria**:
- [ ] PlannerV3 facade implemented
- [ ] All three adapters produce valid PlannerOutput
- [ ] Fallback chain works correctly
- [ ] Schema validation on all outputs
- [ ] Milestone mode supported (even if expansion is stub)

**North Star Hook**: `expand_milestone()` method enables future Meta-Planner / Agent-Level Planner separation.

---

### Phase F-2: DAG + Parallelization ✓ COMPLETED

**Objective**: Upgrade from linear dependencies to true DAG with parallel execution support.

**Implementation**: 
- `handoff/20250928/40_App/orchestrator/core/planner/dag_builder.py`
- `handoff/20250928/40_App/orchestrator/core/planner/parallel_executor.py`
- PR: [#3854](https://github.com/RC918/morningai/pull/3854)

**Deliverables**:

1. **DAG Builder**:

```python
class DAGBuilder:
    """Builds task DAG from various inputs"""
    
    def from_linear(self, tasks: List[TaskNode]) -> TaskTree:
        """Convert linear task list to DAG (sequential edges)"""
        ...
    
    def from_dependencies(self, tasks: List[TaskNode], deps: Dict[str, List[str]]) -> TaskTree:
        """Build DAG from explicit dependencies"""
        ...
    
    def infer_parallelism(self, tree: TaskTree) -> TaskTree:
        """Analyze tasks and add parallel_with edges where safe"""
        ...
    
    def validate(self, tree: TaskTree) -> ValidationResult:
        """Check for cycles, missing nodes, etc."""
        ...
```

2. **Parallel Execution Support**:

```python
class ParallelExecutor:
    """Executes DAG tasks with parallelism"""
    
    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel
    
    def get_executable_batch(
        self,
        tree: TaskTree,
        completed: Set[str],
        in_progress: Set[str]
    ) -> List[TaskNode]:
        """Get batch of tasks that can run in parallel"""
        ...
    
    def execute_batch(
        self,
        tasks: List[TaskNode],
        executor: TaskExecutor
    ) -> List[TaskResult]:
        """Execute tasks in parallel (up to max_parallel)"""
        ...
```

3. **TaskPlanner Upgrade**:
   - Modify `_setup_dependencies()` to support non-linear dependencies
   - Add `parallel_safe` flag to SubTaskType
   - Generate `parallel_with` edges for safe task types

4. **Cycle Detection**:
   - Topological sort validation
   - Clear error messages for invalid DAGs

**Acceptance Criteria**:
- [ ] DAGBuilder creates valid DAGs from various inputs
- [ ] Cycle detection works correctly
- [ ] ParallelExecutor respects dependencies
- [ ] Limited parallelism (max 3 concurrent tasks)
- [ ] Integration tests for parallel execution

**North Star Hook**: DAG structure enables complex branching logic for future advanced planning.

---

### Phase F-3: Flow Integration ✓ COMPLETED

**Objective**: Integrate FlowController v3 with LangGraph orchestrator for end-to-end workflow execution with feature flag support for pilot rollout.

**Implementation**:
- F-3a: `handoff/20250928/40_App/orchestrator/core/planner/agent_task_executor.py` - PR: [#3856](https://github.com/RC918/morningai/pull/3856)
- F-3b: `handoff/20250928/40_App/orchestrator/core/planner/flow_integration.py` - PR: [#3864](https://github.com/RC918/morningai/pull/3864)
- F-3c: Feature Flag + Node integration - PR: [#3868](https://github.com/RC918/morningai/pull/3868)

**Note**: This phase was prioritized over the original F-3 (Agent Assignment) to enable staging pilot testing with feature flags.

**Deliverables**:

1. **AgentTaskExecutor (F-3a)**:
   - Bridges FlowController with individual task execution
   - Handles task state management and error handling
   - Provides execution context for flow nodes

2. **Flow Integration Module (F-3b)**:
   - `flow_integration.py` bridges FlowController with LangGraph's AgentState
   - Converts PlannerOutput to FlowController-compatible format
   - Handles state synchronization between systems

3. **Feature Flags + Node Integration (F-3c)**:

```python
import os
import hashlib

# Feature flags for pilot rollout
ENABLE_FLOW_CONTROLLER_V3 = os.getenv("ENABLE_FLOW_CONTROLLER_V3", "false").lower() == "true"
FLOW_CONTROLLER_SAMPLE_RATE = int(os.getenv("FLOW_CONTROLLER_SAMPLE_RATE", "0"))

# Deterministic bucketing using SHA-256
def should_use_flow_controller(trace_id: str) -> bool:
    if ENABLE_FLOW_CONTROLLER_V3:
        return True
    if FLOW_CONTROLLER_SAMPLE_RATE > 0:
        hash_value = int(hashlib.sha256(trace_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < FLOW_CONTROLLER_SAMPLE_RATE
    return False
```

4. **New AgentState Fields**:
   - `FLOW_EXECUTION_RESULT`: Result from FlowController execution
   - `FLOW_EXECUTION_STATUS`: Status of flow execution
   - `FLOW_COMPLETED_TASKS`: List of completed task IDs
   - `FLOW_FAILED_TASKS`: List of failed task IDs

5. **Conditional Routing**:
   - `flow_executor_node`: Executes plans via FlowController
   - `should_proceed_after_policy_with_flow_controller()`: Routes to FlowController or legacy path

**Pilot Testing**:
```bash
# Route all workflows to FlowController
ENABLE_FLOW_CONTROLLER_V3=true

# Route 10% of workflows (deterministic by trace_id)
FLOW_CONTROLLER_SAMPLE_RATE=10
```

**Acceptance Criteria**:
- [x] AgentTaskExecutor implemented
- [x] Flow integration module bridges FlowController with LangGraph
- [x] Feature flags for pilot rollout
- [x] Deterministic bucketing for canary gating
- [x] New AgentState fields for flow execution tracking
- [x] Conditional routing in orchestrator graph

**North Star Hook**: Feature flag infrastructure enables safe pilot rollout and A/B testing of FlowController v3.

---

### Phase F-4: Agent Assignment + Flow Template Selection (原 F-3)

**Objective**: Implement intelligent agent assignment and explicit flow template selection.

**Deliverables**:

1. **Agent Assignment Rules**:

```python
class AgentAssigner:
    """Assigns agents to tasks based on type and risk"""
    
    ASSIGNMENT_RULES = {
        "analyze": "dev_agent",
        "code": "coder_agent",  # or "senior_coder" for high-risk
        "test": "tester_agent",
        "review": "reviewer_agent",
        "deploy": "ops_agent",
        "document": "dev_agent",
    }
    
    def assign(self, task: TaskNode, context: AssignmentContext) -> str:
        """
        Assign agent based on:
        - Task type
        - Risk level
        - Trust score (from EPIC E)
        - Available agents
        """
        base_agent = self.ASSIGNMENT_RULES.get(task.task_type, "dev_agent")
        
        # Upgrade to senior for high-risk tasks
        if task.risk_level == "high" and base_agent == "coder_agent":
            return "senior_coder"
        
        return base_agent
```

2. **Flow Template Selection**:

```python
class FlowTemplateSelector:
    """Selects appropriate flow template based on plan characteristics"""
    
    TEMPLATES = {
        "code_only": ["analyze", "code", "test"],
        "review_heavy": ["analyze", "code", "review", "test", "review"],
        "full_pipeline": ["analyze", "code", "test", "review", "document", "deploy"],
        "hotfix": ["analyze", "code", "test"],
    }
    
    def select(self, plan: PlannerOutput, context: SelectionContext) -> str:
        """
        Select template based on:
        - Task types in plan
        - Risk level
        - Time constraints
        - User preferences
        """
        if plan.risk_metadata.overall_risk in ["high", "critical"]:
            return "review_heavy"
        
        if context.is_hotfix:
            return "hotfix"
        
        return "full_pipeline"
```

3. **EPIC E Integration**:
   - Read risk_metadata from Safety Governor decisions
   - High-risk plans automatically get `requires_approval: true`
   - Trust score influences agent assignment

**Acceptance Criteria**:
- [ ] Agent assignment rules implemented
- [ ] Flow template selection implemented
- [ ] High-risk tasks assigned to senior agents
- [ ] EPIC E risk_metadata consumed
- [ ] Flow template appears in PlannerOutput

**North Star Hook**: `trust_score_input` field enables E+F+I closed loop when EPIC I matures.

---

### Phase F-5: Self-refinement Loop (原 F-4)

**Objective**: Implement plan → execute → feedback → replan closed loop.

**Deliverables**:

1. **Feedback Collector**:

```python
@dataclass
class ExecutionFeedback:
    """Feedback from task execution"""
    task_id: str
    status: str  # "success", "failed", "partial"
    error_message: Optional[str]
    actual_duration_minutes: int
    outputs: Dict[str, Any]
    failure_context: Optional[str]  # From failure learning

class FeedbackCollector:
    """Collects and aggregates execution feedback"""
    
    def collect(self, task_id: str, result: TaskResult) -> ExecutionFeedback:
        ...
    
    def aggregate(self, feedbacks: List[ExecutionFeedback]) -> PlanFeedback:
        ...
```

2. **Replanner**:

```python
class Replanner:
    """Replans based on execution feedback"""
    
    def __init__(self, planner: PlannerV3):
        self.planner = planner
    
    def should_replan(self, plan: PlannerOutput, feedback: PlanFeedback) -> bool:
        """Determine if replanning is needed"""
        return feedback.has_failures and feedback.recoverable
    
    def replan_partial(
        self,
        plan: PlannerOutput,
        failed_task_id: str,
        feedback: ExecutionFeedback
    ) -> PlannerOutput:
        """Replan only the failed subtask and its dependents"""
        ...
    
    def replan_full(
        self,
        plan: PlannerOutput,
        feedback: PlanFeedback
    ) -> PlannerOutput:
        """Full replan with failure context"""
        ...
```

3. **Failure Learning Integration**:
   - Use existing `_get_learning_context()` from TaskPlanner
   - Include failure context in replan inputs
   - Track replan events for analysis

4. **Replan Limits**:
   - Max 3 replans per task
   - Max 2 full replans per plan
   - Escalate to HITL after limits exceeded

**Acceptance Criteria**:
- [ ] Feedback collection implemented
- [ ] Partial replan (single task) works
- [ ] Full replan with failure context works
- [ ] Replan limits enforced
- [ ] Failure learning context integrated

**North Star Hook**: Feedback structure enables Trust Score adjustment when EPIC I matures.

---

### Phase F-6: Model Tier Selection + Decision Hooks (原 F-5)

**Objective**: Implement rule-based model tier selection and prepare hooks for advanced features.

**Deliverables**:

1. **Model Tier Selector**:

```python
class ModelTierSelector:
    """Selects model tier based on task characteristics"""
    
    TIER_RULES = {
        "tier_0": {  # Most capable, highest cost
            "risk_levels": ["critical"],
            "task_types": ["deploy", "security_review"],
            "complexity": "high"
        },
        "tier_1": {  # High capability
            "risk_levels": ["high"],
            "task_types": ["code", "review"],
            "complexity": "medium"
        },
        "tier_2": {  # Standard
            "risk_levels": ["medium", "low"],
            "task_types": ["analyze", "test", "document"],
            "complexity": "low"
        },
        "tier_3": {  # Fast, low cost
            "risk_levels": ["low"],
            "task_types": ["cleanup", "format"],
            "complexity": "simple"
        }
    }
    
    def select_tier(self, task: TaskNode, context: TierContext) -> str:
        """Select tier based on rules"""
        ...
    
    def get_plan_tiers(self, plan: PlannerOutput) -> Dict[str, str]:
        """Get tier assignments for all tasks in plan"""
        ...
```

2. **Decision Hooks Interface**:

```python
class PlannerHook(Protocol):
    """Protocol for pluggable planner hooks"""
    
    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        """Called after plan creation, can modify plan"""
        ...
    
    def on_task_assigned(self, task: TaskNode, agent: str) -> Tuple[TaskNode, str]:
        """Called after agent assignment, can override"""
        ...

class DebateHook(PlannerHook):
    """Hook for Debate Engine v2 integration (future)"""
    
    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        # Placeholder: will invoke debate for high-risk plans
        return plan

class MemoryHook(PlannerHook):
    """Hook for Memory v2 integration (future)"""
    
    def on_plan_created(self, plan: PlannerOutput) -> PlannerOutput:
        # Placeholder: will enrich with historical context
        return plan
```

3. **Plan Oracle Interface** (stub for future):

```python
class PlanOracle(Protocol):
    """Protocol for pre-execution simulation (future)"""
    
    def simulate(self, plan: PlannerOutput) -> SimulationResult:
        """Simulate plan execution and estimate outcomes"""
        ...

@dataclass
class SimulationResult:
    estimated_cost_usd: float
    estimated_duration_minutes: int
    risk_assessment: str
    requires_approval: bool
    warnings: List[str]
```

4. **Resource-Aware Input Interface** (stub for future):

```python
class ProviderHealthProvider(Protocol):
    """Protocol for provider health data (from EPIC I)"""
    
    def get_health_snapshot(self) -> ProviderHealthSnapshot:
        """Get current provider health status"""
        ...

@dataclass
class ProviderHealthSnapshot:
    timestamp: datetime
    providers: Dict[str, ProviderStatus]

@dataclass
class ProviderStatus:
    health_score: float  # 0.0 to 1.0
    rate_limit_remaining: int
    latency_p99_ms: float
    recommended_tier: Optional[str]
```

**Acceptance Criteria**:
- [ ] Model tier selection rules implemented
- [ ] Tier assignments appear in PlannerOutput
- [ ] Hook interface defined
- [ ] Debate hook stub implemented
- [ ] Memory hook stub implemented
- [ ] Plan Oracle interface defined (stub)
- [ ] Provider health interface defined (stub)

**Future Extensions**:
- Plan Oracle (pre-execution simulation)
- Resource-Aware Planning (provider health input)
- Debate Engine v2 integration
- Memory v2 integration

---

## MVP Scope Guardrail (Non-Goals)

The following are explicitly OUT OF SCOPE for MVP:

- Full Hierarchical Planning (Meta-Planner + Agent-Level Planner autonomous operation)
- Plan Oracle (pre-execution simulation with cost/risk evaluation)
- Resource-Aware Planning (real-time provider health/rate limit consumption)
- Debate Engine v2 (multi-agent deliberation)
- Memory v2 complete integration (depends on EPIC G)

These will be tracked as follow-up issues after MVP completion.

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| EPIC C (Flow Controller v3) | Consumer | **Completed** | F-3 integrates with FlowController |
| EPIC D (Autonomous Coder) | Integration | **Completed** | AgentTaskExecutor bridges to Coder |
| EPIC E (Safety Governor v2) | Risk Metadata | In Planning | Required for F-4 Agent Assignment |
| EPIC G (Memory v2) | Future Integration | Placeholder | Memory hook in F-6 |
| EPIC I (Governance Layer) | Future Integration | Placeholder | Trust score input in F-6 |
| LLMPlannerAdapter | Existing | Available | Used in F-1 |
| TaskPlanner | Existing | Available | Used in F-1 |
| PMAgent | Existing | Available | Used in F-1 |
| LangGraph Orchestrator | Integration | **Completed** | F-3c integrates feature flags |

---

## Cross-EPIC Integration Points

### E + F + I Closed Loop

```
Detection (E) → Recording (I) → Adjustment (F)
```

**Integration Schema Fields**:
- `PlannerOutput.risk_metadata.trust_score_input` - Input from EPIC I
- `PlannerOutput.risk_metadata.requires_approval` - Influenced by EPIC E decisions
- `TaskNode.risk_level` - Consumed by EPIC E for enforcement

This closed loop will be fully activated when EPIC I reaches maturity.

### F → E Integration

When Planner creates a plan:
1. Risk metadata is computed based on task types and complexity
2. High-risk plans are flagged with `requires_approval: true`
3. EPIC E Safety Governor can block or require approval for high-risk plans

### F ← E Integration

When Safety Governor makes decisions:
1. Trust score adjustments are recorded
2. Planner consumes trust score for future plans
3. Low trust score → more conservative planning (higher tiers, more reviews)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Schema Compliance | 100% | All outputs pass validation |
| Fallback Rate | <10% | LLM planner success rate |
| DAG Validity | 100% | No cycles, all deps resolved |
| Parallel Efficiency | >30% | Tasks run in parallel vs sequential |
| Replan Success Rate | >70% | Successful recovery from failures |
| Planning Latency P99 | <2s | Metrics dashboard |

---

## Timeline Estimate

| Phase | Description | Estimated Duration | Dependencies | Status |
|-------|-------------|-------------------|--------------|--------|
| F-0 | Planner Output Contract + Schema | 1-2 days | None | **Completed** |
| F-1 | Single Entrypoint + Adapter | 3-5 days | F-0 | **Completed** |
| F-2 | DAG + Parallelization | 5-7 days | F-1 | **Completed** (PR #3854) |
| F-3 | Flow Integration | 3-5 days | F-2, EPIC C | **Completed** (PRs #3856, #3864, #3868) |
| F-4 | Agent Assignment + Flow Template | 3-5 days | F-3, EPIC E (partial) | Planning |
| F-5 | Self-refinement Loop | 5-7 days | F-3 | Planning |
| F-6 | Model Tier Selection + Hooks | 3-5 days | F-4, F-5 | Planning |

**Completed Duration**: ~2-3 weeks (F-0 through F-3)
**Remaining Duration**: ~2-3 weeks (F-4 through F-6)
**Total Estimated Duration**: 4-6 weeks

---

## References

- [Blueprint Section 3.1: Planner v3](../north_star/MorningAI_Ecosystem_Blueprint_2025_Final.md)
- [Wish Pool v2: EPIC F](../north_star/ECOSYSTEM_WISHPOOL_V2.md)
- [LLMPlannerAdapter](../../handoff/20250928/40_App/orchestrator/llm_planner_adapter.py)
- [TaskPlanner](../../handoff/20250928/40_App/orchestrator/meta_agent/task_planner.py)
- [PMAgent](../../handoff/20250928/40_App/orchestrator/pm_agent/agent.py)
- [EPIC E Roadmap](./EPIC_E_SAFETY_GOVERNOR_V2_ROADMAP.md)
