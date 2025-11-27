#!/usr/bin/env python3
"""
Project Engineer Agent - Devin-like Meta-Agent
Phase 2 Step B Implementation

Features:
- Task decomposition using LLM Planner
- Safe task classification
- Code generation execution for safe tasks
- Structured result reporting
- Integration with existing orchestrator components
"""
import logging
import uuid
import time
from typing import List, Optional
from dataclasses import dataclass

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

    Phase 2 Step B Scope:
    - Code generation execution for safe tasks ✅
    - Integration with CodeGenerationWorkflow ✅
    - PR creation and monitoring ✅
    """

    def __init__(self, enable_code_generation: bool = False, dev_agent=None):
        """
        Initialize ProjectEngineerAgent with dependencies

        Args:
            enable_code_generation: Enable code generation execution (default: False)
            dev_agent: DevAgent instance for CodeGenerationWorkflow (required if enable_code_generation=True)

        Dependencies:
        - LLMPlannerAdapter: For task decomposition
        - TaskClassifier: For task type identification
        - SafeTasks: For safe task validation
        - CodeGenerationWorkflow: For code generation execution (if enabled)
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
        logger.info(f"[ProjectEngineerAgent] Initialized successfully (mode: {self.mode})")

    async def run_task(self, description: str, repo: str = "morningai/morningai") -> List[TaskResult]:
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

                result = await self._process_step(
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

    async def _process_step(self, step_text: str, step_index: int, trace_id: str) -> TaskResult:
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

            # Step 5: Execute code generation if enabled and safe
            if self.enable_code_generation and is_safe:
                logger.info(f"[ProjectEngineerAgent] Executing code generation for step {step_index}")
                return await self._execute_code_generation(
                    step_text=step_text,
                    task_type=task_type,
                    task_id=task_id,
                    trace_id=trace_id
                )

            # Return analysis-only result
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
                    f"This task requires manual review and cannot be automated."
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
                "task_id": hash(task_id) & 0x7FFFFFFF,  # Convert to positive int
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
            logger.info("[ProjectEngineerAgent] Starting CodeGenerationWorkflow execution")
            result_state = await self.workflow.execute(state)

            # Extract results
            if result_state.get("error"):
                logger.error(f"[ProjectEngineerAgent] Code generation failed: {result_state['error']}")
                return TaskResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="failed",
                    is_safe=True,
                    details=f"Code generation failed: {result_state['error']}",
                    error=result_state["error"]
                )

            # Success
            logger.info(
                f"[ProjectEngineerAgent] Code generation completed successfully. "
                f"PR: {result_state.get('pr_url', 'N/A')}"
            )
            return TaskResult(
                task_id=task_id,
                task_type=task_type,
                status="success",
                is_safe=True,
                details="Code generation completed successfully. PR created.",
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

    def get_status(self) -> dict:
        """
        Get agent status and configuration

        Returns:
            Dict with agent status information
        """
        return {
            "agent_type": "ProjectEngineerAgent",
            "version": "1.0.0-phase2-step-b",
            "planner_available": self.planner is not None,
            "classifier_available": self.classifier is not None,
            "workflow_available": self.workflow is not None,
            "mode": self.mode,
            "features": {
                "task_decomposition": self.planner is not None,
                "task_classification": self.classifier is not None,
                "safe_task_gating": True,
                "code_generation": self.enable_code_generation,
            }
        }


async def run_task(description: str, repo: str = "morningai/morningai") -> List[TaskResult]:
    """
    Convenience function to run a task using ProjectEngineerAgent

    Args:
        description: Natural language task description
        repo: Repository name

    Returns:
        List of TaskResult objects

    Example:
        >>> results = await run_task("更新 README.md")
        >>> print(f"Processed {len(results)} steps")
    """
    agent = ProjectEngineerAgent()
    return await agent.run_task(description, repo)
