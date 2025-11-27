#!/usr/bin/env python3
"""
Project Engineer Agent - Devin-like Meta-Agent
Phase 2 Step A Implementation

Features:
- Task decomposition using LLM Planner
- Safe task classification
- Structured result reporting
- Integration with existing orchestrator components
"""
import logging
import uuid
from typing import List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    task_type: str
    status: str  # "success", "failed", "skipped"
    is_safe: bool
    details: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None


class ProjectEngineerAgent:
    """
    Devin-like Meta-Agent that accepts natural language commands
    and orchestrates task execution.
    
    This agent serves as the entry point for human-friendly task execution,
    integrating with existing components:
    - LLMPlannerAdapter for task decomposition
    - TaskClassifier for task type identification
    - Safe Tasks whitelist for code generation gating
    - Orchestrator for actual execution (Phase 2 Step B)
    
    Phase 2 Step A Scope:
    - Task planning and decomposition ✅
    - Safe task classification ✅
    - Analysis-only mode (no code generation yet) ✅
    
    Phase 2 Step B Scope (future):
    - Code generation execution for safe tasks
    - Integration with CodeGenerationWorkflow
    - PR creation and monitoring
    """
    
    def __init__(self):
        """
        Initialize ProjectEngineerAgent with dependencies
        
        Dependencies:
        - LLMPlannerAdapter: For task decomposition
        - TaskClassifier: For task type identification
        - SafeTasks: For safe task validation
        """
        try:
            from llm_planner_adapter import LLMPlannerAdapter
            self.planner = LLMPlannerAdapter()
            logger.info("[ProjectEngineerAgent] LLMPlannerAdapter initialized")
        except ImportError as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to import LLMPlannerAdapter: {e}")
            self.planner = None
        
        try:
            from agents.dev_agent.workflows.task_classifier import TaskClassifier
            self.classifier = TaskClassifier()
            logger.info("[ProjectEngineerAgent] TaskClassifier initialized")
        except ImportError as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to import TaskClassifier: {e}")
            self.classifier = None
        
        from .safe_tasks import is_safe_task
        self.is_safe_task = is_safe_task
        
        logger.info("[ProjectEngineerAgent] Initialized successfully")
    
    def run_task(self, description: str, repo: str = "morningai/morningai") -> List[TaskResult]:
        """
        Execute a task based on natural language description
        
        Workflow:
        1. Validate input
        2. Use LLM Planner to decompose task into steps
        3. Classify each step's task type
        4. Check if task is safe for code generation
        5. Return structured results (analysis only in Phase 2 Step A)
        
        Args:
            description: Natural language task description
            repo: Repository name (default: morningai/morningai)
            
        Returns:
            List of TaskResult objects with execution details
            
        Raises:
            ValueError: If description is empty or invalid
            
        Example:
            >>> agent = ProjectEngineerAgent()
            >>> results = agent.run_task("更新 README.md 添加安裝說明")
            >>> for result in results:
            ...     print(f"{result.task_type}: {result.status}")
        """
        # Step 1: Validate input
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")
        
        logger.info(f"[ProjectEngineerAgent] Running task: {description[:100]}...")
        
        results = []
        
        try:
            # Step 2: Use LLM Planner to decompose task
            trace_id = str(uuid.uuid4())
            
            if self.planner:
                plan_result = self.planner.generate_plan(
                    goal=description,
                    repo=repo,
                    trace_id=trace_id
                )
                
                plan_steps = plan_result.get("plan", [])
                planner_type = plan_result.get("planner_type", "unknown")
                
                logger.info(
                    f"[ProjectEngineerAgent] Generated {len(plan_steps)} steps "
                    f"using {planner_type} planner"
                )
            else:
                # Fallback: treat entire description as single task
                plan_steps = [description]
                logger.warning("[ProjectEngineerAgent] No planner available, using single-step fallback")
            
            # Step 3-5: Process each step
            for i, step in enumerate(plan_steps):
                step_text = step if isinstance(step, str) else step.get("step", str(step))
                
                result = self._process_step(
                    step_text=step_text,
                    step_index=i,
                    trace_id=trace_id
                )
                results.append(result)
            
            logger.info(
                f"[ProjectEngineerAgent] Task completed: "
                f"{len(results)} steps processed"
            )
            
        except Exception as e:
            logger.error(f"[ProjectEngineerAgent] Task execution failed: {e}", exc_info=True)
            
            # Return error result
            results.append(TaskResult(
                task_id=str(uuid.uuid4()),
                task_type="unknown",
                status="failed",
                is_safe=False,
                details=f"Task execution failed: {str(e)}",
                error=str(e)
            ))
        
        return results
    
    def _process_step(self, step_text: str, step_index: int, trace_id: str) -> TaskResult:
        """
        Process a single step from the plan
        
        Args:
            step_text: Step description
            step_index: Index of step in plan
            trace_id: Trace ID for logging
            
        Returns:
            TaskResult for this step
        """
        task_id = f"{trace_id}-step-{step_index}"
        
        try:
            # Step 3: Classify task type
            if self.classifier:
                task_type_enum = self.classifier.classify(step_text)
                task_type = task_type_enum.value if hasattr(task_type_enum, 'value') else str(task_type_enum)
                
                metadata = self.classifier.get_task_metadata(task_type_enum)
                complexity = metadata.get("complexity", "unknown")
                
                logger.info(
                    f"[ProjectEngineerAgent] Step {step_index} classified as "
                    f"{task_type} (complexity: {complexity})"
                )
            else:
                task_type = "unknown"
                logger.warning(f"[ProjectEngineerAgent] No classifier available for step {step_index}")
            
            # Step 4: Check if task is safe
            is_safe = self.is_safe_task(task_type)
            
            logger.info(
                f"[ProjectEngineerAgent] Step {step_index} safety check: "
                f"is_safe={is_safe}, task_type={task_type}"
            )
            
            # Step 5: Return result (analysis only in Phase 2 Step A)
            if is_safe:
                status = "skipped"
                details = (
                    f"Task classified as '{task_type}' (safe for code generation). "
                    f"Code generation will be enabled in Phase 2 Step B. "
                    f"Current mode: analysis only."
                )
            else:
                status = "skipped"
                details = (
                    f"Task classified as '{task_type}' (not in safe whitelist). "
                    f"This task requires manual review and cannot be automated. "
                    f"Current mode: analysis only."
                )
            
            return TaskResult(
                task_id=task_id,
                task_type=task_type,
                status=status,
                is_safe=is_safe,
                details=details
            )
            
        except Exception as e:
            logger.error(
                f"[ProjectEngineerAgent] Failed to process step {step_index}: {e}",
                exc_info=True
            )
            
            return TaskResult(
                task_id=task_id,
                task_type="unknown",
                status="failed",
                is_safe=False,
                details=f"Step processing failed: {str(e)}",
                error=str(e)
            )
    
    def get_status(self) -> dict:
        """
        Get agent status and configuration
        
        Returns:
            Dict with agent status information
        """
        return {
            "agent_type": "ProjectEngineerAgent",
            "version": "1.0.0-phase2-step-a",
            "planner_available": self.planner is not None,
            "classifier_available": self.classifier is not None,
            "mode": "analysis_only",  # Will change to "execution" in Phase 2 Step B
            "features": {
                "task_decomposition": self.planner is not None,
                "task_classification": self.classifier is not None,
                "safe_task_gating": True,
                "code_generation": False,  # Will be True in Phase 2 Step B
            }
        }


def run_task(description: str, repo: str = "morningai/morningai") -> List[TaskResult]:
    """
    Convenience function to run a task using ProjectEngineerAgent
    
    Args:
        description: Natural language task description
        repo: Repository name
        
    Returns:
        List of TaskResult objects
        
    Example:
        >>> results = run_task("更新 README.md")
        >>> print(f"Processed {len(results)} steps")
    """
    agent = ProjectEngineerAgent()
    return agent.run_task(description, repo)
