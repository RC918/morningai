#!/usr/bin/env python3
"""
Project Engineer Agent - Devin-like Meta-Agent
Phase 2 Step B Implementation + Phase 3 PR-4 Enhancements

Features:
- Task decomposition using LLM Planner
- Safe task classification
- Code generation execution for safe tasks
- Structured result reporting
- Integration with existing orchestrator components
- Agent-level timeout (Phase 3 PR-4)
- Semantic task rules: repo/directory/task type restrictions (Phase 3 PR-4)
"""
import logging
import uuid
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

    def __init__(self, enable_code_generation: bool = None, dev_agent=None):
        """
        Initialize ProjectEngineerAgent with dependencies

        Args:
            enable_code_generation: Enable code generation execution
                                   If None, reads from ENABLE_PROJECT_ENGINEER_CODEGEN env var
                                   If False, forces analysis-only mode
                                   If True, enables execution mode (requires dev_agent)
            dev_agent: DevAgent instance for CodeGenerationWorkflow (required if enable_code_generation=True)

        Dependencies:
        - LLMPlannerAdapter: For task decomposition
        - TaskClassifier: For task type identification
        - SafeTasks: For safe task validation
        - CodeGenerationWorkflow: For code generation execution (if enabled)
        """
        # Phase 2 Step C: Read from feature flag if not explicitly set
        if enable_code_generation is None:
            try:
                from common.config.settings import settings
                enable_code_generation = settings.enable_project_engineer_codegen
                logger.info(
                    "[ProjectEngineerAgent] Using ENABLE_PROJECT_ENGINEER_CODEGEN=%s",
                    enable_code_generation,
                )
            except (ImportError, AttributeError) as e:
                # Expected non-fatal: settings module or field missing (e.g., partial deploy)
                logger.warning(
                    "[ProjectEngineerAgent] Failed to read feature flag from settings "
                    "(import/attribute error: %s), defaulting to False",
                    e,
                )
                enable_code_generation = False
            except Exception as e:
                # Unexpected error (e.g., ValidationError from misconfig): fail fast
                logger.exception(
                    "[ProjectEngineerAgent] Unexpected error while reading feature flag; "
                    "not falling back silently: %s",
                    e,
                )
                raise
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

    def _validate_repo_allowed(self, repo: str) -> tuple[bool, str]:
        """
        Validate if repository is in the allowed list (Phase 3 PR-4: Semantic task rules)

        Args:
            repo: Repository name (owner/repo format)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        try:
            from .semantic_rules import validate_repo
            is_valid, error = validate_repo(repo)
            if not is_valid:
                return False, error or f"Repository '{repo}' is not allowed"
            return True, ""
        except ImportError:
            # Fallback to original implementation
            try:
                from common.config.settings import settings
                allowed_repos_str = settings.project_engineer_allowed_repos
                allowed_repos = [r.strip() for r in allowed_repos_str.split(",") if r.strip()]

                if not allowed_repos:
                    return True, ""

                if repo in allowed_repos:
                    return True, ""

                return False, (
                    f"Repository '{repo}' is not in the allowed list. "
                    f"Allowed repositories: {', '.join(allowed_repos)}"
                )
            except (ImportError, AttributeError) as e:
                logger.warning(f"[ProjectEngineerAgent] Failed to read allowed repos from settings: {e}")
                if repo == "RC918/morningai":
                    return True, ""
                return False, f"Repository '{repo}' is not allowed (default: RC918/morningai only)"

    def _validate_directories_allowed(self, file_paths: list) -> tuple[bool, str]:
        """
        Validate if file paths are in allowed directories (Phase 4 PR-1: Semantic Rules v2)

        Args:
            file_paths: List of file paths to validate

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not file_paths:
            return True, ""

        try:
            from .semantic_rules import get_validator
            validator = get_validator()
            is_valid, violations = validator.validate_file_paths(file_paths)
            if not is_valid:
                error_messages = [v.message for v in violations]
                return False, "; ".join(error_messages)
            return True, ""
        except ImportError as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to import semantic_rules: {e}")
            # Fallback: allow all paths (less secure but maintains backward compatibility)
            return True, ""

    def _validate_task_type_allowed(self, task_type: str) -> tuple[bool, str]:
        """
        Validate if task type is allowed (Phase 4 PR-1: Semantic Rules v2)

        Args:
            task_type: Task type to validate

        Returns:
            Tuple of (is_allowed, error_message)
        """
        try:
            from .semantic_rules import validate_task_type
            is_valid, error = validate_task_type(task_type)
            if not is_valid:
                return False, error or f"Task type '{task_type}' is not allowed"
            return True, ""
        except ImportError as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to import semantic_rules: {e}")
            # Fallback to safe_tasks check
            return self.is_safe_task(task_type), f"Task type '{task_type}' is not in safe whitelist"

    def _get_task_timeout(self) -> int:
        """
        Get task timeout from settings (Phase 3 PR-4: Agent-level timeout)

        Returns:
            Timeout in seconds (default: 300)
        """
        try:
            from common.config.settings import settings
            return settings.project_engineer_task_timeout_seconds
        except (ImportError, AttributeError) as e:
            logger.warning(f"[ProjectEngineerAgent] Failed to read timeout from settings: {e}")
            return 300  # Default 5 minutes

    def _validate_task_semantic_rules(
        self,
        repo: str,
        task_type: str,
        action: str,
        file_paths: Optional[List[str]] = None,
        command: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> tuple[bool, str, bool]:
        """
        Validate task using comprehensive semantic rules (Phase 1 Security Foundation)

        This method uses get_validator() to get the full validator instance and calls
        its validate_task method to check:
        - Repository validation
        - Task type validation
        - Action whitelist validation
        - Sensitive file blocking
        - High-risk command detection
        - HITL approval requirements

        Args:
            repo: Repository name for validation
            task_type: Task type for validation
            action: Action being performed (e.g., "write_file", "run_command")
            file_paths: List of file paths involved in the action
            command: Command being executed (if applicable)
            trace_id: Trace ID for logging and metrics

        Returns:
            Tuple of (is_valid, error_message, requires_approval)
            - is_valid: True if task passes all validations (or only has approval-required violations)
            - error_message: Description of validation failure (empty if valid)
            - requires_approval: True if task requires HITL approval
        """
        try:
            from .semantic_rules import get_validator
            validator = get_validator()

            is_ok, violations = validator.validate_task(
                repo=repo,
                task_type=task_type,
                file_paths=file_paths,
                action=action,
                command=command,
            )

            if is_ok:
                return True, "", False

            # Process violations to determine error message and approval requirements
            error_messages = [v.message for v in violations]
            error_message = "; ".join(error_messages)

            # Check if any violation requires approval (HITL)
            requires_approval = any(
                getattr(v, 'requires_approval', False) for v in violations
            )

            # A task is "valid to proceed" if it only has violations that require approval
            # It's invalid if there are any hard-blocking violations
            has_hard_blocking = any(
                not getattr(v, 'requires_approval', False) for v in violations
            )
            is_valid_to_proceed = not has_hard_blocking

            if trace_id:
                logger.info(
                    f"[ProjectEngineerAgent] Semantic validation for {trace_id}: "
                    f"valid={is_valid_to_proceed}, requires_approval={requires_approval}, "
                    f"violations={len(violations)}"
                )

            return is_valid_to_proceed, error_message, requires_approval
        except ImportError as e:
            logger.warning(f"[ProjectEngineerAgent] semantic_rules not available: {e}")
            # Fallback: allow action but log warning
            return True, "", False
        except Exception as e:
            logger.error(f"[ProjectEngineerAgent] Semantic rules validation failed: {e}", exc_info=True)
            # Fail closed: reject task on validation error
            return False, f"Semantic rules validation error: {str(e)}", False

    async def run_task(self, description: str, repo: str = "RC918/morningai") -> List[TaskResult]:
        """
        Execute a task based on natural language description

        Workflow:
        1. Validate input and semantic rules (repo allowed)
        2. Use LLM Planner to decompose task into steps
        3. Classify each step's task type
        4. Check if task is safe for code generation
        5. Return structured results (analysis only in Phase 2 Step A)

        Phase 3 PR-4 Enhancements:
        - Agent-level timeout (configurable via PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS)
        - Semantic task rules: repo validation (configurable via PROJECT_ENGINEER_ALLOWED_REPOS)

        Args:
            description: Natural language task description
            repo: Repository name (default: RC918/morningai)

        Returns:
            List of TaskResult objects with execution details

        Raises:
            ValueError: If description is empty or invalid
            asyncio.TimeoutError: If task exceeds configured timeout

        Example:
            >>> agent = ProjectEngineerAgent()
            >>> results = agent.run_task("更新 README.md 添加安裝說明")
            >>> for result in results:
            ...     print(f"{result.task_type}: {result.status}")
        """
        # Step 1: Validate input
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")

        # Phase 3 PR-4: Validate repository is allowed
        repo_allowed, repo_error = self._validate_repo_allowed(repo)
        if not repo_allowed:
            logger.warning(f"[ProjectEngineerAgent] Repository validation failed: {repo_error}")
            return [TaskResult(
                task_id=str(uuid.uuid4()),
                task_type="validation_error",
                status="failed",
                is_safe=False,
                details=repo_error,
                error=repo_error
            )]

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
                    trace_id=trace_id,
                    repo=repo
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

    async def _process_step(
        self,
        step_text: str,
        step_index: int,
        trace_id: str,
        repo: str = "RC918/morningai"
    ) -> TaskResult:
        """
        Process a single step from the plan

        Args:
            step_text: Step description
            step_index: Index of step in plan
            trace_id: Trace ID for logging
            repo: Repository name for semantic rules validation

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

            # Step 4: Check if task is safe (Phase 4 PR-1: Use semantic rules validation)
            task_type_allowed, task_type_error = self._validate_task_type_allowed(task_type)
            is_safe = task_type_allowed

            logger.info(
                f"[ProjectEngineerAgent] Step {step_index} safety check: "
                f"is_safe={is_safe}, task_type={task_type}"
            )

            if not is_safe and task_type_error:
                logger.warning(
                    f"[ProjectEngineerAgent] Task type validation failed: {task_type_error}"
                )

            # Phase 1 Security Foundation: Comprehensive semantic rules validation
            # Maps task_type to action for semantic rules validation
            # Keys match TaskClassifier TaskType enum values
            action_mapping = {
                "documentation_update": "write_file",
                "test_generation": "write_file",
                "code_review": "review_code",
                "bug_fix": "write_file",
                "refactoring": "write_file",
                "feature_implementation": "write_file",
                "backend_utils_bug_fix": "write_file",  # Backend utility bug fixes
                "frontend_ui_tokens": "write_file",  # Frontend UI token updates
                "simple_api_endpoint": "write_file",  # Simple API endpoint creation
                "unknown": "analyze_code",
            }
            action = action_mapping.get(task_type, "analyze_code")

            semantic_valid, semantic_error, requires_approval = self._validate_task_semantic_rules(
                repo=repo,
                task_type=task_type,
                action=action,
                file_paths=None,  # File paths determined during execution
                command=None,
                trace_id=trace_id
            )

            if not semantic_valid:
                logger.warning(
                    f"[ProjectEngineerAgent] Semantic rules validation failed for step {step_index}: "
                    f"{semantic_error}"
                )
                return TaskResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="blocked",
                    is_safe=False,
                    details=f"Semantic rules validation failed: {semantic_error}",
                    error=semantic_error
                )

            if requires_approval:
                logger.info(
                    f"[ProjectEngineerAgent] Step {step_index} requires HITL approval"
                )
                return TaskResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="pending_approval",
                    is_safe=True,
                    details=(
                        f"Task requires Human-in-the-Loop approval. "
                        f"Action '{action}' flagged for manual review."
                    )
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
            # Generate deterministic task ID (CTO review fix: use hashlib instead of hash())
            import hashlib
            task_id_int = int(hashlib.sha256(task_id.encode('utf-8')).hexdigest(), 16) & 0x7FFFFFFF

            # Get task metadata for safe task constraints
            from project_engineer.safe_tasks import get_safe_task_metadata
            task_metadata = get_safe_task_metadata(task_type)

            # Prepare task dict for CodeGenerationWorkflow.execute()
            # Note: execute() expects "id", "title", "description" keys
            task_dict = {
                "id": task_id_int,
                "title": step_text[:100],
                "description": step_text,
                "task_type": task_type,
                "task_metadata": task_metadata if task_metadata else None,
            }

            # Execute workflow
            logger.info("[ProjectEngineerAgent] Starting CodeGenerationWorkflow execution")
            result_state = await self.workflow.execute(task_dict)

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
            "version": "1.2.0-phase1-security",
            "planner_available": self.planner is not None,
            "classifier_available": self.classifier is not None,
            "workflow_available": self.workflow is not None,
            "mode": self.mode,
            "features": {
                "task_decomposition": self.planner is not None,
                "task_classification": self.classifier is not None,
                "safe_task_gating": True,
                "code_generation": self.enable_code_generation,
                "semantic_rules_v3": True,
                "directory_validation": True,
                "task_type_validation": True,
                "action_whitelist": True,
                "sensitive_file_blocking": True,
                "hitl_approval": True,
            }
        }


async def run_task(description: str, repo: str = "RC918/morningai") -> List[TaskResult]:
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
