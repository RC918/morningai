# Phase 2 Step B Technical Design: Code Generation Integration

**Status**: Draft  
**Version**: 1.0.0  
**Date**: 2025-11-27  
**Author**: Devin AI  

---

## Executive Summary

Phase 2 Step B enables actual code generation execution in ProjectEngineerAgent by integrating the existing CodeGenerationWorkflow. This builds on Phase 2 Step A's analysis-only infrastructure and activates automated code generation for safe tasks.

**Key Changes**:
- Enable code generation mode in ProjectEngineerAgent
- Integrate CodeGenerationWorkflow for safe task execution
- Add execution monitoring and error handling
- Maintain conservative safety-first approach

**Scope**:
- ✅ Enable code generation for 2 safe task types (documentation_update, test_generation)
- ✅ Integrate existing CodeGenerationWorkflow
- ✅ Add comprehensive error handling and rollback
- ✅ Add execution metrics and monitoring
- ⚠️ TaskClassifier expansion deferred (current 2 types sufficient for MVP)

---

## Table of Contents

1. [Background](#background)
2. [Architecture](#architecture)
3. [Implementation Plan](#implementation-plan)
4. [API Design](#api-design)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Plan](#deployment-plan)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Risk Assessment](#risk-assessment)
9. [Future Work](#future-work)

---

## 1. Background

### Phase 2 Step A Achievements

Phase 2 Step A (PR #1660) delivered:
- ProjectEngineerAgent with task decomposition
- Safe Tasks whitelist (9 types, frozenset immutable)
- PR Review CLI tool
- Analysis-only mode (no code execution)

### Current State

**Components Available**:
1. **ProjectEngineerAgent** - Devin-like meta-agent (analysis mode)
2. **CodeGenerationWorkflow** - Complete LangGraph workflow (8 stages)
3. **TaskClassifier** - Produces 6 task types (2 match Safe Tasks)
4. **Safe Tasks** - 9 types whitelisted (2 currently reachable)

**Gap**: ProjectEngineerAgent cannot execute code generation (mode: analysis_only)

### Phase 2 Step B Goals

**Primary Goal**: Enable code generation execution for safe tasks

**Success Criteria**:
- ProjectEngineerAgent can execute code generation for safe tasks
- CodeGenerationWorkflow integrated and functional
- All safety checks pass before code execution
- Comprehensive error handling and rollback
- Execution metrics collected

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ProjectEngineerAgent                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Task Decomposition (LLMPlannerAdapter)             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. Task Classification (TaskClassifier)               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. Safety Check (Safe Tasks Whitelist)                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. Code Generation Execution ⭐ NEW                    │ │
│  │    - Integrate CodeGenerationWorkflow                  │ │
│  │    - Execute for safe tasks only                       │ │
│  │    - Monitor and log execution                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CodeGenerationWorkflow (LangGraph)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Classify │→ │ Analyze  │→ │ Generate │→ │ Validate │   │
│  │   Task   │  │ Context  │  │   Code   │  │ Security │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Apply   │→ │ Generate │→ │   Run    │→ │  Create  │   │
│  │   Code   │  │  Tests   │  │  Tests   │  │    PR    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Integration

**ProjectEngineerAgent Changes**:
```python
class ProjectEngineerAgent:
    def __init__(self, enable_code_generation: bool = False):
        # Existing: planner, classifier, is_safe_task
        
        # NEW: CodeGenerationWorkflow integration
        if enable_code_generation:
            self.workflow = CodeGenerationWorkflow(dev_agent)
            self.mode = "execution"
        else:
            self.workflow = None
            self.mode = "analysis_only"
    
    def _process_step(self, step_text, step_index, trace_id):
        # Existing: classify, safety check
        
        # NEW: Execute code generation for safe tasks
        if self.mode == "execution" and is_safe:
            result = await self._execute_code_generation(
                step_text, task_type, trace_id
            )
            return result
        else:
            # Return analysis-only result (existing behavior)
            return TaskResult(status="skipped", ...)
    
    async def _execute_code_generation(self, step_text, task_type, trace_id):
        """NEW: Execute code generation using CodeGenerationWorkflow"""
        # 1. Prepare state
        # 2. Execute workflow
        # 3. Handle errors and rollback
        # 4. Return structured result
```

### 2.3 Data Flow

**Execution Flow** (Safe Task):
```
User Input: "Add unit tests for utils.py"
    │
    ▼
ProjectEngineerAgent.run_task()
    │
    ├─→ LLMPlannerAdapter.generate_plan()
    │   └─→ ["Add unit tests for utils.py"]
    │
    ├─→ TaskClassifier.classify()
    │   └─→ TaskType.TEST_GENERATION
    │
    ├─→ is_safe_task("test_generation")
    │   └─→ True ✅
    │
    └─→ _execute_code_generation()  ⭐ NEW
        │
        └─→ CodeGenerationWorkflow.execute()
            ├─→ classify_task()
            ├─→ analyze_context()
            ├─→ generate_code()
            ├─→ validate_security()
            ├─→ apply_code()
            ├─→ generate_tests()
            ├─→ run_tests()
            └─→ create_pr()
                │
                └─→ TaskResult(
                    status="success",
                    pr_number=1234,
                    pr_url="https://..."
                )
```

**Execution Flow** (Unsafe Task):
```
User Input: "Refactor entire codebase"
    │
    ▼
ProjectEngineerAgent.run_task()
    │
    ├─→ TaskClassifier.classify()
    │   └─→ TaskType.UNKNOWN
    │
    ├─→ is_safe_task("unknown")
    │   └─→ False ❌
    │
    └─→ TaskResult(
        status="skipped",
        details="Task not in safe whitelist"
    )
```

---

## 3. Implementation Plan

### 3.1 Phase 2 Step B Milestones

**Milestone 1: Core Integration** (2-3 hours)
- [ ] Add `enable_code_generation` parameter to ProjectEngineerAgent
- [ ] Integrate CodeGenerationWorkflow initialization
- [ ] Implement `_execute_code_generation()` method
- [ ] Add error handling and rollback logic

**Milestone 2: Testing** (1-2 hours)
- [ ] Add unit tests for code generation mode
- [ ] Add integration tests with CodeGenerationWorkflow
- [ ] Test error handling and rollback
- [ ] Test safe vs unsafe task execution

**Milestone 3: Monitoring** (1 hour)
- [ ] Add execution metrics
- [ ] Add logging for code generation events
- [ ] Add performance tracking

**Milestone 4: Documentation & PR** (1 hour)
- [ ] Update technical design document
- [ ] Create PR with comprehensive description
- [ ] Wait for CI to pass

**Total Estimated Time**: 5-7 hours

### 3.2 Implementation Steps

#### Step 1: Modify ProjectEngineerAgent.__init__()

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/agent.py`

**Changes**:
```python
def __init__(self, enable_code_generation: bool = False, dev_agent=None):
    """
    Initialize ProjectEngineerAgent with dependencies
    
    Args:
        enable_code_generation: Enable code generation execution (default: False)
        dev_agent: DevAgent instance for CodeGenerationWorkflow (required if enable_code_generation=True)
    """
    # Existing initialization...
    
    # NEW: CodeGenerationWorkflow integration
    self.enable_code_generation = enable_code_generation
    self.workflow = None
    
    if enable_code_generation:
        if not dev_agent:
            raise ValueError("dev_agent required when enable_code_generation=True")
        
        try:
            from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow
            self.workflow = CodeGenerationWorkflow(dev_agent)
            logger.info("[ProjectEngineerAgent] CodeGenerationWorkflow initialized")
        except ImportError as e:
            logger.error(f"[ProjectEngineerAgent] Failed to import CodeGenerationWorkflow: {e}")
            raise
    
    self.mode = "execution" if enable_code_generation else "analysis_only"
    logger.info(f"[ProjectEngineerAgent] Mode: {self.mode}")
```

#### Step 2: Implement _execute_code_generation()

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/agent.py`

**New Method**:
```python
async def _execute_code_generation(
    self,
    step_text: str,
    task_type: str,
    task_id: str,
    trace_id: str
) -> TaskResult:
    """
    Execute code generation using CodeGenerationWorkflow
    
    Args:
        step_text: Task description
        task_type: Classified task type
        task_id: Unique task ID
        trace_id: Trace ID for logging
    
    Returns:
        TaskResult with execution details
    """
    logger.info(f"[ProjectEngineerAgent] Executing code generation for task {task_id}")
    
    try:
        # Prepare state for CodeGenerationWorkflow
        state = {
            "task_id": hash(task_id),  # Convert to int
            "task_title": step_text[:100],
            "task_description": step_text,
            "task_type": task_type,
            "task_metadata": None,
            "target_files": [],
            "generated_code": None,
            "generated_tests": None,
            "code_diff": None,
            "test_results": None,
            "pr_number": None,
            "pr_url": None,
            "error": None,
            "execution_start": time.time(),
            "file_backups": {},
            "security_validated": False,
        }
        
        # Execute workflow
        result_state = await self.workflow.execute(state)
        
        # Extract results
        if result_state.get("error"):
            return TaskResult(
                task_id=task_id,
                task_type=task_type,
                status="failed",
                is_safe=True,
                details=f"Code generation failed: {result_state['error']}",
                error=result_state["error"]
            )
        
        # Success
        return TaskResult(
            task_id=task_id,
            task_type=task_type,
            status="success",
            is_safe=True,
            details=f"Code generation completed successfully. PR created.",
            pr_number=result_state.get("pr_number"),
            pr_url=result_state.get("pr_url")
        )
    
    except Exception as e:
        logger.error(
            f"[ProjectEngineerAgent] Code generation failed for task {task_id}: {e}",
            exc_info=True
        )
        
        return TaskResult(
            task_id=task_id,
            task_type=task_type,
            status="failed",
            is_safe=True,
            details=f"Code generation execution failed: {str(e)}",
            error=str(e)
        )
```

#### Step 3: Modify _process_step()

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/agent.py`

**Changes**:
```python
def _process_step(self, step_text: str, step_index: int, trace_id: str) -> TaskResult:
    """Process a single step from the plan"""
    task_id = f"{trace_id}-step-{step_index}"
    
    try:
        # Existing: classify task type
        task_type = ...
        
        # Existing: check if task is safe
        is_safe = self.is_safe_task(task_type)
        
        # NEW: Execute code generation if enabled and safe
        if self.enable_code_generation and is_safe:
            logger.info(f"[ProjectEngineerAgent] Executing code generation for step {step_index}")
            return await self._execute_code_generation(
                step_text=step_text,
                task_type=task_type,
                task_id=task_id,
                trace_id=trace_id
            )
        
        # Existing: Return analysis-only result
        if is_safe:
            status = "skipped"
            details = (
                f"Task classified as '{task_type}' (safe for code generation). "
                f"Code generation disabled (mode: {self.mode}). "
                f"Set enable_code_generation=True to execute."
            )
        else:
            status = "skipped"
            details = (
                f"Task classified as '{task_type}' (not in safe whitelist). "
                f"This task requires manual review."
            )
        
        return TaskResult(
            task_id=task_id,
            task_type=task_type,
            status=status,
            is_safe=is_safe,
            details=details
        )
    
    except Exception as e:
        # Existing error handling...
```

#### Step 4: Update get_status()

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/agent.py`

**Changes**:
```python
def get_status(self) -> dict:
    """Get agent status and configuration"""
    return {
        "agent_type": "ProjectEngineerAgent",
        "version": "1.0.0-phase2-step-b",  # Updated version
        "planner_available": self.planner is not None,
        "classifier_available": self.classifier is not None,
        "workflow_available": self.workflow is not None,  # NEW
        "mode": self.mode,  # "execution" or "analysis_only"
        "features": {
            "task_decomposition": self.planner is not None,
            "task_classification": self.classifier is not None,
            "safe_task_gating": True,
            "code_generation": self.enable_code_generation,  # Updated
        }
    }
```

---

## 4. API Design

### 4.1 ProjectEngineerAgent API

#### Constructor

```python
ProjectEngineerAgent(
    enable_code_generation: bool = False,
    dev_agent: Optional[DevAgent] = None
)
```

**Parameters**:
- `enable_code_generation`: Enable code generation execution (default: False for safety)
- `dev_agent`: DevAgent instance required for CodeGenerationWorkflow (required if enable_code_generation=True)

**Example**:
```python
# Analysis-only mode (Phase 2 Step A behavior)
agent = ProjectEngineerAgent()

# Execution mode (Phase 2 Step B)
from agents.dev_agent import DevAgent
dev_agent = DevAgent()
agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=dev_agent)
```

#### run_task()

```python
async def run_task(
    description: str,
    repo: str = "morningai/morningai"
) -> List[TaskResult]
```

**No changes to signature** - behavior changes based on `enable_code_generation` flag.

**Returns**:
- Analysis mode: `TaskResult` with `status="skipped"`
- Execution mode: `TaskResult` with `status="success"/"failed"` and PR details

#### get_status()

```python
def get_status() -> dict
```

**Returns**:
```python
{
    "agent_type": "ProjectEngineerAgent",
    "version": "1.0.0-phase2-step-b",
    "planner_available": bool,
    "classifier_available": bool,
    "workflow_available": bool,  # NEW
    "mode": "execution" | "analysis_only",
    "features": {
        "task_decomposition": bool,
        "task_classification": bool,
        "safe_task_gating": bool,
        "code_generation": bool
    }
}
```

### 4.2 TaskResult Structure

**No changes** - existing structure supports both analysis and execution modes:

```python
@dataclass
class TaskResult:
    task_id: str
    task_type: str
    status: str  # "success", "failed", "skipped"
    is_safe: bool
    details: str
    pr_number: Optional[int] = None  # Populated in execution mode
    pr_url: Optional[str] = None      # Populated in execution mode
    error: Optional[str] = None
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/tests/test_agent.py`

**New Tests** (15 existing + 12 new = 27 total):

```python
class TestProjectEngineerAgentCodeGeneration:
    """Test code generation mode"""
    
    def test_init_with_code_generation_disabled(self):
        """Test initialization with code generation disabled (default)"""
        agent = ProjectEngineerAgent()
        assert agent.enable_code_generation is False
        assert agent.mode == "analysis_only"
        assert agent.workflow is None
    
    def test_init_with_code_generation_enabled_no_dev_agent(self):
        """Test initialization fails without dev_agent"""
        with pytest.raises(ValueError, match="dev_agent required"):
            ProjectEngineerAgent(enable_code_generation=True)
    
    def test_init_with_code_generation_enabled(self):
        """Test initialization with code generation enabled"""
        mock_dev_agent = MagicMock()
        
        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )
            
            assert agent.enable_code_generation is True
            assert agent.mode == "execution"
            assert agent.workflow is not None
    
    async def test_execute_code_generation_success(self):
        """Test successful code generation execution"""
        mock_dev_agent = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.execute = AsyncMock(return_value={
            "error": None,
            "pr_number": 1234,
            "pr_url": "https://github.com/test/repo/pull/1234"
        })
        
        agent = ProjectEngineerAgent.__new__(ProjectEngineerAgent)
        agent.workflow = mock_workflow
        agent.enable_code_generation = True
        
        result = await agent._execute_code_generation(
            step_text="Add unit tests",
            task_type="test_generation",
            task_id="test-123",
            trace_id="trace-456"
        )
        
        assert result.status == "success"
        assert result.pr_number == 1234
        assert result.pr_url == "https://github.com/test/repo/pull/1234"
    
    async def test_execute_code_generation_failure(self):
        """Test code generation execution failure"""
        mock_workflow = MagicMock()
        mock_workflow.execute = AsyncMock(return_value={
            "error": "Security validation failed"
        })
        
        agent = ProjectEngineerAgent.__new__(ProjectEngineerAgent)
        agent.workflow = mock_workflow
        agent.enable_code_generation = True
        
        result = await agent._execute_code_generation(
            step_text="Add unit tests",
            task_type="test_generation",
            task_id="test-123",
            trace_id="trace-456"
        )
        
        assert result.status == "failed"
        assert result.error == "Security validation failed"
    
    async def test_process_step_execution_mode_safe_task(self):
        """Test step processing in execution mode with safe task"""
        # Test that safe tasks are executed in execution mode
        pass
    
    async def test_process_step_execution_mode_unsafe_task(self):
        """Test step processing in execution mode with unsafe task"""
        # Test that unsafe tasks are skipped even in execution mode
        pass
    
    async def test_process_step_analysis_mode_safe_task(self):
        """Test step processing in analysis mode with safe task"""
        # Test that safe tasks are skipped in analysis mode
        pass
    
    def test_get_status_execution_mode(self):
        """Test get_status() in execution mode"""
        mock_dev_agent = MagicMock()
        
        with patch('agents.dev_agent.workflows.code_generation_workflow.CodeGenerationWorkflow'):
            agent = ProjectEngineerAgent(
                enable_code_generation=True,
                dev_agent=mock_dev_agent
            )
            
            status = agent.get_status()
            
            assert status["mode"] == "execution"
            assert status["workflow_available"] is True
            assert status["features"]["code_generation"] is True
    
    def test_get_status_analysis_mode(self):
        """Test get_status() in analysis mode"""
        agent = ProjectEngineerAgent()
        
        status = agent.get_status()
        
        assert status["mode"] == "analysis_only"
        assert status["workflow_available"] is False
        assert status["features"]["code_generation"] is False
    
    async def test_run_task_execution_mode_integration(self):
        """Integration test: run_task() in execution mode"""
        # End-to-end test with mocked CodeGenerationWorkflow
        pass
```

### 5.2 Integration Tests

**File**: `handoff/20250928/40_App/orchestrator/project_engineer/tests/test_agent_integration.py` (NEW)

```python
class TestProjectEngineerAgentIntegration:
    """Integration tests with CodeGenerationWorkflow"""
    
    async def test_documentation_update_end_to_end(self):
        """Test documentation update task end-to-end"""
        # Test with real CodeGenerationWorkflow (mocked LLM)
        pass
    
    async def test_test_generation_end_to_end(self):
        """Test test generation task end-to-end"""
        # Test with real CodeGenerationWorkflow (mocked LLM)
        pass
    
    async def test_unsafe_task_rejected(self):
        """Test that unsafe tasks are rejected"""
        pass
    
    async def test_error_handling_and_rollback(self):
        """Test error handling and file rollback"""
        pass
```

### 5.3 Test Coverage Goals

- **Unit Tests**: 90%+ coverage for new code
- **Integration Tests**: Cover all safe task types
- **Error Handling**: Test all failure modes
- **Rollback**: Verify file restoration on errors

---

## 6. Deployment Plan

### 6.1 Feature Flag

**Environment Variable**: `ENABLE_PROJECT_ENGINEER_CODEGEN`

**Configuration**:
```yaml
# config/env.schema.yaml
ENABLE_PROJECT_ENGINEER_CODEGEN:
  type: boolean
  default: false
  description: "Enable code generation execution in ProjectEngineerAgent (Phase 2 Step B)"
```

**Usage**:
```python
from common.config.settings import settings

enable_codegen = settings.get("ENABLE_PROJECT_ENGINEER_CODEGEN", False)
agent = ProjectEngineerAgent(
    enable_code_generation=enable_codegen,
    dev_agent=dev_agent if enable_codegen else None
)
```

### 6.2 Rollout Strategy

**Phase 1: Development** (Week 1)
- Deploy to development environment
- Feature flag OFF by default
- Manual testing with safe tasks

**Phase 2: Staging** (Week 2)
- Deploy to staging environment
- Feature flag ON for internal testing
- Monitor execution metrics

**Phase 3: Canary** (Week 3)
- Deploy to production
- Feature flag ON for 5% of users
- Monitor error rates and success metrics

**Phase 4: Full Rollout** (Week 4)
- Gradually increase to 100%
- Monitor continuously

### 6.3 Rollback Plan

**Immediate Rollback**:
- Set `ENABLE_PROJECT_ENGINEER_CODEGEN=false`
- Agent reverts to analysis-only mode
- No code changes required

**Criteria for Rollback**:
- Error rate > 10%
- Security violations detected
- Performance degradation > 50%

---

## 7. Monitoring & Metrics

### 7.1 Execution Metrics

**Metrics to Track**:
```python
# Execution metrics
project_engineer_codegen_executions_total
project_engineer_codegen_successes_total
project_engineer_codegen_failures_total
project_engineer_codegen_duration_seconds

# Task type breakdown
project_engineer_codegen_by_task_type{task_type="test_generation"}
project_engineer_codegen_by_task_type{task_type="documentation_update"}

# Safety metrics
project_engineer_safe_tasks_executed_total
project_engineer_unsafe_tasks_rejected_total

# Error metrics
project_engineer_codegen_errors_by_type{error_type="security_validation"}
project_engineer_codegen_errors_by_type{error_type="workflow_execution"}
```

### 7.2 Logging

**Log Levels**:
- `INFO`: Execution start/end, task classification, safety checks
- `WARNING`: Unsafe tasks rejected, workflow errors
- `ERROR`: Execution failures, security violations

**Log Format**:
```python
logger.info(
    "[ProjectEngineerAgent] Code generation executed",
    extra={
        "task_id": task_id,
        "task_type": task_type,
        "is_safe": is_safe,
        "status": status,
        "duration_ms": duration_ms,
        "pr_number": pr_number
    }
)
```

### 7.3 Alerts

**Critical Alerts**:
- Security validation failures > 5 in 5 minutes
- Error rate > 10% for 10 minutes
- Workflow execution timeout > 5 minutes

**Warning Alerts**:
- Unsafe task rejection rate > 50%
- PR creation failures > 3 in 10 minutes

---

## 8. Risk Assessment

### 8.1 Risks & Mitigation

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Security bypass | Critical | Low | Multi-layer validation (Safe Tasks + CodeGenWorkflow security) |
| Code corruption | High | Low | Atomic writes, file backups, rollback on error |
| Workflow timeout | Medium | Medium | Timeout limits, async execution, monitoring |
| LLM hallucination | Medium | Medium | Code review required, test generation, PR process |
| Resource exhaustion | Medium | Low | Rate limiting, execution quotas |
| Integration bugs | Low | Medium | Comprehensive testing, gradual rollout |

### 8.2 Safety Measures

**Multi-Layer Safety**:
1. **Safe Tasks Whitelist** - Only 2 task types allowed initially
2. **CodeGenerationWorkflow Security** - 15 dangerous patterns blocked
3. **File Path Validation** - Repo root boundary enforcement
4. **Code Size Limits** - Max 50,000 characters
5. **Atomic Writes** - Temp file + os.replace()
6. **File Backups** - Automatic backup before modification
7. **Rollback on Error** - Restore original files on failure

### 8.3 Failure Modes

**Failure Mode 1: Security Validation Fails**
- **Impact**: Code generation aborted
- **Recovery**: Return error TaskResult, no files modified
- **User Impact**: Task marked as failed, manual review required

**Failure Mode 2: Workflow Execution Timeout**
- **Impact**: Partial code generation
- **Recovery**: Rollback files, return error TaskResult
- **User Impact**: Task marked as failed, retry possible

**Failure Mode 3: PR Creation Fails**
- **Impact**: Code generated but not committed
- **Recovery**: Code remains in working directory
- **User Impact**: Manual PR creation required

---

## 9. Future Work

### 9.1 Phase 2 Step C (Future)

**TaskClassifier Expansion**:
- Add 7 new task types to match Safe Tasks whitelist
- Improve classification accuracy with real-world data
- Add complexity scoring

**Safe Tasks Expansion**:
- Add `fix_lint`, `fix_typo`, `update_readme`
- Add `env_sync`, `config_update`, `i18n_update`
- Expand to 15-20 task types

### 9.2 Phase 3 (Future)

**Multi-Agent Coordination**:
- Parallel task execution
- Agent-to-agent communication
- Distributed workflow orchestration

**Advanced Features**:
- Interactive code review
- Incremental code generation
- Context-aware suggestions

---

## Appendix A: Code Examples

### Example 1: Analysis-Only Mode (Phase 2 Step A)

```python
from project_engineer.agent import ProjectEngineerAgent

# Initialize in analysis mode (default)
agent = ProjectEngineerAgent()

# Run task
results = agent.run_task("Add unit tests for utils.py")

# Result
for result in results:
    print(f"Task: {result.task_type}")
    print(f"Status: {result.status}")  # "skipped"
    print(f"Details: {result.details}")
    # Output: "Task classified as 'test_generation' (safe for code generation).
    #          Code generation disabled (mode: analysis_only).
    #          Set enable_code_generation=True to execute."
```

### Example 2: Execution Mode (Phase 2 Step B)

```python
from project_engineer.agent import ProjectEngineerAgent
from agents.dev_agent import DevAgent

# Initialize DevAgent
dev_agent = DevAgent()

# Initialize in execution mode
agent = ProjectEngineerAgent(
    enable_code_generation=True,
    dev_agent=dev_agent
)

# Run task
results = await agent.run_task("Add unit tests for utils.py")

# Result
for result in results:
    print(f"Task: {result.task_type}")
    print(f"Status: {result.status}")  # "success"
    print(f"PR: {result.pr_url}")
    # Output: "Task classified as 'test_generation' (safe for code generation).
    #          Code generation completed successfully. PR created.
    #          PR: https://github.com/RC918/morningai/pull/1234"
```

### Example 3: Unsafe Task Rejection

```python
# Both modes reject unsafe tasks
agent = ProjectEngineerAgent(enable_code_generation=True, dev_agent=dev_agent)

results = await agent.run_task("Refactor entire codebase")

# Result
for result in results:
    print(f"Task: {result.task_type}")  # "unknown"
    print(f"Status: {result.status}")  # "skipped"
    print(f"Is Safe: {result.is_safe}")  # False
    # Output: "Task classified as 'unknown' (not in safe whitelist).
    #          This task requires manual review."
```

---

## Appendix B: Testing Checklist

### Pre-Merge Checklist

- [ ] All unit tests pass (27/27)
- [ ] All integration tests pass
- [ ] Lint checks pass (flake8)
- [ ] Type checks pass (mypy)
- [ ] Code coverage > 90%
- [ ] Security review completed
- [ ] Documentation updated
- [ ] PR description comprehensive
- [ ] CI/CD pipeline passes (38/38 checks)

### Post-Merge Checklist

- [ ] Deploy to development environment
- [ ] Manual testing with safe tasks
- [ ] Monitor execution metrics
- [ ] Verify rollback functionality
- [ ] Update Phase 2 roadmap

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-27 | Devin AI | Initial draft |

---

**End of Document**
